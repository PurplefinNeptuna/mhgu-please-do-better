#!/usr/bin/env python3
"""Pinned native reward-copy fixtures."""
import itertools
import struct
from unicorn import arm_const as a
from please_do_better_runtime_probe import Probe, MAIN, DATA, STACK, STOP, REGS
import please_do_better as recipe


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
    report={'checks':checks,'main_sha256':recipe.binary.MAIN_SHA,'native_copies':rows,
            'list_copy':{'start':'0x623c08','end_exclusive':'0x623c60','sha256':recipe.sha(image[0x623c08:0x623c60])},
            'limits':['Native copy fragments stop before allocation/free/refresh callbacks','No gameplay execution']}
    recipe.write_json(recipe.OUT/'native-tests.json',report)
    print(f'PASS: {checks} original native copy fixtures; gameplay pending')


if __name__=='__main__':main()
