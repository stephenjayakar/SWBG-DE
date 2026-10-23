# Changelog

## Unreleased

- Translated age/economic resource IDs; isolated unresolved special mechanics from native DE resource slots.
- Added roster and worker task-swap dependency extraction, plus batch artwork staging with explicit missing/frame-error reports.
- Extended directional conversion to full eight-direction sprites, sixteen-direction missiles and five-part walls.

- Added source-to-DE unit class translation and explicit target expansion for overlapping class effects/tasks; verified task defaults and target membership. Full-faction intermediate remains uninstalled.

- Added an uninstalled three-civ source-rule intermediate with source units, costs, production, technologies and effects; exported-field parity and raw roundtrip checks pass. Cross-engine semantics remain in progress.

- User confirmed the prefab/trail preview works.
- Began full Imperial/Rebel source-rule migration with semantic table export for economy, production, technologies, effects and tasks.

- Restored the omitted SWGB blaster tracking effects in the optional preview, using source trail spacing; visual test pending.

- Converted six factions' dwelling structure/shadow sets.
- Installed optional Buildings-Preview dataset: two house sets with construction stages and damage-fire layers; native costs/population/footprints preserved. Runtime verification pending.

- Investigating additive Imperial and Rebel civilization slots that preserve the existing DE roster.

## 0.0.1 — 2026-09-08

First local playable prototype; native DE economy and technology progression.

- Imperial and Rebel troopers on the Archer line, with blaster projectiles and impact art.
- Imperial mech graphics on Scorpion and Heavy Scorpion.
- Twenty adapted SWGB/Expanding Fronts random maps, including Savannah, Arena and Motherlode.
- Fixed empty maps by declaring RMS entity constants.
- Expanded five source directions into eight explicit DE directions and corrected their order.
- Reduced oversized troops and mechs to source-size standard graphics and doubled enhanced graphics.
- Separate data, artwork and map packages; English unit names.
- Larger laser projectile sprites for visibility.

Validation: user confirmed Savannah generation and improved unit rendering. Converter pixel/anchor roundtrips, reference checks, installed-file comparisons and native-data collateral-change audit pass. Latest laser visibility and full combat behavior still require in-game confirmation.

Limitations: existing civ slots supply gameplay; most buildings, icons, sounds and mechanics are native DE. Other maps need individual play tests. This is not a full SWGB rules port.
