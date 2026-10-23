"""Compress a patched raw DAT (faction_parity_patch output) into the installed and staged Draft mods.

Usage (repo root): python outputs/toolkit/install_parity_dat.py <patched.raw>
Backs up the previous installed DAT under work/parity-backups/. Same deflate settings as package_factions.py.
The patched raw keeps SWGB unit IDs; the committed reserved-unit-id-remap.json is applied before
compressing (DE reads 900-999 as class groups, see reserved_unit_ids.py), then the transport
garrison-task repair (transport_garrison.py) so troops can board transports.
"""
import hashlib, shutil, sys, time, zlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reserved_unit_ids
import transport_garrison

REL = Path('resources/_common/dat/empires2_x2_p1.dat')
TARGETS = [Path(r'C:\Users\aj12a\Games\Age of Empires 2 DE\76561198022514833\mods\local\SWGB-DE-Factions-Draft'),
           Path('outputs/SWGB-DE-Factions-Draft')]


def main(raw_path):
    raw, stats = reserved_unit_ids.remap_raw_dat(Path(raw_path).read_bytes())
    print('reserved unit IDs:', stats)
    raw, stats = transport_garrison.repair_raw_dat(raw)
    print('transport garrison tasks:', stats)
    c = zlib.compressobj(9, zlib.DEFLATED, -15)
    compressed = c.compress(raw) + c.flush()
    assert zlib.decompress(compressed, -15) == raw
    backup = Path('work/parity-backups') / time.strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True, exist_ok=True)
    for root in TARGETS:
        dst = root / REL
        if dst.exists():
            shutil.copy2(dst, backup / (root.name + '-' + dst.name))
        dst.write_bytes(compressed)
        assert zlib.decompress(dst.read_bytes(), -15) == raw
        print('installed', dst, hashlib.sha256(compressed).hexdigest()[:16])
    print('raw sha256', hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    main(sys.argv[1])
