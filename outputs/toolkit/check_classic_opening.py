"""Offline checks of the Classic AI's Tech Level 1 Troop Center chain (classic_ai_opening.py).

Runs on the shipped scripts (default payload/SWBG-Data), from the repository root:
  python outputs/toolkit/check_classic_opening.py [--root payload/SWBG-Data]

- The bootstrap requests SWGB's building queue (sn-enable-new-building-system 0) once,
  and nothing else changes it.
- Every rule that a still-unset map identity (resource 1997 == 0) can enable, but a real
  identity would not, waits for (game-time > 3).
- A small interpreter replays the map-setup rules (every rule that writes special-map) for
  each difficulty, mode and faction, with the identity applied only after the first pass as
  in DE. SWGB Factions Savannah (identity 18) must stay a land map; an unmarked map keeps the
  source CUSTOM-MAP water branch; a marked water map is still water. As a self-test, the
  same replay without the guards must reproduce the 2026-10-20 regression (Savannah water).
- Land Tech Level 1 chain for both factions and every difficulty: a first Carbon Center rule
  without the dropsite-distance test, the Troop Center rule (Power Core + Food + Carbon
  centres), and the Tech Level 1 trooper rule.
This does not simulate the economy or prove in-game behavior.
"""
import argparse
import re
from pathlib import Path
from classic_ai_config import resolve_configuration
from classic_ai_opening import (BOOTSTRAP_NEW, DROPSITE, SETTLED, identities, is_first_carbon_rule,
                                needs_settled_identity, rule_spans)
from classic_ai_source import parse, render
from classic_ai_extreme import untwin

cli = argparse.ArgumentParser()
cli.add_argument('--root', type=Path, default=Path('payload/SWBG-Data'))
args = cli.parse_args()
ai = args.root/'resources/_common/ai'
# Logical single-copy view of the Hardest/Extreme twins (classic_ai_extreme.untwin).
script = untwin((ai/'SWGB Classic AI.per').read_text(encoding='utf-8'))
checks = 0
LEVELS = ('easiest', 'easy', 'moderate', 'hard', 'hardest', 'extreme')
MODES = (None, 'DEATH-MATCH', 'WONDER-RACE', 'DEFEND-WONDER')


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


def configuration(level, mode=None):
    symbols = {'DIFFICULTY-'+level.upper(), 'POPULATION-CAP-200', 'TINY-MAP', 'VICTORY-CONQUEST', 'TEAMS-LOCKED'}
    if mode:
        symbols.add(mode)
    return resolve_configuration(ai, symbols, 'boomer')[0]


# 1. SWGB building queue.
writes = re.findall(r'\(set-strategic-number sn-enable-new-building-system (\S+)\)', script)
check(writes == ['0'], f'sn-enable-new-building-system written once, to 0 ({writes})')
first = parse(script[slice(*rule_spans(script)[0])])[0]
check(BOOTSTRAP_NEW in render(first) and first[1] == ['true'] and ['disable-self'] in first,
      'Building queue set by the unconditional first rule')
for personality in sorted((ai/'SWGB Classic').glob('*.per')):
    check('sn-enable-new-building-system' not in personality.read_text(encoding='utf-8'),
          personality.name+': no building-system writes')

# 2. Map identity guard on the shipped text.
known = identities(script)
rules = [parse(script[a:b])[0] for a, b in rule_spans(script)]
guarded = [r for r in rules if needs_settled_identity(r, known)]
custom = [r for r in rules if ['up-resource-amount', '1997', '==', '0'] in r]
check(len(custom) == 6 and all(r in guarded for r in custom), 'All six CUSTOM-MAP (identity 0) rules need a settled identity')
check(all(r[2] == ['game-time', '>', '3'] for r in guarded), 'Every identity-0-enabled rule waits for (game-time > 3)')
check(len(guarded) == 66, f'66 guarded rules ({len(guarded)})')
# The guard sits directly after civ-selected; the source's own (game-time > 3) facts do not.
GUARD = re.compile(r'(\(civ-selected \d\)\n)  \(game-time > 3\)\n')


def strip_guards(text):
    return GUARD.sub(r'\1', text)


check(len(GUARD.findall(script)) == len(guarded), 'One guard per guarded rule, directly after civ-selected')

# 3. Map-setup replay. Identities: Savannah 18 (land), Sea 19 (water), unmarked map 0.
RELATIONS = {'==': int.__eq__, '!=': int.__ne__, '<': int.__lt__, '<=': int.__le__, '>': int.__gt__, '>=': int.__ge__}


def fact(node, state):
    head = node[0]
    if head in ('true', 'false'):
        return head == 'true'
    if head in ('and', 'or', 'nor', 'nand'):
        values = [fact(x, state) for x in node[1:]]
        value = all(values) if head in ('and', 'nand') else any(values)
        return value if head in ('and', 'or') else not value
    if head == 'not':
        return not fact(node[1], state)
    if head == 'civ-selected':
        return int(node[1]) == state['civ']
    if head == 'up-resource-amount':
        assert node[1] == '1997', node
        return RELATIONS[node[2]](state['identity'], int(node[3]))
    if head == 'game-time':
        return RELATIONS[node[1]](state['time'], int(node[2]))
    if head == 'cc-players-unit-type-count':
        # No carbon gas vents and fewer than 30 Gaia fish (Savannah has 24 shore fish).
        return RELATIONS[node[3]](0, int(node[4]))
    raise AssertionError('uninterpreted map-setup fact: '+render(node))


