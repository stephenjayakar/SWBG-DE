# Building preview (unreleased)

Optional installed data mod: SWGB-DE-Buildings-Preview. Keep SWGB-DE-Assets enabled, restart DE, and select this dataset for a new Skirmish. Existing 0.0.1 archive/tag and Trooper-MVP data are unchanged.

Use Britons or Franks and build houses. This candidate imports source dwelling structure and shadow layers, three construction stages, and damage fire at 25/50/75 percent damage. It covers DE house IDs 70, 463, 464 and 465, retaining native costs, population capacity, build time, footprint, destruction and rubble. Other civs still use native houses. Snow-specific house art is disabled for these eight modified entries.

Check construction progresses visibly, completed houses sit correctly on their footprint, population increases normally, damage adds fire and repairs remove it. Repeat after advancing ages and on snow terrain. No such runtime test has been completed yet. Use Trooper-MVP again to return to the released dataset.

Rebuild from task root:

1. Build work/dat-tool, then run `work/dat-build/Release/portdat.exe build-houses work/de.raw work/building-mod.raw`.
2. Run `python work/extract_sprites.py work/building-graphic-mapping.tsv work/building-slp`.
3. Compile PortSprites.java and convert building-slp into building-converted (scale 1) and building-converted4x (scale 2), using the same palette/classpath as the release build. Construction sprites have three stage groups, which must remain in source order rather than using directional expansion.
4. Run `work/dat-build/Release/portdat.exe audit-houses work/building-mod.raw work/building-audited.raw`.
5. Run `python outputs/toolkit/package_buildings.py`.

The package check verifies the normalized DAT is byte-identical to native DE, validates frame counts, preserves existing released sprite bytes, and checks installed copies. It does not validate DE rendering. Composite parent graphics have no sprite file; their child references provide the imagery.

## Laser trail correction

The preview now imports source tracking effects. SWGB Empire projectile 5090 tracks effect 1345 (graphic 5354); Rebel projectile 2337 tracks effect 2338 (graphic 11805). Both use tracking mode 2 and density 0.035 at speed 8.8. The earlier prototype cloned DE arrows without copying these tracking effects, producing a moving point rather than the source trail. New native-compatible effect units 2704/2705 are cloned from DE Trail Smoke (type 20), assigned the source art/resource lifetime fields, and referenced only by the custom projectiles. Recursive tracking is disabled. The house audit validates these references in every civilization.

To check this correction, select Buildings-Preview, train troopers and fire at an enemy. Verify visible trails, impacts and disappearing effects after the shot. This behavior is not yet engine-verified. Release 0.0.1 remains immutable and does not include the trail correction.
