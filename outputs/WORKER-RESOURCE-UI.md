# Worker AI, Ore and resource HUD repair

The two-faction Empire/Rebels checkpoint is retained. The all-faction expansion remains paused on `codex/all-factions-paused`.

## Changes

- Ore: four existing graphics (eight SMXs across both resolutions) now carry explicit neutral damage masks, as Nova already does. Visible/player pixels, shadows, outlines, frame counts and anchors are exactly unchanged after serialized readback.
- AI: added a DE-format resource catalogue derived from this installed DAT's Gaia resource stores and translated resource classes. The native list omitted SWGB objects such as Savannah palm 7067 and treated SWGB effect 65 as native deer. The catalogue contains 119 food, 70 carbon, 5 ore and 8 Nova types. This is a plausible gathering fix, not proof that the engine used the old catalogue in the reported match.
- AI initialization: removed the default exploration threshold before construction, enabled independent building plans, set explicit builder/gatherer caps, expanded town/dropsite reach, and removed the previous ten-tile gather cutoff. The Troop Center and Core are requested at eight workers instead of twelve. Both the custom AI and default PromiDE entry receive the same script. No free resources or combat bonuses are added.
- Resource HUD: original SWGB interface sheet 50731 supplies blue Carbon (frame 0), purple Ore (1), orange Food (2) and green Nova (3). Replaced all eight ordinary/transparent textures and their SD/HD/UHD atlas regions. Every compressed atlas block outside those regions remains byte-identical. Existing unit and technology portraits are unchanged.

The compressed DAT, maps, music, unit balance and saved expansion branch are unchanged. `airesourcetypes.json` belongs to the Data mod; the AI scripts, Ore sprites and resource icons belong to the Assets companion. Both players should update both parts before a new multiplayer match. A website data subscription alone cannot deliver the updated local Assets folder.

## Validation and test

The pinned independent AI parser reports zero findings. The two script entry points match; Ore pixel/anchor checks and UI decode/collateral checks pass. Individual HUD textures exactly match the resized source pixels. Atlas compression remains lossy within the changed regions, with mean visible per-channel error below 5% at all scales. No game was launched and no in-engine success is claimed.

Restart DE after updating the companion, then start a **fresh** Savannah match with ordinary resources, an Empire or Rebel enemy and the normal **AI** choice (then the land AI, removed in October 2026). Use Moderate or Hard for an active-opponent test. Check that workers gather and construct buildings immediately, a Troop Center appears as the economy grows, and troops are produced. Check Ore brightness and all four top-bar resource symbols. Save a replay if workers remain idle; it will distinguish AI loading from economy/placement problems. Existing saves retain old AI state and are unsuitable for this test.

This is still a partial land AI port. Source difficulty rules have since been adapted; naval/air strategy, guaranteed Power Core coverage and the full original strategy tree remain unfinished.

## Reproduce the narrow patch

Do not rebuild from the paused expansion's generic `work/faction-*` staging. Start from the verified current assembly and snapshot its install/package manifests under `work/worker-ui-repair`.

1. Use `portdat economy-report` on the current two-faction raw DAT to write `work/worker-ui-repair/mod.txt`.
2. Run `stage_worker_ui_repair.py` to generate Ore masks and the resource catalogue.
3. Run `ai_entries.py --root work/worker-ui-repair/patch` and `check_faction_ai.py --root work/worker-ui-repair/patch` (the land AI generator `faction_ai.py` was removed in October 2026).
4. Run `faction_resource_ui.py` and inspect `outputs/resource-hud-preview.png`.
5. Run `assemble_worker_ui_repair.py`, then `install_factions.py` and the AI check with `--installed`.

The targeted assembler rejects drift and confirms the DAT remains byte-identical. Its baseline is the economy-repair candidate; it is not a general release upgrade tool.
