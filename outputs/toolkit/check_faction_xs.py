"""Check the shipped XS with the pinned standalone checker, not the DE engine.

Download the author's Windows v0.2.29 release into work/xs-check/xs-check.exe:
https://github.com/Divy1211/xs-check/releases/download/v0.2.29/xs-check.exe
Run from the workspace root after packaging and installing the current draft.
"""
from pathlib import Path
import hashlib
import json
import subprocess

CHECKER = Path('work/xs-check/xs-check.exe')
EXPECTED = '12dd4aba0cf3f494e2317db90b722692783f04913f85d8f3e95cc4197c46da6e'
RELATIVE = Path('resources/_common/xs/swgb_factions.xs')
paths = {
    'staged': Path('work/faction-package') / RELATIVE,
    'packaged': Path('outputs/SWGB-DE-Factions-Draft') / RELATIVE,
    'installed': Path(r'C:\Users\aj12a\Games\Age of Empires 2 DE\76561198022514833\mods\local\SWGB-DE-Factions-Assets') / RELATIVE,
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

if digest(CHECKER) != EXPECTED:
    raise RuntimeError('Unexpected checker binary; review its provenance before updating the pin')
version = subprocess.run([str(CHECKER), '--version'], capture_output=True, text=True,
                         check=True, timeout=30).stdout.strip()
if version.splitlines()[0] != "xs-check v0.2.29: A linter for AoE2:DE's flavour of XS":
    raise RuntimeError(f'Unexpected checker version: {version}')
hashes = {name: digest(path) for name, path in paths.items()}
if len(set(hashes.values())) != 1:
    raise RuntimeError(f'Staged, packaged and installed XS differ: {hashes}')
result = subprocess.run([str(CHECKER), str(paths['staged'])], capture_output=True,
                        text=True, timeout=60)
if result.returncode != 0 or 'No errors found in file' not in result.stdout:
    raise RuntimeError(result.stdout + result.stderr)
report = {
    'standalone_syntax_and_type_check': 'PASS',
    'checker': version,
    'checker_sha256': EXPECTED,
    'checker_source': 'https://github.com/Divy1211/xs-check',
    'script_sha256': hashes,
    'output': result.stdout.strip(),
    'stderr': result.stderr.strip(),
    'engine_compilation_verified': False,
    'runtime_verified': False,
    'limits': 'Does not execute XS, validate game behavior, or prove current DE engine compatibility.',
}
Path('outputs/faction-xs-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print('PASS: XS Check 0.2.29; staged, packaged and installed scripts match. Engine/runtime unverified.')
