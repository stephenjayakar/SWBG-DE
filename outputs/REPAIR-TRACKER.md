# September 16 AI difficulties

Payload b9ca555 is installed with source-derived Computer Classic difficulty rules for Easiest, Standard/Easy, Moderate, Hard and Hardest; DE Extreme uses Hardest's strategy. Changed only the two companion AI entry points. Added the missing Spaceport/Research Center/Heavy Weapons Factory build requests needed for later age prerequisites. Static validation includes 3,736 decision/source-graph checks and zero pinned-parser findings, with both installed entry points matching. Game runtime remains untested. The full source AI strategy tree is still incomplete; see AI-DIFFICULTIES.md.

Published data remains version 1.4 and matches all nine data files. Release b9ca555 retains the global shading repairs. The new Dropbox delivery rule retains the latest verified full-share/data-upload pair under `E:\Dropbox\temp\SWBG`; source and release history remain in Git. The faction expansion remains paused.

# September 15 economy repair

Build 6a6b7cf is installed and published as service version 1.3. Corrected farm construction terrain flags; added Holocron placement and Nova damage-mask candidates. Static checks passed; runtime verification remains pending. See ECONOMY-REPAIR.md and RELEASES.md. The faction expansion remains paused.

# September 9 user-reported repairs

The user requested autonomous work while asleep. Do not request manual testing during this work.

- Right-click marker: open; investigate native hardcoded graphic references after replacing the source graphics table.
- Missing build names and icons: open; screenshots confirm blank button art and cost-only tooltip. Source strings exist, so field lookup and runtime UI loading need investigation.
- Spatial hotkeys: open; use dataset-specific hotkeys.json and source command positions, preserving global controls and the user profile.
- Savannah carbon: staged fix keeps seven forest identities distinct. Previously TREE_C and TREE_F both mapped to 10, so a TREE_F clearing rule also cleared TREE_C. New raw DAT and roundtrip are byte-exact; all seven source forest spawn lists match. Not installed yet.
- Ore color: open; compare source palette, frame and terrain appearance.
- Base in water: open; inspect starting placement and shallow-water terrain conversion.
- Missing Nova: open; source Nova placement blocks remain present, which does not prove successful placement or rendering.

Forest checkpoint: work/factions-forest-fix.raw, work/factions-forest-fix-roundtrip.raw and work/faction-forest-dependencies. The staging RMS scripts and terrain mapping now reflect this change; canonical work/factions.raw and installed draft have not yet been updated. Finish related terrain/resource fixes before packaging them together.

Hotkey inspection exported source command HotKeyID into production.tsv. The spatial audit found 141 existing IDs, two shared IDs used in different grid positions, and 240 visible/miscellaneous commands with missing IDs or special button positions. Safe grid conversion requires assigning unique IDs in the DAT before generating dataset hotkeys.json; editing the existing defaults alone would leave conflicts and missing research keys. No personal hotkey profile was changed.

Spatial hotkey implementation checkpoint: faction_hotkeys.py now generates 585 unique command IDs and dataset hotkeys.json; faction_hotkeys.h applies them to the matching DAT production locations. check_faction_hotkeys.py verifies all serialized bindings, row keys, unchanged native controls and exact DAT roundtrip. All presets receive the requested QWERT/ASDFG/ZXCVB production defaults; personal profiles remain untouched. Six AVAIL ship technology records at button positions 21-23 remain excluded pending special-button semantics. Staged work/factions-repair.raw and its roundtrip include both this change and the forest repair. Not packaged or installed yet. Build prerequisite: run faction_hotkeys.py before build-factions.

Marker candidate repair: DE graphic 1963 is the native flags resource, but the imported table placed source LRMASSTEMP_S there. faction_marker.h reserves that native flag slot and relocates the source graphic to 29106, updating its one source reference. This is a runtime hypothesis supported by the table collision, not yet proof of the right-click fix. The original source graphic remains preserved. The new checkpoint is work/factions-marker.raw, which includes forest and hotkey repairs. No marker-unit fields were guessed or overwritten.

