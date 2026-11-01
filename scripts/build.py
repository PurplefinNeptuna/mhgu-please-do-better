#!/usr/bin/env python3
"""Offline standalone candidate build. No command installs, activates or starts a game."""
import argparse, hashlib, json, os, shutil, subprocess, sys, zipfile
from html import escape
from pathlib import Path
from paths import MOD, ROOT, CONFIG, BUILD_ROOT, WORK_ROOT, CARGO_TARGET, PYTHON, VERSION, ELF, input_path

NRO='please_do_better.nro'
PROBES=('please_do_better_arm_probe','please_do_better_runtime_probe','please_do_better_native_probe','please_do_better_observation_probe','please_do_better_display_probe','please_do_better_highlight_probe','please_do_better_quantity_probe')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def source_hashes():
    """Tie receipts to the exact owned executable recipe inputs."""
    files=['Cargo.toml','Cargo.lock','.cargo/config.toml','armv7a-none-eabi.json','build.rs']
    files+=[str(p.relative_to(MOD)) for folder in ['src','core/src','core/tests','link']
            for p in sorted((MOD/folder).rglob('*')) if p.is_file()]
    return {n:digest(MOD/n) for n in files}
def record(name,value):
    BUILD_ROOT.mkdir(parents=True,exist_ok=True);(BUILD_ROOT/name).write_text(json.dumps(value,indent=2)+'\n')
def run(args,**kw): subprocess.run(list(map(str,args)),check=True,**kw)
def environment():
    env=os.environ.copy();env.update(PDB_VERSION=VERSION)
    rust=Path(CONFIG['rust_bin']);compiler=CONFIG.get('devkitarm') or env.get('DEVKITARM')
    if not compiler: raise ValueError('Set devkitarm in build.local.json or DEVKITARM')
    env.update(CARGO_HOME=str(CONFIG['cargo_home']),RUSTUP_HOME=str(Path(CONFIG['cargo_home']).parent/'rustup'),
               RUSTUP_TOOLCHAIN='nightly',RUSTC=str(rust/'rustc'),CARGO_NET_OFFLINE='true',
               DEVKITARM=str(compiler),CARGO_TARGET_DIR=str(CARGO_TARGET))
    env['PATH']=os.pathsep.join([str(rust),str(Path(compiler)/'bin'),env.get('PATH','')])
    return env,rust
def converter(): return Path(CONFIG['cargo_forge'])
def doctor():
    env,rust=environment();lock=json.loads((MOD/'dependencies.lock.json').read_text())
    version=subprocess.check_output([rust/'rustc','--version'],env=env,text=True).strip()
    if version!=lock['rust_version']: raise ValueError('Pinned Rust version differs')
    pinned=[('rustc',rust/'rustc'),('cargo_forge',converter())]
    pinned.extend((name,Path(CONFIG['devkitarm'])/'bin'/name) for name in lock['tool_sha256'] if name.startswith('arm-none-eabi-'))
    for n,p in pinned:
        if digest(p)!=lock['tool_sha256'][n]: raise ValueError('Pinned tool differs: '+n)
    for n,h in lock['files'].items():
        if digest(MOD/n)!=h: raise ValueError('Pinned source differs: '+n)
    for n,h in lock['inputs'].items():
        if digest(input_path(n))!=h: raise ValueError('Supplied input differs: '+n)
    if digest(Path(CONFIG['rust_bin']).parent/'lib/rustlib/src/rust/library/Cargo.lock')!=digest(MOD/'research/sysroot-Cargo.lock'):
        raise ValueError('Pinned rust-src resolver differs')
    required=dict(line.split('==') for line in (MOD/'requirements.txt').read_text().split())
    run([PYTHON,'-c','import importlib.metadata as m,json,sys;r=json.loads(sys.argv[1]);a={n:m.version(n) for n in r};assert a==r,(a,r)',json.dumps(required)])
    print('PASS: pinned Rust, Forge sources, registry sources, Python packages and copied inputs')
def prepare():
    """Check every pinned hook window against the original NSO before any build."""
    doctor()
    import please_do_better as recipe
    recipe.validate_inputs()
    recipe.write_json(BUILD_ROOT/'highlight-research.json',json.loads((MOD/'research/highlight-fixtures.json').read_text()))
    print('Prepared: pinned inputs and hook windows checked')
def native_outputs(env):
    """The disassembly, readelf and symbols the audit and ARM fixtures read."""
    native=WORK_ROOT/'native';native.mkdir(parents=True,exist_ok=True)
    tools=Path(CONFIG['devkitarm'])/'bin'
    (native/'symbols.txt').write_text(subprocess.check_output([tools/'arm-none-eabi-nm','-n',ELF],text=True))
    (native/'disassembly.txt').write_text(subprocess.check_output([tools/'arm-none-eabi-objdump','-d',ELF],text=True))
    (native/'readelf.txt').write_text(subprocess.check_output([tools/'arm-none-eabi-readelf','-aW',ELF],text=True))
    shutil.copy2(BUILD_ROOT/('package/romfs/nativeNX/plugins/'+NRO),native/'plugin.nro')
