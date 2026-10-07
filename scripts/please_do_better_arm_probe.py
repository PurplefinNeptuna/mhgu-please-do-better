from paths import MOD, SCRIPTS, FORGE, DEPS, PYTHON, CONTAINER_STORAGE, input_path
#!/usr/bin/env python3
"""ARM32 instruction/SVC ABI fixtures. This does not run Eden or the game."""
import itertools
import json
from pathlib import Path
import re
import struct

import unicorn
from unicorn import arm_const as arm
import please_do_better as recipe

CODE = 0x10000000
STACK = 0x21000000
DATA = 0x22000000
RETURN = CODE + 0xfff0
MASK = 0xf80f0000 # NZCVQ and all GE patterns
REGS = [getattr(arm, f'UC_ARM_REG_R{i}') for i in range(13)]


def main():
    recipe.require(unicorn.__version__ == '2.1.4', 'Use pinned Unicorn 2.1.4')
    native = recipe.WORK / 'native'
    payload = (native / 'plugin.nro').read_bytes()
    symbols = {name: int(value, 16) for value, _, name in
               re.findall(r'^([0-9a-f]+)\s+(\w)\s+(\S+)$', (native / 'symbols.txt').read_text(), re.M)}
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(arm.UC_CPU_ARM_MAX)
    uc.mem_map(CODE, (len(payload)+struct.unpack_from("<I",payload,56)[0]+4095)&~4095)
    uc.mem_write(CODE, payload)
    uc.mem_map(STACK, 0x10000)
    uc.mem_map(DATA, 0x10000)
    checks = 0

    def check(condition, label):
        nonlocal checks
        if not condition:
            raise AssertionError(label)
        checks += 1

    # Retain the r1/source-cheat reference instruction fixture. R2 conditional
    # gateways are exercised separately by please_do_better_runtime_probe.py.
    instruction = DATA + 0x8000
    uc.mem_write(instruction, struct.pack('<I', 0xe3a00001))
    for flags, ge in itertools.product(range(32), range(16)):
        cpsr = (flags << 27) | (ge << 16) | 0x10
        uc.reg_write(arm.UC_ARM_REG_CPSR, cpsr) # select user-mode bank before setting SP/LR
        values = [0x13400000+i for i in range(13)]
        for register, value in zip(REGS, values):
            uc.reg_write(register, value)
        uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK+0xff00)
        uc.emu_start(instruction, instruction+4, count=1)
        check(uc.reg_read(REGS[0]) == 1, 'MOV forces r0=1')
        check([uc.reg_read(r) for r in REGS[1:]] == values[1:], 'Other integer registers preserved')
        check(uc.reg_read(arm.UC_ARM_REG_CPSR) & MASK == cpsr & MASK, 'NZCVQ and GE unchanged')
        check(uc.reg_read(arm.UC_ARM_REG_LR) == RETURN and uc.reg_read(arm.UC_ARM_REG_SP) == STACK+0xff00,
              'LR and stack unchanged')

    validation = json.loads((recipe.OUT / 'input-validation.json').read_text())
    for i, site in enumerate(validation['sites']):
        words = list(struct.unpack('<8I', bytes.fromhex(site['bytes'])))
        words[3] = site['replacement']
        address = DATA + 0x9000 + i*0x100
        uc.mem_write(address, struct.pack('<8I', *words))
        uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10 | 0x000f0000)
        uc.emu_start(address+12, address+28, count=4)
        check(uc.reg_read(arm.UC_ARM_REG_R0) == 1, 'Patched continuation retains forced success')
        check(uc.reg_read(arm.UC_ARM_REG_R5) == (0x1f if i == 0 else 1), 'Original branch value preserved')
        if i == 0:
            check(uc.reg_read(arm.UC_ARM_REG_PC) == address+24+8+0x1c*4, 'Reward branch skips weaker luck checks')
        else:
            check(uc.reg_read(arm.UC_ARM_REG_PC) == address+28, 'Second branch continues to the retained 0x102 check')
        check(uc.reg_read(arm.UC_ARM_REG_CPSR) & 0x000f0000 == 0x000f0000, 'Continuation preserves incoming GE')

    current = {}

    def svc(u, interrupt, _):
        pc = u.reg_read(arm.UC_ARM_REG_PC)
        opcode, = struct.unpack('<I', bytes(u.mem_read(pc-4, 4)))
        check(interrupt == 2 and opcode & 0xffffff == current['svc'], 'Expected compiled SVC')
        regs = [u.reg_read(r) for r in REGS]
        if current['svc'] == 6:
            check(regs[:4] == [DATA, DATA+0x80, 0xabcdef00, 0x12], 'QueryMemory ARM32 arguments')
            u.mem_write(DATA, struct.pack('<QQ6I', 0xabcdef00, 4096, 3, 0, 5, 0, 0, 0))
            u.reg_write(arm.UC_ARM_REG_R1, 0x7654)
        elif current['svc'] == 0x29:
            check(regs[:4] == [0x11223344, 18, 0xffff8001, 0x55667788], 'GetInfo ARM32 arguments')
            u.reg_write(arm.UC_ARM_REG_R1, 0x08dd8000)
            u.reg_write(arm.UC_ARM_REG_R2, 0x01007700)
        elif current['svc']==0x4b:
            check(regs[:4]==[DATA,0xabcdef00,4096,0],'CreateCodeMemory ARM32 output/source/u64 size')
            u.reg_write(arm.UC_ARM_REG_R1,7)
        elif current['svc']==0x4c:
            check(regs[:7]==[7,1,0xabcdef00,0x12,0x11223344,0x55667788,5],'ControlCodeMemory aligned u64 address/size/permission')
            for i in range(4,7):u.reg_write(REGS[i],0xdead0000+i)
        elif current['svc']==0x16:
            check(regs[0]==7,'CloseHandle argument')
        else:
            check(regs[:5] == [0xffff8001, 0x11223344, 0xabcdef00, 0x12, 0x55667788],
                  'FlushProcessDataCache ARM32 64-bit arguments')
            u.reg_write(arm.UC_ARM_REG_R4, 0xdeadbeef) # wrapper must restore caller's r4
        u.reg_write(arm.UC_ARM_REG_R0, current['result'])

    def stop(u, address, size, _):
        if address == RETURN:
            u.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_INTR, svc)
    uc.hook_add(unicorn.UC_HOOK_CODE, stop)
    for name, number in [('pdb_svc_query',6),('pdb_svc_get_info',0x29),('pdb_svc_flush',0x5f),
                         ('pdb_svc_create',0x4b),('pdb_svc_control',0x4c),('pdb_svc_close',0x16)]:
        for result in (0, 0x1234):
            current.update(svc=number, result=result)
            for i, reg in enumerate(REGS):
                uc.reg_write(reg, 0x13400000+i)
            saved = [uc.reg_read(r) for r in REGS[4:]]
            sp = STACK+0xff00
            uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
            uc.reg_write(arm.UC_ARM_REG_SP, sp)
            uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
            uc.mem_write(sp, struct.pack('<III', 0x11223344, 0x55667788,5))
            args = ([DATA, DATA+0x80, 0xabcdef00, 0x12] if number == 6 else
                    [DATA,18,0xffff8001,0] if number == 0x29 else
                    [DATA,0xabcdef00,4096,0] if number == 0x4b else
                    [7,1,0xabcdef00,0x12] if number == 0x4c else [7] if number == 0x16 else
                    [0xffff8001, 0, 0xabcdef00, 0x12])
            for reg, value in zip(REGS, args):
                uc.reg_write(reg, value)
            uc.emu_start(CODE+symbols[name], RETURN, count=32)
            check(uc.reg_read(arm.UC_ARM_REG_PC) == RETURN and uc.reg_read(arm.UC_ARM_REG_R0) == result,
                  'SVC returns exact success/failure result')
            check([uc.reg_read(r) for r in REGS[4:]] == saved and uc.reg_read(arm.UC_ARM_REG_SP) == sp,
                  'SVC callee-saved registers/stack preserved')
            check(uc.reg_read(arm.UC_ARM_REG_LR) == RETURN, 'SVC LR preserved')
            if number == 6:
                check(struct.unpack('<I', bytes(uc.mem_read(DATA+0x80, 4)))[0] == 0x7654, 'Query output pointer restored')
            if number == 0x29:
                check(struct.unpack('<Q', bytes(uc.mem_read(DATA, 8)))[0] == 0x0100770008dd8000,
                      'GetInfo 64-bit output pointer restored')
            if number==0x4b:check(struct.unpack('<I',uc.mem_read(DATA,4))[0]==7,'Create output pointer stores kernel output even on failure')
    report = {'checks': checks, 'instruction_cases': 512, 'continuation_cases': 2, 'svc_cases': 12,
              'nro_sha256': recipe.sha(payload), 'unicorn': unicorn.__version__,
              'coverage': 'Exact MOV, immediate continuations and compiled private SVC wrappers',
              'limit': 'Fake kernel; does not validate Eden JIT/cache behavior or gameplay'}
    recipe.write_json(recipe.OUT / 'arm-tests.json', report)
    print(f'PASS: {checks} ARM32 checks (512 cheat flag cases, 2 continuations, 12 compiled SVC cases)')


if __name__ == '__main__':
    main()
