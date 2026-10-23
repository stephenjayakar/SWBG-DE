"""Civilization metadata for the two-faction DE dataset (civilizations.json, picker strings and images).

DE build 185872 (2026-09-25) changed two things that broke the previous minimal entries:
  * The lobby gates civs by ``data_name`` against a hard-coded native list. Unknown names are treated
    as Lords of the West civs ("A selected civilization is available in the Lords of the West DLC")
    and the game refuses to start. Each faction therefore reuses the native data_name of the slot it
    occupies (1=Britons, 2=Franks). Display name, strings and images stay SWGB.
  * Entries carry the full native field set (unique unit/tech ids, image paths, string ids).

DE 101.103.54800 (build 185872) also resolves ``tech_tree_name`` only against its native civs: a custom
name such as SWGB_EMPIRE leaves the lobby and in-game technology trees empty even when
``CivTechTrees/SWGB_EMPIRE.json`` is present and valid, while a native name loads the data mod's
``CivTechTrees/<name>.json`` (verified in game 2026-10-21). Each faction therefore also reuses the
native tech tree name of its slot (BRITONS, FRANKS); the panel content is still the SWGB tree written
by faction_tree_ui.py. check_civ_tech_trees.py guards this.
"""
from pathlib import Path

from reserved_unit_ids import de_unit_id

GAIA = {'internal_name': 'Gaia', 'tech_tree_name': 'GAIA', 'data_name': 'GAIA', 'hud_style': 'CivWest',
        'name_string_id': 10102, 'era': 'base'}

# slot, internal, native tech tree name (legacy custom name), native data_name, name sid, description sid, source description sid,
# unique unit, elite unique unit, elite upgrade tech, unit line, unit name sid, unit help sid, icon index.
# Unit IDs are SWGB IDs (993/971/979 sit in DE's reserved group range 900-999); civ_entry() writes the
# moved DE IDs via reserved_unit_ids.de_unit_id. The string IDs stay derived from the SWGB IDs.
FACTIONS = (
    dict(slot=1, internal='GalacticEmpire', tech_tree='BRITONS', legacy_tech_tree='SWGB_EMPIRE', data_name='BRITON-CIV', name_sid=890001,
         desc_sid=890011, source_desc_sid=20150, unit=993, elite=971, upgrade=472, line=-341,
         unit_name_sid=2000993, unit_help_sid=2100993, icon=48, image='galacticempire'),
    dict(slot=2, internal='RebelAlliance', tech_tree='FRANKS', legacy_tech_tree='SWGB_REBELS', data_name='FRANKISH-CIV', name_sid=890002,
         desc_sid=890012, source_desc_sid=20152, unit=6, elite=979, upgrade=476, line=-349,
         unit_name_sid=3000006, unit_help_sid=3100006, icon=68, image='rebelalliance'),
)


def civ_entry(f):
    return {
        'internal_name': f['internal'], 'tech_tree_name': f['tech_tree'], 'data_name': f['data_name'],
        'hud_style': 'CivWest',
        'tech_tree_image_path': f"/resources/civ_techtree/menu_techtree_{f['image']}.png",
        'emblem_image_path': f"/resources/civ_emblems/{f['image']}.png",
        'unique_unit_image_paths': [f"/resources/uniticons/swgb_{f['image']}_unique.png"],
        'name_string_id': f['name_sid'], 'tech_tree_description_string_id': f['desc_sid'],
        'computer_name_string_table_offset': 4400 if f['slot'] == 1 else 4500,
        # SWGB/EF unique technologies are ordinary tech-tree techs, not DE castle/imperial unique techs.
        'unique_tech_id_1': -1, 'unique_tech_id_2': -1,
        'unique_unit_line': f['line'], 'unique_unit_upgrade_id': f['upgrade'],
        'unique_unit_id': de_unit_id(f['unit']), 'elite_unique_unit_id': de_unit_id(f['elite']),
        'unique_unit_string_ids': [{'name': f['unit_name_sid'], 'description': f['unit_help_sid']}],
        'era': 'base',
    }


def civilizations():
    return {'civilization_list': [dict(GAIA)] + [civ_entry(f) for f in FACTIONS]}


def _split_items(text):
    """Split 'A (X); B, C (Y).' into ['A (X)', 'B (Y)', 'C (Y)'] keeping the shared location."""
    items = []
    for part in [p.strip().rstrip('.') for p in text.split(';') if p.strip()]:
        loc = ''
        if part.endswith(')') and '(' in part:
            loc = part[part.rindex('('):]
            part = part[:part.rindex('(')].strip()
        names = [n.strip() for n in part.split(',') if n.strip()]
        items += [f'{n} {loc}'.strip() for n in names]
    return items


def picker_description(source_text):
    """Convert an SWGB/EF civ help string to DE's civ-picker layout.

    DE parses: '<type> civilization', blank line, '\u2022 feature' lines, then '<b>Unique Unit:<b>',
    '<b>Unique Techs:<b>' and '<b>Team Bonus:<b>' sections (see native string 120150).
    """
    fields = {}
    for line in source_text.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        line = line.strip().lstrip('\u2022\x95\u00b7* ').strip()
        head, sep, rest = line.partition(':')
        if sep:
            fields[head.strip().lower()] = rest.strip()
    strong = fields.get('strong units', '')
    features = [f.strip().rstrip('.') for f in fields.get('civilization bonus', '').split(';') if f.strip()]
    if fields.get('weaknesses'):
        features += [f.strip().rstrip('.') for f in fields['weaknesses'].split(';') if f.strip()]
    if fields.get('fortress bonus'):
        features.append(fields['fortress bonus'].rstrip('.'))
    unique_units = fields.get('unique units') or fields.get('unique unit', '')
    techs = _split_items(fields.get('unique technologies', ''))
    out = [f'{strong} civilization' if strong else 'Civilization', '']
    out += [f'\u2022 {f}' for f in features]
    out += ['', '<b>Unique Unit:<b> ', unique_units.rstrip('.'), '', '<b>Unique Techs:<b> ']
    out += [f'\u2022 {t}' for t in techs]
    out += ['', '<b>Team Bonus:<b> ', fields.get('team bonus', '').rstrip('.')]
    return '\n'.join(out)


def description_strings(source_strings):
    return {f['desc_sid']: picker_description(source_strings[f['source_desc_sid']]) for f in FACTIONS}


def write_images(icon_dir, wpfg_root):
    """Write picker PNGs (unique unit, emblem, tech-tree button) from the converted unit icons."""
    from PIL import Image
    icon_dir, wpfg_root = Path(icon_dir), Path(wpfg_root)
    written = []
    for f in FACTIONS:
        icon = Image.open(icon_dir / f"{f['icon']:03d}_50730.dds").convert('RGBA')
        targets = {
            wpfg_root / 'resources/uniticons' / f"swgb_{f['image']}_unique.png": icon.resize((256, 256), Image.LANCZOS),
            wpfg_root / 'resources/civ_techtree' / f"menu_techtree_{f['image']}.png": icon.resize((104, 104), Image.LANCZOS),
        }
        emblem = Image.new('RGBA', (450, 280), (0, 0, 0, 0))
        emblem.paste(icon.resize((280, 280), Image.LANCZOS), (85, 0))
        targets[wpfg_root / 'resources/civ_emblems' / f"{f['image']}.png"] = emblem
        for path, image in targets.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            image.save(path)
            written.append(path)
    return written
