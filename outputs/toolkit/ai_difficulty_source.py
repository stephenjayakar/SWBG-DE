"""Read numeric difficulty settings from the installed Computer Classic AI.

This is a small source preprocessor, not an interpreter for the game's AI.
Only the directives used in the inspected source files are accepted.
"""
import hashlib
import re
from pathlib import Path

SOURCE = Path('E:/GOG Games/Star Wars - Galactic Battlegrounds/Game/AI/Computer Classic')
LEVELS = ('easiest', 'easy', 'moderate', 'hard', 'hardest')


def preprocess(script, symbols, defconst_symbols=True):
    """defconst_symbols: SWGB's preprocessor (the source) lets a defconst define a
    #load-if symbol; DE's does not (pass False for scripts DE loads)."""
    symbols = set(symbols)
    stack = []
    active = True
    output = []
    for raw in script.splitlines():
        line = raw.split(';', 1)[0].strip()
        if line.startswith(('#load-if-defined ', '#load-if-not-defined ')):
            directive, name = line.split()
            condition = name in symbols
            if directive == '#load-if-not-defined':
                condition = not condition
            stack.append((active, condition))
            active = active and condition
        elif line == '#else':
            parent, condition = stack[-1]
            active = parent and not condition
        elif line == '#end-if':
            active = stack.pop()[0]
        elif line.startswith('#'):
            raise ValueError('Unsupported source directive: ' + line)
        elif active:
            output.append(line)
            match = re.fullmatch(r'\(defconst\s+(\S+)\s+(-?\d+)\)', line)
            if match and defconst_symbols:
                symbols.add(match[1])
    assert not stack, 'Unclosed preprocessor directive'
    return '\n'.join(output)


def constants(text):
    pairs = re.findall(r'\(defconst\s+(\S+)\s+(-?\d+)\)', text)
    result = {}
    for key, value in pairs:
        # Some installed source tables repeat the same declaration.
        assert key not in result or result[key] == int(value), (key, value)
        result[key] = int(value)
    return result


def profiles(source=SOURCE):
    names = ('CC_population.per', 'CC_military-population.per', 'CC_sn-soldiers.per',
             'CC_homebase.per', 'CC_attack.per', 'CC_age-advacement.per')
    files = {name: (source/name).read_text(errors='strict') for name in names}
    provenance = {name: hashlib.sha256((source/name).read_bytes()).hexdigest() for name in names}
    caps = sorted(set(map(int, re.findall(r'POPULATION-CAP-(\d+)', files[names[0]]))))
    table = {}
    for cap in caps:
        table[cap] = {}
        for level in LEVELS:
            symbols = {f'POPULATION-CAP-{cap}', 'DIFFICULTY-' + level.upper(), 'EMPIRE'}
            pop = constants(preprocess(files[names[0]], symbols))
            # TL1 trooper target is outside faction-specific branches.
            military = preprocess(files[names[1]], symbols)
            tl1 = int(re.search(r'\(defconst TL1-trooper (\d+)\)', military)[1])
            if level == 'easiest':
                workers = [pop['worker-easiest'] + 1] * 4  # source uses <=
            elif level == 'easy':
                workers = [pop['worker-easy'] + 1] * 4
            elif level == 'moderate':
                workers = [pop['civ-dark-mod'], pop['civ-feudal-mod'],
                           pop['civ-feudal-mod'], pop['civ-dark-mod']]
            else:
                workers = [pop['civ-dark-hard'], pop['civ-feudal'],
                           pop['civ-castle-hard'], pop['fifty-percent-pop']]
            table[cap][level] = dict(workers=workers, population_limit=pop['unit-max'],
                                     opening_troopers=tl1)
    combat = {}
    for level in LEVELS:
        text = preprocess(files['CC_sn-soldiers.per'], {'DIFFICULTY-' + level.upper()})
        combat[level] = {
            'response': int(re.search(r'\(set-strategic-number sn-percent-enemy-sighted-response (\d+)\)', text)[1]),
            'maintain_distance': int(re.search(r'\(set-difficulty-parameter ability-to-maintain-distance (\d+)\)', text)[1]),
            'dodge': int(re.search(r'\(set-difficulty-parameter ability-to-dodge-missiles (\d+)\)', text)[1])}
    return table, combat, provenance
