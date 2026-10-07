from paths import MOD, SCRIPTS, FORGE, DEPS, PYTHON, CONTAINER_STORAGE, input_path
#!/usr/bin/env python3
"""Offline GUI resources, original ARM receipts and Maxwell position dataflow."""
import argparse
import subprocess
import shutil
import json
import re
import struct
import zlib
from pathlib import Path
import please_do_better as recipe

DEST=recipe.WORK/'highlight-research'
PROGRAMS=(489,640,769,2080,2550,2952,3306,3620,3688,4035,5958,6091,6303)
SEEDS=(0x622d4c,0x623c08,0x546f84,0xa4fc9c,0xa4feb4,0xa4eb9c,0xa397d4,0xa37c1c,
       0x87a8a0,0x93eff4,0x882760,0xbc0e98,0xbbe66c,0xbbe9c8,0xbc0524,0x86a30c,0xbc0688,0xbc0874)

TRACES={'verified':SEEDS,
        'r9-draw':(0xa50290,0x542aa0,0xb37dcc,0xb3880c,0x93eff4),
        'r9-pipeline':(0x8826fc,0xa4fa80,0xa4fa8c),
        'r9-shader':(0xbd993c,), 'r9-program':(0xbd8f8c,0xbda3a4),
        'r9-uniform':(0xbd9478,), 'r10-surfaces':(0x86a28c,0xbc0bfc,0xbbe66c,0x86a24c),
        'r10-texture-surface':(0xb09098,), 'r10-texture-create':(0xb0811c,0xb084a4),
        'r10-surface-view':(0xb07b18,), 'r10-window-init':(0x869c84,0x869ecc), 'r10-window':(0x86a080,),
    'r10-surface-bind':(0xbc0e98,0x86a28c,0x86a30c),
    'r13-nvn':(0x865408,)}


