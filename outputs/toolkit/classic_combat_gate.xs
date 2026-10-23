// Development source UnitAI dispatch. Include factory, base/mobile eligibility
// and conversion modules first. Refresh actor, motion and permissions for each
// synchronous observation pass; these scratch values are not persistent units.
int classicCombatActorType = -1;
int classicCombatActorClass = -1;
int classicCombatActorKind = -1;
int classicCombatActorState = 0;
int classicCombatActorHeld = -1;

void classicCombatSetActorIdentity(int sourceAIType = -1, int sourceClass = -1,
                                  int ownState = 0, int heldAttribute = -1,
                                  int computerPlayer = 1) {
    classicCombatActorType = sourceAIType;
    classicCombatActorClass = sourceClass;
    classicCombatActorKind = classicUnitAIAttackKind(sourceAIType);
    classicCombatActorState = ownState;
    classicCombatActorHeld = heldAttribute;
    classicAttackSiegeSetState(ownState,computerPlayer);
    classicAttackSoldierMotionAllowed = false;
    classicConvertSetPermissions(false,0.0,0.0,0.0);
}

void classicCombatSetActorTemplate(int sourceClass = -1, int volleyMissileID = -1,
                                  int ownState = 0, int heldAttribute = -1,
                                  int computerPlayer = 1, int sourceType = 70) {
    int type = -1;
    if (sourceType == 70 || sourceType == 80) type = classicUnitAIType(sourceClass,volleyMissileID);
    classicCombatSetActorIdentity(type,sourceClass,ownState,heldAttribute,computerPlayer);
}

bool classicCombatActorHasAI() {
    return (classicCombatActorType >= 0);
}

bool classicCombatCanAttack(int sourceID = -1, int targetClass = -1, int targetID = -1,
                           bool invisible = false, float resource31 = 0.0,
                           bool targetPresent = true, int ownerID = 1, int targetOwner = 2,
                           int targetType = 70, int targetFlag = 0, int actionType = -1) {
    if (classicCombatActorKind < 0 || targetPresent == false) return (false);
    int cls = classicCombatActorClass;
    int kind = classicCombatActorKind;
    if (kind == 0) return (classicAttackBase(cls,sourceID,targetClass,targetID,invisible,resource31));
    if (kind == 1) return (classicAttackBuilding(cls,sourceID,targetClass,targetID,invisible,resource31));
    if (kind == 2) return (classicAttackTower(cls,sourceID,targetClass,targetID,invisible,resource31,
                                           targetPresent,ownerID,targetOwner,targetType,targetFlag,classicCombatActorState));
    if (kind == 3) return (classicAttackSoldier(cls,sourceID,targetClass,targetID,invisible,resource31,
                                             targetPresent,ownerID,targetOwner,targetType,targetFlag,actionType));
    if (kind == 4) return (classicAttackPriest(cls,sourceID,targetClass,targetID,invisible,resource31,
                                            targetPresent,ownerID,targetOwner,targetType,targetFlag,classicCombatActorHeld));
    if (kind == 5) return (classicAttackSiege(cls,sourceID,targetClass,targetID,invisible,resource31,
                                           targetPresent,ownerID,targetOwner,targetType,targetFlag,actionType));
    if (kind == 6 || kind == 7) return (classicAttackNullable(cls,sourceID,targetClass,targetID,invisible,resource31,targetPresent));
    return (classicAttackNever());
}

bool classicCombatCanConvert(bool padawan = false, float force = 0.0, bool ignoreForce = false,
                            bool targetExists = false, int targetOwner = 0,
                            int targetClass = -1, int targetID = -1,
                            int targetType = 70, int unconvertible = 0) {
    if (classicUnitAIHasConversion(classicCombatActorType) == false) return (false);
    return (classicCanConvert(classicCombatActorClass,padawan,force,ignoreForce,targetExists,
                              targetOwner,targetClass,targetID,targetType,unconvertible));
}
