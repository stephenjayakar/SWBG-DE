# Farm, Holocron and Nova repair

This candidate updates the Empire/Rebels checkpoint e6cf77a. The 15-faction expansion remains paused on `codex/all-factions-paused` and is not included. No game was launched.

## Changes and evidence

The terrain importer incorrectly treated the legacy `IsWater` byte as a boolean. In current DE it is a bitmask: native land, including farm construction stages 29–31, carries value 32. Unmapped land therefore received water restrictions. Farm foundations became unbuildable when construction began. The repair reads the actual surface bits and maps the three native farm construction stages to the source land-farm construction terrain. Ground, water, beach, ice, snow and walkable shallows remain distinct; mapped terrain identities stay unchanged. AGE's local `AGE_Frame/Terrains.cpp` documents these bits.

Selected sections recovered from the latest 120×120 Rebel replay contained 16 Nova deposits and no Holocron objects. Full-header parsing is unsupported for this game version, so this is diagnostic object-list evidence, not a complete replay interpretation. All 20 maps now explicitly request Gaia-owned Holocrons. Savannah retains five Holocrons but places them on open grass, at least 18 tiles from starts and 12 apart, instead of the previous 25/20 spacing. The Gaia Holocron uses native DE's relic formation sentinel; its source art, tasks and statistics are retained. Spawn success and pickup/deposit still require a new-match test.

Source-versus-converted Nova previews retain the bright green source colors. Five installed Nova sprite variants now include explicit neutral damage masks at standard and enhanced resolution. Java readback checked every visible pixel, shadow/outline layer and anchor unchanged, and checked zero damage modifiers. This is a rendering candidate; it does not prove how DE shades the result.

Validation checks all 5,502 serialized terrain restriction cells, farm-stage build/walk permission and resource exclusion, all map Holocron branches, exact DAT roundtrip, and byte-for-byte restoration to the previous DAT after removing only the permitted terrain-table and relic-formation changes. Costs, technology trees, factions, combat, AI and music are unchanged. There are 31 changed payload files: one DAT, 20 maps and 10 sprite files.

## Test in a fresh match

1. Use the matching data mod and Assets companion, **Rebel Alliance**, **SWGB Factions Savannah**, **Standard resources**, and cheats enabled if desired. Restart DE to refresh loaded data/assets.
2. On clear ground, place a farm and let a worker finish it. Confirm it produces food, can be reseeded and remains walkable. Repeat as Empire.
3. Reveal the map with `marco` and `polo`; look for five Holocrons. Test collection and Temple deposit.
4. Inspect Nova deposits before and during mining. They should retain their bright green appearance.

Existing saves contain old map generation and are not a test of this candidate. For online play both players need the matching published data version and the updated local Assets folder from the full share ZIP. Report any remaining farm obstruction with its location/ground type; runtime behavior is not yet verified.

## Rebuild this narrow patch

Keep the previous release and package/install manifests until verification succeeds. Restore the e6cf77a DAT to `work/economy-repair/before.raw`; mirror current C++ sources to `work/dat-tool` and rebuild. Run `repair-economy`, `roundtrip`, `audit-economy`, `de-dependencies` and `economy-report` into the isolated economy-repair directory. Run `stage_economy_repair.py`; run `NeutralBuildingMasks` on each staged Nova resolution; run `check_economy_repair.py`, then `assemble_economy_repair.py` and the normal installer/exporter. The staging script snapshots the previous manifests. Do not use the paused expansion's generic staging directories for this patch. A full future rebuild uses the corrected terrain importer, map helper and updated building/Nova mask selector.
