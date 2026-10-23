"""Validate the pure XS target ranker, without claiming DE VM/runtime parity."""
from pathlib import Path
import hashlib
import json
import math
import random
import re
import subprocess
from classic_target_model import Target, target_order
from check_classic_air_planner import CMAKE, PREFIX

WORK = Path('work/classic-engine/target-host')
TOOLKIT = Path('outputs/toolkit')
FLOAT_HOST = r'''
int xsArrayCreateFloat(int n,float v,const char*) { arrays.emplace_back(std::vector<float>(n,v)); return int(arrays.size()-1); }
float xsArrayGetFloat(int a,int i) { return std::get<std::vector<float>>(arrays.at(a)).at(i); }
void xsArraySetFloat(int a,int i,float v) { std::get<std::vector<float>>(arrays.at(a)).at(i)=v; }
'''
MAIN = r'''
int main() {
    int n;
    while(std::cin>>n) {
        classicTargetReset();
        for(int i=0;i<n;i++) {
            int uid,unordered,cls,id,zone;float score;
            std::cin>>uid>>score>>unordered>>cls>>id>>zone;
            classicTargetAdd(uid,score,unordered!=0,cls,id,zone!=0);
        }
        for(int repeat=0;repeat<2;repeat++) {
            classicTargetRank();
            std::cout<<classicTargetOrderedCount;
            for(int i=0;i<classicTargetOrderedCount;i++) std::cout<<' '<<xsArrayGetInt(classicTargetOrder,i);
            std::cout<<'\n';
        }
        if(arrays.size()!=8) throw std::runtime_error("Ranker leaked arrays");
    }
}
'''


def main():
    report_path = Path('work/classic-engine/target-validation.json')
    report = json.loads(report_path.read_text())
    assert report['passed']
    for name, expected in report['tool_hashes'].items():
        assert hashlib.sha256((TOOLKIT/name).read_bytes()).hexdigest() == expected, name
    xs = TOOLKIT/'classic_target_ranker.xs'
    lint = subprocess.run(['work/xs-check/xs-check.exe', str(xs)], capture_output=True, text=True, check=True)
    clean = re.sub(r'\x1b\[[0-9;]*m', '', lint.stdout+lint.stderr)
    assert 'Error:' not in clean and 'Warning:' not in clean and 'No errors found' in clean, clean
    code, count = re.subn(r'for \((\w+) = ([^;]+); < ([^)]+)\)',
                         lambda m: f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)', xs.read_text())
    assert count == 4
    prefix = PREFIX.replace('std::vector<vector>>;', 'std::vector<vector>, std::vector<float>>;')
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK/'ranker.cpp').write_text(prefix+FLOAT_HOST+code+MAIN)
    (WORK/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_target_ranker LANGUAGES CXX)\nadd_executable(ranker ranker.cpp)\ntarget_compile_features(ranker PRIVATE cxx_std_17)\n')
    subprocess.run([CMAKE, '-S', str(WORK), '-B', str(WORK/'build')], capture_output=True, check=True)
    subprocess.run([CMAKE, '--build', str(WORK/'build'), '--config', 'Release'], capture_output=True, check=True)
    rng = random.Random(59230)
    layouts = [([], [])]
    for n in (1,2,7,8,39,40,127,128,129,512,1024,1025):
        for kind in range(5):
            targets, scores = [], []
            for i in range(n):
                targets.append(Target(1000+i, source_class=rng.choice((6,7,8,18,32,43,51)),
                                      source_id=rng.choice((4,50,68,70,104,209,276,323,562,584)),
                                      same_zone=bool(rng.randrange(2))))
                scores.append((0, 100, math.nan, rng.choice((0,25,50,75,99,100,1000)),
                               rng.choice((math.nan,-50,0,99.9,100)))[kind])
            layouts.append((targets,scores))
    for _ in range(200):
        n = rng.randrange(1,60)
        targets = [Target(i,source_class=rng.randrange(70),source_id=rng.randrange(600),
                          same_zone=bool(rng.randrange(2))) for i in range(n)]
        scores = [rng.choice((math.nan,0,25,50,75,99,100,1000)) for _ in targets]
        layouts.append((targets,scores))
    inputs, expected = [], []
    for targets,scores in layouts:
        inputs.append(str(len(targets))+' '+ ' '.join(
            f'{t.uid} {0 if math.isnan(s) else s} {int(math.isnan(s))} {t.source_class} {t.source_id} {int(t.same_zone)}'
            for t,s in zip(targets,scores)))
        admitted = targets[:1024]
        order = target_order(admitted,scores[:1024])
        line = ' '.join([str(len(order))]+[str(admitted[i].uid) for i in order])
        expected.extend((line,line))
    result = subprocess.run([str(WORK/'build/Release/ranker.exe')], input='\n'.join(inputs)+'\n',
                            text=True,capture_output=True,check=True)
    actual = result.stdout.splitlines()
    assert len(actual) == len(expected)
    for index,(a,e) in enumerate(zip(actual,expected)):
        assert a == e, (index,a,e)
    output = dict(passed=True,cases=len(expected),xs_sha256=hashlib.sha256(xs.read_bytes()).hexdigest(),
                  source_model_checks=report['checks'], xs_checker_warnings=0,
                  oracle_report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
                  limitations=['C++ host is not the DE XS VM.',
                               'Source-bytecode comparison covers up to 128 targets; larger arrays check only the reference algorithm.',
                               'Caller must supply source-compatible target admission, scores and memory.'],
                  installed=False,full_behavior_parity=False)
    Path('work/classic-engine/target-ranker-validation.json').write_text(json.dumps(output,indent=2)+'\n')
    print('PASS',len(expected),'compiled ranker cases; XS syntax clean; not installed')


if __name__ == '__main__':
    main()
