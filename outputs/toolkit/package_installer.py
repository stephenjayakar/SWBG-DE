"""Package the game-asset-free installer: <out>/SWGB-DE-Installer-<ver>-<label>.zip (+ .exe).

The ZIP holds the installer scripts, the asset recipe (identifiers + SHA-256 only),
the bundled vgmstream decoder and the project-authored payload (SWBG-Logic data
mod; AI, maps, XS and strings for SWBG-Data). It contains no SWGB/EF sprites,
sounds, music or DE art: Install-SWGB-DE.cmd regenerates those from the user's
own installs.

Inputs come from the repository only, so the same command works locally and in
GitHub Actions (.github/workflows/release.yml):
- payload/SWBG-Logic, payload/SWBG-Data: the shipped files (recipe.tsv "ship"
  rows, checked by SHA-256) plus each mod's info.json;
- vgmstream: the official r2117 Windows x64 release, downloaded once to
  work/downloads/ and checked against a pinned SHA-256.

    python outputs/toolkit/package_installer.py [--build HEAD] [--label <name>] [--out DIR]

The label defaults to the build commit's short hash. Afterwards the ZIP is
wrapped into the single-file .exe (build_installer_exe.py) unless --no-exe.
Does not install, upload or copy anything to Dropbox.

After a data change on the development machine, refresh the committed payload
from the local DE mods folder (outputs/faction-install-report.json) with
    python outputs/toolkit/package_installer.py --update-payload
which copies every "ship" file whose SHA-256 matches recipe.tsv.

Both paths run check_reserved_unit_ids.py on the payload first and refuse to package
any unit or unit reference in DE's reserved group-ID range 900-999 (crash at
AoE2DE_s.exe+0x1356be0), and check_civ_tech_trees.py (DE renders custom tech tree
names as empty trees), check_transports.py, check_single_ai.py (SWBG ships one AI),
check_build_menu.py and check_classic_power_placement.py. The DAT parts need genieutils-py 0.1.2 (CI installs it).

SWBG-Logic's info.json carries its own data-mod version (matching the ageofempires.com
service version of mod 549437 it corresponds to); SWBG-Data's gets VERSION.
"""
from pathlib import Path
import argparse, hashlib, io, json, shutil, subprocess, sys, urllib.request, zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[2]
VERSION = '0.0.2-dev'
LOGIC, DATA = 'SWBG-Logic', 'SWBG-Data'
# Folder names of the development install in the local DE mods folder (pre-rename).
DEV_FOLDERS = {LOGIC: 'SWGB-DE-Factions-Draft', DATA: 'SWGB-DE-Factions-Assets'}
AUTHOR = 'Local SWGB port project'
VGMSTREAM = dict(
    version='r2117',
    url='https://github.com/vgmstream/vgmstream/releases/download/r2117/vgmstream-win64.zip',
    sha256='6c4a8a3813864fefed081bbd337dbc0ad93bf88e0b92f5db98d7ab258b22dc6c',
)
FORBIDDEN = ('.smx', '.slp', '.sld', '.drs', '.wem', '.wav', '.ogg', '.mp3', '.dds', '.bina')
DOCS = ('ORIGINAL-AI.md', 'FACTION-TESTING.md', 'TODO.md', 'MUSIC-POWER.md')
RECIPE = ROOT / 'outputs/installer/installer/recipe.tsv'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def recipe_rows():
    return [l.rstrip('\n').split('\t') for l in RECIPE.read_text().splitlines() if l and not l.startswith('#')]


def vgmstream_files():
    """Return {name: bytes} from the pinned official vgmstream release (cached download)."""
    cache = ROOT / 'work/downloads' / f"vgmstream-{VGMSTREAM['version']}-win64.zip"
    if not cache.is_file():
        cache.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(VGMSTREAM['url'], timeout=120) as r:
            data = r.read()
        assert sha(data) == VGMSTREAM['sha256'], f"vgmstream download SHA-256 mismatch: {sha(data)}"
        cache.write_bytes(data)
    data = cache.read_bytes()
    assert sha(data) == VGMSTREAM['sha256'], f'Cached vgmstream ZIP SHA-256 mismatch, delete {cache}'
    out = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            assert '/' not in info.filename, info.filename
            out[info.filename] = z.read(info)
    assert 'vgmstream-cli.exe' in out and 'COPYING' in out, sorted(out)
    return out


