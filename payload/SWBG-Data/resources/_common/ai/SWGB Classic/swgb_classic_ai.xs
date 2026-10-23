// Invoked only by SWGB Classic AI. Goal slots 100..111 are reserved.
// 100: source max-unpowered threshold; 101: observed unpowered buildings;
// 102: requested source aircraft attack percent (DE has no separate air pool);
// 103: nursery headroom; 104: caller's player number.
// 105 reserved; 106..111: individual nursery command bridge below.
int classicBuildings = -1;
int classicOtherUnits = -1;
int classicWorkers = -1;
int classicAnimals = -1;
int classicEmitterPositions = -1;
int classicEmitterRanges = -1;
int classicLastTimes = -1;
int classicEmitterCount = 0;
bool classicPowerTarget(int id = -1) {
    return(id == 10 ||
           id == 14 ||
           id == 30 ||
           id == 31 ||
           id == 45 ||
           id == 47 ||
           id == 49 ||
           id == 51 ||
           id == 86 ||
           id == 87 ||
           id == 101 ||
           id == 104 ||
           id == 133 ||
           id == 150 ||
           id == 153 ||
           id == 317 ||
           id == 318 ||
           id == 319 ||
           id == 320 ||
           id == 321 ||
           id == 322 ||
           id == 335 ||
           id == 336 ||
           id == 337 ||
           id == 3342 ||
           id == 3343 ||
           id == 3550 ||
           id == 3551 ||
           id == 3552 ||
           id == 3553 ||
           id == 3582 ||
           id == 3583 ||
           id == 3584 ||
           id == 3585 ||
           id == 3586 ||
           id == 3587 ||
           id == 3588 ||
           id == 3589 ||
           id == 3590 ||
           id == 3591 ||
           id == 3592 ||
           id == 3593 ||
           id == 3594 ||
           id == 3595 ||
           id == 3596 ||
           id == 3597);
}
bool classicNursery(int id = -1) {
    return(id == 319 ||
           id == 320 ||
           id == 321 ||
           id == 322 ||
           id == 3550 ||
           id == 3551 ||
           id == 3552 ||
           id == 3553);
}
bool classicNurseryAnimal(int id = -1) {
    return(id == 594 ||
           id == 833 ||
           id == 4286 ||
           id == 4288 ||
           id == 4290 ||
           id == 4292 ||
           id == 4296 ||
           id == 4300 ||
           id == 4304 ||
           id == 4421 ||
           id == 7416 ||
           id == 7418 ||
           id == 7420 ||
           id == 7422 ||
           id == 7534 ||
           id == 7585 ||
           id == 7587 ||
           id == 7589 ||
           id == 7591 ||
           id == 7593 ||
           id == 7595 ||
           id == 7597 ||
           id == 7685 ||
           id == 7805);
}
bool classicAnimalFallback(int id = -1) {
    return(id == 68 ||
           id == 71 ||
           id == 109 ||
           id == 129 ||
           id == 130 ||
           id == 131 ||
           id == 141 ||
           id == 142 ||
           id == 3546 ||
           id == 3547 ||
           id == 3548 ||
           id == 3549 ||
           id == 3578 ||
           id == 3579 ||
           id == 3580 ||
           id == 3581 ||
           id == 3646 ||
           id == 3647 ||
           id == 3648 ||
           id == 3649 ||
           id == 3650 ||
           id == 3651 ||
           id == 3652 ||
           id == 3653 ||
           id == 4780 ||
           id == 4781 ||
           id == 4782 ||
           id == 4783);
}
float classicEmitterRange(int player = 1, int id = -1) {
    if (xsGetPlayerCivilization(player) == 1) {
        if (id == 12) return(10.0);
        if (id == 20) return(10.0);
        if (id == 132) return(10.0);
        if (id == 498) return(10.0);
        if (id == 1009) return(5.0);
        if (id == 1013) return(5.0);
        if (id == 3554) return(10.0);
        if (id == 3555) return(10.0);
        if (id == 3556) return(10.0);
        if (id == 3557) return(10.0);
    }
    if (xsGetPlayerCivilization(player) == 2) {
        if (id == 12) return(10.0);
        if (id == 20) return(10.0);
        if (id == 132) return(10.0);
        if (id == 498) return(10.0);
        if (id == 1009) return(5.0);
        if (id == 1013) return(5.0);
        if (id == 3554) return(10.0);
        if (id == 3555) return(10.0);
        if (id == 3556) return(10.0);
        if (id == 3557) return(10.0);
    }
    return(0.0);
}

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

