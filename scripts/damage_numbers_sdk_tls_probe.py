from paths import MOD, SCRIPTS, FORGE, DEPS, PYTHON, CONTAINER_STORAGE, input_path
#!/usr/bin/env python3
"""Execute original SDK TLS and clock ABI bytes; no Eden or SDK allocation."""
from pathlib import Path
import ctypes
import hashlib
import json
import struct
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn import arm_const as arm

from paths import ROOT, MOD, SCRIPTS, FORGE, DEPS, PYTHON, CONTAINER_STORAGE, input_path
SDK_SHA = '9a9b7035266637ee693a32da6b0fde54bda00e897bef05b1c8d8cda30f8ac8b0'


def sdk_image():
    source = input_path('sdk')
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != SDK_SHA or data[:4] != b'NSO0':
        raise ValueError('SDK fingerprint differs')
    decompress = ctypes.CDLL('liblz4.so.1').LZ4_decompress_safe
    decompress.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    decompress.restype = ctypes.c_int
    flags = struct.unpack_from('<I', data, 12)[0]
    segments = []
    for i in range(3):
        offset, address, size = struct.unpack_from('<III', data, 16+16*i)
        stored = struct.unpack_from('<I', data, 96+4*i)[0] if flags & (1 << i) else size
        if offset+stored > len(data) or size > 128*1024*1024:
            raise ValueError('SDK segment bounds differ')
        raw = data[offset:offset+stored]
        if flags & (1 << i):
            destination = ctypes.create_string_buffer(size)
            if decompress(raw, destination, stored, size) != size:
                raise ValueError('SDK decompression failed')
            raw = destination.raw
        if flags & (1 << (i+3)) and hashlib.sha256(raw).digest() != data[160+32*i:192+32*i]:
            raise ValueError('SDK segment hash differs')
        segments.append((address, raw))
    image = bytearray(max(address+len(raw) for address,raw in segments))
    for address,raw in segments: image[address:address+len(raw)] = raw
    return bytes(image)


def main():
    image = sdk_image()
    # Pinned exported native C++ implementations and their C entry wrappers.
    expected = {0x9d7f8:'701f1dee', 0x9d80c:'702f1dee',
                0x9e634:'5d740eea', 0x9e638:'5f740eea'}
    for offset, prefix in expected.items():
        if image[offset:offset+4].hex() != prefix: raise ValueError('SDK TLS bytes differ')
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    sdk, tls, thread, stop = 0x60000000, 0x33000000, 0x33001000, 0x33003000
    u.mem_map(sdk,(len(image)+4095)&~4095); u.mem_write(sdk,image)
    u.mem_map(tls,0x4000)
    u.mem_write(tls+0x1fc,struct.pack('<I',thread))
    u.reg_write(arm.UC_ARM_REG_C13_C0_3,tls)
    checks = 0
    for thread_index in range(2):
        current = thread+thread_index*0x1000
        u.mem_write(tls+0x1fc,struct.pack('<I',current))
        for slot in range(32):
            address = current+0x48+4*slot
            value = 0x10000000+thread_index*0x10000+slot*256
            u.reg_write(arm.UC_ARM_REG_R0,slot);u.reg_write(arm.UC_ARM_REG_R1,value)
            u.reg_write(arm.UC_ARM_REG_LR,stop)
            u.emu_start(sdk+0x9d80c,stop,count=10)
            if u.reg_read(arm.UC_ARM_REG_PC)!=stop or u.reg_read(arm.UC_ARM_REG_R0)!=current+4*slot:
                raise AssertionError('Native void setter retains a nonzero computed address, not Result zero')
            checks += 1
            if bytes(u.mem_read(address,4)) != struct.pack('<I',value):
                raise AssertionError('Native setter writes the selected slot')
            checks += 1
            u.reg_write(arm.UC_ARM_REG_R0,slot);u.reg_write(arm.UC_ARM_REG_LR,stop)
            u.emu_start(sdk+0x9d7f8,stop,count=10)
            if u.reg_read(arm.UC_ARM_REG_PC)!=stop or u.reg_read(arm.UC_ARM_REG_R0)!=value:
                raise AssertionError('Native getter retrieves the selected thread value')
            checks += 1
    for thread_index in range(2):
        for slot in range(32):
            address = thread+thread_index*0x1000+0x48+4*slot
            value = 0x10000000+thread_index*0x10000+slot*256
            if bytes(u.mem_read(address,4)) != struct.pack('<I',value):
                raise AssertionError('TLS values remain distinct across threads and slots')
            checks += 1
    # The C Tick wrapper converts the native C++ aggregate return to u64 r0/r1.
    # Execute that wrapper with only the hardware-counter query stubbed.
    assert image[0x9e640:0x9e660].hex()=='00482de90db0a0e108d04de20d00a0e1a9750eeb03009de80bd0a0e10088bde8'
    assert image[0x9d840:0x9d850].hex()=='00080fe30010a0e3240140e31eff2fe1'
    instruction=struct.unpack_from('<I',image,0x9e650)[0]
    displacement=(instruction&0xffffff)<<2
    if displacement&(1<<25): displacement-=1<<26
    query=sdk+0x9e658+displacement
    counter=[0]
    def clock_query(engine,address,size,opaque):
        if address==query:
            destination=engine.reg_read(arm.UC_ARM_REG_R0)
            engine.mem_write(destination,struct.pack('<Q',counter[0]))
            engine.reg_write(arm.UC_ARM_REG_PC,engine.reg_read(arm.UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE,clock_query)
    for value in (96000000,(1<<33)+96000000,(1<<48)+123):
        counter[0]=value;u.reg_write(arm.UC_ARM_REG_SP,stop-16);u.reg_write(arm.UC_ARM_REG_LR,stop)
        u.emu_start(sdk+0x9e640,stop,count=20)
        actual=u.reg_read(arm.UC_ARM_REG_R0)+(u.reg_read(arm.UC_ARM_REG_R1)<<32)
        if u.reg_read(arm.UC_ARM_REG_PC)!=stop or actual!=value: raise AssertionError('SDK C Tick wrapper must return u64 r0/r1')
        checks+=1
    u.reg_write(arm.UC_ARM_REG_LR,stop);u.emu_start(sdk+0x9d840,stop,count=10)
    if u.reg_read(arm.UC_ARM_REG_R0)+(u.reg_read(arm.UC_ARM_REG_R1)<<32)!=19200000:
        raise AssertionError('Native SDK tick frequency differs')
    checks+=1
    report = {'checks':checks,'sdk_sha256':SDK_SHA,
              'native_functions':['0x9d7f8 GetTlsValue','0x9d80c void SetTlsValue'],
              'clock_functions':['0x9e640 C Tick wrapper returns u64','0x9d840 tick frequency 19200000'],
              'limits':['SDK allocation and scheduler not executed','Synthetic TLS/thread storage and hardware counter, no Eden trial']}
    output=ROOT/'build/damage-numbers/open-assets/sdk-tls-probe.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Passed {checks} original SDK TLS/clock ABI checks; no Eden trial')


if __name__ == '__main__': main()
