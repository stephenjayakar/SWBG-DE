"""Check source/XS mutations on actual source DAT upgrade inputs and edge cases."""
from pathlib import Path
import csv
import json
import re
import subprocess
from classic_combat_attribute import modify
from classic_combat_attribute_oracle import CombatAttributeOracle
from classic_combat_data import ROOT as DATA, read_units
from classic_unit_identity import sha
from classic_engine_oracle import SOURCE_SHA
from check_classic_air_planner import CMAKE, PREFIX
from check_classic_target_ranker import FLOAT_HOST
from check_classic_attack_dispatch_xs import EXTRA

ROOT = Path('work/classic-engine/combat-attribute-host')
TOOLKIT = Path('outputs/toolkit')
MAIN = r'''
int main() {
    int classes=xsArrayCreateInt(1024,-1,"classes");
    int values=xsArrayCreateInt(1024,0,"values");
    int mode,encoded,count;
    while(std::cin>>mode>>encoded>>count) {
        for(int i=0;i<count;i++) {int c,v;std::cin>>c>>v;xsArraySetInt(classes,i,c);xsArraySetInt(values,i,v);}
        if(!classicAttributeModify(classes,values,count,mode,encoded))throw std::runtime_error("Rejected valid input");
        for(int i=0;i<count;i++)std::cout<<xsArrayGetInt(classes,i)<<':'<<xsArrayGetInt(values,i)<<',';
        std::cout<<'\n';
        if(arrays.size()!=2)throw std::runtime_error("Leaked arrays");
    }
    if(classicAttributeModify(-1,values,1,0,0) || classicAttributeModify(classes,values,1025,0,0)
       || classicAttributeModify(classes,values,1,3,0) || classicAttributeModify(classes,values,-1,0,0))
        throw std::runtime_error("Invalid bounds accepted");
}
'''


def cases():
    result = set()
    units = read_units(DATA / 'source-combat.tsv')
    commands = list(csv.DictReader((DATA / 'source-effects.tsv').open(), delimiter='\t'))
    applications = 0
    for command in commands:
        mode, attr = int(command['type']), int(command['c'])
        if mode not in (0,4,5) or attr not in (8,9): continue
        amount = float(command['d'])
        assert amount.is_integer() and abs(amount) <= 65535
        for (_, uid), row in units.items():
            target = int(command['a'])
            if not (uid == target if target >= 0 else int(row['class']) == int(command['b'])): continue
            entries = tuple(row['armor' if attr == 8 else 'attacks'])
            result.add((entries, mode, int(amount), attr)); applications += 1
    actual_cases = len(result)
    for entries in ((), ((3,10),), ((3,10),(3,20),(0,7)), ((0,-32768),(1,32767),(3,-51)),
                    ((-1,123),(255,100),(4,-50)), ((100,7),)*256):
        for mode in (0,4,5):
            for selector in (0,1,2,3,4,100,255):
                for amount in (0,1,50,99,100,101,200,255):
                    for attr in (8,9):
                        result.add((entries,mode,selector*256+amount,attr))
        for encoded in (-1,-257,-65536,-65537,65536,65537):
            for mode in (0,4,5): result.add((entries,mode,encoded,9))
    # Percent boundaries where float32 intermediate rounding changes truncation.
    for before in (-32768,-30001,-151,-101,-51,-50,-1,0,1,50,51,101,151,30001,32767):
        for amount in range(256): result.add((((3,before),),5,3*256+amount,9))
    return sorted(result), applications, actual_cases


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    names = ('classic_target_ranker.xs','classic_target_scorer.xs','classic_combat_attribute.xs')
    text = '\n'.join((TOOLKIT/n).read_text() for n in names)
    (ROOT/'combined.xs').write_text(text)
    lint = subprocess.run(['work/xs-check/xs-check.exe',str(ROOT/'combined.xs')], capture_output=True,text=True)
    clean = re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode == 0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean), clean
    text = re.sub(r'for \((\w+) = ([^;]+); < ([^)]+)\)',
                  lambda m:f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)',text)
    prefix = PREFIX.replace('std::vector<vector>>;','std::vector<vector>, std::vector<float>>;')
    (ROOT/'attribute.cpp').write_text(prefix+FLOAT_HOST+EXTRA+text+MAIN)
    (ROOT/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(attribute LANGUAGES CXX)\nadd_executable(attribute attribute.cpp)\ntarget_compile_features(attribute PRIVATE cxx_std_17)\ntarget_compile_options(attribute PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(ROOT),'-B',str(ROOT/'build')],[CMAKE,'--build',str(ROOT/'build'),'--config','Release']):
        run = subprocess.run(args,capture_output=True,text=True)
        assert run.returncode == 0,run.stdout+run.stderr
    fixtures, applications, actual_cases = cases()
    oracle = CombatAttributeOracle()
    inputs, expected = [], []
    for entries,mode,encoded,attr in fixtures:
        try:
            result = oracle.modify(entries,mode,encoded,attr)
        except Exception as exc:
            from unicorn.x86_const import UC_X86_REG_EIP
            raise AssertionError((entries,mode,encoded,attr,hex(oracle.cpu.reg_read(UC_X86_REG_EIP)))) from exc
        assert result == modify(entries,mode,encoded),(entries,mode,encoded,attr,result,modify(entries,mode,encoded))
        inputs.append(' '.join(map(str,[mode,encoded,len(entries)]+[v for p in entries for v in p])))
        expected.append(''.join(f'{c}:{v},' for c,v in result))
    run = subprocess.run([str(ROOT/'build/Release/attribute.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert run.returncode == 0,run.stderr
    lines = run.stdout.splitlines()
    assert len(lines) == len(expected),(len(lines),len(expected))
    for i,(actual,want) in enumerate(zip(lines,expected)):
        assert actual == want,(fixtures[i],actual,want)
    report = dict(passed=True,cases=len(fixtures),source_dat_applications=applications,
                  unique_dat_cases=actual_cases,source_sha256=SOURCE_SHA,
                  hashes={n:sha(TOOLKIT/n) for n in (*names,'classic_combat_attribute.py','classic_combat_attribute_oracle.py','check_classic_combat_attribute.py')},
                  data_hashes={n:sha(DATA/n) for n in ('source-combat.tsv','source-effects.tsv')},
                  installed=False,full_behavior_parity=False,
                  limitations=['Isolated source methods and XS C++ host, not native DE gameplay.',
                               'Does not model effect activation, player selectors or research timing.',
                               'Finite integer encodings; source floating-to-integer edge cases outside DAT inputs are not claimed.'])
    (ROOT.parent/'combat-attribute-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(fixtures)} source/XS table mutations; {applications} DAT applications / {actual_cases} unique cases')


if __name__ == '__main__': main()
