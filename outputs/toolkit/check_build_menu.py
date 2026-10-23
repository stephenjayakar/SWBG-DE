"""Guard: every building an Empire or Rebel player can build has its own build-menu position.

Offline check of SWBG-Logic's DAT and hotkeys.json against DE's page model (see build_menu.py).
For the default state and for each construction-layout research it fails on:
  * two building families that the civ can ever get sharing one builder/page/position (DE shows
    only one of them; the check is stricter than DE and also rejects families available at
    different times);
  * a native Dock ID (45/133/47/51) on a build page: DE never shows those;
  * a technology without prerequisites and with research time 0 at a building: DE researches it
    at game start instead of offering it;
  * a building on a position DE does not offer (14 = next page, 15 = cancel) or with an interface
    kind other than 2 (economic) and 10 (military);
  * a building a human can reach (enabled, or enabled by research with a visible button, an
    automatic availability tech or a completed building) that no layout shows, directly, through
    an upgrade of its line or through a foundation that turns into it;
  * a shown building whose hotkey ID is missing from hotkeys.json or whose default key does not
    match its grid position (QWERT/ASDFG/ZXC);
  * a Military construction layout that does not restore the default state.

  python outputs/toolkit/check_build_menu.py [--logic payload/SWBG-Logic] [--report menu.json]

Needs genieutils-py 0.1.2.
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

ROOT = Path(__file__).resolve().parents[2]
HOTKEYS_REL = 'resources/_common/dat/hotkeys.json'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--logic', type=Path, default=ROOT / 'payload/SWBG-Logic')
    ap.add_argument('--report', type=Path, help='write the per-layout menus as JSON')
    a = ap.parse_args()
    dat = R.parse_raw(zlib.decompress((a.logic / R.DAT_REL).read_bytes(), -15))
    hotkeys = json.loads((a.logic / HOTKEYS_REL).read_text(encoding='utf-8'))
    problems, report = B.analyse(dat, hotkeys)
    if a.report:
        a.report.write_text(json.dumps(report, indent=2) + '\n')
    for p in problems[:80]:
        print('FAIL', p)
    if len(problems) > 80:
        print(f'... {len(problems) - 80} more')
    if problems:
        sys.exit(f'{len(problems)} build-menu problems; see build_menu.py and fix_build_menu.py')
    shown = {civ: sorted({u for menu in states.values() for us in menu.values() for u in us})
             for civ, states in report.items()}
    print('build menu: OK', {civ: f'{len(v)} buildings, layouts: {", ".join(report[civ])}' for civ, v in shown.items()})


if __name__ == '__main__':
    main()
