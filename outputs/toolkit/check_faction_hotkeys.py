"""Verify grid bindings after DAT serialization; no gameplay claim."""
from pathlib import Path
import csv,json
read=lambda p:list(csv.DictReader(open(p),delimiter='\t'))
manifest=read('work/faction-hotkeys.tsv')
actual=read('work/faction-target/production.tsv')
lookup={(r['kind'],r['civ'] if r['kind']=='unit' else '-1',r['id'],r['location'],r['button']):r for r in actual}
config=json.loads(Path('work/faction-package/resources/_common/dat/hotkeys.json').read_text())
native=json.loads(Path(r'E:\SteamLibrary\steamapps\common\AoE2DE\resources\_common\dat\hotkeys.json').read_text())
assert config['shared_hotkey_group_list']==native['shared_hotkey_group_list']
assert config['hotkey_group_list'][:-1]==native['hotkey_group_list']
entries=config['hotkey_group_list'][-1]['hotkey_list']
by_id={e['string_index_list'][0]:e for e in entries}
assert len(by_id)==len(entries)==len(manifest)
for r in manifest:
    key=(r['kind'],r['civ'],r['id'],r['location'],r['button'])
    assert lookup[key]['hotkey']==r['hotkey'],key
    expected='QWERTASDFGZXCVB'[int(r['button'])-1]
    assert r['key']==expected
    assert all(d['key']==expected for d in by_id[int(r['hotkey'])]['defaults_list'])
assert Path('work/factions.raw').read_bytes()==Path('work/factions-roundtrip.raw').read_bytes()
print(len(manifest),'DAT readback/grid bindings pass; native controls preserved; raw roundtrip exact')
