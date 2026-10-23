"""Let the Classic AI reach its Tech Level 1 troopers in DE (Troop Center chain).

The 2026-10-20 Savannah recordings (Moderate 15:13, Hardest 19:34) and the 2026-09-29 /
2026-10-19 Hard ones show the same opening: no Troop Center (87) before 10:00 on Hard and
Hardest, none at all on Moderate, so no troopers and no Moderate Tech Level 2. Three
port/engine differences cause it (details in ORIGINAL-AI.md):

1. Map identity race. Source map branches are load-time symbols; the port tests the map
   identity that each SWGB RMS writes to resource 1997 (`effect_amount 1 1997 0 N`). DE
   applies RMS effects after the game is created: the recordings' start state already has
   Tech Level 1's effects but resource 1997 is still 0. The first rule pass therefore takes
   the source CUSTOM-MAP branch (identity 0), which sets special-map WATER and disables
   itself. Savannah became a water map: Shipyard and fishing ships at Tech Level 1, and the
   Troop Center waits for the Shipyard or 10:00 instead of Power Core + Food + Carbon
   centres. Every rule that a still-unset identity can enable (identity 0, or a negated
   identity test) now also needs `(game-time > 3)`, the delay the source itself uses for its
   Gaia-based water detection. Rules that need a real identity are unchanged.
   Correction (2026-10-21 in-game probe): DE never applies that effect at all, so the guard
   alone only delayed the water branch by 3 s. classic_ai_map_identity.py now sets resource
   1997 from XS by map name on the first rule pass; the guard keeps unknown maps working.
2. DE's new building system. The bootstrap set sn-enable-new-building-system 1, so every
   rule pass queued another copy of a requested building. SWGB (and DE with 0) queues a type
   only when none is waiting or under construction. The recordings show 3-4 Prefab
   Shelters at 0:00 from the source's single "no shelter yet" rule, four Shipyard
   placements in one second, eight farms in 28 seconds and 32 shelters by 19 minutes.
   The cheap repeated buildings come first in rule order and took every carbon unit that
   the Power Core (200), Carbon Center (100) and Troop Center (160) needed. Set to 0.
3. First Carbon Center. The source's Tech Level 1 Carbon Center rule also needs
   `(dropsite-min-distance carbon > 5)`. In DE that counts the straggler trees the SWGB
   maps place 4-8 tiles from the Command Center, so it stays false until they are cut
   (DE's AI reference warns against using it for first dropsites). Moderate never built
   one in 15 minutes although it held 100-200 unspent carbon for over two minutes, and the
   land Troop Center needs it. The distance test is dropped from that first-centre rule
   only (it already requires none built); the "build as needed" rules keep it.

Run from the repository root to apply the same transformation to an existing script tree
in place (idempotent):
  python outputs/toolkit/classic_ai_opening.py --root payload/SWBG-Data
"""
import argparse
import re
from pathlib import Path
from classic_ai_source import parse

IDENTITY = '1997'
SETTLED = '(game-time > 3)'
BOOTSTRAP_OLD = '(set-strategic-number sn-enable-new-building-system 1)'
BOOTSTRAP_NEW = '(set-strategic-number sn-enable-new-building-system 0)'
BOOTSTRAP_NOTE = ('; SWGB queues a building type only when none is waiting or under construction '
                  '(DE new building system off).')
DROPSITE = '(dropsite-min-distance wood > 5)'
# The source's Tech Level 1 "first Carbon Center" rule (CC_carbon.per), with or without DROPSITE.
FIRST_CARBON = ('(resource-found wood)', 'bldg-main > 0)', 'bldg-dropchow > 0)', 'bldg-dropcarbon == 0)')


def rule_spans(text):
    """(start, end) of every top-level defrule, skipping comments and strings."""
    spans, depth, start, i, n = [], 0, None, 0, len(text)
    while i < n:
        c = text[i]
        if c == ';':
            i = text.find('\n', i)
            i = n if i < 0 else i
            continue
        if c == '"':
            i = text.index('"', i+1)+1
            continue
        if c == '(':
            if depth == 0 and text.startswith('(defrule', i):
                start = i
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0 and start is not None:
                spans.append((start, i+1))
                start = None
        i += 1
    assert depth == 0
    return spans


