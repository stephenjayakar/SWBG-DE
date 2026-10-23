// Per-player source tactical-group containers. Not installed or issuing orders.
// Opaque handles are slot+1; deleted slots are reused without changing list order.
// Records: owner,next,prev,id,kind,size,desired,action,target,targetType,inUse,
// flags,retreat,lastAdded, followed by 40 ordered member IDs. Stride is 54.
int classicGroups = -1;
int classicGroupHeads = -1;
int classicGroupTails = -1;
int classicGroupNextIds = -1;
int classicGroupCounts = -1;

int classicGroupGet(int handle = 0, int field = 0) {
    return(xsArrayGetInt(classicGroups, (handle - 1) * 54 + field));
}
void classicGroupSet(int handle = 0, int field = 0, int value = 0) {
    xsArraySetInt(classicGroups, (handle - 1) * 54 + field, value);
}
bool classicGroupValid(int handle = 0) {
    if (classicGroups < 0 || handle < 1) return(false);
    if (handle * 54 > xsArrayGetSize(classicGroups)) return(false);
    return(classicGroupGet(handle, 0) > 0);
}
void classicGroupsReset(int nextId = 1) {
    if (classicGroups < 0) {
        classicGroups = xsArrayCreateInt(432, 0, "classic tactical groups");
        classicGroupHeads = xsArrayCreateInt(9, 0, "classic group heads");
        classicGroupTails = xsArrayCreateInt(9, 0, "classic group tails");
        classicGroupNextIds = xsArrayCreateInt(9, 0, "classic group next ids");
        classicGroupCounts = xsArrayCreateInt(9, 0, "classic group counts");
    }
    for (i = 0; < xsArrayGetSize(classicGroups)) xsArraySetInt(classicGroups, i, 0);
    for (p = 0; < 9) {
        xsArraySetInt(classicGroupHeads, p, 0);
        xsArraySetInt(classicGroupTails, p, 0);
        xsArraySetInt(classicGroupNextIds, p, nextId);
        xsArraySetInt(classicGroupCounts, p, 0);
    }
}
int classicGroupCreate(int player = 1, int initialize = 1, bool allocationFailed = false) {
    if (player < 1 || player > 8 || allocationFailed) return(0);
    int handle = 1;
    while (handle * 54 <= xsArrayGetSize(classicGroups)) {
        if (classicGroupGet(handle, 0) == 0) break;
        handle++;
    }
    if (handle * 54 > xsArrayGetSize(classicGroups))
        xsArrayResizeInt(classicGroups, xsArrayGetSize(classicGroups) + 432);
    for (i = 0; < 54) classicGroupSet(handle, i, 0);
    classicGroupSet(handle, 0, player);
    classicGroupSet(handle, 3, -1);
    classicGroupSet(handle, 4, -1);
    classicGroupSet(handle, 8, -1);
    classicGroupSet(handle, 9, -1);
    classicGroupSet(handle, 11, 32);
    classicGroupSet(handle, 12, -1);
    for (i = 14; < 54) classicGroupSet(handle, i, -1);
    int tail = xsArrayGetInt(classicGroupTails, player);
    classicGroupSet(handle, 2, tail);
    if (tail > 0) classicGroupSet(tail, 1, handle);
    else xsArraySetInt(classicGroupHeads, player, handle);
    xsArraySetInt(classicGroupTails, player, handle);
    if (initialize == 1) {
        int id = xsArrayGetInt(classicGroupNextIds, player);
        classicGroupSet(handle, 3, id);
        xsArraySetInt(classicGroupNextIds, player, id + 1);
        xsArraySetInt(classicGroupCounts, player, xsArrayGetInt(classicGroupCounts, player) + 1);
    }
    return(handle);
}
int classicGroupAdd(int handle = 0, int unit = -1, int now = 0) {
    if (classicGroupValid(handle) == false) return(0);
    int count = classicGroupGet(handle, 5);
    if (count >= 40) return(0);
    classicGroupSet(handle, 14 + count, unit);
    classicGroupSet(handle, 5, count + 1);
    classicGroupSet(handle, 13, now);
    return(1);
}
int classicGroupRemove(int handle = 0, int unit = -1) {
    if (classicGroupValid(handle) == false) return(0);
    int count = classicGroupGet(handle, 5);
    int index = 0;
    while (index < count) {
        if (classicGroupGet(handle, 14 + index) == unit) break;
        index++;
    }
    if (index == count) return(0);
    while (index < count - 1) {
        classicGroupSet(handle, 14 + index, classicGroupGet(handle, 15 + index));
        index++;
    }
    classicGroupSet(handle, 14 + index, -1);
    classicGroupSet(handle, 5, count - 1);
    return(1);
}
void classicGroupUnlink(int handle = 0) {
    int player = classicGroupGet(handle, 0);
    int before = classicGroupGet(handle, 2);
    int after = classicGroupGet(handle, 1);
    if (before > 0) classicGroupSet(before, 1, after);
    else xsArraySetInt(classicGroupHeads, player, after);
    if (after > 0) classicGroupSet(after, 2, before);
    else xsArraySetInt(classicGroupTails, player, before);
    xsArraySetInt(classicGroupCounts, player, xsArrayGetInt(classicGroupCounts, player) - 1);
    classicGroupSet(handle, 0, 0);
}
int classicGroupDelete(int player = 1, int id = -1) {
    int handle = xsArrayGetInt(classicGroupHeads, player);
    while (handle > 0) {
        if (classicGroupGet(handle, 3) == id) {
            classicGroupUnlink(handle);
            return(1);
        }
        handle = classicGroupGet(handle, 1);
    }
    return(0);
}
int classicGroupDeleteKind(int player = 1, int kind = -1) {
    int handle = xsArrayGetInt(classicGroupHeads, player);
    while (handle > 0) {
        int after = classicGroupGet(handle, 1);
        if (kind == -1 || classicGroupGet(handle, 4) == kind) classicGroupUnlink(handle);
        handle = after;
    }
    return(1);
}
int classicGroupContaining(int player = 1, int unit = -1) {
    int handle = xsArrayGetInt(classicGroupHeads, player);
    while (handle > 0) {
        int count = classicGroupGet(handle, 5);
        for (i = 0; < count) {
            if (classicGroupGet(handle, 14 + i) == unit) return(handle);
        }
        handle = classicGroupGet(handle, 1);
    }
    return(0);
}
