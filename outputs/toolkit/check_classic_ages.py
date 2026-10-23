"""Offline checks of the Classic AI's Tech Level advancement and age clock.

Runs on the shipped scripts (default payload/SWBG-Data), from the repository root:
  python outputs/toolkit/check_classic_ages.py [--root payload/SWBG-Data] [--skip-lint]

- No raw `current-age-time` fact remains: DE does not restart it for SWGB Tech Levels
  (see classic_ai_age_clock.py). The emulated clock (goals 114-116) runs before every
  source rule, nothing else writes its goals, and a small interpreter of the emitted
  rules shows the clock restarting when the age changes.
- Every DE difficulty loads the source age-advancement rules for research 1-3
  (SWGB TECH-AGE2..4): Hard, Hardest and Extreme advance independently with the same
  rules; Moderate waits for its TL1 troop force; Standard (source Easy) follows any
  human to each level; Easiest follows every human to Tech Level 2 only.
- The pinned independent parser lints each difficulty and personality.
This does not simulate the economy or prove in-game behavior.
"""
import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from classic_ai_age_clock import AGE_TIME, GOALS, MARKER, clock_rules
from classic_ai_config import resolve_configuration
from classic_ai_source import parse, render
from classic_ai_extreme import untwin

cli = argparse.ArgumentParser()
cli.add_argument('--root', type=Path, default=Path('payload/SWBG-Data'))
cli.add_argument('--skip-lint', action='store_true')
args = cli.parse_args()
ai = args.root/'resources/_common/ai'
main_path = ai/'SWGB Classic AI.per'
# Logical single-copy view of the Hardest/Extreme twins (classic_ai_extreme.untwin).
script = untwin(main_path.read_text(encoding='utf-8'))
personalities = {p.name: p.read_text(encoding='utf-8') for p in sorted((ai/'SWGB Classic').glob('*.per'))}
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


# 1. Age clock: no engine current-age-time, a single unconditional clock ahead of every use.
for name, text in [(main_path.name, script), *personalities.items()]:
    check(not re.search(r'\(\s*current-age-time\b', text), name+': raw current-age-time (DE never restarts it for SWGB Tech Levels)')
uses = sum(text.count(f'(up-compare-goal {AGE_TIME} c:') for text in [script, *personalities.values()])
check(uses == 66, f'All 66 source current-age-time conditions use the emulated clock ({uses})')
check(script.count(MARKER) == 1 and script.count(clock_rules()) == 1, 'Age clock emitted once, unmodified')
start = script.index(MARKER)
prefix = script[:start]
depth = 0
for line in prefix.splitlines():
    line = line.split(';', 1)[0].strip()
    depth += line.startswith('#load-if') - (line == '#end-if')
check(depth == 0, 'Age clock is outside every load-time condition')
check(f'(up-compare-goal {AGE_TIME} c:' not in prefix, 'Age clock precedes every use')
block = [node for node in parse(clock_rules()) if node[0] == 'defrule']
check(len(block) == 3, 'Three age clock rules')
writers = re.compile(r'\((?:set-goal|up-modify-goal)\s+(\d+)|\(up-get-fact\s+[\w-]+\s+\S+\s+(\d+)\)|xsSetGoal\((\d+)')
outside = script.replace(clock_rules(), '')
for name, text in [(main_path.name, outside), *personalities.items()]:
    written = {int(a or b or c) for a, b, c in writers.findall(text)}
    check(not written & set(GOALS), name+': nothing else writes goals 114-116')
for xs in sorted(args.root.rglob('*.xs')):
    written = {int(c) for _, _, c in writers.findall(xs.read_text(encoding='utf-8'))}
    check(not written & set(GOALS), xs.name+': XS does not write goals 114-116')


