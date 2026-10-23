"""Execute the pure XS path-decision controller in an explicit C++ host."""
from pathlib import Path
import hashlib
import json
import math
import re
import struct
import subprocess
from check_classic_air_planner import CMAKE, PREFIX
from check_classic_paths import fixtures
from classic_path_model import choose_path

WORK = Path('work/classic-engine/path-host')
TOOLKIT = Path('outputs/toolkit')
MAIN = r'''
struct Target {
    int id,zone,exists,direct,transport,obstruction,retry;
    std::vector<int> blockers,missing,terrains;
};
void readList(std::vector<int>& v) { int n;std::cin>>n;v.resize(n);for(auto& x:v)std::cin>>x; }
bool has(const std::vector<int>& v,int x) { return std::find(v.begin(),v.end(),x)!=v.end(); }
int main() {
    int n;
    while(std::cin>>n) {
        classicPathReset();
        std::vector<Target> targets(n);
        for(auto& t:targets) {
            std::cin>>t.id>>t.zone>>t.exists>>t.direct>>t.transport>>t.obstruction>>t.retry;
            readList(t.blockers);readList(t.missing);readList(t.terrains);
            classicPathAdd(t.id,t.zone,t.exists!=0);
        }
        int nr;std::cin>>nr;
        for(int i=0;i<nr;i++) {
            int kind;float value;std::cin>>kind>>value;
            if(kind==2)value=std::numeric_limits<float>::quiet_NaN();
            classicPathAddRange(value,kind!=0);
        }
        int canTransport,sn241,resume,nt;
        uint32_t start,budget;
        std::cin>>canTransport>>sn241>>resume>>start>>budget>>nt;
        std::vector<uint32_t> ticks(nt);for(auto& t:ticks)std::cin>>t;
        int clockIndex=0;
        classicPathBegin(canTransport,sn241,resume);
        std::vector<std::string> events;
        for(int guard=0;classicPathRequest!=7;guard++) {
            if(guard>10000)throw std::runtime_error("Path controller failed to terminate");
            if(classicPathRequest==0) {
                bool expired=false;
                if(classicPathIndex>classicPathStart && classicPathIndex<classicPathCount) {
                    auto tick=clockIndex<nt?ticks.at(clockIndex++):start;
                    expired=uint32_t(tick-start)>=budget;
                }
                classicPathStep(expired);continue;
            }
            auto& t=targets.at(classicPathIndex);
            int request=classicPathRequest;
            if(request==1) { events.push_back("D"+std::to_string(t.id));classicPathAnswer(t.direct); }
            else if(request==2) { events.push_back("T"+std::to_string(t.id));classicPathAnswer(t.transport); }
            else if(request==3) { events.push_back("O"+std::to_string(t.id));classicPathAnswer(t.obstruction); }
            else if(request==4) {
                int terrain=classicPathTerrain();
                events.push_back("E"+std::to_string(t.id)+":"+std::to_string(terrain));
                classicPathAnswer(has(t.terrains,terrain));
            } else if(request==5) { events.push_back("R"+std::to_string(t.id));classicPathAnswer(t.retry); }
            else if(request==6) {
                for(int uid:t.blockers)classicPathAddBlocker(uid,!has(t.missing,uid));
                classicPathFinishBlockers();
            } else throw std::runtime_error("Unknown path controller request");
        }
        std::cout<<classicPathSelected<<' '<<classicPathSameZone<<' '<<classicPathNeedTransport<<' '
                 <<classicPathResume<<' '<<classicPathAttempt<<' ';
        if(std::isnan(classicPathRadius))std::cout<<"nan";
        else { uint32_t bits;std::memcpy(&bits,&classicPathRadius,4);std::cout<<bits; }
        std::cout<<" B";
        for(int i=0;i<classicPathBlockerCount;i++)std::cout<<' '<<xsArrayGetInt(classicPathBlockers,i);
        std::cout<<" E";for(auto& e:events)std::cout<<' '<<e;std::cout<<'\n';
        if(arrays.size()!=4)throw std::runtime_error("Path controller leaked arrays");
    }
}
'''