def build():
    prepare();env,_=environment();lock=digest(MOD/'Cargo.lock')
    link=MOD/'target'
    if link.exists() or link.is_symlink() or (MOD/NRO).exists(): raise ValueError('Preserving existing target/ or loose NRO')
    CARGO_TARGET.mkdir(parents=True,exist_ok=True);link.symlink_to(CARGO_TARGET,target_is_directory=True)
    try: run([converter(),'forge','build','--release'],cwd=MOD,env=env)
    finally:
        link.unlink()
        if (MOD/NRO).exists(): shutil.move(MOD/NRO,CARGO_TARGET/NRO)
    if digest(MOD/'Cargo.lock')!=lock: raise ValueError('Cargo.lock changed during build')
    dest=BUILD_ROOT/('package/romfs/nativeNX/plugins/'+NRO)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(CARGO_TARGET/NRO,dest)
    native_outputs(env)
    record('build.json',{'version':VERSION,'status':'BUILT','nro_sha256':digest(dest),
        'forge_rs_revision':'d1865b68e9b194eb3eacc8bd71bbf601a5fac63e','source_sha256':source_hashes(),'runtime_test':'NOT RUN'})
def test(host=False):
    env,rust=environment()
    run([rust/'cargo','test','--locked','--config',MOD/'.cargo/vendor.toml','--manifest-path',MOD/'core/Cargo.toml',
         '--target','x86_64-unknown-linux-gnu'],cwd=MOD.parent,env=env)
    if host:
        print('PASS: host tests only; ARM probes and verify not run');return
    for name in PROBES:
        run([PYTHON,MOD/'scripts'/(name+'.py')])
    verify()
    record('tests.json',{'status':'PASSED','nro_sha256':digest(BUILD_ROOT/('package/romfs/nativeNX/plugins/'+NRO)),'host':True,'arm_verified':True,'runtime_test':'NOT RUN'})
def verify(): run([PYTHON,MOD/'scripts/verify.py'])
def package():
    spec=json.loads((MOD/'DISTRIBUTION.json').read_text())
    if spec['status'] in ('READY_TO_DISTRIBUTE','PUBLISHED'):
        raise ValueError('No distribution approval exists for this version; package() builds a candidate only')
    verify();source=BUILD_ROOT/'package';nro=source/('romfs/nativeNX/plugins/'+NRO)
    test_record=json.loads((BUILD_ROOT/'tests.json').read_text())
    if test_record['status']!='PASSED' or test_record['nro_sha256']!=digest(nro) or not test_record['arm_verified']:
        raise ValueError('Test this exact build first')
    dest=BUILD_ROOT/'delivery';dest.mkdir(parents=True,exist_ok=True)
    payloads={str(p.relative_to(source)):digest(p) for p in source.rglob('*') if p.is_file()}
    package_name=spec['package_name'];named=dest/package_name
    previous={str(p.relative_to(named)) for p in named.rglob('*') if p.is_file()}
    if previous-payloads.keys(): raise ValueError('Preserving unexpected previous candidate files')
    shutil.copytree(source,named,dirs_exist_ok=True)
    guide=(MOD/'README.md').read_text().encode();(dest/'README.md').write_bytes(guide)
    archive=dest/spec['archive']
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('README.md',guide)
        for n in sorted(payloads): z.write(source/n,package_name+'/'+n)
    import mod_distribution as distribution
    (dest/'README.html').write_bytes(distribution.readme_html(guide))
    (dest/'GAMEBANANA_README.html').write_bytes(distribution.gamebanana_readme_html(guide,spec['gamebanana']))
    # spec['notices'] is workspace-root-relative; this builder resolves both forms.
    notices='\n\n'.join(((MOD/n) if (MOD/n).is_file() else (ROOT/n)).read_text() for n in spec['notices'])
    (dest/'NOTICES.txt').write_text(notices);(dest/'NOTICES.html').write_text('<pre>'+escape(notices)+'</pre>\n')
    evidence={n:json.loads((BUILD_ROOT/(n+'.json')).read_text()) for n in ['build','verify','tests']}
    (dest/'VALIDATION.json').write_text(json.dumps(evidence,indent=2)+'\n')
    manifest={'mod':spec['mod'],'version':VERSION,'status':'DEVELOPMENT','runtime_test':'NOT RUN',
              'package_name':package_name,'payloads':payloads,'archive_sha256':digest(archive)}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (dest/'SHA256SUMS').write_text(''.join(digest(p)+'  '+str(p.relative_to(dest))+'\n'
                 for p in sorted(dest.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and z.read('README.md')==guide
        assert set(z.namelist())=={'README.md',*(package_name+'/'+n for n in payloads)}
        for n,h in payloads.items(): assert hashlib.sha256(z.read(package_name+'/'+n)).hexdigest()==h==digest(named/n)
    for line in (dest/'SHA256SUMS').read_text().splitlines():
        h,n=line.split('  ',1);assert digest(dest/n)==h
    distribution.verify_candidate(spec,ROOT)
    print('Verified active DEVELOPMENT candidate:',archive)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',nargs='?',default='build',choices=['doctor','prepare','build','test','verify','package','export'])
    p.add_argument('--host',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
    if a.command=='export':
        if a.output is None: p.error('export requires --output')
        run([PYTHON,MOD/'scripts/export_source.py','--output',a.output])
    elif a.command=='test': test(a.host)
    else: globals()[a.command]()
if __name__=='__main__':
    try: main()
    except (ValueError,OSError,subprocess.CalledProcessError) as e: print(e,file=sys.stderr);sys.exit(1)
