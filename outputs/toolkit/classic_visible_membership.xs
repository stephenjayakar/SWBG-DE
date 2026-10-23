// Original visible-list membership from supplied visibility-mask events.
// Eight reusable arrays; list storage grows in segments and retains source order.
// Caller maintains the object lookup-presence flags used for pointer repair.
int classicVMemberPlayers = 0;
int classicVMemberCategories = 0;
int classicVMemberBases = -1;
int classicVMemberCounts = -1;
int classicVMemberCaps = -1;
int classicVMemberIDs = -1;
int classicVMemberDetails = -1;
int classicVMemberPositions = -1;
int classicVMemberPointers = -1;
int classicVMemberLookup = -1;
int classicVMemberPoolSize = 0;

void classicVMemberInit(int players = 0, int categories = 0) {
    if (classicVMemberBases < 0) {
        classicVMemberBases = xsArrayCreateInt(1, 0, "visible membership bases");
        classicVMemberCounts = xsArrayCreateInt(1, 0, "visible membership counts");
        classicVMemberCaps = xsArrayCreateInt(1, 0, "visible membership capacities");
        classicVMemberIDs = xsArrayCreateInt(1, 0, "visible membership IDs");
        classicVMemberDetails = xsArrayCreateInt(1, 0, "visible membership details");
        classicVMemberPositions = xsArrayCreateInt(1, 0, "visible membership positions");
        classicVMemberPointers = xsArrayCreateInt(1, -1, "visible object pointers");
        classicVMemberLookup = xsArrayCreateInt(1, 0, "visible object lookup");
    }
    classicVMemberPlayers = players;
    classicVMemberCategories = categories+1;
    int lists = players*classicVMemberCategories;
    int allocated = lists;
    if (allocated < 1) allocated = 1;
    xsArrayResizeInt(classicVMemberBases, allocated);
    xsArrayResizeInt(classicVMemberCounts, allocated);
    xsArrayResizeInt(classicVMemberCaps, allocated);
    for (i = 0; < lists) {
        xsArraySetInt(classicVMemberBases, i, i*64);
        xsArraySetInt(classicVMemberCounts, i, 0);
        xsArraySetInt(classicVMemberCaps, i, 64);
    }
    classicVMemberPoolSize = lists*64;
    allocated = classicVMemberPoolSize;
    if (allocated < 1) allocated = 1;
    xsArrayResizeInt(classicVMemberIDs, allocated);
    xsArrayResizeInt(classicVMemberDetails, allocated);
    xsArrayResizeInt(classicVMemberPositions, allocated);
    for (i = 0; < allocated) {
        xsArraySetInt(classicVMemberIDs, i, 0);
        xsArraySetInt(classicVMemberDetails, i, 0);
        xsArraySetInt(classicVMemberPositions, i, 0);
    }
    xsArrayResizeInt(classicVMemberPointers, 1);
    xsArraySetInt(classicVMemberPointers, 0, -1);
    xsArrayResizeInt(classicVMemberLookup, 1);
    xsArraySetInt(classicVMemberLookup, 0, 0);
}

void classicVMemberEnsureUnit(int unit = 0) {
    int size = xsArrayGetSize(classicVMemberPointers);
    int required = (unit+1)*classicVMemberPlayers;
    if (required > size) {
        xsArrayResizeInt(classicVMemberPointers, required);
        for (i = size; < required) xsArraySetInt(classicVMemberPointers, i, -1);
    }
    size = xsArrayGetSize(classicVMemberLookup);
    if (unit >= size) {
        xsArrayResizeInt(classicVMemberLookup, unit+1);
        for (i = size; < unit+1) xsArraySetInt(classicVMemberLookup, i, 0);
    }
}
void classicVMemberSetLookup(int unit = 0, bool present = false) {
    classicVMemberEnsureUnit(unit);
    if (present) xsArraySetInt(classicVMemberLookup, unit, 1);
    else xsArraySetInt(classicVMemberLookup, unit, 0);
}

void classicVMemberCopy(int destination = 0, int source = 0) {
    xsArraySetInt(classicVMemberIDs, destination, xsArrayGetInt(classicVMemberIDs, source));
    xsArraySetInt(classicVMemberDetails, destination, xsArrayGetInt(classicVMemberDetails, source));
    xsArraySetInt(classicVMemberPositions, destination, xsArrayGetInt(classicVMemberPositions, source));
}
void classicVMemberRepair(int index = 0, int player = 0) {
    int unit = xsArrayGetInt(classicVMemberIDs, index);
    if (unit < xsArrayGetSize(classicVMemberLookup) && xsArrayGetInt(classicVMemberLookup, unit) != 0)
        xsArraySetInt(classicVMemberPointers, unit*classicVMemberPlayers+player, index);
}

bool classicVMemberUpdate(int unit = 0, int owner = 0, int x = 0, int y = 0,
    int radius = 0, int category = 0, int priorMask = 0, int newMask = 0) {
    if (unit < 0 || category < 0) return(false);
    if (category >= classicVMemberCategories) return(true);
    classicVMemberEnsureUnit(unit);
    int oldBits = (priorMask%65536+65536)%65536;
    int newBits = (newMask%65536+65536)%65536;
    for (player = 0; < classicVMemberPlayers) {
        if (oldBits%2 != newBits%2) {
            int list = player*classicVMemberCategories+category;
            int base = xsArrayGetInt(classicVMemberBases, list);
            int count = xsArrayGetInt(classicVMemberCounts, list);
            int pointer = unit*classicVMemberPlayers+player;
            if (newBits%2 != 0) {
                int capacity = xsArrayGetInt(classicVMemberCaps, list);
                if (count == capacity) {
                    int next = classicVMemberPoolSize;
                    classicVMemberPoolSize = classicVMemberPoolSize+capacity*2;
                    xsArrayResizeInt(classicVMemberIDs, classicVMemberPoolSize);
                    xsArrayResizeInt(classicVMemberDetails, classicVMemberPoolSize);
                    xsArrayResizeInt(classicVMemberPositions, classicVMemberPoolSize);
                    for (i = 0; < count) {
                        classicVMemberCopy(next+i, base+i);
                        classicVMemberRepair(next+i, player);
                    }
                    base = next;
                    xsArraySetInt(classicVMemberBases, list, base);
                    xsArraySetInt(classicVMemberCaps, list, capacity*2);
                }
                int at = base+count;
                xsArraySetInt(classicVMemberIDs, at, unit);
                xsArraySetInt(classicVMemberDetails, at, (radius%256+256)%256+((owner%256+256)%256)*256);
                xsArraySetInt(classicVMemberPositions, at, (x%256+256)%256+((y%256+256)%256)*256);
                xsArraySetInt(classicVMemberPointers, pointer, at);
                xsArraySetInt(classicVMemberCounts, list, count+1);
            } else {
                int removed = xsArrayGetInt(classicVMemberPointers, pointer);
                // Source dereferences the supplied record pointer. Invalid
                // removal events are an explicit caller-precondition failure.
                if (removed < base || removed >= base+count) return(false);
                int last = base+count-1;
                if (removed != last) {
                    classicVMemberCopy(removed, last);
                    classicVMemberRepair(removed, player);
                }
                xsArraySetInt(classicVMemberPointers, pointer, -1);
                xsArraySetInt(classicVMemberCounts, list, count-1);
            }
        }
        oldBits = oldBits/2;
        newBits = newBits/2;
    }
    return(true);
}