def run_clock(age_at):
    """Interpret the emitted clock rules once per game second; return goal 116 per second."""
    goals, history = {}, []
    ops = {'==': int.__eq__, '!=': int.__ne__, '<': int.__lt__, '<=': int.__le__, '>': int.__gt__, '>=': int.__ge__}
    for second in range(0, 3600):
        facts = {'current-age': age_at(second), 'game-time': second}
        for rule in block:
            split = rule.index('=>')
            ok = True
            for fact in rule[1:split]:
                if fact == ['true']:
                    continue
                assert fact[0] == 'up-compare-goal', fact
                kind, op = fact[2].split(':')
                right = goals.get(int(fact[3]), 0) if kind == 'g' else int(fact[3])
                ok = ok and ops[op](goals.get(int(fact[1]), 0), right)
            if not ok:
                continue
            for action in rule[split+1:]:
                if action[0] == 'up-get-fact':
                    goals[int(action[3])] = facts[action[1]]
                elif action[0] == 'up-modify-goal':
                    target, value = int(action[1]), goals.get(int(action[3]), 0)
                    goals[target] = {'g:=': value, 'g:-': goals.get(target, 0)-value}[action[2]]
                else:
                    raise AssertionError(action)
        history.append(goals[AGE_TIME])
    return history


# Replay timings: Tech Level 2 at 718 s (11:58), Tech Level 3 at 1500 s.
clock = run_clock(lambda t: 0 if t < 718 else 1 if t < 1500 else 2)
check(clock[600] == 600 and clock[717] == 717, 'Tech Level 1 time counts from the start of the game')
check(clock[718] == 0 and clock[718+420] == 420 and clock[1499] == 781, 'Tech Level 2 restarts the clock')
check(clock[1500] == 0 and clock[1800] == 300, 'Tech Level 3 restarts the clock')
check(not (clock[718] >= 420), 'Hardest 7-minute Tech Level 2 bonus no longer fires on arrival')
advanced = run_clock(lambda t: 1)
check(advanced[0] == 0 and advanced[300] == 300, 'Advanced Tech Level 2 starts count from game start')

# 2. Age-advancement gates per DE difficulty (DE numbering: easiest 4 ... hardest 0, extreme -1).
techs = Path('work/original-ai/current-dat/techs.tsv')
if techs.exists():
    names = {r['id']: r['name'] for r in csv.DictReader(techs.open(), delimiter='\t')}
    check([names[t] for t in '123'] == ['TECH-AGE2', 'TECH-AGE3', 'TECH-AGE4'], 'research 1-3 are the DAT Tech Level techs')
levels = dict(easiest=4, easy=3, moderate=2, hard=1, hardest=0, extreme=-1)
relations = {'==': int.__eq__, '!=': int.__ne__, '<': int.__lt__, '<=': int.__le__, '>': int.__gt__, '>=': int.__ge__}


def evaluate(node, difficulty):
    """Three-valued: True/False for difficulty and constant facts, None otherwise."""
    head = node[0]
    if head in ('true', 'false'):
        return head == 'true'
    if head == 'difficulty':
        return relations[node[1]](difficulty, levels[node[2]])
    if head in ('and', 'or'):
        values = [evaluate(x, difficulty) for x in node[1:]]
        if head == 'and':
            return False if False in values else None if None in values else True
        return True if True in values else None if None in values else False
    if head in ('not', 'nand', 'nor'):
        inner = evaluate(node[1], difficulty) if head == 'not' else evaluate(['and' if head == 'nand' else 'or', *node[1:]], difficulty)
        return None if inner is None else not inner
    return None


def age_rules(level, personality, civ):
    symbols = {'DIFFICULTY-'+level.upper(), 'POPULATION-CAP-200', 'TINY-MAP', 'VICTORY-CONQUEST', 'TEAMS-LOCKED'}
    text, _ = resolve_configuration(ai, symbols, personality)
    found = {}
    for node in parse(text):
        if not (isinstance(node, list) and node[0] == 'defrule'):
            continue
        split = node.index('=>')
        facts, actions = node[1:split], node[split+1:]
        if facts[0] != ['civ-selected', civ]:
            continue
        research = [a[1] for a in actions if a[0] == 'research' and a[1] in ('1', '2', '3')]
        values = [evaluate(f, levels[level]) for f in facts[1:]]
        if not research or False in values:
            continue
        gates = tuple(render(f) for f, v in zip(facts[1:], values) if v is None)
        for tech in research:
            found.setdefault(tech, []).append(gates)
    return found


def human_gate(gates, tech):
    pattern = r'\(players-current-age (any|every)-human (>=|==) (\d)\)'
    return {(m[1], int(m[3])) for g in gates for m in [re.fullmatch(pattern, g)] if m}


