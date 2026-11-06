#!/usr/bin/env python3
"""R5 native display-copy/collection fixtures. No GPU, launch or disk settings."""
import itertools
import struct
import unicorn
from unicorn import arm_const as a
from please_do_better_runtime_probe import Probe, MAIN, DATA, STACK, STOP, REGS
import please_do_better as recipe


def main():
    image,_=recipe.binary.main_image((recipe.input_path('main')).read_bytes())
    payload=(recipe.WORK/'native/plugin.nro').read_bytes()
    checks=0
    def check(ok,label):
        nonlocal checks
        assert ok,label;checks+=1
    p=Probe(image,payload);p.call('forge_onInit');u=p.u
    stop_at=[0]
    def boundary(engine,address,size,unused):
        if address==stop_at[0]:engine.emu_stop()
    u.hook_add(unicorn.UC_HOOK_CODE,boundary)
    def run(start,end):
        stop_at[0]=end
        try:u.emu_start(start,STOP,count=100000)
        finally:stop_at[0]=0
        check(u.reg_read(a.UC_ARM_REG_PC)==end,'Native fragment reaches exact fixture boundary')
    ui,source,target,new_array,list_obj,descriptor,flags_desc= [DATA+i for i in (0x10000,0x11000,0x12000,0x13000,0x14000,0x15000,0x16000)]
    entries=struct.pack('<16H',123,3,456,2,123,2,123,3,789,2,123,3,456,1,123,2)
    def batch(offset=0):
        p.write(ui+0x3c,2);p.write(ui+0x5c,target);p.write(ui+0x60,16)
        u.mem_write(source,entries);u.mem_write(target,bytes(192))
        _,root=p.frame(12,[ui],at=DATA+0x4000)
        _,counter=p.frame(9,[0,int(bool(offset))],caller=MAIN+(0x387a98 if offset else 0x381dc4),at=DATA+0x4400)
        p.frame(25,[31,0,0,0,4],at=DATA+0x4800)
        for slots in range(4,8):p.frame(2,[22 if slots==4 else 0,0,0,0,slots,31],at=DATA+0x4800)
        p.write(counter+272,8);p.leave(counter)
        u.reg_write(a.UC_ARM_REG_CPSR,0x10);u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00)
        u.reg_write(REGS[4],ui);u.reg_write(REGS[6 if offset else 7],source)
        run(MAIN+(0x387b00 if offset else 0x3875bc),MAIN+(0x387bc4 if offset else 0x387680))
        p.leave(root);p.call('forge_onUpdate',[0])
        check(p.read(p.private('bonus_count'))==4 and p.read(p.private('generated_count'))==8 and p.read(p.private('summary_status'))==1,
              'Fixture reproduces r4 eight slots/four extras with duplicate IDs')
    def list_copy(array=target,capacity=16):
        p.write(descriptor,array);p.write(descriptor+4,capacity);p.write(list_obj+0x5c,capacity)
        p.write(flags_desc,source+128);p.write(flags_desc+4,0)
        p.write(ui+0x3c,2);_,update=p.frame(15,[ui],at=DATA+0x4000)
        p.native[MAIN+0x623c68]=0 # Item-icon refresh is outside this copy fixture.
        p.call(MAIN+0x623c08,[list_obj,descriptor,flags_desc]);p.leave(update);p.call('forge_onUpdate',[0])
    batch(32);list_copy()
    displayed=p.private('displayed');before=p.read(p.private('drops'))
    # Execute the ORIGINAL native quantity subtraction, then the native index
    # copy. No collection counts, item matching or regenerated rewards.
    u.reg_write(REGS[6],target+32+5*4);u.reg_write(REGS[4],1)
    run(MAIN+0x38a110,MAIN+0x38a11c);list_copy()
    check(p.read(p.private('drops'))==before and p.read(displayed+36)==0xf0,
          'Native quantity decrease retains eligible bonus slot without a capture fault')
    # Execute all four native emptying variants on distinct exact slots.
    for index,start,end,reg in ((4,0x389bc4,0x389bcc,4),(5,0x389cb0,0x389cb8,5),
                                (6,0x389e58,0x389e60,7),(7,0x38a164,0x38a16c,4)):
        u.reg_write(REGS[6 if start!=0x389e58 else 4],target+32+index*4)
        u.reg_write(REGS[reg],0)
        if start==0x389e58:u.reg_write(REGS[6],0)
        run(MAIN+start,MAIN+end);list_copy()
        check(not (p.read(displayed+36)&(1<<index)) and p.read(p.private('drops'))==before,
              'Native empty slot hides only that index; duplicate items remain distinct')
    check(p.read(p.private('expected_refreshes'))>=5 and p.read(p.private('bonus_count'))==4 and p.read(p.private('summary_status'))==1,
          'Expected collection refreshes retain completed generation totals')
    for refresh in range(8):list_copy()
    check(p.read(p.private('drops'))==before,'Eight copies of collected slots reproduce no false capture drops in r5')
    # This is the old exact-equality fault cause, not proof of the historical
    # eight events: the user screenshots did not retain per-event identities.
    for bad in (struct.pack('<HH',124,1),struct.pack('<HH',123,4),struct.pack('<HH',0,1),struct.pack('<HH',123,0)):
        batch(32);u.mem_write(target+32+7*4,bad);before=p.read(p.private('drops'));list_copy()
        check(p.read(p.private('drops'))>before and not p.read(displayed+12),
              'Changed ID, increased quantity and malformed empty pairs suppress display provenance and report faults')
    batch(32);list_copy(target+32,8)
    check(p.read(displayed+28)==list_obj+0x60 and p.read(displayed+36)==0xf0,
          'Native row/category subarray copy follows source-relative index into a new list row')
    # Delayed consumer regression: the same native list is refreshed twice
    # before Forge drains it. Earlier records must not reread the later bytes.
    def queued_copy(array,obj=list_obj,capacity=8):
        p.write(descriptor,array);p.write(descriptor+4,capacity);p.write(obj+0x5c,capacity)
        p.write(ui+0x3c,2);_,update=p.frame(15,[ui],at=DATA+0x4000)
        p.call(MAIN+0x623c08,[obj,descriptor,flags_desc]);p.leave(update)
    foreign=DATA+0x19000;other_list=DATA+0x1a000
    u.mem_write(foreign,struct.pack('<16H',*([777,1]*8)))
    batch();before=p.read(p.private('drops'))
    queued_copy(target);queued_copy(foreign);p.call('forge_onUpdate',[0])
    check(p.read(p.private('drops'))==before and not p.read(displayed+12),
          'Later unrelated refresh of same list clears only that list, without a false earlier-copy fault')
    batch();queued_copy(target);queued_copy(foreign,other_list);p.call('forge_onUpdate',[0])
    check(p.read(displayed+16)==list_obj and p.read(displayed+36)==0xf0,
          'Refresh of an unrelated list preserves the verified main list provenance')
    batch();queued_copy(target,capacity=48);p.call('forge_onUpdate',[0])
    check(p.read(displayed+28)==list_obj+0x60 and p.read(displayed+36)==0xf0,
          'Bounded eight-entry immutable chunks retain the 48-slot list prefix')
    before=p.read(p.private('drops'));queued_copy(target,capacity=49);p.call('forge_onUpdate',[0])
    check(p.read(p.private('drops'))>before and not p.read(displayed+12),
          'Over-capacity copy clears previous list provenance and reports capture failure')
    batch();queued_copy(target);p.call('forge_onUpdate',[0]);before=p.read(p.private('drops'))
    _,update=p.frame(15,[ui]);_,copy_frame=p.frame(14,[list_obj,descriptor,flags_desc],at=DATA+0x4400)
    p.fail_svc[6]=p.svc_calls[6]+2 # field check succeeds; immediate payload query fails.
    p.leave(copy_frame);p.leave(update);p.call('forge_onUpdate',[0]);p.fail_svc.pop(6)
    check(p.read(p.private('drops'))>before and not p.read(displayed+12),
          'Failed immutable payload capture clears previous provenance instead of reusing old bindings')
    # Observe the real state-1 relocation loops for both native capacities.
    relocation_cases=0
    for capacity,offset in itertools.product((16,48),(0,32)):
        batch(offset);p.write(ui+0x3c,1);_,update=p.frame(15,[ui],at=DATA+0x4000)
        u.mem_write(new_array,b'\xaa'*192)
        u.reg_write(REGS[8],ui);u.reg_write(REGS[4],new_array)
        run(MAIN+(0x384bf0 if capacity==16 else 0x384c7c),MAIN+(0x384c24 if capacity==16 else 0x384cb0))
        check(bytes(u.mem_read(new_array,64))==bytes(u.mem_read(target,64)),
              'Pinned reallocation loop preserves every entry by index')
        # Native memset/free are not executed; poison the freed old allocation
        # before leave to prove capture never dereferences it after reallocation.
        u.mem_write(new_array+64,bytes((capacity-16)*4));u.mem_write(target,b'\xdd'*192)
        p.write(ui+0x5c,new_array);p.write(ui+0x60,capacity);p.write(ui+0x3c,2)
        p.leave(update);p.call('forge_onUpdate',[0]);list_copy(new_array,capacity)
        check(p.read(displayed+28)==list_obj+0x60+offset and p.read(displayed+36)==0xf0,
              'State-1 remap joins exact old/new allocation and preserves category offset')
        check(p.read(p.private('summary_status'))==1 and p.read(p.private('bonus_count'))==4,
              'Relocation preserves completed totals')
        relocation_cases+=1
    # First initialization may have no old array. Only a same-UI nested
    # builder supersedes that pre-generation snapshot; it does not hide faults
    # in a different object's relocation or certify an incomplete new batch.
    p.write(ui+0x3c,1);p.write(ui+0x5c,0);p.write(ui+0x60,0)
    _,initial=p.frame(15,[ui],at=DATA+0x4c00);before=p.read(p.private('drops'))
    batch();p.leave(initial);p.call('forge_onUpdate',[0]);list_copy()
    check(p.read(p.private('drops'))==before and p.read(displayed+36)==0xf0,
          'Same-UI generation supersedes an unavailable empty preimage and retains verified new rewards')
    batch();p.write(ui+0x3c,1);_,initial=p.frame(15,[ui],at=DATA+0x4c00)
    _,empty_builder=p.frame(12,[ui],at=DATA+0x4000);p.leave(empty_builder)
    p.write(ui+0x3c,2);p.leave(initial);p.call('forge_onUpdate',[0])
    check(p.read(p.private('summary_status'))==2 and not p.read(p.private('observed')+12),
          'An incomplete replacement batch remains unavailable; old provenance is not adopted')
    batch();p.write(ui+0x3c,1);_,initial=p.frame(15,[ui],at=DATA+0x4c00)
    _,other_builder=p.frame(12,[ui+0x800],at=DATA+0x4000);p.leave(other_builder)
    p.write(target+7*4,999|(1<<16));p.write(ui+0x3c,2);before=p.read(p.private('drops'))
    p.leave(initial);p.call('forge_onUpdate',[0])
    check(p.read(p.private('drops'))>before,
          'Different-UI generation cannot suppress a genuine old-object relocation mismatch')
    p.tree={'Please do Better###pdb_panel':True,'Diagnostics###pdb_diagnostics':True}
    p.messages.clear();p.text.clear();p.call('forge_onImGuiRender')
    check(p.read(p.private('mapping_detail')+16)==1 and not any(fmt.startswith('Last mapping fault:') for fmt,state in p.text),
          'A relocation mismatch retains its exact fault route internally without diagnostic UI')
    # Guard the copies, not just the pointer. Failures never adopt foreign data.
    for failure in ('changed_copy','unmapped','over_capacity','short_capacity','stale_epoch','identity'):
        batch(32);p.write(ui+0x3c,1);_,update=p.frame(15,[ui],at=DATA+0x4000)
        u.mem_write(new_array,bytes(u.mem_read(target,64)))
        p.write(ui+0x5c,0xdead0000 if failure=='unmapped' else new_array)
        p.write(ui+0x60,49 if failure=='over_capacity' else 8 if failure=='short_capacity' else 48)
        if failure=='changed_copy':p.write(new_array+32+7*4,0)
        if failure=='identity':p.write(ui+0x5c,target) # Allocation failure: unchanged mapping is valid.
        if failure=='stale_epoch':
            _,nested=p.frame(12,[ui],at=DATA+0x4800);p.leave(nested)
        p.write(ui+0x3c,2);before=p.read(p.private('drops'));p.leave(update);p.call('forge_onUpdate',[0])
        if failure in ('identity','stale_epoch'):
            check(p.read(p.private('drops'))==before,'Unchanged allocation or old epoch cannot invent a copy fault')
        else:
            check(p.read(p.private('drops'))>before and not p.read(p.private('observed')+12),
                  'Invalid relocation clears live provenance and reports a genuine mapping fault')
    batch();list_copy();p.write(ui+0x3c,18);_,update=p.frame(15,[ui]);p.leave(update);p.call('forge_onUpdate',[0])
    check(not p.read(displayed+12) and p.read(p.private('summary_status'))==1 and p.read(p.private('bonus_count'))==4,
          'Screen exit hides provenance while retaining completed summary')
    batch();list_copy();_,dtor=p.frame(16,[ui]);p.leave(dtor);p.call('forge_onUpdate',[0])
    check(not p.read(displayed+12),'Destruction clears live provenance')
    # Original list-group address calculation proves 40-byte strides. These are
    # synthetic group tables, not proof of category-to-slot-FRAME identity.
    for group in range(16):
        p.write(list_obj+0x4c,group);u.reg_write(REGS[11],list_obj)
        run(MAIN+0x623c80,MAIN+0x623ca0)
        check(u.reg_read(REGS[1])==list_obj+group*0x28+0x16c and
              u.reg_read(REGS[9])==list_obj+group*0x28+0x160,'Native group root/item-node offsets use stride 0x28')
    holder,roots_a,roots_b,root_nodes,node_table= [DATA+i for i in (0x20000,0x21000,0x22000,0x23000,0x24000)]
    p.write(holder+0x298,2);p.write(holder+0xf8,roots_a);p.write(holder+0x294,roots_b)
    selected=[]
    def setter():selected.append((u.reg_read(REGS[0]),u.reg_read(REGS[1])));return 0
    p.native[MAIN+0xa4fb58]=setter
    for root in range(4):
        p.write((roots_a if root<2 else roots_b)+(root%2)*4,root_nodes+root*0x100)
        p.write(root_nodes+root*0x100+0xd8,node_table+root*64)
        for index in range(8):p.write(node_table+root*64+index*4,DATA+0x25000+root*0x100+index*16)
    for root,index in itertools.product(range(4),range(8)):
        p.call(MAIN+0x546f84,[holder,root,index,source])
        check(selected[-1]==(DATA+0x25000+root*0x100+index*16,source),'Native holder resolves both root tables and exact node index')
    p.write(root_nodes+0xd8,0);p.call(MAIN+0x546f84,[holder,0,7,source])
    check(selected[-1]==(0,source),'Absent native node table is not mistaken for geometry')
    for panel,diagnostics in itertools.product((False,True),repeat=2):
        p.tree={'Please do Better###pdb_panel':panel,'Diagnostics###pdb_diagnostics':diagnostics}
        p.messages.clear();p.text.clear();p.call('forge_onImGuiRender')
        check(p.tree_depth==0,'Compact panel balances both trees on every path')
        formats=[fmt for fmt,state in p.text]
        check(not any(any(raw in fmt for raw in ('Owned words','Executed checks','clearing events','UI update hits')) for fmt in formats),
              'Compact panel excludes raw counters and ownership masks')
        check(not any(fmt.startswith('Currently highlighted slots:') for fmt in formats),
              'Settings panel has no reward summaries or diagnostic rows')
    report={'checks':checks,'native_relocation_cases':relocation_cases,
            'native_group_stride_cases':16,'native_holder_index_cases':33,
            'main_sha256':recipe.binary.MAIN_SHA,'nro_sha256':recipe.sha(payload),
            'highlight':'Native frame tint; compiled frame mapping in highlight-tests.json',
            'limits':['Native copy/collection fragments execute; allocation, free and GUI refresh are fixtures',
                      'No GPU, emulator gameplay or natural-luck highlight test',
                      'Historical eight faults cannot be individually identified from screenshots']}
    recipe.write_json(recipe.OUT/'display-tests.json',report)
    print(f'PASS: {checks} compiled display-copy/collection/panel checks')


if __name__=='__main__':main()
