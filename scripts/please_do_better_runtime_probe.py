from paths import MOD, SCRIPTS, FORGE, DEPS, PYTHON, CONTAINER_STORAGE, input_path
#!/usr/bin/env python3
"""Compiled startup/gateway fixtures; fake kernel, no game launch or disk I/O."""
import itertools
import json
import re
import struct
from damage_numbers_sdk_tls_probe import sdk_image
import unicorn
from unicorn import arm_const as a
import please_do_better as recipe
from mhgu_binary import Nro

MAIN, MODULE, DATA, STACK, STOP = 0x04000000, 0x10000000, 0x30000000, 0x30100000, 0x30200000
REGS = [getattr(a, f'UC_ARM_REG_R{i}') for i in range(13)]
MASK = 0xf80f0000
SDK_IMAGE = sdk_image()


class Probe:
    def __init__(self, image, payload, title=True, conflict=None, fail_flush=0,fail_svc=None):
        self.u = u = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        u.ctl_set_cpu_model(a.UC_CPU_ARM_MAX)
        u.reg_write(a.UC_ARM_REG_C1_C0_2, 0xf00000)
        u.reg_write(a.UC_ARM_REG_FPEXC, 0x40000000)
        self.nro = n = Nro(payload)
        self.regions = [(MAIN, 0x2400000, 5), (MODULE, (len(payload)+n.u32(56)+4095)&~4095, 7),
                        (DATA, 0x210000, 7), (0x32000000, 0x20000, 5)]
        for start, size, _ in self.regions: u.mem_map(start, size)
        u.mem_write(MAIN, image); u.mem_write(MODULE, payload)
        u.mem_map(0x60000000,(len(SDK_IMAGE)+4095)&~4095);u.mem_write(0x60000000,SDK_IMAGE)
        self.symbols = {name: int(at,16) for at,_,name in re.findall(
            r'^([0-9a-f]+)\s+(\w)\s+(\S+)$', (recipe.WORK/'native/symbols.txt').read_text(), re.M)}
        self.imports = {0x32000000+i*16: name.decode() for i,(name,e,*_) in enumerate(n.symbols) if name and not e[5]}
        imports = {name: at for at,name in self.imports.items()}
        for addr, size in [(n.tags.get(17,0),n.tags.get(18,0)),(n.tags.get(23,0),n.tags.get(2,0))]:
            for at in range(addr,addr+size,8):
                target,info = struct.unpack_from('<II',payload,at); kind=info&255
                addend=self.read(MODULE+target); name,e,*_=n.symbols[info>>8]
                if kind==23: value=MODULE+addend
                else:
                    value=MODULE+e[1] if e[5] else imports[name.decode()]
                    if kind==2:value+=addend
                self.write(MODULE+target,value)
        self.title=title; self.flushes=0; self.fail_flush=fail_flush; self.allocations=0; self.tls_allocations=0
        self.fail_svc=fail_svc or {};self.svc_calls={};self.closes=0
        self.aliases=[]; self.thread=0; self.tree=False; self.tree_depth=0; self.edits={}; self.messages=[];self.logs=[];self.log_records=[]
        self.skill_calls=0; self.scope_entries=[]; self.fs_calls=0;self.text=[]
        self.save_available=False;self.mounts=0;self.handles={};self.files={};self.paths=[];self.commits=0
        self.fail_commit=0;self.fail_write=0;self.writes=0;self.guard=0;self.button=False
        self.read_corrupt=False
        self.singleton=0;self.draws=[];self.clips=[];self.clip_history=[];self.time=0;self.draw_enabled=True
        self.native={};self.rolls=[];self.rng=[];self.generated=[]
        if conflict:self.write(MAIN+conflict,0xe3a00001)
        u.hook_add(unicorn.UC_HOOK_CODE,self.trace)
        u.hook_add(unicorn.UC_HOOK_MEM_WRITE,self.mirror)
        u.hook_add(unicorn.UC_HOOK_INTR,self.svc)
    def address(self,name):return MODULE+self.symbols[name]
    def private(self,name):return self.address(f'_ZN3pdbL{len(name)}{name}E')
    def read(self,addr,fmt='<I'):return struct.unpack(fmt,self.u.mem_read(addr,struct.calcsize(fmt)))[0]
    def write(self,addr,value,fmt='<I'):self.u.mem_write(addr,struct.pack(fmt,value))
    def string(self,addr):return bytes(self.u.mem_read(addr,1024)).split(b'\0',1)[0].decode()
    def ret(self,value=0):self.u.reg_write(REGS[0],value);self.u.reg_write(a.UC_ARM_REG_PC,self.u.reg_read(a.UC_ARM_REG_LR))
    def mirror(self,u,access,addr,size,value,_):
        for owner,slave in self.aliases:
            if owner<=addr<owner+4096:u.mem_write(slave+addr-owner,value.to_bytes(size,'little'));return
    def svc(self,u,interrupt,_):
        assert interrupt==2
        pc=u.reg_read(a.UC_ARM_REG_PC);op=self.read(pc-4)&0xffffff
        self.svc_calls[op]=self.svc_calls.get(op,0)+1
        failing=self.svc_calls[op]==self.fail_svc.get(op)
        r=[u.reg_read(x) for x in REGS]
        if op==6:
            addr=r[2]+(r[3]<<32)
            region=next(((s,n,3,p) for s,n,p in self.regions if s<=addr<s+n),None)
            if region is None:
                end=min([s for s,n,p in self.regions if addr<s<0x50010000]+[0x50010000])
                region=(addr,end-addr if 0x50000000<=addr<0x50010000 else 4096,0,0)
            s,n,t,p=region;u.mem_write(r[0],struct.pack('<QQ6I',s,n,t,0,p,0,0,0));u.reg_write(REGS[1],0)
        elif op==0x29:
            values={18:0x0100770008dd8000 if self.title else 0,12:0x50000000,13:0x10000,
                    2:0x51000000,3:0x10000,4:0x52000000,5:0x10000}
            value=values[r[1]];u.reg_write(REGS[1],value&0xffffffff);u.reg_write(REGS[2],value>>32)
        elif op==0x4b:
            assert r[2:4]==[4096,0];self.allocations+=1;u.reg_write(REGS[1],7)
        elif op==0x4c:
            assert r[0]==7 and r[3:6]==[0,4096,0]
            if failing:pass
            elif r[1]<2:
                assert r[6]==(3 if r[1]==0 else 5)
                u.mem_map(r[2],4096);self.regions.append((r[2],4096,r[6]))
                if r[1]==0:self.owner=r[2]
                else:self.aliases.append((self.owner,r[2]))
            else:
                self.regions=[x for x in self.regions if x[0]!=r[2]];u.mem_unmap(r[2],4096)
                self.aliases=[x for x in self.aliases if r[2] not in x]
        elif op==0x5f:
            assert r[0]==0xffff8001 and r[3]==0 and r[4]==0
            self.flushes+=1
        elif op==0x16:self.closes+=1
        else:raise AssertionError(f'Unexpected SVC {op:x}')
        u.reg_write(REGS[0],99 if failing or (op==0x5f and self.flushes==self.fail_flush) else 0)
    def trace(self,u,addr,size,_):
        if addr==STOP:u.emu_stop();return
        if addr==MAIN+0xe0da0:self.skill_calls+=1
        if addr in self.native:
            result=self.native[addr]
            if callable(result):result=result()
            self.ret(result);return
        if addr not in self.imports:return
        name=self.imports[addr];r=[u.reg_read(x) for x in REGS]
        if name=='forge_mem_getMainTextAddr':self.ret(MAIN)
        elif name=='nnosAllocateTlsSlot':self.tls_allocations+=1;self.write(r[0],17);self.ret()
        elif name in ('nnosGetTlsValue','nnosSetTlsValue','_ZN2nn2os16GetCurrentThreadEv'):
            if name!='_ZN2nn2os16GetCurrentThreadEv':assert r[0]==17
            # Execute pinned SDK callees (C exports tail-call via SDK PLT).
            # They preserve GE and the
            # setter has a void ABI with a nonzero address left in r0.
            self.write(DATA+0x501fc,DATA+0x51000+0x1000*self.thread)
            u.reg_write(a.UC_ARM_REG_C13_C0_3,DATA+0x50000)
            u.reg_write(a.UC_ARM_REG_PC,0x60000000+({'nnosGetTlsValue':0x9d7f8,'nnosSetTlsValue':0x9d80c,'_ZN2nn2os16GetCurrentThreadEv':0x9d56c}[name]))
        elif name=='forge_singleton_getInstanceByName':
            assert self.string(r[0])=='sFestaRender';self.ret(self.singleton)
        elif name=='igGetIO_Nil':self.ret(DATA+0xf0000)
        elif name=='igGetBackgroundDrawList_Nil':self.ret(DATA+0xf0100 if self.draw_enabled else 0)
        elif name=='igGetTime':
            bits=struct.pack('<d',self.time);u.reg_write(REGS[0],struct.unpack_from('<I',bits)[0]);u.reg_write(REGS[1],struct.unpack_from('<I',bits,4)[0]);u.reg_write(a.UC_ARM_REG_PC,u.reg_read(a.UC_ARM_REG_LR))
        elif name=='ImDrawList_AddLine':
            # Softfp AAPCS: this,r1/r2 first ImVec2, r3/stack second,
            # followed by stack color/thickness.
            stack=bytes(u.mem_read(u.reg_read(a.UC_ARM_REG_SP),12))
            vals=struct.unpack('<4f',struct.pack('<3I',r[1],r[2],r[3])+stack[:4])
            color,thickness=struct.unpack('<If',stack[4:12]);self.draws.append((vals,color,thickness));self.ret()
        elif name=='ImDrawList_PushClipRect':
            stack=bytes(u.mem_read(u.reg_read(a.UC_ARM_REG_SP),8))
            vals=struct.unpack('<4f',struct.pack('<3I',r[1],r[2],r[3])+stack[:4]);self.clips.append(vals);self.clip_history.append(vals);self.ret()
        elif name=='ImDrawList_PopClipRect':assert self.clips;self.clips.pop();self.ret()
        elif name=='forge_log':
            fmt=self.string(r[1]);self.logs.append(fmt);values=[];position=2
            # ARM32 variadic arguments start at r2. Doubles and ll integers
            # align to an even core-register/stack word position (softfp ABI).
            sp=u.reg_read(a.UC_ARM_REG_SP)
            def log_word(pos):return r[pos] if pos<4 else self.read(sp+(pos-4)*4)
            for match in re.finditer(r'%(?:[-+ #0]*[0-9]*(?:\.[0-9]+)?)(ll)?([sduxXifeg])',fmt):
                wide,kind=match.groups()
                if wide or kind in 'feg':
                    position=(position+1)&~1
                    bits=struct.pack('<2I',log_word(position),log_word(position+1));position+=2
                    value=struct.unpack('<d' if kind in 'feg' else '<Q',bits)[0]
                else:
                    value=log_word(position);position+=1
                    if kind=='s':value=self.string(value)
                    elif kind in ('d','i') and value>=0x80000000:value-=0x100000000
                values.append(value)
            self.log_records.append((fmt,values));self.ret()
        elif name=='igTreeNode_Str':
            opened=self.tree.get(self.string(r[0]),False) if isinstance(self.tree,dict) else self.tree
            if opened:self.tree_depth+=1
            self.ret(int(opened))
        elif name=='igTreePop':self.tree_depth-=1;assert self.tree_depth>=0;self.ret()
        elif name=='igCheckbox':
            label=self.string(r[0]);value=self.edits.pop(label,None)
            if value is not None:self.write(r[1],int(value),'<B')
            self.ret(int(value is not None))
        elif name=='igButton':self.ret(int(self.button));self.button=False
        elif name=='igTextUnformatted':self.messages.append(self.string(r[0]));self.ret()
        elif name=='igText':
            fmt=self.string(r[0]);self.text.append((fmt,self.string(r[1]) if fmt.startswith(('Conditional:','Observation:','Last mapping fault:','Last suppressed draw:','First suppressed draw this screen:')) else None));self.ret()
        elif name in ('igSetCurrentContext','igSetAllocatorFunctions'):self.ret()
        elif name=='forge_fs_mountSaveData':
            assert self.guard==1;self.fs_calls+=1;self.mounts+=int(self.save_available);self.ret(int(self.save_available))
        elif name=='forge_fs_unmountSaveData':assert self.guard==1 and self.mounts==1 and not self.handles;self.mounts-=1;self.ret()
        elif name=='_ZN2nn2fs23ScopedAutoAbortDisablerC1Ev':self.guard+=1;self.write(r[0],0x1234);self.ret()
        elif name=='_ZN2nn2fs25SetCurrentThreadFsContextEPKNS0_9FsContextE':assert r[0]==0x1234;self.guard-=1;self.ret()
        elif name.startswith('_ZN2nn2fs'):
            assert self.guard==self.mounts==1
            if name=='_ZN2nn2fs14CommitSaveDataEPKc':
                assert self.string(r[0])=='savedata' and not self.handles
                self.commits+=1;self.ret(int(self.commits==self.fail_commit))
            elif name=='_ZN2nn2fs8OpenFileEPNS0_10FileHandleEPKci':
                path=self.string(r[1]);self.paths.append(path)
                assert path == 'savedata:/please_do_better.ini'
                if path not in self.files:self.ret(1)
                else:
                    handle=len(self.handles)+1;self.handles[handle]=(path,r[2]);self.write(r[0],handle);self.ret()
            elif name=='_ZN2nn2fs9CloseFileENS0_10FileHandleE':del self.handles[r[0]];self.ret()
            elif name=='_ZN2nn2fs11GetFileSizeEPxNS0_10FileHandleE':self.write(r[0],len(self.files[self.handles[r[1]][0]]),'<q');self.ret()
            elif name=='_ZN2nn2fs8ReadFileENS0_10FileHandleExPvj':
                buffer,length=struct.unpack('<2I',u.mem_read(u.reg_read(a.UC_ARM_REG_SP),8))
                assert r[2:4]==[0,0] and 0<length<128
                path=self.handles[r[0]][0];data=self.files[path][:length]
                if self.read_corrupt and self.writes==1 and path.endswith('/please_do_better.ini'):
                    data=bytes([data[0]^1])+data[1:];self.read_corrupt=False
                u.mem_write(buffer,data);self.ret()
            elif name=='_ZN2nn2fs9WriteFileENS0_10FileHandleExPKvjRKNS0_11WriteOptionE':
                buffer,length,option=struct.unpack('<3I',u.mem_read(u.reg_read(a.UC_ARM_REG_SP),12))
                assert r[2:4]==[0,0] and 0<length<128 and self.read(option)==1
                path,mode=self.handles[r[0]];assert mode==2;self.writes+=1
                self.files[path]=bytes(u.mem_read(buffer,length if self.writes!=self.fail_write else 3))
                self.ret(int(self.writes==self.fail_write))
            elif name=='_ZN2nn2fs11SetFileSizeENS0_10FileHandleEx':
                assert 0<r[2]<128 and not r[3]
                path,mode=self.handles[r[0]];assert mode==2
                self.files[path]=self.files[path][:r[2]].ljust(r[2],b'\0');self.ret()
            elif name=='_ZN2nn2fs10CreateFileEPKcx':
                path=self.string(r[0]);assert path == 'savedata:/please_do_better.ini'
                assert 0<r[2]<128 and not r[3] and path not in self.files
                self.files[path]=bytes(r[2]);self.ret()
            elif name=='_ZN2nn2fs9FlushFileENS0_10FileHandleE':self.ret()
            else:raise AssertionError(f'Unexpected filesystem fixture {name}')
        else:raise AssertionError(f'Unexpected import fixture {name}')
    def call(self,name,args=(),sp=None,budget=500000):
        u=self.u;u.reg_write(a.UC_ARM_REG_CPSR,0x10)
        u.reg_write(a.UC_ARM_REG_SP,sp or STACK+0xff00);u.reg_write(a.UC_ARM_REG_LR,STOP)
        for reg,value in zip(REGS,args):u.reg_write(reg,value)
        u.emu_start(self.address(name) if isinstance(name,str) else name,STOP,count=budget)
        assert u.reg_read(a.UC_ARM_REG_PC)==STOP,f'Fixture budget exhausted at {u.reg_read(a.UC_ARM_REG_PC):x}'
        return u.reg_read(REGS[0])
    def frame(self,kind,values=(),caller=STOP,at=DATA+0x4000):
        self.u.mem_write(at,bytes(328))
        for i,value in enumerate(values):self.write(at+272+4*i,value)
        self.write(at+324,caller)
        return self.call('pdb_gateway_dispatch',[kind,at]),at
    def leave(self,at):
        self.write(at+324,self.address('pdb_gateway_after'))
        return self.call('pdb_gateway_leave',[at])