def check_reserved_ids(payload):
    """Fail on units / unit references in DE's reserved group-ID range 900-999."""
    from check_reserved_unit_ids import check
    problems, info = check(payload / LOGIC, payload / DATA)
    assert not problems, f'{len(problems)} reserved unit-ID problems, e.g. {problems[:5]}; run remap_reserved_unit_ids.py'
    print(json.dumps(dict(reserved_unit_ids='ok', **info)))
    # Transports must be loadable in DE (class-targeted garrison tasks, see transport_garrison.py).
    from check_transports import check as check_transports
    problems, info = check_transports(payload / LOGIC)
    assert not problems, f'{len(problems)} transport problems, e.g. {problems[:5]}; run transport_garrison.py'
    print(json.dumps(dict(transport_check='ok', **info)))
    # One AI: no .ai listing files or SWGB Land AI; DE's built-in entries load SWGB Classic AI.
    from check_single_ai import check as check_single_ai
    problems = check_single_ai(payload / DATA, payload / LOGIC)
    assert not problems, f'{len(problems)} one-AI problems, e.g. {problems[:5]}; see ai_entries.py'
    print(json.dumps(dict(single_ai='ok')))


def check_tech_trees(payload):
    """Fail on civ tech trees DE would render empty or that do not match the DAT (check_civ_tech_trees.py)."""
    from check_civ_tech_trees import check
    problems, info = check(payload / LOGIC, None)
    assert not problems, f'{len(problems)} civ tech tree problems, e.g. {problems[:5]}; run check_civ_tech_trees.py'
    print(json.dumps(dict(civ_tech_trees='ok', **info)))


def check_build_menu(payload):
    """Fail on worker build menus DE would cover or hide (check_build_menu.py, fix_build_menu.py)."""
    import zlib
    import build_menu
    import reserved_unit_ids as R
    logic = payload / LOGIC
    dat = R.parse_raw(zlib.decompress((logic / R.DAT_REL).read_bytes(), -15))
    hotkeys = json.loads((logic / 'resources/_common/dat/hotkeys.json').read_text(encoding='utf-8'))
    problems, _ = build_menu.analyse(dat, hotkeys)
    assert not problems, f'{len(problems)} build-menu problems, e.g. {problems[:5]}; run fix_build_menu.py'
    print(json.dumps(dict(build_menu='ok')))
    # Classic AI Power Core placement and unpowered count (classic_ai_power_placement.py).
    subprocess.run([sys.executable, str(ROOT / 'outputs/toolkit/check_classic_power_placement.py'),
                    '--root', str(payload / DATA), '--logic', str(logic)], cwd=ROOT, check=True)


