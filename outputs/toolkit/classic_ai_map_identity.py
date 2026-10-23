"""Give the Classic AI its map identity (resource 1997) from XS, by map name.

The port tells the AI which SWGB map it is on through resource 1997: every SWGB Factions
map writes `effect_amount 1 1997 0 N` in <PLAYER_SETUP>, and the source map branches
test `(up-resource-amount 1997 == N)`. DE never applies that effect. A probe on
2026-10-21 (DE build 185872, Savannah, SWBG-Logic 1.7) read the resource from the AI
and from AI XS (`xsPlayerAttribute`): both stayed 0 for over three minutes, while
resource 2018, which the DAT sets, read 10 through both. So every SWGB map ran the
source CUSTOM-MAP branch, which treats an unknown map as WATER: Shipyard, fishing and
transport ships at Tech Level 1 on Savannah, and the Troop Center waiting for the
Shipyard or 10:00. The `(game-time > 3)` guard of classic_ai_opening.py only delays that.

The same probe showed that AI XS can read the map's file name (`xsGetMapName(false)`
returned "SWGB Factions Savannah") and that a value written with
`xsSetPlayerAttribute(player, 1997, ...)` is what the AI's `up-resource-amount 1997`
reads. So the XS observer, which the AI calls at the top of every rule pass (before any
map rule), now sets resource 1997 from a table of the shipped maps while it is still
0. Unknown maps keep 0, so the source CUSTOM-MAP branch still runs there after 3 s.
The RMS markers stay; they are where the table comes from.

Second cause of the water branch, found with the same instrumented replays: the source's
Gaia water detection, `(or (cc-players-unit-type-count 0 7091 > 0) (or
(cc-players-unit-type-count 0 6482 > 0) (cc-players-unit-type-count 0 gaia-fish-line >= 30)))`,
fired at 0:04 on Savannah. 6482 and 7091 are carbon gas vents, which no SWGB Factions map
places, but DE's raw unit-type count returned more than 10 for both (and for 7500, a
Tauntaun, also absent; 4000-6000 read 0, the 7067 palms that Savannah's forest terrain
places read more than 10). Counts of these high type IDs are not reliable in DE, while the
fish line (an exact unitlines.json group) read 20-29 there. The two vent tests are dropped
from that rule (`(cc-players-unit-type-count 0 <X>-gaia-fish-line >= 30)` remains), which
is what the source engine evaluates on the shipped maps.

Run from the repository root to apply the same transformation to an existing script
tree in place (idempotent):
  python outputs/toolkit/classic_ai_map_identity.py --root payload/SWBG-Data
"""
import argparse
import re
from pathlib import Path

RESOURCE = 1997
BEGIN = '// Classic AI map identity (resource 1997) from the map name; see classic_ai_map_identity.py.'
END = '// End of Classic AI map identity.'
CALL = '    classicSetMapIdentity(player);'
PLAYER_CHECK = '    if (player < 1 || player > 8) return;\n'
OBSERVE = 'void swgbClassicObserve() {\n'
MARKER = re.compile(r'^effect_amount 1 1997 0 (\d+)\s*$', re.M)
GAIA_VENTS = re.compile(r'\(or \(cc-players-unit-type-count 0 7091 > 0\) \(or \(cc-players-unit-type-count 0 6482 > 0\) '
                        r'(\(cc-players-unit-type-count 0 c[er]-gaia-fish-line >= 30\))\)\)')
PER = 'resources/_common/ai/SWGB Classic AI.per'
# Every copy of the observer the AI may include (bare-name include, see port_classic_ai.py).
XS_COPIES = ('resources/_common/xs/swgb_classic_ai.xs',
             'resources/_common/ai/swgb_classic_ai.xs',
             'resources/_common/ai/SWGB Classic/swgb_classic_ai.xs')


def table_from_maps(root):
    """{map name (file name without .rms): identity} from the RMS markers."""
    table = {}
    for rms in sorted((Path(root) / 'resources/_common/random-map-scripts').glob('*.rms')):
        found = MARKER.findall(rms.read_text(errors='replace'))
        if found:
            assert len(found) == 1, rms
            table[rms.stem] = int(found[0])
    assert table, 'no map identity markers found'
    assert len(set(table.values())) == len(table), 'map identities must be unique'
    return table


def xs_block(table):
    lines = [BEGIN,
             '// DE does not apply the maps\' `effect_amount 1 1997 0 N`, so the observer sets the',
             '// resource that the source map branches test, before any of them runs.',
             'float classicMapIdentity(string name = "") {']
    for name, identity in sorted(table.items(), key=lambda kv: kv[1]):
        assert '"' not in name and '\\' not in name, name
        lines.append(f'    if (name == "{name}") return({identity}.0);')
    lines += ['    return(0.0);', '}', '',
              'void classicSetMapIdentity(int player = 1) {',
              f'    if (xsPlayerAttribute(player, {RESOURCE}) != 0.0) return;',
              '    float identity = classicMapIdentity(xsGetMapName(false));',
              f'    if (identity > 0.0) xsSetPlayerAttribute(player, {RESOURCE}, identity);',
              '}', END, '']
    return '\n'.join(lines)


def rewrite(text, table):
    """Insert or refresh the identity block and its call; returns (text, changed)."""
    original = text
    block = xs_block(table)
    if BEGIN in text:
        start = text.index(BEGIN)
        end = text.index(END, start) + len(END) + 1
        text = text[:start] + block + text[end:]
    else:
        assert text.count(OBSERVE) == 1, 'observer entry point not found'
        text = text.replace(OBSERVE, block + '\n' + OBSERVE)
    head, body = text.split(OBSERVE)
    if CALL not in body.split('\n}\n')[0]:
        assert body.startswith('    int player = xsGetGoal(104);\n' + PLAYER_CHECK), 'unexpected observer prologue'
        body = body.replace(PLAYER_CHECK, PLAYER_CHECK + CALL + '\n', 1)
    text = head + OBSERVE + body
    return text, text != original


def apply(root, table=None):
    root = Path(root)
    table = table_from_maps(root) if table is None else table
    report = []
    for rel in XS_COPIES:
        path = root / rel
        if not path.is_file():
            continue
        with path.open(encoding='utf-8', newline='') as handle:
            raw = handle.read()
        newline = '\r\n' if '\r\n' in raw else '\n'
        text, changed = rewrite(raw.replace('\r\n', '\n'), table)
        if changed:
            with path.open('w', encoding='utf-8', newline='') as handle:
                handle.write(text.replace('\n', newline))
        report.append(f'{rel} {"changed" if changed else "unchanged"}')
    assert report, 'no swgb_classic_ai.xs found under ' + str(root)
    path = root / PER
    with path.open(encoding='utf-8', newline='') as handle:
        raw = handle.read()
    text, count = rewrite_per(raw)
    if text != raw:
        with path.open('w', encoding='utf-8', newline='') as handle:
            handle.write(text)
    report.append(f'{PER} gaia vent tests dropped: {count}')
    return report


def rewrite_per(text):
    """Drop the unreliable raw vent counts from the Gaia water detection; (text, count)."""
    return GAIA_VENTS.subn(lambda m: m.group(1), text)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--root', type=Path, default=Path('payload/SWBG-Data'))
    args = cli.parse_args()
    table = table_from_maps(args.root)
    for line in apply(args.root, table):
        print(line)
    print(f'{len(table)} maps: ' + ', '.join(f'{k}={v}' for k, v in sorted(table.items(), key=lambda kv: kv[1])))


if __name__ == '__main__':
    main()
