// taskActiveGroupAttack continuation, connected to classic_group_state.xs.
// One synchronous context. Load stored group vectors before Begin; persist them
// after completion. The caller must deliver each task request before Continue.
// This is not a native order adapter and no installed rule invokes it.
int classicActiveHandle = 0;
int classicActiveRequest = 0; // 0 done, 1 taskGroup callback, 2 deferred selection
int classicActiveTask = -1;
int classicActiveForce = 0;
int classicActivePhase = 0;
int classicActiveDeferredGround = -1;
int classicActiveDeferredAir = -1;
int classicActiveTaskTime = 0;
int classicActiveTarget = -1;
int classicActiveType = -1;
vector classicActivePosition = cInvalidVector;
vector classicActiveHome = cInvalidVector;
vector classicActiveSavedHome = cInvalidVector;
vector classicActiveSelectedPosition = cInvalidVector;

// Signed interpretation of a wrapping 32-bit subtraction, then max(delta,0).
// Splitting into words prevents XS signed arithmetic overflow.
int classicActiveElapsed(int now = 0, int previous = 0) {
    int lowNow = now % 65536;
    int highNow = now / 65536;
    if (lowNow < 0) { lowNow = lowNow + 65536; highNow--; }
    int lowPrevious = previous % 65536;
    int highPrevious = previous / 65536;
    if (lowPrevious < 0) { lowPrevious = lowPrevious + 65536; highPrevious--; }
    int low = lowNow - lowPrevious;
    int high = highNow - highPrevious;
    if (low < 0) { low = low + 65536; high--; }
    high = (high % 65536 + 65536) % 65536;
    if (high >= 32768) return(0);
    return(high * 65536 + low);
}
bool classicActiveFlag(int handle = 0, int mask = 1) {
    // Low flag bits remain readable even when the signed word is negative.
    int low = (classicGroupGet(handle, 11) % 256 + 256) % 256;
    return(low / mask % 2 == 1);
}
bool classicActiveAttackEligible(int handle = 0, int attackEnabled = 0) {
    if (classicGroupValid(handle) == false) return(false);
    int kind = classicGroupGet(handle, 4);
    if (kind != 100 && kind != 102 && kind != 108) return(false);
    return(attackEnabled != 0 || classicActiveFlag(handle, 8));
}
bool classicActiveSelect(int target = -1, int targetType = -1,
    vector position = cInvalidVector) {
    if (classicActiveRequest == 1) return(false);
    classicActiveTarget = target;
    classicActiveType = targetType;
    classicActiveSelectedPosition = position;
    return(true);
}
void classicActiveStoreTarget(int action = 2) {
    classicGroupSet(classicActiveHandle, 7, action);
    classicGroupSet(classicActiveHandle, 8, classicActiveTarget);
    classicGroupSet(classicActiveHandle, 9, classicActiveType);
    classicGroupSet(classicActiveHandle, 10, 1);
    classicActivePosition = classicActiveSelectedPosition;
}
// Invoke after the original target/path selection boundary; flags may have
// changed during selection. A selected record may contain ID -1: presence is
// explicit and must not be inferred from the ID.
bool classicActiveAttackComplete(int handle = 0, int elapsed = 0, int now = 0,
    bool hasTarget = false, int needTransport = 0) {
    if (classicActiveRequest == 1 || classicGroupValid(handle) == false) return(false);
    classicActiveHandle = handle;
    classicActiveRequest = 0;
    classicActiveTask = -1;
    classicActivePhase = 0;
    if (classicActiveFlag(handle, 64)) {
        if (classicGroupGet(handle, 4) == 108) classicActiveDeferredAir = classicGroupGet(handle, 3);
        else classicActiveDeferredGround = classicGroupGet(handle, 3);
        classicActiveRequest = 2;
        return(true);
    }
    if (hasTarget == false) {
        if (elapsed < 5000) { classicGroupSet(handle, 7, 1); return(true); }
        if (classicActiveFlag(handle, 32)) classicActiveSavedHome = classicActiveHome;
        classicGroupSet(handle, 7, 18);
        classicActiveTaskTime = now;
        classicActiveTask = 18;
        classicActiveForce = 1;
        classicActivePhase = 1;
    } else {
        if (classicActiveFlag(handle, 32) == false)
            classicGroupSet(handle, 11, classicGroupGet(handle, 11) + 32);
        if (classicGroupGet(handle, 4) == 100 && needTransport == 1) {
            classicActiveTask = 12;
            classicActiveForce = 0;
            classicActivePhase = 2;
        } else {
            classicActiveStoreTarget(2);
            classicActiveTask = 2;
            classicActiveForce = 1;
            classicActivePhase = 3;
        }
    }
    classicActiveRequest = 1;
    return(true);
}
bool classicActiveTaskComplete() {
    if (classicActiveRequest != 1 || classicGroupValid(classicActiveHandle) == false) return(false);
    // Preserve source ordering: taskGroup executes BEFORE these mutations.
    if (classicActivePhase == 1) {
        classicGroupSet(classicActiveHandle, 10, 1);
        classicGroupSet(classicActiveHandle, 8, -1);
        classicGroupSet(classicActiveHandle, 9, -1);
        classicActivePosition = classicActiveHome;
    }
    if (classicActivePhase == 2) classicActiveStoreTarget(11);
    classicActiveRequest = 0;
    classicActivePhase = 0;
    return(true);
}
