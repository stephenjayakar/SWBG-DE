"""Stage source nursery economy through DE XS; engine validation remains pending."""
from pathlib import Path
import csv,json,hashlib,argparse
from reserved_unit_ids import de_unit_id

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path('work/faction-package'))
parser.add_argument('--report',type=Path,default=Path('outputs/faction-nursery-report.json'))
args=parser.parse_args()

source_exe=Path(r'E:\GOG Games\Star Wars - Galactic Battlegrounds\Game\battlegrounds_x2.exe')
assert hashlib.sha256(source_exe.read_bytes()).hexdigest().upper() == 'D64E7F0ECC546C3BD833C5C6A7BC97B75EE74940D89B1CB22349B0ACE0F3FC58', 'Re-audit source nursery timing after executable changes'

def rows(name):
    return list(csv.DictReader(open(f'work/faction-source/{name}.tsv'),delimiter='\t'))
source_units={int(r['id']):r for r in rows('units') if r['civ']=='1'}
nursery_ids={319}
while True:
    expanded=nursery_ids|{int(r['b']) for r in rows('effects') if r['type']=='3'
                           and int(r['a']) in nursery_ids and source_units[int(r['b'])]['type']=='80'}
    if expanded==nursery_ids:break
    nursery_ids=expanded
assert nursery_ids=={319,320,321,322,3550,3551,3552,3553}, 'Review nursery upgrade family'
rates={int(r['civ']):float(r['workrate']) for r in rows('unit-behavior') if r['unit']=='319'}
assert rates[1]==rates[3]==0.13
assert all(float(r['workrate'])==.13 for r in rows('unit-behavior')
           if r['civ'] in ('1','3') and int(r['unit']) in nursery_ids)
effects=[r for r in rows('effects') if r['type'] in ('0','4','5') and r['c']=='13'
         and (r['a']=='319' or r['b']=='18')]
assert all(r['type']=='5' for r in effects)
techs=rows('techs')
upgrades=[]
for e in effects:
    matches=[r for r in techs if r['effect']==e['effect']]
    assert len(matches)==1
    t=matches[0]
    if t['civ'] not in ('-1','1','3'):continue
    upgrades.append((int(t['id']),float(e['d'])))
assert dict(upgrades)=={82:1.17,83:1.33333,127:1.5,571:1.1}
script='''// Source nursery adapter. Experimental: requires current DE unit-query APIs.
// Source 0x55537e uses integer elapsed milliseconds / 1000 as a one-second gate.
// Source 0x555509 credits master work_rate once per class-1 animal inside.
// Power changes work_rate2; it does not scale this source food calculation.
int swgbHerdArray = -1;
int swgbNurseryLastSecond = -1;

bool swgbIsNursery(int id = -1) {
    return(NURSERY_FAMILY);
}

float swgbNurseryRate(int player = 1) {
    float rate = 0.13;
'''
for tech,multiplier in upgrades:
    script+=f'    if (xsGetTechState({tech}, player) == 3) rate = rate * {multiplier};\n'
script+='''    return(rate);
}

rule swgbNurseryTick
active
minInterval 1
maxInterval 1
{
    int now = xsGetGameTime();
    if (swgbNurseryLastSecond < 0) {
        swgbNurseryLastSecond = now;
        return;
    }
    if (now <= swgbNurseryLastSecond) return;
    float elapsed = now - swgbNurseryLastSecond;
    swgbNurseryLastSecond = now;
    // Reuse one array; no array is allocated per animal or per tick.
    int lastPlayer = xsGetNumPlayers();
    if (lastPlayer > 8) lastPlayer = 8;
    for (player = 1; <= lastPlayer) {
        swgbHerdArray = xsGetPlayerUnitIds(player, 958, swgbHerdArray);
        if (swgbHerdArray >= 0) {
            for (index = 0; < xsArrayGetSize(swgbHerdArray)) {
                int animal = xsArrayGetInt(swgbHerdArray, index);
                int building = xsGetGarrisonedInUnitId(animal);
                if (building >= 0) {
                    if (xsDoesUnitExist(building)) {
                        if (swgbIsNursery(xsGetUnitCopyId(building))) {
                            int owner = xsGetUnitOwner(building);
                            // Income belongs to the building owner, including allied livestock.
                            if (owner > 0) {
                                if (xsGetPlayerInGame(owner)) {
                                    xsEffectAmount(cModResource, cAttributeFood, cAddAttribute,
                                                   swgbNurseryRate(owner) * elapsed, owner);
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

void main() {
    swgbHerdArray = xsArrayCreateInt(1, -1, "swgb herd query");
    swgbNurseryLastSecond = xsGetGameTime();
}
'''
from faction_astromech import integrate_astromech
# XS compares DE unit IDs: map SWGB IDs out of DE's reserved group range 900-999.
script=script.replace('NURSERY_FAMILY',' || '.join(f'id == {de_unit_id(uid)}' for uid in sorted(nursery_ids)))
script=integrate_astromech(script)
script=Path(__file__).with_name('faction_defense_shields.xs').read_text(encoding='ascii')+'\n'+script
assert script.count('{')==script.count('}')
dest=args.root/'resources/_common/xs';dest.mkdir(parents=True,exist_ok=True)
(dest/'swgb_factions.xs').write_text(script,encoding='ascii')
maps=list((args.root/'resources/_common/random-map-scripts').glob('SWGB Factions *.rms'))
assert len(maps)==20
for path in maps:
    body=path.read_text(encoding='ascii')
    if not body.startswith('#includeXS swgb_factions.xs\n'):
        body='#includeXS swgb_factions.xs\n'+body
        path.write_bytes(body.encode('ascii'))
    assert body.count('#includeXS')==1
report=dict(base_food_per_animal_per_second=.13,upgrade_multipliers=dict(upgrades),
            interval_seconds=1,clock='elapsed game seconds',catch_up_delayed_ticks=True,source_power_independent=True,maps=len(maps),
            engine_compilation_verified=False,engine_income_verified=False,
            limitations=['Garrison queries and save/load need engine checks',
                         'Credits stockpile food; source earned-resource statistics need verification',
                         'Only maps that include swgb_factions.xs run the food adapter'],
            nursery_ids=sorted(nursery_ids))
args.report.write_text(json.dumps(report,indent=2))
print(json.dumps(report))
