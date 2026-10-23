r"""SWBG ships one AI: SWGB Classic AI. This module writes the SWBG-Data files that route DE's
built-in lobby AI entries to it.

How DE fills the Skirmish lobby's player dropdown (AoE2DE_s.exe build 185872, its string table,
and the lobby itself on 2026-10-22):
- "AI" (string NEW_AI_TAG): built in, always listed; runs PromiDE (drs/gamedata_x2/PromiDE.per2).
- "AI (CD version)" (ORIG_AI_TAG): built in, always listed; runs RandomGame
  (drs/gamedata_x2/randomgame.per2).
- one entry per <name>.ai file in resources/_common/ai of the game and of every enabled mod,
  labelled <name>. DE skips its scenario script E3-p2.ai and labels its own
  "AI (HD version).ai" with HD_AI_TAG.
A mod can add or override files but cannot hide a base-game file, so the three DE entries stay.
SWBG-Data ships no .ai file (no further entry) and makes all three run SWGB Classic AI:
- "AI (HD version)": its script resources/_common/ai/AI (HD version).per is overridden with
  (load "SWGB Classic AI"); DE uses the mod's copy.
- "AI": the mod's PromiDE.per2 (load "SWGB Classic AI") replaces DE's. It must stay the only file
  in SWBG-Data's drs/gamedata_x2: with more files there (stubs, a RandomGame.per2), DE ignored the
  mod's PromiDE.per2 in some sessions and ran its own (shown with a marker in a Promisory file), and
  also took some stubs there from the game instead of the mod.
- "AI (CD version)": DE never used a mod's randomgame.per2 (lower- or upper-case name); it runs its
  own. DE resolves the files it loads in resources/_common/ai (game and mods) before
  drs/gamedata_x2, though. Its first load, Promisory\defaultConstants, becomes
  (load "SWGB Classic AI"), and every other file it loads directly becomes a comment-only stub
  (STUBS) in the ai folder: Promisory\<name>.per replaces DE's file, "elite ... .per" shadows
  DE's drs/gamedata_x2 "elite ... .per2". DE's randomgame.per2 then runs SWGB Classic AI and nothing
  else. DE's own PromiDE.per2 loads Promisory\defaultConstants first as well, and the other
  Promisory files it loads are stubbed too, so even if DE ran its own PromiDE.per2, "AI" would get
  SWGB Classic AI (plus DE's two ailib XS includes).
Before this, "AI (CD version)" ran DE's own AI on the SWGB data: an AI Script Error
(Promisory\finalingConstants line 105, invalid identifier) on load, after which no AI
of a later player number ran in that match.

    python outputs/toolkit/ai_entries.py --root <SWBG-Data or SWGB-DE-Factions-Assets>

writes the files and deletes the retired ones (RETIRED). check_single_ai.py checks the result.
"""
from pathlib import Path
import argparse

CLASSIC = 'SWGB Classic AI'
# Files that must exist for (load "SWGB Classic AI"): the script and its XS include, which DE
# resolves in resources/_common/xs (the ai/ copies are kept for the parser and old installs).
CLASSIC_FILES = ('resources/_common/ai/SWGB Classic AI.per',
                 'resources/_common/xs/swgb_classic_ai.xs')
AI_DIR = 'resources/_common/ai'
GAMEDATA = 'resources/_common/drs/gamedata_x2'
# DE's built-in lobby entries: label -> DE's own script (DE install relative) and the name DE's exe uses.
DE_ENTRIES = {
    'AI': (f'{GAMEDATA}/PromiDE.per2', 'PromiDE'),
    'AI (CD version)': (f'{GAMEDATA}/randomgame.per2', 'RandomGame'),
    'AI (HD version)': (f'{AI_DIR}/AI (HD version).per', 'AI (HD version)'),
}
# SWBG-Data files that contain only (load "SWGB Classic AI").
ENTRIES = {
    # The only file in SWBG-Data's drs/gamedata_x2 (see above), named exactly like DE's.
    f'{GAMEDATA}/PromiDE.per2': 'DE lobby entry "AI" (PromiDE)',
    f'{AI_DIR}/AI (HD version).per': 'DE lobby entry "AI (HD version)"',
    f'{AI_DIR}/Promisory/defaultConstants.per':
        'first file DE\'s PromiDE.per2 ("AI") and randomgame.per2 ("AI (CD version)") load',
}
# Every other file DE's PromiDE.per2 and randomgame.per2 load directly (DE build 185872), as a
# stub in the ai folder, which DE searches first; check_single_ai.py --de compares this list with
# DE's scripts.
PROMISORY_LOADS = ('boarhunting', 'buildings', 'customConstants', 'dawn', 'escrow', 'event', 'finaling',
                   'finalingConstants', 'gatherers', 'general', 'init', 'interaction', 'orb', 'researches',
                   'resign', 'scoutcontrol', 'threats', 'trade', 'tsa', 'units', 'watercontrol')
