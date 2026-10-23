"""Append new DE UI catalogue entries without remapping existing SWGB icon art.

Run after a game update. Does not claim to fix dataset loading or alter the DAT.
Starts from the verified installed payload, never mutable full-build staging.
"""
from pathlib import Path
import copy
import hashlib
import json
from stage_defenses import sha, game_closed

ROOT = Path('work/dataset-compat/catalog')
REPORT = Path('outputs/faction-install-report.json')
NATIVE = Path('E:/SteamLibrary/steamapps/common/AoE2DE/widgetui')


def merge(old, native):
    result = copy.deepcopy(old)
    for category, entries in native.items():
        if category not in result:
            result[category] = copy.deepcopy(entries)
        elif isinstance(entries, dict):
            for key, value in entries.items():
                result[category].setdefault(key, copy.deepcopy(value))
        elif isinstance(entries, list):
            # materials.json has named MaterialDef/AtlasDef/TextureDef records.
            def identity(row):
                kind = next(iter(row))
                return kind, row[kind]['Name']
            by_name = {identity(row): row for row in result[category]}
            # Native catalogues include a few identical duplicate definitions.
            assert all(by_name[identity(row)] == row for row in result[category])
            for row in entries:
                key = identity(row)
                if key not in by_name:
                    result[category].append(copy.deepcopy(row))
                    by_name[key] = result[category][-1]
                elif key[0] == 'AtlasDef':
                    dest = by_name[key]['AtlasDef']['Textures']
                    existing = {t['RefName'] for t in dest}
                    dest.extend(copy.deepcopy(t) for t in row['AtlasDef']['Textures'] if t['RefName'] not in existing)
    return result


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    report = json.loads(REPORT.read_text())
    local = Path(report['data_mod']).resolve().parent
    rows = report['installed_files']
    for row in rows:
        root = (local / row['mod']).resolve()
        file = (root / row['path']).resolve()
        assert file.is_relative_to(root) and sha(file) == row['sha256'], row['path']
    changes = []
    payload = {}
    for filename in ('icons.json', 'materials.json'):
        rel = 'widgetui/' + filename
        old_bytes = (Path(report['data_mod']) / rel).read_bytes()
        old = json.loads(old_bytes)
        native = json.loads((NATIVE / filename).read_text())
        new = merge(old, native)
        # Idempotent, with every old icon slot and material definition retained.
        assert merge(new, native) == new
        if filename == 'icons.json':
            for category, values in old.items():
                assert all(new[category][k] == v for k, v in values.items())
            assert all(set(v) <= set(new[k]) for k, v in native.items())
            added = sum(len(new[k]) - len(old.get(k, {})) for k in new)
        else:
            added = 0
            for category, values in old.items():
                for before, after in zip(values, new[category]):
                    if 'AtlasDef' in before:
                        x=copy.deepcopy(after);x['AtlasDef']['Textures']=x['AtlasDef']['Textures'][:len(before['AtlasDef']['Textures'])]
                        assert x == before
                    else:
                        assert before == after
                added += len(new[category]) - len(values)
        data = (json.dumps(new, indent=2) + '\n').encode()
        path = ROOT / filename
        path.write_bytes(data)
        (ROOT / ('before-' + filename)).write_bytes(old_bytes)
        payload[rel] = data
        changes.append(dict(path=rel, added_entries=added, before_sha256=hashlib.sha256(old_bytes).hexdigest(),
                            after_sha256=sha(path), native_sha256=sha(NATIVE / filename)))
    before_report = REPORT.read_bytes()
    (ROOT/'install-report-before.json').write_bytes(before_report)
    game_closed()
    written=[]
    try:
        for rel, data in payload.items():
            file=Path(report['data_mod'])/rel
            record=next(r for r in rows if r['mod']=='SWGB-DE-Factions-Draft' and r['path']==rel)
            assert sha(file)==record['sha256']
            file.write_bytes(data);written.append(rel)
            assert file.read_bytes()==data
            record['sha256']=sha(file)
        report['payload_baseline_commit']='bae79c2a287185f70aa5c86853010aabf8e9c437'
        report['payload_changes']=['Append current DE UI catalogue entries; preserve all prior SWGB icon mappings and gameplay data']
        REPORT.write_text(json.dumps(report,indent=2)+'\n')
    except BaseException:
        for rel in written:(Path(report['data_mod'])/rel).write_bytes((ROOT/('before-'+Path(rel).name)).read_bytes())
        REPORT.write_bytes(before_report)
        raise
    result=dict(passed=True,installed=True,verified_baseline_files=len(rows),changes=changes,
                dat_unchanged=True,assets_unchanged=True,existing_icon_mappings_unchanged=True,
                engine_verified=False,dataset_load_fix_confirmed=False)
    Path('outputs/ui-catalog-update-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
