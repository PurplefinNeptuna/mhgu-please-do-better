from paths import MOD, SCRIPTS, FORGE, DEPS, PYTHON, CONTAINER_STORAGE, input_path
#!/usr/bin/env python3
"""Execute compiled copy taps and pinned counters. Fake item selection, no launch."""
import itertools
import struct
import unicorn
from unicorn import arm_const as a
from please_do_better_runtime_probe import Probe, MAIN, DATA, STACK, STOP, REGS, MASK
import please_do_better as recipe

ROUTES = [(21,0x3875bc,0x387680,7,0x5c,0,0x381dc4,0),
          (22,0x3878e0,0x3879a4,7,0x5c,0,0x381dc4,0),
          (23,0x387b00,0x387bc4,6,0x5c,32,0x387a98,1),
          (24,0x388084,0x388144,5,0x64,32,0x388084,0)]


def main():
    image,_=recipe.binary.main_image((recipe.input_path('main')).read_bytes())
    payload=(recipe.WORK/'native/plugin.nro').read_bytes()
    p=Probe(image,payload);p.call('forge_onInit');u=p.u
    stop_at=[0]
    def boundary(engine,address,size,unused):
        if address==stop_at[0]:engine.emu_stop()
    u.hook_add(unicorn.UC_HOOK_CODE,boundary)
    def run(start,end):
        # Explicit boundary hook avoids reusing a cached fixture block whose
        # earlier emu_start() had a different stop address.
        stop_at[0]=end
        try:u.emu_start(start,STOP,count=100000)
        finally:stop_at[0]=0
    checks=0
    def check(ok,label):
        nonlocal checks
        assert ok,label;checks+=1
    ui,source,target,container=DATA+0x10000,DATA+0x11000,DATA+0x12000,DATA+0x13000
    # Each compiled gateway must reproduce the two displaced instructions for
    # every NZCVQ/GE combination, both stack alignments and all VFP registers.
    preservation=0
    for kind,start,end,reg,field,offset,caller,category in ROUTES:
        p.write(ui+field,target);p.write(source,123,'<H')
        for flags,ge,alignment in itertools.product(range(32),range(16),(0,4)):
            values=[0x12300000+i for i in range(13)];values[4]=ui;values[reg]=source
            cpsr=0x10|(flags<<27)|(ge<<16);sp=STACK+0xff00-alignment;lr=STOP+64
            vfp=[0x1234567800000000+i for i in range(32)]
            for r,v in zip(REGS,values):u.reg_write(r,v)
            for i,v in enumerate(vfp):u.reg_write(getattr(a,f'UC_ARM_REG_D{i}'),v)
            u.reg_write(a.UC_ARM_REG_FPSCR,0x01000000);u.reg_write(a.UC_ARM_REG_CPSR,cpsr)
            u.reg_write(a.UC_ARM_REG_SP,sp);u.reg_write(a.UC_ARM_REG_LR,lr)
            run(MAIN+start,MAIN+start+8)
            expected=values[:];expected[0]=target;expected[1]=123
            check(u.reg_read(a.UC_ARM_REG_PC)==MAIN+start+8 and [u.reg_read(r) for r in REGS]==expected,'Copy tap native continuation and GPR outputs')
            check(u.reg_read(a.UC_ARM_REG_CPSR)&MASK==cpsr&MASK and u.reg_read(a.UC_ARM_REG_SP)==sp and u.reg_read(a.UC_ARM_REG_LR)==lr,'Copy tap preserves NZCVQ/GE/SP/LR')
            check([u.reg_read(getattr(a,f'UC_ARM_REG_D{i}')) for i in range(32)]==vfp and u.reg_read(a.UC_ARM_REG_FPSCR)==0x01000000,'Copy tap preserves VFP/FPSCR')
            preservation+=1
    initial_cases=0
    for first,flags,ge,alignment in itertools.product((0,2,7,8,9),range(32),range(16),(0,4)):
        values=[31]+[0x12300000+i for i in range(1,13)];values[4]=first
        cpsr=0x10|(flags<<27)|(ge<<16);sp=STACK+0xff00-alignment;lr=STOP+64
        vfp=[0x8765432100000000+i for i in range(32)]
        for r,v in zip(REGS,values):u.reg_write(r,v)
        for i,v in enumerate(vfp):u.reg_write(getattr(a,f'UC_ARM_REG_D{i}'),v)
        u.reg_write(a.UC_ARM_REG_FPSCR,0x01000000);u.reg_write(a.UC_ARM_REG_CPSR,cpsr)
        u.reg_write(a.UC_ARM_REG_SP,sp);u.reg_write(a.UC_ARM_REG_LR,lr)
        run(MAIN+0x3820b4,MAIN+0x3820bc)
        expected=values[:];expected[5]=31
        result=(first-7)&0xffffffff
        nzcv=(result&0x80000000)|(0x40000000 if not result else 0)|(0x20000000 if first>=7 else 0)
        check(u.reg_read(a.UC_ARM_REG_PC)==MAIN+0x3820bc and [u.reg_read(r) for r in REGS]==expected,'Initial-count tap replays MOV and native continuation')
        check(u.reg_read(a.UC_ARM_REG_CPSR)&MASK==((cpsr&0x080f0000)|nzcv) and u.reg_read(a.UC_ARM_REG_SP)==sp and u.reg_read(a.UC_ARM_REG_LR)==lr,'Initial-count CMP preserves Q/GE/SP/LR and computes native NZCV')
        check([u.reg_read(getattr(a,f'UC_ARM_REG_D{i}')) for i in range(32)]==vfp and u.reg_read(a.UC_ARM_REG_FPSCR)==0x01000000,'Initial-count tap preserves VFP/FPSCR')
        initial_cases+=1
    # Set up exact native counter/selector globals, as in the RNG equivalence
    # fixtures. These external quest/meal/RNG inputs are fixture callbacks.
    festa,skills,rem=DATA+0x18000,DATA+0x19000,DATA+0x1a000
    literals=[(0x382100,0x381ff8),(0x382104,0x382014),(0x38210c,0x382034),(0x382108,0x382048),
              (0x382110,0x38205c),(0x382114,0x38209c),(0x382118,0x3820c4),(0x382368,0x3822c4),
              (0x382fe0,0x382ea8),(0x382fe4,0x382ecc),(0x382fe8,0x382eec),(0x382fec,0x382f0c),
              (0x382ff0,0x382f2c),(0x382ff4,0x382f4c),(0x382ff8,0x382f6c)]
    for literal,site in literals:
        cell=site+8+struct.unpack_from('<i',image,literal)[0]
        p.write(MAIN+cell,MAIN+struct.unpack_from('<I',image,cell)[0])
    p.write(festa+4+0x188,skills);p.write(rem+4,1,'<B');p.write(container,source)
    p.native.update({MAIN+0x3ae5b8:0,MAIN+0x3a3284:0,MAIN+0x3a3370:0,
                     MAIN+0x275a30:festa,MAIN+0x26fe10:0,MAIN+0x3c6124:rem,MAIN+0x37c500:DATA+0x1d000})
    def rng():
        result=p.rolls[len(p.rng)];p.rng.append(result);return result
    p.native[MAIN+0x3f8344]=rng
    def items(n):return struct.pack('<16H',*[v for j in range(8) for v in ((123 if j%3 else 456,j%2+1) if j<n else (0,0))])
    selected=[]
    def generate():
        n=u.reg_read(REGS[3]);selected.append(n);u.mem_write(source,items(n))
        return 0xdeadbeef # Secondary builder returns void; deliberately not n.
    p.native[MAIN+0x38211c]=generate
    table=MAIN+struct.unpack_from('<I',image,0x183c89c)[0]
    batch_cases=0
    def native_count(route,tier,first,rolls,forced=False,missing=False):
        kind,start,end,reg,field,offset,caller,category=route
        p.call('_ZN3pdb13request_forceEb',[int(forced)])
        p.write(ui+field,target);p.write(ui+0x3c,18);u.mem_write(source,bytes(32));u.mem_write(target,b'\xaa'*96)
        _,root=p.frame(12,[ui],at=DATA+0x4000)
        p.write(table+category,first,'<B');u.mem_write(skills+0x3dc,bytes(64))
        skill={8:255,16:254,22:None,25:253,28:252,31:251}[tier]
        if skill is not None:p.write(skills+0x3dc+(skill//32)*4,1<<(skill%32))
        p.rolls=rolls;p.rng=[];selected.clear()
        if not missing:
            u.reg_write(a.UC_ARM_REG_CPSR,0x10);u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00)
            u.reg_write(a.UC_ARM_REG_LR,MAIN+caller)
            for r,v in zip(REGS,[0,container,8] if kind==24 else [0,category]):u.reg_write(r,v)
            try:
                run(MAIN+(0x382e1c if kind==24 else 0x381fec),MAIN+caller)
            except Exception as error:
                raise AssertionError(f'Counter fixture {kind=} {tier=} {first=} {rolls=} PC={u.reg_read(a.UC_ARM_REG_PC):x} regs={[hex(u.reg_read(r)) for r in REGS]}') from error
            check(u.reg_read(a.UC_ARM_REG_PC)==MAIN+caller,'Real counter returns through compiled paired hook to verified copy caller')
            n=selected[0] if kind==24 and selected else 0 if kind==24 else u.reg_read(REGS[0])
            if kind!=24:u.mem_write(source,items(n))
        else:n=4;u.mem_write(source,items(n))
        return root,n
    def native_copy(route):
        kind,start,end,reg,field,offset,caller,category=route
        u.reg_write(a.UC_ARM_REG_CPSR,0x10);u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00)
        u.reg_write(REGS[4],ui);u.reg_write(REGS[reg],source)
        run(MAIN+start,MAIN+end)
        check(u.reg_read(a.UC_ARM_REG_PC)==MAIN+end and bytes(u.mem_read(target+offset,32))==bytes(u.mem_read(source,32)),'Full native copy fragment including compiled capture preserves item order/duplicates')
    for route,tier,first,rolls in itertools.product(ROUTES,(8,16,22,25,28,31),(0,2,7,8),
                                                  ([0]*12,[22,0,31]+[31]*9,[31]*12)):
        root,n=native_count(route,tier,first,rolls);native_copy(route);p.leave(root);p.call('forge_onUpdate',[0])
        guaranteed=2 if route[0]==24 else first
        normal=guaranteed
        for roll in p.rng:
            if normal>=8 or (roll&31)>=22:break
            normal+=1
        normal=max(1,min(8,normal));expected=max(0,n-normal) if tier>22 else 0
        check(p.read(p.private('summary_status'))==1 and p.read(p.private('latest_tier'))==tier,'Complete native count/copy path records every tier, including zero bonus and guaranteed cap')
        check(p.read(p.private('generated_count'))==n and p.read(p.private('bonus_count'))==expected,'Observed slots agree with same-roll normal counterfactual')
        batch_cases+=1
    # Reproduce the user's diagnostic pattern: generation hook absent, forced
    # positive threshold observed, then copy publication and state 18 clearing.
    root,n=native_count(ROUTES[2],22,2,[22,0,31]+[31]*9,forced=True);native_copy(ROUTES[2]);p.leave(root);p.call('forge_onUpdate',[0])
    check(p.read(p.private('completed_generations'))==0 and p.read(p.private('latest_tier'))==31 and p.read(p.private('bonus_count'))==2,'Forced batch publishes extras without generator observation')
    _,frame=p.frame(15,[ui]);p.leave(frame);p.call('forge_onUpdate',[0])
    check(p.read(p.private('summary_status'))==1 and p.read(p.private('bonus_count'))==2 and p.read(p.private('last_ui_state'))==18,'State 18 cannot erase completed diagnostic totals')
    for failure in ('missing_count','changed_destination','bad_prefix','missing_first','missing_comparison',
                    'source_query','destination_query','unknown_caller','empty_table'):
        route=ROUTES[2] if failure!='empty_table' else ROUTES[3]
        saved=None
        if failure in ('missing_first','missing_comparison'):
            start=0x3820b4 if failure=='missing_first' else 0x3820d0
            saved=bytes(u.mem_read(MAIN+start,8));u.mem_write(MAIN+start,image[start:start+8]);u.ctl_remove_cache(MAIN+start,MAIN+start+8)
        if failure=='empty_table':p.native[MAIN+0x3c6124]=0
        count_route=(*route[:6],0x387a9c,route[7]) if failure=='unknown_caller' else route
        root,n=native_count(count_route,31,2,[22,0,31]+[31]*9,missing=failure=='missing_count')
        if saved is not None:u.mem_write(MAIN+start,saved);u.ctl_remove_cache(MAIN+start,MAIN+start+8)
        if failure=='bad_prefix':p.write(source+4,0)
        if failure=='source_query':p.fail_svc[6]=p.svc_calls[6]+2 # field query then source snapshot query
        native_copy(route)
        if failure=='changed_destination':p.write(target+route[5]+8,0)
        if failure=='destination_query':p.fail_svc[6]=p.svc_calls[6]+1
        p.leave(root);p.call('forge_onUpdate',[0])
        check(p.read(p.private('summary_status'))==(1 if failure=='empty_table' else 2),'Missing count/taps, malformed prefix or changed destination never reports complete zero-bonus coverage')
        if failure!='empty_table':
            p.tree=True;p.messages.clear();p.call('forge_onImGuiRender')
            check(not any('Extra-slot total' in x for x in p.messages),'Incomplete observation remains guarded internally and emits no reward summary UI')
        if failure=='empty_table':
            check(p.read(p.private('generated_count'))==p.read(p.private('bonus_count'))==0,'Absent native table yields a verified empty copied batch')
            p.native[MAIN+0x3c6124]=rem
    # No renderer, UI balance and explicit unavailable wording are compiled.
    p.tree=True;p.call('forge_onImGuiRender');check(p.tree_depth==0,'Diagnostics tree balances every opened row')
    p.call('forge_onImGuiFreeRender');check(not p.draws,'No drawing without verified bindings/geometry/presentation')
    report={'checks':checks,'copy_gateway_preservation_cases':preservation,'initial_gateway_preservation_cases':initial_cases,'native_count_copy_batches':batch_cases,
            'nro_sha256':recipe.sha(payload),'runtime':'NOT RUN',
            'limits':['Fake kernel and UI; reward item selection supplies controlled prefix fixtures',
                      'Real native counters, skill selector, copy fragments and compiled gateways execute; full UI builder is scoped by fixture entry/leave',
                      'No Eden translation/multicore proof or gameplay observation; highlight GPU alignment remains pending']}
    recipe.write_json(recipe.OUT/'observation-tests.json',report)
    print(f'PASS: {checks} observation checks; {preservation} copy gateway cases; {batch_cases} native count/copy batches')


if __name__=='__main__':main()
