"""Check DE bridge callbacks against source-verified dispatch and failure cases.

This is a C++ builtin host plus PER parsing/flow checks, not native game proof.
"""
from pathlib import Path
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from check_classic_air_planner import CMAKE, PREFIX
from check_classic_attack_dispatch import fixtures
from check_classic_attack_dispatch_xs import EXTRA
from classic_attack_dispatch import dispatch
from classic_group_state import GroupState
from classic_dispatch_bridge import OBSERVE, STOP
from classic_ai_source import graph, parse

ROOT = Path('work/classic-engine')
TOOLKIT = Path('outputs/toolkit')
HOST = r'''
struct Object { int copy,zone,owner;float x,y;bool exists; };
std::map<int,Object> objects;
int goals[512]={};int civilization=1;
bool xsDoesUnitExist(int id) { return objects.count(id) && objects.at(id).exists; }
int xsGetUnitOwner(int id) { return objects.at(id).owner; }
int xsGetUnitCopyId(int id) { return objects.at(id).copy; }
int xsGetPlayerCivilization(int owner) { return civilization; }
vector xsGetUnitPosition(int id) { auto o=objects.at(id);return vector(o.x,o.y,0); }
int xsGetGoal(int id) { return goals[id]; }
void xsSetGoal(int id,int value) { goals[id]=value; }
'''
MAIN = r'''
int main() {
    int n,ng,nb,na,gp,bp,ap,difficulty,radius,now,player,mode;
    int ground=xsArrayCreateInt(0,0,""),boats=xsArrayCreateInt(0,0,""),air=xsArrayCreateInt(0,0,"");
    classicIdentityInit();
    while(std::cin>>n>>ng>>nb>>na>>gp>>bp>>ap>>difficulty>>radius>>now>>player>>civilization>>mode) {
        objects.clear();
        for(int i=0;i<n;i++) { int uid;Object o;std::cin>>uid>>o.copy>>o.x>>o.y>>o.zone;
            o.owner=player;o.exists=true;objects[uid]=o; }
        for(auto item:{std::pair<int,int>{ground,ng},{boats,nb},{air,na}}) {
            xsArrayResizeInt(item.first,item.second);
            for(int i=0;i<item.second;i++) { int uid;std::cin>>uid;xsArraySetInt(item.first,i,uid); }
        }
        classicGroupsReset(7);
        if(ng) { int h=classicGroupCreate(player);classicGroupSet(h,4,101);classicGroupAdd(h,xsArrayGetInt(ground,0),123); }
        auto original=objects;
        for(int repeat=0;repeat<2;repeat++) {
            objects=original;
            if(mode==2) objects.at(2).owner=player%8+1;
            goals[104]=player;
            if(!classicBridgeBegin(player,ground,boats,air,gp,bp,ap,difficulty,radius,now)) throw std::runtime_error("Begin failed");
            if(classicBridgeBegin(player)) throw std::runtime_error("Busy bridge overwritten");
            int observations=0;
            while(true) {
                int cursor=classicBridgeCursor,domain=classicBridgeDomain;
                goals[104]=player%8+1;
                swgbClassicDispatchObserveNext();swgbClassicDispatchStopNext();
                if(classicBridgeCursor!=cursor || classicBridgeDomain!=domain) throw std::runtime_error("Cross-player callback");
                goals[104]=player;
                swgbClassicDispatchObserveNext();
                int uid=goals[112];if(uid<0) break;
                if(++observations>ng+nb+na) throw std::runtime_error("Unbounded observation loop");
                if(mode==9 || (mode==1 && uid==2)) continue;
                goals[113]=objects.at(uid).zone;goals[114]=1;
                if(mode==3 && uid==2) objects.at(uid).owner=player%8+1;
                if(mode==4 && uid==2001) objects.at(uid).exists=false;
                if(mode==11) {
                    goals[104]=player%8+1;swgbClassicDispatchObserveCommit();goals[104]=player;
                    if(classicBridgePending!=uid) throw std::runtime_error("Foreign commit");
                }
                swgbClassicDispatchObserveCommit();
                if(mode==10) swgbClassicDispatchObserveCommit();
            }
            if(mode==5) objects.at(2).exists=false;
            if(mode==6) objects.at(2).owner=player%8+1;
            std::vector<int> sent;
            int commands=0;
            while(true) {
                swgbClassicDispatchStopNext();int uid=goals[115];if(uid<0) break;
                if(++commands>ng+nb+na) throw std::runtime_error("Unbounded command loop");
                if(mode==8 && uid==2) continue;
                if(mode==7 && uid==2) objects.at(uid).owner=player%8+1;
                goals[118]=objects.at(uid).owner;
                if(goals[118]==goals[104]) sent.push_back(uid);
            }
            if(classicBridgeBusy) throw std::runtime_error("Bridge remained busy");
            if(classicBridgeBegin(0) || classicBridgeBegin(9)) throw std::runtime_error("Invalid player accepted");
            std::cout<<sent.size();for(int uid:sent) std::cout<<' '<<uid;
            std::cout<<' '<<xsArrayGetInt(classicGroupNextIds,player)<<' '<<xsArrayGetInt(classicGroupCounts,player);
            for(int h=xsArrayGetInt(classicGroupHeads,player);h;h=classicGroupGet(h,1)) {
                for(int field:{3,4,6,7,8,9,10,11,12,13,5}) std::cout<<' '<<classicGroupGet(h,field);
                for(int i=0;i<classicGroupGet(h,5);i++) std::cout<<' '<<classicGroupGet(h,14+i);
            }
            std::cout<<'\n';
            if(arrays.size()!=18) throw std::runtime_error("Bridge array leak");
        }
    }
}
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases():
    for f in fixtures():
        # Allocation failure belongs to the isolated engine oracle, not a DE
        # builtin failure we can force through this bridge's public API.
        if f['fail_after'] is None:
            yield f, 0
    for mode in range(1, 12):
        for difficulty in (0, 2, 3, 4):
            for percentage in (1, 50, 100):
                yield dict(ground=[1, 2, 3], boats=[2001, 2002], air=[1001, 1002],
                           classes={1:32, 2:32, 3:32, 2001:20, 2002:20, 1001:48, 1002:48},
                           positions={u:(i*3, 5, 0) for i,u in enumerate((1,2,3,2001,2002,1001,1002))},
                           ground_percent=percentage, boat_percent=percentage, air_percent=percentage,
                           difficulty=difficulty, radius=20, now=8765, fail_after=None), mode


def main():
    source = json.loads((ROOT/'dispatch-validation.json').read_text())
    assert source['passed']
    for name, digest in source['tool_hashes'].items():
        assert sha(TOOLKIT/name) == digest, name
    identity = json.loads((ROOT/'identity-manifest.json').read_text())
    assert sha(ROOT/'classic_unit_identity.xs') == identity['xs_sha256']
    assert sha(ROOT/'unit-identity.tsv') == identity['identity_tsv_sha256']
    files = ('classic_group_state.xs', 'classic_army_pool.xs', 'classic_air_planner.xs',
             'classic_attack_dispatch.xs', 'classic_dispatch_bridge.xs')
    text = (ROOT/'classic_unit_identity.xs').read_text() + '\n' + '\n'.join((TOOLKIT/n).read_text() for n in files)
    host = ROOT/'dispatch-bridge-host'
    host.mkdir(exist_ok=True)
    (host/'combined.xs').write_text(text)
    lint = subprocess.run(['work/xs-check/xs-check.exe', str(host/'combined.xs')], capture_output=True, text=True)
    output = re.sub(r'\x1b\[[0-9;]*m', '', lint.stdout+lint.stderr)
    assert lint.returncode == 0 and 'No errors found' in output and not re.search(r'\b(?:Error|Warning):', output), output
    text = text.replace('for (i = 0; < xsArrayGetSize(classicGroups))',
                        'for (int i = 0; i < xsArrayGetSize(classicGroups); i++)')
    text, loops = re.subn(r'for \((\w+) = ([^;]+); < ([^)]+)\)',
                          lambda m: f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)', text)
    assert loops == 14
    (host/'bridge.cpp').write_text(PREFIX+EXTRA+HOST+text+MAIN)
    (host/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_bridge LANGUAGES CXX)\nadd_executable(bridge bridge.cpp)\ntarget_compile_features(bridge PRIVATE cxx_std_17)\n')
    for args in ([CMAKE, '-S', str(host), '-B', str(host/'build')],
                 [CMAKE, '--build', str(host/'build'), '--config', 'Release']):
        r = subprocess.run(args, capture_output=True, text=True)
        assert r.returncode == 0, r.stdout+r.stderr
    records = list(csv.DictReader((ROOT/'unit-identity.tsv').open(), delimiter='\t'))
    copies = {(c, cls): next(int(r['slot']) for r in records if int(r['civ'])==c and int(r['source_class'])==cls)
              for c in (1, 2) for cls in (20, 32, 48, 50, 51, 59, 63)}
    inputs, expected = [], []
    for index, (f, mode) in enumerate(cases()):
        player, civ = index%8+1, index%2+1
        values = [len(f['classes']), len(f['ground']), len(f.get('boats', ())), len(f['air']),
                  f['ground_percent'], f.get('boat_percent', 0), f['air_percent'], f['difficulty'],
                  f['radius'], f['now'], player, civ, mode]
        for uid, cls in f['classes'].items():
            values += [uid, copies[civ, cls], *f['positions'][uid]]
        values += f['ground'] + list(f.get('boats', ())) + f['air']
        inputs.append(' '.join(map(str, values)))
        model = GroupState(7)
        if f['ground']:
            h = model.create(); model.groups[h].kind = 101; model.add(h, f['ground'][0], 123)
        changed = dict(f)
        if mode in (1, 2, 3):
            changed['ground'] = [u for u in f['ground'] if u != 2]
        if mode == 4:
            changed['classes'] = {u:c for u,c in f['classes'].items() if u != 2001}
        if mode == 9:
            changed.update(ground=[], boats=[], air=[])
        for repeat in range(2):
            stops = dispatch(model, **changed)
            if mode in (5, 6, 7, 8):
                stops = [u for u in stops if u != 2]
            out = [len(stops)] + stops + [model.next_id, model.count]
            for g in model.groups.values():
                out += [g.id, g.kind, g.desired, g.action, g.target, g.target_type,
                        g.in_use, g.flags, g.retreat, g.last_added, len(g.members)] + g.members
            expected.append(' '.join(map(str, out)))
    run = subprocess.run([str(host/'build/Release/bridge.exe')], input='\n'.join(inputs)+'\n', capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    actual = run.stdout.splitlines()
    assert len(actual) == len(expected), (len(actual), len(expected))
    for i, (a,b) in enumerate(zip(actual, expected)):
        assert a == b, (i, inputs[i//2], a, b)

    # Backward jumps always reach an advancing Next callback, not the same item.
    for block, function in ((OBSERVE, 'swgbClassicDispatchObserveNext'), (STOP, 'swgbClassicDispatchStopNext')):
        rules = [n for n in parse(block) if isinstance(n, list) and n[0]=='defrule']
        assert len(rules)==5 and rules[3][-1]==['up-jump-rule', '-4']
        assert 3+1+int(rules[3][-1][1])==0 and function in str(rules[0])
    assert '(up-get-object-data object-data-map-zone-id 113)' in OBSERVE
    assert '(up-get-object-data object-data-player 118)' in STOP
    assert '(up-compare-goal 118 g:== 104)' in STOP
    assert '(up-target-point 116 action-stop -1 -1)' in STOP
    nodes, alternatives, _ = graph()
    nodes += sum(alternatives.values(), [])
    constants = {}
    for n in nodes:
        if isinstance(n, list) and n[0]=='defconst' and re.fullmatch(r'-?\d+', n[2]):
            constants.setdefault(n[1], set()).add(int(n[2]))
    def slots(nodes):
        used = set()
        for n in nodes:
            if not isinstance(n, list): continue
            if n and n[0] in ('goal', 'set-goal'):
                used |= {int(n[1])} if n[1].isdigit() else constants[n[1]]
            used |= slots(n)
        return used
    assert not slots(nodes) & set(range(112, 119))
    per = host/'bridge.per'
    per.write_text(OBSERVE+'\n'+STOP+'\n(include "combined.xs")\n')
    parser = Path('work/ai-parser')
    env = dict(os.environ, PYTHONPATH=str((parser/'src').resolve()))
    r = subprocess.run([sys.executable, '-m', 'aoe2_ai_lab', 'lint-package', str(per), '--profile', 'corpus', '--json'],
                       env=env, capture_output=True, text=True)
    (host/'parser.json').write_text(r.stdout)
    assert r.returncode == 0, r.stdout+r.stderr
    parsed = json.loads(r.stdout)
    assert not parsed['failed'] and not parsed['finding_groups'] and not parsed['issue_groups'], parsed
    report = dict(passed=True, scenarios=len(inputs), dispatch_calls=len(expected), source_dispatch_calls=source['cases'],
                  xs_hashes={n:sha(TOOLKIT/n) for n in files}, identity_manifest_sha256=sha(ROOT/'identity-manifest.json'),
                  bridge_sha256=sha(TOOLKIT/'classic_dispatch_bridge.py'), checker_sha256=sha(Path(__file__)),
                  installed=False, full_behavior_parity=False,
                  limitations=['C++ host and standalone parser, not native DE VM/PER execution.',
                               'Caller supplies source-ordered pools; pool maintenance is not implemented here.',
                               'DE map-zone equivalence and command delivery need game verification.',
                               'Only dispatch stop requests; subsequent target selection/orders are not connected.',
                               'Entire bridge pass must finish synchronously; saving mid-pass is not tested.'])
    (ROOT/'dispatch-bridge-validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS',len(inputs),'bridge scenarios /',len(expected),'dispatch calls; not installed')


if __name__=='__main__':
    main()