// Classic AI map identity (resource 1997) from the map name; see classic_ai_map_identity.py.
// DE does not apply the maps' `effect_amount 1 1997 0 N`, so the observer sets the
// resource that the source map branches test, before any of them runs.
float classicMapIdentity(string name = "") {
    if (name == "SWGB Factions Arena") return(1.0);
    if (name == "SWGB Factions Desert") return(3.0);
    if (name == "SWGB Factions Flats") return(4.0);
    if (name == "SWGB Factions Forest") return(5.0);
    if (name == "SWGB Factions Ice Lake") return(7.0);
    if (name == "SWGB Factions LandMass") return(8.0);
    if (name == "SWGB Factions Islands") return(9.0);
    if (name == "SWGB Factions Large Sea") return(10.0);
    if (name == "SWGB Factions Motherlode") return(11.0);
    if (name == "SWGB Factions Nova Assault") return(12.0);
    if (name == "SWGB Factions Nova Lake") return(13.0);
    if (name == "SWGB Factions Precipice") return(15.0);
    if (name == "SWGB Factions Rivers") return(17.0);
    if (name == "SWGB Factions Savannah") return(18.0);
    if (name == "SWGB Factions Sea") return(19.0);
    if (name == "SWGB Factions Shoreline") return(21.0);
    if (name == "SWGB Factions Swamp") return(43.0);
    if (name == "SWGB Factions Team Islands") return(44.0);
    if (name == "SWGB Factions Tundra") return(46.0);
    if (name == "SWGB Factions WaterMass") return(47.0);
    return(0.0);
}

void classicSetMapIdentity(int player = 1) {
    if (xsPlayerAttribute(player, 1997) != 0.0) return;
    float identity = classicMapIdentity(xsGetMapName(false));
    if (identity > 0.0) xsSetPlayerAttribute(player, 1997, identity);
}
// End of Classic AI map identity.

