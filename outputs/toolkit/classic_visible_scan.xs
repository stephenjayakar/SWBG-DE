// Original GetVisibleUnits (0x614A00), fed original category/record order.
// Requires generated distance table. This filters supplied known records;
// it does not discover native objects or reconstruct visibility membership.
int classicVisibleCounts = -1;
int classicVisibleIDs = -1;
int classicVisibleDetails = -1;
int classicVisiblePositions = -1;
int classicVisibleX = 0;
int classicVisibleY = 0;
int classicVisibleLOS = 0;
int classicVisibleTotal = 0;
bool classicVisibleActive = false;

void classicVisibleInit() {
    if (classicVisibleCounts >= 0) return;
    classicVisibleDistanceInit();
    classicVisibleCounts = xsArrayCreateInt(5, 0, "source visible counts");
    classicVisibleIDs = xsArrayCreateInt(1280, -1, "source visible IDs");
    classicVisibleDetails = xsArrayCreateInt(1280, 0, "source visible owner distance");
    classicVisiblePositions = xsArrayCreateInt(1280, 0, "source visible positions");
}

bool classicVisibleBegin(int x = 0, int y = 0, int los = 0,
    int player = 1, int players = 3, int desiredCount = 0) {
    classicVisibleInit();
    classicVisibleTotal = 0;
    classicVisibleActive = false;
    // Original early returns retain existing result buffers and counts.
    if (desiredCount <= 0 || player >= players) return(false);
    classicVisibleX = x;
    classicVisibleY = y;
    classicVisibleLOS = los;
    if (classicVisibleLOS > 15) classicVisibleLOS = 15;
    for (i = 0; < 5) xsArraySetInt(classicVisibleCounts, i, 0);
    classicVisibleActive = true;
    return(true);
}

// All record fields except ID are source bytes. Group comes from the supplied
// player relation map (0..4). These are caller preconditions, not remappings.
void classicVisibleAdd(int unit = -1, int radius = 0, int owner = 0,
    int x = 0, int y = 0, int bucket = 0) {
    if (classicVisibleActive == false) return;
    if (x < classicVisibleX-classicVisibleLOS-7 || x > classicVisibleX+classicVisibleLOS+7
        || y < classicVisibleY-classicVisibleLOS-7 || y > classicVisibleY+classicVisibleLOS+7) return;
    int dx = x-classicVisibleX;
    int dy = y-classicVisibleY;
    if (dx < 0) dx = 0-dx;
    if (dy < 0) dy = 0-dy;
    int distance = xsArrayGetInt(classicVisibleDistanceTable, (dy%32)*32+dx%32);
    if (distance > classicVisibleLOS) {
        distance = distance-radius;
        if (distance <= 0) distance = 1;
        else if (distance > classicVisibleLOS) return;
    }
    int count = xsArrayGetInt(classicVisibleCounts, bucket);
    if (count >= 256) return;
    int index = bucket*256+count;
    xsArraySetInt(classicVisibleIDs, index, unit);
    xsArraySetInt(classicVisibleDetails, index, distance+owner*256);
    xsArraySetInt(classicVisiblePositions, index, x+y*256);
    xsArraySetInt(classicVisibleCounts, bucket, count+1);
    classicVisibleTotal++;
}

int classicVisibleEnd() {
    classicVisibleActive = false;
    return(classicVisibleTotal);
}
