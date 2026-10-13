#!/usr/bin/env python3
"""Execute compiled quantity changes and native collection with fake memory only."""
import struct
import unicorn
from unicorn import arm_const as a
import please_do_better as recipe
from please_do_better_runtime_probe import Probe, MAIN, DATA, STACK, STOP, REGS

def main():
    image,_=recipe.binary.main_image(recipe.input_path('main').read_bytes())
    payload=(recipe.WORK/'native/plugin.nro').read_bytes()
    checks=0
    def check(ok,label):
        nonlocal checks
        assert ok,label
        checks+=1
    ui,array,secondary,plunder,source=[DATA+i for i in (0x10000,0x12000,0x13000,0x14000,0x15000)]
    def setup(force=False,multiplier=5,count=48):
        p=Probe(image,payload);p.call('forge_onInit');p.tree=True
        p.edits={'Force Miraculous Luck###pdb_force':force,'Reward multiplier###pdb_multiplier':multiplier}
        p.call('forge_onImGuiRender')
        p.write(ui+0x5c,array);p.write(ui+0x60,count);p.write(ui+0x3c,2)
        for offset,target in ((0x64,secondary),(0x6c,plunder),(0x74,plunder+0x100)):
            p.write(ui+offset,target);p.write(ui+offset+4,48)
            p.u.mem_write(target,b'\x23\x01\x03\x00'*48)
        p.u.mem_write(array,bytes(192)+b'Q'*32)
        check(p.read(p.private('mode'))==int(force)+2*(multiplier-1),'Independent integer slider publication')
        return p
    def begin(p):return p.frame(12,[ui],at=DATA+0x4000)[1]
    def records(count):return [(123+i%3,i%7+1) for i in range(count)]
    def put(p,items):p.u.mem_write(array,b''.join(struct.pack('<HH',*r) for r in items))
    def get(p,count):return [struct.unpack('<HH',p.u.mem_read(array+i*4,4)) for i in range(count)]
    primary='savedata:/please_do_better.ini'
    for bits in range(10):
        multiplier=bits//2+1
        p=setup(bool(bits&1),multiplier);p.save_available=True;p.button=True;p.call('forge_onImGuiRender')
        expected=f'force_miraculous={bits&1}\nreward_multiplier={multiplier}\n'.encode()
        check(p.files[primary]==expected and not p.mounts and not p.handles and not p.guard,'Compiled two-setting save balances storage')
        restarted=Probe(image,payload);restarted.call('forge_onInit');restarted.save_available=True;restarted.files=p.files.copy()
        restarted.call('forge_onImGuiFreeRender')
        check(restarted.read(restarted.private('mode'))==bits,'Compiled restart restores all ten setting combinations')
    for force in (0,1):
        for doubled in (0,1):
            for legacy in (b'',b'version=2\n'):
                p=Probe(image,payload);p.call('forge_onInit');p.save_available=True
                record=legacy+f'force_miraculous={force}\ndouble_quantity={doubled}\n'.encode()
                p.files[primary]=record;p.call('forge_onImGuiFreeRender')
                check(p.read(p.private('mode'))==0 and p.files[primary]==record,
                      'Old configs use natural 1x defaults without automatic rewrite')
    for value,expected in ((-10,1),(0,1),(6,5),(99,5)):
        p=setup();p.edits={'Reward multiplier###pdb_multiplier':value};p.call('forge_onImGuiRender')
        check(p.read(p.private('mode'))==2*(expected-1),'Typed slider input clamped to 1..5 before publication')
    for fail_write,fail_commit in ((1,0),(0,1)):
        p=setup(True,5);p.save_available=True;p.fail_write=fail_write;p.fail_commit=fail_commit
        p.button=True;p.call('forge_onImGuiRender')
        check(p.read(p.private('mode'))==9 and not p.mounts and not p.handles and not p.guard,
              'Failed compiled save retains both session choices and releases storage')
    for force in (False,True):
        for multiplier in range(1,6):
            for count in (16,48):
                p=setup(force,multiplier,count);root=begin(p);items=records(count);items[3]=(0,0);put(p,items)
                before=[bytes(p.u.mem_read(t,192)) for t in (secondary,plunder,plunder+0x100)]
                p.leave(root)
                expected=[(item,amount*multiplier) for item,amount in items]
                check(get(p,count)==expected,'All occupied first-screen slots multiplied, IDs/empty slots retained')
                check(bytes(p.u.mem_read(array+192,32))==b'Q'*32,'Neighbor sentinel unchanged')
                check(before==[bytes(p.u.mem_read(t,192)) for t in (secondary,plunder,plunder+0x100)],'All secondary/plunder arrays unchanged')
                for _ in range(3):p.call('forge_onUpdate',[0]);p.call('forge_onImGuiRender');p.call('forge_onImGuiFreeRender')
                check(get(p,count)==expected,'Repeated UI/presentation never reapplies multiplier')
                again=begin(p);p.leave(again)
                check(get(p,count)==expected,'No new native generation retains old rewards')
                p.u.mem_write(array,bytes(count*4));next_root=begin(p);put(p,items);p.leave(next_root)
                check(get(p,count)==expected,'Next fresh generation multiplies once')
    for initial in range(1,6):
        subsequent=initial%5+1
        p=setup(False,initial);root=begin(p);items=records(48);put(p,items)
        p.edits={'Reward multiplier###pdb_multiplier':subsequent};p.call('forge_onImGuiRender');p.leave(root)
        check(get(p,48)==[(i,n*initial) for i,n in items],'Mid-generation slider edit uses latched setting')
        p=setup(False,initial)
        _,outer=p.frame(15,[ui],at=DATA+0x5000)
        p.edits={'Reward multiplier###pdb_multiplier':subsequent};p.call('forge_onImGuiRender')
        root=begin(p);put(p,items);p.leave(root);p.leave(outer)
        check(get(p,48)==[(i,n*initial) for i,n in items],'Nested builder inherits complete outer-generation mode')
    for defect in ('overflow','empty_amount','empty_item','readonly','unmapped','count','pointer','alias','unaligned'):
        p=setup();root=begin(p);items=records(48)
        if defect=='overflow':items[47]=(123,6554)
        if defect=='empty_amount':items[47]=(123,0)
        if defect=='empty_item':items[47]=(0,2)
        put(p,items);before=bytes(p.u.mem_read(array,192))
        if defect=='readonly':p.regions=[(s,n,1 if s==DATA else perm) for s,n,perm in p.regions]
        if defect=='unmapped':p.regions=[r for r in p.regions if r[0]!=DATA]
        if defect=='count':p.write(ui+0x60,49)
        if defect=='pointer':p.write(ui+0x5c,array+4)
        if defect=='alias':p.write(ui+0x64,array+4)
        if defect=='unaligned':p.write(ui+0x5c,array+1)
        p.leave(root);check(bytes(p.u.mem_read(array,192))==before,'Preflight failure has no partial writes: '+defect)
        for _ in range(3):p.call('forge_onUpdate',[0])
        check(sum('Multiplier skipped' in fmt for fmt,_ in p.log_records)==1,'Fault log emitted once: '+defect)
    # Original native A-copy observations keep the same Luck mask at every
    # multiplier. Multiply live values and snapshots before publication.
    for multiplier in range(1,6):
        p=setup(True,multiplier);u=p.u;root=begin(p);entries=records(8)
        u.mem_write(source,b''.join(struct.pack('<HH',*r) for r in entries))
        _,counter=p.frame(9,[0,0],caller=MAIN+0x381dc4,at=DATA+0x4400)
        p.frame(25,[31,0,0,0,4],at=DATA+0x4800)
        for slots in range(4,8):p.frame(2,[22 if slots==4 else 0,0,0,0,slots,31],at=DATA+0x4800)
        p.write(counter+272,8);p.leave(counter)
        u.reg_write(a.UC_ARM_REG_CPSR,0x10);u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00)
        u.reg_write(REGS[4],ui);u.reg_write(REGS[7],source)
        u.emu_start(MAIN+0x3875bc,MAIN+0x387680,count=10000)
        p.leave(root);p.call('forge_onUpdate',[0])
        check(get(p,8)==[(i,n*multiplier) for i,n in entries],'Native copy keeps multiplied first-screen records')
        check(p.read(p.private('bonus_count'))==4 and p.read(p.private('summary_status'))==1,'Multiplied snapshots retain four Luck bonus slots')
        check(not p.read(p.private('quantity_faults')),'Known snapshots pass original-value validation')
    # Native enqueue reads a signed quantity and appends one item ID per unit.
    # Stub only item metadata; execute the original game's enqueue instructions.
    save,itemdata,queue=DATA+0x20000,DATA+0x23000,DATA+0x24000
    # main_image verifies original NSO bytes but leaves image-relative GOT
    # pointers unrelocated. Supply only the singleton roots used by these bodies.
    def global_root(literal,load,value):
        slot=MAIN+load+8+p.read(MAIN+literal,'<i')
        p.write(slot,value)
    global_root(0x3c6d3c,0x3c6c84,DATA+0x25000)
    p.write(DATA+0x25000,DATA+0x26000)
    p.native[MAIN+0x194228]=itemdata;p.write(itemdata+0x16,1,'<B');p.write(save+0xb08,queue)
    for multiplier in range(1,6):
      for initial,quantity in ((0,1),(0,3),(147,2),(150,1)):
        expected=min(150,initial+quantity*multiplier)
        p.write(save+0xb16,initial,'<B');u.mem_write(queue,b'\xAA'*304)
        p.write(source,123,'<H');p.write(source+2,quantity*multiplier,'<H')
        result=p.call(MAIN+0x3c6c6c,[save,source,0])
        check(result==1 and p.read(save+0xb16,'<B')==expected,'Native appraisal count follows multiplied quantity and 150 cap')
        check(bytes(u.mem_read(queue+initial*2,(expected-initial)*2))==struct.pack('<H',123)*(expected-initial),'Each appended charm retains item ID')
        check(bytes(u.mem_read(queue+300,4))==b'\xAA'*4,'Appraisal queue sentinel preserved')
    # Original Send-to-Box caller forwards the full multiplied signed quantity;
    # fake the inventory service's remaining count to exercise its native
    # complete/partial/full-storage branches, without touching any real save.
    global_root(0x38a3f4,0x38a2f4,DATA+0x25000)
    global_root(0x38a3f8,0x38a328,DATA+0x25000)
    global_root(0x38a3fc,0x38a33c,DATA+0x27000)
    p.write(DATA+0x27000,0xbaf,'<H')
    received=[]
    for available,leftover in ((True,0),(True,2),(False,6)):
        p.write(source,123,'<H');p.write(source+2,6,'<H');received.clear()
        p.native[MAIN+0x199390]=int(available)
        def receive():
            received.append((u.reg_read(REGS[1]),u.reg_read(REGS[2])))
            remaining=p.read(u.reg_read(a.UC_ARM_REG_SP))
            p.write(remaining,leftover)
            return 1
        p.native[MAIN+0x19945c]=receive;p.native[MAIN+0x54f260]=0
        p.call(MAIN+0x38a2dc,[ui,source])
        current=struct.unpack('<HH',u.mem_read(source,4))
        check(received==([(123,6)] if available else []),'Box service receives multiplied quantity only when storage is available')
        check(current==((123,leftover) if leftover else (0,0)),'Native box caller retains partial/full-capacity leftovers')
    # Execute the original manual-collection fragment through its native
    # capacity decision and remaining-quantity stores. Inventory/audio services
    # are recording fixtures; all branching and halfword writes are game code.
    global_root(0x38a190,0x389b68,DATA+0x25000)
    global_root(0x38a194,0x389b80,DATA+0x25000)
    global_root(0x38a19c,0x38a014,DATA+0x25000)
    global_root(0x38a1ac,0x38a038,DATA+0x27000)
    global_root(0x38a1a0,0x38a08c,DATA+0x27000)
    p.write(itemdata+0x16,0,'<B')
    def receive_pouch():
        received.append((u.reg_read(REGS[1]),u.reg_read(REGS[2])))
        return 0
    p.native[MAIN+0x19b7fc]=receive_pouch
    boundary=MAIN+0x389bd0
    def stop(engine,address,size,unused):
        if address==boundary:engine.emu_stop()
    handle=u.hook_add(unicorn.UC_HOOK_CODE,stop)
    for capacity,leftover,quantity in ((9,0,6),(2,4,2),(0,6,0),(0xffffffff,6,0)):
        p.write(source,123,'<H');p.write(source+2,6,'<H');received.clear()
        p.native[MAIN+0x19c58c]=capacity
        u.reg_write(a.UC_ARM_REG_CPSR,0x10);u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00)
        u.reg_write(REGS[6],source);u.reg_write(REGS[8],ui)
        u.emu_start(MAIN+0x389b60,STOP,count=10000)
        check(u.reg_read(a.UC_ARM_REG_PC)==boundary,'Native pouch fragment reaches completion boundary')
        check(received==([(123,quantity)] if quantity else []),'Native pouch service receives only fitting multiplied quantity')
        check(struct.unpack('<HH',u.mem_read(source,4))==((123,leftover) if leftover else (0,0)),'Native pouch caller retains uncollected remainder')
    u.hook_del(handle)
    recipe.write_json(recipe.OUT/'quantity-tests.json',{'checks':checks,'nro_sha256':recipe.sha(payload),
        'scope':'Compiled Switch multiplier, atomic settings, native copy/attribution, original appraisal queue and pouch/box callers with recording services',
        'runtime':'NOT RUN','limits':['Game inventory/appraisal UI and platform acceptance remain manual','Original appraisal queue cap is 150']})
    print(f'PASS: {checks} quantity/native appraisal checks; gameplay pending')
if __name__=='__main__':main()