GAMEDATA_LOADS = ('elite AI petersen rules', 'elite petersen constants', 'elite petersen deathmatch',
                  'elite petersen diplomacy', 'elite petersen groups', 'elite petersen map loads',
                  'elite petersen resign', 'elite petersen supplement', 'elite wonder kill', 'elite wonder rush')
STUBS = tuple([f'{AI_DIR}/Promisory/{n}.per' for n in PROMISORY_LOADS]
              + [f'{AI_DIR}/{n}.per' for n in GAMEDATA_LOADS])
# Shipped by earlier releases; the installer deletes them from existing SWBG-Data installs.
# SWGB Land AI was a partial land adapter; "SWGB Classic AI.ai" listed Classic a second time.
RETIRED = ('resources/_common/ai/SWGB Land AI.ai',
           'resources/_common/ai/SWGB Land AI.per',
           'resources/_common/ai/SWGB Classic AI.ai')


# Plain, short comment lines only (the stubs must parse as empty AI files).
def entry_text(rel: str) -> bytes:
    assert rel in ENTRIES, rel
    return (b'; SWBG-Data: runs SWGB Classic AI, the only SWBG AI.\n'
            b'; Written by ai_entries.py, see ORIGINAL-AI.md.\n'
            + f'(load "{CLASSIC}")\n'.encode('ascii'))


def stub_text(rel: str) -> bytes:
    assert rel in STUBS, rel
    return (b'; SWBG-Data stub: SWBG ships one AI, SWGB Classic AI.\n'
            b'; Written by ai_entries.py.\n')


def expected_files() -> dict[str, bytes]:
    out = {rel: entry_text(rel) for rel in ENTRIES}
    out.update({rel: stub_text(rel) for rel in STUBS})
    return out


def de_direct_loads(de: Path) -> set[str]:
    """Stub paths (ai folder) for the files DE's PromiDE.per2 and randomgame.per2 load directly."""
    import re
    out = set()
    for script in (DE_ENTRIES['AI'][0], DE_ENTRIES['AI (CD version)'][0]):
        for name in re.findall(r'\(load\s+"([^"]+)"', (de/script).read_text(errors='replace')):
            name = name.replace(chr(92), '/')
            exists = (de/f'{AI_DIR}/{name}.per').is_file() or (de/f'{GAMEDATA}/{name}.per2').is_file()
            out.add(f'{AI_DIR}/{name}.per' if exists else f'<unresolved {name}>')
    return out


def apply(root: Path) -> list[str]:
    """Write the entries and stubs into a SWBG-Data folder, delete retired files; return what changed."""
    changed = []
    for rel, data in expected_files().items():
        path = root/rel
        if path.is_file() and path.name not in {f.name for f in path.parent.iterdir()}:
            path.unlink()  # same name in another case (e.g. PromiDE.per2): the case matters to DE
        if not path.is_file() or path.read_bytes() != data:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            changed.append('wrote ' + rel)
    for rel in RETIRED:
        if (root/rel).is_file():
            (root/rel).unlink()
            changed.append('deleted ' + rel)
    return changed


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument('--root', type=Path, required=True, help='SWBG-Data folder (payload/SWBG-Data or a dev install)')
    root = cli.parse_args().root
    assert all((root/f).is_file() for f in CLASSIC_FILES), f'{root} has no SWGB Classic AI'
    for line in apply(root) or ['nothing to change']:
        print(line)
