"""DE unit-line hygiene for the Classic AI (see CHANGELOG.md, 2026-09-29 entries).

DE treats every unitlines.json entry as an upgrade chain: a unit ID that belongs to a line is resolved
to that line's current member by can-train/train/up-train. The dataset carried
  * DE's 117 native lines, whose native IDs name unrelated SWGB units here (e.g. mameluke-line
    [282, 556] = Rebel Trooper Recruit -> Rebel scout bike; skirmisher-line contains the Airspeeder), and
  * three counting-only groups: -313 worker (83 at index 2), -353 ground soldiers (2079 IDs incl. the
    medic, Jedi, grenade trooper...) and -352 warboats.
As a result (can-train 83) was always false and the Classic AI never trained a worker. The counting
groups are replaced by native facts: villager-class (904), soldier-count and warboat-count.
"""
import json, re
from reserved_unit_ids import de_unit_id

COUNT_GROUPS = {'swgb-unit-worker-count-line', 'swgb-source-ground-soldier-line', 'swgb-source-warboat-line'}
VILLAGER_CLASS = 904
# (unit-type-count 904 ...) returned 0 in DE build 185872 for this dataset, which let the Hard
# "no workers, no army" rule resign the AI. Worker counts come from the XS observer (goal 120,
# xsGetPlayerUnitIds(player, 904)) instead; see classic_ai_observer.py.
WORKER_GOAL = 120
OPS = {'>': 'c:>', '<': 'c:<', '>=': 'c:>=', '<=': 'c:<=', '==': 'c:==', '!=': 'c:!='}


def clean_unitlines(data):
    """Keep only SWGB lines that are real unit/building families; drop native lines and count groups."""
    def names(l):
        ident = l.get('Identifier', '')
        return ident if isinstance(ident, list) else [ident]
    kept = [l for l in data['UnitLines']
            if all(n.startswith('swgb-') for n in names(l)) and not (set(names(l)) & COUNT_GROUPS)]
    dropped = len(data['UnitLines']) - len(kept)
    out = dict(data)
    out['UnitLines'] = kept
    return out, dropped


def rewrite_per(text):
    """Replace counting-group facts with native DE facts. Returns (text, counts)."""
    counts = {}
    text, counts['worker_defconst'] = re.subn(r'\(defconst ([ce][er])-unit-worker-count-line -?\d+\)',
                                              lambda m: f'(defconst {m[1]}-unit-worker-count-line {VILLAGER_CLASS})', text)
    text, counts['worker_facts'] = re.subn(
        r'\(unit-type-count(?:-total)? [ce][er]-unit-worker-count-line (>=|<=|==|!=|>|<) ([^\s()]+)\)',
        lambda m: f'(up-compare-goal {WORKER_GOAL} {OPS[m[1]]} {m[2]})', text)
    assert not re.search(r'\(unit-type-count\S* [ce][er]-unit-worker-count-line', text)
    text, counts['soldier'] = re.subn(r'\(unit-type-count(?:-total)? [ce][er]-source-ground-soldier-line ', '(soldier-count ', text)
    text, counts['warboat'] = re.subn(r'\(unit-type-count(?:-total)? [ce][er]-source-warboat-line ', '(warboat-count ', text)
    assert not re.search(r'\((?:unit-type-count|train|can-train)\S* [ce][er]-source-(?:ground-soldier|warboat)-line', text)
    return text, counts


# The source line groups list every SWGB civ's variant (e.g. trooper line: TRECC, TRECN, TRECR, ...).
# DE resolved such a line to IDChain[0], a unit neither faction has: in-game both Classic AIs issued
# train commands only for 1552 (Confederacy trooper), 183 (Gungan padawan), 781 (Wookiee fighter),
# 874 (Wookiee boat) and 5034 (Gungan transport mech), and never built an army. Each faction now gets
# its own chain: the group members that faction can enable or upgrade into, kept in source group
# order (recruit, trooper, heavy, repeater...). Rebels get new LineIDs; Empire keeps the old ones.
FACTION_CIVS = {'ce-': '1', 'cr-': '2'}
SPLIT_SKIP = ('swgb-bldg-', 'swgb-gaia-')


def faction_reach(dat_dir):
    """Units each faction starts with or can enable/upgrade into, from a dat TSV dump."""
    import csv, collections
    rows = lambda name: list(csv.DictReader(open(f'{dat_dir}/{name}.tsv'), delimiter='\t'))
    effects = collections.defaultdict(list)
    for r in rows('effects'):
        effects[r['effect']].append(r)
    civs = {r['id']: r for r in rows('civs')}
    units = rows('units')
    reach = {}
    for civ in FACTION_CIVS.values():
        tree = effects[civs[civ]['techtree']]
        disabled_techs = {e['d'] for e in tree if e['type'] == '102'}
        disabled_units = {e['a'] for e in tree if e['type'] == '2' and e['b'] == '0'}
        found = {r['id'] for r in units if r['civ'] == civ and r['enabled'] == '1'}
        upgrades = collections.defaultdict(set)
        for t in rows('techs'):
            if t['civ'] not in ('-1', civ) or t['id'] in disabled_techs:
                continue
            for e in effects[t['effect']]:
                if e['type'] == '2' and e['b'] == '1':
                    found.add(e['a'])
                elif e['type'] == '3':
                    upgrades[e['a']].add(e['b'])
        found -= disabled_units
        todo = list(found)
        while todo:
            for b in upgrades[todo.pop()]:
                if b not in found:
                    found.add(b)
                    todo.append(b)
        # Compare in DE IDs: port_classic_ai writes IDChain with reserved_unit_ids.de_unit_id, and a
        # dump of an already remapped DAT is left unchanged (the mapping is idempotent).
        reach[civ] = {de_unit_id(int(u)) for u in found}
    return reach


def split_faction_lines(data, per, reach):
    """Give each faction its own unit-line chains. Returns (data, per, report)."""
    lines = data['UnitLines']
    used = {l['LineID'] for l in lines}
    free = iter(i for i in range(-399, -199) if i not in used)
    rebel_ids, report, added = {}, [], []
    for l in lines:
        ident = l['Identifier'] if isinstance(l['Identifier'], str) else l['Identifier'][0]
        if l.get('Building') or ident.startswith(SPLIT_SKIP):
            continue
        empire = [u for u in l['IDChain'] if u in reach['1']]
        rebel = [u for u in l['IDChain'] if u in reach['2']]
        if not empire and not rebel:
            continue
        if empire and rebel and empire != rebel:
            new = dict(l, Name=l['Name'] + ' (Rebels)', Identifier=ident.replace('swgb-', 'swgb-rebel-', 1),
                       LineID=next(free), IDChain=rebel)
            added.append(new)
            rebel_ids[l['LineID']] = new['LineID']
            l['IDChain'] = empire
        else:
            l['IDChain'] = empire or rebel
        report.append((l['LineID'], ident, l['IDChain'], rebel_ids.get(l['LineID']), rebel if l['LineID'] in rebel_ids else None))
    out = dict(data)
    out['UnitLines'] = lines + added
    per, n = re.subn(r'\(defconst (cr-\S+) (-\d+)\)',
                     lambda m: f'(defconst {m[1]} {rebel_ids.get(int(m[2]), int(m[2]))})', per)
    # The shared air dispatch rule searches by line; add the Rebel line after each split Empire line.
    per = re.sub(r' \(up-find-local c: (-\d+) c: 240\)',
                 lambda m: m[0] + (f'\n (up-find-local c: {rebel_ids[int(m[1])]} c: 240)' if int(m[1]) in rebel_ids else ''), per)
    return out, per, report
