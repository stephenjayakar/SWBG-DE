"""Compare the composed XS scorer/ranker with original executable outputs."""
from pathlib import Path
import hashlib
import json
import math
import random
import re
import struct
import subprocess
from check_classic_air_planner import CMAKE, PREFIX
from check_classic_target_ranker import FLOAT_HOST
from check_classic_targets import fixtures
from classic_air_model import f32
from classic_target_model import Target, FLOAT_MAX
from classic_target_oracle import TargetOracle
from classic_engine_oracle import SOURCE_SHA

ROOT = Path('work/classic-engine')
TOOLKIT = Path('outputs/toolkit')
MAIN = r'''
#include <cstring>
#include <cstdint>
int main() {
    int n,regicide,s1,s2,s3;
    while(std::cin>>n>>regicide>>s1>>s2>>s3) {
        classicScoreReset(regicide!=0,s1,s2,s3);
        for(int i=0;i<n;i++) {
            int uid,cls,id,zone,alive,relic,carry,wonder;float ttk,ttbk,distance;
            std::cin>>uid>>cls>>id>>ttk>>ttbk>>distance>>zone>>alive>>relic>>carry>>wonder;
            classicScoreAdd(uid,cls,id,ttk,ttbk,distance,zone!=0,alive!=0,relic!=0,carry!=0,wonder!=0);
        }
        for(int repeat=0;repeat<2;repeat++) {
            classicScoreEvaluate();
            std::cout<<classicTargetCount;
            for(int i=0;i<classicTargetCount;i++) {
                if(xsArrayGetBool(classicTargetUnordered,i)) std::cout<<" nan";
                else { float v=xsArrayGetFloat(classicTargetScores,i);uint32_t b;std::memcpy(&b,&v,4);std::cout<<' '<<b; }
            }
            for(int i=0;i<classicTargetCount;i++) for(int j=0;j<4;j++) {
                if(j==1 && xsArrayGetBool(classicTargetUnordered,i)) std::cout<<" nan";
                else { float v=xsArrayGetFloat(classicScoreComponents,i*4+j);uint32_t b;std::memcpy(&b,&v,4);std::cout<<' '<<b; }
            }
            std::cout<<' '<<classicTargetOrderedCount;
            for(int i=0;i<classicTargetOrderedCount;i++) std::cout<<' '<<xsArrayGetInt(classicTargetOrder,i);
            std::cout<<'\n';
        }
        if(arrays.size()!=11) throw std::runtime_error("Scorer leaked arrays");
    }
}
'''


def scenarios():
    yield from fixtures()
    for delta in (f32(0.00000005), f32(0.000000099), f32(0.0000001), f32(0.00000011)):
        yield [Target(1,ttk=0,ttbk=0,distance=0), Target(2,ttk=delta,ttbk=delta,distance=delta)], {}
    for small in (0.0, f32(1e-20), 1.0, f32(1e10), f32(1e20), f32(1e30)):
        for same_zone in (False, True):
            yield [Target(1,ttk=small,ttbk=small,distance=small,same_zone=same_zone),
                   Target(2,ttk=FLOAT_MAX,ttbk=FLOAT_MAX,distance=FLOAT_MAX,same_zone=same_zone)], {}
    for exponent in range(-66, -22):
        for multiplier in (1.0, 1.25, 1.5000001192092896):
            small = f32(multiplier * 2**exponent)
            yield [Target(1,ttk=small,ttbk=small,distance=small,same_zone=False),
                   Target(2,ttk=1.0,ttbk=1.0,distance=1.0,same_zone=False)], {}
    rng = random.Random(592980)
    for _ in range(32):
        targets = []
        for i in range(8):
            values = [f32(10**rng.uniform(-6,38)), f32(10**rng.uniform(-6,38)), f32(rng.uniform(0,1000))]
            targets.append(Target(i+1,32,4,*values,same_zone=bool(rng.randrange(2))))
        yield targets, {}
    for case in range(250):
        targets = []
        for i in range(rng.choice((2,3,8,16,32,64))):
            cls,uid = rng.choice(((32,4),(18,70),(18,104),(18,276),(6,117),(8,487),(51,4),(46,4)))
            values = [f32(rng.uniform(0,1000)) for _ in range(3)]
            targets.append(Target(i+1,cls,uid,*values,same_zone=bool(rng.randrange(2)),alive=rng.randrange(10)!=0))
        yield targets, {}


