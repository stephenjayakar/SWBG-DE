// Compose original list membership with GetVisibleUnits result ordering.
// Requires membership, generated distance table and visible scan modules.
void classicVisibilityReset(int players = 0, int categories = 0) {
    classicVMemberInit(players, categories);
    classicVisibleInit();
    for (i = 0; < 5) xsArraySetInt(classicVisibleCounts, i, 0);
    classicVisibleTotal = 0;
    classicVisibleActive = false;
}

// Desired categories and relation map must be valid source arrays, and player
// nonnegative. Native events/cache gating remain separate from this query.
int classicVisibilityScan(int x = 0, int y = 0, int los = 0, int player = 0,
    int desired = -1, int desiredCount = 0, int relations = -1) {
    if (classicVisibleBegin(x,y,los,player,classicVMemberPlayers,desiredCount) == false) return(0);
    for (i = 0; < desiredCount) {
        int category = xsArrayGetInt(desired, i);
        int list = player*classicVMemberCategories+category;
        int base = xsArrayGetInt(classicVMemberBases, list);
        int count = xsArrayGetInt(classicVMemberCounts, list);
        for (j = 0; < count) {
            int at = base+j;
            int detail = xsArrayGetInt(classicVMemberDetails, at);
            int position = xsArrayGetInt(classicVMemberPositions, at);
            int owner = detail/256;
            classicVisibleAdd(xsArrayGetInt(classicVMemberIDs,at), detail%256, owner,
                position%256, position/256, xsArrayGetInt(relations,owner));
        }
    }
    return(classicVisibleEnd());
}
