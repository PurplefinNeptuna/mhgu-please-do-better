"""Paths for a mod in this workspace or an independent source checkout."""
from pathlib import Path
import json, os, sys, shutil
MOD=Path(__file__).resolve().parents[1]
SCRIPTS=MOD/'scripts'
MOD_CONFIG=json.loads((MOD/'mod.json').read_text())
NAME=MOD_CONFIG['mod']
WORKSPACE=(MOD.parent.name=='mods' and (MOD.parent.parent/'scripts/mod_distribution.py').is_file())
ROOT=MOD.parent.parent if WORKSPACE else MOD
OUTPUT_VERSION=MOD_CONFIG.get('version') if MOD_CONFIG.get('candidate') else None
if OUTPUT_VERSION and (Path(OUTPUT_VERSION).name!=OUTPUT_VERSION or OUTPUT_VERSION in ('.','..')):
    raise ValueError('Unsafe candidate output version')
BUILD_ROOT=ROOT/'build'/NAME
WORK_ROOT=ROOT/'work'/NAME
if OUTPUT_VERSION:
    BUILD_ROOT=BUILD_ROOT/'candidates'/OUTPUT_VERSION
    WORK_ROOT=WORK_ROOT/'candidates'/OUTPUT_VERSION
CONFIG=json.loads((MOD/'build.local.json').read_text()) if (MOD/'build.local.json').exists() else {}
def configured(name, default):
    value=CONFIG.get(name)
    if name=='python' and value and '/' not in str(value):
        value=shutil.which(str(value)) or value
    return (MOD/str(value)).absolute() if value else Path(default)
FORGE=MOD/'vendor/forge'
DEPS=MOD/'vendor/sdk'
PYTHON=configured('python', ROOT/'tools/mwc-analysis-venv/bin/python' if WORKSPACE and (ROOT/'tools/mwc-analysis-venv/bin/python').exists() else MOD/'.venv/bin/python' if (MOD/'.venv/bin/python').exists() else sys.executable)
CONTAINER_STORAGE=configured('container_storage',ROOT/'tools/forge-container/storage')
def input_path(name):
    return configured(name,ROOT/'work/shared/game-exefs'/name)
def check_dependencies():
    import hashlib
    record=json.loads((MOD/'dependencies.lock.json').read_text())
    config=json.loads((MOD/'mod.json').read_text())
    if config.get('compiler_image')!=record['compiler_image']:raise ValueError('Compiler pin differs from dependency record')
    for name,expected in record['files'].items():
        p=MOD/name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
            raise ValueError('Pinned dependency differs: '+name)
    return record
