// Compose source group state, pool admission and spatial planner.
// Requires classic_group_state.xs, classic_army_pool.xs, classic_air_planner.xs.
// Caller supplies owned source-classified objects, positions and pathing zones.
// Output is a stop-request queue. Native commands/targeting are not wired yet.
int classicDispatchStops = -1;
int classicDispatchStopCount = 0;
int classicDispatchCreated = 0;
int classicDispatchAddFailures = 0;
bool classicDispatchFirstMissing = false;

void classicDispatchBegin() {
    if (classicDispatchStops < 0)
        classicDispatchStops = xsArrayCreateInt(80, -1, "classic dispatch stop queue");
    classicDispatchStopCount = 0;
    classicDispatchCreated = 0;
    classicDispatchAddFailures = 0;
}
void classicDispatchPoolBegin() {
    classicDispatchFirstMissing = false;
    classicArmyPoolBegin();
    classicAirReset();
}
void classicDispatchCandidate(int player = 1, int unit = -1, bool aircraft = false,
    bool exists = false, int sourceClass = -1, int difficulty = 1,
    vector position = vector(0,0,0), int zone = 0) {
    int before = classicArmyPoolSize;
    classicArmyPoolConsider(unit, aircraft, exists, sourceClass,
        classicGroupContaining(player, unit) > 0, difficulty);
    if (classicArmyPoolSize > before) classicAirAddCandidate(unit, position, zone);
}
void classicDispatchBoatCandidate(int player = 1, int unit = -1, bool exists = false,
    vector position = vector(0,0,0), int zone = 0) {
    if (classicGroupContaining(player, unit) > 0) return;
    int before = classicArmyPoolSize;
    classicArmyPoolAppend(unit);
    if (classicArmyPoolSize == before) return;
    if (before == 0 && exists == false) classicDispatchFirstMissing = true;
    // Missing IDs consume slots in the original first-40 window.
    if (before < 40 && exists) classicAirAddCandidate(unit, position, zone);
}
void classicDispatchFinalize(int handle = 0, int difficulty = 1) {
    if (handle == 0) return;
    int size = classicGroupGet(handle, 5);
    classicGroupSet(handle, 6, size);
    if (difficulty >= 3) classicGroupSet(handle, 12, size / 2);
}
void classicDispatchPoolFinish(int player = 1, int kind = 100, int percentage = 75,
    int difficulty = 1, float radius = 20.0, int now = 0, int failAfter = -1) {
    if (percentage <= 0 || classicDispatchFirstMissing) return;
    int requested = (classicArmyPoolReported * percentage + 99) / 100;
    classicAirPlanCount(classicArmyPoolSize, requested, radius);
    int previous = -1;
    int handle = 0;
    for (i = 0; < classicAirSelectedCount) {
        int cluster = xsArrayGetInt(classicAirSelectedGroups, i);
        if (cluster != previous) {
            classicDispatchFinalize(handle, difficulty);
            handle = classicGroupCreate(player, 1, failAfter >= 0 && classicDispatchCreated >= failAfter);
            if (handle == 0) return;
            classicDispatchCreated++;
            classicGroupSet(handle, 4, kind);
            classicGroupSet(handle, 7, 1);
            classicGroupSet(handle, 11, 40);
            previous = cluster;
        }
        int unit = xsArrayGetInt(classicAirSelectedIds, i);
        // Source still queues stop if addUnit fails; expose that failure without
        // changing the source command sequence.
        if (classicGroupAdd(handle, unit, now) == 0) classicDispatchAddFailures++;
        if (classicDispatchStopCount >= xsArrayGetSize(classicDispatchStops))
            xsArrayResizeInt(classicDispatchStops, classicDispatchStopCount + 40);
        xsArraySetInt(classicDispatchStops, classicDispatchStopCount, unit);
        classicDispatchStopCount++;
    }
    classicDispatchFinalize(handle, difficulty);
}
