// Connect a completed source armor query to the combat estimator.
// Requires classic_damage_calculator.xs and classic_combat_estimator.xs.
// canAttack is the source UnitAI predicate, not a guess from armor damage.
// Source conversion capability remains a separate input.
void classicCombatWeaponOutgoing(int member = 0, bool canAttack = false, bool canConvert = false,
    bool attackerHasAI = true, bool targetPresent = true) {
    float damage = classicDamageCapability(targetPresent, attackerHasAI, canAttack);
    classicCombatAddOutgoing(member, damage, canConvert);
}
void classicCombatWeaponIncoming(int member = 0, float reload = 2.0,
    bool canAttack = false, bool canConvert = false, bool enemyExists = true, bool enemyHasAI = true,
    bool targetPresent = true) {
    float damage = classicDamageCapability(targetPresent, enemyHasAI, canAttack);
    classicCombatAddIncoming(member, damage, reload, canConvert, enemyExists, enemyHasAI);
}
