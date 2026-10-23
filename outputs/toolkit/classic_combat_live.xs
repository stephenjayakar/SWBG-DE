// Development orchestration for admitted army/target/enemy IDs.
// Requires source identity, combat observation, estimator and damage modules.
// Caller computes original eligibility/modifiers for each requested pair.
// No discovery, permission inference, attack orders or native AI takeover.
// Begin/steps/finish must run synchronously in one caller pass; this is not
// a persistent snapshot across game updates. Wrong-order calls preserve the
// current pass for retry; native observation failures abort it completely.
bool classicLiveCombatBusy = false;
bool classicLiveCombatComplete = false;
int classicLiveCombatError = 0;
int classicLiveCombatTarget = -1;
int classicLiveCombatEnemies = -1;
int classicLiveCombatEnemyCount = 0;
int classicLiveCombatOutgoingNext = 0;
int classicLiveCombatIncomingMember = 0;
int classicLiveCombatIncomingEnemy = 0;

bool classicLiveCombatFinite(float value = 0.0) {
    return(value >= 0.0 && value <= 340282346638528859811704183484516925440.0);
}
int classicLiveCombatAIType(int unit = -1) {
    int owner = xsGetUnitOwner(unit);
    int civilization = 0;
    if (owner != 0) civilization = xsGetPlayerCivilization(owner);
    int packed = classicSourcePacked(xsGetUnitCopyId(unit), civilization);
    if (packed < 0) return(-2);
    return(packed / 33554432 % 16 - 1);
}
bool classicLiveCombatAbort(int error = 1) {
    classicLiveCombatBusy = false;
    classicLiveCombatComplete = false;
    classicLiveCombatError = error;
    classicLiveCombatTarget = -1;
    classicLiveCombatEnemyCount = 0;
    classicLiveCombatOutgoingNext = 0;
    classicLiveCombatIncomingMember = 0;
    classicLiveCombatIncomingEnemy = 0;
    classicCombatObservationReset();
    classicCombatReset();
    classicCombatTargetBegin(0.0, 0);
    return(false);
}
bool classicLiveCombatBegin(int members = -1, int count = 0, int target = -1,
    int enemies = -1, int enemyCount = 0) {
    // A duplicate begin must not destroy the evaluation already in progress.
    if (classicLiveCombatBusy) return(false);
    if (members < 0 || count < 1 || count > 40 || enemies < 0 || enemyCount < 0)
        return(classicLiveCombatAbort(1));
    if (count > xsArrayGetSize(members) || enemyCount > xsArrayGetSize(enemies))
        return(classicLiveCombatAbort(1));
    classicCombatObservationReset();
    classicCombatReset();
    classicLiveCombatComplete = false;
    classicLiveCombatError = 0;
    if (xsDoesUnitExist(target) == false) return(classicLiveCombatAbort(2));
    if (classicLiveCombatAIType(target) == -2) return(classicLiveCombatAbort(6));
    float hp = xsGetUnitHitpoints(target);
    if (classicLiveCombatFinite(hp) == false) return(classicLiveCombatAbort(3));
    if (classicLiveCombatEnemies < 0)
        classicLiveCombatEnemies = xsArrayCreateInt(enemyCount, -1, "classic live combat enemies");
    if (xsArrayGetSize(classicLiveCombatEnemies) < enemyCount)
        xsArrayResizeInt(classicLiveCombatEnemies, enemyCount);
    for (e = 0; < enemyCount)
        xsArraySetInt(classicLiveCombatEnemies, e, xsArrayGetInt(enemies, e));
    for (i = 0; < count) {
        int unit = xsArrayGetInt(members, i);
        bool exists = xsDoesUnitExist(unit);
        float unitHP = 0.0;
        float reload = 0.0;
        if (exists) {
            unitHP = xsGetUnitHitpoints(unit);
            reload = xsGetUnitAttribute(unit, cAttackReloadTime);
            if (classicLiveCombatFinite(unitHP) == false || classicLiveCombatFinite(reload) == false)
                return(classicLiveCombatAbort(3));
        }
        int member = classicCombatAddMember(unit, unitHP, reload, exists);
        if (member != i) return(classicLiveCombatAbort(1));
    }
    classicLiveCombatTarget = target;
    classicLiveCombatEnemyCount = enemyCount;
    classicLiveCombatOutgoingNext = 0;
    classicLiveCombatIncomingMember = 0;
    if (enemyCount == 0) classicLiveCombatIncomingMember = count;
    classicLiveCombatIncomingEnemy = 0;
    classicCombatTargetBegin(hp, enemyCount);
    classicLiveCombatBusy = true;
    return(true);
}
bool classicLiveCombatOutgoing(int member = 0, int attacker = -1,
    bool canAttack = false, bool canConvert = false,
    float attackModifier = 1.0, float terrainModifier = 1.0) {
    if (classicLiveCombatBusy == false || member != classicLiveCombatOutgoingNext
        || member < 0 || member >= classicCombatCount) return(false);
    if (xsArrayGetInt(classicCombatIds, member) != attacker) return(false);
    if (xsArrayGetBool(classicCombatExists, member)) {
        if (classicCombatObserveDamage(attacker, classicLiveCombatTarget, attackModifier, terrainModifier) == false)
            return(classicLiveCombatAbort(3));
        if (classicCombatObservedTargetPresent == false) return(classicLiveCombatAbort(2));
        // Expected source UnitAI type is distinct from a native DE UnitAI.
        int aiType = classicLiveCombatAIType(attacker);
        if (aiType == -2) return(classicLiveCombatAbort(6));
        bool hasAI = aiType >= 0;
        float damage = classicDamageCapability(true, hasAI, canAttack);
        // The original dereferences a missing own UnitAI at low damage.
        // Treat that invalid source input as an incomplete candidate here.
        if (hasAI == false && (damage <= classicCombatEpsilon || damage != damage))
            return(classicLiveCombatAbort(5));
        xsArraySetFloat(classicCombatReload, member, classicCombatObservedReload);
        classicCombatAddOutgoing(member, damage, canConvert);
    }
    classicLiveCombatOutgoingNext++;
    return(true);
}
bool classicLiveCombatIncoming(int member = 0, int enemyIndex = 0, int attacker = -1,
    bool canAttack = false, bool canConvert = false,
    float attackModifier = 1.0, float terrainModifier = 1.0) {
    if (classicLiveCombatBusy == false || classicLiveCombatOutgoingNext != classicCombatCount)
        return(false);
    if (member != classicLiveCombatIncomingMember || enemyIndex != classicLiveCombatIncomingEnemy
        || member < 0 || member >= classicCombatCount || enemyIndex < 0
        || enemyIndex >= classicLiveCombatEnemyCount) return(false);
    if (xsArrayGetInt(classicLiveCombatEnemies, enemyIndex) != attacker) return(false);
    if (xsArrayGetBool(classicCombatExists, member) && xsDoesUnitExist(attacker)) {
        int aiType = classicLiveCombatAIType(attacker);
        if (aiType == -2) return(classicLiveCombatAbort(6));
        if (aiType >= 0) {
            int victim = xsArrayGetInt(classicCombatIds, member);
            if (classicCombatObserveDamage(attacker, victim, attackModifier, terrainModifier) == false)
                return(classicLiveCombatAbort(3));
            if (classicCombatObservedTargetPresent == false) return(classicLiveCombatAbort(3));
            float damage = classicDamageCapability(true, true, canAttack);
            classicCombatAddIncoming(member, damage, classicCombatObservedReload, canConvert, true, true);
        }
    }
    classicLiveCombatIncomingEnemy++;
    if (classicLiveCombatIncomingEnemy == classicLiveCombatEnemyCount) {
        classicLiveCombatIncomingEnemy = 0;
        classicLiveCombatIncomingMember++;
    }
    return(true);
}
bool classicLiveCombatFinish() {
    if (classicLiveCombatBusy == false || classicLiveCombatOutgoingNext != classicCombatCount
        || classicLiveCombatIncomingMember != classicCombatCount) return(false);
    classicCombatFinish();
    classicLiveCombatBusy = false;
    classicLiveCombatComplete = true;
    return(true);
}
// Caller opens a target batch with classicScoreReset and ranks it with
// classicScoreEvaluate after submitting completed admitted candidates.
bool classicLiveCombatScore(float distance = 20.0, bool sameZone = true,
    bool relicCountdown = false, bool carriesRelic = false, bool wonderCountdown = false) {
    if (classicLiveCombatBusy || classicLiveCombatComplete == false) return(false);
    if (classicScoreValues < 0 || classicTargetCount >= 1024) return(false);
    if (xsDoesUnitExist(classicLiveCombatTarget) == false) return(classicLiveCombatAbort(2));
    if (classicLiveCombatAIType(classicLiveCombatTarget) == -2) return(classicLiveCombatAbort(6));
    int sourceClass = classicSourceUnitClass(classicLiveCombatTarget);
    // Original scoring uses retained master ID, not the upgraded copy ID.
    int sourceId = xsGetUnitObjectId(classicLiveCombatTarget);
    int owner = xsGetUnitOwner(classicLiveCombatTarget);
    int civ = 0;
    if (owner != 0) civ = xsGetPlayerCivilization(owner);
    if (classicSourcePacked(sourceId, civ) < 0) return(classicLiveCombatAbort(6));
    classicScoreAdd(classicLiveCombatTarget, sourceClass, sourceId, classicCombatTTK,
        classicCombatTTBK, distance, sameZone, true, relicCountdown, carriesRelic, wonderCountdown);
    classicLiveCombatComplete = false;
    return(true);
}
