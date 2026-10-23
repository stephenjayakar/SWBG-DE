// Source objectToAttack2 candidate gates, before scoring/path selection.
// Inputs use SOURCE IDs/classes/flags. Caller must supply genuine observations;
// these helpers neither discover hidden units nor substitute DE unit classes.

bool classicAdmissionMemory(int unit = -1, int memoryOwner = 0, int wantedPlayer = -1,
                            bool exists = false, int ownerStatus = 0, int relation = 3,
                            int state = 2, float hp = 0.0) {
    if (unit == -1 || memoryOwner == 0) return(false);
    if (wantedPlayer != -1 && memoryOwner != wantedPlayer) return(false);
    if (exists == false || ownerStatus == 2 || relation == 1 || state > 2) return(false);
    // Source x87 equality also rejects unordered HP values.
    return(hp != 0.0 && hp == hp);
}

bool classicAdmissionVisibility(int masterType = 70, int visibility = 0,
                                int fogFlag = 0, int moving = 0) {
    if (masterType == 80) return(true);
    if (visibility == 0 || (visibility == 128 && fogFlag == 0)) return(false);
    return(moving != 1);
}

bool classicAdmissionWallTile(vector position = vector(0,0,0), int tileX = 0, int tileY = 0,
                              int width = 0, int height = 0) {
    if (tileX < 0 || tileY < 0 || tileX >= width || tileY >= height) return(false);
    float px = xsVectorGetX(position);
    float py = xsVectorGetY(position);
    int x = 0 - xsCeilToInt(0.0 - px);
    int y = 0 - xsCeilToInt(0.0 - py);
    if (px < 0.0) x = xsCeilToInt(px);
    if (py < 0.0) y = xsCeilToInt(py);
    return(tileX >= x - 3 && tileX <= x + 3 && tileY >= y - 3 && tileY <= y + 3);
}

bool classicAdmissionDomain(int landGroup = 1, bool boat = false, int masterType = 70,
                            int sourceId = -1, int sourceClass = -1, bool wallReachable = false,
                            int forceDifferentZone = 0, int targetZone = -1, int groupZone = -1) {
    if (landGroup == 1 && (boat || masterType == 45)) return(false);
    if (landGroup == 0 && boat == false && sourceId != 45) {
        if (sourceClass != 6 || wallReachable == false) return(false);
    }
    if (forceDifferentZone == 1 && landGroup == 1 && targetZone == groupZone) return(false);
    return(true);
}

bool classicAdmissionPolicy(int allMonks = 0, bool referenceMonk = false, bool monkUnitAI = false,
                            int convertible = 0, int difficulty = 1, int sourceClass = -1) {
    if (allMonks == 1 && referenceMonk && monkUnitAI && convertible == 0) return(false);
    if (difficulty >= 3 && sourceClass == 58) return(false);
    return(true);
}
