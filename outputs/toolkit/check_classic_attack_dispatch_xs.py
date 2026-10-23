"""Exercise the composed XS attack controller against source-verified cases."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from check_classic_attack_dispatch import fixtures
from classic_attack_dispatch import dispatch
from classic_group_state import GroupState
from check_classic_air_planner import CMAKE, PREFIX

ROOT = Path('work/classic-engine')
TOOLKIT = Path('outputs/toolkit')
EXTRA = r'''
#include <map>
int xsArrayGetSize(int a) { return int(std::visit([](auto &v){return v.size();},arrays.at(a))); }
void xsArrayResizeInt(int a,int n) { std::get<std::vector<int>>(arrays.at(a)).resize(n); }
'''
SUFFIX = r'''
struct Object { int cls,zone;float x,y; };
int main() {
    int n,ng,nb,na,gp,bp,ap,difficulty,radius,now,failAfter,player;
    while(std::cin>>n>>ng>>nb>>na>>gp>>bp>>ap>>difficulty>>radius>>now>>failAfter>>player) {
        std::map<int,Object> objects;
        for(int i=0;i<n;i++) { int uid;Object o;std::cin>>uid>>o.cls>>o.x>>o.y>>o.zone;objects[uid]=o; }
        std::vector<int> ground(ng),boats(nb),air(na);
        for(int &uid:ground) std::cin>>uid;
        for(int &uid:boats) std::cin>>uid;
        for(int &uid:air) std::cin>>uid;
        classicGroupsReset(7);
        if(ng) {
            int h=classicGroupCreate(player);classicGroupSet(h,4,101);
            classicGroupAdd(h,ground[0],123);
        }
        for(int repeat=0;repeat<2;repeat++) {
        classicDispatchBegin();
        for(int category=0;category<3;category++) {
            classicDispatchPoolBegin();
            for(int uid:category==0?ground:category==1?boats:air) {
                auto it=objects.find(uid);bool exists=it!=objects.end();
                Object o=exists?it->second:Object{-1,0,0,0};
                if(category==1) classicDispatchBoatCandidate(player,uid,exists,vector(o.x,o.y,0),o.zone);
                else classicDispatchCandidate(player,uid,category==2,exists,o.cls,difficulty,vector(o.x,o.y,0),o.zone);
            }
            classicDispatchPoolFinish(player,category==0?100:category==1?102:108,category==0?gp:category==1?bp:ap,difficulty,radius,now,failAfter);
        }
        std::cout<<classicDispatchStopCount;
        for(int i=0;i<classicDispatchStopCount;i++) std::cout<<' '<<xsArrayGetInt(classicDispatchStops,i);
        std::cout<<' '<<xsArrayGetInt(classicGroupNextIds,player)<<' '<<xsArrayGetInt(classicGroupCounts,player);
        for(int h=xsArrayGetInt(classicGroupHeads,player);h;h=classicGroupGet(h,1)) {
            if(classicGroupGet(h,0)!=player) throw std::runtime_error("Wrong owner");
            for(int field:{3,4,6,7,8,9,10,11,12,13,5}) std::cout<<' '<<classicGroupGet(h,field);
            for(int i=0;i<classicGroupGet(h,5);i++) std::cout<<' '<<classicGroupGet(h,14+i);
        }
        std::cout<<'\n';
        }
        if(arrays.size()!=13) throw std::runtime_error("Controller array leak");
    }
}
'''


def main():
    oracle = json.loads((ROOT/'dispatch-validation.json').read_text())
    assert oracle['passed']
    for name, digest in oracle['tool_hashes'].items():
        assert hashlib.sha256((TOOLKIT/name).read_bytes()).hexdigest() == digest, name
    files = ('classic_group_state.xs', 'classic_army_pool.xs', 'classic_air_planner.xs', 'classic_attack_dispatch.xs')
    text = '\n'.join((TOOLKIT/name).read_text() for name in files)
    host = ROOT/'dispatch-host'
    host.mkdir(exist_ok=True)
    combined = host/'combined.xs'
    combined.write_text(text)
    lint = subprocess.run(['work/xs-check/xs-check.exe', str(combined)], capture_output=True, text=True)
    output = re.sub(r'\x1b\[[0-9;]*m', '', lint.stdout+lint.stderr)
    assert lint.returncode == 0 and 'No errors found' in output and not re.search(r'\b(?:Error|Warning):', output), output
    special = 'for (i = 0; < xsArrayGetSize(classicGroups))'
    assert text.count(special) == 1
    text = text.replace(special, 'for (int i = 0; i < xsArrayGetSize(classicGroups); i++)')
    text, loops = re.subn(r'for \((\w+) = ([^;]+); < ([^)]+)\)',
        lambda m: f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)', text)
    assert loops == 11
    (host/'dispatch.cpp').write_text(PREFIX+EXTRA+'\n'+text+'\n'+SUFFIX)
    (host/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_dispatch LANGUAGES CXX)\nadd_executable(dispatch dispatch.cpp)\ntarget_compile_features(dispatch PRIVATE cxx_std_17)\n')
    for args in ([CMAKE, '-S', str(host), '-B', str(host/'build')],
                 [CMAKE, '--build', str(host/'build'), '--config', 'Release']):
        result = subprocess.run(args, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout+result.stderr
    inputs, expected = [], []
    for index, fixture in enumerate(fixtures()):
        f = fixture
        values = [len(f['classes']), len(f['ground']), len(f.get('boats', ())), len(f['air']),
                  f['ground_percent'], f.get('boat_percent', 0), f['air_percent'],
                  f['difficulty'], f['radius'], f['now'], -1 if f['fail_after'] is None else f['fail_after'], index % 8 + 1]
        for uid, cls in f['classes'].items():
            values += [uid, cls, *f['positions'][uid]]
        values += f['ground'] + list(f.get('boats', ())) + f['air']
        inputs.append(' '.join(map(str, values)))
        model = GroupState(7)
        if f['ground']:
            handle = model.create()
            model.groups[handle].kind = 101
            model.add(handle, f['ground'][0], 123)
        for repeat in range(2):
            stops = dispatch(model, **f)
            output = [len(stops)] + stops + [model.next_id, model.count]
            for group in model.groups.values():
                output += [group.id, group.kind, group.desired, group.action, group.target,
                           group.target_type, group.in_use, group.flags, group.retreat,
                           group.last_added, len(group.members)] + group.members
            expected.append(' '.join(map(str, output)))
    run = subprocess.run([str(host/'build/Release/dispatch.exe')], input='\n'.join(inputs)+'\n',
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    actual = run.stdout.splitlines()
    assert len(actual) == len(expected)
    for i, (a, b) in enumerate(zip(actual, expected)):
        assert a == b, (i, a, b)
    report = dict(passed=True, cases=len(inputs), dispatch_calls=len(expected), source_cases=oracle['cases'],
                  xs_hashes={n: hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest() for n in files},
                  installed=False, full_behavior_parity=False,
                  limitations=['C++ host, not native DE XS execution.',
                               'Source-classified pools and geometry observations supplied by caller.',
                               'Stop queue is not connected to a PER command bridge; targeting is pending.'])
    (ROOT/'dispatch-xs-validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS', len(inputs), 'composed XS scenarios /', len(expected), 'dispatch calls; not installed')


if __name__ == '__main__':
    main()
