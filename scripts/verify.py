#!/usr/bin/env python3
"""Check the staged candidate: pinned inputs, exact hook windows, the emitted-code audit and the payload
inventory. Static analysis only; it proves nothing about gameplay."""
import json
from paths import BUILD_ROOT,ELF,PACKAGED_NRO,VERSION
from build import doctor,digest,record,source_hashes
import please_do_better as recipe
def verify():
    doctor();data=PACKAGED_NRO.read_bytes();nro=recipe.binary.Nro(data)
    # DT_TEXTREL / DF_TEXTREL require writes to memory the Switch maps read-only.
    if 22 in nro.tags or nro.tags.get(30,0)&4: raise ValueError('NRO requires dynamic relocations in read-only memory')
    receipt=json.loads((BUILD_ROOT/'build.json').read_text())
    if receipt.get('version')!=VERSION or receipt['nro_sha256']!=digest(PACKAGED_NRO) or receipt.get('source_sha256')!=source_hashes():
        raise ValueError('Build receipt differs from the staged NRO or current sources')
    inputs=recipe.validate_inputs();audit=recipe.inspect_binary(data)
    package=BUILD_ROOT/'package';actual={str(p.relative_to(package)) for p in package.rglob('*') if p.is_file()}
    if actual!={'romfs/nativeNX/plugins/please_do_better.nro','manifest.txt'}: raise ValueError('Unexpected runtime payload files: '+str(actual))
    record('verify.json',{'status':'PASSED','nro_sha256':digest(PACKAGED_NRO),'elf_sha256':digest(ELF),'exports':audit['exports'],
        'strong_imports':audit['imports'],'signature_windows':len(inputs['hooks'])+1,
        'gateway_sha256':digest(recipe.RECIPE/'src/gateway.S'),'text_relocations':False,'runtime_test':'NOT RUN'})
    print('PASS: pinned inputs, 22 hook windows and the frame colour setter, NZCVQ/GE audit, exports and payload inventory')
if __name__=='__main__': verify()
