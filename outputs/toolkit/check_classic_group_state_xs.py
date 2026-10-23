"""Replay source-verified lifecycle sequences through the XS container host.

Sequences are interleaved across eight players and compared after every mutation.
This checks XS algorithms through a C++ host, not DE VM execution or networking.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from classic_group_state import GroupState
from check_classic_army_pool_xs import PREFIX
from check_classic_air_planner import CMAKE

ROOT = Path('work/classic-engine')
TOOLKIT = Path('outputs/toolkit')
SUFFIX = r'''
#include <map>
int main() {
    std::map<int,int> aliases[9];
    char op;
    while(std::cin>>op) {
        int result=0,p=0,a=0,b=0,c=0,d=0;
        if(op=='Z') { classicGroupsReset();for(auto &m:aliases)m.clear(); }
        else {
            std::cin>>p;
            if(op=='I') { std::cin>>a;xsArraySetInt(classicGroupNextIds,p,a); }
            if(op=='C') {
                std::cin>>a>>b>>c;int h=classicGroupCreate(p,a,b!=0);
                aliases[p][c]=h;result=h!=0;
            }
            if(op=='A') { std::cin>>a>>b>>c;result=classicGroupAdd(aliases[p].at(a),b,c); }
            if(op=='R') { std::cin>>a>>b;result=classicGroupRemove(aliases[p].at(a),b); }
            if(op=='D') { std::cin>>a;result=classicGroupDelete(p,a); }
            if(op=='K') { std::cin>>a;result=classicGroupDeleteKind(p,a); }
            if(op=='T') { std::cin>>a>>b;classicGroupSet(aliases[p].at(a),4,b); }
            if(op=='F') {
                std::cin>>a;int found=classicGroupContaining(p,a),ordinal=1;
                for(int h=xsArrayGetInt(classicGroupHeads,p);h;h=classicGroupGet(h,1),ordinal++)
                    if(h==found) { result=ordinal;break; }
            }
        }
        std::cout<<result;
        for(int owner=1;owner<=8;owner++) {
            int n=0,previous=0;
            for(int h=xsArrayGetInt(classicGroupHeads,owner);h;h=classicGroupGet(h,1)) {
                if(++n>1000 || classicGroupGet(h,0)!=owner || classicGroupGet(h,2)!=previous)
                    throw std::runtime_error("Bad group links/ownership");
                previous=h;
            }
            if(previous!=xsArrayGetInt(classicGroupTails,owner)) throw std::runtime_error("Bad tail");
            std::cout<<' '<<xsArrayGetInt(classicGroupNextIds,owner)<<' '<<xsArrayGetInt(classicGroupCounts,owner)<<' '<<n;
            for(int h=xsArrayGetInt(classicGroupHeads,owner);h;h=classicGroupGet(h,1)) {
                for(int field:{3,4,6,7,8,9,10,11,12,13,5}) std::cout<<' '<<classicGroupGet(h,field);
                for(int i=0;i<classicGroupGet(h,5);i++) std::cout<<' '<<classicGroupGet(h,14+i);
            }
        }
        std::cout<<'\n';
        if(arrays.size()!=5) throw std::runtime_error("Group array leak");
    }
    // The fixtures repeatedly delete all groups. Capacity should reflect peak
    // simultaneous groups, not the cumulative number of creations.
    if(xsArrayGetSize(classicGroups)>54*128) throw std::runtime_error("Deleted slots were not reused");
}
'''


def main():
    source = json.loads((ROOT/'group-state-validation.json').read_text())
    assert source['passed']
    for name, digest in source['tool_hashes'].items():
        assert hashlib.sha256((TOOLKIT/name).read_bytes()).hexdigest() == digest, name
    xs = TOOLKIT/'classic_group_state.xs'
    lint = subprocess.run(['work/xs-check/xs-check.exe', str(xs)], capture_output=True, text=True)
    output = re.sub(r'\x1b\[[0-9;]*m', '', lint.stdout+lint.stderr)
    assert lint.returncode == 0 and 'No errors found' in output and not re.search(r'\b(?:Error|Warning):', output), output
    # The first bound contains a function call, which the generic regex cannot
    # parse. Translate that one literal loop explicitly before the generic pass.
    text = xs.read_text()
    special = 'for (i = 0; < xsArrayGetSize(classicGroups))'
    assert text.count(special) == 1
    text = text.replace(special, 'for (int i = 0; i < xsArrayGetSize(classicGroups); i++)')
    text, loops = re.subn(r'for \((\w+) = ([^;]+); < ([^)]+)\)',
        lambda m: f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)', text)
    assert loops == 4
    host = ROOT/'group-state-host'
    host.mkdir(exist_ok=True)
    (host/'groups.cpp').write_text(PREFIX+'\n'+text+'\n'+SUFFIX)
    (host/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_group_state LANGUAGES CXX)\nadd_executable(groups groups.cpp)\ntarget_compile_features(groups PRIVATE cxx_std_17)\n')
    for args in ([CMAKE, '-S', str(host), '-B', str(host/'build')],
                 [CMAKE, '--build', str(host/'build'), '--config', 'Release']):
        build = subprocess.run(args, capture_output=True, text=True)
        assert build.returncode == 0, build.stdout+build.stderr
    inputs, expected = [], []
    models = {}
    def record(command, result=0):
        fields = [int(result)]
        for player in range(1, 9):
            model = models[player]
            fields += [model.next_id, model.count, len(model.groups)]
            for group in model.groups.values():
                fields += [group.id, group.kind, group.desired, group.action, group.target,
                           group.target_type, group.in_use, group.flags, group.retreat,
                           group.last_added, len(group.members)] + group.members
        inputs.append(command)
        expected.append(' '.join(map(str, fields)))
    for batch in range(2):
        models = {p: GroupState() for p in range(1, 9)}
        record('Z')
        sequences = source['sequences'][batch*8:(batch+1)*8]
        for p, sequence in enumerate(sequences, 1):
            models[p].next_id = sequence['next_id']
            record(f'I {p} {models[p].next_id}')
        for step in range(max(len(s['operations']) for s in sequences)):
            for p, sequence in enumerate(sequences, 1):
                if step >= len(sequence['operations']):
                    continue
                name, *args = sequence['operations'][step]
                model = models[p]
                if name == 'kind':
                    model.groups[args[0]].kind = args[1]
                    record(f'T {p} {args[0]} {args[1]}')
                    continue
                result = getattr(model, name)(*args)
                if name == 'create':
                    record(f'C {p} {args[0]} {int(args[1])} {result}', bool(result))
                elif name == 'containing':
                    ordinal = list(model.groups).index(result)+1 if result else 0
                    record(f'F {p} {args[0]}', ordinal)
                else:
                    symbol = {'add':'A', 'remove':'R', 'delete':'D', 'delete_kind':'K'}[name]
                    record(f'{symbol} {p} '+ ' '.join(map(str,args)), result)
    run = subprocess.run([str(host/'build/Release/groups.exe')], input='\n'.join(inputs)+'\n',
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    actual = run.stdout.splitlines()
    assert len(actual) == len(expected), (len(actual), len(expected))
    for i, (a, b) in enumerate(zip(actual, expected)):
        assert a == b, (i, inputs[i], a, b)
    report = dict(passed=True, cases=len(expected), source_cases=source['cases'], players=8,
                  xs_sha256=hashlib.sha256(xs.read_bytes()).hexdigest(), installed=False,
                  full_behavior_parity=False,
                  limitations=['C++ host, not DE VM/network/save-load verification.',
                               'Container fields only; targeting/path memory/order scheduling remain separate.'])
    (ROOT/'group-state-xs-validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS', len(expected), 'interleaved XS group transitions across eight players; not installed')


if __name__ == '__main__':
    main()
