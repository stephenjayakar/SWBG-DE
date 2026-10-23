"""Apply the count predicates and their matching groups after fresh validation."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path('outputs/SWGB-DE-Factions-Draft')
PATCH = Path('work/original-ai/patch')
WORK = Path('work/classic-counts')
MANIFEST = Path('outputs/faction-package-manifest.json')
ALLOWED = {'resources/_common/ai/SWGB Classic AI.per',
           'resources/_common/dat/unitlines.json'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    prior = WORK/'faction-package-manifest.before.json'
    if not prior.exists():
        shutil.copy2(MANIFEST, prior)
    baseline = json.loads(prior.read_text())
    before = {r['path']: r for r in baseline['files']}
    assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()} == before.keys()
    for name, row in before.items():
        assert digest(ROOT/name) == row['sha256'], ('Assembly drift', name)
    ai = json.loads(Path('work/original-ai/validation.json').read_text())
    counts = json.loads(Path('work/original-ai/count-validation.json').read_text())
    assert ai['passed'] and len(ai['parser_configurations']) == 81 and counts['passed']
    for name, sha in counts['tool_hashes'].items():
        assert digest(Path('outputs/toolkit')/name) == sha, ('Stale count tools', name)
    assert {r['path']: r['sha256'] for r in ai['files']} == counts['files'], 'Validation payloads differ'
    changes = []
    for row in ai['files']:
        name = row['path']
        assert name in before and digest(PATCH/name) == row['sha256'], ('Stale validation', name)
        if row['sha256'] != before[name]['sha256']:
            assert name in ALLOWED, ('Unexpected change', name)
            changes.append(dict(**row, before_sha256=before[name]['sha256']))
    assert {r['path'] for r in changes} == ALLOWED
    assert before['resources/_common/dat/empires2_x2_p1.dat']['sha256'] == '47802b6088a2255aec2c538b3b30a491ea9ad09f278c04eb781bef8ea5b79f4a'
    for row in changes:
        name = row['path']
        backup = WORK/'assembly-before'/name
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(ROOT/name, backup)
        assert digest(backup) == row['before_sha256']
        shutil.copy2(PATCH/name, ROOT/name)
        before[name] = {k: row[k] for k in ('path', 'sha256', 'bytes')}
    for name, row in before.items():
        assert digest(ROOT/name) == row['sha256'], ('Post-assembly drift', name)
    baseline.update(files=list(before.values()), total_bytes=sum(r['bytes'] for r in before.values()),
                    status='Classic AI source army count groups; game verification pending')
    MANIFEST.write_text(json.dumps(baseline, indent=2)+'\n')
    result = dict(passed=True, files=changes, count_checks=counts['checks'],
                  parser_configurations=81, classic_checks=ai['checks'],
                  unchanged_files=len(before)-len(changes), binary_dat_unchanged=True,
                  engine_verified=False, full_behavior_parity=False,
                  limitations=counts['limitations'])
    Path('outputs/classic-count-validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