// Power placement point (goals 121/122); see classic_ai_power_placement.py.
// The Power Core (finished or not) with the fewest power-dependent buildings in range,
// else the Command Center, else a worker; -1 if the player has none of these.
// It also collects the power emitters for the unpowered count (goal 101): DE powers a
// building when the gap between the two collision boxes is less than the aura range.
int classicAuraPositions = -1;
int classicAuraHalves = -1;
int classicAuraRanges = -1;
int classicAuraCount = 0;
int classicNewestCore = -1;
bool classicPowerCore(int id = -1) {
    return(id == 12 ||
           id == 20 ||
           id == 132 ||
           id == 498 ||
           id == 3554 ||
           id == 3555 ||
           id == 3556 ||
           id == 3557);
}
bool classicMainBuilding(int id = -1) {
    return(id == 109 ||
           id == 71 ||
           id == 141 ||
           id == 142 ||
           id == 3578 ||
           id == 3579 ||
           id == 3580 ||
           id == 3581 ||
           id == 3646 ||
           id == 3647 ||
           id == 3648 ||
           id == 3649 ||
           id == 3650 ||
           id == 3651 ||
           id == 3652 ||
           id == 3653 ||
           id == 4780 ||
           id == 4781 ||
           id == 4782 ||
           id == 4783);
}
bool classicShipyard(int id = -1) {
    return(id == 45 ||
           id == 47 ||
           id == 51 ||
           id == 133 ||
           id == 3586 ||
           id == 3587 ||
           id == 3588 ||
           id == 3589);
}
float classicHalfSize(int id = -1) {
    if (id == 319 ||
        id == 320 ||
        id == 321 ||
        id == 322 ||
        id == 3550 ||
        id == 3551 ||
        id == 3552 ||
        id == 3553) return(1.0);
    if (id == 10 ||
        id == 14 ||
        id == 30 ||
        id == 31 ||
        id == 45 ||
        id == 47 ||
        id == 51 ||
        id == 87 ||
        id == 104 ||
        id == 133 ||
        id == 335 ||
        id == 336 ||
        id == 337 ||
        id == 3582 ||
        id == 3583 ||
        id == 3584 ||
        id == 3585 ||
        id == 3586 ||
        id == 3587 ||
        id == 3588 ||
        id == 3589 ||
        id == 3593 ||
        id == 3594 ||
        id == 3595) return(1.5);
    if (id == 49 ||
        id == 86 ||
        id == 101 ||
        id == 150 ||
        id == 153 ||
        id == 317 ||
        id == 318 ||
        id == 3342 ||
        id == 3343 ||
        id == 3590 ||
        id == 3591 ||
        id == 3592 ||
        id == 3596 ||
        id == 3597) return(2.0);
    return(1.5);
}
float classicEmitterHalfSize(int id = -1) {
    if (id == 1009 ||
        id == 1013) return(0.2);
    if (id == 12 ||
        id == 20 ||
        id == 132 ||
        id == 498 ||
        id == 3554 ||
        id == 3555 ||
        id == 3556 ||
        id == 3557) return(0.5);
    return(0.5);
}
float classicGap(float d = 0.0, float halves = 0.0) {
    if (d < 0.0) d = 0.0 - d;
    d = d - halves;
    if (d < 0.0) return(0.0);
    return(d);
}
bool classicInAura(vector a = vector(0,0,0), float ha = 0.0, vector b = vector(0,0,0), float hb = 0.0, float range = 10.0) {
    float gx = classicGap(xsVectorGetX(a) - xsVectorGetX(b), ha + hb);
    float gy = classicGap(xsVectorGetY(a) - xsVectorGetY(b), ha + hb);
    return(gx*gx + gy*gy < range*range);
}
void classicAddAuras(int player = 1, int array = -1) {
    if (array < 0) return;
    for (i = 0; < xsArrayGetSize(array)) {
        int unit = xsArrayGetInt(array, i);
        if (xsDoesUnitExist(unit)) {
            int id = xsGetUnitCopyId(unit);
            float range = classicEmitterRange(player, id);
            if (range > 0.0) {
                bool ready = true;
                if (xsGetUnitType(unit) == 80) ready = classicFinished(unit);
                if (ready) {
                    if (classicAuraCount >= xsArrayGetSize(classicAuraPositions)) {
                        xsArrayResizeVector(classicAuraPositions, classicAuraCount + 1);
                        xsArrayResizeFloat(classicAuraHalves, classicAuraCount + 1);
                        xsArrayResizeFloat(classicAuraRanges, classicAuraCount + 1);
                    }
                    xsArraySetVector(classicAuraPositions, classicAuraCount, xsGetUnitPosition(unit));
                    xsArraySetFloat(classicAuraHalves, classicAuraCount, classicEmitterHalfSize(id));
                    xsArraySetFloat(classicAuraRanges, classicAuraCount, range);
                    classicAuraCount++;
                }
            }
        }
    }
}
// Goal 101 counts a finished power target unless a core reaches it, it is a Nursery or a
// Shipyard (placed away from the cores, so a new core cannot reach it), or it was already
// there when the newest core was placed (one core per unpowered building, not one a minute).
bool classicCountsUnpowered(int unit = -1, int id = -1) {
    if (classicNursery(id) || classicShipyard(id)) return(false);
    if (unit <= classicNewestCore) return(false);
    vector at = xsGetUnitPosition(unit);
    float half = classicHalfSize(id);
    for (j = 0; < classicAuraCount) {
        if (classicInAura(at, half, xsArrayGetVector(classicAuraPositions, j),
                          xsArrayGetFloat(classicAuraHalves, j), xsArrayGetFloat(classicAuraRanges, j)))
            return(false);
    }
    return(true);
}
void classicSetPowerPoint(int player = 1) {
    vector home = vector(-1,-1,-1);
    vector core = vector(-1,-1,-1);
    int fewest = 1000000;
    if (classicAuraPositions < 0) {
        classicAuraPositions = xsArrayCreateVector(1, vector(0,0,0), "classic aura positions");
        classicAuraHalves = xsArrayCreateFloat(1, 0.0, "classic aura half sizes");
        classicAuraRanges = xsArrayCreateFloat(1, 0.0, "classic aura ranges");
    }
    classicAuraCount = 0;
    classicAddAuras(player, classicBuildings);
    classicAddAuras(player, classicOtherUnits);
    classicNewestCore = -1;
    if (classicWorkers >= 0) {
        if (xsArrayGetSize(classicWorkers) > 0) home = xsGetUnitPosition(xsArrayGetInt(classicWorkers, 0));
    }
    if (classicBuildings >= 0) {
        int n = xsArrayGetSize(classicBuildings);
        for (i = 0; < n) {
            int unit = xsArrayGetInt(classicBuildings, i);
            if (xsDoesUnitExist(unit)) {
                int id = xsGetUnitCopyId(unit);
                vector at = xsGetUnitPosition(unit);
                if (classicMainBuilding(id)) home = at;
                if (classicPowerCore(id)) {
                    if (unit > classicNewestCore) classicNewestCore = unit;
                    int load = 0;
                    for (j = 0; < n) {
                        int other = xsArrayGetInt(classicBuildings, j);
                        if (xsDoesUnitExist(other)) {
                            int otherId = xsGetUnitCopyId(other);
                            if (classicPowerTarget(otherId) && classicNursery(otherId) == false) {
                                if (classicInAura(xsGetUnitPosition(other), classicHalfSize(otherId), at,
                                                  classicEmitterHalfSize(id), 10.0)) load++;
                            }
                        }
                    }
                    if (load <= fewest) {
                        fewest = load;
                        core = at;
                    }
                }
            }
        }
    }
    if (xsVectorGetX(core) < 0.0) core = home;
    if (xsVectorGetX(core) < 0.0) {
        xsSetGoal(121, -1);
        xsSetGoal(122, -1);
        return;
    }
    xsSetGoal(121, xsCeilToInt(xsVectorGetX(core) - 0.5));
    xsSetGoal(122, xsCeilToInt(xsVectorGetY(core) - 0.5));
}
// End of power placement point.

