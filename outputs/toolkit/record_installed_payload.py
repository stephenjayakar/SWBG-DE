"""Record the current local two-folder install in outputs/faction-install-report.json.

Use after in-place repairs to the installed mods (apply_* scripts) so share_factions.py can package them.
Refuses while DE is running. Lists every changed/new payload file; never touches the mods themselves.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess

REPORT = Path('outputs/faction-install-report.json')
NAMES = ('SWGB-DE-Factions-Draft', 'SWGB-DE-Factions-Assets')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--change', action='append', required=True, help='payload_changes entry (repeatable)')
    args = p.parse_args()
    check = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                            'if (Get-Process AoE2DE_s -ErrorAction SilentlyContinue) { exit 10 } else { exit 0 }'])
    assert check.returncode == 0, 'DE is running or process check failed; installed files may be in use'
    report = json.loads(REPORT.read_text())
    local = Path(report['asset_mod']).resolve().parent
    rows = report['installed_files']
    known = {(r['mod'], r['path']): r for r in rows}
    changed, added = [], []
    for r in rows:
        f = local / r['mod'] / r['path']
        assert f.is_file(), f'missing installed file {r["mod"]}/{r["path"]}'
        digest = sha(f)
        if digest != r['sha256']:
            r['sha256'] = digest
            changed.append(r['mod'] + '/' + r['path'])
    for name in NAMES:
        root = local / name
        for f in sorted(root.rglob('*')):
            rel = f.relative_to(root).as_posix()
            if f.is_file() and rel != 'info.json' and (name, rel) not in known:
                rows.append(dict(mod=name, path=rel, sha256=sha(f)))
                added.append(name + '/' + rel)
    report['payload_changes'] = args.change
    report['engine_verified'] = False
    REPORT.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(changed=changed, added=added, files=len(rows)), indent=2))


if __name__ == '__main__':
    main()
