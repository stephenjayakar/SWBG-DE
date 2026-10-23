r"""Guard: SWBG ships exactly one AI, SWGB Classic AI (ai_entries.py explains how DE lists AIs).

Fails when
- any .ai/.ai2 file is in SWBG-Data or SWBG-Logic (each one adds a lobby AI entry, e.g. the
  retired "SWGB Land AI.ai" or a second "SWGB Classic AI.ai" listing),
- SWGB Land AI, or any AI script not listed in ALLOWED, is in SWBG-Data's ai/ or drs/gamedata_x2/,
- the files that route DE's built-in entries (AI, AI (CD version), AI (HD version)) to SWGB
  Classic AI differ from ai_entries.py (PromiDE.per2, the only file allowed in drs/gamedata_x2,
  AI (HD version).per and
  Promisory\defaultConstants.per only (load "SWGB Classic AI"); the other files DE's PromiDE.per2
  and randomgame.per2 load are comment-only stubs in the ai folder), or Classic's script or XS is
  missing,
- recipe.tsv ships an .ai file or a retired file, or misses one of those files,
- the installer's $RetiredDataFiles differs from ai_entries.RETIRED.
With a DE install (default E:\SteamLibrary\steamapps\common\AoE2DE, or --de) it also checks DE's
side: the exe still names PromiDE, RandomGame, "AI (HD version)" and E3-p2.ai, the string table
still has the three labels, DE ships no other .ai file (a new built-in entry would need routing),
and DE's PromiDE.per2 and randomgame.per2 load exactly Promisory\defaultConstants plus the stubbed
files (a DE patch that adds a load would otherwise run DE code). Then it runs itself on mutated
copies of the payload.

  python outputs/toolkit/check_single_ai.py [--payload payload] [--de DIR | --no-de] [--no-self-test]
"""
from pathlib import Path
import argparse, json, re, shutil, sys, tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ai_entries import (AI_DIR, CLASSIC_FILES, DE_ENTRIES, ENTRIES, GAMEDATA, RETIRED, STUBS,
                        de_direct_loads, expected_files)

ROOT = Path(__file__).resolve().parents[2]
DE_DEFAULT = Path(r'E:\SteamLibrary\steamapps\common\AoE2DE')
RECIPE = ROOT/'outputs/installer/installer/recipe.tsv'
INSTALLER = ROOT/'outputs/installer/installer/Install-SWGB-DE.ps1'
CHAIN = f'{AI_DIR}/Promisory/defaultConstants.per'
# Every file allowed in SWBG-Data's ai/ (besides Classic's personality folder "SWGB Classic") and
# drs/gamedata_x2/. Anything else there is a second AI script or an override of another DE script,
# so it has to be added on purpose.
ALLOWED = {f'{AI_DIR}/SWGB Classic AI.per', f'{AI_DIR}/swgb_classic_ai.xs', *ENTRIES, *STUBS}
# DE build 185872: string keys of the three built-in labels, names in the exe, its own .ai files.
DE_LABELS = {'NEW_AI_TAG': 'AI', 'ORIG_AI_TAG': 'AI (CD version)', 'HD_AI_TAG': 'AI (HD version)'}
DE_EXE_NAMES = (b'PromiDE', b'RandomGame', b'AI (HD version)', b'E3-p2.ai')
DE_AI_FILES = {f'{AI_DIR}/AI (HD version).ai', f'{AI_DIR}/E3-p2.ai', f'{GAMEDATA}/randomgame.ai'}


def is_ai_listing(path: str) -> bool:
    return path.lower().endswith(('.ai', '.ai2'))


