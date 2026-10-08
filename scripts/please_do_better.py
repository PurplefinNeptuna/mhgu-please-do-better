from paths import MOD, SCRIPTS, FORGE, DEPS, PYTHON, CONTAINER_STORAGE, input_path, BUILD_ROOT, WORK_ROOT, MOD_CONFIG
#!/usr/bin/env python3
"""Build/check the primary-config gold highlight candidate. Never install or launch."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zipfile

import mhgu_binary as binary
from native_support import snapshot

from paths import ROOT, MOD, SCRIPTS, FORGE, DEPS, PYTHON, CONTAINER_STORAGE, input_path, BUILD_ROOT, WORK_ROOT, MOD_CONFIG
RECIPE = MOD
WORK = WORK_ROOT
OUT = BUILD_ROOT
VERSION = MOD_CONFIG['version']
CANDIDATE = OUT / 'delivery' if MOD_CONFIG.get('candidate') else OUT / 'candidates' / VERSION
MEMBER = 'Please do Better/romfs/nativeNX/plugins/please_do_better.nro'
ARCHIVE = 'please-do-better-' + VERSION + '-candidate.zip'
SUPPORT = {'README.md': 'README.md', 'NOTICES.txt': 'THIRD_PARTY.md',
           'MANUAL_TESTS.md': 'MANUAL_TESTS.md', 'IMPLEMENTATION.md': 'IMPLEMENTATION.md',
           'VALIDATION.md': 'CONFIG_CANDIDATE.md', 'RESEARCH.md':'RESEARCH.md',
           'DIAGNOSTICS.md':'R15_RELEASE.md'}
CALLBACKS = {'init', 'fini', 'forge_onLoad', 'forge_onInit', 'forge_onUpdate',
             'forge_onImGuiInit', 'forge_onImGuiRender', 'forge_onImGuiFreeRender'}
ALLOWED_IMPORTS = {'forge_mem_getMainTextAddr', 'forge_log', 'igTreeNode_Str', 'igTreePop',
                   'forge_singleton_getInstanceByName', 'igGetIO_Nil', 'igGetTime', 'igGetBackgroundDrawList_Nil', 'ImDrawList_AddLine', 'ImDrawList_PushClipRect', 'ImDrawList_PopClipRect',
                   'igText', 'igTextUnformatted', 'igSetCurrentContext', 'igSetAllocatorFunctions'}
LIMITS = ['User confirmed r14 gold highlighting working on the tested Eden reward grid; installed hash and matching log/screenshot retained. R15 removes verbose render logging only. Forge menu corruption with simultaneous background overlays is unresolved and outside this release; broader gameplay and Ryujinx coverage remain pending.',
          'Gold borders and procedural markers implemented for verified 2D reward frames on the native direct and one-frame parallel presentation routes. GPU/gameplay alignment remains pending; offset/half targets and unknown shaders are suppressed.',
          'Flush results/barriers/readback do not establish Eden CPU translation freshness.',
          'Reward probability, quest return/restart and multicore behavior remain unverified.',
          'Second site broader gameplay role is incompletely traced; 0x102 check is preserved.',
          'Ryujinx compatibility is untested for this plugin; no native Switch support claim.']


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def write_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')


def sources():
    return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(RECIPE.rglob('*'))
            if p.is_file() and not any(x in p.relative_to(RECIPE).parts for x in ('build','work','tools','.venv','__pycache__','history')) and p.name!='build.local.json'}


def baseline():
    from paths import check_dependencies
    from native_support import snapshot
    check_dependencies()
    return snapshot()


def validate_inputs():
    main_path = input_path('main')
    image, segments = binary.main_image(main_path.read_bytes())
    rows = re.findall(r'\{(0x[0-9a-f]+)u,\s*\{([^}]+)\}\}', (RECIPE / 'src/patches.h').read_text())
    require(len(rows) == 2, 'Expected exactly two signature windows')
    evidence = json.loads((MOD / 'research/patch-sites.json').read_text())
    sites = []
    for (offset, values), old in zip(rows, evidence['patch_sites']):
        start = int(offset, 16)
        words = [int(v.strip().removesuffix('u'), 16) for v in values.split(',') if v.strip()]
        require(len(words) == 8, 'Expected 32-byte signature')
        window = struct.pack('<8I', *words)
        require(start == int(old['surrounding_start'], 16) and window.hex() == old['surrounding_bytes'],
                'Signature differs from handoff')
        require(image[start:start+32] == window, f'Original NSO signature mismatch: {offset}')
        require(start+12 == int(old['main_offset'], 16) and words[3] == int(old['original_word'], 16),
                'Unexpected patch offset/original')
        sites.append({'window': start, 'offset': start+12, 'original': words[3],
                      'replacement': 0xe3a00001, 'bytes': window.hex()})
    require([s['offset'] for s in sites] == [0x3822dc, 0x4d17f4], 'Patch scope changed')
    hook_rows=re.findall(r'\{(0x[0-9a-f]+),(0x[0-9a-f]+),0,\{([^}]+)\},(true|false)\}',
                         (RECIPE/'src/signatures.h').read_text())
    require(len(hook_rows)==22,'Unexpected r4 hook inventory')
    for site,window,words,paired in hook_rows:
        start=int(window,16);values=[int(x,16) for x in words.split(',')]
        require(len(values)==8 and image[start:start+32]==struct.pack('<8I',*values),f'R2 original window differs: {window}')
        require(start<=int(site,16)<=start+24,'Displaced words escape signature window')
    rendering=[]
    for site,window,values in re.findall(r'\{(0x[0-9a-f]+),(0x[0-9a-f]+),uint32_t\(uintptr_t\(pdb_gateway_\d+\)\),\s*\{([^}]+)\}',(RECIPE/'src/highlight_gate.h').read_text()):
        words=[int(x.strip(),16) for x in values.split(',')]
        require(len(words)==8 and image[int(window,16):int(window,16)+32]==struct.pack('<8I',*words),'Rendering boundary signature differs')
        rendering.append(dict(site=site,window=window,original_words=words,published=True))
    require([r['site'] for r in rendering]==['0x00a4fe50','0x0086a330'],'Unexpected rendering inventory')
    require(struct.unpack_from('<3I', image, 0x4d1804) == (0xe1a00004, 0xe3001102, 0xebf6797d),
            'Second site 0x102 continuation differs')
    cheat = MOD / 'vendor/wiki-cheats' / 'Always Lucky/cheats/FB08F1D20FD1204F.txt'
    require(sha(cheat.read_bytes()) == '378d0df1a25845bdf3d315dd38b6d6de1dedaf4c34d25475de4e8a6c2d9a4351',
            'Two-site cheat input changed')
    # Check the recipe itself before compile, not only its external input.
    require('constexpr uint32_t replacement = 0xe3a00001u;' in (RECIPE / 'src/patches.h').read_text(),
            'Replacement instruction changed')
    report = {'main': str(main_path), 'sha256': binary.MAIN_SHA,
              'build_id': binary.BUILD_ID[:32].upper(), 'sites': sites,
              'hooks': [{'site':site,'window':window,'paired':paired=='true','original_words':words}
                           for site,window,words,paired in hook_rows],
              'text_bytes': len(segments[0][1]), 'runtime_identity': 'Title + exact signatures, not full build ID'}
    report['highlight_boundaries']=rendering
    write_json(OUT / 'input-validation.json', report)
    return report


def host_tests():
    results = []
    destination = WORK / 'tests'
    destination.mkdir(parents=True, exist_ok=True)
    for name in ('transaction', 'native_platform', 'preferences', 'attribution', 'hooks', 'highlight', 'settings_storage'):
        inputs = [RECIPE / f'tests/{name}.cpp']
        flags = ['-std=c++17', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                 '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-fno-pie', '-no-pie']
        if name == 'settings_storage':
            mock=destination/'mock/forge';mock.mkdir(parents=True,exist_ok=True)
            (mock/'fs.h').write_text('#pragma once\nbool forge_fs_mountSaveData();\nvoid forge_fs_unmountSaveData();\n')
            (mock/'log.h').write_text('#pragma once\nvoid forge_log_warn(const char*,...);\nvoid forge_log_info(const char*,...);\n')
            flags += ['-I',str(mock.parent)]
        if name == 'native_platform':
            flags += ['-DPDB_HOST_PLATFORM_TEST']
            inputs += [RECIPE / 'src/native_platform.cpp']
        exe = destination / name
        binary.run(['g++', *flags, '-I', RECIPE / 'src', '-I', RECIPE / 'tests', *inputs, '-o', exe])
        result = subprocess.run([str(exe)], capture_output=True, text=True,
                                # LeakSanitizer cannot run under this host's ptrace sandbox.
                                env=dict(os.environ, ASAN_OPTIONS='detect_leaks=0'))
        (destination / f'{name}.log').write_text(result.stdout + result.stderr)
        require(result.returncode == 0, f'{name} failed: {destination / (name + ".log")}')
        results.append({'test': name, 'status': 'passed', 'output': result.stdout.strip()})
        print(result.stdout.strip())
    write_json(OUT / 'host-tests.json', results)
    return results


def inspect_binary(payload, inventory):
    nro = binary.Nro(payload)
    imports = {name.decode() for name, entry, *_ in nro.symbols if name and entry[5] == 0}
    exports = {name.decode() for name, entry, *_ in nro.symbols if name and entry[5] != 0}
    require(exports == CALLBACKS, f'Unexpected callbacks/exports: {exports}')
    from native_support import nso_exports
    sdk = input_path('sdk')
    require(sha(sdk.read_bytes()) == '9a9b7035266637ee693a32da6b0fde54bda00e897bef05b1c8d8cda30f8ac8b0', 'SDK fingerprint differs')
    sdk_imports = nso_exports(sdk)
    extra = {'nnosAllocateTlsSlot','nnosGetTlsValue','nnosSetTlsValue',
             'forge_fs_mountSaveData','forge_fs_unmountSaveData','igCheckbox','igButton', 'memcpy'}
    fs_imports = set(re.findall(r'asm\("([^"]+)"\)', (RECIPE / 'src/sdk_fs.h').read_text()))
    fs_imports |= set(re.findall(r'asm\("([^"]+)"\)', (RECIPE / 'src/sdk_tls.h').read_text()))
    require(imports <= ALLOWED_IMPORTS | extra | fs_imports, f'Unexpected imports: {imports-ALLOWED_IMPORTS-extra-fs_imports}')
    targets = [entry for entry in inventory if 'exports' in entry]
    require({e['emulator'] for e in targets} == {'configured'}, 'Missing installed Forge inventories')
    for target in targets:
        require(imports <= set(target['exports']) | sdk_imports, f'Unresolved imports: {target["path"]}')
    native = WORK / 'native'
    readelf = (native / 'readelf.txt').read_text()
    disassembly = (native / 'disassembly.txt').read_text()
    require('.init_array' not in readelf and '.fini_array' not in readelf,
            'Unsupported dynamic static initialization')
    require(not re.search(r'\bmsr\b.*(?:APSR_g|APSR_nzcvqg|CPSR_(?:c|x|s|fs))', disassembly, re.I),
            'Forbidden flag-register write')
    # ARM signed/unsigned parallel add/subtract families change GE even without
    # an S suffix. Saturating/halving variants do not, but none are needed here.
    require(not re.search(r'\b(?:s|u)(?:add8|add16|sub8|sub16|asx|sax)\w*\s',disassembly,re.I),
            'Gateway helper contains a GE-writing parallel arithmetic instruction')
    msr_words=re.findall(r'\b([0-9a-f]{8})\s+msr\s',disassembly,re.I)
    require(msr_words and set(msr_words)=={'e128f002'},'Only audited NZCVQ restore may write flags')
    svcs = re.findall(r'\bsvc\s+(0x[0-9a-f]+)', disassembly)
    require(sorted(int(x, 16) for x in svcs) == [6, 0x16, 0x29, 0x4b, 0x4c, 0x5f], 'Unexpected SVC scope')
    require('dsb\tsy' in disassembly and re.search(r'\bisb\b', disassembly), 'Missing executable barriers')
    bss = struct.unpack_from('<I', payload, 56)[0]
    # R14 bounded telemetry adds code/format strings; arena and BSS limits stay fixed.
    require(bss <= 81920 and len(payload) <= 81920, 'Unexpected allocation-free plugin size')
    # Loader relocations must target in-image storage and use supported ARM types.
    relocations = []
    for addr_tag, size_tag in ((17, 18), (23, 2)):
        if addr_tag not in nro.tags:
            continue
        start, size = nro.tags[addr_tag], nro.tags[size_tag]
        nro.region(start, size)
        require(size % 8 == 0, 'Malformed ARM REL table')
        for pos in range(start, start+size, 8):
            address, info = struct.unpack_from('<II', payload, pos)
            require(address % 4 == 0 and address+4 <= len(payload)+bss and info >> 8 < nro.count,
                    'Invalid relocation target/symbol')
            require(info & 255 in (2, 21, 22, 23), 'Unsupported ARM relocation')
            relocations.append({'address': address, 'type': info & 255})
    report = {'nro_sha256': sha(payload), 'nro_bytes': len(payload), 'bss_bytes': bss,
              'imports': sorted(imports), 'exports': sorted(exports), 'relocations': relocations,
              'CodeMemory_objects_added': 1, 'plugin_heap_allocations': 0,
              'forbidden_APSR_g_instructions': 0, 'runtime': 'NOT RUN',
              'installed_inventory': inventory}
    write_json(OUT / 'binary-validation.json', report)
    return report


def package_candidate(payload):
    CANDIDATE.mkdir(parents=True, exist_ok=True)
    target = CANDIDATE / MEMBER
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    archive = CANDIDATE / ARCHIVE
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
        info = zipfile.ZipInfo(MEMBER, (1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        zipped.writestr(info, payload)
    for name, source in SUPPORT.items():
        shutil.copyfile(RECIPE / source, CANDIDATE / name)
    (CANDIDATE/'VALIDATION.md').write_text((RECIPE/'CONFIG_CANDIDATE.md').read_text()+
        '\nNRO SHA-256: '+sha(payload)+'\nZIP SHA-256: '+sha(archive.read_bytes())+'\n')
    if os.environ.get('MHGU_DIAGNOSTICS','0')=='1':
        (CANDIDATE/'VALIDATION.md').write_text('Development diagnostics candidate; not approved for release. No gameplay run.\nNRO SHA-256: '+sha(payload)+'\nZIP SHA-256: '+sha(archive.read_bytes())+'\n')
    report = {'mod': 'please-do-better', 'version': VERSION, 'diagnostics':os.environ.get('MHGU_DIAGNOSTICS','0')=='1', 'status': 'DEVELOPMENT',
              'package_name': 'Please do Better', 'target': 'MHGU Nintendo Switch 1.4.0; Forge 1.4.1',
              'settings_save_paths':['savedata:/please_do_better.ini'],
              'settings_format':'One force_miraculous setting; no version marker; existing version=2 accepted',
              'settings_backup_access':False, 'settings_save_policy':'validate, write, flush, readback verification, commit; session retained on failure',
              'build_id': binary.BUILD_ID[:32].upper(), 'runtime_inventory': {MEMBER: sha(payload)},
              'archive': {'name': ARCHIVE, 'sha256': sha(archive.read_bytes())},
              'sources': sources(), 'evidence': {
                  p.name: sha(p.read_bytes()) for p in sorted(OUT.glob('*-validation.json'))+[OUT/'highlight-research.json']},
              'tests': {p.name: sha(p.read_bytes()) for p in (OUT / 'host-tests.json', OUT / 'arm-tests.json', OUT / 'runtime-tests.json', OUT / 'native-tests.json', OUT / 'observation-tests.json',OUT/'display-tests.json',OUT/'highlight-tests.json',OUT/'log-tests.json')},
              'support': {name: sha((CANDIDATE / name).read_bytes()) for name in SUPPORT},
              'limitations': LIMITS, 'published': False, 'runtime_tested': False}
    write_json(CANDIDATE / 'candidate-manifest.json', report)
    lines = [f'{sha(p.read_bytes())}  {p.relative_to(CANDIDATE)}' for p in sorted(CANDIDATE.rglob('*'))
             if p.is_file() and p.name != 'SHA256SUMS']
    (CANDIDATE / 'SHA256SUMS').write_text('\n'.join(lines) + '\n')
    verify_candidate()
    return archive


def verify_candidate():
    manifest = json.loads((CANDIDATE / 'candidate-manifest.json').read_text())
    require(manifest['status'] == 'DEVELOPMENT' and manifest['sources'] == sources(), 'Stale candidate sources')
    spec = json.loads((RECIPE / 'DISTRIBUTION.json').read_text())
    require(spec['mod']=='please-do-better','Candidate identity differs from distribution record')
    expected = {MEMBER, ARCHIVE, 'candidate-manifest.json', 'SHA256SUMS'} | set(SUPPORT)
    actual = {str(p.relative_to(CANDIDATE)) for p in CANDIDATE.rglob('*') if p.is_file()}
    require(actual == expected and not any(p.is_symlink() for p in CANDIDATE.rglob('*')), 'Candidate inventory differs')
    payload = (CANDIDATE / MEMBER).read_bytes()
    require(manifest['runtime_inventory'] == {MEMBER: sha(payload)}, 'Runtime hash mismatch')
    archive = CANDIDATE / ARCHIVE
    require(manifest['archive'] == {'name': ARCHIVE, 'sha256': sha(archive.read_bytes())}, 'ZIP hash mismatch')
    with zipfile.ZipFile(archive) as zipped:
        require(zipped.testzip() is None and zipped.namelist() == [MEMBER] and zipped.read(MEMBER) == payload,
                'ZIP CRC/member readback failed')
    validation_text = (CANDIDATE / 'VALIDATION.md').read_text()
    require(sha(payload) in validation_text and sha(archive.read_bytes()) in validation_text,
            'Tracked validation note has stale runtime/archive hashes')
    for field in ('support', 'evidence', 'tests'):
        for name, digest in manifest[field].items():
            path = CANDIDATE / name if field == 'support' else OUT / name
            require(sha(path.read_bytes()) == digest, f'Stale {field}: {name}')
    checksums = {}
    for line in (CANDIDATE / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        require(name in expected and name != 'SHA256SUMS' and name not in checksums, 'Invalid checksum inventory')
        checksums[name] = digest
        require(sha((CANDIDATE / name).read_bytes()) == digest, f'Checksum mismatch: {name}')
    require(set(checksums) == expected - {'SHA256SUMS'}, 'Incomplete checksums')
    print(f'PASS: candidate ZIP/readback/support/checksums; NRO SHA-256 {sha(payload)}')


def build():
    before = baseline()
    write_json(OUT/"highlight-research.json",json.loads((RECIPE/"research/highlight-fixtures.json").read_text()))
    validate_inputs()
    binary.run(['python3',SCRIPTS / 'please_do_better_log_probe.py'])
    host_tests()
    native = WORK / 'native'
    native.mkdir(parents=True, exist_ok=True)
    command = r'''set -eu
export PATH=/opt/devkitpro/devkitARM/bin:$PATH
arm-none-eabi-g++ --version > /output/compiler.txt
flags='-DMHGU_DIAGNOSTICS={diagnostics} -Wall -Wextra -Werror -O2 -fPIC -marm -march=armv8-a+crc+crypto -mfloat-abi=softfp -mfpu=crypto-neon-fp-armv8 -fno-exceptions -fno-rtti -fno-unwind-tables -fno-asynchronous-unwind-tables -fno-threadsafe-statics -fno-builtin -fno-tree-loop-distribute-patterns'
for unit in plugin native_platform arena runtime settings bytes; do
 arm-none-eabi-g++ -std=c++17 $flags -include /mod/vendor/forge/include/compat.h -I/mod/vendor/forge/include -isystem /mod/vendor/sdk/libs/libnx/nx/include -isystem /mod/vendor/sdk/libs/cimgui -c /mod/src/$unit.cpp -o /output/$unit.o
done
for unit in start svc gateway; do
 arm-none-eabi-gcc -fPIC -marm -c /mod/src/$unit.S -o /output/$unit.o
done
arm-none-eabi-g++ -shared -nostdlib -Wl,--hash-style=sysv,-z,max-page-size=4096,-z,noexecstack,-init=init,-fini=fini -Wl,--version-script=/mod/src/exports.txt -Wl,-T,/mod/src/plugin.ld /output/start.o /output/plugin.o /output/native_platform.o /output/arena.o /output/runtime.o /output/settings.o /output/bytes.o /output/gateway.o /output/svc.o -o /output/plugin.elf
arm-none-eabi-readelf -aW /output/plugin.elf > /output/readelf.txt
arm-none-eabi-nm -n /output/plugin.elf > /output/symbols.txt
arm-none-eabi-objdump -d /output/plugin.elf > /output/disassembly.txt
'''
    args = ['podman', '--root', CONTAINER_STORAGE, '--runroot',
            f'/tmp/mhgu-forge-container-{os.getuid()}', '--storage-driver', 'vfs', 'run', '--pull=never', '--rm',
            '--network=none', '-v', f'{MOD}:/mod:ro', '-v', f'{ROOT}:/workspace:ro', '-v', f'{native}:/output:rw',
            binary.IMAGE, 'bash', '-lc', command.replace('{diagnostics}', os.environ.get('MHGU_DIAGNOSTICS', '0'))]
    result = subprocess.run(list(map(str, args)), capture_output=True, text=True)
    (native / 'build.log').write_text(result.stdout + result.stderr)
    require(result.returncode == 0, f'ARM32 build failed: {native / "build.log"}')
    payload = binary.elf_to_nro((native / 'plugin.elf').read_bytes())
    (native / 'plugin.nro').write_bytes(payload)
    inspect_binary(payload, before)
    binary.run([PYTHON, SCRIPTS / 'please_do_better_arm_probe.py'])
    binary.run([PYTHON, SCRIPTS / 'please_do_better_runtime_probe.py'])
    binary.run([PYTHON, SCRIPTS / 'please_do_better_native_probe.py'])
    binary.run([PYTHON, SCRIPTS / 'please_do_better_observation_probe.py'])
    binary.run([PYTHON, SCRIPTS / 'please_do_better_display_probe.py'])
    binary.run([PYTHON, SCRIPTS / 'please_do_better_highlight_probe.py'])
    require(baseline() == before, 'Installed packages/maintained Forge changed during build')
    archive = package_candidate(payload)
    print(f'Built {archive}: {len(payload)} bytes; ZIP SHA-256 {sha(archive.read_bytes())}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('test', 'build', 'verify'))
    args = parser.parse_args()
    if args.command == 'build':
        build()
    elif args.command == 'test':
        baseline(); validate_inputs(); host_tests()
    else:
        inventory = baseline()
        recorded = json.loads((OUT / 'binary-validation.json').read_text())
        require(inventory == recorded['installed_inventory'], 'Installed inventory changed since validation')
        validate_inputs(); verify_candidate()


if __name__ == '__main__':
    main()
