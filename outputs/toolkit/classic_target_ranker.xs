// Pure port of the source's seven target-ranking passes (0x592C30).
// Caller supplies source-compatible scores and admission/memory observations.
// A separate flag represents unordered scores without dividing by zero in XS.
int classicTargetIds = -1;
int classicTargetScores = -1;
int classicTargetUnordered = -1;
int classicTargetPreferred = -1;
int classicTargetWalls = -1;
int classicTargetSameZone = -1;
int classicTargetUsed = -1;
int classicTargetOrder = -1;
int classicTargetCount = 0;
int classicTargetOrderedCount = 0;

void classicTargetReset() {
    if (classicTargetIds < 0) {
        classicTargetIds = xsArrayCreateInt(1024, -1, "classic target ids");
        classicTargetScores = xsArrayCreateFloat(1024, 0.0, "classic target scores");
        classicTargetUnordered = xsArrayCreateBool(1024, false, "classic target unordered");
        classicTargetPreferred = xsArrayCreateBool(1024, false, "classic target preferred");
        classicTargetWalls = xsArrayCreateBool(1024, false, "classic target walls");
        classicTargetSameZone = xsArrayCreateBool(1024, false, "classic target zones");
        classicTargetUsed = xsArrayCreateBool(1024, false, "classic target used");
        classicTargetOrder = xsArrayCreateInt(1024, -1, "classic target order");
    }
    classicTargetCount = 0;
    classicTargetOrderedCount = 0;
}

bool classicTargetEconomicId(int sourceId = -1) {
    return(sourceId == 70 || sourceId == 562 || sourceId == 584 || sourceId == 323 ||
           sourceId == 103 || sourceId == 50 || sourceId == 209 || sourceId == 68);
}

void classicTargetAdd(int unit = -1, float score = 0.0, bool unordered = false,
                      int sourceClass = -1, int sourceId = -1, bool sameZone = true) {
    if (classicTargetCount >= 1024) return;
    int index = classicTargetCount;
    bool preferred = true;
    if ((sourceClass == 18 || sourceClass == 7) && classicTargetEconomicId(sourceId)) preferred = false;
    xsArraySetInt(classicTargetIds, index, unit);
    xsArraySetFloat(classicTargetScores, index, score);
    xsArraySetBool(classicTargetUnordered, index, unordered);
    xsArraySetBool(classicTargetPreferred, index, preferred);
    xsArraySetBool(classicTargetWalls, index, sourceClass == 6 || sourceClass == 8);
    xsArraySetBool(classicTargetSameZone, index, sameZone);
    classicTargetCount++;
}

bool classicTargetInTier(int index = 0, int tier = 0) {
    bool sameZone = xsArrayGetBool(classicTargetSameZone, index);
    bool wall = xsArrayGetBool(classicTargetWalls, index);
    bool preferred = xsArrayGetBool(classicTargetPreferred, index);
    if (tier == 0) return(xsArrayGetBool(classicTargetUnordered, index) == false &&
                          xsArrayGetFloat(classicTargetScores, index) >= 100.0);
    if (tier == 1) return(sameZone && wall == false && preferred);
    if (tier == 2) return(sameZone && wall == false && preferred == false);
    if (tier == 3) return(sameZone && wall && preferred);
    if (tier == 4) return(sameZone == false && wall == false && preferred);
    if (tier == 5) return(sameZone == false && wall == false && preferred == false);
    if (tier == 6) return(sameZone == false && wall && preferred);
    return(false);
}

void classicTargetRankTier(int tier = 0) {
    for (slot = 0; < classicTargetCount) {
        int best = -1;
        for (candidate = 0; < classicTargetCount) {
            if (xsArrayGetBool(classicTargetUsed, candidate) == false && classicTargetInTier(candidate, tier)) {
                bool replace = best < 0;
                if (best >= 0) {
                    replace = xsArrayGetBool(classicTargetUnordered, candidate) ||
                              xsArrayGetBool(classicTargetUnordered, best) ||
                              xsArrayGetFloat(classicTargetScores, candidate) > xsArrayGetFloat(classicTargetScores, best);
                }
                if (replace) best = candidate;
            }
        }
        if (best < 0) return;
        xsArraySetBool(classicTargetUsed, best, true);
        xsArraySetInt(classicTargetOrder, classicTargetOrderedCount, xsArrayGetInt(classicTargetIds, best));
        classicTargetOrderedCount++;
    }
}

void classicTargetRank() {
    classicTargetOrderedCount = 0;
    for (i = 0; < classicTargetCount) {
        xsArraySetBool(classicTargetUsed, i, false);
    }
    for (tier = 0; < 7) {
        classicTargetRankTier(tier);
    }
}