def resource():
    from mhgu_assets import read_arc
    archive,entries=read_arc(DEST/'result_eng.arc')
    recipe.require(recipe.sha(archive)=='c2973af8653ec7bb9e60e79fe930c266f67eb799804837b7df34a60099f5ab12','Reward archive identity changed')
    d=(DEST/'reward.gui').read_bytes()
    recipe.require(any(e['data']==d for e in entries.values()),'GUI not extracted from pinned archive')
    h=struct.unpack_from('<74I',d)
    recipe.require(h[0]==0x495547 and h[1]==0x22715 and h[2]==len(d),'GUI header changed')
    recipe.require(h[42]-h[41]==((h[10]*24+15)&~15),'GUI animations use 24 bytes; reference template size constant is obsolete')
    def string(off):
        recipe.require(h[65]+off<len(d),'GUI string bounds')
        return d[h[65]+off:].split(b'\0',1)[0].decode()
    animations=[];objects=[]
    for i in range(h[12]):
        x=struct.unpack_from('<9I',d,h[43]+i*36);props={}
        for j in range(x[1]&255):
            z=struct.unpack_from('<5I',d,h[45]+20*(x[6]+j));kind=z[1]&255
            if z[4]==0xffffffff:continue
            start=h[67 if kind in (3,17,18) else 69 if kind==4 else 68]+z[4]
            fmt='<4f' if kind==4 else '<f' if kind==2 else '<B' if kind in (3,17,18) else '<I'
            recipe.require(start+struct.calcsize(fmt)<=len(d),'GUI value bounds')
            props[string(z[3])]=struct.unpack_from(fmt,d,start)
        objects.append(dict(id=x[0],name=string(x[4]),kind=x[5],props=props))
    for i in range(h[10]):
        x=struct.unpack_from('<6I',d,h[41]+i*24)
        animations.append(dict(name=string(x[4]),first=x[3],count=x[1]&0xffff))
    layouts=[]
    for icon_name,bg_name,rows,delta in (('icon','bg',6,2),('icon_2','bg_2',4,4),('icon_3','bg_3',2,2)):
        ia=next(a for a in animations if a['name']==icon_name);ba=next(a for a in animations if a['name']==bg_name)
        for index in range(rows*8):
            icon_index=2+9*(index//8)+index%8;frame_index=icon_index+delta
            icon=objects[ia['first']+icon_index];frame=objects[ba['first']+frame_index]
            recipe.require(icon['name'].startswith('Tex_iconS') and frame['name'].startswith('Txt_item'),'Wrong native ordinal route')
            recipe.require(frame['props']['Tiling']==(0,) and frame['kind']==0x1b6313a3 and frame['props']['Size'][:2]==(36.,36.) and
                           frame['props']['Texture']==(11,) and frame['props']['mTextureRect'] in ((280.,0.,316.,36.),(280.,0.,318.,38.)),f'Not a reward slot frame: {icon_name}/{index} {frame}')
            recipe.require(icon['props']['Size'][:2]==(32.,32.),'Icon is separate from frame')
            layouts.append(dict(layout=icon_name,index=index,icon_index=icon_index,frame_index=frame_index,frame_id=frame['id']))
    return dict(sha256=recipe.sha(d),layouts=layouts)


def position_programs():
    # Decode the pinned Maxwell encoding table as research data. No emulator
    # implementation or shader code is copied into the runtime plugin.
    source=recipe.ROOT/'references/eden/src/shader_recompiler/frontend/maxwell/maxwell.inc'
    patterns=[]
    for name,pattern in re.findall(r'INST\((\w+),\s*"[^"]+",\s*"([01 -]+)"\)',source.read_text()):
        bits=pattern.replace(' ','');shift=64-len(bits)
        mask=int(''.join('0' if c=='-' else '1' for c in bits),2)<<shift
        value=int(bits.replace('-','0'),2)<<shift;patterns.append((name,mask,value))
    d=(recipe.WORK/'inputs/root.spkg').read_bytes();h=struct.unpack_from('<11I',d);meta=44
    shader_table=meta+struct.unpack_from('<I',d,meta+12)[0]
    def atom(name):return {(name,):1}
    def add(x,y):
        z=dict(x)
        for key,value in y.items():z[key]=z.get(key,0)+value
        return {k:v for k,v in z.items() if v}
    def mul(x,y):
        z={}
        for a,av in x.items():
            for b,bv in y.items():
                key=tuple(sorted(a+b));z[key]=z.get(key,0)+av*bv
        return z
    expected=[]
    for axis in (0,1):
        world=add(add(mul(atom('x'),atom(f'm{axis}')),mul(atom('y'),atom(f'm{axis+4}'))),
                  add(mul(atom('z'),atom(f'm{axis+8}')),atom(f'm{axis+12}')))
        expected.append(add(mul(world,atom(f'g{axis}')),atom(f'g{axis+2}')))
    expected.append({():1})
    # Exhaustive metadata scan establishes that the runtime uniform-sequence
    # whitelist cannot accidentally accept an unexamined program in this SPK.
    uniforms_base=meta+struct.unpack_from('<I',d,meta+4)[0]
    program_count=(struct.unpack_from('<I',d,meta)[0]-0x4028)//72
    candidates=[]
    for i in range(program_count):
        record=struct.unpack_from('<18I',d,meta+0x4028+i*72)
        if record[17]>=3:
            first=struct.unpack_from('<3I',d,uniforms_base+record[16]*4)
            if first==(0x2d7,0x2d6,0x16f):candidates.append(i)
    recipe.require(candidates==list(PROGRAMS),'GUI binding family has unexamined programs')
    results=[]
    for program in PROGRAMS:
        packed,_,offset=struct.unpack_from('<3I',d,shader_table+program*12)
        blob=d[h[10]+offset:h[10]+offset+(packed>>10)];header=struct.unpack_from('<8I',blob)
        start,size=header[5:7];recipe.require(start+size<=len(blob),'Shader byte bounds')
        registers=[atom(f'unset{i}') for i in range(255)]+[{}];outputs={};instructions=[]
        for pc in range(start+160,start+size,8):
            if (pc-start-160)%32==0:continue
            w=struct.unpack_from('<Q',blob,pc)[0];op=next((n for n,m,v in patterns if w&m==v),'UNKNOWN')
            dst=w&255;a=(w>>8)&255;c=(w>>39)&255;r20=(w>>20)&255
            cb=(w>>34)&31;co=((w>>20)&0x3fff)*4
            const=atom(f'm{co//4}') if cb==3 else atom(f'g{co//4}') if cb==4 else atom(f'c{cb}_{co}')
            result=atom(f'unknown_{pc:x}_{op}')
            if op=='EXIT':break
            if op=='AST':
                outputs[(w>>20)&1023]=registers[dst];continue
            if op=='ALD':
                off=(w>>20)&1023;result=atom({128:'x',132:'y',136:'z'}.get(off,f'attr{off}'))
            elif op=='MOV_cbuf':result=const
            elif op=='MOV32I':
                value=struct.unpack('<f',struct.pack('<I',(w>>20)&0xffffffff))[0];result={():value} if value else {}
            elif op=='MOV_reg':result=registers[r20]
            elif op=='FMUL_cbuf':result=mul(registers[a],const)
            elif op=='FMUL_reg':result=mul(registers[a],registers[r20])
            elif op=='FADD_cbuf':result=add(registers[a],const)
            elif op=='FADD_reg':result=add(registers[a],registers[r20])
            elif op=='FFMA_cr':result=add(mul(registers[a],const),registers[c])
            elif op=='FFMA_rc':result=add(mul(registers[a],registers[c]),const)
            elif op=='FFMA_reg':result=add(mul(registers[a],registers[r20]),registers[c])
            # Validate arithmetic modifiers, not only the opcode mnemonic.
            # Unknown or modified values taint their dependents; only position
            # X/Y/W dataflow is accepted, leaving unrelated depth math alone.
            if op.startswith('FFMA') and ((w>>48)&7):result=atom(f'modified_{pc:x}')
            if op.startswith('FMUL') and (((w>>41)&7) or ((w>>48)&1) or ((w>>50)&1)):result=atom(f'modified_{pc:x}')
            if op.startswith('FADD') and any((w>>bit)&1 for bit in (45,46,48,49,50)):result=atom(f'modified_{pc:x}')
            if ((w>>16)&7)!=7 or ((w>>19)&1):result=atom(f'predicated_{pc:x}')
            registers[dst]=result;instructions.append(dict(pc=hex(pc),op=op,word=hex(w)))
        actual=[outputs.get(i) for i in (0x70,0x74,0x7c)];accepted=actual==expected
        # Serialized constant bindings: shader slot 0/1/2 maps to Maxwell c3/4/5.
        bindings=struct.unpack_from('<'+str(header[2])+'Q',blob,header[1]+32)
        ids=[(b>>6)&0xfff for b in bindings];slots=[b&63 for b in bindings]
        recipe.require(ids[:3]==[0x2d7,0x2d6,0x16f] and slots[:3]==[0,1,2],'GUI CB mapping changed')
        program_record=struct.unpack_from('<18I',d,meta+0x4028+program*72)
        count=program_record[17];uniform_table=meta+struct.unpack_from('<I',d,meta+4)[0]
        uniforms=list(struct.unpack_from('<'+str(count)+'I',d,uniform_table+program_record[16]*4))
        # Native BD9478 builds the runtime list by de-duplicating reflected
        # constant IDs, then texture/sampler pairs, VS before PS. Check that
        # the serialized whitelist is also the exact runtime sequence.
        runtime_uniforms=[]
        for table_offset,stage_index in ((12,program_record[8]),(16,program_record[9])):
            table=meta+struct.unpack_from('<I',d,meta+table_offset)[0]
            stage_packed,_,stage_offset=struct.unpack_from('<3I',d,table+stage_index*12)
            stage=d[h[10]+stage_offset:h[10]+stage_offset+(stage_packed>>10)]
            stage_header=struct.unpack_from('<8I',stage)
            nc=stage_header[2]&65535;nt=stage_header[2]>>16
            start=stage_header[1]+32
            constants=struct.unpack_from('<'+str(nc)+'Q',stage,start)
            textures=struct.unpack_from('<'+str(nt)+'Q',stage,start+nc*8)
            reflected=[(x>>6)&1023 for x in constants]
            for x in textures:reflected.extend(((x>>6)&1023,(x>>16)&65535))
            for identity in reflected:
                if identity not in runtime_uniforms:runtime_uniforms.append(identity)
        recipe.require(runtime_uniforms==uniforms,'Native runtime uniform sequence differs from serialized metadata')
        results.append(dict(runtime_uniforms=runtime_uniforms,program=program,shader_sha256=recipe.sha(blob),bytes=len(blob),uniforms=uniforms,
                            screen_xy_w1=accepted,dataflow=str(actual),bindings=ids,instructions=instructions))
    recipe.require([r['program'] for r in results if r['screen_xy_w1']]==[p for p in PROGRAMS if p!=3620],'Expected twelve 2D programs and one rejected perspective program')
    return dict(encoding_table_sha256=recipe.sha(source.read_bytes()),programs=results)


def check():
    report=dict(resource=resource(),shaders=position_programs(),native=[])
    image,_=recipe.binary.main_image((recipe.input_path('main')).read_bytes())
    for folder,seeds in TRACES.items():
        path=DEST/folder/'research.json';record=json.loads(path.read_text())
        recipe.require(record['executable_sha256']==recipe.binary.MAIN_SHA,'Wrong imported main')
        recipe.require({f['requested_offset'] for f in record['functions']}==set(seeds),f'Incomplete rendering trace: {folder}')
        for f in record['functions']:
            for inst in f['instructions']:
                original=bytes.fromhex(inst['original_bytes'])
                recipe.require(image[inst['offset']:inst['offset']+len(original)]==original and
                               original==bytes.fromhex(inst['database_bytes']),'Imported native bytes differ')
        report['native'].append(dict(trace=folder,sha256=recipe.sha(path.read_bytes()),functions=len(record['functions'])))
    # The game-specific texture subclass shares the base layout and rendering
    # methods. DTI is a lead; acceptance uses original main vtable words.
    tables={name:struct.unpack_from('<30I',image,offset) for name,offset in
            (('texture',0x178fcc8),('festa_texture',0x176c7c4))}
    recipe.require(all(tables['texture'][i]==tables['festa_texture'][i]
                       for i in range(30) if i not in (1,5)), 'Festa texture inherited ABI differs')
    recipe.require(tables['texture'][15]==0xa4fc9c and tables['texture'][16]==0xa4eddc,
                   'Texture draw/vertex method identity differs')
    report['texture_classes']={name:dict(vtable=offset,bytes_sha256=recipe.sha(image[offset:offset+120]))
                              for name,offset in (('texture',0x178fcc8),('festa_texture',0x176c7c4))}
    # Original BC1314 uses PC+8 plus its BC13D8 literal, then reads the
    # relocated pointer in that GOT entry. BC1330..BC1364 implement the
    # sentinel equality and cached-viewport substitution after intersection.
    literal=struct.unpack_from('<I',image,0xbc13d8)[0]
    recipe.require(0xbc131c+literal==0x183f2b0 and
                   struct.unpack_from('<I',image,0x183f2b0)[0]==0x191eaa0,
                   'Native scissor sentinel indirection changed')
    report['clip_sentinel']={'got_offset':'0x183f2b0','unrelocated_pointer':'0x191eaa0',
                            'native_fragment':['0xbc12d8','0xbc1368'],
                            'semantics':'Compare normalized intersection with runtime sentinel; exact match uses cached viewport',
                            'runtime_contents':'Read guarded; no zero-value assumption'}
    recipe.require(0xbbecfc+struct.unpack_from('<I',image,0xbbfbd0)[0]==0x18418f8 and
                   0xbbed38+struct.unpack_from('<I',image,0xbbfd2c)[0]==0x18418f8,
                   'Native downsample callback indirection changed')
    recipe.require(0x868c78+struct.unpack_from('<I',image,0x8695c8)[0]==0x18418f8 and
                   image[0x157168b:0x157168b+len(b'nvnCommandBufferDownsample\0')]==b'nvnCommandBufferDownsample\0',
                   'Native NVN callback initializer changed')
    report['downsample']={'gateways':['0xbbfb08','0xbbfb44'],'callback_got':'0x18418f8',
                         'kind':'nvnCommandBufferDownsample','arguments':'r8 command buffer; r11 source texture; r10 destination texture',
                         'scope':'Original same-size whole-texture native branches, with equal or differing surface formats; observed source to acquired image for exact frame'}
    report.update(main_sha256=recipe.binary.MAIN_SHA,runtime_gpu_tested=False,
                  acceptance='Verified reward frame ordinals and 2D shader dataflow; native producer serial/index correlated to direct and one-frame parallel presentation',
                  unsupported=['half-size or offset render targets','unmatched shader variants'])
    recipe.write_json(recipe.OUT/'highlight-research.json',report)
    print('PASS: reward frame resource/Maxwell/native receipts; 2D programs:',[r['program'] for r in report['shaders']['programs'] if r['screen_xy_w1']])
    return report

def prepare():
    # Copies only; never edits the dump. Preserve the pinned ARC/MFX identities.
    from mhgu_assets import read_arc
    DEST.mkdir(parents=True,exist_ok=True)
    source=Path('~/.local/share/eden/dump/0100770008DD8000/romfs/nativeNX/eng/arc/result_eng.arc')
    shutil.copyfile(source,DEST/'result_eng.arc')
    _,entries=read_arc(DEST/'result_eng.arc')
    rewards=[e['data'] for (name,kind),e in entries.items() if name.endswith('reward')]
    recipe.require(len(rewards)==1,'Ambiguous reward GUI member')
    (DEST/'reward.gui').write_bytes(rewards[0])
    inputs=recipe.WORK/'inputs';inputs.mkdir(exist_ok=True)
    romfs=ROOT/'work/inputs/romfs/nativeNX'
    shutil.copyfile(romfs/'system/app_shader/AppShaderPackage.mfx',inputs/'AppShaderPackage.mfx')
    shutil.copyfile(romfs/'sa/NX/root.arc',inputs/'root.arc')
    arc=(inputs/'root.arc').read_bytes()
    recipe.require(recipe.sha(arc)=='63d861e9beb9464ca8308760479ed2514d87e9975568889b9599e7a22d91615c','Root ARC identity changed')
    recipe.require(struct.unpack_from('<4sHH',arc)==(b'ARC\0',17,1),'Expected pinned single-member shader ARC')
    name,kind,size,flags,offset=struct.unpack_from('<64sIIII',arc,12)
    recipe.require(name.split(b'\0')[0]==b'sc\\NX\\root' and kind==37064218 and offset+size<=len(arc),'Root SPK entry changed')
    decoder=zlib.decompressobj();spk=decoder.decompress(arc[offset:offset+size])+decoder.flush()
    # The shared small-resource ARC helper uses a 24-bit size mask; this 58MB
    # member needs the pinned ARC's full 30-bit expanded-size field.
    recipe.require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail and
        len(spk)==flags&0x3fffffff and recipe.sha(spk)=='7dea1d84f3e64d1a79df8f7a4d7bdf063643e996de6cfab95e7c5d782f8b795e','Shader ARC decompression/identity changed')
    (inputs/'root.spkg').write_bytes(spk)
    import research_tools as research
    for folder,seeds in TRACES.items():
        target=DEST/folder;target.mkdir(exist_ok=True)
        command=[research.GHIDRA/'support/analyzeHeadless',research.PROJECTS,'MHGU_1.4.0',
            '-process','MHGU_1.4.0','-readOnly','-noanalysis','-scriptPath',research.SCRIPTS / 'ghidra',
            '-postScript','ExportDamageNumberResearch.java',target,research.WORK/'inputs/main-memory.bin',','.join(hex(x) for x in seeds)]
        result=subprocess.run(list(map(str,command)),env=research.ghidra_environment(),capture_output=True,text=True)
        (target/'headless.log').write_text(result.stdout+result.stderr)
        recipe.require(result.returncode==0,f'Read-only native export failed: {folder}')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',nargs='?',choices=('prepare','check'),default='check')
    if parser.parse_args().command=='prepare':prepare()
    check()
