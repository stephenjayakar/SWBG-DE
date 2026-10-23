"""Guard: every SWGB transport can be boarded by its intended units and can unload (offline).

Checks the DE DAT of an assembled SWBG-Logic (payload by default): every DE-garrisonable unit
that a garrison task targets (Assault/Hvy Assault/Transport Mechs, Air Transports, Transport
Ships, campaign carriers) has boarders whose garrison task uses a DE target diplomacy (1 or 4,
never SWGB's 0), keeps trait bit 0 + capacity + an ungarrison-capable interface, and class-20
transports keep DE's Unload task. In each playable civ the core lines must be boardable by
workers and by trained units. See transport_garrison.py for the cause and the repair.

  python outputs/toolkit/check_transports.py [--payload payload] [--logic DIR]

This is a data check; loading and unloading in the running engine still needs a game test.
Needs genieutils-py 0.1.2.
"""
from __future__ import annotations

import argparse
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reserved_unit_ids as R  # noqa: E402
import transport_garrison as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def check(logic: Path) -> tuple[list[str], dict]:
    dat = R.parse_raw(zlib.decompress((logic / R.DAT_REL).read_bytes(), -15))
    return T.scan_dat(dat)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--payload', type=Path, default=ROOT / 'payload')
    ap.add_argument('--logic', type=Path, help='SWBG-Logic (or SWGB-DE-Factions-Draft) folder')
    a = ap.parse_args()
    problems, info = check(a.logic or a.payload / 'SWBG-Logic')
    for p in problems[:60]:
        print('FAIL', p)
    if len(problems) > 60:
        print(f'... {len(problems) - 60} more')
    if problems:
        sys.exit(f'{len(problems)} transport problems; run transport_garrison.py')
    print('transports: OK', info)


if __name__ == '__main__':
    main()
