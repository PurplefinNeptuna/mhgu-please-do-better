from paths import MOD, SCRIPTS, FORGE, DEPS, PYTHON, CONTAINER_STORAGE, input_path
#!/usr/bin/env python3
"""Pinned native copy/quad fixtures. World-space quads are not screen proof."""
import itertools
import math
import struct
from unicorn import arm_const as a
from please_do_better_runtime_probe import Probe, MAIN, DATA, STACK, STOP, REGS
import please_do_better as recipe


def native_clip(p,view,clip,sentinel,alternate=0,extent=(1920,1080)):
    """Execute original bank/clamp/intersection/sentinel ARM, excluding NVN calls."""
    u=p.u;packet,nv,rect=DATA+0x170000,DATA+0x170100,DATA+0x170200
    u.mem_write(packet,bytes(0x100));u.mem_write(nv,bytes(0x100))
    p.write(packet+0x58,extent[0]|(extent[1]<<16))
    u.mem_write(packet+0x18+(16 if alternate else 0),struct.pack('<4i',*view))
    u.mem_write(packet+0x38+(16 if alternate else 0),struct.pack('<4i',*clip))
    p.write(MAIN+0x183f2b0,rect);u.mem_write(rect,struct.pack('<4i',*sentinel))
    u.reg_write(a.UC_ARM_REG_CPSR,0x10);u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00)
    p.write(STACK+0xff08,alternate);u.reg_write(REGS[8],alternate)
    u.reg_write(REGS[9],nv);u.reg_write(REGS[10],packet)
    u.emu_start(MAIN+0xbc1204,MAIN+0xbc1278,count=100)
    viewport=tuple(u.reg_read(REGS[i]) for i in (1,2,12))+(u.reg_read(a.UC_ARM_REG_LR),)
    u.mem_write(nv+0x74,struct.pack('<4I',*viewport))
    u.mem_write(nv+0x84,struct.pack('<4i',-999,-998,-997,-996))
    u.emu_start(MAIN+0xbc12d8,MAIN+0xbc1394,count=200)
    assert u.reg_read(a.UC_ARM_REG_PC)==MAIN+0xbc1394,'Native clip fragment did not reach NVN submission boundary'
    out=tuple(u.reg_read(REGS[i]) for i in (1,2,3))+(u.reg_read(a.UC_ARM_REG_LR),)
    return tuple(x if x<2**31 else x-2**32 for x in out)


