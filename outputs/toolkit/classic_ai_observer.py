"""Generate the XS observations missing from DE's native PER vocabulary."""
from pathlib import Path
import csv
import json
from classic_ai_bindings import unit_bindings
from reserved_unit_ids import de_unit_id
from classic_ai_map_identity import rewrite as identity_rewrite
from classic_ai_power_placement import rewrite_xs as power_points_rewrite

root=Path('work/original-ai/patch')
raw,groups,_,_=unit_bindings()
required=('bldg-dropanim','bldg-shldgen','bldg-trainair','bldg-trainboat',
          'bldg-trainheavy','bldg-trainjedi','bldg-trainmech','bldg-traintrooper')
targets=sorted(set().union(*(set(groups[g]) for g in required)))
nurseries=groups['bldg-dropanim']
aura=list(csv.DictReader(Path('work/economy-repair/dependencies/aura-tasks.tsv').open(),delimiter='\t'))
emitters={}
for r in aura:
    if r['attribute']=='13' and r['work1']=='3' and r['civ'] in ('1','2'):
        emitters.setdefault(int(r['civ']),{})[int(r['unit'])]=float(r['range'])
assert set(emitters)=={1,2}

def member(name,items):
    # Break expressions into short lines for both the XS compiler and inspection.
    # Runtime IDs are DE IDs: SWGB IDs in 900-999 are moved (reserved_unit_ids).
    return f'bool {name}(int id = -1) {{\n    return('+(' ||\n           '.join(f'id == {de_unit_id(i)}' for i in items))+');\n}\n'

text='''// Invoked only by SWGB Classic AI. Goal slots 100..111 are reserved.
// 100: source max-unpowered threshold; 101: observed unpowered buildings;
// 102: requested source aircraft attack percent (DE has no separate air pool);
// 103: nursery headroom; 104: caller's player number.
// 105 reserved; 106..111: individual nursery command bridge below.
// 120: worker count (DE villager class 904). Replaces the source worker count group, because a DE
//      unitlines.json group containing unit 83 made (can-train 83) resolve to another line member.
int classicBuildings = -1;
int classicOtherUnits = -1;
int classicWorkers = -1;
int classicAnimals = -1;
int classicEmitterPositions = -1;
int classicEmitterRanges = -1;
int classicLastTimes = -1;
int classicEmitterCount = 0;
'''
text+=member('classicPowerTarget',targets)+member('classicNursery',nurseries)
animals=json.loads(Path('work/original-ai/translation.json').read_text())['herdable_ids']
text+=member('classicNurseryAnimal',animals)
text+=member('classicAnimalFallback',sorted(set(groups['bldg-main'])|set(groups['bldg-dropchow'])))
text+='float classicEmitterRange(int player = 1, int id = -1) {\n'
for civ,values in sorted(emitters.items()):
    text+=f'    if (xsGetPlayerCivilization(player) == {civ}) {{\n'
    for uid,radius in sorted(values.items()):text+=f'        if (id == {uid}) return({radius});\n'
    text+='    }\n'