Replay inspection: the user match recorded at 00:41:55 is available locally. Its decompressed header reports VER 9.4 / save version 68.0 and has 9,241,279 bytes. Upstream mgz 1.8.51 fails in parse_de; AoEInsights/mgz-fast commit 6fd28520fea4e80a2f0d67bc219d2bc4cf119751 also fails before map parsing (string marker mismatch at offset 1658). No terrain or resource counts have been inferred from either failed parse. The raw header is retained only under work/user-match-header.raw for further format investigation; no replay or private match data was uploaded. Source resource terrain restriction 8 correctly allows grass and rejects shallow water in the staged DAT, and Nova/ore sprites exist through composite child graphics, so missing top-level sprite filenames are not alone a defect.

## Combined repair candidate

The canonical DAT now includes forest identities, spatial hotkeys, native flag-slot relocation, and revised language IDs. Unit names occupy disjoint blocks with creation at name+1000 and help text at name+21000 (DAT Help=name+100000). This supplies the derived tooltip lookup described by the independent mod implementation at https://github.com/napkingcole/aoe2-empire-forge/blob/main/CLAUDE.md . Custom-name support is still an engine question; the user's previous selected-unit names did render. All 68,981 generated string IDs resolve without collisions. The 642 custom textures now use lossless uncompressed DDS; source pixel equality is checked. This is a compatibility candidate, not a confirmed icon fix.

Replay recovery supersedes the earlier inability to read its map: upstream parse_map and parse_players can read selected sections at validated offsets. The diagnostic tool pins the raw-header SHA-256 and parser commit and exports no player names. The 120x120 map has 4,534 terrain-145 tiles. Installed DE random_map.def defines TREE_C as 401; its low byte is 145. The old map redeclared TREE_C as 10. All source constants are now namespaced to prevent these built-in collisions. The distinct-forest mapping additionally prevents one source clearing rule from affecting a different forest.

The recovered replay contains 16 Nova objects, but the nearest are about 80.3 and 34.0 tiles from the two Command Centers. Both centers are on terrain 1 (water). Savannah now gives player lands an explicit ID, removes the normal CC's group scatter radius, and removes the zone-edge cap on per-player Nova groups while preserving their source counts and distance bounds. These are placement safeguards requiring new-match validation, not proof that every seed is fixed.

Ore appearance remains open. Its converted preview is magenta; Nova is green. All three ore/Nova child sprites contain ordinary palette pixels, with no player-color pixels. The converter's target palette exactly matches the installed DE original.pal. No speculative recoloring was applied. A source/game rendering comparison remains necessary.

The refreshed DE window still fails capture with SetIsBorderRequired / 0x80004002 after the permitted retry. No blind game input or manual-test request was made. Static checks passed for semantic parity (allowing explicit hotkey remaps), exact DAT roundtrip, all 585 hotkeys, 642 icon references, terrain spawns/restrictions, language references, technology panels, power, nursery map includes and blast behavior records. Engine verification remains open for all user-reported repairs.

Installation checkpoint: combined repair commit 979472c was packaged and installed as 0.0.2-dev in the existing separate data/assets mods. All 4,412 installed payload files matched their manifest, and the base DE DAT stayed unchanged. Superseded PNG textures were hash-verified and backed up under work/retired-icon-pngs. The user must start a fresh game after DE reloads the mod to evaluate these candidates; no in-game success is claimed. Stable 0.0.1 was not changed.

Resource palette audit: ResourcePaletteAudit.java compares every ordinary source pixel against its anchor-aligned converted counterpart across all frames. Ore 5234: 39,845 pixels, mean maximum-channel error 0.00271/255, maximum 9/255. Ore 5237: 35,335 pixels, mean 0.01656/255, maximum 9/255. Nova 5136: 51,210 pixels, mean 1.28377/255, maximum 11/255. Source-left/converted-right PNGs are outputs/resource-palette-{5136,5234,5237}.png. Both source and converted ore are magenta. This rules out a broad offline palette conversion error; it does not prove the correct graphic is selected/rendered in DE. Ore remains open pending runtime evidence.

## Morning regression repair

User reports supersede any optimistic interpretation of the earlier candidate: selection icons and right-click markers still failed, Rebel starts contained Stormtroopers, and matches crashed repeatedly.

