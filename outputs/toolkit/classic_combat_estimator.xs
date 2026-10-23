// Source addUnit combat aggregation (0x592430), prior to target scoring.
// Requires classic_target_scorer.xs arithmetic helpers and its ranker.
// Caller supplies source damageCapability/canConvert results in source order.
// No live damage/visibility queries or native unit commands are issued here.
int classicCombatIds = -1;
int classicCombatHP = -1;
int classicCombatReload = -1;
int classicCombatExists = -1;
int classicCombatIncoming = -1;
int classicCombatIncomingState = -1;
int classicCombatCount = 0;
int classicCombatEnemyCount = 0;
float classicCombatTargetHP = 0.0;
float classicCombatOutgoing = 0.0;
int classicCombatOutgoingState = 0;
float classicCombatTTK = 0.0;
float classicCombatTTBK = 0.0;
float classicCombatAccumulated = 0.0;
int classicCombatAccumulatedState = 0;
float classicCombatEpsilon = 0.0000001;

float classicCombatAddQuotient(float total = 0.0, float numerator = 0.0, float denominator = 1.0) {
    // The original adds the quotient before storing the accumulated float32.
    // Retain the quotient's rounding residual through that final addition.
    for (scale = 0; < 128) {
        if (numerator <= 1.0 && numerator >= -1.0 && denominator <= 1.0 && denominator >= -1.0) break;
        numerator = numerator * 0.5;
        denominator = denominator * 0.5;
    }
    float quotient = numerator / denominator;
    classicScoreMultiplyWide(quotient, denominator);
    float residual = numerator - classicScoreHi;
    residual = residual - classicScoreLo;
    float correction = residual / denominator;
    classicScoreAddWide(total, quotient);
    return(classicScoreHi + (classicScoreLo + correction));
}

void classicCombatAccumulate(float total = 0.0, int state = 0, float victimHP = 0.0,
    float damage = 0.0, float reload = 1.0, bool convertible = false) {
    // Nonfinite DPS is represented explicitly: 1 +infinity, -1 -infinity, 2 NaN.
    // This preserves zero-reload source branches without dividing by zero in XS.
    classicCombatAccumulated = total;
    classicCombatAccumulatedState = state;
    if (state == 2) return;
    bool conversion = (damage <= classicCombatEpsilon || damage != damage) && convertible;
    int amountState = 0;
    if (conversion == false) {
        if (damage != damage || reload != reload) amountState = 2;
        else if (reload == 0.0) {
            if (damage == 0.0) amountState = 2;
            else if (damage > 0.0) amountState = 1;
            else amountState = -1;
        }
    }
    if (amountState != 0) {
        if (amountState == 2 || (state != 0 && state != amountState)) classicCombatAccumulatedState = 2;
        else classicCombatAccumulatedState = amountState;
        return;
    }
    if (state != 0) return;
    if (conversion) {
        classicScoreMultiplyWide(victimHP, 0.1);
        float high = classicScoreHi;
        float low = classicScoreLo;
        classicScoreAddWide(total, high);
        classicCombatAccumulated = classicScoreHi + (classicScoreLo + low);
    } else classicCombatAccumulated = classicCombatAddQuotient(total, damage, reload);
}

