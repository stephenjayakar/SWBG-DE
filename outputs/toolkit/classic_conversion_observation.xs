// Development conversion observation for supplied, already admitted unit IDs.
// Requires source identity, UnitAI factory, conversion eligibility and Force rank.
// Source Force and target immunity remain explicit observations, NOT DE charge.
bool classicConversionObservationReady = false;
bool classicConversionObservedAllowed = false;

bool classicObserveConversion(int actor = -1, int target = -1,
    float sourceForce = 0.0, bool ignoreForce = false, int targetUnconvertible = 0) {
    classicConversionObservationReady = false;
    classicConversionObservedAllowed = false;
    if (classicForceObservePermissions(actor) == false) return(false);
    int actorCiv = 0;
    if (classicForceObservedOwner != 0)
        actorCiv = xsGetPlayerCivilization(classicForceObservedOwner);
    int actorClass = classicSourceClass(classicForceObservedSourceID, actorCiv);
    int actorAI = classicSourceAIType(classicForceObservedCopyID, actorCiv);
    // Known non-converters and absent targets are complete, denied decisions.
    if (classicUnitAIHasConversion(actorAI) == false || xsDoesUnitExist(target) == false) {
        classicConversionObservationReady = true;
        return(true);
    }
    int owner = xsGetUnitOwner(target);
    int civ = 0;
    if (owner != 0) civ = xsGetPlayerCivilization(owner);
    int raw = xsGetUnitObjectId(target);
    int copy = xsGetUnitCopyId(target);
    int original = classicSourcePacked(raw, civ);
    int upgraded = classicSourcePacked(copy, civ);
    if (original < 0 || upgraded < 0) {
        classicConvertSetPermissions(false, 0.0, 0.0, 0.0);
        return(false);
    }
    int targetClass = original % 128 - 1;
    int targetType = upgraded / 128 % 128;
    classicConversionObservedAllowed = classicCanConvert(actorClass,
        classicForceObservedPadawan, sourceForce, ignoreForce, true, owner,
        targetClass, raw, targetType, targetUnconvertible);
    classicConversionObservationReady = true;
    return(true);
}