All three new crash dumps (BB8T6AI4, L2T937G6, CH2P5NM5) stop at game RVA 0x17104ae. Both upgrade endpoints are -1 (R14/R15), and the code indexes the unit-pointer array at index -1 before reading the target unit. Source effect 2 (Tech Level 3) contains exactly three Type 3 commands with A=B=C=-1 and D=0. The builder now omits those three invalid placeholders and rejects remaining negative upgrade endpoints. This is a concrete data/exception match; a runtime retest is still required.

The real movement/waypoint slots are native graphics 2961 MOVEX_NN/MOVETO and 2962 WAYPT_NN. The source table put building-damage composites at these slots, with six and five flame deltas respectively. Restoring only 1963 was insufficient. All three native slots are now reserved, preserving displaced source graphics at appended indices and remapping references.

DE resource 263 was inherited as 448 for all factions. That native scout ID means a Stormtrooper in SWGB. It now contains 550 for Empire/Gaia and 556 for Rebels. The alias remains for original map compatibility. The morning faction replay actually started both sides with 448; this fix targets that verified starting-unit issue, not a claim that every faction availability rule is verified.

Custom icons now use the same Atlas/AlphaPlayerColor material structure as native unit icons, with a dedicated precached DDS atlas and SD/HD/UHD/default source paths. All 642 atlas regions are pixel-exact copies of their individual converted icons. The preceding Texture/InverseAlpha scheme failed the user test. New atlas rendering still needs confirmation.

The 10:39 faction replay has 4,541 forest-terrain tiles and 4,641 palm objects, with both Command Centers on foundation terrain. The 10:43 replay instead contains native TC annexes and native forest objects, so it is not evidence of the same faction dataset. Do not use the partially parsed civilization_id field (96) as a valid civ number.

