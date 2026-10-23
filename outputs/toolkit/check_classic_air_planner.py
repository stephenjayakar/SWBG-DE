"""Check XS planner syntax and execute its pure algorithm in a C++ harness.

This is NOT an XS VM or game-runtime test. Only XS loop syntax is translated;
array/vector/math builtins are supplied by a small explicit host. Differential
checks bind it to the independently tested original-executable reference model.
"""
from pathlib import Path
import hashlib
import json
import random
import re
import subprocess
from classic_air_model import Aircraft, attack_groups, scaled_air_percent

CMAKE = 'C:/Program Files/Microsoft Visual Studio/2022/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
WORK = Path('work/classic-engine/planner-host')
TOOLKIT = Path('outputs/toolkit')
PREFIX = r'''
#include <vector>
#include <variant>
#include <string>
#include <iostream>
#include <cmath>
#include <stdexcept>
struct vector { float x, y, z; vector(float a=0,float b=0,float c=0):x(a),y(b),z(c){} };
using Storage = std::variant<std::vector<int>, std::vector<bool>, std::vector<vector>>;
std::vector<Storage> arrays;
int xsArrayCreateInt(int n,int v,const char*) { arrays.emplace_back(std::vector<int>(n,v)); return int(arrays.size()-1); }
int xsArrayCreateBool(int n,bool v,const char*) { arrays.emplace_back(std::vector<bool>(n,v)); return int(arrays.size()-1); }
int xsArrayCreateVector(int n,vector v,const char*) { arrays.emplace_back(std::vector<vector>(n,v)); return int(arrays.size()-1); }
int xsArrayGetInt(int a,int i) { return std::get<std::vector<int>>(arrays.at(a)).at(i); }
bool xsArrayGetBool(int a,int i) { return std::get<std::vector<bool>>(arrays.at(a)).at(i); }
vector xsArrayGetVector(int a,int i) { return std::get<std::vector<vector>>(arrays.at(a)).at(i); }
void xsArraySetInt(int a,int i,int v) { std::get<std::vector<int>>(arrays.at(a)).at(i)=v; }
void xsArraySetBool(int a,int i,bool v) { std::get<std::vector<bool>>(arrays.at(a)).at(i)=v; }
void xsArraySetVector(int a,int i,vector v) { std::get<std::vector<vector>>(arrays.at(a)).at(i)=v; }
float xsVectorGetX(vector v) { return v.x; }
float xsVectorGetY(vector v) { return v.y; }
vector xsVectorSet(float x,float y,float z) { return vector(x,y,z); }
float xsVectorLength(vector v) { return std::sqrt(v.x*v.x+v.y*v.y+v.z*v.z); }
int xsCeilToInt(float v) { return int(std::ceil(v)); }
'''
SUFFIX = r'''
int main() {
    char kind;
    while (std::cin >> kind) {
        if(kind=='S') {
            int value,difficulty,noScale; std::cin>>value>>difficulty>>noScale;
            std::cout << classicAirScalePercent(value,difficulty,noScale!=0) << '\n';
        } else if(kind=='P') {
            int n,percent;float radius;std::cin>>n>>percent>>radius;
            classicAirReset();
            for(int i=0;i<n;i++) {
                int uid,zone;float x,y;std::cin>>uid>>x>>y>>zone;
                classicAirAddCandidate(uid,vector(x,y,0),zone);
            }
            classicAirPlan(n,percent,radius);
            std::cout<<classicAirSelectedCount;
            for(int i=0;i<classicAirSelectedCount;i++)
                std::cout<<' '<<xsArrayGetInt(classicAirSelectedGroups,i)<<':'<<xsArrayGetInt(classicAirSelectedIds,i);
            std::cout<<'\n';
            if(arrays.size()!=6) throw std::runtime_error("Planner leaked arrays");
        } else return 2;
    }
}
'''


