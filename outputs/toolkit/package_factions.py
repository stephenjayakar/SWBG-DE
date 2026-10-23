"""Assemble an uninstalled experimental build; never alters a stable release."""
from pathlib import Path
import csv, hashlib, json, shutil, sys, zlib
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reserved_unit_ids
import transport_garrison

root = Path('outputs/SWGB-DE-Factions-Draft')
stage = Path('work/faction-package')
root.mkdir(parents=True, exist_ok=True)
# Retire only PNG textures replaced by verified DDS siblings in this build.
for dds in (stage/'widgetui/textures/swgb').glob('*.dds'):
    old=root/'widgetui/textures/swgb'/dds.with_suffix('.png').name
    assert old.resolve().is_relative_to(root.resolve())
    if old.exists():old.unlink()
shutil.copytree(stage, root, dirs_exist_ok=True)
graphics = root/'resources/_common/drs/graphics'
graphics.mkdir(parents=True, exist_ok=True)
validation = json.loads(Path('outputs/faction-art-validation.json').read_text())
verified = {(r['graphic'],r['scale']):r for r in validation['files']}
expected = set()
for r in csv.DictReader(open('work/faction-roster-art.tsv'), delimiter='\t'):
    if int(r['slp']) < 0:
        continue
    gid = int(r['source'])
    for scale, folder in [(1,'faction-roster-converted'),(2,'faction-roster-enhanced')]:
        source = Path('work')/folder/f'swgb_{gid}.smx'
        assert hashlib.sha256(source.read_bytes()).hexdigest() == verified[gid,scale]['sha256']
        name = r['filename'].replace('_x1',f'_x{scale}')+'.smx'
        shutil.copy2(source,graphics/name)
        expected.add(name)
assert {p.name for p in graphics.iterdir()} == expected, 'Unexpected stale graphics in package'
raw = Path('work/factions.raw').read_bytes()
assert raw == Path('work/factions-roundtrip.raw').read_bytes()
# Mandatory: work/factions.raw keeps SWGB unit IDs; DE reads 900-999 as class groups, so the
# packaged DAT uses the committed reserved-unit-id-remap.json (see reserved_unit_ids.py).
raw, remap_stats = reserved_unit_ids.remap_raw_dat(raw)
print('reserved unit IDs:', remap_stats)
# Mandatory: DE matches garrison tasks by class only; the builder's per-unit expansion left every
# transport unboardable (see transport_garrison.py). Idempotent DE-boundary step.
raw, transport_stats = transport_garrison.repair_raw_dat(raw)
print('transport garrison tasks:', transport_stats)
# Same table for the staged JSON/AI/RMS/XS (no-op where the generator already wrote DE IDs).
print(*reserved_unit_ids.remap_mod_pair(root, root, dat=False), sep='\n')
existing = root/'resources/_common/dat/empires2_x2_p1.dat'
compressed = existing.read_bytes() if existing.exists() else b''
if not compressed or zlib.decompress(compressed,-15) != raw:
    c = zlib.compressobj(9,zlib.DEFLATED,-15)
    compressed = c.compress(raw)+c.flush()
assert zlib.decompress(compressed,-15) == raw
(root/'resources/_common/dat/empires2_x2_p1.dat').write_bytes(compressed)
metadata = dict(Author='Local SWGB port project',CacheStatus=0,Title=root.name,
                Version='0.0.2-dev',Description='EXPERIMENTAL, NOT ENGINE VERIFIED. Source Empire/Rebels dataset, artwork, audio and 20 maps. Full gameplay remains incomplete. Separate from stable 0.0.1.')
(root/'info.json').write_text(json.dumps(metadata,indent=2))
(root/'VERSION').write_text('0.0.2-dev\n')
(root/'README.md').write_text('''# Experimental faction draft

This is an experimental development build, not a tested release.
Stable 0.0.1 is unchanged. This dataset exposes Empire and Rebels in its own
three-entry civilization roster (including Gaia); it does not add slots to
the normal DE roster. Use only the matching SWGB Factions maps and SWGB Classic AI.

Includes source unit/technology data, both sprite resolutions, source sounds/music,
icons, English text, technology panels and original map object rules.
Static conversion and reference checks pass. Engine loading, UI, audio playback,
AI and full gameplay have not been verified. Aircraft, shields,
garrisoned power droids and other executable-specific mechanics remain unfinished.
Power uses an experimental native aura with unverified stacking/placement behavior.
Core upgrades retain their aura at every tech level; enable Building and Aura
Range Indicator in DE options to see the configured power radius.
Music includes shared SWGB/EF streams and Empire/Rebel opening themes. Use
Standard soundtrack playlist for faction themes and source stream order.
Nursery food is implemented by an experimental XS script; engine compilation and income are unverified.
Four missing optional fishing overlays are omitted; seven sprite files use fixed
paint for invalid player-color pixels; one flying animation repeats static poses.

Use toolkit/install_factions.py to install separate data and checkbox media mods.
Do not treat this combined assembly folder as the final local-mod layout.
The draft is for local use with the user's installed source games. It has not
been published. See ../FACTION-PORT.md and ../FACTION-STATUS.md for details.
''')
files = []
for p in sorted(root.rglob('*')):
    if p.is_file():
        files.append(dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,
                          sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
report = dict(version='0.0.2-dev',status='uninstalled experimental draft',
              engine_verified=False,files=files,total_bytes=sum(r['bytes'] for r in files))
Path('outputs/faction-package-manifest.json').write_text(json.dumps(report,indent=2))
print(f"Packaged {len(files)} files, {report['total_bytes']:,} bytes; not installed")
