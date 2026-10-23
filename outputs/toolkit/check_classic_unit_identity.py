"""Check the generated metadata adapter against both exported DAT identities."""
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess
from check_classic_air_planner import CMAKE, PREFIX
from classic_unit_ai_factory_oracle import UnitAIFactoryOracle
from classic_attack_eligibility import catalog,generate_catalog

WORK = Path('work/classic-engine/identity-host')
ROOT = WORK.parent
HOST = r'''
int currentUnit=-1,currentOwner=-1,currentCiv=-1,currentCopy=-1;
bool currentExists=false;
bool xsDoesUnitExist(int uid) { return uid==currentUnit && currentExists; }
int xsGetUnitOwner(int uid) { if(uid!=currentUnit)throw std::runtime_error("Wrong queried unit");return currentOwner; }
int xsGetPlayerCivilization(int owner) { if(owner!=currentOwner)throw std::runtime_error("Wrong queried player");return currentCiv; }
int xsGetUnitCopyId(int uid) { if(uid!=currentUnit)throw std::runtime_error("Wrong queried unit");return currentCopy; }
'''
MAIN = r'''
int main() {
    int civ,id,exists;
    while(std::cin>>civ>>id>>exists) {
        std::cout<<classicSourceClass(id,civ)<<' '<<classicSourceType(id,civ)<<' '
                 <<classicSourceFlags(id,civ)<<' '<<classicSourceFog(id,civ)<<' '
                 <<classicSourceLine(id,civ)<<' '<<classicSourceAIType(id,civ)<<' ';
        currentUnit=42;currentOwner=civ==0?0:7;currentCiv=civ;currentCopy=id;currentExists=exists!=0;
        std::cout<<classicSourceUnitClass(42)<<' '<<classicSourceUnitAIType(42)<<' '
                 <<classicSourceUnitAttackKind(42)<<' '<<classicSourceUnitNeutralKind(42)<<' '
                 <<classicSourceUnitHasConversion(42)<<' ';
        classicAttackSoldierMotionAllowed=true;
        classicConvertSetPermissions(true,1.0,1.0,1.0);
        bool known=classicCombatObserveActor(42,3,57,2);
        std::cout<<known<<' '<<classicCombatActorClass<<' '<<classicCombatActorType<<' '
                 <<classicCombatActorKind<<' '<<classicCombatActorState<<' '<<classicCombatActorHeld<<' '
                 <<classicAttackSiegeComputer<<' '<<classicAttackSoldierMotionAllowed<<' '
                 <<classicConvertEnabled<<' '<<classicConvertForceUsers<<' '<<classicConvertMechanical<<'\n';
        if(arrays.size()>2)throw std::runtime_error("Identity adapter leaked arrays");
    }
}
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest_path = ROOT / 'identity-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    xs = ROOT / 'classic_unit_identity.xs'
    export = ROOT / 'unit-identity.tsv'
    for path, key in ((xs, 'xs_sha256'), (export, 'identity_tsv_sha256'),
                      (Path('outputs/toolkit/classic_unit_identity.py'), 'generator_sha256'),
                      (Path('outputs/toolkit/main.cpp'), 'exporter_source_sha256'),
                      (Path('outputs/toolkit/classic_unit_ai_factory.py'), 'factory_model_sha256'),
                      (Path('work/original-ai/current.raw'), 'current_raw_sha256'),
                      (Path('work/ef.raw'), 'source_raw_sha256')):
        assert sha(path) == manifest[key], key
    WORK.mkdir(parents=True, exist_ok=True)
    component_names=('classic_unit_ai_factory.xs','classic_unit_ai_identity.xs','classic_attack_eligibility.xs',
                     'classic_soldier_eligibility.xs','classic_conversion_eligibility.xs','classic_combat_gate.xs','classic_combat_identity.xs')
    catalog_ids,catalog_sha=catalog()
    combined=generate_catalog(catalog_ids,catalog_sha)+xs.read_text()+'\n'+'\n'.join((Path('outputs/toolkit')/n).read_text() for n in component_names)
    combined_path=WORK/'combined.xs';combined_path.write_text(combined)
    lint = subprocess.run(['work/xs-check/xs-check.exe', str(combined_path)], capture_output=True, text=True, check=True)
    clean = re.sub(r'\x1b\[[0-9;]*m', '', lint.stdout + lint.stderr)
    assert 'Error:' not in clean and 'Warning:' not in clean and 'No errors found' in clean, clean
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / 'identity.cpp').write_text(PREFIX + HOST + combined + MAIN)
    (WORK / 'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_identity LANGUAGES CXX)\nadd_executable(identity identity.cpp)\ntarget_compile_features(identity PRIVATE cxx_std_17)\n')
    subprocess.run([CMAKE, '-S', str(WORK), '-B', str(WORK / 'build')], capture_output=True, check=True)
    subprocess.run([CMAKE, '--build', str(WORK / 'build'), '--config', 'Release'], capture_output=True, check=True)
    rows, expected = [], []
    fields = ('source_class', 'source_type', 'source_trait', 'source_fog', 'source_line')
    records = list(csv.DictReader(export.open(), delimiter='\t'))
    oracle=UnitAIFactoryOracle();factory_results={}
    for r in records:
        key=(int(r['source_class']),int(r['source_volley_missile']))
        ai_type=-1
        if int(r['source_type']) in (70,80):
            if key not in factory_results:factory_results[key]=oracle.select(*key)[0]
            ai_type=factory_results[key]
        for exists in (1, 0):
            rows.append(f"{r['civ']} {r['slot']} {exists}")
            entry=oracle.catalog[ai_type] if exists and ai_type!=-1 else dict(attack_kind=-1,neutral_kind=4,can_convert=False)
            gates=f"{entry['attack_kind']} {entry['neutral_kind']} {int(entry['can_convert'])}"
            context=f"1 {r['source_class']} {ai_type} {entry['attack_kind']} 3 57 2 0 0 0 0" if exists else '0 -1 -1 -1 0 -1 2 0 0 0 0'
            expected.append(' '.join(r[f] for f in fields) + ' '+str(ai_type)+' ' + (r['source_class'] if exists else '-1')+' '+str(ai_type if exists else -1)+' '+gates+' '+context)
    holes = set(range(manifest['slots'])) - {int(r['slot']) for r in records}
    for civ in (0, 1, 2):
        for uid in sorted(holes | {-1, manifest['slots'], manifest['slots'] + 100}):
            rows.append(f'{civ} {uid} 1')
            expected.append('-1 -1 -1 -1 -1 -1 -1 -1 -1 4 0 0 -1 -1 -1 0 -1 2 0 0 0 0')
    for civ in (-1, 3, 42):
        for uid in (83, 109, 319, 773):
            rows.append(f'{civ} {uid} 1')
            expected.append('-1 -1 -1 -1 -1 -1 -1 -1 -1 4 0 0 -1 -1 -1 0 -1 2 0 0 0 0')
    run = subprocess.run([str(WORK / 'build/Release/identity.exe')], input='\n'.join(rows) + '\n',
                         text=True, capture_output=True, check=True)
    actual = run.stdout.splitlines()
    assert len(actual) == len(expected), (len(actual), len(expected))
    for index, (got, want) in enumerate(zip(actual, expected)):
        assert got == want, (index, rows[index], got, want)
    result = dict(passed=True, cases=len(expected), records=len(records), xs_checker_warnings=0,
                  source_factory_cases=len(factory_results),
                  identity_manifest_sha256=sha(manifest_path), xs_sha256=sha(xs),
                  tool_sha256=sha(Path(__file__)),
                  component_hashes={n:sha(Path('outputs/toolkit')/n) for n in component_names},
                  attack_catalog_sha256=catalog_sha,
                  factory_oracle_sha256=sha(Path('outputs/toolkit/classic_unit_ai_factory_oracle.py')),
                  catalog_tool_sha256=sha(Path('outputs/toolkit/classic_unit_ai_catalog.py')),
                  installed=False, full_behavior_parity=False,
                  limitations=['C++ host with explicit ownership/copy-ID inputs; not native DE XS execution.',
                               'Metadata only; no target observation, army ownership or unit commands.',
                               'Copy-ID behavior after native upgrades/conversions still requires runtime verification.'])
    (ROOT / 'identity-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'PASS {len(expected)} identity adapter cases covering {len(records)} DAT records; not installed')


if __name__ == '__main__':
    main()
