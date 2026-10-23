"""Patch only defensive build-menu fields and their spatial hotkeys.

Starts from the verified installed Classic AI .4 / Savannah repair payload,
not the mutable full-build staging directory. Never starts the game.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import re
import subprocess
import zlib

ROOT = Path('work/defenses')
REPORT = Path('outputs/faction-install-report.json')
TOOL = Path('work/dat-build/Release/portdat.exe')
DATA = 'SWGB-DE-Factions-Draft'
DAT = 'resources/_common/dat/empires2_x2_p1.dat'
HOTKEYS = 'resources/_common/dat/hotkeys.json'
BASE_DAT = '47802b6088a2255aec2c538b3b30a491ea9ad09f278c04eb781bef8ea5b79f4a'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def game_closed():
    result = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
        'if (Get-Process AoE2DE_s -ErrorAction SilentlyContinue) { exit 10 } else { exit 0 }'],
        capture_output=True)
    assert result.returncode == 0, 'DE is running or process check failed; no installation'


def run(mode, source, output, *extra):
    subprocess.run([str(TOOL), mode, str(source), str(output), *map(str, extra)], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    report = json.loads(REPORT.read_text())
    local = Path(report['data_mod']).resolve().parent
    assert local == Path('C:/Users/aj12a/Games/Age of Empires 2 DE/76561198022514833/mods/local').resolve()
    rows = report['installed_files']
    assert sha(local / DATA / DAT) == BASE_DAT, 'Requires the last playable .4-map.1 DAT'
    for row in rows:
        assert row['mod'] in (DATA, 'SWGB-DE-Factions-Assets')
        root = (local / row['mod']).resolve()
        file = (root / row['path']).resolve()
        assert file.is_relative_to(root) and sha(file) == row['sha256'], row['path']
    (ROOT / 'install-report-before.json').write_bytes(REPORT.read_bytes())
    raw = ROOT / 'baseline.raw'
    raw.write_bytes(zlib.decompress((local / DATA / DAT).read_bytes(), -15))
    candidate = ROOT / 'candidate.raw'
    run('repair-defense-menu', raw, candidate)
    run('audit-defense-menu', candidate, ROOT / 'restored.raw', raw)
    assert (ROOT / 'restored.raw').read_bytes() == raw.read_bytes(), 'Unexpected gameplay changes'
    run('roundtrip', candidate, ROOT / 'roundtrip.raw')
    assert (ROOT / 'roundtrip.raw').read_bytes() == candidate.read_bytes()
    run('construction-menu-report', candidate, ROOT / 'menu.tsv')
    menus = list(csv.DictReader((ROOT / 'menu.tsv').open(), delimiter='\t'))
    rosters = json.loads(Path('outputs/faction-roster-report.json').read_text())
    header = Path(__file__).with_name('faction_defenses.h').read_text()
    mapping = {}
    for cases, button in re.findall(r'((?:case\s+\d+:\s*)+)return (\d+);', header):
        mapping.update({int(uid): int(button) for uid in re.findall(r'case\s+(\d+):', cases)})
    assert len(mapping) == 17 and set(mapping.values()) == {3, 4, 8, 11, 13}
    changed_hotkeys = {}
    checked = []
    remaining = []
    for civ, source_civ in ((1, 1), (2, 3)):
        reachable = {unit['id'] for unit in rosters[str(source_civ)]['production_roster']}
        current = [row for row in menus if row['dataset'] == 'current' and int(row['civ']) == civ
                   and int(row['id']) in reachable and row['location'] == '118']
        for row in current:
            uid = int(row['id'])
            if uid in mapping:
                assert int(row['interface']) == 10 and int(row['button']) == mapping[uid]
                assert int(row['icon']) >= 0 and int(row['hotkey']) >= 1000000
                key = 'QWERTASDFGZXCVB'[mapping[uid] - 1]
                changed_hotkeys[int(row['hotkey'])] = key
                checked.append(dict(civ=civ, id=uid, button=mapping[uid], key=key))
            elif row['interface'] == '10':
                assert int(row['button']) not in mapping.values(), ('Menu collision', row)
            elif row['interface'] == '11':
                remaining.append(dict(civ=civ, id=uid, name=row['name']))
        assert {mapping[int(row['id'])] for row in current if int(row['id']) in mapping} == set(mapping.values())
    # Existing upgraded variants deliberately share a slot within their own
    # upgrade family. No new cross-family or navigation collision is allowed.
    original_hotkeys = json.loads((local / DATA / HOTKEYS).read_text())
    hotkeys = json.loads(json.dumps(original_hotkeys))
    applied = set()
    for group in hotkeys['hotkey_group_list']:
        for entry in group['hotkey_list']:
            ids = set(entry.get('string_index_list', [])) & set(changed_hotkeys)
            if not ids:
                continue
            assert len(ids) == 1
            uid = next(iter(ids))
            assert uid not in applied
            applied.add(uid)
            for default in entry['defaults_list']:
                default['key'] = changed_hotkeys[uid]
    assert applied == set(changed_hotkeys)
    # Keep profile, AI, unit art, research, costs and combat data untouched.
    patch = ROOT / 'patch'
    for rel in (DAT, HOTKEYS):
        (patch / rel).parent.mkdir(parents=True, exist_ok=True)
        backup = ROOT / 'before' / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes((local / DATA / rel).read_bytes())
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    payload = compressor.compress(candidate.read_bytes()) + compressor.flush()
    assert zlib.decompress(payload, -15) == candidate.read_bytes()
    (patch / DAT).write_bytes(payload)
    (patch / HOTKEYS).write_text(json.dumps(hotkeys, indent=2) + '\n')
    result = dict(passed=True, baseline_dat_sha256=BASE_DAT,
        candidate_dat_sha256=sha(patch / DAT), roundtrip_exact=True,
        gameplay_collateral_audit_exact=True, menu_bindings=checked,
        pending_defensive_page=remaining, installed=False, game_launched=False,
        engine_verified=False, verified_baseline_files=len(rows))
    if args.install:
        game_closed()
        for row in rows:
            assert sha(local / row['mod'] / row['path']) == row['sha256'], row['path']
        game_closed()
        written = []
        try:
            for rel in (DAT, HOTKEYS):
                dest = local / DATA / rel
                written.append(rel)
                dest.write_bytes((patch / rel).read_bytes())
                assert sha(dest) == sha(patch / rel)
                match = [row for row in rows if row['mod'] == DATA and row['path'] == rel]
                assert len(match) == 1
                match[0]['sha256'] = sha(dest)
            for row in rows:
                assert sha(local / row['mod'] / row['path']) == row['sha256'], row['path']
            report['payload_baseline_commit'] = '8b5298daa56f514922fdb84e64872c4c17b413a4'
            report['payload_changes'] = ['Five core defense families exposed on military construction page; matching spatial hotkeys']
            report['engine_verified'] = False
            REPORT.write_text(json.dumps(report, indent=2) + '\n')
        except BaseException:
            for rel in written:
                (local / DATA / rel).write_bytes((ROOT / 'before' / rel).read_bytes())
            REPORT.write_bytes((ROOT / 'install-report-before.json').read_bytes())
            raise
        result['installed'] = True
    (ROOT / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('menu_bindings', 'pending_defensive_page')}))


if __name__ == '__main__':
    main()
