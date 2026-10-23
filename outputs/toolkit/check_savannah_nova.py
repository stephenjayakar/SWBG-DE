"""Check the staged Nova repair and the user's captured starting-map regression.

The geometric check is not DE's random map generator. It establishes that the
reserved group has room in the actual protected terrain, not a native guarantee.
Requires aoe2-rms-parser@2.0.1 installed in work/age-crash/rms-check.
"""
from pathlib import Path
import hashlib,json,math,re,subprocess
from faction_savannah_nova import repair_savannah_nova,MARKER

ROOT=Path('work/age-crash')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    before=ROOT/'savannah-before.rms'
    after=ROOT/'patch/resources/_common/random-map-scripts/SWGB Factions Savannah.rms'
    stage=json.loads((ROOT/'savannah-nova-stage.json').read_text())
    assert sha(before)==stage['before'] and sha(after)==stage['after']
    old=before.read_text();new=after.read_text()
    assert new==repair_savannah_nova(old)
    assert repair_savannah_nova(new)==new
    # Both source and namespaced converter forms must produce the same repair.
    assert repair_savannah_nova(old.replace('SWGB_',''))==new.replace('SWGB_','')
    block=re.search(r'create_object SWGB_OBJ-NOVA\s*\{[^{}]*\}',new)[0]
    assert new.index(block)>new.index('<OBJECTS_GENERATION>')
    assert not re.search(r'\bcreate_object\b',new[new.index('<OBJECTS_GENERATION>'):new.index(block)])
    assert new.count('create_object SWGB_OBJ-NOVA')==old.count('create_object SWGB_OBJ-NOVA')
    assert 'max_distance_to_other_zones' not in block
    # Removing the replacement and original primary block must leave every
    # other source instruction and its order unchanged (whitespace normalized).
    old_primary=next(m[0] for m in re.finditer(r'create_object SWGB_OBJ-NOVA\s*\{[^{}]*\}',old) if 'set_place_for_every_player' in m[0])
    normalize=lambda text:re.sub(r'\s+',' ',text).strip()
    assert normalize(old.replace(old_primary,'',1))==normalize(new.replace(MARKER,'',1).replace(block,'',1))
    fixture='#const SWGB_OBJ-NOVA 66\n#const SWGB_GRASS2 12\n<OBJECTS_GENERATION>\n'+block+'\n'
    (ROOT/'rms-check/nova-block.rms').write_text(fixture)
    script='''const fs=require('fs');const p=require('aoe2-rms-parser');
const result=p.parse(fs.readFileSync('nova-block.rms','utf8'));
if(result.errors.length)throw Error(JSON.stringify(result.errors));
const findings=p.lint(result.ast);console.log(JSON.stringify(findings));
if(findings.length)process.exit(1);
'''
    (ROOT/'rms-check/nova-block.cjs').write_text(script)
    run=subprocess.run(['C:/Program Files/nodejs/node.exe','nova-block.cjs'],cwd=ROOT/'rms-check',capture_output=True,text=True)
    assert run.returncode==0,run.stdout+run.stderr

    data=(ROOT/'nova-replay-header.raw').read_bytes()
    terrain=json.loads((ROOT/'nova-replay-map.json').read_text())[0]
    players=json.loads((ROOT/'nova-replay-players.json').read_text())[0]
    size=terrain['size'];start=terrain['tile_start']
    def grass(x,y):return 0<=x<size and 0<=y<size and data[start+(y*size+x)*10]==12
    nova=[o['position'] for o in players[0]['objects'] if o['object_id']==66]
    assert nova
    starts=[]
    # One legal seven-crystal shape within the configured radius; this does not
    # reproduce RNG, object collision, ordering or the full placement algorithm.
    offsets=((0,0),(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1))
    for player in players[1:]:
        cc=next(o['position'] for o in player['objects'] if o['object_id']==109)
        nearest=min(math.hypot(o['x']-cc['x'],o['y']-cc['y']) for o in nova)
        candidates=[]
        for y in range(size):
            for x in range(size):
                distance=math.hypot(x+.5-cc['x'],y+.5-cc['y'])
                if 12<=distance<=16 and all(grass(x+dx,y+dy) for dx,dy in offsets):candidates.append((x,y))
        assert len(candidates)>100,(player['number'],len(candidates))
        starts.append(dict(player=player['number'],command_center=cc,original_nearest_nova=nearest,
                           terrain_only_eligible_group_centers=len(candidates)))
    assert starts[0]['original_nearest_nova']>78
    report=dict(passed=True,starts=starts,before_sha256=sha(before),after_sha256=sha(after),
        replay_header_sha256=sha(ROOT/'nova-replay-header.raw'),
        source_hashes={p:sha(Path('outputs/toolkit')/p) for p in ('faction_savannah_nova.py','check_savannah_nova.py','faction_maps.py')},
        replacement_parser='aoe2-rms-parser 2.0.1',replacement_parse_and_lint_clean=True,
        installed=False,engine_verified=False,
        limitations=['Full legacy map uses conditional object syntax unsupported by this independent parser; only replacement is parser-checked.',
                     'Original non-primary placement instructions are unchanged.',
                     'Geometric room in recorded terrain does not prove native map generation, collision handling or seed coverage.'])
    (ROOT/'savannah-nova-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,starts=starts,installed=False,engine_verified=False)))

if __name__=='__main__':main()