def main():
    proof = Path('work/classic-engine/path-validation.json')
    report = json.loads(proof.read_text())
    assert report['passed']
    for name, expected in report['tool_hashes'].items():
        assert hashlib.sha256((TOOLKIT / name).read_bytes()).hexdigest() == expected, name
    xs = TOOLKIT / 'classic_path_selector.xs'
    lint = subprocess.run(['work/xs-check/xs-check.exe', str(xs)], capture_output=True, text=True, check=True)
    clean = re.sub(r'\x1b\[[0-9;]*m', '', lint.stdout + lint.stderr)
    assert 'Error:' not in clean and 'Warning:' not in clean and 'No errors found' in clean, clean
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / 'selector.cpp').write_text('#include <algorithm>\n#include <cstdint>\n#include <cstring>\n#include <limits>\n' + PREFIX + xs.read_text() + MAIN)
    (WORK / 'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_path LANGUAGES CXX)\nadd_executable(selector selector.cpp)\ntarget_compile_features(selector PRIVATE cxx_std_17)\n')
    subprocess.run([CMAKE, '-S', str(WORK), '-B', str(WORK / 'build')], capture_output=True, check=True)
    subprocess.run([CMAKE, '--build', str(WORK / 'build'), '--config', 'Release'], capture_output=True, check=True)
    rows, expected = [], []
    for targets, options in fixtures():
        fields = [len(targets)]
        for t in targets:
            fields.extend((t.uid, t.same_zone, int(t.exists), t.direct, t.transport, t.obstruction, t.plain_retry))
            for values in (t.blockers, t.missing_blockers, t.exception_terrains):
                fields.extend((len(values), *values))
        ranges = options.get('ranges', (4.0,))
        fields.append(len(ranges))
        for value in ranges:
            kind = 0 if value is None else 2 if math.isnan(value) else 1
            fields.extend((kind, value if kind == 1 else 0))
        fields.extend((options.get('can_transport', 0), options.get('sn241', 0), options.get('resume') or 0,
                       options.get('start_time', 0), options.get('time_budget', 100)))
        ticks = options.get('ticks', ())
        fields.extend((len(ticks), *ticks))
        rows.append(' '.join(map(str, fields)))
        result = choose_path(targets, **options)
        radius = 'nan' if math.isnan(result['radius']) else str(struct.unpack('<I', struct.pack('<f', result['radius']))[0])
        values = (result['target'] if result['target'] is not None else -1, result['same_zone'],
                  result['need_transport'], result['resume'] if result['resume'] is not None else -1,
                  result['attempts'][0] if result['attempts'] else -1, radius)
        line = ' '.join(map(str, values)) + ' B' + ''.join(f' {b}' for b in result['blockers']) + ' E'
        for event in result['events']:
            tag = {'direct': 'D', 'transport': 'T', 'obstruction': 'O', 'exception': 'E', 'plain-retry': 'R'}[event[0]]
            line += ' ' + tag + ':'.join(map(str, event[1:]))
        expected.append(line)
    run = subprocess.run([str(WORK / 'build/Release/selector.exe')], input='\n'.join(rows) + '\n',
                         text=True, capture_output=True, check=True)
    actual = run.stdout.splitlines()
    assert len(actual) == len(expected), (len(actual), len(expected))
    for index, (got, want) in enumerate(zip(actual, expected)):
        assert got == want, (index, rows[index], got, want)
    result = dict(passed=True, cases=len(expected), xs_sha256=hashlib.sha256(xs.read_bytes()).hexdigest(),
                  oracle_report_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(), xs_checker_warnings=0,
                  limitations=['C++ host, not native DE XS/PER execution.',
                               'Geometry and time-budget checks are caller-provided; no live pathfinding adapter.',
                               'Single scratch context; caller must preserve player/group state.',
                               'No issued unit orders, previous-priority processing or memory collection.'],
                  installed=False, full_behavior_parity=False)
    Path('work/classic-engine/path-xs-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'PASS {len(expected)} compiled XS path-controller cases; clean syntax; not installed')


if __name__ == '__main__':
    main()
