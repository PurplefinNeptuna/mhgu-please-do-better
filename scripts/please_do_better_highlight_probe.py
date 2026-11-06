#!/usr/bin/env python3
"""Compiled r6 geometry/presentation/gold draw fixtures. No game or GPU launch."""
import json
import os
import itertools
import struct
from unicorn import arm_const as a
from please_do_better_runtime_probe import Probe, MAIN, DATA, STACK, STOP, REGS, MASK
from please_do_better_native_probe import native_clip
import re
import please_do_better as recipe


def main():
    image,_=recipe.binary.main_image((recipe.input_path('main')).read_bytes())
    payload=(recipe.WORK/'native/plugin.nro').read_bytes();checks=0
    def check(ok,label):
        nonlocal checks
        assert ok,label;checks+=1
    p=Probe(image,payload);p.call('forge_onInit');u=p.u
    check(p.read(p.private('highlight_ready'))==1,'Both guarded fixed rendering gateways applied')
    check(p.allocations==1 and p.tls_allocations==1,'No additional arena/TLS for gold highlights')
    flush_count=p.flushes;p.call('forge_onInit');check(p.flushes==flush_count,'Idempotent rendering startup')
    for site in (0xa4fe50,0x86a330):
        failed=Probe(image,payload,conflict=site);failed.call('forge_onInit')
        check(not failed.read(failed.private('highlight_ready')) and failed.read(failed.private('pair_ready'))==failed.read(failed.private('capture_ready'))==1,'Rendering conflict leaves working r4 mode/observation')
        check(failed.read(MAIN+site)==0xe3a00001,'External modification preserved')
    for fail in (flush_count-1,flush_count):
        failed=Probe(image,payload,fail_flush=fail);failed.call('forge_onInit')
        check(not failed.read(failed.private('highlight_ready')) and failed.read(failed.private('capture_ready'))==1,'Rendering flush failure is isolated')
        check(bytes(failed.u.mem_read(MAIN+0xa4fe50,8))==image[0xa4fe50:0xa4fe58] and bytes(failed.u.mem_read(MAIN+0x86a330,8))==image[0x86a330:0x86a338],'Both rendering detours rolled back')
    changed=Probe(image,payload);changed.call('forge_onInit');before=changed.flushes
    changed.write(MAIN+0x3822dc,0xe1a00000);changed.call('forge_onInit')
    check(changed.read(changed.private('highlight_ready'))==changed.read(changed.private('pair_ready'))==changed.read(changed.private('capture_ready'))==0,'Core ownership loss also disables stale highlighting')
    check(changed.flushes==before and changed.read(MAIN+0x3822dc)==0xe1a00000,'Ownership loss neither adopts nor rewrites external bytes')
    # Fixture publishes exact array/index/node binding; the separate original
    # list-copy tests cover provenance, and resource receipts cover all ordinals.
    sr=DATA+0x80000;owner=sr+0x34100
    node,icon,lst,ctx,renderer,target,program,uniforms,packet,gui,verts,model,global_,default,ref=[DATA+i for i in
        (0x20000,0x20200,0x21000,0x23000,0x25000,0x28000,0x28200,0x28300,0x28400,0x28500,0x29000,0x2a000,0x2b000,0x2c000,0x2d000)]
    p.singleton=sr;p.call('forge_onUpdate',[0]);p.write(sr+0x33f4c,0);p.write(owner+0x46f8,0x345678);p.write(owner+0x46fc,1)
    p.write(sr+0x389c0,default);p.write(default+0x204,ref);p.write(ref,0x334455)
    presented_resource=DATA+0x2f000;presented_ref=DATA+0x2f800
    raw_surface=DATA+0x2f900;gpu=DATA+0x2fa00;image_a=DATA+0x2fb00;image_b=DATA+0x2fc00
    p.write(sr+0x389cc,presented_resource);p.write(presented_resource+0x204,presented_ref)
    p.write(presented_ref,raw_surface);p.write(raw_surface+0x10,gpu);p.write(gpu+0x3c,image_a)
    p.write(default+0x3c,image_a);p.write(presented_resource+0x3c,image_a)
    p.write(owner+0x48c0,default)
    for index in (1,2):p.write(owner+0x48c0+index*4,presented_resource)
    p.write(owner+0x48cc,presented_resource);p.write(owner+0x48d0,1)
    p.write(node,MAIN+0x178fcc8);p.write(node+0x50,12);p.write(node+0xbc,0);p.write(node+0xc0,0x800000)
    p.write(lst+0x4c,1);p.write(lst+0x5c,8);p.write(lst+0x60+4*4,123|(3<<16))
    p.write(ctx+4,renderer);p.write(renderer+0x1ac,target);p.write(target,0x334455)
    p.write(renderer+0x1d8,0xd7376b18);p.write(renderer+0x1a4,packet);p.write(packet+8,program)
    p.write(program+0x40,uniforms);p.write(program+0x44,3);u.mem_write(uniforms,struct.pack('<3I',0x2d7,0x2d6,0x16f))
    p.write(renderer+0x134,24);p.write(renderer+0x138,0);p.write(renderer+0x18bc,model);p.write(renderer+0x18b4,global_)
    p.write(MAIN+0x212668c,gui);p.write(gui+0xb0,verts)
    sentinel_rect=DATA+0x2dd00
    p.write(MAIN+0x183f2b0,sentinel_rect);u.mem_write(sentinel_rect,bytes(16))
    m=[0.]*16
    for k in (0,5,10,15):m[k]=1.
    m[12]=100.;m[13]=-50.;u.mem_write(model,struct.pack('<16f',*m))
    v=[]
    for k in range(4):v.extend((36. if k&1 else 0.,-36. if k&2 else 0.,0.,0.,0.,0.))
    u.mem_write(verts,struct.pack('<24f',*v))
    # Exercise COMPILED category -> inline array -> root -> frame mapping,
    # comparing every supported ordinal with the independently extracted GUI.
    holder,roots,root_icon,root_frame,icon_nodes,frame_nodes,ids=[DATA+i for i in
        (0x40000,0x41000,0x42000,0x42200,0x43000,0x43400,0x44000)]
    p.write(lst+0x24,holder);p.write(holder+0x298,128);p.write(holder+0xf8,roots)
    p.write(root_icon+0xd8,icon_nodes);p.write(root_frame+0xd8,frame_nodes)
    displayed=p.private('displayed');mapping_cases=0
    for case in json.loads((recipe.OUT/'highlight-research.json').read_text())['resource']['layouts']:
        groups=[1,7] if case['layout']=='icon' else [2] if case['layout']=='icon_2' else [5,6]
        for group in groups:
            ir,br=(19,12) if group in (1,7) else (43,44) if group==2 else (66,65)
            index=case['index'];p.write(lst+0x4c,group);p.write(lst+0x5c,48)
            p.write(roots+ir*4,root_icon);p.write(roots+br*4,root_frame)
            p.write(lst+0x160+group*0x28,ir);p.write(lst+0x164+group*0x28,br);p.write(lst+0x16c+group*0x28,ids)
            p.write(ids+index*4,case['icon_index']);p.write(icon_nodes+case['icon_index']*4,icon);p.write(frame_nodes+case['frame_index']*4,node)
            p.write(icon,MAIN+0x176c7c4);p.write(node,MAIN+0x176c7c4);p.write(node+0x50,case['frame_id'])
            record=[DATA+0x10000,7,31,1,lst,1,7,lst+0x60+index*4,1,1,123|(3<<16)]+[0]*7
            u.mem_write(displayed,struct.pack('<18I',*record));p.call('forge_onUpdate',[0])
            b=struct.unpack('<11I',u.mem_read(p.private('bindings'),44))
            check(p.read(p.private('binding_count'))==1 and b[4:10]==(lst,group,index,node,icon,case['frame_id']),'Compiled mapping agrees with exact original GUI ordinal/object ID')
            mapping_cases+=1
    white=[(node,v,0xffffffff) for v in range(4)]
    check(p.tints==white,'Probe tints the bound frame white once, on all four corners')
    check(sum('set white' in s for s in p.logs)==1,'Probe logs the original frame colours once')
    p.write(node+0xa4,0xff0000ff);p.call('forge_onUpdate',[0]);p.call('forge_onUpdate',[0])
    check(sum('tint replaced' in s for s in p.logs)==1 and p.tints==white,'A replaced tint is logged once and not reapplied')
    u.mem_write(displayed,bytes(72));p.call('forge_onUpdate',[0]);p.write(lst+0x4c,1);p.write(node+0x50,12)
    record=[DATA+0x10000,7,31,1,lst,1,7,lst+0x60+4*4,1,1,123|(3<<16)]+[0]*7
    p.write(ids+4*4,2+4);p.write(icon_nodes+(2+4)*4,icon);p.write(frame_nodes+(4+4)*4,node);p.write(node+0x50,8+4)
    p.write(lst+0x160+0x28,19);p.write(lst+0x164+0x28,12);p.write(lst+0x16c+0x28,ids);p.write(roots+19*4,root_icon);p.write(roots+12*4,root_frame)
    u.mem_write(displayed,struct.pack('<18I',*record));p.call('forge_onUpdate',[0])
    check(len(p.tints)==8,'A new reward screen tints its frames again')
    u.mem_write(displayed,bytes(72));p.call('forge_onUpdate',[0]);p.write(lst+0x4c,1);p.write(node+0x50,12)
    def binding(index=4,batch=7):
        # Snapshot ticket and ten atomic payload words; no fixture invokes a
        # private publisher in place of the compiled capture/render code.
        fence=p.read(p.private('live_fence'))
        values=(fence,DATA+0x10000,batch,lst,1,index,node,icon,12,123|(3<<16))
        u.mem_write(p.private('bindings'),struct.pack('<11I',2,*values));p.write(p.private('binding_count'),1)
    binding()
    serial=[0]
    def geometry():
        serial[0]+=1;p.write(sr+0x33f50,serial[0]);p.write(sr+0x33f4c,serial[0]&1)
        p.frame(26,[0,0,0,0,ctx,node,node+0xcc])
    present_proc=DATA+0x2e000;p.write(MAIN+0x1841330,present_proc);p.write(present_proc,STOP)
    def present():
        p.call(MAIN+0x86a30c,[owner])
        check(u.reg_read(REGS[0])==0x345678 and u.reg_read(REGS[1])==owner+0x4740 and
              u.reg_read(REGS[2])==p.read(owner+0x46fc),'Original present wrapper reaches fixed gateway with exact queue/window/index')
    def render():p.draws.clear();p.call('forge_onImGuiFreeRender');return list(p.draws)
    clip_cases=0
    # Compare the compiled full gateway/draw callback with an independent
    # execution of the ORIGINAL ARM clip binder, including its sentinel tail.
    # Previous fixtures stopped before that tail and missed its empty default.
    for alternate,clip,sentinel in itertools.product((0,0x200),
            ((0,0,0,0),(90,45,200,100),(-12,-10,2000,1200),(300,200,100,50),
             (0,45,0,100),(2000,0,2100,100)),
            ((0,0,0,0),(90,45,200,100),(-1,-1,-1,-1))):
        expected=native_clip(p,(0,0,1920,1080),clip,sentinel,alternate)
        p.write(MAIN+0x183f2b0,sentinel_rect);u.mem_write(sentinel_rect,struct.pack('<4i',*sentinel))
        p.write(target+0x14,alternate);p.write(target+0x58,1920|(1080<<16))
        u.mem_write(target+0x18+(16 if alternate else 0),struct.pack('<4i',0,0,1920,1080))
        u.mem_write(target+0x38+(16 if alternate else 0),struct.pack('<4i',*clip))
        u.mem_write(DATA+0xf0000+8,struct.pack('<2f',1920,1080))
        u.mem_write(global_,struct.pack('<4f',2/1920,2/1080,-1,1))
        p.clip_history.clear();geometry();present();draws=render()
        visible=expected[2]>expected[0] and expected[3]>expected[1]
        check(bool(draws)==visible,'Compiled clipping visibility matches complete original ARM')
        check(not visible or p.clip_history==[tuple(float(x) for x in expected)],
              'Gold borders use the exact native effective scissor, including runtime sentinel')
        clip_cases+=1
    p.write(target+0x14,0);u.mem_write(sentinel_rect,bytes(16))
    p.write(MAIN+0x183f2b0,0);geometry();present();check(not render(),'Unreadable sentinel never guesses a full clip')
    p.write(MAIN+0x183f2b0,sentinel_rect)
    # Replay the last exact r11 logged input geometry with the native default
    # sentinel case. This is CPU regression evidence, not a gameplay draw.
    saved_m=m[:];saved_v=v[:];m[12]=1196.;m[13]=178.
    for k in range(4):v[k*6+1]=36. if k&2 else 0.
    u.mem_write(model,struct.pack('<16f',*m));u.mem_write(verts,struct.pack('<24f',*v))
    u.mem_write(global_,struct.pack('<4f',.0015625,-.0027777778,-1,1))
    u.mem_write(target+0x38,bytes(16));p.clip_history.clear()
    geometry();present();draws=render()
    expected=((1794,267,1848,267),(1848,267,1848,321),(1848,321,1794,321),(1794,321,1794,267))
    check(len(draws)==12 and all(all(abs(x-y)<.003 for x,y in zip(d[0],edge)) for d,edge in zip(draws,expected)),
          'R11 logged vertices/model/projection reach the exact transformed gold perimeter with native sentinel clipping')
    check(p.clip_history==[(0.,0.,1920.,1080.)],'Logged geometry regression uses native full-viewport scissor')
    m=saved_m;v=saved_v;u.mem_write(model,struct.pack('<16f',*m));u.mem_write(verts,struct.pack('<24f',*v))
    for width,height,time in itertools.product((1280,1920),(720,1080),(0.,.5,1.,1.5,2.)):
        u.mem_write(DATA+0xf0000+8,struct.pack('<2f',width,height))
        u.mem_write(global_,struct.pack('<4f',2/width,2/height,-1,1))
        u.mem_write(target+0x18,struct.pack('<4i',0,0,width,height));p.write(target+0x58,width|(height<<16));u.mem_write(target+0x38,struct.pack('<4i',90,45,200,100));p.time=time
        geometry();present();draws=render()
        check(len(draws)==12 and p.read(p.private('highlighted_count'))==1,'Four gold perimeter lines and eight procedural sparkle lines')
        expected=((100,50,136,50),(136,50,136,86),(136,86,100,86),(100,86,100,50))
        check(all(all(abs(a-b)<.002 for a,b in zip(line[0],want)) for line,want in zip(draws,expected)),'Shader/viewport coordinates reproduce native frame perimeter')
        check(all(abs(d[2]-1.5*height/720)<.001 for d in draws[:4]),'Border scales from 1.5px at 720p')
        check(all(d[1]&0xffffff==0x54c5f2 for d in draws),'Warm gold without fills')
        check(not p.clips,'Native clip stack balances')
        check(not render(),'Presentation authorization consumed once')
    for frame_vft,icon_vft in itertools.product((0x178fcc8,0x176c7c4),repeat=2):
        p.write(node,MAIN+frame_vft);p.write(icon,MAIN+icon_vft)
        geometry();present();check(len(render())==12,'Both original texture classes retain compiled geometry and gold drawing')
    # Release rendering must remain quiet across repeated successful frames.
    p.write(p.private('live_fence'),p.read(p.private('live_fence'))+1);binding()
    p.write(p.private('binding_count'),1);p.write(sr+0x1f,0,'<B')
    before_logs=len(p.logs)
    for _ in range(240):
        geometry();present();check(len(render())==12,'Quiet release keeps drawing through repeated boundaries')
    check(len(p.logs)==before_logs,'240 successful capture/present/render boundaries emit no diagnostics')
    # Native BC0E98 accepts the actual presented surface as well as resolving
    # its default sentinel. R8 incorrectly required the sentinel alone.
    p.write(target,raw_surface)
    geometry();present();check(len(render())==12,'Resolved presented surface receives the same verified gold geometry')
    # Flag 0x200 selects another rectangle bank. Its full-size path is valid.
    u.mem_write(target+0x28,struct.pack('<4i',0,0,1920,1080))
    u.mem_write(target+0x48,struct.pack('<4i',90,45,200,100));p.write(target+0x14,0x200)
    geometry();present();check(len(render())==12,'Full alternate viewport and native clip bank receive gold markers')
    # The inactive clip bank must not leak into the alternate native path.
    p.write(target+0x40,1);geometry();present();check(len(render())==12,'Selected clip bank is independent of inactive bank')
    p.write(target+0x40,200);p.write(target+0x30,960)
    geometry();present();check(not render(),'Actual reduced alternate viewport stays suppressed')
    p.write(target+0x30,1920);p.write(target+0x14,0)
    p.write(target,0);geometry();present();check(not render(),'Null surface cannot pass an unavailable default lookup')
    check(p.read(p.private('draw_rejection')+4)==4,'First viewport rejection stays readable during later null-target faults')
    p.write(target,0x334455)
    other_surface=DATA+0x2fd00;other_gpu=DATA+0x2fe00
    p.write(other_surface+0x10,other_gpu);p.write(other_gpu+0x3c,image_b)
    p.write(target,raw_surface)
    for index in (0,1,2,0,1,2):
        expected_image=image_a if index==0 else image_b
        p.write(gpu+0x3c,expected_image)
        p.write(presented_ref,other_surface if index==0 else raw_surface)
        p.write(owner+0x46fc,index);p.write(owner+0x48d0,index)
        p.write(owner+0x48cc,default if index==0 else presented_resource)
        p.write(default+0x3c,expected_image);p.write(presented_resource+0x3c,expected_image)
        geometry();present();check(len(render())==12,'Raw descriptor texture matches exact acquired image despite alternating descriptor identity')
    # Our own overlay uses exact projected slot geometry. Its primitives go
    # into Forge's selected image, independently of the game's UI source texture.
    p.write(owner+0x46fc,1);p.write(owner+0x48d0,1);p.write(owner+0x48cc,presented_resource);p.write(owner+0x48c4,presented_resource);p.write(presented_resource+0x3c,image_a)
    p.write(gpu+0x3c,image_a);p.write(presented_ref,other_surface)
    geometry();present();check(len(render())==12,'Current default descriptor cannot reject a different raw descriptor naming the acquired image')
    p.write(p.private('live_fence'),p.read(p.private('live_fence'))+1);binding()
    p.write(gpu+0x3c,image_b);geometry();present();check(len(render())==12,'Independent overlay draws verified geometry from an offscreen UI image')
    stable=bytes(u.mem_read(p.private('draw_rejection'),108))
    p.write(presented_resource+0x3c,image_b);p.write(gpu+0x3c,image_a)
    geometry();present();check(len(render())==12,'Alternating acquired image does not suppress the independent overlay')
    check(bytes(u.mem_read(p.private('draw_rejection'),108))==stable,'Texture identity changes create no false suppression diagnostic')
    p.write(owner+0x48cc,presented_resource);p.write(owner+0x48c4,presented_resource);p.write(presented_resource+0x3c,image_a);p.write(gpu+0x3c,image_a)
    p.write(presented_ref,raw_surface);p.write(target,0x334455)
    p.write(p.private('live_fence'),p.read(p.private('live_fence'))+1);binding()
    # Nondefault texture views must not be mistaken for full acquired images.
    p.write(target,raw_surface);p.write(raw_surface+0x14,DATA+0x2ff00)
    geometry();present();check(not render(),'Nondefault mip/layer view remains unsupported')
    p.write(raw_surface+0x14,0);p.write(target,0x334455)
    # Invalid acquired metadata provides no new presentation authorization.
    p.write(p.private('live_fence'),p.read(p.private('live_fence'))+1);binding()
    for addr,bad in ((owner+0x48d0,0),(owner+0x48cc,image_b),(owner+0x48c4,image_b),(owner+0x46fc,3)):
        old=p.read(addr);p.write(addr,bad)
        geometry();present();check(not render(),'Invalid acquired cache/index/table suppresses this boundary')
        p.write(addr,old)
    check(p.read(p.private('draw_rejection')+4)==7,'Acquired metadata failure has its own stable diagnostic')
    geometry();present();check(len(render())==12,'Valid acquired metadata restores future rendering without patch writes')
    # End-to-end compiled regression: native count/copy observation -> real
    # inline list copy -> Festa frame binding -> native present -> gold calls.
    ui,source,array,descriptor,flags_descriptor=[DATA+i for i in (0x10000,0x11000,0x12000,0x13000,0x14000)]
    # Native state 1 resizes BEFORE calling the nested reward builder.
    # The old pre-generation array is empty; comparing it to new rewards is
    # precisely the false relocation failure visible in the R7 screenshot.
    old_array=DATA+0x15000;u.mem_write(old_array,bytes(192))
    p.write(ui+0x3c,1);p.write(ui+0x5c,old_array);p.write(ui+0x60,16)
    before_drops=p.read(p.private('drops'))
    _,initial_update=p.frame(15,[ui],at=DATA+0x4c00)
    u.reg_write(REGS[8],ui);u.reg_write(REGS[4],array);u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00)
    u.emu_start(MAIN+0x384c7c,MAIN+0x384cb0,count=10000)
    u.mem_write(array+64,bytes(128));u.mem_write(old_array,b'\xdd'*192)
    p.write(ui+0x5c,array);p.write(ui+0x60,48)
    u.mem_write(source,struct.pack('<16H',*([123,3]*8)))
    _,root=p.frame(12,[ui],at=DATA+0x4000)
    p.write(descriptor,array);p.write(descriptor+4,48)
    _,wrapper=p.frame(13,[0,0,descriptor],at=DATA+0x5000)
    _,counter=p.frame(9,[0,0],caller=MAIN+0x381dc4,at=DATA+0x4400)
    p.frame(25,[31,0,0,0,4],at=DATA+0x4800)
    for slots in range(4,8):p.frame(2,[22 if slots==4 else 0,0,0,0,slots,31],at=DATA+0x4800)
    p.write(counter+272,8);p.leave(counter);p.leave(wrapper)
    u.reg_write(REGS[4],ui);u.reg_write(REGS[7],source);u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00)
    u.emu_start(MAIN+0x3875bc,MAIN+0x387680,count=10000);p.leave(root)
    p.write(ui+0x3c,2);p.leave(initial_update);p.call('forge_onUpdate',[0])
    recipe.write_json(recipe.WORK/'r15-report'/('state1-'+recipe.sha(payload)[:12]+'.json'),dict(
        nro_sha256=recipe.sha(payload),main_sha256=recipe.binary.MAIN_SHA,
        capture_faults_added=p.read(p.private('drops'))-before_drops,
        retained_record=bool(p.read(p.private('observed')+12)),
        summary_status=p.read(p.private('summary_status')),generated=p.read(p.private('generated_count')),
        extras=p.read(p.private('bonus_count')),bound_slots=p.read(p.private('binding_count'))))
    check(p.read(p.private('drops'))==before_drops and p.read(p.private('observed')+12)!=0,
          'Native state-1 resize then nested reward generation retains the new batch without a false relocation fault')
    p.write(lst+0x24,holder);p.write(lst+0x4c,1);p.write(lst+0x5c,48)
    p.write(roots+19*4,root_icon);p.write(roots+12*4,root_frame)
    p.write(lst+0x188,19);p.write(lst+0x18c,12);p.write(lst+0x194,ids)
    tracked=[]
    for index in range(4,8):
        n=node+(index-4)*0x400;i=icon+(index-4)*0x400
        u.mem_write(n,bytes(u.mem_read(node,0x130)));u.mem_write(i,bytes(u.mem_read(icon,0x130)))
        p.write(n,MAIN+0x176c7c4);p.write(i,MAIN+0x176c7c4);p.write(n+0x50,8+index)
        p.write(ids+index*4,2+index);p.write(icon_nodes+(2+index)*4,i);p.write(frame_nodes+(4+index)*4,n)
        tracked.append(n)
    p.write(descriptor,array);p.write(descriptor+4,48);p.write(flags_descriptor,source+128)
    _,update=p.frame(15,[ui]);p.native[MAIN+0x623c68]=0
    p.call(MAIN+0x623c08,[lst,descriptor,flags_descriptor]);p.leave(update);p.call('forge_onUpdate',[0])
    check(p.read(p.private('bonus_count'))==4 and p.read(p.private('binding_count'))==4,
          'Eight native generated slots/four extras bind four actual Festa texture frames')
    serial[0]+=1;p.write(sr+0x33f50,serial[0]);p.write(sr+0x33f4c,serial[0]&1)
    u.mem_write(target+0x38,bytes(16))
    # Replay the matching r13 log's real GUI transforms with the source texture
    # DIFFERENT from the acquired image. Four duplicate items must still draw
    # four distinct borders at their native projected positions, no copy hook.
    saved_m,saved_v=m[:],v[:];saved_global=bytes(u.mem_read(global_,16))
    v=[coordinate for k in range(4) for coordinate in (36. if k&1 else 0.,36. if k&2 else 0.,0.,0.,0.,0.)]
    u.mem_write(verts,struct.pack('<24f',*v));u.mem_write(global_,struct.pack('<4f',2/1280,-2/720,-1,1))
    p.write(target,raw_surface);p.write(gpu+0x3c,image_b)
    for index,n in enumerate(tracked):
        m[12]=1064.+44*index;m[13]=138.;u.mem_write(model,struct.pack('<16f',*m))
        p.frame(26,[0,0,0,0,ctx,n,n+0xcc])
    present();draws=render()
    check(len(draws)==48 and p.read(p.private('highlighted_count'))==4,
          'Native copied rewards with different source/acquired images reach four independent borders/sparkles')
    for index in range(4):
        x=1596.+66*index
        expected=((x,207.,x+54.,207.),(x+54.,207.,x+54.,261.),(x+54.,261.,x,261.),(x,261.,x,207.))
        check(all(all(abs(a-b)<.003 for a,b in zip(line[0],want)) for line,want in zip(draws[index*12:index*12+4],expected)),
              'Native logged transform preserves exact separate perimeter for duplicate reward index')
    m,v=saved_m,saved_v;u.mem_write(model,struct.pack('<16f',*m));u.mem_write(verts,struct.pack('<24f',*v));u.mem_write(global_,saved_global)
    p.write(gpu+0x3c,image_a);p.write(target,0x334455)
    u.mem_write(target+0x38,struct.pack('<4i',90,45,200,100))
    _,update=p.frame(16,[ui]);p.leave(update);p.call('forge_onUpdate',[0]);p.write(lst+0x5c,8);binding()
    # Negative gates exercise compiled gateway and rendering, rather than just
    # pure transform tests. A failed/uncertain path produces zero draw calls.
    p.write(target+0x30,960)
    tests={'empty':(lst+0x70,0),'new_item':(lst+0x70,124|(3<<16)),
           'increased_quantity':(lst+0x70,123|(4<<16)), 'category':(lst+0x4c,2),
           'node_id':(node+0x50,13),'node_type':(node,MAIN),
           'skipped_draw':(renderer+0x54,0x50),'uncached_vertices':(node+0xc0,0),
           'alternate_constructor':(node+0x108,0x10),'stride':(renderer+0x134,32),
           'offset':(renderer+0x138,96),'half_target':(target+0x14,0x200),
           'other_target':(target,0x334456),'unknown_shader':(renderer+0x1d8,0),
           'unknown_execution_mode':(sr+0x1f,2),'empty_clip':(target+0x40,10)}
    for name,(addr,value) in tests.items():
        prior=p.read(addr);p.write(addr,value);geometry();present();check(not render(),'Suppress uncertain geometry: '+name);p.write(addr,prior)
    # Each previously combined rejection is separately reported. Diagnostic
    # rendering must describe the actual class without consuming geometry.
    for reason,addr,value in ((1,node+0x108,0x10),(2,renderer+0x1ac,0),
                             (6,target,0x445567),(4,target+0x14,0x200),(5,renderer+0x1d8,0)):
        p.write(p.private('live_fence'),p.read(p.private('live_fence'))+1);binding()
        prior=p.read(addr);p.write(addr,value);before_logs=len(p.logs);geometry()
        check(len(p.logs)==before_logs,'Rejection gateway calls no logger/formatter with live GE')
        present();check(not render(),'Rejected draw stays unmarked')
        detail=struct.unpack('<17I',u.mem_read(p.private('draw_rejection'),68))
        check(detail[1]==reason,'Precise immutable rejection class')
        if reason==6 and os.environ.get('MHGU_DIAGNOSTICS','0')!='1':check(detail[3]==0,'Release rejection snapshot omits texture addresses')
        if reason==5 and os.environ.get('MHGU_DIAGNOSTICS','0')!='1':check(detail[6:11]==(0,0,0,0,0),'Release rejection snapshot omits shader/uniform traces')
        p.tree=True;p.text.clear();p.call('forge_onImGuiRender')
        check(not any('details are in the emulator log' in text for text in p.messages) and p.tree_depth==0,
              'Failures appear only in logs; settings trees remain balanced')
        check(not any(any(raw in fmt for raw in ('Draw texture','Surface 0x','Viewport %d','Technique 0x','Bindings:')) for fmt,text in p.text),'Panel contains no raw rendering addresses, viewport or shader data')
        p.tree=False;p.write(addr,prior)
    draw_logs=[message for message in p.logs if 'unsupported reward draw path' in message]
    check(len(draw_logs)==6,'Deferred Forge rendering logs each remaining rejection class once')
    # All twelve verified program uniform lists are accepted; prefix-only
    # perspective lookalikes still fail below.
    for shader in json.loads((recipe.OUT/'highlight-research.json').read_text())['shaders']['programs']:
        values=shader['runtime_uniforms'];u.mem_write(uniforms,struct.pack('<'+str(len(values))+'I',*values));p.write(program+0x44,len(values))
        geometry();present();check(bool(render())==shader['screen_xy_w1'],'Native reflected shader list agrees with verified position dataflow')
    p.write(program+0x44,3);u.mem_write(uniforms,struct.pack('<3I',0x2d7,0x2d6,0x16f))
    u.mem_write(uniforms,struct.pack('<8I',0x2d7,0x2d6,0x16f,0x2db,0x2dd,0x2de,0x3ca,0x3cb));p.write(program+0x44,8)
    geometry();present();check(not render(),'Reject perspective blend program despite matching prefix');p.write(program+0x44,3)
    p.write(lst+0x70,123|(2<<16));geometry();present();check(len(render())==12,'Quantity decrease keeps exact index eligible');p.write(lst+0x70,123|(3<<16))
    geometry();p.write(sr+0x33f4c,p.read(sr+0x33f4c)^1);present();check(not render(),'Reordered presentation/frame rejected');p.write(sr+0x33f4c,0)
    geometry();present();p.write(p.private('live_fence'),p.read(p.private('live_fence'))+1);check(not render(),'Screen exit invalidates geometry immediately');binding()
    geometry();present();p.write(p.private('frame_overflow')+p.read(sr+0x33f4c)*4,p.read(sr+0x33f50)+1);check(not render(),'Overflow suppresses entire affected frame')
    geometry();present();p.write(owner+0x46fc,2);p.frame(27,[0,owner+0x4740,1,STOP,0,0,0,0,0,0,0,0,0x345678]);check(len(render())==12,'Invalid present does not overwrite a valid captured boundary');p.write(owner+0x46fc,1)
    # Current producer and previous executor coexist without guessing which
    # ping-pong buffer Forge presents. Move the current quad to distinguish it.
    geometry();u.mem_write(model+48,struct.pack('<f',300));geometry()
    p.write(sr+0x1f,1);present();draws=render()
    check(len(draws)==12 and abs(draws[0][0][0]-100)<.002,'Parallel presentation selects previous producer geometry, not newer quad')
    p.write(sr+0x1f,0);present();draws=render()
    check(len(draws)==12 and abs(draws[0][0][0]-300)<.002,'Direct presentation selects current producer geometry')
    u.mem_write(model+48,struct.pack('<f',100))
    # The producer can mutate a wrapper after the older draw snapshot. The
    # older geometry retains its image, rather than re-reading the wrapper.
    p.write(target,raw_surface);p.write(gpu+0x3c,image_a)
    geometry();p.write(gpu+0x3c,image_b);geometry()
    p.write(sr+0x1f,1,'<B');present();check(len(render())==12,'Previous raw draw preserves immutable image across producer wrapper mutation')
    p.write(sr+0x1f,0,'<B');present();check(len(render())==12,'Current raw draw naming a different image still draws its own overlay')
    p.write(gpu+0x3c,image_a);p.write(target,0x334455)
    # Execute original begin/executor fragments to prove the frame tag model,
    # rather than merely setting values matching the renderer's assumptions.
    frame_fragments=0
    for parallel,initial_index in itertools.product((0,1),(0,1)):
        p.write(sr+0x33f50,10);p.write(sr+0x33f4c,initial_index);p.write(sr+0x1e,parallel,'<B')
        u.reg_write(REGS[4],sr);u.reg_write(REGS[5],sr);u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00)
        u.emu_start(MAIN+0xbc06ec,MAIN+0xbc0700,count=20)
        u.emu_start(MAIN+0xbc0720,MAIN+0xbc0738,count=20)
        u.emu_start(MAIN+0xbc0760,MAIN+0xbc0770,count=20)
        check(p.read(sr+0x33f50)==11 and p.read(sr+0x33f4c)==initial_index^1 and p.read(sr+0x1f,'<B')==parallel,'Original begin frame increments serial, toggles index and latches execution mode')
        u.reg_write(REGS[10],sr);u.emu_start(MAIN+0xbbea08,MAIN+0xbbea2c,count=20)
        check(u.reg_read(REGS[0])==sr+((initial_index^1^parallel)*4),'Original executor selects exactly producer index XOR mode')
        present();snapshot=struct.unpack('<8I',u.mem_read(p.private('presentation'),32))
        check(snapshot[2]==(initial_index^1^parallel) and snapshot[7]==11-parallel,'Compiled presentation records matching executed index/serial')
        render();frame_fragments+=1
    p.write(sr+0x1f,0,'<B');serial[0]=12
    # Rotate/mirror animated model while preserving the native strip perimeter.
    for model_values in ((0.,1.,-1.,0.),(-1.,0.,0.,1.),(.5,.25,-.25,.5)):
        m[0],m[1],m[4],m[5]=model_values;m[12]=100.;m[13]=-50.
        u.mem_write(model,struct.pack('<16f',*m));geometry();present();draws=render()
        check(len(draws)==12,'Rotated/mirrored/animated models remain renderable')
        g=(2/1920,2/1080,-1,1)
        points=[]
        for k in range(4):
            x,y,z=v[k*6:k*6+3];points.append((m[0]*x+m[4]*y+100,-(m[1]*x+m[5]*y-50)))
        order=(0,1,3,2)
        check(all(all(abs(actual-wanted)<.002 for actual,wanted in zip(draws[k][0],points[order[k]]+points[order[(k+1)%4]])) for k in range(4)),'Animated geometry draws edges without diagonals')
    m[0]=m[5]=1.;m[1]=m[4]=0.;u.mem_write(model,struct.pack('<16f',*m))
    # Two identical item IDs at distinct exact nodes never collapse into one.
    fence=p.read(p.private('live_fence'));node_b=DATA+0x20400
    u.mem_write(node_b,bytes(u.mem_read(node,0x130)));p.write(node_b+0x50,13);p.write(lst+0x74,123|(3<<16))
    values=(fence,DATA+0x10000,7,lst,1,5,node_b,icon,13,123|(3<<16))
    u.mem_write(p.private('bindings')+44,struct.pack('<11I',2,*values));p.write(p.private('binding_count'),2)
    geometry();u.mem_write(model+48,struct.pack('<f',180));p.frame(26,[0,0,0,0,ctx,node_b,node_b+0xcc]);present();draws=render()
    check(len(draws)==24 and abs(draws[0][0][0]-100)<.002 and abs(draws[12][0][0]-180)<.002,'Duplicate item IDs retain two different gold frame perimeters')
    p.write(lst+0x74,0);geometry();p.frame(26,[0,0,0,0,ctx,node_b,node_b+0xcc]);present();check(len(render())==12,'Empty duplicate suppresses only its exact index')
    p.write(p.private('binding_count'),0);geometry();present();check(not render(),'Normal/no-luck binding absence produces no marker')
    binding();u.mem_write(model+48,struct.pack('<f',100))
    # Fill the REAL bounded pool in one producer frame, then overflow the next
    # parallel frame: no silent overwrite of the prior frame is permitted.
    p.write(p.private('live_fence'),fence+1);fence+=1
    p.write(p.private('binding_count'),64);serial[0]+=1;p.write(sr+0x33f50,serial[0]);p.write(sr+0x33f4c,serial[0]&1)
    nodes=[]
    for i in range(64):
        addr=DATA+0x60000+i*0x140;nodes.append(addr);u.mem_write(addr,bytes(u.mem_read(node,0x130)))
        values=(fence,DATA+0x10000,7,lst,1,4,addr,icon,12,123|(3<<16))
        u.mem_write(p.private('bindings')+44*i,struct.pack('<11I',2,*values));p.frame(26,[0,0,0,0,ctx,addr,addr+0xcc])
    present();check(len(render())==64*12,'Exactly 64 immutable geometry samples fit without allocation')
    serial[0]+=1;p.write(sr+0x33f50,serial[0]);p.write(sr+0x33f4c,serial[0]&1)
    before=p.read(p.private('render_faults'));p.frame(26,[0,0,0,0,ctx,nodes[0],nodes[0]+0xcc]);present()
    check(p.read(p.private('render_faults'))>before and not render(),'Pool overflow reports a real capture fault and suppresses affected frame')
    p.write(sr+0x1f,1,'<B');present();check(len(render())==64*12,'Overflow does not erase the valid previous frame')
    # An out-of-order producer must not adopt a future sample as "old" via
    # unsigned subtraction and silently overwrite it.
    p.write(sr+0x1f,0,'<B');saved_serial=serial[0];p.write(sr+0x33f50,saved_serial-2);p.write(sr+0x33f4c,(saved_serial-2)&1)
    p.frame(26,[0,0,0,0,ctx,nodes[0],nodes[0]+0xcc]);p.write(sr+0x33f50,saved_serial);p.write(sr+0x33f4c,saved_serial&1)
    p.write(sr+0x1f,1,'<B');present();check(len(render())==64*12,'Reordered older geometry cannot overwrite a future valid frame')
    p.write(sr+0x1f,0,'<B');p.write(p.private('binding_count'),0)
    # A separate fixture checks all NZCVQ/GE combinations and both native stack
    # alignments at the compiled present tail gateway, including all VFP state.
    preservation=0;geometry_preservation=0
    binding();p.write(sr+0x33f50,serial[0]+2);p.write(sr+0x33f4c,(serial[0]+2)&1)
    for flags,ge,alignment in itertools.product(range(32),range(16),(0,4)):
        values=[0x12300000+i for i in range(13)];values[1]=owner+0x4740;values[2]=1;values[3]=STOP;values[12]=0x345678
        cpsr=0x10|(flags<<27)|(ge<<16);sp=STACK+0xff00-alignment;lr=STOP+64
        for r,value in zip(REGS,values):u.reg_write(r,value)
        vfp=[0x1234567800000000+i for i in range(32)]
        for i,value in enumerate(vfp):u.reg_write(getattr(a,f'UC_ARM_REG_D{i}'),value)
        u.reg_write(a.UC_ARM_REG_CPSR,cpsr);u.reg_write(a.UC_ARM_REG_SP,sp);u.reg_write(a.UC_ARM_REG_LR,lr);u.reg_write(a.UC_ARM_REG_FPSCR,0x1000000)
        u.emu_start(p.address('pdb_gateway_27'),STOP,count=100000)
        expected=values[:];expected[0]=values[12]
        check([u.reg_read(r) for r in REGS]==expected and u.reg_read(a.UC_ARM_REG_CPSR)&MASK==cpsr&MASK,'Present replay preserves GPR/NZCVQ/GE')
        check(u.reg_read(a.UC_ARM_REG_SP)==sp and u.reg_read(a.UC_ARM_REG_LR)==lr,'Present preserves stack/LR')
        check([u.reg_read(getattr(a,f'UC_ARM_REG_D{i}')) for i in range(32)]==vfp and u.reg_read(a.UC_ARM_REG_FPSCR)==0x1000000,'Present preserves VFP/FPSCR')
        preservation+=1
        values[4]=ctx;values[5]=node;values[6]=node+0xcc
        for r,value in zip(REGS,values):u.reg_write(r,value)
        for i,value in enumerate(vfp):u.reg_write(getattr(a,f'UC_ARM_REG_D{i}'),value)
        u.reg_write(a.UC_ARM_REG_CPSR,cpsr);u.reg_write(a.UC_ARM_REG_SP,sp);u.reg_write(a.UC_ARM_REG_LR,lr);u.reg_write(a.UC_ARM_REG_FPSCR,0x1000000)
        u.emu_start(p.address('pdb_gateway_26'),MAIN+0xa4fe58,count=1000000)
        check(u.reg_read(a.UC_ARM_REG_PC)==MAIN+0xa4fe58,'Geometry preservation fixture reaches displaced continuation before state comparison')
        expected=values[:];expected[0]=p.read(node+0xcc)&15
        check([u.reg_read(r) for r in REGS]==expected and u.reg_read(a.UC_ARM_REG_CPSR)&MASK==cpsr&MASK,'Active geometry capture/replay preserves GPR/NZCVQ/GE')
        check(u.reg_read(a.UC_ARM_REG_SP)==sp and u.reg_read(a.UC_ARM_REG_LR)==lr,'Active geometry capture preserves stack/LR')
        check([u.reg_read(getattr(a,f'UC_ARM_REG_D{i}')) for i in range(32)]==vfp and u.reg_read(a.UC_ARM_REG_FPSCR)==0x1000000,'Active geometry math restores every VFP register/FPSCR')
        geometry_preservation+=1
    verbose=('render trace','geometry gates','present gates','render gates','native-present',
             'selected-present','last-capture','capture vertices','model XY','clip input',
             'clip effective','perimeter[','binding[')
    check(not any(any(marker in fmt for marker in verbose) for fmt in p.logs),
          'Release retains only startup and bounded unsupported-path messages')
    rejects=[(fmt,args) for fmt,args in p.log_records if 'unsupported reward draw path' in fmt]
    reasons=[re.search(r'\((\d+): ([^)]+)\)',fmt) for fmt,_ in rejects]
    check(len(rejects)==6 and all(m and 1<=int(m[1])<=7 and len(m[2])>4 for m in reasons),
          'Concise suppression reasons retain correct ARM variadic ABI')
    recipe.write_json(recipe.OUT/'highlight-tests.json',dict(checks=checks,native_clip_equivalence_cases=clip_cases,present_preservation_cases=preservation,active_geometry_preservation_cases=geometry_preservation,native_resource_mapping_cases=mapping_cases,native_frame_fragment_cases=frame_fragments,nro_sha256=recipe.sha(payload),gpu_gameplay_tested=False))
    print(f'PASS: {checks} compiled capture/present/gold draw checks; {preservation} present state cases; GPU/gameplay pending')

if __name__=='__main__':main()