def main():
    image,_=recipe.binary.main_image((recipe.input_path('main')).read_bytes())
    payload=(recipe.WORK/'native/plugin.nro').read_bytes()
    checks=0
    def check(ok,label):
        nonlocal checks
        assert ok,label;checks+=1
    for conflict in (None,0x3822dc,0x4d17f4):
        p=Probe(image,payload,conflict=conflict);p.call('forge_onInit')
        check(p.allocations==(0 if conflict else 1),'One arena only after valid conditional pair')
        check(p.tls_allocations==(0 if conflict else 1),'One native TLS slot')
        p.call('forge_onInit');check(p.allocations<=1 and p.tls_allocations<=1,'Repeated init does not allocate')
    p=Probe(image,payload,title=False);p.call('forge_onInit');check(not p.flushes and not p.allocations,'Wrong title has no writes/cache/allocation')
    for fail in (1,2):
        p=Probe(image,payload,fail_flush=fail);p.call('forge_onInit')
        check(bytes(p.u.mem_read(MAIN+0x3822dc,8))==image[0x3822dc:0x3822e4] and
              bytes(p.u.mem_read(MAIN+0x4d17f4,8))==image[0x4d17f4:0x4d17fc],'Conditional flush failure restores both words')
    for op,nth in ((0x4b,1),(0x4c,1),(0x4c,2)):
        p=Probe(image,payload,fail_svc={op:nth});p.call('forge_onInit')
        check(p.read(p.private('pair_ready'))==1 and p.read(p.private('capture_ready'))==0,'Safe visual resource failure retains natural conditional pair')
        check(not p.aliases and all(s<0x50000000 or s>=0x50010000 for s,n,perm in p.regions),'Failed preparation releases mapped arena storage')
        p.call('_ZN3pdb13request_forceEb',[1]);pc,f=p.frame(0,[DATA,251])
        check(pc==MAIN+0xe0da0,'Visual resource failure never silently enables always-forced mode')
    for fail in (3,4,8,22,23):
        p=Probe(image,payload,fail_flush=fail);p.call('forge_onInit')
        check(p.read(p.private('pair_ready'))==1 and not p.read(p.private('capture_ready')) and not p.aliases,
              'Visual cache failure safely rolls back and retains conditional-only natural behavior')
    for site in (0x3820b4,0x3875bc,0x3878e0,0x387b00,0x388084):
        p=Probe(image,payload,conflict=site);p.call('forge_onInit')
        check(p.read(p.private('pair_ready'))==1 and not p.read(p.private('capture_ready')) and not p.allocations,
              'Conflict at each new observation tap rejects observation before arena allocation')
    p=Probe(image,payload,fail_flush=4,fail_svc={0x5f:5});p.call('forge_onInit');p.tree=True;p.call('forge_onImGuiRender')
    check(not p.read(p.private('capture_ready')) and len(p.aliases)==1,'Unsafe restoration retains reachable executable arena')
    check(any('unsafe restore' in str(args) for fmt,args in p.log_records),'Unsafe restoration is explicitly reported once through Forge logs')
    p=Probe(image,payload);p.call('forge_onInit')
    check(p.read(p.private('pair_ready'))==1 and p.read(p.private('capture_ready'))==1,'Compiled startup publishes both transactions')
    # Execute exact native hasSkill bytes, not a synthetic successful-return stub.
    subject=DATA+0x1000;skills=DATA+0x2000
    p.write(subject+0x188,skills);p.write(subject+4+0x188,skills)
    for forced,equipped,site,unaligned in itertools.product((False,True),(False,True),(0,1),(False,True)):
        p.call('_ZN3pdb13request_forceEb',[int(forced)])
        p.write(skills+0x3dc+(251//32)*4,(1<<(251%32)) if equipped else 0)
        offset=(0x3822dc,0x4d17f4)[site];end=MAIN+offset+8
        reference=MAIN+0x1f00000
        callee=MAIN+(0xe0da0 if site==0 else 0x26fe08)
        branch=0xeb000000|(((callee-reference-8)//4)&0xffffff)
        p.u.mem_write(reference,struct.pack('<2I',0xe3a00001 if forced else branch,0xe3a0501f if site==0 else 0xe3a05001))
        # The fixture rewrites its reference snippet between cases. Explicitly
        # invalidate Unicorn's cached translation; this is not an Eden operation.
        p.u.ctl_remove_cache(reference,reference+8)
        for flags,ge in itertools.product(range(32),range(16)):
            u=p.u;values=[subject,251]+[0x12300000+i for i in range(2,13)]
            cpsr=(flags<<27)|(ge<<16)|0x10;u.reg_write(a.UC_ARM_REG_CPSR,cpsr)
            sp=STACK+0xff00-(4 if unaligned else 0);u.reg_write(a.UC_ARM_REG_SP,sp);u.reg_write(a.UC_ARM_REG_LR,STOP)
            for reg,value in zip(REGS,values):u.reg_write(reg,value)
            ds=[0x1234567800000000+i for i in range(32)]
            for i,value in enumerate(ds):u.reg_write(getattr(a,f'UC_ARM_REG_D{i}'),value)
            u.reg_write(a.UC_ARM_REG_FPSCR,0x08000000)
            old_calls=p.skill_calls;u.emu_start(MAIN+offset,end,count=30000)
            check(u.reg_read(REGS[0])==int(forced or equipped),'Natural/forced native return')
            check(p.skill_calls-old_calls==int(not forced),'Only natural mode invokes original check')
            check(u.reg_read(REGS[5])==(31 if site==0 else 1),'Displaced MOV replay')
            check(u.reg_read(a.UC_ARM_REG_LR)==(STOP if forced else MAIN+offset+4),'Cheat/original BL LR behavior')
            check(u.reg_read(a.UC_ARM_REG_SP)==sp,'Original native stack and alignment restored')
            check(u.reg_read(a.UC_ARM_REG_CPSR)&0x080f0000==cpsr&0x080f0000,'Q and all GE preserved')
            check([u.reg_read(getattr(a,f'UC_ARM_REG_D{i}')) for i in range(32)]==ds and u.reg_read(a.UC_ARM_REG_FPSCR)==0x08000000,'All VFP registers and FPSCR preserved')
            if forced:check(u.reg_read(a.UC_ARM_REG_CPSR)&MASK==cpsr&MASK,'Forced mode preserves full flags')
            actual=[u.reg_read(reg) for reg in REGS];actual_flags=u.reg_read(a.UC_ARM_REG_CPSR)&MASK
            u.reg_write(a.UC_ARM_REG_CPSR,cpsr);u.reg_write(a.UC_ARM_REG_SP,sp);u.reg_write(a.UC_ARM_REG_LR,STOP)
            for reg,value in zip(REGS,values):u.reg_write(reg,value)
            u.emu_start(reference,reference+8,count=100)
            check(u.reg_read(a.UC_ARM_REG_PC)==reference+8,'Reference BL is in ARM branch range and completes')
            expected=[u.reg_read(reg) for reg in REGS]
            check(actual==expected and actual_flags==(u.reg_read(a.UC_ARM_REG_CPSR)&MASK),
                  f'GPR/flags differ: mode={forced} skill={equipped} site={site} flags={flags} GE={ge}: '
                  f'{[(i,hex(x),hex(y)) for i,(x,y) in enumerate(zip(actual,expected)) if x!=y]} '
                  f'flags={actual_flags:x}/{u.reg_read(a.UC_ARM_REG_CPSR)&MASK:x}')
    # Closed panel is balanced and does not disable update/settings polling.
    p.call('forge_onImGuiRender');check(p.tree_depth==0,'Closed tree has no unmatched pop')
    p.tree=True;p.edits['Force Miraculous Luck###pdb_force']=False;p.call('forge_onImGuiRender')
    check(p.tree_depth==0 and p.read(p.private('mode'))==0,'Live checkbox changes the atomic request')
    p.call('forge_onImGuiFreeRender');check(p.fs_calls==0,'User edit cancels delayed loading')
    # Compile-time helpers run with the real native TLS getter/setter, and the
    # comparison gateways replay each original AND/MOV/CMP exactly.
    for kind,threshold,roll,ge in itertools.product(range(2,9),(8,16,22,25,28,31),range(32),range(16)):
        offset=(0x3820d0,0x382edc,0x382efc,0x382f1c,0x382f3c,0x382f5c,0x382f7c)[kind-2]
        values=[0x12300000+i for i in range(13)];values[0]=roll;values[4]=2;values[5 if kind==2 else 6]=threshold
        u=p.u;flags=0xd80f0010&~0x000f0000 | ge<<16
        for reg,value in zip(REGS,values):u.reg_write(reg,value)
        u.reg_write(a.UC_ARM_REG_CPSR,flags);u.reg_write(a.UC_ARM_REG_SP,STACK+0xfe00);u.reg_write(a.UC_ARM_REG_LR,STOP)
        u.emu_start(MAIN+offset,MAIN+offset+8,count=30000)
        actual=[u.reg_read(reg) for reg in REGS];actual_flags=u.reg_read(a.UC_ARM_REG_CPSR)&MASK
        reference=MAIN+0x1f01000;u.mem_write(reference,image[offset:offset+8]);u.ctl_remove_cache(reference,reference+8)
        for reg,value in zip(REGS,values):u.reg_write(reg,value)
        u.reg_write(a.UC_ARM_REG_CPSR,flags);u.emu_start(reference,reference+8,count=20)
        check(actual==[u.reg_read(reg) for reg in REGS] and actual_flags==u.reg_read(a.UC_ARM_REG_CPSR)&MASK,
              'All seven comparisons preserve native outputs and GE')
    # Full native reward-count algorithms and selector execute. Only unrelated
    # quest/player/table lookups and RNG itself are deterministic stubs. Compare
    # the exact consumed roll stream with original execution or original cheat.
    original=Probe(image,payload);observed=Probe(image,payload);observed.call('forge_onInit')
    literals=[(0x382100,0x381ff8),(0x382104,0x382014),(0x38210c,0x382034),(0x382108,0x382048),
              (0x382110,0x38205c),(0x382114,0x38209c),(0x382118,0x3820c4),(0x382368,0x3822c4),
              (0x382fe0,0x382ea8),(0x382fe4,0x382ecc),(0x382fe8,0x382eec),(0x382fec,0x382f0c),
              (0x382ff0,0x382f2c),(0x382ff4,0x382f4c),(0x382ff8,0x382f6c)]
    festa,skills,rem,container=DATA+0x18000,DATA+0x19000,DATA+0x1a000,DATA+0x1b000
    for engine in (original,observed):
        for literal,site in literals:
            cell=site+8+struct.unpack_from('<i',image,literal)[0]
            engine.write(MAIN+cell,MAIN+struct.unpack_from('<I',image,cell)[0])
        engine.write(festa+4+0x188,skills);engine.write(rem+4,1,'<B');engine.write(container,DATA+0x1c000)
        engine.native.update({MAIN+0x3ae5b8:0,MAIN+0x3a3284:0,MAIN+0x3a3370:0,
                              MAIN+0x275a30:festa,MAIN+0x26fe10:0,MAIN+0x3c6124:rem,MAIN+0x37c500:DATA+0x1d000})
        def rng(engine=engine):
            value=engine.rolls[len(engine.rng)];engine.rng.append(value);return value
        def generate(engine=engine):
            engine.generated.append([engine.u.reg_read(r) for r in REGS[:4]]);return 0
        engine.native[MAIN+0x3f8344]=rng;engine.native[MAIN+0x38211c]=generate
    table=MAIN+struct.unpack_from('<I',image,0x183c89c)[0]
    rng_cases=0
    for skill,guaranteed,category,meal,sequence,forced in itertools.product(
            (None,251,252,321,253,254,255),(0,2,7,8),(0,1),(0,16,17),
            ([0]*12,[21,22,24,25,27,28,30,31,31,31,31,31],[31]*12),(False,True)):
        observed.call('_ZN3pdb13request_forceEb',[int(forced)])
        original.write(MAIN+0x3822dc,0xe3a00001 if forced else struct.unpack_from('<I',image,0x3822dc)[0])
        original.u.ctl_remove_cache(MAIN+0x3822dc,MAIN+0x3822e0)
        results=[]
        for engine in (original,observed):
            engine.u.mem_write(skills+0x3dc,bytes(64))
            if skill is not None:engine.write(skills+0x3dc+(skill//32)*4,1<<(skill%32))
            engine.write(table+category,guaranteed,'<B')
            engine.native[MAIN+0x26fe10]=lambda engine=engine,meal=meal: int(engine.u.reg_read(REGS[1])==meal)
            engine.rolls=[0x1000+x for x in sequence];engine.rng=[]
            result=engine.call(MAIN+0x381fec,[0,category],budget=100000)
            results.append((result,list(engine.rng)))
        check(results[0]==results[1],'Main count and RNG stream agree with original/cheat across skills, meals and caps');rng_cases+=1
    for skill,sequence,forced,table_present in itertools.product((None,251,252,321,253,254,255),
            ([0]*6,[21,22,24,25,27,28],[31]*6),(False,True),(False,True)):
        observed.call('_ZN3pdb13request_forceEb',[int(forced)])
        original.write(MAIN+0x3822dc,0xe3a00001 if forced else struct.unpack_from('<I',image,0x3822dc)[0])
        original.u.ctl_remove_cache(MAIN+0x3822dc,MAIN+0x3822e0)
        results=[]
        for engine in (original,observed):
            engine.u.mem_write(skills+0x3dc,bytes(64))
            if skill is not None:engine.write(skills+0x3dc+(skill//32)*4,1<<(skill%32))
            engine.native[MAIN+0x3c6124]=rem if table_present else 0
            engine.rolls=sequence;engine.rng=[];engine.generated=[]
            engine.call(MAIN+0x382e1c,[0,container,8],budget=100000)
            results.append((list(engine.rng),list(engine.generated)))
        check(results[0]==results[1],'Secondary count and RNG stream include final slot-eight comparison and absent tables');rng_cases+=1
    # Compiled scope/attribution/publication helpers. Actual native copies are
    # independently executed in the native research fixtures.
    p=Probe(image,payload);p.call('forge_onInit');p.call('_ZN3pdb13request_forceEb',[1])
    ui,source,target,container=DATA+0x10000,DATA+0x11000,DATA+0x12000,DATA+0x13000
    p.write(ui+0x5c,target);p.write(ui+0x64,target+0x1000);p.write(ui+0x3c,2)
    p.write(container,source);p.write(container+4,8)
    _,root=p.frame(12,[ui],at=DATA+0x4000)
    _,counter=p.frame(9,[0,1],caller=MAIN+0x387a98,at=DATA+0x4400)
    p.call('_ZN3pdb13request_forceEb',[0])
    pc,f=p.frame(0,[ui,251],at=DATA+0x4800)
    check(pc==MAIN+0x3822e4 and p.read(f+272)==1,'In-batch toggle retains latched force')
    p.frame(25,[31,0,0,0,2],at=DATA+0x4800)
    for slots,roll in ((2,22),(3,0),(4,31)):p.frame(2,[roll,0,0,0,slots,31],at=DATA+0x4800)
    p.write(counter+272,4);p.leave(counter)
    rewards=struct.pack('<16H',123,2,123,2,456,1,123,2,0,0,0,0,0,0,0,0)
    p.u.mem_write(source,rewards)
    p.u.reg_write(REGS[4],ui);p.u.reg_write(REGS[6],source)
    p.u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00)
    p.u.emu_start(MAIN+0x387b00,MAIN+0x387bc4,count=100000)
    check(p.u.reg_read(a.UC_ARM_REG_PC)==MAIN+0x387bc4,'Compiled copy gateway resumes exact native halfword copy')
    p.leave(root)
    p.call('forge_onUpdate',[0]);check(p.read(p.private('bonus_count'))==2 and p.read(p.private('latest_tier'))==31 and p.read(p.private('summary_status'))==1,'Compiled attribution uses exact copied slots and duplicate identities')
    check(p.read(p.private('gateway_hits')+12*4)==1 and p.read(p.private('completed_batches'))==1 and
          p.read(p.private('completed_generations'))==0 and p.read(p.private('published_rewards'))==1,
          'Copy publication succeeds with no generator detour execution')
    check(p.read(p.private('forced_checks'))==1 and p.read(p.private('natural_checks'))==0 and
          p.read(p.private('last_comparison_tier'))==31 and p.read(p.private('update_hits'))==1,
          'Diagnostics report actual forced execution, observed threshold and consumer activity')
    pc,f=p.frame(0,[ui,251]);check(pc==MAIN+0xe0da0,'After-batch check uses new natural mode')
    check(p.read(p.private('natural_checks'))==1 and p.read(p.private('gateway_hits'))==2,
          'Natural and forced checks are counted independently without altering mode')
    list_object,src=DATA+0x14000,DATA+0x16000;display=list_object+0x60
    p.write(src,target);p.write(src+4,16);p.write(list_object+0x5c,16)
    _,update=p.frame(15,[ui],at=DATA+0x4000)
    _,copy_frame=p.frame(14,[list_object,src],at=DATA+0x4400)
    p.u.mem_write(display,bytes(p.u.mem_read(target,64)));p.leave(copy_frame);p.leave(update);p.call('forge_onUpdate',[0])
    displayed=p.private('displayed')
    check(p.read(displayed+6*4+4)==display+32,'Native list copy follows array-relative index, including duplicate IDs')
    p.write(target+32+8,0);p.call('forge_onUpdate',[0]);check(p.read(p.private('bonus_count'))==2,'Completed observation does not become collection tracking')
    p.write(ui+0x3c,6);_,update=p.frame(15,[ui]);p.leave(update);p.call('forge_onUpdate',[0])
    check(p.read(p.private('bonus_count'))==2 and not p.read(displayed+3*4),'Reward-screen close suppresses live provenance and retains completed totals')
    check(p.read(p.private('cleared_rewards'))==1 and p.read(p.private('last_ui_state'))==6 and
          p.read(p.private('gateway_hits')+15*4)==2 and p.read(p.private('published_rewards'))==1,
          'Clearing diagnostics retain cumulative publication evidence after provenance is hidden')
    # Four observed scopes: overflow suppresses attribution while parent mode
    # remains latched; unwinding recovers and does not invent return addresses.
    frames=[];p.call('_ZN3pdb13request_forceEb',[1])
    for i in range(4):_,f=p.frame(15,[ui],caller=STOP+4*i,at=DATA+0x4000+0x400*i);frames.append(f)
    p.call('_ZN3pdb13request_forceEb',[0]);pc,f=p.frame(15,[ui],at=DATA+0x5800)
    check(p.read(f+324)==STOP,'Overflow leaves original caller LR untouched')
    pc,f=p.frame(0,[ui,251],at=DATA+0x5c00);check(pc==MAIN+0x3822e4,'Overflow keeps root force latch')
    for i,f in reversed(list(enumerate(frames))):check(p.leave(f)==STOP+4*i,'Nested leave preserves native caller')
    pc,f=p.frame(0,[ui,251]);check(pc==MAIN+0xe0da0,'Overflow quarantine recovers after root unwind')
    p.call('_ZN3pdb13request_forceEb',[1]);_,root=p.frame(12,[ui],caller=STOP+64)
    p.write(DATA+0x51000+0x48+17*4,0xdeadbeef) # Lost/foreign value in our reserved slot.
    p.call('_ZN3pdb13request_forceEb',[0]);pc,f=p.frame(0,[ui,251],at=DATA+0x4400)
    check(pc==MAIN+0x3822e4,'Lost TLS preserves already-latched force through immutable native thread identity')
    check(p.leave(root)==STOP+64 and p.read(DATA+0x51000+0x48+17*4)==0xdeadbeef,'Lost TLS does not invent a caller or overwrite external bytes')
    p.call('forge_onUpdate',[0]);check(p.read(p.private('summary_status'))==2,'Lost TLS reports incomplete observation')
    # Overflow the bounded mailbox without a consumer, then verify stale state
    # is cleared even when read() exits immediately after detecting overwrite.
    old_drops=p.read(p.private('drops'))
    for i in range(24):_,f=p.frame(12,[ui]);p.leave(f)
    p.call('forge_onUpdate',[0])
    check(p.read(p.private('summary_status'))==2 and p.read(p.private('drops'))>old_drops,'Publication overflow suppresses attribution and reports incomplete coverage')
    for thread in range(1,9):p.thread=thread;p.frame(0,[ui,251])
    p.call('_ZN3pdb13request_forceEb',[1]);pc,f=p.frame(0,[ui,251])
    check(pc==MAIN+0xe0da0,'Exhausted thread pool remains natural when batch latching is unavailable')
    # Plugin preference I/O operates only on in-memory fake files. Verify the
    # compiled SDK argument layout, counted mount and primary-only commit paths.
    primary='savedata:/please_do_better.ini';backup='savedata:/please_do_better_backup.ini'
    off=b'force_miraculous=0\n';on=off.replace(b'=0\n',b'=1\n')
    for force,record in ((0,off),(1,on)):
        p=Probe(image,payload);p.call('forge_onInit');p.save_available=True;p.files[primary]=b'version=2\n'+record
        p.call('forge_onImGuiFreeRender')
        check(p.read(p.private('mode'))==force,'Existing version-2 preference preserves requested mode in compiled load')
        p.tree=True;p.button=True;p.call('forge_onImGuiRender')
        check(p.files[primary]==record and not p.mounts and not p.handles and not p.guard,
              'Compiled save removes obsolete version marker with balanced cleanup')
        restarted=Probe(image,payload);restarted.call('forge_onInit');restarted.save_available=True;restarted.files=p.files.copy()
        restarted.call('forge_onImGuiFreeRender')
        check(restarted.read(restarted.private('mode'))==force,'Compiled restart loads migrated versionless preference')
    for fail_write,fail_commit in ((0,0),(1,0),(0,1)):
        p=Probe(image,payload);p.call('forge_onInit');p.save_available=True;p.files[primary]=off;p.files[backup]=on
        p.call('forge_onImGuiFreeRender');check(p.read(p.private('mode'))==0,'Valid saved natural mode loads')
        p.tree=True;p.edits['Force Miraculous Luck###pdb_force']=True;p.call('forge_onImGuiRender')
        p.fail_write=fail_write;p.fail_commit=fail_commit;p.button=True;p.call('forge_onImGuiRender')
        check(not p.mounts and not p.handles and not p.guard,'Preference failure releases counted mount, handles and SDK guard')
        check(p.files[backup]==on and set(p.paths)=={primary},'Only primary accessed; legacy backup left unused')
        check(p.read(p.private('mode'))==1,'Save failure retains live session choice')
        if not fail_write and not fail_commit:check(p.files[primary]==on,'Primary save verified and committed')
    for original,recovery,expected in ((b'invalid',on,0),(on,None,1),(None,on,0)):
        p=Probe(image,payload);p.call('forge_onInit');p.call('forge_onImGuiFreeRender');check(p.fs_calls==1,'Storage unavailable leaves delayed load pending')
        p.save_available=True
        if original is not None:p.files[primary]=original
        if recovery is not None:p.files[backup]=recovery
        before=p.files.copy()
        for frame in range(60):p.call('forge_onImGuiFreeRender')
        check(p.read(p.private('mode'))==expected and p.files==before,'Delayed load uses primary only or defaults; never recovers backup')
    for fresh,corrupt in ((True,False),(False,True)):
        p=Probe(image,payload);p.call('forge_onInit');p.save_available=True;p.files[backup]=on
        if not fresh:p.files[primary]=off
        p.tree=True;p.edits['Force Miraculous Luck###pdb_force']=True;p.call('forge_onImGuiRender')
        p.read_corrupt=corrupt;p.button=True;p.call('forge_onImGuiRender')
        check(p.files[backup]==on and set(p.paths)=={primary},'Fresh save/readback failure never writes or reads legacy backup')
        check(not p.mounts and not p.handles and not p.guard,'Primary readback paths balance mounts, handles and guard')
        if corrupt:check(any('Save failed' in str(args) for fmt,args in p.log_records),'Corrupt readback explicitly reports save failure')
    p=Probe(image,payload);p.call('forge_onInit');p.write(MAIN+0x3822dc,0xe1a00000)
    flushes=p.flushes;p.call('forge_onInit')
    check(p.read(p.private('capture_ready'))==p.read(p.private('pair_ready'))==0 and p.flushes==flushes and
          p.read(MAIN+0x3822dc)==0xe1a00000,'Repeated init detects external change without rewriting it')
    report={'checks':checks,'gateway_cases':8192,'native_rng_cases':rng_cases,'nro_sha256':recipe.sha(payload),'runtime':'NOT RUN',
            'scope':'Compiled startup, native SDK TLS, natural hasSkill, conditional and comparison gateways, batch toggles, scopes, attribution/copies, primary-only preference ABI/failures and UI fixtures',
            'limits':['Fake kernel and ImGui; not emulator cache/multicore or gameplay evidence','Visual geometry still requires independent native binding fixtures']}
    recipe.write_json(recipe.OUT/'runtime-tests.json',report)
    print(f'PASS: {checks} compiled runtime/gateway checks')


if __name__=='__main__':main()
