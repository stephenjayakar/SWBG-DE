"""Check XS candidate gates against the source-tested admission fixtures.

The C++ host is not the DE XS VM. Source observations stay explicit; neither
this check nor the helpers provide live visibility/memory/pathfinding.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import subprocess
from check_classic_air_planner import CMAKE, PREFIX
from check_classic_admission import fixtures
from classic_admission_model import candidate_admitted

WORK = Path('work/classic-engine/admission-host')
TOOLKIT = Path('outputs/toolkit')
MAIN = r'''
int main() {
    int uid,owner,wanted,exists,status,relation,state,unordered,master,visible,fog,moving,
        flags,cls,source,land,force,zone,group,monks,reference,ai,convertible,difficulty,width,height,n;
    float hp,x,y;
    while(std::cin>>uid>>owner>>wanted>>exists>>status>>relation>>state>>hp>>unordered
          >>master>>visible>>fog>>moving>>flags>>cls>>source>>land>>force>>zone>>group
          >>monks>>reference>>ai>>convertible>>difficulty>>x>>y>>width>>height>>n) {
        bool wall=false;
        for(int i=0;i<n;i++) {
            int tx,ty;std::cin>>tx>>ty;
            if(classicAdmissionWallTile(vector(x,y,0),tx,ty,width,height)) wall=true;
        }
        if(unordered) hp=std::numeric_limits<float>::quiet_NaN();
        bool admitted=classicAdmissionMemory(uid,owner,wanted,exists!=0,status,relation,state,hp)
            && classicAdmissionVisibility(master,visible,fog,moving)
            && classicAdmissionDomain(land,(flags&2)!=0,master,source,cls,wall,force,zone&255,group)
            && classicAdmissionPolicy(monks,reference!=0,ai!=0,convertible,difficulty,cls);
        std::cout<<int(admitted)<<'\n';
    }
}
'''


def main():
    proof = Path('work/classic-engine/admission-validation.json')
    report = json.loads(proof.read_text())
    assert report['passed']
    for name, expected in report['tool_hashes'].items():
        assert hashlib.sha256((TOOLKIT / name).read_bytes()).hexdigest() == expected, name
    xs = TOOLKIT / 'classic_target_admission.xs'
    lint = subprocess.run(['work/xs-check/xs-check.exe', str(xs)], capture_output=True, text=True, check=True)
    clean = re.sub(r'\x1b\[[0-9;]*m', '', lint.stdout + lint.stderr)
    assert 'Error:' not in clean and 'Warning:' not in clean and 'No errors found' in clean, clean
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / 'admission.cpp').write_text('#include <limits>\n' + PREFIX + xs.read_text() + MAIN)
    (WORK / 'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_admission LANGUAGES CXX)\nadd_executable(admission admission.cpp)\ntarget_compile_features(admission PRIVATE cxx_std_17)\n')
    subprocess.run([CMAKE, '-S', str(WORK), '-B', str(WORK / 'build')], capture_output=True, check=True)
    subprocess.run([CMAKE, '--build', str(WORK / 'build'), '--config', 'Release'], capture_output=True, check=True)
    rows, expected = [], []
    for t, c, tiles in fixtures():
        fields = (t.uid, t.memory_owner, c.player, int(t.exists), t.owner_status, t.relation, t.state,
                  0 if math.isnan(t.hp) else t.hp, int(math.isnan(t.hp)), t.master_type, t.visibility,
                  t.fog_flag, t.moving, t.object_flags, t.source_class, t.source_id, c.land_group,
                  c.force_different_zone, t.zone, c.group_zone, c.all_monks, int(c.reference_monk),
                  int(c.monk_unit_ai), t.convertible, c.difficulty, t.x, t.y, c.width, c.height, len(tiles))
        rows.append(' '.join(map(str, fields)) + ' ' + ' '.join(f'{x} {y}' for x, y in tiles))
        expected.append(str(int(candidate_admitted(t, c, tiles))))
    run = subprocess.run([str(WORK / 'build/Release/admission.exe')], input='\n'.join(rows) + '\n',
                         text=True, capture_output=True, check=True)
    actual = run.stdout.splitlines()
    assert len(actual) == len(expected), (len(actual), len(expected))
    for index, (got, want) in enumerate(zip(actual, expected)):
        assert got == want, (index, rows[index], got, want)
    result = dict(passed=True, cases=len(expected), xs_sha256=hashlib.sha256(xs.read_bytes()).hexdigest(),
                  oracle_report_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(), xs_checker_warnings=0,
                  limitations=['C++ host, not native DE XS/PER execution.',
                               'Caller supplies source-compatible memory, visibility, movement, conversion and zone observations.',
                               'No live orders, target memory updates or path selection.'],
                  installed=False, full_behavior_parity=False)
    Path('work/classic-engine/admission-xs-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'PASS {len(expected)} compiled XS admission cases; clean syntax; not installed')


if __name__ == '__main__':
    main()
