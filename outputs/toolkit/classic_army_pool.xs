// Source attack-pool admission; caller supplies original class and group state.
// Scratch queue must be consumed/copied before beginning another player's pool.
// Not installed: live source group ownership is still required from the caller.
int classicArmyPoolIds = -1;
int classicArmyPoolSize = 0;
int classicArmyPoolReported = 0;

bool classicArmyPoolEligible(bool aircraft = false, bool exists = false,
    int sourceClass = -1, bool grouped = false, int difficulty = 1) {
    if (exists == false || grouped) return(false);
    if (aircraft) return(sourceClass != 59);
    if (sourceClass == 51) return(false);
    if (difficulty > 2 && sourceClass == 50) return(false);
    return(true);
}

void classicArmyPoolBegin() {
    if (classicArmyPoolIds < 0)
        classicArmyPoolIds = xsArrayCreateInt(40, -1, "classic army admission queue");
    classicArmyPoolSize = 0;
    classicArmyPoolReported = 0;
}

void classicArmyPoolAppend(int unit = -1) {
    classicArmyPoolReported++;
    for (i = 0; < classicArmyPoolSize) {
        if (xsArrayGetInt(classicArmyPoolIds, i) == unit) return;
    }
    if (classicArmyPoolSize >= xsArrayGetSize(classicArmyPoolIds))
        xsArrayResizeInt(classicArmyPoolIds, classicArmyPoolSize + 32);
    xsArraySetInt(classicArmyPoolIds, classicArmyPoolSize, unit);
    classicArmyPoolSize++;
}

void classicArmyPoolConsider(int unit = -1, bool aircraft = false,
    bool exists = false, int sourceClass = -1, bool grouped = false,
    int difficulty = 1) {
    if (classicArmyPoolEligible(aircraft, exists, sourceClass, grouped, difficulty) == false) return;
    classicArmyPoolAppend(unit);
}