def main():
    report = json.loads(Path('work/classic-engine/validation.json').read_text())
    assert report['passed']
    for name, expected in report['tool_hashes'].items():
        assert hashlib.sha256((TOOLKIT/name).read_bytes()).hexdigest() == expected, ('Oracle/model drift', name)
    xs = TOOLKIT/'classic_air_planner.xs'
    lint = subprocess.run(['work/xs-check/xs-check.exe', str(xs)], capture_output=True, text=True, check=True)
    clean = re.sub(r'\x1b\[[0-9;]*m', '', lint.stdout+lint.stderr)
    assert 'Error:' not in clean and 'Warning:' not in clean and 'No errors found' in clean, clean
    text = xs.read_text()
    # The planner is a deliberately pure subset. Translation never changes its
    # decisions or operators. Numeric expressions were checked for XS's rule
    # that the first operand controls arithmetic type (unlike normal C++).
    pattern = r'for \((\w+) = ([^;]+); < ([^)]+)\)'
    text, count = re.subn(pattern, lambda m: f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)', text)
    assert count == 5 and not re.search(r'for\s*\([^;]+;\s*<', text)
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK/'planner.cpp').write_text(PREFIX+'\n'+text+'\n'+SUFFIX)
    (WORK/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_air_planner LANGUAGES CXX)\nadd_executable(planner planner.cpp)\ntarget_compile_features(planner PRIVATE cxx_std_17)\n')
    subprocess.run([CMAKE, '-S', str(WORK), '-B', str(WORK/'build')], check=True, capture_output=True)
    subprocess.run([CMAKE, '--build', str(WORK/'build'), '--config', 'Release'], check=True, capture_output=True)
    inputs, expected = [], []
    for difficulty in range(-1, 5):
        for no_scale in (0, 1):
            for value in (-1, 0, 1, 2, 3, 5, 25, 50, 75, 99, 100):
                inputs.append(f'S {value} {difficulty} {no_scale}')
                expected.append(str(scaled_air_percent(value, max(0,difficulty), no_scaling=bool(no_scale))))
    rng = random.Random(549437)
    layouts = [[], [Aircraft(1,0,0)], [Aircraft(1,0,0),Aircraft(2,20,0)],
               [Aircraft(1,0,0),Aircraft(2,20.001,0)],
               [Aircraft(1,0,0),Aircraft(2,15,0),Aircraft(3,30,0),Aircraft(4,100,0)]]
    for n in (39, 40, 41, 60, 100, 200, 1000):
        layouts.append([Aircraft(i+1,i*30,0) for i in range(n)])
        layouts.append([Aircraft(i+1,i%10,i//10) for i in range(n)])
    for _ in range(100):
        n = rng.choice((2,3,8,20,39,40,41,60,100))
        points = rng.sample([(x,y) for x in range(0,120,3) for y in range(0,120,3)],n)
        layouts.append([Aircraft(i+1,x,y,int(x>=60)) for i,(x,y) in enumerate(points)])
    for candidates in layouts:
        for percentage in (0,1,12,18,25,37,50,56,75,99,100):
            for radius in (0,20,30):
                inputs.append(f'P {len(candidates)} {percentage} {radius} '+
                              ' '.join(f'{a.uid} {a.x} {a.y} {a.zone}' for a in candidates))
                groups = attack_groups(candidates,percentage,radius)
                flat = [f'{g}:{uid}' for g,members in enumerate(groups) for uid in members]
                expected.append(' '.join([str(len(flat))]+flat))
    result = subprocess.run([str(WORK/'build/Release/planner.exe')], input='\n'.join(inputs)+'\n',
                            text=True, capture_output=True, check=True)
    actual = result.stdout.splitlines()
    assert len(actual) == len(expected)
    for i,(a,e) in enumerate(zip(actual,expected)):
        assert a == e, (i, inputs[i][:200], a, e)
    output = dict(passed=True, cases=len(expected), xs_sha256=hashlib.sha256(xs.read_bytes()).hexdigest(),
                  source_model_checks=report['checks'], xs_checker_warnings=0,
                  oracle_report_sha256=hashlib.sha256(Path('work/classic-engine/validation.json').read_bytes()).hexdigest(),
                  test_method='XS syntax check plus same pure algorithm compiled in C++ with explicit builtin adapters',
                  limitations=['Not a DE XS VM test. Builtin floating-point/array semantics still need game verification.',
                               'No unit orders or live target selection are implemented by this planner.'],
                  installed=False, full_behavior_parity=False)
    Path('work/classic-engine/planner-validation.json').write_text(json.dumps(output,indent=2)+'\n')
    print('PASS', len(expected), 'compiled planner cases; XS syntax clean; not installed')


if __name__ == '__main__':
    main()
