#!/usr/bin/env python3
"""Compiled native frame-tint fixtures: slot-to-frame mapping and the white vertex colour. No game launch."""
import json
import struct
from please_do_better_runtime_probe import Probe, MAIN, DATA
import please_do_better as recipe

WHITE = 0xffffffff


def main():
    image,_=recipe.binary.main_image((recipe.input_path('main')).read_bytes())
    payload=(recipe.WORK/'native/plugin.nro').read_bytes();checks=0
    def check(ok,label):
        nonlocal checks
        assert ok,label;checks+=1
    p=Probe(image,payload);p.call('forge_onInit');u=p.u
    check(p.read(p.private('capture_ready'))==1,'Capture hooks ready')
    for site in (0xa4fe50,0x86a330):
        check(bytes(u.mem_read(MAIN+site,8))==image[site:site+8],'Former render sites stay unhooked')
    lst,icon,node=DATA+0x21000,DATA+0x20200,DATA+0x20000
    holder,roots,root_icon,root_frame,icon_nodes,frame_nodes,ids=[DATA+i for i in
        (0x40000,0x41000,0x42000,0x42200,0x43000,0x43400,0x44000)]
    p.write(lst+0x24,holder);p.write(holder+0x298,128);p.write(holder+0xf8,roots)
    p.write(root_icon+0xd8,icon_nodes);p.write(root_frame+0xd8,frame_nodes)
    displayed=p.private('displayed')

    def show(group,case,frame_id=None):
        """One displayed record whose single slot is an extra-luck slot at `case`'s GUI ordinal."""
        ir,br=(19,12) if group in (1,7) else (43,44) if group==2 else (66,65)
        index=case['index'];p.write(lst+0x4c,group);p.write(lst+0x5c,48)
        p.write(roots+ir*4,root_icon);p.write(roots+br*4,root_frame)
        p.write(lst+0x160+group*0x28,ir);p.write(lst+0x164+group*0x28,br);p.write(lst+0x16c+group*0x28,ids)
        p.write(ids+index*4,case['icon_index']);p.write(icon_nodes+case['icon_index']*4,icon);p.write(frame_nodes+case['frame_index']*4,node)
        p.write(icon,MAIN+0x176c7c4);p.write(node,MAIN+0x176c7c4)
        p.write(node+0x50,case['frame_id'] if frame_id is None else frame_id)
        u.mem_write(node+0xa4,struct.pack('<4I',*[0xa02337dc]*4))
        record=[DATA+0x10000,7,31,1,lst,1,7,lst+0x60+index*4,1,1,123|(3<<16)]+[0]*7
        u.mem_write(displayed,struct.pack('<18I',*record))

    # Every supported layout: the compiled category -> inline array -> root -> frame mapping agrees
    # with the independently extracted GUI, and that frame alone gets white on all four corners.
    mapping_cases=0
    for case in json.loads((recipe.OUT/'highlight-research.json').read_text())['resource']['layouts']:
        groups=[1,7] if case['layout']=='icon' else [2] if case['layout']=='icon_2' else [5,6]
        for group in groups:
            show(group,case);p.tints.clear();p.call('forge_onUpdate',[0])
            check(p.read(p.private('binding_count'))==1 and p.tints==[(node,v,WHITE) for v in range(4)],
                  'Compiled mapping tints exactly the original GUI frame white')
            check(struct.unpack('<4I',u.mem_read(node+0xa4,16))==(WHITE,)*4,'Frame corners hold white')
            mapping_cases+=1
    case=json.loads((recipe.OUT/'highlight-research.json').read_text())['resource']['layouts'][0]
    show(1,case,frame_id=case['frame_id']+1);p.tints.clear();p.call('forge_onUpdate',[0])
    check(not p.tints and p.read(p.private('binding_count'))==0,'A frame with the wrong object ID is left alone')
    show(1,case);p.write(node,MAIN+0x178fcc8+4);p.tints.clear();p.call('forge_onUpdate',[0])
    check(not p.tints,'A node that is not a texture object is left alone')
    show(1,case);p.write(ids+case['index']*4,case['icon_index']+1);p.tints.clear();p.call('forge_onUpdate',[0])
    check(not p.tints,'A slot outside the known layouts is left alone')
    show(1,case);p.call('forge_onUpdate',[0]);p.tints.clear();p.call('forge_onUpdate',[0])
    check(p.tints==[(node,v,WHITE) for v in range(4)],'Each update reasserts the tint through the setter')
    u.mem_write(displayed,bytes(72));p.tints.clear();p.call('forge_onUpdate',[0])
    check(not p.tints and struct.unpack('<4I',u.mem_read(node+0xa4,16))==(WHITE,)*4,
          'Without a displayed highlight nothing is set back')

    changed=Probe(image,payload);changed.write(MAIN+0xa4e0b8+8,0xe1a00000);changed.call('forge_onInit')
    check(any('frame colour setter differs' in s for s in changed.logs),'A changed setter is reported')
    check(changed.read(changed.private('capture_ready'))==1,'A changed setter leaves luck and capture working')
    p=changed;u=p.u;displayed=p.private('displayed')
    p.write(lst+0x24,holder);p.write(holder+0x298,128);p.write(holder+0xf8,roots)
    p.write(root_icon+0xd8,icon_nodes);p.write(root_frame+0xd8,frame_nodes)
    show(1,case);p.call('forge_onUpdate',[0])
    check(not p.tints,'A changed setter is never called')

    recipe.write_json(recipe.OUT/'highlight-tests.json',dict(checks=checks,native_resource_mapping_cases=mapping_cases,
                      nro_sha256=recipe.sha(payload),gameplay_tested=False))
    print(f'PASS: {checks} compiled frame-mapping/tint checks; {mapping_cases} GUI layout cases; gameplay pending')


if __name__=='__main__':main()
