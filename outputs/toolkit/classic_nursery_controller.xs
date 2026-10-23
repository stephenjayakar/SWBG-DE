// Original Artifact::update nursery policy, bridged to PER unit commands.
// Shared helpers: classicFinished, classicNursery, classicNurseryAnimal,
// classicAnimalFallback. Goal 104 is the calling player; 106..111 are private.
// 106 animal, 107 destination, 108 action (7 enter / 1 move),
// 109 current unit-AI action, 110 current order, 111 destination occupants.
int classicNurseryQueue = -1;
int classicNurseryBuildings = -1;
int classicNurseryTimes = -1;
int classicNurseryCursor = 0;
int classicNurseryQueueCount = 0;

void swgbClassicNurseryBegin() {
    classicNurseryCursor = 0;
    classicNurseryQueueCount = 0;
    int player = xsGetGoal(104);
    if (player < 1 || player > 8) return;
    if (classicNurseryTimes < 0)
        classicNurseryTimes = xsArrayCreateInt(9, -1, "classic animal decision times");
    int now = xsGetGameTime();
    if (xsArrayGetInt(classicNurseryTimes, player) == now) return;
    xsArraySetInt(classicNurseryTimes, player, now);
    classicNurseryQueue = xsGetPlayerUnitIds(player, 958, classicNurseryQueue);
    classicNurseryBuildings = xsGetPlayerUnitIds(player, 903, classicNurseryBuildings);
    if (classicNurseryQueue >= 0) classicNurseryQueueCount = xsArrayGetSize(classicNurseryQueue);
}

void swgbClassicNurseryNext() {
    xsSetGoal(106, -1);
    xsSetGoal(107, -1);
    xsSetGoal(108, -1);
    xsSetGoal(109, -2);
    xsSetGoal(110, -2);
    xsSetGoal(111, -1);
    int start = classicNurseryCursor;
    for (i = start; < classicNurseryQueueCount) {
        classicNurseryCursor = i + 1;
        int animal = xsArrayGetInt(classicNurseryQueue, i);
        if (xsDoesUnitExist(animal)) {
            if (xsGetUnitOwner(animal) == xsGetGoal(104) &&
                xsGetGarrisonedInUnitId(animal) < 0 &&
                classicNurseryAnimal(xsGetUnitCopyId(animal))) {
                xsSetGoal(106, animal);
                return;
            }
        }
    }
}

int classicNurseryNearest(int animal = -1, int exclude = -1, bool fallback = false) {
    if (classicNurseryBuildings < 0 || xsDoesUnitExist(animal) == false) return(-1);
    vector position = xsGetUnitPosition(animal);
    int best = -1;
    float bestDistance = -1.0;
    for (i = 0; < xsArrayGetSize(classicNurseryBuildings)) {
        int building = xsArrayGetInt(classicNurseryBuildings, i);
        if (building != exclude && classicFinished(building)) {
            if (xsGetUnitOwner(building) == xsGetGoal(104)) {
                int id = xsGetUnitCopyId(building);
                bool eligible = classicNursery(id);
                if (fallback) eligible = classicAnimalFallback(id);
                if (eligible) {
                    vector other = xsGetUnitPosition(building);
                    float dx = xsVectorGetX(position) - xsVectorGetX(other);
                    float dy = xsVectorGetY(position) - xsVectorGetY(other);
                    float distance = dx*dx + dy*dy;
                    if (best < 0 || distance < bestDistance) {
                        best = building;
                        bestDistance = distance;
                    }
                }
            }
        }
    }
    return(best);
}

void swgbClassicNurseryChoose() {
    int animal = xsGetGoal(106);
    int destination = classicNurseryNearest(animal);
    int action = 7;
    if (destination < 0) {
        destination = classicNurseryNearest(animal, -1, true);
        action = 1;
    }
    xsSetGoal(107, destination);
    xsSetGoal(108, action);
}

void swgbClassicNurseryCapacity() {
    int destination = xsGetGoal(107);
    if (xsDoesUnitExist(destination) == false) {
        xsSetGoal(107, -1);
        return;
    }
    int used = xsGetGoal(111);
    if (used < 0) {
        xsSetGoal(107, -1);
        return;
    }
    if (used >= xsGetUnitAttribute(destination, cGarrisonCapacity)) {
        // Source checks only the first nursery's capacity. If that is full,
        // it requests entry to the next nearest without checking it again.
        xsSetGoal(107, classicNurseryNearest(xsGetGoal(106), destination));
    }
}
