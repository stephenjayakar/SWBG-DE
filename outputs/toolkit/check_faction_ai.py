r"""Validate the AI entry points of SWBG-Data with a pinned independent parser.

SWBG ships one AI, SWGB Classic AI. DE's three built-in lobby entries reach it: "AI" through
PromiDE.per2, "AI (HD version)" through AI (HD version).per, and "AI (CD version)" through DE's own
randomgame.per2, whose first load (Promisory\defaultConstants) loads Classic while every other file
it loads is a stub (ai_entries.py). check_single_ai.py checks that nothing else is listed.

Setup (the dependency stays in ignored work/):
  git -c core.longpaths=true clone https://github.com/joerollman/aoe2-ai-parser.git work/ai-parser
  git -C work/ai-parser checkout 3dfa2583b7c2ec36b85ccb421ebd0abe9ff276ba
This is static validation, not DE engine verification.

  python outputs/toolkit/check_faction_ai.py --root payload/SWBG-Data [--de <DE install>]
"""
import argparse
import hashlib
import json
import ntpath
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ai_entries import AI_DIR, CLASSIC_FILES, DE_ENTRIES, GAMEDATA, RETIRED, STUBS, expected_files

PARSER_COMMIT = '3dfa2583b7c2ec36b85ccb421ebd0abe9ff276ba'
DE_DEFAULT = Path(r'E:\SteamLibrary\steamapps\common\AoE2DE')
parser = Path('work/ai-parser')
revision = subprocess.check_output(['git', '-C', str(parser), 'rev-parse', 'HEAD'], text=True).strip()
assert revision == PARSER_COMMIT, revision
env = dict(os.environ, PYTHONPATH=str((parser/'src').resolve()))
cli = argparse.ArgumentParser()
cli.add_argument('--root', type=Path, default=Path('payload/SWBG-Data'))
cli.add_argument('--de', type=Path, default=DE_DEFAULT, help='DE install: also lint its own PromiDE.per2 / randomgame.per2 over the stubs')
args = cli.parse_args()
root = args.root
for rel, want in expected_files().items():
    assert (root/rel).read_bytes() == want, rel
for rel in CLASSIC_FILES:
    assert (root/rel).is_file(), rel
for rel in RETIRED:
    assert not (root/rel).exists(), rel
assert not [p for p in root.rglob('*') if p.suffix.lower() in ('.ai', '.ai2')]
# Lint the ai folder with each entry as a root. DE resolves the loads of the drs/gamedata_x2
# scripts in resources/_common/ai first, where all stubs are, so the parser resolves them the same
# way. Roots:
# our PromiDE.per2 ("AI") and AI (HD version).per, and with a DE install DE's own PromiDE.per2 and
# randomgame.per2 ("AI (CD version)"), which reach SWGB Classic AI through
# Promisory\defaultConstants and otherwise only load stubs.
lintroot = Path('work/faction-ai-lint')
if lintroot.exists():
    assert lintroot.resolve().is_relative_to(Path('work').resolve())
    shutil.rmtree(lintroot)
shutil.copytree(root/AI_DIR, lintroot)
sources = {'PromiDE': root/GAMEDATA/'PromiDE.per2', 'AI (HD version)': root/AI_DIR/'AI (HD version).per'}
if args.de and (args.de/DE_ENTRIES['AI'][0]).is_file():
    sources['DE PromiDE'] = args.de/DE_ENTRIES['AI'][0]
    sources['DE randomgame'] = args.de/DE_ENTRIES['AI (CD version)'][0]
    shutil.copytree(args.de/'resources/_common/xs/ailib', lintroot/'ailib')  # DE PromiDE's (include "ailib/...")
roots = []
for stem, source in sources.items():
    (lintroot/(stem + '.per')).write_bytes(source.read_bytes())
    (lintroot/(stem + '.ai')).write_bytes(b'')
    roots.append(stem)
details_path = Path('work/faction-ai-lint.json')
result = subprocess.run([sys.executable, '-m', 'aoe2_ai_lab', 'lint-package',
                         str(lintroot), '--output', str(details_path),
                         '--fail-level', 'info'], env=env, capture_output=True, text=True)
details = json.loads(details_path.read_text())
# Unpreprocessed, SWGB Classic AI.per loads its random personality (SWGB Classic/c?-dip-*) once per
# difficulty/game-mode branch, which the package lint reports as conditional duplicate loads (42 per
# root); check_classic_ai.py lints every preprocessed configuration with zero findings. DE's own
# randomgame.per2 likewise loads some (stubbed) elite files in several branches. Those are the only
# findings allowed.
stub_names = {Path(rel).stem for rel in STUBS}
for group in details['finding_groups']:
    assert group['code'] == 'duplicate-per-load-target', group['code']
    assert set(group['confidence_counts']) == {'conditional'}, group['confidence_counts']
    for example in group['examples']:
        name, message = ntpath.basename(example['path']), example['message']
        classic = name == 'SWGB Classic AI.per' and "load target 'SWGB Classic/c" in message and '-dip-' in message
        de_stub = name == 'DE randomgame.per' and message.split("'")[1] in stub_names
        assert classic or de_stub, (name, message)
per_root = {Path(ntpath.basename(r['ai_path'])).stem: r['code_counts'] for r in details['roots']}
assert sorted(per_root) == sorted(roots), per_root
for stem, counts in per_root.items():
    assert set(counts) <= {'duplicate-per-load-target'}, (stem, counts)
assert per_root['PromiDE'] == per_root['AI (HD version)'], per_root
expected_duplicates = per_root['PromiDE'].get('duplicate-per-load-target', 0)
report = dict(parser_repository='https://github.com/joerollman/aoe2-ai-parser',
              parser_commit=revision, entry_findings=0,
              classic_conditional_personality_duplicates_per_entry=expected_duplicates,
              findings_per_root=per_root,
              entry_points=[str(s) for s in sources.values()],
              entries_load='SWGB Classic AI',
              sha256={rel: hashlib.sha256(data).hexdigest() for rel, data in expected_files().items() if b'(load' in data},
              engine_parser_verified=False, gameplay_verified=False)
Path('outputs/faction-ai-validation.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
