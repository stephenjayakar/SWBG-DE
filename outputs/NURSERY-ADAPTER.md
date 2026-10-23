# Nursery adapter evidence

The experimental faction maps now load `swgb_factions.xs`. This restores a draft implementation of nursery food production rather than borrowing DE's different livestock-income formula. It is installed within the experimental data/media pair but is not enabled and has not passed the engine's XS compiler or a runtime income test.

Read-only inspection of the installed SWGB executable establishes:

- At 0x55537e–0x5553b9, building processing uses elapsed milliseconds divided by 1,000 as a gate. It advances the saved timestamp by whole seconds.
- At 0x555509–0x55552f, it visits each contained unit, checks source class 1, and credits food to the building owner using the building master's work rate at offset 0x110.
- Power-controlled training/research instead uses runtime work rate at offset 0x114. Thus the nursery's food calculation uses its base work rate independently of power.
- Source nursery 319 has work rate 0.13 for Empire and Rebels. Applicable technologies multiply it: 82 by 1.17, 83 by 1.33333, 127 by 1.5 and 571 by 1.1. The Republic-only technology 582 is excluded.

The generator guards the exact source executable hash and these source values. The script queries each player's herd animals, checks their garrison parent, credits the nursery owner (including allied animals), and reuses a query array. Completed technologies determine the rate. It pays once per observed game second, without awarding missed offline time.

Expected ordinary-game cases: an empty nursery earns zero; ten animals without upgrades earn 1.3 food per second; Stimulants changes this to 1.521 food per second. Different animal food reserves do not change this calculation. Destroying or emptying the nursery stops subsequent payments once the garrison query reflects that state.

This is source-model evidence, not runtime verification. Outstanding checks include whether garrisoned animals are included in the query, save/load persistence, the engine's XS parser, the phase of the one-second tick, and earned-resource statistics. Nonstandard scenario buildings that can hold livestock are outside the current adapter, which recognizes nursery 319.

The [official XS reference](https://www.forgottenempires.net/age-of-empires-ii-definitive-edition/xs-scripting-in-age-of-empires-ii-definitive-edition) documents unit queries, garrison-parent lookup and RMS inclusion. [DE update 66692](https://www.ageofempires.com/news/age-of-empires-ii-definitive-edition-update-66692/) documents the native livestock system's diminishing returns; copying that bonus would change source behavior.

The mechanics exporter also now records collision, flight, blast levels, garrison flags, resource storage and detailed task parameters. Source troops commonly use blast level 4 while DE's ordinary targeted attacks use 3. Those fields need a semantic combat audit; numeric copying is insufficient. No speculative blast-level remapping was applied in this checkpoint.

The combined installed XS script passes standalone XS Check 0.2.29 syntax/type checking, with identical staged/package/install hashes (faction-xs-validation.json). This does not replace DE engine compilation or runtime verification.
