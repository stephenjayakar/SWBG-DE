"""Verified, reversible patch of the installed defenses.1 payload; never launches DE."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import re
import subprocess
import zlib
from stage_defenses import sha, game_closed, run
from faction_defense_ui import defense_strings, layout_hotkeys

ROOT=Path('work/defenses2')
REPORT=Path('outputs/faction-install-report.json')
DATA='SWGB-DE-Factions-Draft'
ASSETS='SWGB-DE-Factions-Assets'
DAT='resources/_common/dat/empires2_x2_p1.dat'
KEYS='resources/_common/dat/hotkeys.json'
STRINGS='resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
XS='resources/_common/xs/swgb_factions.xs'
BASE='5ce6160b66a00b6da9bbf449f655ed30327eae162f3aa79b4812e941a754a527'


def main():
    p=argparse.ArgumentParser();p.add_argument('--install',action='store_true');args=p.parse_args()
    ROOT.mkdir(parents=True,exist_ok=True)
    report=json.loads(REPORT.read_text());rows=report['installed_files']
    local=Path(report['data_mod']).resolve().parent
    assert local==Path('C:/Users/aj12a/Games/Age of Empires 2 DE/76561198022514833/mods/local').resolve()
    assert sha(local/DATA/DAT)==BASE, 'Requires installed defenses.1 baseline'
    def verify():
        for row in rows:
            assert row['mod'] in (DATA,ASSETS)
            root=(local/row['mod']).resolve();path=(root/row['path']).resolve()
            assert path.is_relative_to(root) and sha(path)==row['sha256'],row['path']
    verify()
    (ROOT/'install-report-before.json').write_bytes(REPORT.read_bytes())
    raw=ROOT/'baseline.raw';raw.write_bytes(zlib.decompress((local/DATA/DAT).read_bytes(),-15))
    candidate=ROOT/'candidate.raw'
    run('extend-defense-menu',raw,candidate)
    run('audit-defense-extension',candidate,ROOT/'restored.raw',raw)
    assert (ROOT/'restored.raw').read_bytes()==raw.read_bytes(), 'Unexpected changes outside reviewed defense fields'
    run('roundtrip',candidate,ROOT/'roundtrip.raw')
    assert (ROOT/'roundtrip.raw').read_bytes()==candidate.read_bytes()
    rosters=json.loads(Path('outputs/faction-roster-report.json').read_text())
    layout=Path(__file__).with_name('faction_defense_extension.h').read_text()
    mapping={int(uid):int(button) for cases,button in re.findall(r'((?:case\s+\d+:\s*)+)return (\d+);',layout)
             for uid in re.findall(r'case\s+(\d+):',cases)}
    assert len(mapping)==7
    changed_keys={};coverage={};menus={}
    for mode in ('military','defense'):
        path=ROOT/f'menu-{mode}.tsv';run('construction-menu-report',candidate,path,mode)
        menus[mode]=list(csv.DictReader(path.open(),delimiter='\t'))
        for civ,sc in ((1,1),(2,3)):
            reachable={u['id'] for u in rosters[str(sc)]['production_roster']}
            source={int(r['id']):r for r in menus[mode] if r['dataset']=='source' and int(r['civ'])==sc}
            current=[r for r in menus[mode] if r['dataset']=='current' and int(r['civ'])==civ and int(r['id']) in reachable]
            visible=set();slots={}
            for row in current:
                uid=int(row['id']);kind=int(row['interface']);button=int(row['button']);loc=int(row['location'])
                if loc not in (118,13) or kind not in (2,10):continue
                assert 1<=button<=13 and int(row['icon'])>=0 and int(row['hotkey'])>=1000000,row
                # Upgrade variants share their original source family position.
                family=(source[uid]['interface'],source[uid]['button'])
                slot=(loc,kind,button)
                assert slot not in slots or slots[slot]==family, ('Cross-family collision',mode,civ,row,slots.get(slot))
                slots[slot]=family;visible.add(uid)
                if uid in mapping:
                    assert mode=='defense' and kind==10 and button==mapping[uid]
                    changed_keys[int(row['hotkey'])]='QWERTASDFGZXCVB'[button-1]
            coverage.setdefault(civ,set()).update(visible)
            expected={uid for uid,r in source.items() if uid in reachable and int(r['location']) in (118,13) and 1<=int(r['button'])<=13}
            if mode=='defense':assert expected<=coverage[civ],('Unreachable buildings',civ,expected-coverage[civ])
    hotkeys=json.loads((local/DATA/KEYS).read_text());applied=set()
    for group in hotkeys['hotkey_group_list']:
        for entry in group['hotkey_list']:
            ids=set(entry.get('string_index_list',[]))&set(changed_keys)
            if ids:
                assert len(ids)==1
                uid=next(iter(ids));assert uid not in applied;applied.add(uid)
                for default in entry['defaults_list']:default['key']=changed_keys[uid]
    assert applied==set(changed_keys)
    hotkeys['hotkey_group_list'].append(dict(data_name='SWGB_CONSTRUCTION_LAYOUTS',name_string_id=898011,hotkey_list=layout_hotkeys()))
    original=(local/ASSETS/STRINGS).read_text(encoding='utf-8')
    strings={int(line.split(' ',1)[0]):json.loads(line.split(' ',1)[1]) for line in original.splitlines() if line.strip()}
    strings.update(defense_strings())
    prefix=Path(__file__).with_name('faction_defense_shields.xs').read_text(encoding='ascii')
    old_xs=(local/ASSETS/XS).read_bytes()
    assert b'swgbDefenseShieldTick' not in old_xs
    script=prefix.encode('ascii')+b'\n'+old_xs
    checker=Path('work/xs-check/xs-check.exe')
    assert sha(checker)=='12dd4aba0cf3f494e2317db90b722692783f04913f85d8f3e95cc4197c46da6e'
    test_script=ROOT/'swgb_factions.xs';test_script.write_bytes(script)
    lint=subprocess.run([str(checker),str(test_script)],capture_output=True,text=True,timeout=60)
    assert lint.returncode==0 and 'No errors found in file' in lint.stdout and 'warning' not in lint.stdout.lower(),lint.stdout+lint.stderr
    host=json.loads((ROOT/'shield-host-validation.json').read_text())
    assert host['passed'] and host['source_sha256']==hashlib.sha256(prefix.encode()).hexdigest()
    maps=list((local/ASSETS/'resources/_common/random-map-scripts').glob('SWGB Factions *.rms'))
    assert len(maps)==20 and all('#includeXS swgb_factions.xs' in m.read_text() for m in maps)
    compressor=zlib.compressobj(9,zlib.DEFLATED,-15)
    compressed=compressor.compress(candidate.read_bytes())+compressor.flush()
    assert zlib.decompress(compressed,-15)==candidate.read_bytes()
    payload={(DATA,DAT):compressed,(DATA,KEYS):(json.dumps(hotkeys,indent=2)+'\n').encode(),
             (ASSETS,STRINGS):''.join(f'{sid} {json.dumps(value,ensure_ascii=False)}\n' for sid,value in sorted(strings.items())).encode('utf-8'),
             (ASSETS,XS):script}
    for (mod,rel),body in payload.items():
        dest=ROOT/'patch'/mod/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body)
        backup=ROOT/'before'/mod/rel;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes((local/mod/rel).read_bytes())
    result=dict(passed=True,baseline_dat_sha256=BASE,candidate_dat_sha256=hashlib.sha256(compressed).hexdigest(),
        roundtrip_exact=True,collateral_restoration_exact=True,construction_coverage={c:sorted(v) for c,v in coverage.items()},
        changed_hotkeys=changed_keys,xs_lint=lint.stdout.strip(),shield_host=host,verified_baseline_files=len(rows),
        installed=False,game_launched=False,engine_verified=False,
        limits=['Native aura, demolition behavior, placement and layout research need in-game validation',
                'Shields are a bonus-health/regeneration adaptation, not the original shield pool',
                'Visible mines; source stealth/detectors unavailable','Shield controller requires SWGB Factions map'])
    if args.install:
        game_closed();verify();game_closed();written=[]
        try:
            for (mod,rel),body in payload.items():
                dest=local/mod/rel;written.append((mod,rel));dest.write_bytes(body)
                assert dest.read_bytes()==body
                match=[r for r in rows if r['mod']==mod and r['path']==rel];assert len(match)==1
                match[0]['sha256']=sha(dest)
            verify()
            report['payload_baseline_commit']='53a49193210782935c90a7c8962154d66ea58e9e'
            report['payload_changes']=['Full defensive construction access via layout switches; sea lookout',
                'Native land/air turret selectors and visible demolition mines',
                'Powered shield bonus-health/regeneration adaptation with XS controller']
            report['engine_verified']=False
            REPORT.write_text(json.dumps(report,indent=2)+'\n')
        except BaseException:
            for mod,rel in written:(local/mod/rel).write_bytes((ROOT/'before'/mod/rel).read_bytes())
            REPORT.write_bytes((ROOT/'install-report-before.json').read_bytes());raise
        result['installed']=True
    Path('outputs/defense-extension-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('construction_coverage','changed_hotkeys','xs_lint','shield_host')}))


if __name__=='__main__':main()
