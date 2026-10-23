"""Apply the worker build-menu layout (build_menu.py) to an assembled SWBG-Logic/SWBG-Data pair.

Bug: a human player's worker never offered Troop Center, Shipyard, Mech Factory or Temple; the AI
(which builds by unit ID) was unaffected. Three causes, all verified in DE:
  * Sentry Post, Shield Generator and Trip Mine sat on military positions 1/5/6 with SWGB interface
    kind 11, which the layout switch was meant to hide. DE shows kind 11 on the military page, so
    they covered Troop Center, Mech Factory and Temple.
  * Both layout researches had no prerequisite and research time 0, so DE researched them at game
    start: every game began in the defense layout and the Command Center offered no switch.
  * DE never shows the native Dock IDs 45/133/47/51 (SWGB's Shipyard) in a build menu.

This deterministic, idempotent step:
  * DAT (genieutils-py 0.1.2, byte-exact round trip checked first): adds Shipyard foundation unit
    1696 (copy of each civ's Shipyard that turns into unit 45 when finished, enabled with it) and
    hides the Shipyard IDs; Sentry Post -> military 7 (always shown); Advanced Infantry Center ->
    button 0 (cheat/AI only); Anti-Air Battery/Shield Generator/Trip Mine -> kind 10, button 0 by
    default; both layout researches move ButtonIDs (attribute 43) instead of the interface kind
    (attribute 141) and take 1 second;
  * hotkeys.json: every building the layouts move gets the default key of its position
    (Sentry Post Q -> S); nothing else changes;
  * SWBG-Data strings: the two layout research help texts (faction_defense_ui.defense_strings).

  python outputs/toolkit/fix_build_menu.py                       # payload/ + recipe.tsv hashes
  python outputs/toolkit/fix_build_menu.py --logic <SWBG-Logic dir> --data <SWBG-Data dir>

The C++ builder produces the same DAT (faction_build_menu.h; on the previous payload the two give
identical bytes); run check_build_menu.py afterwards. The unit IDs here are outside 900-999, so the
step commutes with remap_reserved_unit_ids.py.
"""
from __future__ import annotations

import argparse
import json
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_menu as B  # noqa: E402
import reserved_unit_ids as R  # noqa: E402
from faction_defense_ui import defense_strings  # noqa: E402
from remap_reserved_unit_ids import refresh_recipe  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HOTKEYS_REL = 'resources/_common/dat/hotkeys.json'
STRINGS_REL = 'resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
LAYOUT_STRINGS = (919010, 919011)


def fix_raw_dat(raw: bytes):
    dat = R.parse_raw(raw)
    if dat.to_bytes() != raw:
        raise SystemExit('genieutils-py does not round-trip this DAT byte-exactly; refusing to rewrite it')
    stats = B.fix_build_menu(dat)
    return dat.to_bytes(), stats, dat


def hotkey_positions(dat) -> dict[int, str]:
    """{hotkey string ID: grid key} for every building whose position the layouts set."""
    displaced = B.displaced_units(dat)
    slots = dict(displaced)
    slots.update(B.DEFENSE_EXTRAS)
    slots.update({uid: B.SENTRY_SLOT for uid in B.SENTRY})
    out = {}
    for c in B.FACTIONS:
        potential = B.availability(dat, c)[0]
        for uid, slot in slots.items():
            if uid not in potential:
                continue  # not in this faction's roster; it has no hotkeys.json entry
            for t in dat.civs[c].units[uid].creatable.train_locations:
                if t.unit_id == B.WORKER and t.hot_key_id >= 0:
                    out[t.hot_key_id] = B.GRID[slot - 1]
    return out


def fix_hotkeys(text: str, keys: dict[int, str]) -> tuple[str, int]:
    doc = json.loads(text)
    changed, seen = 0, set()
    for group in doc['hotkey_group_list']:
        for entry in group['hotkey_list']:
            for sid in entry.get('string_index_list', []):
                if sid in keys:
                    seen.add(sid)
                    for default in entry['defaults_list']:
                        if default['key'] != keys[sid]:
                            default['key'] = keys[sid]
                            changed += 1
    missing = set(keys) - seen
    if missing:
        raise SystemExit(f'hotkeys.json lacks hotkey IDs {sorted(missing)}')
    return json.dumps(doc, indent=2) + '\n', changed


def fix_strings(body: bytes) -> tuple[bytes, int]:
    text = defense_strings()
    nl = b'\r\n' if b'\r\n' in body else b'\n'
    lines = body.split(nl)
    changed, seen = 0, set()
    for i, line in enumerate(lines):
        sid = line.split(b' ', 1)[0]
        if sid.isdigit() and int(sid) in LAYOUT_STRINGS:
            new = f'{int(sid)} {json.dumps(text[int(sid)], ensure_ascii=False)}'.encode('utf-8')
            seen.add(int(sid))
            if new != line:
                lines[i] = new
                changed += 1
    if seen != set(LAYOUT_STRINGS):
        raise SystemExit(f'strings file lacks {sorted(set(LAYOUT_STRINGS) - seen)}')
    return nl.join(lines), changed


def apply(logic: Path, data: Path, dry_run: bool) -> list[str]:
    log = []
    dat_path = logic / R.DAT_REL
    raw = zlib.decompress(dat_path.read_bytes(), -15)
    out, stats, dat = fix_raw_dat(raw)
    if out != raw:
        if not dry_run:
            dat_path.write_bytes(R.compress_dat(out))
        log.append(f'DAT: {stats}')
    else:
        log.append('DAT: already fixed')
    hk_path = logic / HOTKEYS_REL
    text, n = fix_hotkeys(hk_path.read_text(encoding='utf-8'), hotkey_positions(dat))
    if n and not dry_run:
        hk_path.write_bytes(text.encode('utf-8'))
    log.append(f'hotkeys.json: {n} default keys changed')
    st_path = data / STRINGS_REL
    body, n = fix_strings(st_path.read_bytes())
    if n and not dry_run:
        st_path.write_bytes(body)
    log.append(f'strings: {n} layout help texts changed')
    return log


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--payload', type=Path, default=ROOT / 'payload')
    ap.add_argument('--logic', type=Path, help='SWBG-Logic (or SWGB-DE-Factions-Draft) folder')
    ap.add_argument('--data', type=Path, help='SWBG-Data (or SWGB-DE-Factions-Assets) folder')
    ap.add_argument('--recipe', type=Path, default=ROOT / 'outputs/installer/installer/recipe.tsv')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if bool(a.logic) != bool(a.data):
        ap.error('--logic and --data go together')
    logic = a.logic or a.payload / 'SWBG-Logic'
    data = a.data or a.payload / 'SWBG-Data'
    log = apply(logic, data, a.dry_run)
    if not a.logic:
        log.append(refresh_recipe(a.payload, a.recipe, a.dry_run))
    print('\n'.join(log) + (' [dry run]' if a.dry_run else ''))


if __name__ == '__main__':
    main()