def main():
    image,_=recipe.binary.main_image((recipe.input_path('main')).read_bytes())
    p=Probe(image,(recipe.WORK/'native/plugin.nro').read_bytes());u=p.u
    checks=0
    def check(ok,label):
        nonlocal checks
        assert ok,label;checks+=1
    ui,source,target=DATA+0x10000,DATA+0x11000,DATA+0x12000
    fragments=[(0x3875bc,0x387680,7,0x5c,0),(0x3878e0,0x3879a4,7,0x5c,0),
               (0x387b00,0x387bc4,6,0x5c,32),(0x388084,0x388144,5,0x64,32)]
    rows=[]
    for start,end,reg,field,offset in fragments:
        rows.append({'start':hex(start),'end_exclusive':hex(end),'sha256':recipe.sha(image[start:end]),
                     'source_register':reg,'destination_field':hex(field),'destination_byte_offset':offset})
        for seed in range(8):
            rewards=struct.pack('<16H',*[v for i in range(8) for v in (123 if i%3 else 456,seed+i+1)])
            u.mem_write(source,rewards);u.mem_write(target,b'\xaa'*96);p.write(ui+field,target)
            u.reg_write(REGS[4],ui);u.reg_write(REGS[reg],source)
            u.emu_start(MAIN+start,MAIN+end,count=100)
            check(u.reg_read(a.UC_ARM_REG_PC)==MAIN+end and bytes(u.mem_read(target+offset,32))==rewards,
                  'Original UI halfword copies preserve each duplicate item slot')
            check(bytes(u.mem_read(target,offset))==b'\xaa'*offset and
                  bytes(u.mem_read(target+offset+32,96-offset-32))==b'\xaa'*(96-offset-32),'Copies preserve adjacent slots')
    list_object,container,flags=DATA+0x13000,DATA+0x14000,DATA+0x15000
    target=list_object+0x60
    for count,capacity in itertools.product((0,1,2,8,16,48),(0,1,2,8,16,48)):
        rewards=struct.pack('<96H',*[v for i in range(48) for v in (123 if i%2 else 456,i+1)])
        u.mem_write(source,rewards);u.mem_write(flags,bytes(range(48)))
        u.mem_write(list_object,bytes(0x200));u.mem_write(target,b'\xaa'*192);p.write(list_object+0x5c,capacity)
        p.write(container,source);p.write(container+4,count);p.write(container+8,flags)
        u.reg_write(REGS[0],list_object);u.reg_write(REGS[1],container);u.reg_write(REGS[2],container+8)
        u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00);u.reg_write(a.UC_ARM_REG_LR,STOP)
        u.emu_start(MAIN+0x623c08,MAIN+0x623c60,count=1000)
        n=min(count,capacity)
        check(u.reg_read(a.UC_ARM_REG_PC)==MAIN+0x623c60 and bytes(u.mem_read(target,n*4))==rewards[:n*4],
              'Native list copies min(source count, capacity) by index')
        check(bytes(u.mem_read(target+n*4,192-n*4))==b'\xaa'*(192-n*4),'Native list leaves uncopied slots unchanged')
        check(bytes(u.mem_read(list_object+0x120,n))==bytes(range(n)),'Native per-slot flag copy shares the index mapping')
    # Native world geometry helper: anchor, scale about centre, matrix and Y
    # direction. Deliberately no viewport/projection inference in this fixture.
    obj,out=DATA+0x16000,DATA+0x17000
    matrices=[(1,0,0,1,100,200),(2,0,0,.5,50,60),(0,1,-1,0,100,200),(1,.25,.5,1,50,60)]
    for hx,vy,flip,scale,m in itertools.product(range(3),range(3),(False,True),(.5,1,1.5),matrices):
        u.mem_write(obj,bytes(0x200));p.write(obj+0xa0,hx+4*vy);p.write(obj+0x56,0x40 if flip else 0,'<B')
        xx,xy,yx,yy,tx,ty=m
        matrix=(xx,xy,0,0,yx,yy,0,0,0,0,1,0,tx,ty,0,1)
        u.mem_write(obj+0x10,struct.pack('<16f',*matrix));u.mem_write(obj+0xb4,struct.pack('<2f',32,24))
        u.reg_write(a.UC_ARM_REG_S0,struct.unpack('<I',struct.pack('<f',scale))[0]);p.call(MAIN+0xa4b390,[obj,out,obj+0xb4])
        height=-24 if flip else 24
        left=-hx*16;top=-vy*height/2;dx=(32*scale-32)/2;dy=(height*scale-height)/2
        l,r=left-dx,left+32+dx;t,b=top-dy,top+height+dy
        expected=[(tx+xx*x+yx*y,ty+xy*x+yy*y,0,0) for x,y in ((l,t),(l,b),(r,b),(r,t))]
        actual=struct.unpack('<16f',u.mem_read(out,64))
        check(all(math.isclose(x,y,abs_tol=1e-4) for x,y in zip(actual,sum((list(v) for v in expected),[]))),
              'Native animated world quad agrees with anchors, scale, rotation/shear and Y convention')
    # Execute original rectangle selection/clamping, then scissor intersection.
    # Stop around external NVN/cache loads; their calls and GPU are not mocked
    # as evidence of presentation. Original bytes are checked by research.py.
    packet=DATA+0x70000;nv=DATA+0x71000;viewport_cases=0
    views=[(0,0,1920,1080),(-12,-10,2000,1200),(100,50,1600,900),(0,0,960,540),(2000,2000,2100,2100)]
    clips=[(0,0,1920,1080),(90,45,200,100),(-12,-10,2000,1200),(300,200,100,50)]
    for alt,view,clip in itertools.product((0,0x200),views,clips):
        u.mem_write(packet,bytes(0x100));p.write(packet+0x58,1920|(1080<<16))
        u.mem_write(packet+0x18+(16 if alt else 0),struct.pack('<4i',*view));u.mem_write(packet+0x38+(16 if alt else 0),struct.pack('<4i',*clip))
        u.reg_write(a.UC_ARM_REG_CPSR,0x10);u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00);p.write(STACK+0xff08,alt)
        u.reg_write(REGS[9],nv);u.reg_write(REGS[10],packet)
        u.reg_write(REGS[8],alt)
        u.emu_start(MAIN+0xbc1204,MAIN+0xbc1278,count=100)
        l,t,rr,b=max(view[0],0),max(view[1],0),min(view[2],1920),min(view[3],1080)
        if rr<l:l=rr=0
        if b<t:t=b=0
        got=tuple(u.reg_read(REGS[i]) for i in (1,2,12))+(u.reg_read(a.UC_ARM_REG_LR),)
        assert got==(l,t,rr,b),(view,got,(l,t,rr,b));viewport_cases+=1
        u.emu_start(MAIN+0xbc12d8,MAIN+0xbc12f8,count=100)
        u.emu_start(MAIN+0xbc12fc,MAIN+0xbc1314,count=100)
        u.emu_start(MAIN+0xbc1318,MAIN+0xbc1330,count=100)
        cl,ct,cr,cb=max(l,clip[0]),max(t,clip[1]),min(rr,clip[2]),min(b,clip[3])
        if cr<cl:cl=cr=0
        if cb<ct:ct=cb=0
        got=tuple(u.reg_read(REGS[i]) for i in (1,2,3))+(u.reg_read(a.UC_ARM_REG_LR),)
        assert got==(cl,ct,cr,cb),(alt,view,clip,got,(cl,ct,cr,cb));viewport_cases+=1
    sentinel_cases=0
    for alt,view,clip,sentinel in itertools.product((0,0x200),views,
            clips+[(0,0,0,0),(0,45,0,100)],((0,0,0,0),(90,45,200,100),(-1,-1,-1,-1))):
        out=native_clip(p,view,clip,sentinel,alt)
        l,t,r,b=max(view[0],0),max(view[1],0),min(view[2],1920),min(view[3],1080)
        if r<l:l=r=0
        if b<t:t=b=0
        effective=[max(l,clip[0]),max(t,clip[1]),min(r,clip[2]),min(b,clip[3])]
        if effective[2]<effective[0]:effective[0]=effective[2]=0
        if effective[3]<effective[1]:effective[1]=effective[3]=0
        if tuple(effective)==sentinel:effective=[l,t,r,b]
        check(out==tuple(effective),'Complete original ARM scissor sentinel semantics');sentinel_cases+=1
    # Original render-target binding resolves a default descriptor before
    # passing the exact NVN texture and view to SetRenderTargets.
    sr,default,default_ref,actual,actual_ref,surface,alias,gpu,alias_gpu = [DATA+i for i in
        (0x80000,0xc0000,0xc0400,0xc0800,0xc0c00,0xc1000,0xc1400,0xc1800,0xc1c00)]
    texture_checks=0
    p.write(sr+0x389c0,default);p.write(default+0x204,default_ref);p.write(default_ref,0x334455)
    p.write(sr+0x389cc,actual);p.write(actual+0x204,actual_ref);p.write(actual_ref,surface)
    p.write(surface+0x10,gpu);p.write(alias+0x10,alias_gpu)
    for cached,view,image_ptr in itertools.product((0x334455,surface,alias),(0,DATA+0xc2000),(DATA+0xc3000,DATA+0xc3400)):
        p.write(packet,1);p.write(nv+0x94,cached)
        for item,wrapper in ((surface,gpu),(alias,alias_gpu)):
            p.write(item+0x14,view);p.write(wrapper+0x3c,image_ptr)
        u.reg_write(a.UC_ARM_REG_CPSR,0x10);u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00)
        for reg,val in ((4,sr),(9,nv),(10,packet)):u.reg_write(REGS[reg],val)
        u.emu_start(MAIN+0xbc1148,MAIN+0xbc11bc,count=100)
        check(p.read(STACK+0xff14)==image_ptr and p.read(STACK+0xff54)==view and u.reg_read(REGS[1])==1,
              'Original descriptor resolution supplies exact image/view regardless of wrapper identity')
        texture_checks+=1
    # Window is 0x180 bytes; the subsequent game-owned RESOURCE pointer table
    # supplies the acquired resource and index. No GPU acquire is simulated.
    owner=DATA+0xc4000
    for index,resource_ptr in itertools.product(range(3),(DATA+0xc3000,DATA+0xc3400)):
        p.write(owner+0x46fc,index);p.write(owner+0x48c0+index*4,resource_ptr)
        for reg,val in ((4,owner),(5,owner+0x4740),(6,0x46fc)):u.reg_write(REGS[reg],val)
        u.emu_start(MAIN+0x86a2e8,MAIN+0x86a304,count=100)
        check(p.read(owner+0x48cc)==resource_ptr and p.read(owner+0x48d0)==index,
              'Original acquired-index fragment copies the exact window resource')
        texture_checks+=1
    # Original window constructor separates resource ownership from NVN
    # texture pointers: resource+0x3C is passed in the SetTextures array.
    window=owner+0x4740;resource=DATA+0xca000
    for store,start,end,stack_off in ((0x180,0x869f40,0x869f50,0x68),(0x184,0x869f88,0x869f98,0x6c),(0x188,0x869fd0,0x869fe0,0x70)):
        for image_ptr in (DATA+0xcb000,DATA+0xcb400):
            p.write(resource+0x3c,image_ptr);u.reg_write(REGS[0],resource);u.reg_write(REGS[4],window)
            u.reg_write(a.UC_ARM_REG_SP,STACK+0xff00)
            u.emu_start(MAIN+start,MAIN+end,count=20)
            check(p.read(window+store)==resource and p.read(STACK+0xff00+stack_off)==image_ptr,
                  'Original window constructor owns resources but passes resource+3C NVN textures')
            texture_checks+=1
    # Default level with no parent (the window constructor's route) uses
    # a null NVN view. Other layers or incompatible parents build an explicit
    # view; the plugin conservatively rejects those paths.
    parent=DATA+0xcc000
    for level,parent_kind in itertools.product((0,1),('none','same','different')):
        p.write(resource+0x38,0 if parent_kind=='none' else parent)
        p.write(resource+0x18,6);p.write(parent+0x18,6 if parent_kind=='same' else 7)
        p.write(surface+0x14,0xdeadbeef)
        u.reg_write(REGS[0],0);u.reg_write(REGS[4],surface);u.reg_write(REGS[5],resource);u.reg_write(REGS[9],level)
        default_view=level==0 and parent_kind!='different'
        end=0xb07c5c if default_view else 0xb07c70
        u.emu_start(MAIN+0xb07c24,MAIN+end,count=30)
        check(p.read(surface+0x14)==(0 if default_view else surface+0x28),
              'Original surface constructor distinguishes full default views from explicit subresource views')
        texture_checks+=1
    checks+=viewport_cases
    report={'native_scissor_sentinel_checks':sentinel_cases,'native_texture_fragment_checks':texture_checks,'native_viewport_fragment_checks':viewport_cases,'checks':checks,'main_sha256':recipe.binary.MAIN_SHA,'native_copies':rows,
            'list_copy':{'start':'0x623c08','end_exclusive':'0x623c60','sha256':recipe.sha(image[0x623c08:0x623c60])},
            'world_quad':{'start':'0xa4b390','end_exclusive':'0xa4b6c8','sha256':recipe.sha(image[0xa4b390:0xa4b6c8])},
            'screen_geometry_gate':'CPU world-quad and native image identity evidence; compiled presentation coverage in highlight-tests.json',
            'limits':['Native copy fragments stop before allocation/free/refresh callbacks','World quad does not prove shader matrix order, viewport, clipping, node identity or cursor handling','No gameplay or GPU execution']}
    recipe.write_json(recipe.OUT/'native-tests.json',report)
    print(f'PASS: {checks} original native copy/world-quad/viewport fixtures; {viewport_cases} viewport/clip checks; GPU/gameplay pending')


if __name__=='__main__':main()
