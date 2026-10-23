"""Check that Extreme loads exactly the Hardest rules under DE's preprocessor semantics.

DE's `#load-if-defined` only sees symbols the game defines, not defconsts (2026-10-21:
ERR2005 on Extreme from the old defconst alias; see classic_ai_extreme.py). This check:
- fails if the payload still relies on a defconst being seen by #load-if-defined
  (any defconst whose name is tested by a #load-if directive);
- preprocesses the payload script with DE semantics for every difficulty x population cap
  x map size x game mode and requires Extreme == Hardest (rule for rule) and every
  difficulty to define the constants the rules use (ce-/cr-unit-max, pop caps);
- with --before <old per>, requires every difficulty other than Extreme to load the same
  lines as the old script did under the old alias semantics, and Extreme to load what the
  old script meant for it (the Hardest rules).

  python outputs/toolkit/check_classic_extreme.py [--root payload/SWBG-Data] [--before old.per]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classic_ai_extreme import MARKER, PER

LEVELS = ('EASIEST', 'EASY', 'MODERATE', 'HARD', 'HARDEST', 'EXTREME')
CAPS = (25, 75, 200, 500, 1000)
SIZES = ('TINY-MAP', 'MEDIUM-MAP', 'GIANT-MAP')
MODES = ((), ('REGICIDE',), ('DEATH-MATCH',), ('WONDER-RACE',))


def preprocess(script, symbols, alias):
    """DE semantics when alias is False; the old offline model (defconsts define symbols) when True."""
    symbols = set(symbols)
    stack, active, out = [], True, []
    for raw in script.splitlines():
        line = raw.split(';', 1)[0].strip()
        if line.startswith(('#load-if-defined ', '#load-if-not-defined ')):
            directive, name = line.split()
            cond = (name in symbols) == (directive == '#load-if-defined')
            stack.append((active, cond))
            active = active and cond
        elif line == '#else':
            parent, cond = stack[-1]
            active = parent and not cond
        elif line == '#end-if':
            active = stack.pop()[0]
        elif line.startswith('#'):
            raise ValueError('unsupported directive ' + line)
        elif active and line:
            m = re.fullmatch(r'\(defconst\s+(\S+)\s+(-?\d+)\)', line)
            if m and alias:
                symbols.add(m[1])
            if line != '(defconst DIFFICULTY-HARDEST 1)':
                out.append(line)
    assert not stack, 'unclosed directive'
    return out


cli = argparse.ArgumentParser()
cli.add_argument('--root', type=Path, default=Path('payload/SWBG-Data'))
cli.add_argument('--before', type=Path)
args = cli.parse_args()
script = (args.root / PER).read_bytes().decode('utf-8')
before = args.before.read_bytes().decode('utf-8') if args.before else None
checks = 0


def check(ok, message):
    global checks
    checks += 1
    if not ok:
        raise SystemExit('FAIL ' + message)


check(MARKER in script, 'Extreme twin conditionals applied')
tested = set(re.findall(r'^#load-if(?:-not)?-defined (\S+)', script, re.M))
defined = set(re.findall(r'\(defconst (\S+) ', script))
check(not (tested & defined), f'no #load-if directive tests a defconst: {sorted(tested & defined)[:5]}')
configs = 0
for cap in CAPS:
    for size in SIZES:
        for mode in MODES:
            base = {f'POPULATION-CAP-{cap}', size, *mode}
            loaded = {lvl: preprocess(script, base | {'DIFFICULTY-' + lvl}, False) for lvl in LEVELS}
            check(loaded['EXTREME'] == loaded['HARDEST'], f'Extreme == Hardest {cap} {size} {mode}')
            for lvl, lines in loaded.items():
                text = '\n'.join(lines)
                for side in ('ce', 'cr'):
                    check(f'(defconst {side}-unit-max ' in text and f'(defconst {side}-pop-cap {cap})' in text,
                          f'{side}-unit-max / pop cap defined for {lvl} {cap} {size} {mode}')
            if before is not None:
                for lvl in LEVELS:
                    old = preprocess(before, base | {'DIFFICULTY-' + lvl}, True)
                    check(loaded[lvl] == old, f'{lvl} loads what it loaded before (old alias model) {cap} {size} {mode}')
            configs += 1
print(f'PASS {checks} checks; {configs} configurations x {len(LEVELS)} difficulties'
      + ('; identical to the pre-twin script (alias model)' if before is not None else ''))