def special_map(text, civ, identity_at):
    """Interpret the special-map writers once per second, in rule order."""
    prefix = 'ce-' if civ == 1 else 'cr-'
    nodes = [n for n in parse(text) if isinstance(n, list)]
    consts = {n[1]: n[2] for n in nodes if n[0] == 'defconst'}
    writers = [n for n in nodes if n[0] == 'defrule'
               and any(isinstance(a, list) and a[:2] == ['set-goal', prefix+'special-map'] for a in n[n.index('=>')+1:])]
    disabled, goal = set(), consts[prefix+'NO']
    for second in range(12):
        state = dict(civ=civ, time=second, identity=identity_at(second))
        for index, rule in enumerate(writers):
            split = rule.index('=>')
            if index in disabled or not all(fact(f, state) for f in rule[1:split]):
                continue
            for action in rule[split+1:]:
                if action[:2] == ['set-goal', prefix+'special-map']:
                    goal = consts[action[2]]
                elif action == ['disable-self']:
                    disabled.add(index)
    return {consts[prefix+name]: name for name in ('NO', 'WATER', 'ASTEROID')}[goal]


def late(identity):
    """DE: the RMS identity is not yet applied on the first rule pass."""
    return lambda second: identity if second >= 1 else 0


check(script.count(SETTLED) - strip_guards(script).count(SETTLED) == len(guarded), 'Self-test strips exactly the guards')
replays = 0
for level in LEVELS:
    for mode in MODES:
        loaded = configuration(level, mode)
        name = f'{level}/{mode or "random-map"}'
        for civ in (1, 2):
            check(special_map(loaded, civ, late(18)) == 'NO', f'{name} civ {civ}: Savannah stays land when its identity arrives after pass 1')
            check(special_map(loaded, civ, lambda s: 18) == 'NO', f'{name} civ {civ}: Savannah land with an immediate identity')
            # Wonder Race does not load the source map branches at all.
            unmarked = 'WATER' if '(up-resource-amount 1997 == 0)' in loaded else 'NO'
            check(mode == 'WONDER-RACE' or unmarked == 'WATER', f'{name}: CUSTOM-MAP branch loaded')
            check(special_map(loaded, civ, lambda s: 0) == unmarked, f'{name} civ {civ}: unmarked map keeps the source CUSTOM-MAP branch')
            if mode is None:
                check(special_map(loaded, civ, late(19)) == 'WATER', f'{name} civ {civ}: Sea (19) is still water')
            replays += 1
        if mode is None and level in ('moderate', 'hard'):
            # Self-test on the same configuration with the guards stripped (the 2026-10-20 payload).
            stripped = strip_guards(loaded)
            check(stripped != loaded and all(special_map(stripped, civ, late(18)) == 'WATER' for civ in (1, 2)),
                  f'{name}: self-test, without the guards Savannah becomes water (2026-10-20 regression)')

# 4. Land Tech Level 1 chain, every difficulty and both factions.
for level in LEVELS:
    nodes = [n for n in parse(configuration(level)) if isinstance(n, list) and n[0] == 'defrule']
    for civ, prefix in ((1, 'ce-'), (2, 'cr-')):
        own = [n for n in nodes if n[1] == ['civ-selected', str(civ)]]
        texts = [render(n) for n in own]
        first_carbon = [t for t in texts if is_first_carbon_rule(t)]
        check(len(first_carbon) == 1 and DROPSITE not in first_carbon[0],
              f'{level} civ {civ}: first Carbon Center rule without the dropsite test')
        check(sum(DROPSITE in t and f'(build {prefix}bldg-dropcarbon)' in t for t in texts) == 1,
              f'{level} civ {civ}: the Tech Level 2 "build as needed" Carbon Center rule keeps its dropsite test')
        # (build X) or, since classic_ai_power_placement.py, the same build at the Power Core point.
        troop_center = [t for t in texts if (f'(build {prefix}bldg-traintrooper)' in t or
                                             f'(up-build place-point 0 c: {prefix}bldg-traintrooper)' in t)
                        and f'(not (goal {prefix}special-map {prefix}WATER))' in t]
        check(len(troop_center) == 1 and all(f'(building-type-count-total {prefix}bldg-{b} > 0)' in troop_center[0]
              for b in ('powercore', 'dropchow', 'dropcarbon')),
              f'{level} civ {civ}: land Troop Center after Power Core, Food and Carbon centres')
        opening = f'(unit-type-count {prefix}unit-laser-line < {prefix}TL1-trooper)'
        trooper = [n for n in own if render(n[2]) == opening]
        check(len(trooper) == 1 and render(trooper[0][3]) == f'(can-train {prefix}unit-laser-line)' and trooper[0].index('=>') == 4,
              f'{level} civ {civ}: unconditional Tech Level 1 trooper rule')

print('PASS', checks, 'checks;', replays, 'map-setup replays; runtime verification pending')
