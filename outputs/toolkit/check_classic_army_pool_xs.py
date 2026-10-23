"""Host-test XS pool admission with fixtures also checked against source x86.

The C++ host is not DE's XS VM; it supplies arrays and translates loop syntax.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from check_classic_army_pool import fixtures
from classic_army_pool import available, first_group
from check_classic_air_planner import CMAKE

ROOT = Path('work/classic-engine')
TOOLKIT = Path('outputs/toolkit')
PREFIX = r'''
#include <vector>
#include <iostream>
#include <stdexcept>
std::vector<std::vector<int>> arrays;
int xsArrayCreateInt(int n,int v,const char*) { arrays.emplace_back(n,v);return int(arrays.size()-1); }
int xsArrayGetInt(int a,int i) { return arrays.at(a).at(i); }
void xsArraySetInt(int a,int i,int v) { arrays.at(a).at(i)=v; }
int xsArrayGetSize(int a) { return int(arrays.at(a).size()); }
void xsArrayResizeInt(int a,int n) { arrays.at(a).resize(n); }
'''
SUFFIX = r'''
int main() {
    int n,air,difficulty;
    while(std::cin>>n>>air>>difficulty) {
        classicArmyPoolBegin();
        for(int i=0;i<n;i++) {
            int uid,exists,cls,grouped;std::cin>>uid>>exists>>cls>>grouped;
            classicArmyPoolConsider(uid,air!=0,exists!=0,cls,grouped!=0,difficulty);
        }
        std::cout<<classicArmyPoolReported<<' '<<classicArmyPoolSize;
        for(int i=0;i<classicArmyPoolSize;i++) std::cout<<' '<<xsArrayGetInt(classicArmyPoolIds,i);
        std::cout<<'\n';
        if(arrays.size()!=1) throw std::runtime_error("Pool leaked arrays");
    }
}
'''


def main():
    oracle = json.loads((ROOT/'army-pool-validation.json').read_text())
    assert oracle['passed']
    for name, expected in oracle['tool_hashes'].items():
        assert hashlib.sha256((TOOLKIT/name).read_bytes()).hexdigest() == expected, name
    xs = TOOLKIT/'classic_army_pool.xs'
    lint = subprocess.run(['work/xs-check/xs-check.exe', str(xs)], capture_output=True, text=True)
    output = re.sub(r'\x1b\[[0-9;]*m', '', lint.stdout+lint.stderr)
    assert lint.returncode == 0 and 'No errors found' in output and not re.search(r'\b(?:Error|Warning):', output), output
    source, loops = re.subn(r'for \((\w+) = ([^;]+); < ([^)]+)\)',
        lambda m: f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)', xs.read_text())
    assert loops == 1
    host = ROOT/'army-pool-host'
    host.mkdir(exist_ok=True)
    (host/'pool.cpp').write_text(PREFIX+'\n'+source+'\n'+SUFFIX)
    (host/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_army_pool LANGUAGES CXX)\nadd_executable(pool pool.cpp)\ntarget_compile_features(pool PRIVATE cxx_std_17)\n')
    for args in ([CMAKE, '-S', str(host), '-B', str(host/'build')],
                 [CMAKE, '--build', str(host/'build'), '--config', 'Release']):
        subprocess.run(args, capture_output=True, text=True, check=True)
    inputs, expected = [], []
    for pool, classes, groups in fixtures():
        for aircraft in (False, True):
            for difficulty in range(5):
                fields = [len(pool), int(aircraft), difficulty]
                for uid in pool:
                    fields += [uid, int(uid in classes), classes.get(uid, -1), int(first_group(uid, groups) != -1)]
                inputs.append(' '.join(map(str, fields)))
                count, queue = available(pool, classes, groups, aircraft, difficulty)
                expected.append(' '.join(map(str, [count, len(queue)] + queue)))
    result = subprocess.run([str(host/'build/Release/pool.exe')], input='\n'.join(inputs)+'\n',
                            capture_output=True, text=True, check=True)
    actual = result.stdout.splitlines()
    assert len(actual) == len(expected)
    for i, (a, b) in enumerate(zip(actual, expected)):
        assert a == b, (i, a, b)
    report = dict(passed=True, cases=len(expected), xs_sha256=hashlib.sha256(xs.read_bytes()).hexdigest(),
                  source_cases=oracle['cases'], installed=False, full_behavior_parity=False,
                  limitations=['C++ host, not the DE XS VM.',
                               'Caller must provide source-classified pool and original group membership.',
                               'One scratch queue; not a live group lifecycle or command bridge.'])
    (ROOT/'army-pool-xs-validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS', len(expected), 'XS host pool cases; not installed')


if __name__ == '__main__':
    main()
