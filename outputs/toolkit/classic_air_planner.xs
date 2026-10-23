// Pure aircraft selection layer. The caller supplies source-ordered eligible
// aircraft and zones; this file does not issue orders or claim target parity.
// Source routines: attackNow 0x5AE520, groupAIUnits 0x4506F0.
int classicAirIds = -1;
int classicAirPositions = -1;
int classicAirZones = -1;
int classicAirRemaining = -1;
int classicAirSelectedIds = -1;
int classicAirSelectedGroups = -1;
int classicAirCandidateCount = 0;
int classicAirSelectedCount = 0;

void classicAirReset() {
    if (classicAirIds < 0) {
        classicAirIds = xsArrayCreateInt(40, -1, "classic air candidates");
        classicAirPositions = xsArrayCreateVector(40, vector(0,0,0), "classic air positions");
        classicAirZones = xsArrayCreateInt(40, -1, "classic air zones");
        classicAirRemaining = xsArrayCreateBool(40, false, "classic air remaining");
        classicAirSelectedIds = xsArrayCreateInt(40, -1, "classic air selected ids");
        classicAirSelectedGroups = xsArrayCreateInt(40, -1, "classic air selected groups");
    }
    classicAirCandidateCount = 0;
    classicAirSelectedCount = 0;
}

void classicAirAddCandidate(int unit = -1, vector position = vector(0,0,0), int zone = -1) {
    if (classicAirCandidateCount >= 40) return;
    xsArraySetInt(classicAirIds, classicAirCandidateCount, unit);
    xsArraySetVector(classicAirPositions, classicAirCandidateCount, position);
    xsArraySetInt(classicAirZones, classicAirCandidateCount, zone);
    classicAirCandidateCount++;
}

int classicAirScalePercent(int value = 75, int difficulty = 0, bool noScaling = false) {
    if (value <= 0 || noScaling) return(value);
    // DE Extreme (-1) follows the source Hardest branch. Hard multiplayer does
    // not scale percentages; its separate group-size scaling is a different SN.
    float factor = 1.0;
    if (difficulty == 2) factor = 0.75;
    if (difficulty == 3) factor = 0.5;
    if (difficulty == 4) factor = 0.25;
    int scaled = 0 - xsCeilToInt(0.0 - factor * value);
    if (scaled < 1) scaled = 1;
    return(scaled);
}

bool classicAirNear(int a = 0, int b = 0, float radius = 20.0) {
    if (xsArrayGetInt(classicAirZones, a) != xsArrayGetInt(classicAirZones, b)) return(false);
    vector pa = xsArrayGetVector(classicAirPositions, a);
    vector pb = xsArrayGetVector(classicAirPositions, b);
    float dx = xsVectorGetX(pa) - xsVectorGetX(pb);
    float dy = xsVectorGetY(pa) - xsVectorGetY(pb);
    return(xsVectorLength(xsVectorSet(dx, dy, 0.0)) <= radius);
}

void classicAirSelect(int index = 0, int groupIndex = 0, int requested = 0) {
    xsArraySetBool(classicAirRemaining, index, false);
    if (classicAirSelectedCount < requested) {
        xsArraySetInt(classicAirSelectedIds, classicAirSelectedCount, xsArrayGetInt(classicAirIds, index));
        xsArraySetInt(classicAirSelectedGroups, classicAirSelectedCount, groupIndex);
        classicAirSelectedCount++;
    }
}

void classicAirPlanCount(int totalAvailable = 0, int requested = 0, float radius = 20.0) {
    classicAirSelectedCount = 0;
    if (totalAvailable <= 0 || requested <= 0 || classicAirCandidateCount <= 0) return;
    int remaining = classicAirCandidateCount;
    for (i = 0; < classicAirCandidateCount) {
        xsArraySetBool(classicAirRemaining, i, true);
    }
    for (groupIndex = 0; < 40) {
        int leader = -1;
        int bestNeighbors = 0;
        for (a = 0; < classicAirCandidateCount) {
            if (xsArrayGetBool(classicAirRemaining, a)) {
                int neighbors = 0;
                for (b = 0; < classicAirCandidateCount) {
                    if (xsArrayGetBool(classicAirRemaining, b) && classicAirNear(a, b, radius)) neighbors++;
                }
                // Strict > preserves source first-candidate tie breaking.
                if (neighbors > bestNeighbors) {
                    bestNeighbors = neighbors;
                    leader = a;
                }
            }
        }
        if (leader < 0) return;
        classicAirSelect(leader, groupIndex, requested);
        remaining--;
        for (i = 0; < classicAirCandidateCount) {
            if (xsArrayGetBool(classicAirRemaining, i) && classicAirNear(leader, i, radius)) {
                classicAirSelect(i, groupIndex, requested);
                remaining--;
            }
        }
        // Deliberately uses the full available count, even when only its first
        // 40 entries were considered. This preserves an original engine quirk.
        if (remaining <= totalAvailable - requested || remaining <= 0) return;
    }
}

void classicAirPlan(int totalAvailable = 0, int percentage = 75, float radius = 20.0) {
    // Positive integer ceiling matches source rounding over supported ranges.
    int requested = 0;
    if (percentage > 0) requested = (totalAvailable * percentage + 99) / 100;
    classicAirPlanCount(totalAvailable, requested, radius);
}
