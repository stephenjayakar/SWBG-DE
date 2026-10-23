# Flight, garrison, auto-scout and building shading repair

This 0.0.2-dev candidate addresses the five September 15 gameplay reports. No game was launched. The published data mod and local asset companion are separate: everyone needs the updated companion for the building-shading change.

## Changes

- TIE flight hull 5552, flight parent 5551 and shadow 5549 had eight directions but SequenceType 0, without DE's directional bit. Hover graphics already had it. The adapter enables that bit for directional aircraft artwork, retaining all animation frames, timing and source sprites.
- Aircraft retain their original terrain permissions, speed and flight flag, but use zero collision as the DE flying-transport mod does. This allows pathfinding over trees/buildings without making trees passable to ground troops. It also lets aircraft overlap. SWGB's separate airspace and air/ground targeting are not fully reproduced.
- Source worker and troop records had zero in DE's new GarrisonFirepower field. Workers now use native villager contribution -2.5; ordinary troopers and mounted troopers use native archer contribution 1. Existing building projectile types, capacities, shot limits and reload times are unchanged. Training buildings do not gain weapons. Exact SWGB garrison damage balance remains unverified.
- SWGB trait bits above the shared garrison/ship bits meant stealth, detector, mechanical, biological, shielding or invisibility. DE assigns different abilities to those bits. Strip those incompatible meanings and give scout-class units DE's auto-scout flag 16. This includes starting scouts, trained scouts and upgrade records. This does not implement the original stealth/detector/shield mechanics.
- Add explicit zero damage masks to 374 staged building graphics at both resolutions. All 748 sprite files were read back and compared: visible image/player pixels, shadows, outlines, frame counts and anchors are unchanged. Original flame overlays remain. This is a shading candidate; DE's handling of SMX damage masks still requires a visual check.

## Checks

`check_faction_behavior.py` checks serialized traits, firepower, aircraft collision and TIE direction flags. A collateral audit restores only traits, collision, garrison firepower and graphic sequence flags and then reproduces the prior b944fbf raw DAT byte for byte. Source-field parity, task membership/defaults, DAT roundtrip, aircraft dependencies, worker/age/scout/marker regressions, Power Core data and all sprite layouts pass. These are offline checks, not proof of engine behavior or crash resolution.

## Fresh-match tests

1. Fly a TIE in eight directions, then across dense forest, water and a building. It should face its travel direction and cross obstacles; test two selected aircraft as well.
2. With an enemy in range, put five workers in a Command Center. It should fire lasers. Repeat with troopers in an armed turret/fortress. An empty Command Center or an unarmed training building is a different case.
3. Select the starting scout and a newly trained scout on an unexplored map. Both should offer auto-scout; workers should not.
4. Damage a building through the 25%, 50% and 75% thresholds. Flames should appear without the previous heavy darkening. Compare both sprite-quality modes if available.

Sources: [DE flying-transport implementation](https://github.com/SiegeEngineers/auto-mods/blob/master/patches/flying_dutchman.cpp), [DE unit trait documentation](https://ksneijders.github.io/AoE2ScenarioParser/api/AoE2ScenarioParser/datasets/trigger_lists/object_attribute.html#ObjectAttribute.UNIT_TRAIT), [SMP/SMX damage modifier documentation](https://github.com/SFTtech/openage/blob/master/doc/media/smp-files.md#damage-info). The installed native DAT supplies garrison reference values; the installed AGE source documents directional sequence bits.
