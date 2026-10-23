// Original armor damage and attack modifiers (0x4449C0/0x55BBC0/0x557BA0).
// Requires the compensated arithmetic helpers in classic_target_scorer.xs.
// Caller supplies ordered source weapon/armor lists and terrain/height state.
// Eligibility and shield application are separate from this damage estimate.
int classicDamageArmorClasses = -1;
int classicDamageArmorValues = -1;
int classicDamageArmorCount = 0;
int classicDamageWeaponCount = 0;
int classicDamageRawStrength = 0;
int classicDamageBaseArmor = 1000;
float classicDamageAttackModifier = 1.0;
float classicDamageTerrainModifier = 1.0;
float classicDamageSumHi = 0.0;
float classicDamageSumLo = 0.0;
float classicDamageHi = 0.0;
float classicDamageLo = 0.0;

void classicDamageScaleWide(float high = 0.0, float low = 0.0, float factor = 1.0) {
    classicScoreMultiplyWide(high, factor);
    float productHi = classicScoreHi;
    float productLo = classicScoreLo;
    classicScoreMultiplyWide(low, factor);
    float extraHi = classicScoreHi;
    float extraLo = classicScoreLo;
    classicScoreAddWide(productHi, extraHi);
    float highResult = classicScoreHi;
    float lowResult = classicScoreLo + productLo;
    lowResult = lowResult + extraLo;
    classicScoreAddWide(highResult, lowResult);
    classicDamageHi = classicScoreHi;
    classicDamageLo = classicScoreLo;
}

float classicDamageModifier(bool higherGround = false, float attackerZ = 0.0, float targetZ = 0.0,
    int specialMode = 0, bool action133 = false, bool building = false,
    int relics = 0, int specialRelics = 0, bool targetBuilding = false,
    int targetRelics = 0, int targetSpecialRelics = 0) {
    float value = 1.0;
    if (higherGround) value = 1.25;
    else if (attackerZ < targetZ) value = 0.75;
    if (specialMode == 3 && action133) value = value * 2.0;
    classicDamageHi = value;
    classicDamageLo = 0.0;
    if (building) {
        if (specialRelics > 0) classicDamageScaleWide(classicDamageHi, classicDamageLo, 1.2);
        else if (relics > 0) classicDamageScaleWide(classicDamageHi, classicDamageLo, 1.1);
        if (targetBuilding) {
            if (targetSpecialRelics > 0) classicDamageScaleWide(classicDamageHi, classicDamageLo, 0.833333313465118408203125);
            else if (targetRelics > 0) classicDamageScaleWide(classicDamageHi, classicDamageLo, 0.90909087657928466796875);
        }
    }
    return(classicDamageHi + classicDamageLo);
}

void classicDamageReset(int baseArmor = 1000, float attackModifier = 1.0, float terrainModifier = 1.0) {
    if (classicDamageArmorClasses < 0) {
        classicDamageArmorClasses = xsArrayCreateInt(128, -1, "classic armor classes");
        classicDamageArmorValues = xsArrayCreateInt(128, 0, "classic armor values");
    }
    classicDamageArmorCount = 0;
    classicDamageWeaponCount = 0;
    classicDamageRawStrength = 0;
    classicDamageBaseArmor = baseArmor;
    classicDamageAttackModifier = attackModifier;
    classicDamageTerrainModifier = terrainModifier;
    if (classicDamageTerrainModifier < 1.0) classicDamageTerrainModifier = 1.0;
    classicDamageSumHi = 0.0;
    classicDamageSumLo = 0.0;
}
void classicDamageAddArmor(int armorClass = 0, int amount = 0) {
    if (classicDamageArmorCount >= xsArrayGetSize(classicDamageArmorClasses)) {
        xsArrayResizeInt(classicDamageArmorClasses, classicDamageArmorCount + 32);
        xsArrayResizeInt(classicDamageArmorValues, classicDamageArmorCount + 32);
    }
    xsArraySetInt(classicDamageArmorClasses, classicDamageArmorCount, armorClass);
    xsArraySetInt(classicDamageArmorValues, classicDamageArmorCount, amount);
    classicDamageArmorCount++;
}
void classicDamageAddWeapon(int armorClass = 0, int strength = 0) {
    int protection = classicDamageBaseArmor;
    for (i = 0; < classicDamageArmorCount) {
        if (xsArrayGetInt(classicDamageArmorClasses, i) == armorClass)
            protection = xsArrayGetInt(classicDamageArmorValues, i);
    }
    classicDamageWeaponCount++;
    // Source strengths and weapon count are signed 16-bit fields; their
    // maximum positive sum fits a signed 32-bit integer without early rounding.
    if (strength > 0) classicDamageRawStrength = classicDamageRawStrength + strength;
    float amount = strength - protection;
    classicDamageScaleWide(amount, 0.0, classicDamageTerrainModifier);
    classicDamageScaleWide(classicDamageHi, classicDamageLo, classicDamageAttackModifier);
    // Last duplicate armor entry wins; duplicate weapon entries each contribute.
    if (classicDamageHi > 0.0 || (classicDamageHi == 0.0 && classicDamageLo > 0.0)) {
        float high = classicDamageHi;
        float low = classicDamageLo;
        classicScoreAddWide(classicDamageSumHi, high);
        high = classicScoreHi;
        low = low + classicScoreLo;
        low = low + classicDamageSumLo;
        classicScoreAddWide(high, low);
        classicDamageSumHi = classicScoreHi;
        classicDamageSumLo = classicScoreLo;
    }
}
float classicDamageFinish() {
    if (classicDamageWeaponCount == 0) return(0.0);
    float result = classicDamageSumHi + classicDamageSumLo;
    if (result < 1.0) result = 1.0;
    return(result);
}
float classicDamageCapability(bool targetPresent = true, bool attackerHasAI = true, bool canAttack = true) {
    if (targetPresent == false || attackerHasAI == false) return(classicDamageRawStrength);
    if (canAttack == false) return(0.0);
    return(classicDamageFinish());
}
