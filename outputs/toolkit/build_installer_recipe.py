"""Build the installer recipe: how to regenerate every Assets media file from SWGB+EF.

Run from the task root on the development machine, after the verified install
(outputs/faction-install-report.json) is present. Writes
outputs/installer/installer/recipe.tsv. The recipe holds only identifiers,
geometry and SHA-256 digests, never game data. The installer regenerates:

- 2,414 SMX sprites from SWGB/EF SLPs (SwgbDeBuilder.cs, port of PortSprites);
- 1,386 sound WEMs from SWGB/EF WAVs;
- 38 music WEMs from SWGB/EF OGG/MP3 (bundled vgmstream decoder);
- per-icon DDS/PNG textures and the 12 DE UI atlases (DE's own texconv).

Everything else in the two mods is project-authored and shipped as payload
(payload/SWBG-Logic, payload/SWBG-Data; refresh it with
package_installer.py --update-payload). The development install keeps its
older folder names (SWGB-DE-Factions-Draft / -Assets); the recipe uses the
release names SWBG-Logic / SWBG-Data.
"""
from pathlib import Path
import csv, hashlib, json, struct, sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
GAME = Path(r'E:\GOG Games\Star Wars - Galactic Battlegrounds\Game')
DE = Path(r'E:\SteamLibrary\steamapps\common\AoE2DE')
OUT = ROOT / 'outputs/installer/installer/recipe.tsv'
# Development folder name -> release mod name used in the recipe and payload.
RELEASE_NAME = {'SWGB-DE-Factions-Draft': 'SWBG-Logic', 'SWGB-DE-Factions-Assets': 'SWBG-Data'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def drs_index(path):
    out = {}
    with open(path, 'rb') as f:
        head = f.read(84)
        count = struct.unpack_from('<I', head, 76)[0]
        tables = [struct.unpack('<4sII', f.read(12)) for _ in range(count)]
        for ext, off, n in tables:
            f.seek(off)
            t = ext[::-1].decode().strip('\0 ')
            for _ in range(n):
                i, o, s = struct.unpack('<III', f.read(12))
                out[(t, i)] = (o, s)
    return out


_idx = {}


def entry(archive, kind, rid):
    path = GAME / 'Data' / archive
    if archive not in _idx:
        _idx[archive] = drs_index(path)
    o, s = _idx[archive][(kind, rid)]
    with open(path, 'rb') as f:
        f.seek(o)
        return f.read(s)


def main():
    report = json.loads((ROOT / 'outputs/faction-install-report.json').read_text())
    local = Path(report['data_mod']).parent
    files = report['installed_files']
    for r in files:
        assert sha((local / r['mod'] / r['path']).read_bytes()) == r['sha256'], r['path']
    # Never pin a build that still uses DE's reserved group IDs 900-999 as unit IDs (crash at
    # AoE2DE_s.exe+0x1356be0). Fix the install with remap_reserved_unit_ids.py --logic/--data.
    from check_reserved_unit_ids import check
    problems, _ = check(local / 'SWGB-DE-Factions-Draft', local / 'SWGB-DE-Factions-Assets')
    assert not problems, ('reserved unit IDs in the development install', problems[:10])
    lines =['#swgb-de-recipe\t1']
    handled = set()
    assets = {r['path']: r for r in files if r['mod'] == 'SWGB-DE-Factions-Assets'}
    manifest = json.loads((ROOT / 'outputs/archive-manifest.json').read_text())

    pal = entry('interfac_x2.drs', 'bina', 50500)
    lines.append('\t'.join(['palette', 'interfac_x2.drs', 'bina', '50500', sha(pal)]))

    # Sprites -------------------------------------------------------------
    art = {r['id']: r for r in json.loads((ROOT / 'outputs/faction-art-stage-report.json').read_text())['extracted']}
    meta = {int(r['id']): r for r in csv.DictReader(open(ROOT / 'outputs/ef-graphics.tsv'), delimiter='\t')}
    for path, r in sorted(assets.items()):
        if not path.startswith('resources/_common/drs/graphics/'):
            continue
        name = Path(path).stem  # swgb_<gid>_x<scale>
        _, gid, scale = name.split('_')
        gid = int(gid); scale = int(scale[1:])
        a = art[gid]
        data = entry(a['archive'], 'slp', a['slp'])
        assert sha(data) == a['sha256']
        m = meta[gid]
        lines.append('\t'.join(map(str, ['smx', path, r['sha256'], a['archive'], a['slp'], a['sha256'], gid,
                                         m['frames'], m['angles'], m['mirror'], scale])))
        handled.add(path)

    # Sounds --------------------------------------------------------------
    audio = {f['file']: f for f in json.loads((ROOT / 'outputs/faction-audio-report.json').read_text())['files']}
    for path, r in sorted(assets.items()):
        if not path.startswith('resources/_common/drs/sounds/'):
            continue
        wid = Path(path).stem[len('swgb_'):]
        f = audio[wid + '.wav']
        data = entry(f['origin'], 'wav', int(wid))
        assert sha(data) == f['sha256']
        lines.append('\t'.join(['wem', path, r['sha256'], f['origin'], wid, f['sha256']]))
        handled.add(path)

    # Music ---------------------------------------------------------------
    music = json.loads((ROOT / 'outputs/faction-music-report.json').read_text())
    for i, s in enumerate(music['shared_sources']):
        assert sha((GAME / s['file']).read_bytes()) == s['sha256']
        lines.append('\t'.join(['musicsrc', str(i), s['file'], s['sha256']]))
    rows = {f['file']: f for f in music['files']}
    for path, r in sorted(assets.items()):
        if not path.startswith('resources/_common/sound/music/'):
            continue
        name = Path(path).name
        f = rows[name]
        assert f['sha256'] == r['sha256']
        if name == 'lobby01.wem':
            lines.append('\t'.join(['copy', path, r['sha256'], 'resources/_common/sound/music/frontend01.wem']))
        elif name.startswith('ingame'):
            lines.append('\t'.join(['musicslice', path, r['sha256'], str(int(name[6:8])), '30']))
        else:
            assert sha((GAME / f['source']).read_bytes()) == f['source_sha256']
            lines.append('\t'.join(['musiccue', path, r['sha256'], f['source'], f['source_sha256']]))
        handled.add(path)

    # Icons ---------------------------------------------------------------
    icon_rows = json.loads((ROOT / 'outputs/faction-icon-report.json').read_text())
    sheets = icon_rows['sheets']
    binding = {f"{b['civ']}_{b['kind']}_{b['id']}.png": b for b in icon_rows['bindings']}
    candidates = sorted(ROOT.glob('work/faction-icon-png/*.png'), key=lambda p: (p.name.split('_')[0] not in ('1', '3'), p.name))
    ui = Path(report['asset_mod']) / 'widgetui'
    targets = {}
    headers = {}
    for path, r in assets.items():
        if path.startswith('widgetui/textures/ingame/') and path.endswith('.dds') and '/icons/' not in path:
            b = (local / r['mod'] / path).read_bytes()
            h, w = struct.unpack_from('<II', b, 12)
            assert len(b) == 128 + w * h * 4
            targets.setdefault((w, h), {})[sha(b[128:])] = path
            headers.setdefault(b[:128].hex(), []).append(path)
    keys = {}
    for i, hx in enumerate(sorted(headers)):
        keys[hx] = f'h{i}'
        lines.append('\t'.join(['ddshdr', f'h{i}', hx]))
    source_for = {}
    for png in candidates:
        if png.name not in binding:
            continue
        im = Image.open(png).convert('RGBA')
        for (w, h), d in targets.items():
            k = sha(im.resize((w, h), Image.Resampling.NEAREST).tobytes())
            if k in d and d[k] not in source_for:
                source_for[d[k]] = binding[png.name]
    assert len(source_for) == sum(len(d) for d in targets.values()), 'unmatched icon textures'
    for path in sorted(source_for):
        b = (local / 'SWGB-DE-Factions-Assets' / path).read_bytes()
        h, w = struct.unpack_from('<II', b, 12)
        src = source_for[path]
        sheet = sheets[src['slp']]
        data = entry(sheet['archive'], 'slp', int(src['slp']))
        assert sha(data) == sheet['sha256']
        lines.append('\t'.join(map(str, ['icondds', path, assets[path]['sha256'], keys[b[:128].hex()], w, h,
                                         sheet['archive'], src['slp'], src['frame'], sheet['sha256']])))
        handled.add(path)

    # Resource icons (PNG files; pixel-verified, PNG bytes are encoder-specific).
    order = {'interfac.drs': 0, 'interfac_x1.drs': 1, 'interfac_x2.drs': 2}
    res = max((r for r in manifest if r['id'] == 50731 and r['ext'] == 'slp' and r['archive'].lower() in order),
              key=lambda r: order[r['archive'].lower()])
    res_data = entry(res['archive'], 'slp', 50731)
    frames = {'wood': 0, 'stone': 1, 'food': 2, 'gold': 3}
    for path, r in sorted(assets.items()):
        if path.startswith('widgetui/textures/ingame/icons/'):
            im = Image.open(local / r['mod'] / path).convert('RGBA')
            kind = Path(path).stem.split('_')[1]
            lines.append('\t'.join(map(str, ['iconpng', path, sha(im.tobytes()), im.size[0], im.size[1],
                                             res['archive'], 50731, frames[kind], sha(res_data)])))
            handled.add(path)

    # Atlases: geometry from the shipped Draft materials.json (frozen layout).
    draft_materials = json.loads((local / 'SWGB-DE-Factions-Draft/widgetui/materials.json').read_text())
    generated_icons = {p[len('widgetui/'):] for p in handled if p.startswith('widgetui/textures/ingame/')}
    for path, r in sorted(assets.items()):
        if not path.startswith('widgetui/textures/atlas/'):
            continue
        b = (local / r['mod'] / path).read_bytes()
        h, w = struct.unpack_from('<II', b, 12)
        fmt = 'BC3_UNORM' if b[84:88] == b'DXT5' else 'BC7_UNORM'
        if b[84:88] == b'DX10':
            assert struct.unpack_from('<I', b, 128)[0] == 98
        rel = path[len('widgetui/'):]
        atlas = next(a['AtlasDef'] for a in draft_materials['AtlasTextures']
                     if rel in {a['AtlasDef'].get(k) for k in ('SDSource', 'HDSource', 'UHDSource', 'DefaultSource')})
        lines.append('\t'.join(map(str, ['atlas', path, r['sha256'], fmt, w, h, atlas['Name']])))
        for t in atlas['Textures']:
            if t['FileName'] not in generated_icons:
                continue
            box = tuple(round(float(t[k]) * dim + adj) for k, dim, adj in (
                ('imageTLX', w, -.5), ('imageTLY', h, -.5), ('imageBRX', w, .5), ('imageBRY', h, .5)))
            lines.append('\t'.join(map(str, ['atlasbox', path, *box, 'widgetui/' + t['FileName'], t['RefName']])))
        handled.add(path)

    # Payload (project-authored files) ---------------------------------------
    for r in files:
        if r['mod'] == 'SWGB-DE-Factions-Assets' and r['path'] in handled:
            continue
        if r['mod'] == 'SWGB-DE-Factions-Assets' and r['path'].startswith('widgetui/textures/swgb/'):
            # Obsolete per-icon textures from an earlier custom-material design;
            # no materials file references them. Not regenerated or shipped.
            lines.append('\t'.join(['obsolete', RELEASE_NAME[r['mod']], r['path'], r['sha256']]))
            continue
        lines.append('\t'.join(['ship', RELEASE_NAME[r['mod']], r['path'], r['sha256']]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(lines) + '\n', newline='\n')
    kinds = {}
    for l in lines[1:]:
        kinds[l.split('\t')[0]] = kinds.get(l.split('\t')[0], 0) + 1
    print(OUT, kinds)


if __name__ == '__main__':
    main()
