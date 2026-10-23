// Resumable source post-ranking decisions. Geometry is an external adapter.
// Request: 0=advance, 1=direct path, 2=transport path, 3=obstruction path,
// 4=exception terrain, 5=plain retry, 6=collect blockers, 7=finished/yielded.
// Caller saves per-player/per-group state between invocations. This single
// scratch context must not be interleaved between groups or players.
int classicPathIds = -1;
int classicPathZones = -1;
int classicPathExists = -1;
int classicPathBlockers = -1;
int classicPathCount = 0;
int classicPathBlockerCount = 0;
int classicPathIndex = 0;
int classicPathStart = 0;
int classicPathCanTransport = 0;
int classicPathSN241 = 0;
int classicPathRequest = 7;
int classicPathTerrainIndex = 0;
int classicPathSelected = -1;
int classicPathSameZone = -1;
int classicPathNeedTransport = -1;
int classicPathResume = -1;
int classicPathAttempt = -1;
float classicPathRadius = 16.0;

void classicPathReset() {
    if (classicPathIds < 0) {
        classicPathIds = xsArrayCreateInt(1024, -1, "classic path targets");
        classicPathZones = xsArrayCreateInt(1024, -1, "classic path zones");
        classicPathExists = xsArrayCreateBool(1024, false, "classic path existence");
        classicPathBlockers = xsArrayCreateInt(19, -1, "classic path blockers");
    }
    classicPathCount = 0;
    classicPathBlockerCount = 0;
    classicPathSelected = -1;
    classicPathSameZone = -1;
    classicPathNeedTransport = -1;
    classicPathResume = -1;
    classicPathAttempt = -1;
    classicPathRadius = 16.0;
    classicPathRequest = 7;
}

void classicPathAdd(int unit = -1, int sameZone = 1, bool exists = true) {
    if (classicPathCount >= 1024) return;
    xsArraySetInt(classicPathIds, classicPathCount, unit);
    xsArraySetInt(classicPathZones, classicPathCount, sameZone);
    xsArraySetBool(classicPathExists, classicPathCount, exists);
    classicPathCount++;
}

void classicPathAddRange(float value = 16.0, bool exists = true) {
    if (exists == false) return;
    if (value < classicPathRadius || value != value || classicPathRadius != classicPathRadius)
        classicPathRadius = value;
}

void classicPathBegin(int canTransport = 0, int sn241 = 0, int resume = 0) {
    classicPathCanTransport = canTransport;
    classicPathSN241 = sn241;
    classicPathIndex = resume;
    classicPathStart = resume;
    classicPathRequest = 0;
}

int classicPathUnit() {
    if (classicPathIndex < 0 || classicPathIndex >= classicPathCount) return(-1);
    return(xsArrayGetInt(classicPathIds, classicPathIndex));
}

void classicPathFinish(int needTransport = 0) {
    classicPathSelected = classicPathUnit();
    classicPathSameZone = xsArrayGetInt(classicPathZones, classicPathIndex);
    classicPathNeedTransport = needTransport;
    classicPathAttempt = classicPathSelected;
    classicPathResume = -1;
    classicPathRequest = 7;
}

void classicPathSkip() {
    classicPathIndex++;
    classicPathRequest = 0;
}

void classicPathStep(bool timeExpired = false) {
    if (classicPathRequest != 0) return;
    if (classicPathIndex < 0 || classicPathIndex >= classicPathCount) {
        classicPathRequest = 7;
        return;
    }
    // The source always tries the first entry of a new/resumed batch before
    // consulting its time budget, even if that first object no longer exists.
    if (classicPathIndex > classicPathStart && timeExpired) {
        classicPathResume = classicPathIndex;
        classicPathRequest = 7;
        return;
    }
    if (xsArrayGetBool(classicPathExists, classicPathIndex) == false) classicPathSkip();
    else classicPathRequest = 1;
}

void classicPathObstructionFallback() {
    if (xsArrayGetInt(classicPathZones, classicPathIndex) == 1) classicPathRequest = 3;
    else classicPathSkip();
}

int classicPathTerrain() {
    if (classicPathTerrainIndex == 0) return(1);
    if (classicPathTerrainIndex == 1) return(22);
    if (classicPathTerrainIndex == 2) return(23);
    if (classicPathTerrainIndex == 3) return(16);
    return(15);
}

void classicPathAnswer(int result = 0) {
    int zone = xsArrayGetInt(classicPathZones, classicPathIndex);
    if (classicPathRequest == 1) {
        if (result == 1) classicPathFinish(0);
        else if (classicPathCanTransport == 1 && (zone == 0 || (zone == 1 && classicPathSN241 == 0)))
            classicPathRequest = 2;
        else classicPathObstructionFallback();
    } else if (classicPathRequest == 2) {
        if (result == 1) {
            if (zone == 0) classicPathFinish(1);
            else {
                classicPathTerrainIndex = 0;
                classicPathRequest = 4;
            }
        } else classicPathObstructionFallback();
    } else if (classicPathRequest == 3) {
        if (result == 1) {
            classicPathBlockerCount = 0;
            classicPathRequest = 6;
        } else classicPathSkip();
    } else if (classicPathRequest == 4) {
        if (result != 0) classicPathFinish(1);
        else {
            classicPathTerrainIndex++;
            if (classicPathTerrainIndex >= 5) classicPathRequest = 5;
        }
    } else if (classicPathRequest == 5) {
        if (result != 0) classicPathFinish(0);
        else classicPathFinish(1);
    }
}

void classicPathAddBlocker(int unit = -1, bool exists = true) {
    if (classicPathRequest != 6 || exists == false || classicPathBlockerCount >= 19) return;
    xsArraySetInt(classicPathBlockers, classicPathBlockerCount, unit);
    classicPathBlockerCount++;
}

void classicPathFinishBlockers() {
    if (classicPathRequest != 6) return;
    classicPathAddBlocker(classicPathUnit());
    classicPathSelected = xsArrayGetInt(classicPathBlockers, 0);
    classicPathSameZone = xsArrayGetInt(classicPathZones, classicPathIndex);
    classicPathNeedTransport = 0;
    classicPathAttempt = -1;
    classicPathResume = -1;
    classicPathRequest = 7;
}
