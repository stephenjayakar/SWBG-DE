// Bind a supplied existing unit to the original combat-dispatch context.
// Requires generated source identity plus classic_combat_gate.xs. Dynamic state
// arguments remain explicit observations. No enumeration or unseen-unit scan.
bool classicCombatObserveActor(int unit = -1, int ownState = 0,
                               int heldAttribute = -1, int computerPlayer = 1) {
    classicCombatSetActorIdentity(-1,-1,0,-1,computerPlayer);
    if (xsDoesUnitExist(unit) == false) return (false);
    int owner = xsGetUnitOwner(unit);
    int civilization = 0;
    if (owner != 0) civilization = xsGetPlayerCivilization(owner);
    int packed = classicSourcePacked(xsGetUnitCopyId(unit),civilization);
    if (packed < 0) return (false);
    int sourceClass = packed % 128 - 1;
    int sourceAIType = packed / 33554432 % 16 - 1;
    classicCombatSetActorIdentity(sourceAIType,sourceClass,ownState,heldAttribute,computerPlayer);
    return (true);
}