void classicCombatReset() {
    if (classicCombatIds < 0) {
        classicCombatIds = xsArrayCreateInt(40, -1, "classic combat member ids");
        classicCombatHP = xsArrayCreateFloat(40, 0.0, "classic combat member hp");
        classicCombatReload = xsArrayCreateFloat(40, 0.0, "classic combat member reload");
        classicCombatExists = xsArrayCreateBool(40, false, "classic combat member existence");
        classicCombatIncoming = xsArrayCreateFloat(40, 0.0, "classic combat incoming dps");
        classicCombatIncomingState = xsArrayCreateInt(40, 0, "classic combat incoming dps state");
    }
    classicCombatCount = 0;
}
int classicCombatAddMember(int unit = -1, float hp = 100.0, float reload = 2.0, bool exists = true) {
    if (classicCombatCount >= 40) return(-1);
    int index = classicCombatCount;
    xsArraySetInt(classicCombatIds, index, unit);
    xsArraySetFloat(classicCombatHP, index, hp);
    xsArraySetFloat(classicCombatReload, index, reload);
    xsArraySetBool(classicCombatExists, index, exists);
    classicCombatCount++;
    return(index);
}
void classicCombatTargetBegin(float hp = 100.0, int enemyCount = 0) {
    classicCombatTargetHP = hp;
    classicCombatEnemyCount = enemyCount;
    classicCombatOutgoing = 0.0;
    classicCombatOutgoingState = 0;
    classicCombatTTK = 340282346638528859811704183484516925440.0;
    classicCombatTTBK = 0.0;
    for (i = 0; < classicCombatCount) {
        xsArraySetFloat(classicCombatIncoming, i, 0.0);
        xsArraySetInt(classicCombatIncomingState, i, 0);
    }
}
void classicCombatAddOutgoing(int member = 0, float damage = 0.0, bool convertible = false) {
    if (member < 0 || member >= classicCombatCount) return;
    if (xsArrayGetBool(classicCombatExists, member) == false) return;
    classicCombatAccumulate(classicCombatOutgoing, classicCombatOutgoingState, classicCombatTargetHP,
        damage, xsArrayGetFloat(classicCombatReload, member), convertible);
    classicCombatOutgoing = classicCombatAccumulated;
    classicCombatOutgoingState = classicCombatAccumulatedState;
}
void classicCombatAddIncoming(int member = 0, float damage = 0.0, float reload = 2.0,
    bool convertible = false, bool enemyExists = true, bool enemyHasAI = true) {
    if (member < 0 || member >= classicCombatCount || enemyExists == false || enemyHasAI == false) return;
    if (xsArrayGetBool(classicCombatExists, member) == false) return;
    classicCombatAccumulate(xsArrayGetFloat(classicCombatIncoming, member),
        xsArrayGetInt(classicCombatIncomingState, member), xsArrayGetFloat(classicCombatHP, member),
        damage, reload, convertible);
    xsArraySetFloat(classicCombatIncoming, member, classicCombatAccumulated);
    xsArraySetInt(classicCombatIncomingState, member, classicCombatAccumulatedState);
}
void classicCombatFinish() {
    classicCombatTTK = 340282346638528859811704183484516925440.0;
    if (classicCombatOutgoingState == 1) classicCombatTTK = 0.0;
    else if (classicCombatOutgoingState == 0 && classicCombatOutgoing >= classicCombatEpsilon)
        classicCombatTTK = classicCombatTargetHP / classicCombatOutgoing;
    classicCombatTTBK = 0.0;
    for (i = 0; < classicCombatCount) {
        if (xsArrayGetBool(classicCombatExists, i)) {
            float incoming = xsArrayGetFloat(classicCombatIncoming, i);
            int state = xsArrayGetInt(classicCombatIncomingState, i);
            if (classicCombatEnemyCount <= 0 || state == 2 || state == -1 || (state == 0 && incoming < classicCombatEpsilon)) {
                classicCombatTTBK = 340282346638528859811704183484516925440.0;
                return;
            }
            if (state == 0)
                classicCombatTTBK = classicCombatAddQuotient(classicCombatTTBK, xsArrayGetFloat(classicCombatHP, i), incoming);
        }
    }
    if (classicCombatTTBK < classicCombatEpsilon && classicCombatEnemyCount <= 0)
        classicCombatTTBK = 340282346638528859811704183484516925440.0;
}

void classicCombatScoreTarget(int unit = -1, int sourceClass = 32, int sourceId = 4,
    float distance = 20.0, bool sameZone = true, bool alive = true,
    bool relicCountdown = false, bool carriesRelic = false, bool wonderCountdown = false) {
    classicCombatFinish();
    classicScoreAdd(unit, sourceClass, sourceId, classicCombatTTK, classicCombatTTBK,
        distance, sameZone, alive, relicCountdown, carriesRelic, wonderCountdown);
}
