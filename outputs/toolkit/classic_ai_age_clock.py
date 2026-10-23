"""Emulate the source `current-age-time` fact for the Classic AI in DE.

DE keeps its age timestamps (the `current-age-time` fact and, as observed, the
post-game timeline's age markers) for AoE2's own age technologies. SWGB Tech
Levels 2-4 are technologies 1-3, so DE never restarts that clock: after Tech Level 1
the fact reports time since the start of the game. The 2026-10-20 Hardest replay
shows it: on reaching Tech Level 2 at 11:58 both AIs fired the source bonus that
needs `current-age == 1` and `current-age-time >= 420` in the same pass as the
plain `current-age == 1` bonus. `current-age` itself (resource 6) is correct.

The port records the game time at which `current-age` last changed (goal 115, with
the last seen age in goal 114) and keeps the time spent in the current age in goal
116. Every source `(current-age-time <op> <value>)` becomes
`(up-compare-goal 116 c:<op> <value>)`. The clock rules run unconditionally before
every source rule, so each pass sees the current value.

Run from the repository root to apply the same transformation to an existing
script tree in place (idempotent):
  python outputs/toolkit/classic_ai_age_clock.py --root payload/SWBG-Data
"""
import argparse
import re
from pathlib import Path

AGE_SEEN = 114
AGE_START = 115
AGE_TIME = 116
GOALS = (AGE_SEEN, AGE_START, AGE_TIME)
MARKER = '; Source current-age-time emulation (goals 114-116).'
# The clock follows the XS observer bootstrap and precedes the nursery loop.
ANCHOR = '(defrule (true) => (up-get-fact player-number 0 104) (xs-script-call "swgbClassicObserve"))'
PATTERN = re.compile(r'\(current-age-time\s+(==|!=|<=|>=|<|>)\s+([^\s()]+)\)')


def clock_rules():
    """Three unconditional rules; goal 116 = seconds since current-age last changed."""
    return '\n'.join([
        MARKER,
        '; DE restarts its own age clock only for AoE2 age technologies, not SWGB Tech Levels.',
        f'(defrule (true) => (up-get-fact current-age 0 {AGE_TIME}))',
        f'(defrule (up-compare-goal {AGE_TIME} g:!= {AGE_SEEN}) =>',
        f' (up-modify-goal {AGE_SEEN} g:= {AGE_TIME}) (up-get-fact game-time 0 {AGE_START}))',
        f'(defrule (true) => (up-get-fact game-time 0 {AGE_TIME}) (up-modify-goal {AGE_TIME} g:- {AGE_START}))'])


def condition(op, value):
    """Parsed-node form used by port_classic_ai.translate."""
    return ['up-compare-goal', str(AGE_TIME), 'c:'+op, value]


def rewrite(text, main):
    """Return (text, replaced conditions). `main` inserts the clock rules once."""
    text, count = PATTERN.subn(lambda m: f'(up-compare-goal {AGE_TIME} c:{m[1]} {m[2]})', text)
    if main and MARKER not in text:
        newline = '\r\n' if '\r\n' in text else '\n'
        assert text.count(ANCHOR+newline) == 1, 'observer bootstrap anchor not found'
        text = text.replace(ANCHOR+newline, ANCHOR+newline+clock_rules().replace('\n', newline)+newline)
    return text, count


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--root', type=Path, default=Path('payload/SWBG-Data'))
    args = cli.parse_args()
    ai = args.root/'resources/_common/ai'
    paths = [ai/'SWGB Classic AI.per'] + sorted((ai/'SWGB Classic').glob('*.per'))
    total = 0
    for path in paths:
        with path.open(encoding='utf-8', newline='') as handle:
            before = handle.read()
        after, count = rewrite(before, path.name == 'SWGB Classic AI.per')
        total += count
        if after != before:
            with path.open('w', encoding='utf-8', newline='') as handle:
                handle.write(after)
        print(path.relative_to(args.root).as_posix(), 'conditions', count, 'changed' if after != before else 'unchanged')
    print('replaced', total, 'current-age-time conditions')


if __name__ == '__main__':
    main()
