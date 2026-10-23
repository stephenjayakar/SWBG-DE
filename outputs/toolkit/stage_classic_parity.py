"""Stage the nursery/Classic follow-up against its fixed, two-faction checkpoint."""
from pathlib import Path
import csv,hashlib,json,re,shutil

work=Path('work/classic-parity');patch=work/'patch'
root=Path('outputs/SWGB-DE-Factions-Draft')
baseline=work/'faction-package-manifest.before.json'
assert baseline.exists(), 'Snapshot the current assembly before starting'
prior=json.loads(baseline.read_text())
old={r['path']:r for r in prior['files']}
for name,r in old.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==r['sha256'],('Baseline drift',name)
validation=json.loads(Path('work/original-ai/validation.json').read_text())
assert validation['passed'] and len(validation['parser_configurations'])==81
for r in validation['files']:
    name=r['path'];source=Path('work/original-ai/patch')/name
    assert hashlib.sha256(source.read_bytes()).hexdigest()==r['sha256']
    assert name in old
    if r['sha256']!=old[name]['sha256']:
        dest=patch/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest)

name='resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
source=Path('work/original-ai/patch')/name
text=source.read_text()
hint=' Select your captured herdable, then Alt + right-click this completed Nursery to garrison it. Capacity: 10 animals. Select the Nursery and use Ungarrison to release them.'
nurseries={319,320,321,322,3550,3551,3552,3553}
language=list(csv.DictReader(Path('work/economy-repair/dependencies/language-ids.tsv').open(),delimiter='\t'))
# The DAT stores help IDs with the engine's +79000 offset. Each faction has
# its own string bank; never infer IDs from the unit number alone.
help_ids={int(r['help'])-79000 for r in language if r['kind']=='unit' and r['civ'] in ('0','1','2')
          and int(r['id']) in nurseries}
assert len(help_ids)==24
for sid in sorted(help_ids):
    pattern=rf'^{sid} (".*")$'
    matches=re.findall(pattern,text,re.M);assert len(matches)==1
    value=json.loads(matches[0]);assert hint not in value
    new=json.dumps(value+hint,ensure_ascii=False)
    text,count=re.subn(pattern,lambda _:str(sid)+' '+new,text,flags=re.M)
    assert count==1
dest=patch/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text,encoding='utf-8')
print('Staged Classic AI updates and 24 nursery help strings; global XS was generated separately')