def check(data: Path, logic: Path, recipe: Path = RECIPE, installer: Path = INSTALLER) -> list[str]:
    problems = []
    for mod, root in (('SWBG-Data', data), ('SWBG-Logic', logic)):
        for f in sorted(root.rglob('*')):
            rel = f.relative_to(root).as_posix()
            if f.is_file() and is_ai_listing(rel):
                problems.append(f'{mod}/{rel}: .ai file adds a second lobby AI entry')
    for f in sorted(data.rglob('*')):
        rel = f.relative_to(data).as_posix()
        if 'land ai' in rel.lower():
            problems.append(f'SWBG-Data/{rel}: SWGB Land AI is retired')
        elif f.is_file() and f.suffix.lower() in ('.per', '.per2', '.xs', '.txt', '.json', '.rms') \
                and b'swgb land ai' in f.read_bytes().lower():
            problems.append(f'SWBG-Data/{rel}: mentions SWGB Land AI')
    for folder in (AI_DIR, GAMEDATA):
        for f in sorted((data/folder).rglob('*')) if (data/folder).is_dir() else []:
            rel = f.relative_to(data).as_posix()
            if f.is_file() and rel not in ALLOWED and not is_ai_listing(rel) \
                    and not rel.startswith(f'{AI_DIR}/SWGB Classic/'):
                problems.append(f'SWBG-Data/{rel}: unexpected AI script (not in ALLOWED)')
    for rel in RETIRED:
        if (data/rel).exists():
            problems.append(f'SWBG-Data/{rel}: retired file shipped')
    for rel, want in expected_files().items():
        if not (data/rel).is_file():
            problems.append(f'SWBG-Data/{rel}: missing; a DE lobby entry would run DE code (ai_entries.py)')
        elif (data/rel).read_bytes() != want:
            problems.append(f'SWBG-Data/{rel}: differs from ai_entries.py (entries only load SWGB Classic AI, stubs are empty)')
    for rel in CLASSIC_FILES:
        if not (data/rel).is_file():
            problems.append(f'SWBG-Data/{rel}: missing; (load "SWGB Classic AI") fails')
    # recipe.tsv: what the installer ships.
    ship = set()
    for line in recipe.read_text(encoding='ascii').splitlines():
        f = line.split('\t')
        if len(f) == 4 and f[0] == 'ship':
            ship.add((f[1], f[2]))
            if is_ai_listing(f[2]) or 'land ai' in f[2].lower() or (f[1] == 'SWBG-Data' and f[2] in RETIRED):
                problems.append(f'recipe.tsv ships {f[1]}/{f[2]}')
    for rel in [*expected_files(), *CLASSIC_FILES]:
        if ('SWBG-Data', rel) not in ship:
            problems.append(f'recipe.tsv does not ship SWBG-Data/{rel}')
    # Installer cleanup list.
    m = re.search(r"^\$RetiredDataFiles = @\(([^)]*)\)", installer.read_text(encoding='utf-8'), re.M)
    listed = sorted(s.replace('\\', '/') for s in re.findall(r"'([^']*)'", m.group(1))) if m else None
    if listed != sorted(RETIRED):
        problems.append(f'{installer.name}: $RetiredDataFiles {listed} != ai_entries.RETIRED {sorted(RETIRED)}')
    return problems


def check_de(de: Path) -> list[str]:
    problems = []
    exe = (de/'AoE2DE_s.exe').read_bytes()
    for name in DE_EXE_NAMES:
        if name not in exe:
            problems.append(f'AoE2DE_s.exe no longer names {name.decode()}; re-check how DE lists AIs')
    strings = (de/'resources/en/strings/key-value/key-value-strings-utf8.txt').read_text(encoding='utf-8', errors='replace')
    for key, label in DE_LABELS.items():
        if not re.search(rf'^{key} "{re.escape(label)}"', strings, re.M):
            problems.append(f'DE string {key} is no longer "{label}"')
    shipped = {f.relative_to(de).as_posix() for d in (AI_DIR, GAMEDATA) for f in (de/d).iterdir()
               if f.is_file() and is_ai_listing(f.name)}
    if shipped != DE_AI_FILES:
        problems.append(f'DE ships other .ai files {sorted(shipped ^ DE_AI_FILES)}: route them in ai_entries.py')
    for label, (rel, _) in DE_ENTRIES.items():
        if not (de/rel).is_file():
            problems.append(f'DE has no {rel} (entry "{label}"); re-check how DE lists AIs')
    loads = de_direct_loads(de)
    routed = set(STUBS) | {CHAIN}
    if loads != routed:
        problems.append(f'DE PromiDE.per2/randomgame.per2 loads changed: {sorted(loads ^ routed)}; update ai_entries.py')
    for rel in STUBS:  # an ai-folder stub must not replace an unrelated DE file
        if rel.startswith(f'{AI_DIR}/elite') and (de/rel).is_file():
            problems.append(f'DE now ships {rel}; the stub would replace it')
    return problems


