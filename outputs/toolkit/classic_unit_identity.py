"""Generate a source-identity adapter from the current/source DAT pair.

Read-only export: no dataset mutations. The generated XS is development-only
until the live combat controller consumes it. Never infer SWGB classes from DE
classes: their mapping is many-to-one and aircraft were deliberately remapped.
"""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import subprocess
import zlib
from classic_unit_ai_factory import unit_ai_type

WORK = Path('work/classic-engine')
CURRENT = Path('work/original-ai/current.raw')
SOURCE = Path('work/ef.raw')
PACKAGE = Path('outputs/SWGB-DE-Factions-Draft')
DAT = 'resources/_common/dat/empires2_x2_p1.dat'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packed(row):
    cls, kind, flags, fog = (int(row[key]) for key in ('source_class', 'source_type', 'source_trait', 'source_fog'))
    assert -1 <= cls < 127 and 0 <= kind < 128 and 0 <= flags < 256 and 0 <= fog < 8
    ai_type=unit_ai_type(cls,int(row['source_volley_missile'])) if kind in (70,80) else -1
    assert -1<=ai_type<=14
    return cls + 1 + kind * 128 + flags * 16384 + fog * 4194304 + (ai_type+1)*33554432


def generate(rows):
    by_civ = {c: {int(r['slot']): r for r in rows if int(r['civ']) == c} for c in range(3)}
    assert all(by_civ.values())
    base = by_civ[0]
    assert all(set(by_civ[c]) <= set(base) for c in (1, 2))
    for row in rows:
        assert int(row['source_civ']) == (3 if row['civ'] == '2' else int(row['civ']))
        assert all(int(row[field]) == int(row['slot']) for field in (
            'de_id', 'de_copy', 'de_base', 'source_id', 'source_copy', 'source_base'))
        assert row['de_type'] == row['source_type']
    size = max(base) + 1
    values = {uid: packed(row) for uid, row in base.items()}
    lines = {uid: int(row['source_line']) for uid, row in base.items()}
    default = Counter(values.values()).most_common(1)[0][0]
    statements = []
    for uid in range(size):
        value, line = values.get(uid, -1), lines.get(uid, -1)
        if value != default:
            statements.append(f'    xsArraySetInt(classicIdentityData, {uid}, {value});')
        if line != -1:
            statements.append(f'    xsArraySetInt(classicIdentityLines, {uid}, {line});')
    text = '''// Generated from the verified current Data mod and installed SWGB DAT.
// Source IDs/classes/traits/fog/line/expected UnitAI metadata; no orders or hidden-unit scans.
int classicIdentityData = -1;
int classicIdentityLines = -1;
'''
    chunks = [statements[i:i + 128] for i in range(0, len(statements), 128)]
    for index, chunk in enumerate(chunks):
        text += f'void classicIdentityInit{index}() {{\n' + '\n'.join(chunk) + '\n}\n'
    text += f'''void classicIdentityInit() {{
    if (classicIdentityData >= 0) return;
    classicIdentityData = xsArrayCreateInt({size}, {default}, "classic source identity");
    classicIdentityLines = xsArrayCreateInt({size}, -1, "classic source unit lines");
'''
    text += ''.join(f'    classicIdentityInit{i}();\n' for i in range(len(chunks))) + '}\n'
    for suffix, field, table in (('Packed', None, 'classicIdentityData'), ('Line', 'source_line', 'classicIdentityLines')):
        text += f'''int classicSource{suffix}(int copyId = -1, int civilization = 0) {{
    if (copyId < 0 || copyId >= {size} || civilization < 0 || civilization > 2) return(-1);
    classicIdentityInit();
'''
        for civ in (1, 2):
            changes = []
            for uid, row in by_civ[civ].items():
                value = packed(row) if field is None else int(row[field])
                baseline = values[uid] if field is None else lines[uid]
                if value != baseline:
                    changes.append(f'        if (copyId == {uid}) return({value});')
            if changes:
                text += f'    if (civilization == {civ}) {{\n' + '\n'.join(changes) + '\n    }\n'
        text += f'    return(xsArrayGetInt({table}, copyId));\n}}\n'
    for name, division, modulus, offset in (('Class', 1, 128, -1), ('Type', 128, 128, 0),
                                            ('Flags', 16384, 256, 0), ('Fog', 4194304, 8, 0),
                                            ('AIType', 33554432, 16, -1)):
        expression = f'value / {division} % {modulus}' + (' - 1' if offset else '')
        text += f'''int classicSource{name}(int copyId = -1, int civilization = 0) {{
    int value = classicSourcePacked(copyId, civilization);
    if (value < 0) return(-1);
    return({expression});
}}
'''
    text += '''// Resolve only a supplied existing unit; ownership determines the current
// faction template after conversion. Gameplay verification of DE's copy-ID
// semantics across upgrades/conversion is still required.
int classicSourceUnitClass(int unit = -1) {
    if (xsDoesUnitExist(unit) == false) return(-1);
    int owner = xsGetUnitOwner(unit);
    int civilization = 0;
    if (owner != 0) civilization = xsGetPlayerCivilization(owner);
    return(classicSourceClass(xsGetUnitCopyId(unit), civilization));
}
// Expected original UnitAI type from the source template. This does not query
// or claim the existence of a native DE UnitAI object.
int classicSourceUnitAIType(int unit = -1) {
    if (xsDoesUnitExist(unit) == false) return(-1);
    int owner = xsGetUnitOwner(unit);
    int civilization = 0;
    if (owner != 0) civilization = xsGetPlayerCivilization(owner);
    return(classicSourceAIType(xsGetUnitCopyId(unit), civilization));
}
'''
    return text, size


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(Path('outputs/faction-package-manifest.json').read_text())
    expected = next(x['sha256'] for x in manifest['files'] if x['path'] == DAT)
    assert sha(PACKAGE / DAT) == expected
    assert zlib.decompress((PACKAGE / DAT).read_bytes(), -15) == CURRENT.read_bytes()
    inputs = {'current_raw_sha256': sha(CURRENT), 'source_raw_sha256': sha(SOURCE),
              'packaged_dat_sha256': expected, 'exporter_source_sha256': sha(Path('outputs/toolkit/main.cpp')),
              'factory_model_sha256':sha(Path('outputs/toolkit/classic_unit_ai_factory.py'))}
    export = WORK / 'unit-identity.tsv'
    subprocess.run(['work/dat-build/Release/portdat.exe', 'classic-ai-identity', str(CURRENT), str(export), str(SOURCE)], check=True)
    assert sha(CURRENT) == inputs['current_raw_sha256'] and sha(SOURCE) == inputs['source_raw_sha256']
    rows = list(csv.DictReader(export.open(), delimiter='\t'))
    text, size = generate(rows)
    xs = WORK / 'classic_unit_identity.xs'
    xs.write_text(text)
    inputs.update(rows=len(rows), slots=size, identity_tsv_sha256=sha(export), xs_sha256=sha(xs),
                  generator_sha256=sha(Path(__file__)), installed=False,
                  limitations=['Static DAT identity only; native copy-ID behavior across upgrades/conversion remains unverified.',
                               'Unsupported civilizations return unknown; current mod contains Gaia/Empire/Rebels only.',
                               'Definitions absent from a faction use shared Gaia metadata and do not imply trainability.'])
    (WORK / 'identity-manifest.json').write_text(json.dumps(inputs, indent=2) + '\n')
    print(f'Generated source identity adapter for {len(rows)} current unit records; not installed')


if __name__ == '__main__':
    main()
