"""Install only the reviewed Savannah map over an exact verified local payload.

Refuses while DE is running. Does not touch subscribed mods, base game, AI or
data. Create the required full/data release pair with share_factions afterward.
"""
from pathlib import Path
import hashlib,json,subprocess
from faction_savannah_nova import repair_savannah_nova

ROOT=Path('work/age-crash')
REPORT=Path('outputs/faction-install-report.json')
NAME='SWGB-DE-Factions-Assets'
REL='resources/_common/random-map-scripts/SWGB Factions Savannah.rms'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda:stream.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    check=subprocess.run(['powershell.exe','-NoProfile','-Command',
        'if (Get-Process AoE2DE_s -ErrorAction SilentlyContinue) { exit 10 } else { exit 0 }'],
        capture_output=True,text=True)
    assert check.returncode==0,'DE is running or process check failed; leave installed files alone'
    stage=json.loads((ROOT/'savannah-nova-stage.json').read_text())
    validation=json.loads((ROOT/'savannah-nova-validation.json').read_text())
    assert validation['passed'] and validation['after_sha256']==stage['after']
    before=ROOT/'savannah-before.rms';candidate=ROOT/'patch'/REL
    assert sha(before)==stage['before'] and sha(candidate)==stage['after']
    assert candidate.read_text()==repair_savannah_nova(before.read_text())
    report=json.loads(REPORT.read_text());local=Path(report['asset_mod']).resolve().parent
    assert local==Path('C:/Users/aj12a/Games/Age of Empires 2 DE/76561198022514833/mods/local').resolve()
    names={NAME,'SWGB-DE-Factions-Draft'};rows=report['installed_files']
    matches=[r for r in rows if r['mod']==NAME and r['path']==REL]
    assert len(matches)==1 and matches[0]['sha256']==stage['before'],'Unexpected installed map manifest'
    for r in rows:
        assert r['mod'] in names
        root=(local/r['mod']).resolve();dest=(root/r['path']).resolve()
        assert dest.is_relative_to(root) and sha(dest)==r['sha256'],r['path']
    dest=(local/NAME/REL).resolve();assert str(dest)==str(Path(stage['source']).resolve())
    base=Path('E:/SteamLibrary/steamapps/common/AoE2DE/resources/_common/dat/empires2_x2_p1.dat')
    base_sha=sha(base)
    (ROOT/'install-report-before-nova.json').write_bytes(REPORT.read_bytes())
    check=subprocess.run(['powershell.exe','-NoProfile','-Command',
        'if (Get-Process AoE2DE_s -ErrorAction SilentlyContinue) { exit 10 } else { exit 0 }'],
        capture_output=True,text=True)
    assert check.returncode==0,'DE started or process check failed during verification; no files changed'
    dest.write_bytes(candidate.read_bytes());assert sha(dest)==stage['after']
    matches[0]['sha256']=stage['after']
    report['payload_baseline_commit']='db57ca1c0c3aee720eebb60f62c2e69142ec71bb'
    report['payload_changes']=['Savannah primary Nova placement only; AI and Data unchanged from Classic AI .4']
    report['engine_verified']=False
    REPORT.write_text(json.dumps(report,indent=2)+'\n')
    for r in rows:assert sha(local/r['mod']/r['path'])==r['sha256'],r['path']
    assert sha(base)==base_sha
    result=dict(installed=True,changed_payload_files=1,verified_payload_files=len(rows),
        path=str(dest),before_sha256=stage['before'],after_sha256=stage['after'],
        ai_and_data_unchanged=True,base_game_unchanged=True,engine_verified=False,game_launched=False)
    (ROOT/'savannah-nova-installation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