def self_test(payload: Path) -> int:
    """Each mutation of a copy of SWBG-Data (or of the recipe / installer) must be caught."""
    rule = b'(defrule (true) => (do-nothing))\n'
    mutations = {
        'Land AI back': lambda d: ((d/AI_DIR/'SWGB Land AI.ai').write_bytes(b''),
                                   (d/AI_DIR/'SWGB Land AI.per').write_bytes(rule)),
        'second Classic listing': lambda d: (d/AI_DIR/'SWGB Classic AI.ai').write_bytes(b''),
        'any .ai in a subfolder': lambda d: (d/AI_DIR/'SWGB Classic'/'Other.ai').write_bytes(b''),
        'PromiDE override lower-case': lambda d: (d/GAMEDATA/'PromiDE.per2').rename(d/GAMEDATA/'promide.per2'),
        'second file in gamedata_x2': lambda d: (d/GAMEDATA/'randomgame.per2').write_bytes(b'(load "SWGB Classic AI")'+bytes([10])),
        'PromiDE runs another AI': lambda d: (d/GAMEDATA/'PromiDE.per2').write_bytes(b'(load "Promisory\\init")\n'),
        'CD/AI chain entry missing': lambda d: (d/CHAIN).unlink(),
        'HD entry missing': lambda d: (d/AI_DIR/'AI (HD version).per').unlink(),
        'stub missing': lambda d: (d/STUBS[-1]).unlink(),
        'stub with rules': lambda d: (d/STUBS[0]).write_bytes(rule),
        'extra AI script': lambda d: (d/AI_DIR/'Other AI.per').write_bytes(rule),
        'Classic XS missing': lambda d: (d/CLASSIC_FILES[1]).unlink(),
    }
    caught = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, mutate in mutations.items():
            d = Path(tmp)/'data'
            if d.exists():
                shutil.rmtree(d)
            shutil.copytree(payload/'SWBG-Data', d)
            mutate(d)
            assert check(d, payload/'SWBG-Logic'), f'self-test: mutation "{name}" not caught'
            caught += 1
        recipe = Path(tmp)/'recipe.tsv'
        recipe.write_text(RECIPE.read_text(encoding='ascii') + 'ship\tSWBG-Data\tresources/_common/ai/SWGB Land AI.ai\tx\n',
                          encoding='ascii', newline='\n')
        assert check(payload/'SWBG-Data', payload/'SWBG-Logic', recipe=recipe), 'self-test: recipe row not caught'
        ps1 = Path(tmp)/'Install.ps1'
        ps1.write_text(INSTALLER.read_text(encoding='utf-8').replace("'resources\\_common\\ai\\SWGB Classic AI.ai'", "'x'"),
                       encoding='utf-8')
        assert check(payload/'SWBG-Data', payload/'SWBG-Logic', installer=ps1), 'self-test: installer list not caught'
        caught += 2
    return caught


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--payload', type=Path, default=ROOT/'payload')
    ap.add_argument('--de', type=Path, default=None, help=f'DE install (default {DE_DEFAULT} when present)')
    ap.add_argument('--no-de', action='store_true')
    ap.add_argument('--no-self-test', action='store_true')
    a = ap.parse_args()
    problems = check(a.payload/'SWBG-Data', a.payload/'SWBG-Logic')
    de = None if a.no_de else (a.de or (DE_DEFAULT if (DE_DEFAULT/'AoE2DE_s.exe').is_file() else None))
    if de:
        problems += check_de(de)
    for p in problems:
        print('PROBLEM', p)
    if problems:
        sys.exit(f'{len(problems)} one-AI problems')
    mutations = 0 if a.no_self_test else self_test(a.payload)
    print(json.dumps(dict(single_ai='ok', ai='SWGB Classic AI', lobby_entries=sorted(DE_ENTRIES),
                          classic_entries=len(ENTRIES), stubs=len(STUBS),
                          de_checked=str(de) if de else None, self_test_mutations_caught=mutations)))


if __name__ == '__main__':
    main()