def main():
    names = ('classic_target_ranker.xs', 'classic_target_scorer.xs')
    text = '\n'.join((TOOLKIT/n).read_text() for n in names)
    host = ROOT/'score-host'
    host.mkdir(exist_ok=True)
    (host/'combined.xs').write_text(text)
    lint = subprocess.run(['work/xs-check/xs-check.exe', str(host/'combined.xs')], capture_output=True, text=True)
    clean = re.sub(r'\x1b\[[0-9;]*m', '', lint.stdout+lint.stderr)
    assert lint.returncode == 0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):', clean), clean
    text, loops = re.subn(r'for \((\w+) = ([^;]+); < ([^)]+)\)',
                         lambda m: f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)', text)
    assert loops==8
    prefix = PREFIX.replace('std::vector<vector>>;', 'std::vector<vector>, std::vector<float>>;')
    (host/'scorer.cpp').write_text(prefix+FLOAT_HOST+text+MAIN)
    (host/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_scorer LANGUAGES CXX)\nadd_executable(scorer scorer.cpp)\ntarget_compile_features(scorer PRIVATE cxx_std_17)\ntarget_compile_options(scorer PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(host),'-B',str(host/'build')], [CMAKE,'--build',str(host/'build'),'--config','Release']):
        r = subprocess.run(args,capture_output=True,text=True)
        assert r.returncode==0,r.stdout+r.stderr
    inputs, expected = [], []
    oracle = TargetOracle()
    for targets, context in scenarios():
        values = [len(targets), int(context.get('regicide',False)), *[context.get('special'+str(i),-1) for i in (1,2,3)]]
        for t in targets:
            values += [t.uid,t.source_class,t.source_id,t.ttk,t.ttbk,t.distance,int(t.same_zone),int(t.alive),
                       int(t.enemy_relic_countdown),int(t.carries_relic),int(t.enemy_wonder_countdown)]
        inputs.append(' '.join(map(str,values)))
        scores, order = oracle.evaluate(targets, **context)
        out = [len(targets)] + ['nan' if math.isnan(s) else struct.unpack('<I',struct.pack('<f',s))[0] for s in scores]
        out += ['nan' if math.isnan(s) else struct.unpack('<I',struct.pack('<f',s))[0] for parts in oracle.last_components for s in parts]
        out += [len(order)] + [targets[i].uid for i in order]
        expected.extend([' '.join(map(str,out))]*2)
    r = subprocess.run([str(host/'build/Release/scorer.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    actual = r.stdout.splitlines()
    assert len(actual)==len(expected),(len(actual),len(expected))
    failures = [dict(case=i//2, input=inputs[i//2], actual=a, expected=b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b and i%2==0]
    (host/'failures.json').write_text(json.dumps(failures,indent=2)+'\n')
    assert not failures, (len(failures), failures[:2])
    report = dict(passed=True, source_scenarios=len(inputs), host_evaluations=len(expected), source_sha256=SOURCE_SHA,
                  xs_hashes={n:hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest() for n in names},
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), installed=False, full_behavior_parity=False,
                  coverage=['Exact float32 kill/survival/proximity/zone components and final scores.',
                            'Seven-pass ranked unit IDs, including stable ties and explicit unordered scores.',
                            'Victory priorities, absent objects, zero ranges, epsilon boundaries and unreachable targets.',
                            'Fractional metrics, wide combat-time magnitudes and near-cancellation/x87 rounding.',
                            'Repeated evaluation and array reuse.'],
                  limitations=['C++ strict-float host, not the DE XS VM.',
                               'Target admission, combat estimates and countdown state are supplied observations.',
                               'No target-order execution, EF special-type2 patch or source marker-array tail above 128.',
                               'Fixture comparisons are not exhaustive IEEE arithmetic equivalence.'])
    report['tool_hashes'] = {name:hashlib.sha256((TOOLKIT/name).read_bytes()).hexdigest() for name in
                            ('classic_engine_oracle.py','classic_target_oracle.py','classic_target_model.py',
                             'check_classic_targets.py','check_classic_air_planner.py','check_classic_target_ranker.py')}
    (ROOT/'target-scorer-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(inputs),'original scoring/ranking scenarios /',len(expected),'host evaluations; not installed')


if __name__=='__main__': main()
