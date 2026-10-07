from paths import MOD, SCRIPTS, FORGE, DEPS, PYTHON, CONTAINER_STORAGE, input_path
"""Verify current standalone build receipts without parent Git history."""
from paths import ROOT
import hashlib
def verify(name, expected, root=ROOT):
    path=root/name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise ValueError('Build source changed: '+name)