def update_payload(payload):
    """Copy the ship files from the local development mods into payload/ (dev machine only)."""
    report = json.loads((ROOT / 'outputs/faction-install-report.json').read_text())
    local = Path(report['data_mod']).parent
    n = 0
    for r in recipe_rows():
        if r[0] != 'ship':
            continue
        mod, rel, digest = r[1], r[2], r[3]
        data = (local / DEV_FOLDERS[mod] / rel).read_bytes()
        assert sha(data) == digest, (mod, rel, 'does not match recipe.tsv; rebuild the recipe first')
        target = payload / mod / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or target.read_bytes() != data:
            target.write_bytes(data)
            n += 1
    print(json.dumps(dict(payload=str(payload), updated=n)))
    check_reserved_ids(payload)
    check_tech_trees(payload)
    check_build_menu(payload)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--build', default='HEAD', help='Git commit containing the installer sources')
    p.add_argument('--label', help='Build label in the asset names (default: short commit hash)')
    p.add_argument('--payload', type=Path, default=ROOT / 'payload', help='Folder with SWBG-Logic/ and SWBG-Data/')
    p.add_argument('--out', type=Path, default=ROOT / 'outputs/releases', help='Output folder')
    p.add_argument('--no-exe', action='store_true', help='Skip the single-file .exe (build_installer_exe.py)')
    p.add_argument('--update-payload', action='store_true', help='Refresh --payload from the local DE mods folder and exit')
    args = p.parse_args()
    payload = args.payload.resolve()
    if args.update_payload:
        update_payload(payload)
        return
    check_reserved_ids(payload)
    check_tech_trees(payload)
    check_build_menu(payload)
    commit = subprocess.check_output(['git', 'rev-parse', args.build], text=True, cwd=ROOT).strip()
    label = args.label or commit[:7]
    rows = recipe_rows()
    name = f'SWGB-DE-Installer-{VERSION}-{label}'
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    stage = out / name
    dest = out / (name + '.zip')
    assert not dest.exists(), f'Installer archive already exists: {dest}'
    if stage.exists():
        assert stage.resolve().is_relative_to(out)
        shutil.rmtree(stage)
    files = {}

    def put(rel, data):
        target = stage / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        files[rel] = data

    src = ROOT / 'outputs/installer'
    for rel in ('Install-SWGB-DE.cmd', 'Repair-SWGB-DE.cmd', 'Uninstall-SWGB-DE.cmd', 'installer/Install-SWGB-DE.ps1',
                'installer/SwgbDeBuilder.cs', 'installer/recipe.tsv'):
        put(rel, (src / rel).read_bytes())
    for fname, data in sorted(vgmstream_files().items()):
        put('installer/tools/vgmstream/' + fname, data)

    expected = set()
    for r in rows:
        if r[0] != 'ship':
            continue
        mod, rel, digest = r[1], r[2], r[3]
        assert mod in (LOGIC, DATA), mod
        data = (payload / mod / rel).read_bytes()
        assert sha(data) == digest, (mod, rel, 'payload file does not match recipe.tsv')
        put(f'payload/{mod}/{rel}', data)
        expected.add(f'{mod}/{rel}')
    for mod in (LOGIC, DATA):
        info = json.loads((payload / mod / 'info.json').read_text())
        assert info['Author'] == AUTHOR and info['Title'] == mod, info
        if mod == DATA or 'Version' not in info:
            info['Version'] = VERSION  # SWBG-Logic keeps its own data-mod version
        put(f'payload/{mod}/info.json', json.dumps(info, indent=2).encode())
        expected.add(f'{mod}/info.json')
    present = {f.relative_to(payload).as_posix() for f in payload.rglob('*') if f.is_file()}
    assert present == expected, f'Unexpected/missing payload files: {sorted(present ^ expected)[:10]}'
    put('INSTALL.md', (ROOT / 'outputs/INSTALLER.md').read_bytes())
    put('CHANGELOG.md', (ROOT / 'CHANGELOG.md').read_bytes())
    for doc in DOCS:
        put('docs/' + doc, (ROOT / 'outputs' / doc).read_bytes())

    for rel in files:
        low = rel.lower()
        assert not low.endswith(FORBIDDEN), f'Game media must not be packaged: {rel}'
    manifest = [dict(path=k, sha256=sha(v), bytes=len(v)) for k, v in sorted(files.items())]
    kinds = {}
    for r in rows:
        kinds[r[0]] = kinds.get(r[0], 0) + 1
    build = dict(version=VERSION, commit=commit, label=label, kind='installer (no game assets)',
                 mods=dict(logic=LOGIC, data=DATA, published_logic=549437),
                 vgmstream=VGMSTREAM,
                 generated_by_installer=dict(sprites=kinds.get('smx', 0), sounds=kinds.get('wem', 0),
                                             music=kinds.get('musicslice', 0) + kinds.get('musiccue', 0) + kinds.get('copy', 0),
                                             icon_textures=kinds.get('icondds', 0) + kinds.get('iconpng', 0),
                                             ui_atlases=kinds.get('atlas', 0)),
                 payload_files=kinds.get('ship', 0), files=manifest)
    put('BUILD.json', json.dumps(build, indent=2).encode())

    with zipfile.ZipFile(dest, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel, data in sorted(files.items()):
            z.writestr(f'{name}/{rel}', data)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        names = z.namelist()
        assert len(names) == len(set(names)) == len(files)
        for rel, data in files.items():
            assert z.read(f'{name}/{rel}') == data
    digest = sha(dest.read_bytes())
    dest.with_suffix('.zip.sha256').write_text(f'{digest}  {dest.name}\n', newline='\n')
    print(json.dumps(dict(zip=str(dest), folder=str(stage), bytes=dest.stat().st_size, files=len(files),
                          sha256=digest, commit=commit, label=label)))
    if not args.no_exe:
        from build_installer_exe import build
        print(json.dumps(build(commit, out=out, label=label)))


if __name__ == '__main__':
    main()
