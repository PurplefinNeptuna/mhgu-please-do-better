from paths import MOD, SCRIPTS, FORGE, DEPS, PYTHON, CONTAINER_STORAGE, input_path
#!/usr/bin/env python3
"""Read-only r5 native trace export and explicit, closed rendering-gate receipt."""
import argparse
import json
import struct
import subprocess
import please_do_better as recipe
import research_tools as research

DEST=recipe.WORK/'r5-research'
SEEDS=(0x384af0,0x388ee8,0x623c08,0x56e62c,0x56e530,0x546f84,0x545630,
       0xa4fc9c,0xa4feb4,0xa50290,0xa4eb9c,0xa3e3b0,0xa397d4,0xa37c1c,0xce1fbc)


def check():
    image,_=recipe.binary.main_image((recipe.input_path('main')).read_bytes())
    record=json.loads((DEST/'research.json').read_text())
    recipe.require(record['executable_sha256']==recipe.binary.MAIN_SHA,'Wrong research executable')
    recipe.require({f['requested_offset'] for f in record['functions']}==set(SEEDS),'Incomplete trace export')
    receipts=[]
    for function in record['functions']:
        mismatches=0
        for inst in function['instructions']:
            original=bytes.fromhex(inst['original_bytes']);database=bytes.fromhex(inst['database_bytes'])
            recipe.require(image[inst['offset']:inst['offset']+len(original)]==original,'Stale original export bytes')
            mismatches+=original!=database
        recipe.require(not mismatches,'Imported instruction differs from pinned original')
        receipts.append({'requested_offset':hex(function['requested_offset']),'function_offset':hex(function['offset']),
                         'instructions':len(function['instructions']),'byte_mismatches':mismatches})
    # State-1 resize and reward generation share a paired update; they are not
    # two independent phases. Prove the direct builder call from original ARM.
    instruction=struct.unpack_from('<I',image,0x384fc0)[0]
    displacement=(instruction&0xffffff)<<2
    if displacement&0x2000000:displacement-=0x4000000
    recipe.require(instruction>>24==0xeb and 0x384fc0+8+displacement==0x3874e0,
                   'Native state-1 nested reward builder call changed')
    # Confirm the CPU-side group multiplication and offsets from actual words.
    recipe.require(struct.unpack_from('<4I',image,0x623c8c)==(0xe0800100,0xe08b0180,0xe2801f5b,0xe2809e16),
                   'Native group/root/item-node layout changed')
    inputs={}
    for name,expected in (
        ('AppShaderPackage.mfx','2b80892da570f42b38dfe46b31234503af3d593eb634da10109c37534ac36627'),
        ('root.arc','63d861e9beb9464ca8308760479ed2514d87e9975568889b9599e7a22d91615c'),
        ('root.spkg','7dea1d84f3e64d1a79df8f7a4d7bdf063643e996de6cfab95e7c5d782f8b795e')):
        data=(recipe.WORK/'inputs'/name).read_bytes()
        recipe.require(recipe.sha(data)==expected,f'Shader research input changed: {name}')
        inputs[name]={'bytes':len(data),'sha256':expected}
    spkg=(recipe.WORK/'inputs/root.spkg').read_bytes();header=struct.unpack_from('<11I',spkg)
    recipe.require(header[0]==0x4b5053 and (header[2]&0xffff)==0x26 and header[9]+header[10]==len(spkg),
                   'SPK loader format/bounds mismatch')
    mfx=(recipe.WORK/'inputs/AppShaderPackage.mfx').read_bytes()
    names={name:mfx.find(name.encode()+b'\0') for name in ('FGUICalcPosition2D','CBGUIMatrix','CBGUIGlobal','FGUITextureSampling')}
    recipe.require(all(offset>=0 for offset in names.values()),'GUI reflection names missing')
    report={'main_sha256':recipe.binary.MAIN_SHA,'trace_export_sha256':recipe.sha((DEST/'research.json').read_bytes()),
            'native_receipts':receipts,'shader_inputs':inputs,'reflection_name_offsets':names,
            'spkg':{'metadata_end':header[10],'gpu_bytes':header[9],'format':header[2]&0xffff},
            'scope':'Earlier CPU trace; r6 acceptance is recorded in highlight-research.json',
            'unverified':['actual slot-frame identity for each category/row/index',
                          'selected GUI vertex program and framebuffer transform',
                          'native draw epoch/target to Forge presented queue/texture correspondence']}
    recipe.write_json(recipe.OUT/'research-validation.json',report)
    print(f"PASS: {len(receipts)} original-byte native trace receipts; earlier CPU trace checked; r6 rendering covered separately")


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('export','check'))
    args=parser.parse_args()
    if args.command=='export':
        DEST.mkdir(parents=True,exist_ok=True)
        command=[research.GHIDRA/'support/analyzeHeadless',research.PROJECTS,'MHGU_1.4.0',
                 '-process','MHGU_1.4.0','-readOnly','-noanalysis','-scriptPath',research.SCRIPTS / 'ghidra',
                 '-postScript','ExportDamageNumberResearch.java',DEST,research.WORK/'inputs/main-memory.bin',
                 ','.join(hex(seed) for seed in SEEDS)]
        result=subprocess.run(list(map(str,command)),env=research.ghidra_environment(),capture_output=True,text=True)
        (DEST/'headless.log').write_text(result.stdout+result.stderr)
        recipe.require(result.returncode==0,'Read-only Ghidra export failed; inspect headless.log')
    check()


if __name__=='__main__':main()