RELATIONS = {'==': int.__eq__, '!=': int.__ne__, '<': int.__lt__, '<=': int.__le__, '>': int.__gt__, '>=': int.__ge__}


def evaluate(node, identity):
    """Three-valued: map-identity facts are known, every other fact is unknown (None)."""
    head = node[0]
    if head in ('true', 'false'):
        return head == 'true'
    if head == 'up-resource-amount' and node[1] == IDENTITY:
        return RELATIONS[node[2]](identity, int(node[3]))
    if head in ('and', 'or'):
        values = [evaluate(x, identity) for x in node[1:]]
        if head == 'and':
            return False if False in values else None if None in values else True
        return True if True in values else None if None in values else False
    if head in ('not', 'nand', 'nor'):
        inner = evaluate(node[1], identity) if head == 'not' else evaluate(['and' if head == 'nand' else 'or', *node[1:]], identity)
        return None if inner is None else not inner
    return None


def facts(rule):
    return rule[1:rule.index('=>')]


def identities(text):
    return sorted({int(x) for x in re.findall(r'\(up-resource-amount 1997 == (\d+)\)', text)} | {0, 9999})


def needs_settled_identity(rule, known):
    """A still-unset identity (0) can enable the rule, while some real identity would not."""
    if IDENTITY not in str(facts(rule)):
        return False
    def value(identity):
        values = [evaluate(f, identity) for f in facts(rule)]
        return False if False in values else None if None in values else True
    return value(0) is not False and any(value(i) is False for i in known if i)


def is_first_carbon_rule(block):
    return (all(part in block for part in FIRST_CARBON) and 'current-age' not in block
            and re.search(r'\(can-build c[er]-bldg-dropcarbon\)', block)
            and re.search(r'\(build c[er]-bldg-dropcarbon\)', block))


def rewrite(text, main):
    """Return (text, stats). Only the main Classic script carries these rules."""
    stats = dict(guarded=0, first_carbon=0, bootstrap=0)
    if not main:
        return text, stats
    newline = '\r\n' if '\r\n' in text else '\n'
    known = identities(text)
    out, last = [], 0
    for start, end in rule_spans(text):
        block = text[start:end]
        rule = parse(block)[0]
        new = block
        if needs_settled_identity(rule, known):
            stats['guarded'] += 1
            civ = re.match(r'\(defrule\r?\n(  \(civ-selected \d\)\r?\n)', block)
            assert civ, block[:200]
            if not block[civ.end():].startswith('  '+SETTLED):
                new = block[:civ.end()]+'  '+SETTLED+newline+block[civ.end():]
        if is_first_carbon_rule(block):
            stats['first_carbon'] += 1
            new = new.replace('  '+DROPSITE+newline, '', 1)
        out.append(text[last:start]+new)
        last = end
    text = ''.join(out)+text[last:]
    if BOOTSTRAP_OLD in text:
        assert text.count(BOOTSTRAP_OLD) == 1
        text = text.replace(BOOTSTRAP_OLD, BOOTSTRAP_NEW)
    if BOOTSTRAP_NEW in text:
        stats['bootstrap'] = 1
        line = next(l for l in text.split(newline) if BOOTSTRAP_NEW in l)
        if BOOTSTRAP_NOTE not in text:
            text = text.replace(line, BOOTSTRAP_NOTE+newline+line, 1)
    return text, stats


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--root', type=Path, default=Path('payload/SWBG-Data'))
    args = cli.parse_args()
    path = args.root/'resources/_common/ai/SWGB Classic AI.per'
    with path.open(encoding='utf-8', newline='') as handle:
        before = handle.read()
    after, stats = rewrite(before, True)
    assert stats['guarded'] and stats['first_carbon'] == 2 and stats['bootstrap'] == 1, stats
    if after != before:
        with path.open('w', encoding='utf-8', newline='') as handle:
            handle.write(after)
    print(path.relative_to(args.root).as_posix(), stats, 'changed' if after != before else 'unchanged')


if __name__ == '__main__':
    main()
