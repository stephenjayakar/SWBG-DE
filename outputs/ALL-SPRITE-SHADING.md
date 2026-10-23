# Global sprite shading repair

The SWGB SLP loader allocated an SMX damage layer and left its pixels at the
library's unset sentinel. The conversion path did not initialize those values
before saving. The installed SMXs therefore contained non-neutral damage
modifiers even though the original SWGB sprites had no such mask. Low-health,
death and effect rendering can expose this unwanted shading.

Earlier repairs explicitly cleared that layer only for building/resource
graphics. That selection omitted live units, dying animations, corpse decay,
projectiles, explosions, craters and other scenery. This repair scans **every
installed SWGB SMX**, regardless of unit class or animation role. It also makes
neutral damage shading the default in `PortSprites.java`, after rescaling and
before serialization, with readback verification.

## Scope and verification

- All 2,414 sprite files (1,207 graphics at two resolutions) inspected.
- 1,552 files / 77,850 visible frames had non-neutral damage values and are repaired.
- All 82,352 frames are covered; 80,392 contain visible image pixels.
- An independent Java decoder compares all 324,833,980 visible pixels, plus
  shadows, player-color indices, outline pixels, frame palettes and anchors.
- The binary repair changes damage bits only for this installed set. Original
  artwork, encoded drawing commands, frame order, dimensions and shadows stay
  intact. Naturally dark source paint is not artificially brightened.
- A second repair pass is byte-identical. Fresh conversions of an explosion,
  trooper, corpse and stump pass zero-mask and pixel checks at both scales.
- DAT, AI, UI, maps, music and faction selection are unchanged. The additional
  faction branch remains paused.

This is an Assets-only update compatible with the existing published **v1.4
data mod**. Replace `SWGB-DE-Factions-Assets` from the new full release ZIP on
each player's PC, then restart DE to clear cached graphics. The website data
subscription cannot deliver local sprite updates. No new data publication is
needed for this repair.

The game was not opened. Test live units, injured units, death animations,
wreckage and explosions, along with previously repaired buildings and resource
deposits. Offline validation proves the mask/pixel changes, not the renderer's
runtime behavior; any remaining dark example needs a fresh screenshot after
the restart.

## Rebuild

1. Run `stage_all_sprite_masks.py` against the verified two-faction assembly.
2. Compile `PortSprites.java` and `VerifyNeutralSprites.java` against the pinned
   SMX Workshop JAR. Run `VerifyNeutralSprites` on
   `work/all-sprite-masks/verify.tsv`, with `work/all-sprite-masks/verify-pass.txt`
   as its optional report argument, from the workshop directory.
3. Run `check_mask_converter.py`, then `assemble_all_sprite_masks.py` and
   `install_factions.py`. Snapshot manifests and backups remain in the isolated
   repair directory; do not use paused expansion staging.
4. Commit, create and verify the full share/data archives, then apply the
   workspace's release retention rule. Data payload must match published v1.4.

Format reference: [openage SMX documentation](https://github.com/SFTtech/openage/blob/master/doc/media/smx-files.md).
