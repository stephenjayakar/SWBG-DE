"""Generate source combat table layouts, not static live attack/armor values."""
import json
from pathlib import Path
from classic_combat_data import ROOT, read_units
from classic_unit_identity import sha


def profile(row):
    attacks, armor = (tuple(c for c,_ in row[name]) for name in ('attacks','armor'))
    flags = int(len(set(attacks)) != len(attacks))
    flags += 2 * int(len(set(armor)) != len(armor))
    flags += 4 * int(any(c < 0 for c in attacks))
    flags += 8 * int(any(c < 0 for c in armor))
    return (flags,len(attacks),len(armor),*attacks,*armor)


def generate(rows):
    size = max(k[1] for k in rows)+1
    profiles, flat, offsets = {}, [], {}
    for key,row in sorted(rows.items()):
        p = profile(row)
        if p not in profiles:
            profiles[p] = len(flat); flat.extend(p)
        offsets[key] = profiles[p]
    statements = [f'    xsArraySetInt(classicCombatLayouts, {i}, {v});' for i,v in enumerate(flat)]
    statements += [f'    xsArraySetInt(classicCombatLayoutMap, {c*size+uid}, {offset});'
                   for (c,uid),offset in sorted(offsets.items())]
    text = '''// Generated verified source/current combat layouts. No static strengths.
// Unsupported duplicate/negative class layouts remain explicit, not collapsed.
int classicCombatLayouts = -1;
int classicCombatLayoutMap = -1;
'''
    chunks = [statements[i:i+128] for i in range(0,len(statements),128)]
    for i,chunk in enumerate(chunks):
        text += f'void classicCombatLayoutInit{i}() {{\n'+'\n'.join(chunk)+'\n}\n'
    text += f'''void classicCombatLayoutInit() {{
    if (classicCombatLayouts >= 0) return;
    classicCombatLayouts = xsArrayCreateInt({len(flat)}, 0, "source combat layouts");
    classicCombatLayoutMap = xsArrayCreateInt({3*size}, -1, "source combat layout map");
'''
    text += ''.join(f'    classicCombatLayoutInit{i}();\n' for i in range(len(chunks)))+'}\n'
    text += f'''int classicCombatLayout(int copyId = -1, int civilization = 0) {{
    if (copyId < 0 || copyId >= {size} || civilization < 0 || civilization > 2) return(-1);
    classicCombatLayoutInit();
    return(xsArrayGetInt(classicCombatLayoutMap, civilization * {size} + copyId));
}}
'''
    return text,dict(slots=size,profiles=len(profiles),layout_integers=len(flat),
                     map_integers=3*size,records=len(rows),
                     native_unique_layout_records=sum(profile(row)[0] == 0 for row in rows.values()))


def main():
    audit = json.loads((ROOT/'audit.json').read_text())
    for name,value in audit['inputs'].items(): assert sha(Path(name)) == value
    for name,value in audit['exports'].items(): assert sha(ROOT/name) == value
    assert not audit['differences'] and not audit['source_only_records']
    rows = read_units(ROOT/'source-combat.tsv')
    text,statistics = generate(rows)
    out = ROOT/'classic_combat_catalog.xs'; out.write_text(text)
    manifest = dict(statistics=statistics,audit_sha256=sha(ROOT/'audit.json'),xs_sha256=sha(out),
                    generator_sha256=sha(Path(__file__)),installed=False,full_behavior_parity=False,
                    limitations=['Table layouts are invariant under verified source set/add/multiply operations.',
                                 'DE native class membership/getter behavior after upgrades remains unverified.',
                                 'Duplicate or negative classes are flagged for separate handling.'])
    (ROOT/'catalog-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(statistics,indent=2))


if __name__ == '__main__': main()