summary = {}
for civ in ('1', '2'):
    for personality in ('bully', 'boomer', 'feeder'):
        found = {level: age_rules(level, personality, civ) for level in levels}
        key = f'civ{civ}-{personality}'
        summary[key] = {level: {t: len(v) for t, v in sorted(rules.items())} for level, rules in found.items()}
        check(found['hard'] == found['hardest'] == found['extreme'], key+': Hardest/Extreme share Hard age rules')
        for level in ('moderate', 'hard'):
            for tech in '123':
                independent = [g for g in found[level].get(tech, []) if not human_gate(g, tech)]
                check(independent, f'{key} {level}: research {tech} without a human-age gate')
            check(any(set(g) == {f'(can-research-with-escrow {t})'} for t in '23' for g in found[level].get(t, [])),
                  f'{key} {level}: TL3/TL4 advance as resources permit')
        check(any(set(g) == {'(can-research-with-escrow 1)'} for g in found['hard']['1']), key+': Hard TL2 as resources permit')
        troop = '(unit-type-count {0}unit-laser-line >= {0}TL1-trooper)'.format('ce-' if civ == '1' else 'cr-')
        check(found['moderate']['1'] and all(troop in g for g in found['moderate']['1']), key+': Moderate TL2 waits for TL1 troopers')
        for tech, level in (('1', 1), ('2', 2), ('3', 3)):
            rules = found['easy'].get(tech, [])
            check(rules and all(any(kind == 'any' and n == level for kind, n in human_gate(g, tech)) for g in rules),
                  f'{key} Standard: research {tech} follows any human')
        check(found['easiest'].get('1') and all(('every', 1) in human_gate(g, '1') for g in found['easiest']['1']),
              key+': Easiest TL2 follows every human')
        check(not found['easiest'].get('2') and not found['easiest'].get('3'), key+': Easiest stops at Tech Level 2')

# 3. Pinned independent parser on each difficulty and personality.
lint = []
if not args.skip_lint:
    parser = Path('work/ai-parser')
    revision = subprocess.check_output(['git', '-C', str(parser), 'rev-parse', 'HEAD'], text=True).strip()
    check(revision == '3dfa2583b7c2ec36b85ccb421ebd0abe9ff276ba', 'Pinned parser revision')
    env = dict(os.environ, PYTHONPATH=str((parser/'src').resolve()))
    scratch = Path('work/classic-ages')
    lintroot = scratch/'resources/_common/ai'
    if scratch.exists():
        assert scratch.resolve().is_relative_to(Path('work').resolve())
        shutil.rmtree(scratch)
    (lintroot/'SWGB Classic').mkdir(parents=True)
    shutil.copy2(ai/'SWGB Classic/swgb_classic_ai.xs', lintroot/'SWGB Classic/swgb_classic_ai.xs')
    # DE resolves (include "swgb_classic_ai.xs") from resources/_common/xs; the parser looks beside the script.
    shutil.copy2(args.root/'resources/_common/xs/swgb_classic_ai.xs', lintroot/'swgb_classic_ai.xs')
    (lintroot/'SWGB Classic AI.ai').write_bytes(b'')
    for level in levels:
        for personality in ('bully', 'boomer', 'feeder'):
            symbols = {'DIFFICULTY-'+level.upper(), 'POPULATION-CAP-200', 'TINY-MAP', 'VICTORY-CONQUEST', 'TEAMS-LOCKED'}
            loaded, _ = resolve_configuration(ai, symbols, personality)
            (lintroot/'SWGB Classic AI.per').write_text(loaded)
            dest = scratch/f'{level}-{personality}.json'
            result = subprocess.run([sys.executable, '-m', 'aoe2_ai_lab', 'lint-package', str(lintroot), '--output', str(dest),
                                     '--fail-confidence', 'conditional', '--fail-level', 'info'], capture_output=True, text=True, env=env)
            details = json.loads(dest.read_text())
            check(result.returncode == 0 and not details['finding_groups'], f'{level}-{personality}: '+str(details.get('finding_groups'))[:2000])
            lint.append(f'{level}-{personality}')
            print('PASS lint', level, personality, flush=True)

print(json.dumps(dict(age_rules=summary['civ1-boomer']), indent=1))
print('PASS', checks, 'checks;', len(lint), 'parser configurations; runtime verification pending')
