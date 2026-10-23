"""Apply only verified Classic PER/XS nursery replacements to the current build."""
from pathlib import Path
import hashlib,json,shutil

ROOT=Path('outputs/SWGB-DE-Factions-Draft')
WORK=Path('work/classic-nursery-engine')
PATCH=Path('work/original-ai/patch')
MANIFEST=Path('outputs/faction-package-manifest.json')
ALLOWED={'resources/_common/ai/SWGB Classic AI.per',
         'resources/_common/ai/SWGB Classic/swgb_classic_ai.xs'}


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    WORK.mkdir(parents=True,exist_ok=True)
    prior=WORK/'faction-package-manifest.before.json'
    if not prior.exists():shutil.copy2(MANIFEST,prior)
    baseline=json.loads(prior.read_text())
    before={r['path']:r for r in baseline['files']}
    assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}==before.keys()
    for name,r in before.items():assert digest(ROOT/name)==r['sha256'],('Assembly drift',name)
    ai=json.loads(Path('work/original-ai/validation.json').read_text())
    controller=json.loads(Path('work/classic-engine/nursery-controller-validation.json').read_text())
    engine=json.loads(Path('work/classic-engine/nursery-validation.json').read_text())
    assert ai['passed'] and len(ai['parser_configurations'])==81
    assert controller['passed'] and engine['passed']
    from classic_nursery_bridge import PER
    assert controller['bridge_sha256']==hashlib.sha256(PER.encode()).hexdigest()
    assert controller['xs_sha256']==digest(PATCH/'resources/_common/ai/SWGB Classic/swgb_classic_ai.xs')
    for name,sha in engine['tool_hashes'].items():assert digest(Path('outputs/toolkit')/name)==sha,name
    changes=[]
    for r in ai['files']:
        name=r['path']
        assert name in before and digest(PATCH/name)==r['sha256'],('Stale AI validation',name)
        if r['sha256']!=before[name]['sha256']:
            assert name in ALLOWED,('Unexpected change',name)
            changes.append(dict(**r,before_sha256=before[name]['sha256']))
    assert {r['path'] for r in changes}==ALLOWED
    assert before['resources/_common/dat/empires2_x2_p1.dat']['sha256']=='47802b6088a2255aec2c538b3b30a491ea9ad09f278c04eb781bef8ea5b79f4a'
    for r in changes:
        name=r['path'];backup=WORK/'assembly-before'/name
        backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():shutil.copy2(ROOT/name,backup)
        assert digest(backup)==r['before_sha256']
        shutil.copy2(PATCH/name,ROOT/name)
        before[name]={k:r[k] for k in ('path','sha256','bytes')}
    for name,r in before.items():assert digest(ROOT/name)==r['sha256'],('Post-assembly drift',name)
    baseline.update(files=list(before.values()),total_bytes=sum(r['bytes'] for r in before.values()),
                    status='Classic AI individual nursery commands; game verification pending')
    MANIFEST.write_text(json.dumps(baseline,indent=2)+'\n')
    report=dict(passed=True,files=changes,source_checks=engine['checks'],controller_cases=controller['cases'],
                classic_checks=ai['checks'],parser_configurations=81,unchanged_files=len(before)-len(changes),
                binary_dat_unchanged=True,global_nursery_income_unchanged=True,default_ai_unchanged=True,
                engine_verified=False,full_behavior_parity=False,
                limitations=controller['limitations'])
    Path('outputs/classic-nursery-engine-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Assembled',len(changes),'Classic AI files;',len(before)-len(changes),'unchanged; runtime pending')


if __name__=='__main__':main()
