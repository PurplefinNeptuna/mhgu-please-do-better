"""Resolve this mod's own inputs and candidate paths, in either workspace or exported form."""
from pathlib import Path
import json, sys
MOD=Path(__file__).resolve().parents[1]
SCRIPTS=MOD/'scripts'
WORKSPACE=MOD.parent.name=='mods' and (MOD.parent.parent/'scripts/mod_distribution.py').is_file()
ROOT=MOD.parent.parent if WORKSPACE else MOD
CONFIG=json.loads((MOD/'build.local.json').read_text()) if (MOD/'build.local.json').exists() else {}
# Interpret configured relative directories against this source checkout, so
# build.sh stays usable from any working directory after an independent export.
for key in ('rust_bin','cargo_home','cargo_forge','devkitarm','inputs','python'):
    if key in CONFIG and not Path(CONFIG[key]).is_absolute(): CONFIG[key]=str(MOD/CONFIG[key])
NAME='please-do-better'
VERSION='r33'
BUILD_ROOT=ROOT/('build/please-do-better/candidates/'+VERSION)
WORK_ROOT=ROOT/('work/please-do-better/candidates/'+VERSION)
CARGO_TARGET=WORK_ROOT/'cargo-target'
ELF=CARGO_TARGET/'armv7a-none-eabi/release/libplease_do_better.so'
PACKAGED_NRO=BUILD_ROOT/'package/romfs/nativeNX/plugins/please_do_better.nro'
FORGE=MOD/'vendor/forge-rs'
DEPS=MOD/'vendor'
PYTHON=Path(CONFIG.get('python',sys.executable))
CONTAINER_STORAGE=Path(CONFIG.get('container_storage',ROOT/'tools/forge-container/storage'))
def input_path(name):return Path(CONFIG.get('inputs',ROOT/'work/shared/game-exefs'))/name
