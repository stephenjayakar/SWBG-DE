"""Generate discrete Astromech recovery for normal faction aircraft."""
from pathlib import Path
import csv,json
from reserved_unit_ids import de_unit_id

def integrate_astromech(script):
    def read(name):return list(csv.DictReader(open('work/faction-source/'+name+'.tsv'),delimiter='\t'))
    units={(r['civ'],int(r['id'])):r for r in read('units')}
    mechanics={(r['civ'],int(r['unit'])):r for r in read('unit-mechanics')}
    roster=json.loads(Path('outputs/faction-roster-report.json').read_text())
    def table(name):return list(csv.DictReader(open('work/'+name+'.tsv'),delimiter='\t'))
    resource_map={int(r['source']):int(r['target']) for r in table('faction-resource-mapping')}
    class_map={int(r['source']):int(r['target']) for r in table('faction-class-mapping')}
    assert resource_map[212]==2212
    assert [class_map[c] for c in (43,48,59)]==[13,0,20]
    eligible=set()
    for civ in ('1','3'):
        for r in roster[civ]['production_roster']:
            uid=r['id']
            if units[civ,uid]['class'] in ('43','48','59'):
                assert mechanics[civ,uid]['hero_mode']=='0', 'Avoid double-counting innate hero regeneration'
                eligible.add(uid)
    resources=read('resources')
    intervals=[float(r['value']) for r in resources if r['civ'] in ('1','3') and r['id']=='49']
    assert intervals==[2,2]
    assert not [r for r in read('effects') if r['type'] in ('1','6') and r['a']=='49']
    assert next(r for r in read('techs') if r['id']=='663')['effect']=='682'
    expected=[r for r in read('effects') if r['effect']=='682']
    assert [(r['type'],r['a'],r['d']) for r in expected]==[('1','212','1'),('1','214','1')]
    # xsGetUnitCopyId returns DE IDs: SWGB IDs in 900-999 are moved (reserved_unit_ids).
    condition=' || '.join(f'objectId == {de_unit_id(u)}' for u in sorted(eligible))
    addon='''// Astromech resource 212 is isolated at 2212 by the DAT adapter.
int swgbAirQuery = -1;
int swgbAirKeys = -1;
int swgbAirRemainders = -1;
int swgbAirLastSecond = -1;

bool swgbAstromechEligible(int objectId = -1) {
    return(CONDITION);
}

int swgbAirTimerSlot(int unit = -1) {
    int freeSlot = -1;
    for (slot = 0; < xsArrayGetSize(swgbAirKeys)) {
        int key = xsArrayGetInt(swgbAirKeys, slot);
        if (key == unit) return(slot);
        if (key < 0) freeSlot = slot;
    }
    if (freeSlot < 0) {
        freeSlot = xsArrayGetSize(swgbAirKeys);
        xsArrayResizeInt(swgbAirKeys, freeSlot + 1);
        xsArrayResizeFloat(swgbAirRemainders, freeSlot + 1);
    }
    xsArraySetInt(swgbAirKeys, freeSlot, unit);
    xsArraySetFloat(swgbAirRemainders, freeSlot, 0.0);
    return(freeSlot);
}

void swgbRepairAircraft(int unit = -1, float elapsed = 1.0) {
    if (xsDoesUnitExist(unit) == false) return;
    if (swgbAstromechEligible(xsGetUnitCopyId(unit)) == false) return;
    float health = xsGetUnitHitpoints(unit);
    float maximum = xsGetUnitAttribute(unit, cHitpoints);
    if (health < 1.0 || health >= maximum) return;
    int slot = swgbAirTimerSlot(unit);
    float remainder = xsArrayGetFloat(swgbAirRemainders, slot) + elapsed;
    // Source interval is two seconds, one HP per completed interval.
    while (remainder >= 2.0 && health < maximum) {
        remainder = remainder - 2.0;
        health = health + 1.0;
    }
    if (health > maximum) health = maximum;
    xsArraySetFloat(swgbAirRemainders, slot, remainder);
    xsSetUnitHitpoints(unit, health);
}

rule swgbAstromechTick
active
minInterval 1
maxInterval 1
{
    int now = xsGetGameTime();
    if (swgbAirLastSecond < 0) { swgbAirLastSecond = now; return; }
    if (now <= swgbAirLastSecond) return;
    float elapsed = now - swgbAirLastSecond;
    swgbAirLastSecond = now;
    // Reuse dead-unit slots so storage follows peak live aircraft, not total deaths.
    for (slot = 0; < xsArrayGetSize(swgbAirKeys)) {
        int unit = xsArrayGetInt(swgbAirKeys, slot);
        if (unit >= 0) {
            if (xsDoesUnitExist(unit) == false) xsArraySetInt(swgbAirKeys, slot, -1);
        }
    }
    int lastPlayer = xsGetNumPlayers();
    if (lastPlayer > 8) lastPlayer = 8;
    for (player = 1; <= lastPlayer) {
        if (xsGetPlayerInGame(player)) {
            if (xsPlayerAttribute(player, 2212) > 0.0) {
                // Commanded aircraft use military classes after the flight
                // crash repair. Explicit IDs exclude ordinary troops/ships.
                for (query = 0; < 3) {
                    int category = 913;
                    if (query == 1) category = 900;
                    if (query == 2) category = 920;
                    swgbAirQuery = xsGetPlayerUnitIds(player, category, swgbAirQuery);
                    if (swgbAirQuery >= 0) {
                        for (index = 0; < xsArrayGetSize(swgbAirQuery)) {
                            swgbRepairAircraft(xsArrayGetInt(swgbAirQuery, index), elapsed);
                        }
                    }
                }
            }
        }
    }
}

'''.replace('CONDITION',condition)
    assert script.count('void main() {')==1
    initialization='''void main() {
    swgbAirQuery = xsArrayCreateInt(1, -1, "swgb air query");
    swgbAirKeys = xsArrayCreateInt(1, -1, "swgb air timer keys");
    swgbAirRemainders = xsArrayCreateFloat(1, 0.0, "swgb air timers");
    swgbAirLastSecond = xsGetGameTime();'''
    script=addon+script.replace('void main() {',initialization)
    report=dict(eligible_unit_ids=sorted(eligible),source_classes=[43,48,59],source_interval_seconds=2,
                hp_per_interval=1,activation_resource=2212,original_nova_effect_preserved=True,
                engine_verified=False,limitations=['One-second XS sampling can shift recovery phase',
                'Save/load, conversions and large-army performance need runtime checks',
                'Scenario-only aircraft and innate hero regeneration are outside this adapter'])
    Path('outputs/faction-astromech-report.json').write_text(json.dumps(report,indent=2))
    return script
