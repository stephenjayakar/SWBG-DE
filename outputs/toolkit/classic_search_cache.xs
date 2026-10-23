// Original UnitAI search (0x419EE0), over supplied source actor/cache state.
// Requires the visibility pipeline. Cache reset scheduling and notification
// delivery remain caller responsibilities; do not assume one reset per frame.
int classicSearchUsed = 0;
int classicSearchResult = 0;
int classicSearchSeedLo = 0;
int classicSearchSeedHi = 0;
int classicSearchSeen = 0;
float classicSearchTimer = 0.0;
int classicSearchActor = -1;
int classicSearchOwner = 0;
float classicSearchLOS = 0.0;
float classicSearchRadius = 0.0;
int classicSearchDesired = -1;
int classicSearchDesiredCount = 0;
int classicSearchRelations = -1;
int classicSearchOrder = 0;
int classicSearchFollowID = -1;
bool classicSearchWorld = false;
bool classicSearchFollowFound = false;
bool classicSearchFollowAction = false;
int classicSearchFollowOwner = 0;
float classicSearchFollowX = 0.0;
float classicSearchFollowY = 0.0;
float classicSearchFollowLOS = 0.0;
bool classicSearchQueried = false;
bool classicSearchNotifyPending = false;
int classicSearchQueryX = 0;
int classicSearchQueryY = 0;
int classicSearchQueryLOS = 0;
int classicSearchQueryOwner = 0;

// Search-related prefix of UnitAIModule::update (0x419250). Invoke at the
// actual source-equivalent UnitAI update boundary, including early exits.
// Other UnitAI fields/commands from that update remain separate components.
void classicSearchStartUpdate(float elapsed = 0.0) {
    classicSearchUsed = 0;
    classicSearchResult = 0;
    classicSearchTimer = classicSearchTimer+elapsed;
}

void classicSearchSetActor(int unit = -1, int owner = 0, float los = 0.0,
    float radius = 0.0, int desired = -1, int count = 0, int relations = -1,
    int order = 0, int followID = -1, bool world = false, float timer = 0.0, int seen = 0) {
    classicSearchActor = unit;
    classicSearchOwner = owner;
    classicSearchLOS = los;
    classicSearchRadius = radius;
    classicSearchDesired = desired;
    classicSearchDesiredCount = count;
    classicSearchRelations = relations;
    classicSearchOrder = order;
    classicSearchFollowID = followID;
    classicSearchWorld = world;
    classicSearchTimer = timer;
    classicSearchSeen = seen;
}
void classicSearchSetFollow(bool found = false, bool action = false, int owner = 0,
    float x = 0.0, float y = 0.0, float los = 0.0) {
    classicSearchFollowFound = found;
    classicSearchFollowAction = action;
    classicSearchFollowOwner = owner;
    classicSearchFollowX = x;
    classicSearchFollowY = y;
    classicSearchFollowLOS = los;
}

// Source rand() with 16-bit seed halves; intermediates fit signed 32-bit XS.
// This is the source RNG state supplied by the caller, not DE's native RNG.
int classicSearchRandom() {
    int lowProduct = classicSearchSeedLo*17405+2531011;
    int highProduct = classicSearchSeedHi*17405+classicSearchSeedLo*3+lowProduct/65536;
    classicSearchSeedLo = lowProduct%65536;
    classicSearchSeedHi = highProduct%65536;
    return(classicSearchSeedHi%32768);
}
// Source spatial inputs here are finite and fit int32 after truncation.
int classicSearchTruncate(float value = 0.0) {
    if (value < 0.0) return(xsCeilToInt(value));
    return(0-xsCeilToInt(0.0-value));
}

void classicSearchRun(float x = 0.0, float y = 0.0, int allowNotify = 0) {
    int savedDraw = classicSearchRandom();
    classicSearchQueried = false;
    classicSearchNotifyPending = false;
    if (classicSearchUsed != 1) {
        classicSearchUsed = 1;
        if (classicSearchDesired >= 0) {
            bool follow = classicSearchOrder == 701 && classicSearchFollowID != -1
                && classicSearchWorld && classicSearchFollowFound && classicSearchFollowAction;
            if (follow) {
                classicSearchQueryX = classicSearchTruncate(classicSearchFollowX);
                classicSearchQueryY = classicSearchTruncate(classicSearchFollowY);
                classicSearchQueryLOS = classicSearchTruncate(classicSearchFollowLOS);
                classicSearchQueryOwner = classicSearchFollowOwner;
            } else {
                classicSearchQueryX = classicSearchTruncate(x);
                classicSearchQueryY = classicSearchTruncate(y);
                classicSearchQueryLOS = classicSearchTruncate(classicSearchLOS)+1;
                int radius = classicSearchTruncate(classicSearchRadius);
                if (radius > classicSearchQueryLOS) classicSearchQueryLOS = radius;
                classicSearchQueryOwner = classicSearchOwner;
            }
            classicSearchQueried = true;
            classicSearchResult = classicVisibilityScan(classicSearchQueryX,classicSearchQueryY,
                classicSearchQueryLOS,classicSearchQueryOwner,classicSearchDesired,
                classicSearchDesiredCount,classicSearchRelations);
            if (follow == false) {
                classicSearchSeen = 0;
                if (xsArrayGetInt(classicVisibleCounts,4) > 0) classicSearchSeen = 1;
                if (classicSearchSeen == 1 && (allowNotify%256+256)%256 == 1) {
                    if (classicSearchTimer > 10.0) classicSearchNotifyPending = true;
                    classicSearchTimer = 0.0;
                }
            }
        }
    }
    // Original srand(savedDraw) runs even on a cached/null-desired return.
    classicSearchSeedLo = savedDraw;
    classicSearchSeedHi = 0;
}