text+='    return(0.0);\n}\n'
text+='''
bool classicFinished(int unit = -1) {
    return(xsDoesUnitExist(unit) &&
           xsGetUnitBuildPoints(unit) >= xsGetUnitAttribute(unit, cTrainTime));
}

void classicAddEmitters(int player = 1, int array = -1) {
    if (array < 0) return;
    for (i = 0; < xsArrayGetSize(array)) {
        int unit = xsArrayGetInt(array, i);
        if (xsDoesUnitExist(unit)) {
            float radius = classicEmitterRange(player, xsGetUnitCopyId(unit));
            if (radius > 0.0) {
                bool ready = true;
                if (xsGetUnitType(unit) == 80) ready = classicFinished(unit);
                if (ready) {
                    if (classicEmitterCount >= xsArrayGetSize(classicEmitterPositions)) {
                        xsArrayResizeVector(classicEmitterPositions, classicEmitterCount + 1);
                        xsArrayResizeFloat(classicEmitterRanges, classicEmitterCount + 1);
                    }
                    xsArraySetVector(classicEmitterPositions, classicEmitterCount, xsGetUnitPosition(unit));
                    xsArraySetFloat(classicEmitterRanges, classicEmitterCount, radius);
                    classicEmitterCount++;
                }
            }
        }
    }
}

void swgbClassicObserve() {
    int player = xsGetGoal(104);
    if (player < 1 || player > 8) return;
    if (classicLastTimes < 0) {
        classicLastTimes = xsArrayCreateInt(9, -1, "classic observer times");
        classicEmitterPositions = xsArrayCreateVector(1, vector(0,0,0), "classic emitter positions");
        classicEmitterRanges = xsArrayCreateFloat(1, 0.0, "classic emitter ranges");
    }
    int now = xsGetGameTime();
    if (xsArrayGetInt(classicLastTimes, player) == now) return;
    xsArraySetInt(classicLastTimes, player, now);
    classicBuildings = xsGetPlayerUnitIds(player, 903, classicBuildings);
    classicOtherUnits = xsGetPlayerUnitIds(player, 911, classicOtherUnits);
    classicWorkers = xsGetPlayerUnitIds(player, 904, classicWorkers);
    int workers = 0;
    if (classicWorkers >= 0) workers = xsArrayGetSize(classicWorkers);
    xsSetGoal(120, workers);
    classicEmitterCount = 0;
    classicAddEmitters(player, classicBuildings);
    classicAddEmitters(player, classicOtherUnits);
    int unpowered = 0;
    int headroom = 0;
    if (classicBuildings >= 0) {
        for (i = 0; < xsArrayGetSize(classicBuildings)) {
            int unit = xsArrayGetInt(classicBuildings, i);
            if (classicFinished(unit)) {
                int id = xsGetUnitCopyId(unit);
                if (classicNursery(id)) {
                    int capacity = xsCeilToInt(xsGetUnitAttribute(unit, cGarrisonCapacity));
                    headroom = headroom + capacity;
                }
                if (classicPowerTarget(id)) {
                    bool powered = false;
                    vector position = xsGetUnitPosition(unit);
                    for (j = 0; < classicEmitterCount) {
                        vector emitter = xsArrayGetVector(classicEmitterPositions, j);
                        float radius = xsArrayGetFloat(classicEmitterRanges, j);
                        float dx = xsVectorGetX(position) - xsVectorGetX(emitter);
                        float dy = xsVectorGetY(position) - xsVectorGetY(emitter);
                        if (dx*dx + dy*dy <= radius*radius) powered = true;
                    }
                    if (powered == false) unpowered++;
                }
            }
        }
    }
    // Include allied animals housed in our nursery; reuse the query array.
    int lastPlayer = xsGetNumPlayers();
    if (lastPlayer > 8) lastPlayer = 8;
    for (owner = 1; <= lastPlayer) {
        classicAnimals = xsGetPlayerUnitIds(owner, 958, classicAnimals);
        if (classicAnimals >= 0) {
            for (i = 0; < xsArrayGetSize(classicAnimals)) {
                int holder = xsGetGarrisonedInUnitId(xsArrayGetInt(classicAnimals, i));
                if (holder >= 0) {
                    if (xsDoesUnitExist(holder)) {
                        if (xsGetUnitOwner(holder) == player && classicNursery(xsGetUnitCopyId(holder)))
                            headroom--;
                    }
                }
            }
        }
    }
    if (headroom < 0) headroom = 0;
    xsSetGoal(101, unpowered);
    xsSetGoal(103, headroom);
}
'''
text+='\n'+Path('outputs/toolkit/classic_nursery_controller.xs').read_text()
# DE ignores the maps' resource-1997 effect: set the map identity from the map name instead.
patches=json.loads(Path('work/original-ai/translation.json').read_text())['map_patches']
text,_=identity_rewrite(text,{Path(p['file']).stem:p['identity'] for p in patches})
# Placement points for buildings that need power (classic_ai_power_placement.py).
text,_=power_points_rewrite(text)
path=root/'resources/_common/ai/SWGB Classic/swgb_classic_ai.xs';path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(text)
# Runtime copies for the bare-name AI include (see port_classic_ai.py).
for runtime in (root/'resources/_common/xs/swgb_classic_ai.xs',root/'resources/_common/ai/swgb_classic_ai.xs'):
    runtime.parent.mkdir(parents=True,exist_ok=True);runtime.write_text(text)
print('Generated Classic-only XS observer')