void swgbClassicObserve() {
    int player = xsGetGoal(104);
    if (player < 1 || player > 8) return;
    classicSetMapIdentity(player);
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
    classicSetPowerPoint(player);
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
                    if (classicCountsUnpowered(unit, id)) unpowered++;
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

// Original Artifact::update nursery policy, bridged to PER unit commands.
// Shared helpers: classicFinished, classicNursery, classicNurseryAnimal,
// classicAnimalFallback. Goal 104 is the calling player; 106..111 are private.
// 106 animal, 107 destination, 108 action (7 enter / 1 move),
// 109 current unit-AI action, 110 current order, 111 destination occupants.
int classicNurseryQueue = -1;
int classicNurseryBuildings = -1;
int classicNurseryTimes = -1;
int classicNurseryCursor = 0;
int classicNurseryQueueCount = 0;

void swgbClassicNurseryBegin() {
    classicNurseryCursor = 0;
    classicNurseryQueueCount = 0;
    int player = xsGetGoal(104);
    if (player < 1 || player > 8) return;
    if (classicNurseryTimes < 0)
        classicNurseryTimes = xsArrayCreateInt(9, -1, "classic animal decision times");
    int now = xsGetGameTime();
    if (xsArrayGetInt(classicNurseryTimes, player) == now) return;
    xsArraySetInt(classicNurseryTimes, player, now);
    classicNurseryQueue = xsGetPlayerUnitIds(player, 958, classicNurseryQueue);
    classicNurseryBuildings = xsGetPlayerUnitIds(player, 903, classicNurseryBuildings);
    if (classicNurseryQueue >= 0) classicNurseryQueueCount = xsArrayGetSize(classicNurseryQueue);
}

void swgbClassicNurseryNext() {
    xsSetGoal(106, -1);
    xsSetGoal(107, -1);
    xsSetGoal(108, -1);
    xsSetGoal(109, -2);
    xsSetGoal(110, -2);
    xsSetGoal(111, -1);
    int start = classicNurseryCursor;
    for (i = start; < classicNurseryQueueCount) {
        classicNurseryCursor = i + 1;
        int animal = xsArrayGetInt(classicNurseryQueue, i);
        if (xsDoesUnitExist(animal)) {
            if (xsGetUnitOwner(animal) == xsGetGoal(104) &&
                xsGetGarrisonedInUnitId(animal) < 0 &&
                classicNurseryAnimal(xsGetUnitCopyId(animal))) {
                xsSetGoal(106, animal);
                return;
            }
        }
    }
}

int classicNurseryNearest(int animal = -1, int exclude = -1, bool fallback = false) {
    if (classicNurseryBuildings < 0 || xsDoesUnitExist(animal) == false) return(-1);
    vector position = xsGetUnitPosition(animal);
    int best = -1;
    float bestDistance = -1.0;
    for (i = 0; < xsArrayGetSize(classicNurseryBuildings)) {
        int building = xsArrayGetInt(classicNurseryBuildings, i);
        if (building != exclude && classicFinished(building)) {
            if (xsGetUnitOwner(building) == xsGetGoal(104)) {
                int id = xsGetUnitCopyId(building);
                bool eligible = classicNursery(id);
                if (fallback) eligible = classicAnimalFallback(id);
                if (eligible) {
                    vector other = xsGetUnitPosition(building);
                    float dx = xsVectorGetX(position) - xsVectorGetX(other);
                    float dy = xsVectorGetY(position) - xsVectorGetY(other);
                    float distance = dx*dx + dy*dy;
                    if (best < 0 || distance < bestDistance) {
                        best = building;
                        bestDistance = distance;
                    }
                }
            }
        }
    }
    return(best);
}

void swgbClassicNurseryChoose() {
    int animal = xsGetGoal(106);
    int destination = classicNurseryNearest(animal);
    int action = 7;
    if (destination < 0) {
        destination = classicNurseryNearest(animal, -1, true);
        action = 1;
    }
    xsSetGoal(107, destination);
    xsSetGoal(108, action);
}

void swgbClassicNurseryCapacity() {
    int destination = xsGetGoal(107);
    if (xsDoesUnitExist(destination) == false) {
        xsSetGoal(107, -1);
        return;
    }
    int used = xsGetGoal(111);
    if (used < 0) {
        xsSetGoal(107, -1);
        return;
    }
    if (used >= xsGetUnitAttribute(destination, cGarrisonCapacity)) {
        // Source checks only the first nursery's capacity. If that is full,
        // it requests entry to the next nearest without checking it again.
        xsSetGoal(107, classicNurseryNearest(xsGetGoal(106), destination));
    }
}
