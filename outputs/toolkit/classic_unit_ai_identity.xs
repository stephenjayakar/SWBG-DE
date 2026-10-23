// Connect a supplied unit's source template to the implemented combat gates.
// Include generated classic_unit_identity.xs and classic_unit_ai_factory.xs.
// These describe expected original behavior, not a native DE UnitAI instance.
int classicSourceUnitAttackKind(int unit = -1) {
    return (classicUnitAIAttackKind(classicSourceUnitAIType(unit)));
}
int classicSourceUnitNeutralKind(int unit = -1) {
    return (classicUnitAINeutralKind(classicSourceUnitAIType(unit)));
}
bool classicSourceUnitHasConversion(int unit = -1) {
    return (classicUnitAIHasConversion(classicSourceUnitAIType(unit)));
}
