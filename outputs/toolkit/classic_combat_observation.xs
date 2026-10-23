// Development native query adapter. Requires generated combat catalog and
// classic_damage_calculator.xs. Caller supplies already admitted unit IDs;
// this module does not enumerate units or grant visibility/attack permission.
// Getter behavior is documented but not yet verified in the DE runtime.
// Status 0: query complete; 1: missing attacker; 2: unknown template;
// 3: ambiguous source layout; 4: invalid native attribute result.
int classicCombatObservationStatus = 1;
bool classicCombatObservationReady = false;
bool classicCombatObservedTargetPresent = false;
float classicCombatObservedReload = 0.0;
float classicCombatObservedTargetHP = 0.0;
float classicCombatObservedTargetMaxHP = 0.0;
int classicCombatObservedShort = 0;

bool classicCombatObserveShort(int unit = -1, int attribute = 0, int damageClass = -1) {
    float value = xsGetUnitAttribute(unit, attribute, damageClass);
    // This also rejects NaN/inf and fractional values instead of truncating a
    // surprising getter result into apparently valid source data.
    if ((value >= -32768.0 && value <= 32767.0) == false) return(false);
    int integer = xsCeilToInt(value);
    if (value != integer) return(false);
    classicCombatObservedShort = integer;
    return(true);
}
int classicCombatObserveLayout(int unit = -1) {
    int owner = xsGetUnitOwner(unit);
    int civilization = 0;
    if (owner != 0) civilization = xsGetPlayerCivilization(owner);
    return(classicCombatLayout(xsGetUnitCopyId(unit), civilization));
}
void classicCombatObservationReset(int status = 1) {
    classicCombatObservationStatus = status;
    classicCombatObservationReady = false;
    classicCombatObservedTargetPresent = false;
    classicCombatObservedReload = 0.0;
    classicCombatObservedTargetHP = 0.0;
    classicCombatObservedTargetMaxHP = 0.0;
    classicCombatObservedShort = 0;
    classicDamageReset();
}
bool classicCombatObservationFail(int status = 1) {
    classicCombatObservationReset(status);
    return(false);
}
bool classicCombatObserveDamage(int attacker = -1, int target = -1,
    float attackModifier = 1.0, float terrainModifier = 1.0) {
    classicCombatObservationReset(1);
    if (xsDoesUnitExist(attacker) == false) return(false);
    int attackLayout = classicCombatObserveLayout(attacker);
    if (attackLayout < 0) return(classicCombatObservationFail(2));
    int attackFlags = xsArrayGetInt(classicCombatLayouts, attackLayout);
    if (attackFlags % 2 != 0 || attackFlags / 4 % 2 != 0)
        return(classicCombatObservationFail(3));
    bool targetPresent = xsDoesUnitExist(target);
    int targetLayout = -1;
    int baseArmor = 1000;
    if (targetPresent) {
        targetLayout = classicCombatObserveLayout(target);
        if (targetLayout < 0) return(classicCombatObservationFail(2));
        int targetFlags = xsArrayGetInt(classicCombatLayouts, targetLayout);
        if (targetFlags / 2 % 2 != 0 || targetFlags / 8 % 2 != 0)
            return(classicCombatObservationFail(3));
        if (classicCombatObserveShort(target, cBaseArmor) == false)
            return(classicCombatObservationFail(4));
        baseArmor = classicCombatObservedShort;
    }
    classicDamageReset(baseArmor, attackModifier, terrainModifier);
    if (targetPresent) {
        int armorCount = xsArrayGetInt(classicCombatLayouts, targetLayout + 2);
        int armorStart = targetLayout + 3 + xsArrayGetInt(classicCombatLayouts, targetLayout + 1);
        for (i = 0; < armorCount) {
            int armorClass = xsArrayGetInt(classicCombatLayouts, armorStart + i);
            if (classicCombatObserveShort(target, cArmor, armorClass) == false)
                return(classicCombatObservationFail(4));
            classicDamageAddArmor(armorClass, classicCombatObservedShort);
        }
    }
    int weaponCount = xsArrayGetInt(classicCombatLayouts, attackLayout + 1);
    for (j = 0; < weaponCount) {
        int weaponClass = xsArrayGetInt(classicCombatLayouts, attackLayout + 3 + j);
        if (classicCombatObserveShort(attacker, cAttack, weaponClass) == false)
            return(classicCombatObservationFail(4));
        classicDamageAddWeapon(weaponClass, classicCombatObservedShort);
    }
    float reload = xsGetUnitAttribute(attacker, cAttackReloadTime);
    if ((reload >= 0.0 && reload <= 340282346638528859811704183484516925440.0) == false)
        return(classicCombatObservationFail(4));
    if (targetPresent) {
        float hp = xsGetUnitHitpoints(target);
        float maxHP = xsGetUnitAttribute(target, cHitpoints);
        if ((hp >= 0.0 && hp <= 340282346638528859811704183484516925440.0) == false)
            return(classicCombatObservationFail(4));
        if ((maxHP >= 0.0 && maxHP <= 340282346638528859811704183484516925440.0) == false)
            return(classicCombatObservationFail(4));
        classicCombatObservedTargetHP = hp;
        classicCombatObservedTargetMaxHP = maxHP;
    }
    classicCombatObservedReload = reload;
    classicCombatObservedTargetPresent = targetPresent;
    classicCombatObservationStatus = 0;
    classicCombatObservationReady = true;
    return(true);
}
