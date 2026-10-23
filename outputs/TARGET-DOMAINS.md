# Source attack-domain rules

The source action gate at 0x41C530 distinguishes airborne target classes 43, 48, 59, 62, 63 and 64 from other targets. Ordinary troopers are ground-only, anti-air classes are air-only, and fighters normally support both. Flying status alone is not the selector.

Before the class switch, the installed ground-to-air.txt list permits listed attackers to target either domain. AT-AT records 500 and 603 similarly gain both domains when owner resource 31 is positive. The earlier rejection of attacker class 4, target ID 696 and target classes 21/28 still applies. An initial virtual-method target rejection remains outside the current static model.

The [EF air-to-air hook](https://github.com/rva2895/efpatch/blob/f2773079b3deb53737d86165351a7279fa71b5e9/cheatdll/airtoair.cpp) changes the class-derived category to air-only for attackers listed in air-to-air.txt. It runs after the early ground-to-air and AT-AT gates. Do not reverse that precedence.

`audit_faction_target_domains.py` reads both lists and decodes the two jump tables from the hash-guarded installed source executable. It records domain expectations for all 391 production/upgrade records across the two factions: 336 ground-only, 23 air-only, 16 dual-purpose, 2 technology-gated AT-AT records and 14 without a permitted class category. These are record counts, not distinct usable attackers; buildings without weapons can still have a ground-domain category.

This is the reference for a future DE targeting adapter, not an installed restriction. Native class translation alone does not preserve these gates. Do not merely give aircraft high armor: that still permits forbidden attack commands and can introduce minimum-damage and splash errors. An adapter needs to preserve manual and automatic target selection, technology transitions and the existing noncombat tasks, followed by runtime checks for trooper/fighter, anti-air/ground, bomber/air, fighter/air and AT-AT before/after its technology. Flight collision and pathing are separate requirements.

Generated details and external-list hashes are in faction-target-domains.json. The model does not establish weapon availability, range, diplomacy, visibility or pathing, and has not been compared against a running source match.

DE task-filter investigation: the task author reference leaves Combat task semantics undocumented, and a [firsthand modding report](https://forums.ageofempires.com/t/combat-against-specific-class-only/248262) found class-filtered Combat still attacked other classes. That older report is not proof for the current engine; it is sufficient reason not to claim a task-class edit implements these restrictions without a current runtime test.
