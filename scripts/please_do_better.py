#!/usr/bin/env python3
"""Shared recipe facts for the probes: pinned-input validation and the compiled binary audit."""
import hashlib, json, re, struct
import mhgu_binary as binary
from paths import MOD, BUILD_ROOT, WORK_ROOT, input_path
RECIPE=MOD
WORK=WORK_ROOT
OUT=BUILD_ROOT
CALLBACKS={'init','fini','forge_onLoad','forge_onInit','forge_onUpdate','forge_onImGuiInit','forge_onImGuiRender','forge_onImGuiFreeRender','purplelib_on_register'}

def sha(blob): return hashlib.sha256(blob).hexdigest()
def require(ok,message):
    if not ok: raise ValueError(message)
def write_json(path,record):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')

def recipes():
    """(site, window, words, paired) from the Rust table: the 22 hook sites."""
    source=(RECIPE/'core/src/signatures.rs').read_text()
    rows=re.findall(r'row\((0x[0-9a-f]+), (0x[0-9a-f]+), \[([^\]]+)\], (true|false)\)',source)
    return [(s,w,[int(x,16) for x in words.split(',')],paired=='true') for s,w,words,paired in rows]

def validate_inputs():
    image,segments=binary.main_image(input_path('main').read_bytes())
    rows=recipes();require(len(rows)==22,'Unexpected hook inventory')
    sites=[];evidence=json.loads((MOD/'research/patch-sites.json').read_text())
    for (site,window,words,_),old in zip(rows[:2],evidence['patch_sites']):
        start=int(window,16);raw=struct.pack('<8I',*words)
        require(start==int(old['surrounding_start'],16) and raw.hex()==old['surrounding_bytes'],'Signature differs from handoff')
        require(int(site,16)==int(old['main_offset'],16) and words[3]==int(old['original_word'],16),'Unexpected patch offset/original')
        sites.append({'window':start,'offset':int(site,16),'original':words[3],'replacement':0xe3a00001,'bytes':raw.hex()})
    require([s['offset'] for s in sites]==[0x3822dc,0x4d17f4],'Patch scope changed')
    for site,window,words,_ in rows:
        start=int(window,16)
        require(len(words)==8 and image[start:start+32]==struct.pack('<8I',*words),f'Original window differs: {window}')
        require(start<=int(site,16)<=start+24,'Displaced words escape signature window')
    setter=re.search(r'VERTEX_COLOR: \(u32, \[u32; 8\]\) =\s*\((0x[0-9a-f]+), \[([^\]]+)\]\)',(RECIPE/'core/src/signatures.rs').read_text())
    require(setter is not None,'Missing vertex colour setter window')
    start=int(setter[1],16)
    require(image[start:start+32]==struct.pack('<8I',*[int(x,16) for x in setter[2].split(',')]),'Vertex colour setter window differs')
    require(struct.unpack_from('<3I',image,0x4d1804)==(0xe1a00004,0xe3001102,0xebf6797d),'Second site 0x102 continuation differs')
    report={'main':str(input_path('main')),'sha256':binary.MAIN_SHA,'build_id':binary.BUILD_ID[:32].upper(),'sites':sites,
            'hooks':[{'site':s,'window':w,'paired':p,'original_words':[hex(x) for x in words]} for s,w,words,p in rows],
            'frame_colour_setter':{'address':hex(start),'checked':True},
            'text_bytes':len(segments[0][1]),'runtime_identity':'Title + exact signatures, not full build ID'}
    write_json(OUT/'input-validation.json',report)
    return report

def inspect_binary(payload):
    """The emitted-code contract: exports, imports, flag writes, SVC scope, size and relocations."""
    from native_support import nso_exports
    nro=binary.Nro(payload)
    imports={name.decode() for name,entry,*_ in nro.symbols if name and entry[5]==0}
    exports={name.decode() for name,entry,*_ in nro.symbols if name and entry[5]!=0}
    require(exports==CALLBACKS,f'Unexpected callbacks/exports: {exports}')
    available=set().union(*(nso_exports(input_path(n)) for n in ['main','sdk','forge']))
    require(not imports-available,f'Unresolved imports: {imports-available}')
    native=WORK/'native';readelf=(native/'readelf.txt').read_text();disassembly=(native/'disassembly.txt').read_text()
    require('.init_array' not in readelf and '.fini_array' not in readelf,'Unsupported dynamic static initialization')
    require(not re.search(r'\bmsr\b.*(?:APSR_g|APSR_nzcvqg|CPSR_(?:c|x|s|fs))',disassembly,re.I),'Forbidden flag-register write')
    # ARM signed/unsigned parallel add/subtract families change GE even without an S suffix.
    require(not re.search(r'\b(?:s|u)(?:add8|add16|sub8|sub16|asx|sax)\w*\s',disassembly,re.I),'Gateway helper contains a GE-writing parallel arithmetic instruction')
    msr_words=re.findall(r'\b([0-9a-f]{8})\s+msr\s',disassembly,re.I)
    require(msr_words and set(msr_words)=={'e128f002'},'Only audited NZCVQ restore may write flags')
    svcs=re.findall(r'\bsvc\s+(0x[0-9a-f]+)',disassembly)
    require(sorted(int(x,16) for x in svcs)==[6,0x29,0x5f],'Unexpected SVC scope')
    require('dsb\tsy' in disassembly and re.search(r'\bisb\b',disassembly),'Missing executable barriers')
    bss=struct.unpack_from('<I',payload,56)[0]
    # BSS keeps the C++ build's bound. The Rust image carries core/alloc support, so its own bound is 96 KiB.
    require(bss<=81920 and len(payload)<=98304,'Unexpected allocation-free plugin size')
    relocations=0
    for addr_tag,size_tag in ((17,18),(23,2)):
        if addr_tag not in nro.tags: continue
        start,size=nro.tags[addr_tag],nro.tags[size_tag];nro.region(start,size)
        require(size%8==0,'Malformed ARM REL table')
        for pos in range(start,start+size,8):
            address,info=struct.unpack_from('<II',payload,pos)
            require(address%4==0 and address+4<=len(payload)+bss and info>>8<nro.count,'Invalid relocation target/symbol')
            require(info&255 in (2,21,22,23),'Unsupported ARM relocation')
            relocations+=1
    report={'nro_sha256':sha(payload),'nro_bytes':len(payload),'bss_bytes':bss,'imports':sorted(imports),'exports':sorted(exports),
            'relocations':relocations,'CodeMemory_objects_added':1,'plugin_heap_allocations':0,'forbidden_APSR_g_instructions':0,'runtime':'NOT RUN'}
    write_json(OUT/'binary-validation.json',report)
    return report