Missing Ore/Nova in the morning test is explained by Infinite Resources, confirmed by the user. DE omits resource deposits in that mode (official update 34699: https://www.ageofempires.com/news/aoe2de-update-34699/). Use Standard/High resources for map/economy validation. No further speculative resource-placement edits were made this turn. Savannah's original script intentionally contains palms, scattered trees and water; native DE terrain textures still substitute for source textures.

Morning installation: d214633 was packaged and installed as 0.0.2-dev, with 4,413 payload files hash-verified and the base DE DAT unchanged. check_faction_regressions.py passes serialized upgrade endpoints, scout resource IDs, native marker slots and every atlas region. Source parity accounts explicitly for the three omitted TL3 placeholders. A full DE restart and fresh match are required to verify gameplay and atlas loading.

## Builder, clearing and UI regression report (September 9, late morning)

User reports that the preceding atlas still has invisible icons, workers vanish while building, the Imperial temple retains a Jedi label, age advancement cannot be found, and another in-play crash occurs. These supersede earlier optimistic static checks.

The 11:31:34 replay contains faction scouts 550/556, 4,540 forest tiles and 4,640 palm objects. Command Centers at (83,69) and (34,18) have nearest palms 3.81 and 2.92 tiles away. Both standing on foundation terrain did not establish usable starts. Savannah now gives all six start-avoidance terrain blocks an explicit distance of 18 and moves the three scattered-palm groups' minimum player distance from 6 to 18. This uses DE's documented distance parameter: https://www.ageofempires.com/news/aoe2de-update-50292/. Fresh-seed verification remains required. Replay settings are Infinite resources and Castle/TL3 start (raw age 4 minus 2); missing deposits in this match are expected.

Builder tasks 118/212 referenced empty selectors 16790 and 16850, with no SLP or deltas. Actual faction graphics are selector-name plus -C1 (Empire) or -C3 (Rebels), e.g. working poses 16851/16853. faction_task_graphics.h materializes these task choices before serializing DE data. Roster staging now includes the selected variants: 32 additional graphics, 1,207 converted graphics total at both resolutions. The new check validates serialized builder task references independently of the source-preservation subset checks.

EF's langdll.cpp identifies temple IDs 30,31,104,3593,3594,3595. Previously only 104 received the dynamic faction name. All six now use Sith Temple for Empire and Jedi Temple for Rebels; exact staged strings are checked. Other source names and costs remain unchanged.

Age techs 1/2/3 share Command Center slot 9 with Imperial availability tech 525. They now use the otherwise empty slot 10, default G. Original building prerequisites and research costs remain unchanged; runtime availability is still unverified. Starting at TL3 does not waive the two qualifying building-type prerequisites for TL4.

Icon payloads are now placed in the enabled companion's widgetui/textures/swgb, with unique SWGB materials additionally registered through widgetui/morematerials.json. Dataset icons.json/materials.json remain present. This follows the documented non-data-mod material extension (https://support.ageofempires.com/hc/en-us/articles/15607286588948-Return-of-Rome-Mod-Updates). It addresses a possible data-mod texture mounting/registration problem, not a proven rendering root cause. The installer backs up and hash-checks relocated files; it does not overwrite the base game UI.

New dump AoE2DECE6L2SR1.dmp at 11:40:24 crashes at RVA 0xD103F0, reading offset 0x44 through a null pointer. This differs from the repaired TL3 unit[-1] crash. The minidump lacks caller-code and relevant object heap pages, and protected disk code does not yield a trustworthy caller reconstruction. Do not identify register 5246 as a graphic/unit ID without evidence. The exact trigger and stability remain unresolved; no claim that the new graphics repair fixes this crash.

Installation: repair commit 2513c95 was assembled and installed as 0.0.2-dev, with 4,478 payload files verified against the package manifest. The base DE DAT is unchanged. DAT roundtrip, source-field parity with explicit adapters, task graphics, all temple names, age slot exclusivity, spatial hotkeys, terrain/string references, tree links and icon/atlas reference checks pass. All 1,207 sprite files pass conversion readback at both resolutions; the newly converted Imperial and Rebel working-pose previews are visibly nonempty. Runtime icons, clear starts, age progression and stability remain pending. Restart DE completely and start a fresh match; existing matches do not pick up these changes.

## 12:40 regression: protected clearings and native icon slots

The user's new screenshots explicitly disprove the preceding distance-only clearing and companion custom-material repairs. DE's 12:37 session log records both faction mods being loaded, and mod-status.json enables the asset companion. The 12:40:01 replay identifies SWGB Factions Savannah and contains 4,546 forest tiles; both Command Centers have a palm only 0.707 tiles from their centers. This is not usable placement. No claim that the prior 18-tile parameter worked remains valid.

Savannah now builds player lands using GRASS2 (source/target terrain 12), base_size 18 and land_percent 0. It restricts Command Centers to GRASS2. Forest/water generation only replaces GRASS1 or other explicitly named terrain, never GRASS2; terrain 12 has no tree spawns. Explicit start distances are retained for scattered palms. The regression check asserts the protected land, CC restriction, and absence of any terrain rule targeting GRASS2. Map generation is not engine-tested. The new clearing intentionally changes local start terrain rather than relying again on the failed avoidance parameter.

The previous custom DDS atlas and custom materials did not render in the user's HUD. Native individual DDS files use RGBA pixel masks and native SD atlases use DXT5/BC3. The revised adapter deduplicates 642 source bindings into 72 building, 122 unit and 150 technology images, all within existing native category capacities. It assigns their actual native IDs, leaves icons.json/materials.json byte-identical to DE, and paints source artwork into the registered native atlas regions and individual texture paths. All nine SD/HD/UHD atlas files are encoded as BC3 using DE's bundled texconv. No custom material registration or extended icon-ID vector is needed; morematerials.json is empty. The asset companion overrides these UI images while enabled, so it should be disabled for ordinary DE play. Base game files are read-only inputs.

The icon validator checks serialized IDs against native category mappings, exact resized individual DDS pixels, and every compressed atlas crop against its source. The old swgbicons atlas checks have been retired because that atlas is no longer referenced. The native-atlas worker preview visibly contains the correct source droid portrait. These are offline checks, not proof that the live HUD rendered it.

Additional checks found two shared conditional straggler-tree groups with original distances 4-5 and 6-8. Their counts are retained, but they now use distances 20-23 and ordinary GRASS1 outside the protected terrain. The three scattered palm groups and three decorative plant groups are also restricted to GRASS1. This prevents those object rules from repopulating the protected clearing.

The earlier unnecessary land_id 1 override has also been removed from create_player_lands, retaining the standard player-land identity. No object rule used that custom land ID. The protected terrain is buildable under both factions' serialized Command Center restrictions and has no terrain-unit spawns.

The first native-icon pass used eight 80px native technology slots, which compress down to 40px at SD. Crop checks found excessive error (worst mean-channel difference 23.37/255), so that pass was not installed. The adapter now selects only native texture slots at least 255px in both dimensions. The final crop bound remains 8/255; it was not relaxed to accept the failed small-slot pass.

Installation: commit 18dbaf4 is installed as 0.0.2-dev, with 4,831 payload files hash-verified and the original DE DAT unchanged. All 20 assembled maps match their staged files, including removal of the obsolete land_id override. The final icon check passes all 642 serialized bindings, exact individual images, and 1,032 atlas regions across nine quality files; maximum mean-channel error is 7.2638/255. Protected-clearing, worker, temple, age slot, hotkey, source-parity, terrain, tree and roundtrip checks pass. The live map start and HUD still require a fresh match after a full DE restart; neither is labeled engine-verified.

## 2026-09-14: idle AI and reported script error

The user reports idle AI and a load-time script error on Hard, but does not have the error file/line/code. Both attempts to capture DE fail with SetIsBorderRequired 0x80004002; accessibility returns null. The exact dialog error is still unknown.

Read-only decompression of the three latest local replays (2026-09-09 13:15:01, 12:40:01 and 11:31:34) finds the PromiDE entry at header byte 339 and native Promisory chat strings. None contains SWGB Land AI. This identifies a default-AI selection mismatch in those recorded matches, not proof about an unrecorded later match. Staged, assembled and installed custom scripts were byte-identical before this change (SHA-256 86f7199bbe0cfa255d83a4600e443a35d6431a699a0ded7511459d93f4b6c4c8).

faction_ai.py now writes an identical inline copy into the companion's resources/_common/drs/gamedata_x2/PromiDE.per2, so the normal AI choice is intended to run the faction script as well. Native base-game PromiDE.per2 remains unchanged (SHA-256 b03f7a583c0d71008e2cfc8643813dbb65d1a7cb27eb390faa81c1a079814a83). Disable the companion for normal DE games. This is a routing correction; no claim that the unknown error has been reproduced or fixed in the engine.

Added check_faction_ai.py using joerollman/aoe2-ai-parser at commit 3dfa2583b7c2ec36b85ccb421ebd0abe9ff276ba. Package lint reports zero findings. Both entry points must match byte-for-byte; --installed also checks package and installed files. No scripted difficulty branches exist: Hard is acceptable but does not select a different strategy. Original SWGB/EF AI remains TODO. Engine startup, worker economy and attacks remain unverified.

Installation: implementation commit 97b0f68 is installed as 0.0.2-dev. All 4,832 payload files passed the existing installer's manifest checks. check_faction_ai.py --installed reports zero parser findings and identical staged, packaged and installed default/custom AI scripts. The native AI entry hash and base DAT are unchanged. Stable 0.0.1 is unchanged. Restart DE and create a fresh match; old saves/replays retain their old AI state. Live validation remains pending.

## 2026-09-14 14:57: match-start crash and unmapped Gaia icons

New dump AoE2DEPT9D5595.dmp and crash report identify SinglePlayerInGame at WorldTime=0. MainLog records an impossible 6,086,737,227,502,545,319-byte allocation before the deliberate failure handler at game RVA 0x1ac93f2. The September 9 13:15 dump AoE2DEJ3H97NN1.dmp hits the same handler after another impossible allocation, predating the AI alias. This shared handler is not a symbolic identification of the original corrupting instruction. Caller code/heap are absent from the minidump, and disk code is protected, so the exact crash trigger remains unproven.

The new replay has the mod's protected terrain (2,714 tiles of terrain 12) and does not contain the old native Promisory chat strings. It still names the PromiDE entry, as expected for the new alias. It is not evidence that the original native AI is still running.

A whole-dataset audit found 4,644 unit icon references outside the applicable native category tables. The prior validator covered only the 642 explicitly mapped faction bindings. Two offending Gaia objects are actually present in the crashing Savannah replay: OBJ-TIMBERB (414), IconID 1784; OBJ-TIMBER_PALMCC (7067), IconID 1783. Native Units has only entries 0-756. Native source units in the reference export contain no similarly high icon IDs. These are concrete invalid UI references and plausible causes of out-of-bounds UI reads, but have not been linked to the failing caller in the dump.

faction_icons.h now replaces every out-of-range source icon with DE's -1 no-icon sentinel after applying the valid faction mappings. Unmapped environmental/editor records may therefore lack portraits; this is deliberate until their icons are converted. No mapped playable portrait is removed. Bounds are generated from the installed native icons.json by faction_icon_limits.py; the native icon generator also refreshes them. The full serialized dataset is checked, in addition to the existing mapped portrait and texture tests. The normal-AI alias is retained because the identical earlier allocation failure predates it; its engine behavior is still unverified.

The build also found 3,265 source IconID=-2 values; native reference exports use only -1 for negative icon IDs. These are normalized to -1 as well, for 7,909 repaired fields total. A serialized before/after comparison against the previously installed DAT finds exactly 12,534 changed bytes, all changing to 0xFF, matching the audited icon values; file length is unchanged. No other serialized bytes changed.

Installation: ba04fb3 is installed as 0.0.2-dev; all 4,832 payload hashes pass and the base DE DAT is unchanged. Full bounds checks pass for 22,993 exported icon records. All 642 mapped portraits and 1,032 atlas regions still pass; source-field parity, worker/temple/age/hotkey regressions, terrain references, tree panels and byte-exact DAT roundtrip pass. Stable 0.0.1 is unchanged. The next required check is a fresh-match load in DE; no claim that the allocation crash is resolved until that succeeds.

## 2026-09-14: checkpoint before worker portrait and Force combat repairs

User reports that a working builder displays what looks like a scout portrait, asks whether timing respects game speed, and reports Sith Knights converting instead of attacking. Requested order: commit the current state, explain and prepare sharing, then fix these issues. User will handle all game launching and runtime tests. No new runtime success/stability claim is inferred from the portrait screenshot.

## 2026-09-14: worker portraits, Force combat and elapsed game time installed

Checkpoint 2e2d3d1 preserves the preceding build. Repair implementation 69338c1 is now installed as 0.0.2-dev. All 4,832 installed payload files match the package, and the base DE DAT remains unchanged. The user explicitly handles the game; no game launch or runtime verification was attempted.

Worker-job records previously retained source icon 59 after the base worker received a native portrait slot. All 48 faction worker records now use their own faction's base-worker icon. Armed Force users now map to infantry with native combat targeting; eligible units receive the native Sun Ce non-monk conversion ability. Conversion balance, source Force energy and Holocron interactions remain experimental. See WORKER-FORCE-TIMING.md for the mechanics and limits.

Serialized checks pass for 805 Force records, 585 conversion configurations, source melee reload preservation and the explicit Empire/Rebel Padawan/Knight/Master cases. Gaia's source conversion range is zero; playable faction ranges are nine. The initial targeted check incorrectly assumed Gaia also used nine; it now compares each civilization's range against its source resource. Nursery elapsed-time accounting passes regular, skipped and paused game-clock cases. XS Check 0.2.29 passes and all staged/package/installed script hashes agree. The pinned AI parser reports zero findings and both installed AI entry points match. Existing source-field parity, byte-exact DAT roundtrip, worker/temple/age, hotkey, icon, world and tree checks pass. These do not establish engine behavior or crash resolution.

Share exports are separate two-folder ZIPs, with installation instructions and BUILD.json checksums. The pre-fix archive remains SWGB-DE-0.0.2-dev-2e2d3d1.zip. The repaired archive is outputs/releases/SWGB-DE-0.0.2-dev-69338c1.zip, 319,255,366 bytes, SHA-256 a495c326871680f7c6e8158be5d8eae36a3f9e56b03b247daff41870b96990c7. Both ZIP integrity and every payload hash were read back successfully. Stable 0.0.1 remains unchanged.

## 2026-09-14: music and Power Core upgrade repair installed

User requested music with source faction distinctions and reported no core speedup at Troop Center/War Center with cheats apparently off. Source effects 1/2/3 upgrade core 12 to 498/132/20; the old adapter attached power only to 12. This explains why cores after age advancement had no aura. Implementation 310ed21 follows the eight-record source core upgrade family, including evacuation variants, and retains the two reachable droid emitters per faction. It derives work-rate tasks from native building 2275, uses proportional bonus 3 (+300%) over the quarter-rate baseline, and sets one visible radius per emitter. Static checks cover 20 emitters, 254 recipients and 2,540 aura tasks. Runtime ratio, destruction, stacking and placement-preview visibility remain unverified.

Installed music includes 38 WEM files: 30 contiguous parts of the two installed shared streams (130 minutes 16 seconds), Empire/Rebel source cues under DE's exact custom theme names, EF menu/lobby, credits and victory/defeat tracks. Every converted file was decoded by vgmstream and checked against its PCM input. The shared output concatenation matches the complete decoded source streams byte for byte, and the installed files match staging and package. DE playlist transitions and menu/result selection remain adaptations: source result routine 0x4EF0B0 selects won2 for end conditions 100/101 and won1 otherwise, while DE randomly chooses the two supplied victory tracks; this is not faction-dependent. No game was opened.

Package/install: 4,870 payload files verified, base DAT unchanged, XS checker passes with staged/package/installed hashes matching. Source-field parity, DAT roundtrip, native portraits/atlases, worker/Force/hotkey/age regressions, terrain and technology-tree checks pass. Share archive outputs/releases/SWGB-DE-0.0.2-dev-310ed21.zip is 1,660,017,563 bytes; SHA-256 a2067ceda9af58af9a322b50fe6b6ded9577bf91f5de1f1ba14b46b52b75611c. ZIP CRC and each payload hash were read back successfully. This remains 0.0.2-dev, with stable 0.0.1 unchanged. Test instructions are in MUSIC-POWER.md and FACTION-TESTING.md.


## 2026-09-14: TIE Fighter movement-crash candidate installed

The user clarifies that the crash occurred after the music update while flying TIE Fighters. Latest dump/replay agree on world time 335442 ms; the final MOVE contains unit instances 5307 and 5306, with R12=5306 at the null read in RVA 0xD103F0. The earlier scenery hypothesis is unconfirmed and superseded by this command correlation. See AIRCRAFT-CRASH.md for the raw-selection decoding caveat and the limits of this evidence. Private crash/replay files remain under ignored work/, with the preceding raw DAT and install manifest preserved.

The compatibility candidate removes ambient Bird class 38 from commanded aircraft, assigning fighters to native archer class and bombers/cruisers to siege. All 1,185 affected source records retain their exported flight/movement/combat fields; 20 producible aircraft have 120 covered graphic dependencies. Class effects/tasks retain source target membership through existing explicit expansion. This is not proof of the engine crash cause, nor a completed air/ground combat adapter.

Source-field parity, task membership/defaults, exact DAT roundtrip, worker/Force/temple/age, hotkey/icon, terrain, tree and Power Core checks pass. Restoring only classes and selector tables reproduces the previous raw DAT byte for byte (SHA-256 751de1e3f0ec5588803cd639873b25b4a87900e3572b72027cf4357c8658dc72). Current raw DAT SHA-256 is 4c3bcf2d753ef8103fe3ffd8fbfcf6de8da958d49356fda36be7b07fc2108adb.

Installed 4,870 verified payload files. Only the compressed mod DAT differs from the prior installed payload: music, sprites, UI, maps, AI and XS files are byte-identical. Original DE DAT is unchanged. The user handles the game; no game launch or runtime claim was made. Start a fresh match and move two selected TIE Fighters with music enabled, including across forests/water and through formation/attack changes. Stable 0.0.1 and the 310ed21 music-build ZIP are preserved.

Aircraft candidate checkpoint: b944fbf415810518fadd24a109b327b9d2ae1b5f. Share archive outputs/releases/SWGB-DE-0.0.2-dev-b944fbf.zip contains both installed mod folders and AIRCRAFT-CRASH.md. Size 1,660,048,853 bytes; SHA-256 f3d5b0a742f22ee25273ede2868343cbeff5931a4ca64956ec9bb346c090e90b. ZIP CRC and every payload hash passed readback. Runtime retest remains pending.


## 2026-09-15: flight, garrison, scout and building damage candidates

Five user reports: TIEs inconsistently face their flight direction, cannot cross trees, garrisoned units do not produce laser fire, scouts lack auto-scout, and damaged buildings darken. The user explicitly handles all game testing and asked not to launch DE.

Serialized TIE flight parent/hull/shadow had eight angles but no directional sequence bit; the adapter enables it through aircraft graphic dependencies. For 1,176 flying aircraft records, zero collision replaces the unavailable SWGB airspace traversal behavior while keeping military classes and original terrain rules, speed and weapons. This permits aircraft overlap and does not complete air/ground targeting.

SWGB-only trait flags are cleared before enabling native auto-scout on 189 scout records; 6,356 records had foreign trait bits. This prevents detector/mechanical traits becoming DE transformation or auto-scout abilities. Worker garrison firepower uses native -2.5 and ordinary/mounted troopers use 1, covering 72 worker and 2,538 troop records (including Gaia/editor records). Exact SWGB damage balance is still pending. Building projectile settings are unchanged.

All 748 modified building SMXs (374 graphics at both resolutions) pass neutral-mask readback and exact visible pixel, player pixel, shadow, outline, frame-count and anchor comparison. Source flames are retained; SMX damage-mask rendering is not engine-tested.

The behavior audit restores only traits, collision, garrison firepower and graphic sequence fields, then reproduces b944fbf raw DAT SHA-256 4c3bcf2d753ef8103fe3ffd8fbfcf6de8da958d49356fda36be7b07fc2108adb exactly. Source parity, task membership/defaults, roundtrip, aircraft sprite dependencies, prior regressions and power checks pass. See FLIGHT-GARRISON-SCOUT.md for limitations and fresh-match tests.

## Published behavior checkpoint: September 15

Implementation e6cf77a was installed with all 4,870 payload hashes verified. Full share and eight-file data upload ZIPs passed CRC and payload verification. Existing unlisted listing 549437 accepted the update and displays version 1.2 and build e6cf77a. The local publishing copy was updated with metadata preserved; subscribed files were left to the game. Only the DAT and 472 building SMX files changed relative to b944fbf. Old archives were removed after successful verification. No game was launched; flight, auto-scout, garrison firepower and damage shading require runtime confirmation. See FLIGHT-GARRISON-SCOUT.md and RELEASES.md.


## 2026-09-15: idle workers, dark Ore and resource HUD

Installed repair f8e11f9 changes 18 payload files, adding 12 files for a total of 4,882. The compressed DAT, maps, music and existing portrait atlases are unchanged. Ore mask serialization preserves all visible layers/anchors. Original SWGB resource symbols occupy ordinary/transparent slots in SD/HD/UHD; other compressed atlas blocks remain exact. The AI catalogue now uses resource-bearing SWGB Gaia IDs rather than the native DE list, and initialization no longer gates building on exploration or gathering on ten-tile dropsite distance. Troop Center/Core requests start at eight workers. These address plausible causes; idle-worker resolution and military buildup are not engine-verified.

The pinned AI parser reports zero findings, and custom/default entry hashes match in staging, assembly and installation. Full share and nine-file data ZIPs pass integrity and payload verification. Existing unlisted mod 549437 visibly shows version 1.4 and build f8e11f9 after publishing; its local publishing copy preserves owner metadata. Old build archives were deleted only after successful new-build verification. Fresh-match instructions and limitations are in WORKER-RESOURCE-UI.md. The game was not opened, and the expansion branch remains paused.


## 2026-09-16: global sprite damage-shading repair

User reported dark corpses/wreckage and explosions beyond the earlier building and resource fixes. The SLP conversion allocated an SMX damage layer with unset sentinel pixels and saved it without neutral initialization. Full installed-set scan found 77,850 non-neutral visible frames in 1,552 files, out of 2,414 SMXs / 82,352 frames. Binary repair preserves drawing commands and all non-damage fields; the independent Java decoder confirmed all 324,833,980 visible pixels, shadow/outline layers, palettes and geometry unchanged. All 80,392 visible frames now have neutral damage values. The converter explicitly initializes zero masks, with readback and source conversion regression checks at both resolutions.

Implementation 05646c4 is installed and packaged with all 4,882 file hashes checked. Only Assets sprites differ; nine data files match published v1.4. The data listing and local publishing payload were not republished or changed. Friends should replace Assets and restart DE. This removes the shared bad mask values across every animation category; runtime darkening resolution remains to be confirmed by the user. No game was opened; extra factions remain paused. See ALL-SPRITE-SHADING.md and RELEASES.md.
