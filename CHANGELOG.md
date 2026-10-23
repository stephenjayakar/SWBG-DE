# Changelog

Commit hashes below are build labels from the local development history before the GitHub repository was squashed to a single commit on 2026-10-19; they do not exist on GitHub (see outputs/RELEASES.md). The `v0.0.1` / `v0.0.2-dev-*` tags named below are local only.

## Unreleased: one AI, SWGB Classic AI (2026-10-22)

SWBG now ships exactly one AI: every AI choice in the Skirmish lobby runs SWGB Classic AI at every difficulty. SWBG-Logic is unchanged (the 1.7 upload package stays valid); only SWBG-Data, the installer and the tooling changed.

- **How DE fills the lobby's AI list** (AoE2DE_s.exe build 185872, its string table and the lobby itself):
  - **AI** (string `NEW_AI_TAG`): built in, always listed, runs `PromiDE` (`drs/gamedata_x2/PromiDE.per2`).
  - **AI (CD version)** (`ORIG_AI_TAG`): built in, always listed, runs `RandomGame` (`drs/gamedata_x2/randomgame.per2`).
  - One entry per `.ai` file in `resources/_common/ai` of the game and of every enabled mod, named after the file. DE skips its scenario script `E3-p2.ai` (named in the exe) and labels its own `AI (HD version).ai` with `HD_AI_TAG`.
  - Before this change the list was AI, AI (CD version), AI (HD version), SWGB Classic AI, SWGB Land AI. "AI" and "SWGB Classic AI" ran the same script. The CD and HD entries ran DE's own AIs, which do not know the SWGB units.
  - A mod can add and override files but cannot hide a base-game file, so the three DE entries cannot be removed. The list is now **Closed, AI, AI (CD version), AI (HD version)**, and all three AIs run SWGB Classic AI.
- **Change (SWBG-Data), written by the new `ai_entries.py`:**
  - Removed `SWGB Land AI.per`/`.ai` (the partial land adapter) and the `SWGB Classic AI.ai` listing file. `SWGB Classic AI.per`, the `SWGB Classic/` folder and `swgb_classic_ai.xs` stay.
  - **AI:** `drs/gamedata_x2/PromiDE.per2` contains only `(load "SWGB Classic AI")`, as before. It stays the only file in that folder (see the in-game findings).
  - **AI (HD version):** new `ai/AI (HD version).per` with only `(load "SWGB Classic AI")`. DE uses the mod's copy.
  - **AI (CD version):** DE never used a mod's `randomgame.per2` (tried lower- and upper-case). It does resolve the files that script loads in `resources/_common/ai` (game and mods) before `drs/gamedata_x2`. Its first load, `Promisory\defaultConstants`, is now `ai/Promisory/defaultConstants.per` with only `(load "SWGB Classic AI")`. Every other file that it or DE's `PromiDE.per2` loads directly is a two-line comment stub: 21 `ai/Promisory/*.per` files, and 10 `ai/elite ... .per` files that DE finds before its `drs/gamedata_x2/elite ... .per2`. So DE's own `randomgame.per2` runs SWGB Classic AI and nothing else. If DE ever ran its own `PromiDE.per2`, that would reach SWGB Classic AI the same way.
  - SWBG-Data is a normal (non-data) mod and stays enabled. So while it is enabled, DE's own AIs are replaced in ordinary games too (before, only "AI" was). The docs already say to disable SWBG-Data for ordinary games.
- **In game** (DE build 185872, SWGB Factions Savannah, Moderate, all installed with the installer onto this PC's profile; screenshots in `E:\swbg-round3\shots`). The setup was the human as Galactic Empire and three computer players: AI (CD version), AI and AI (HD version).
  - The lobby's AI dropdown lists only Closed, AI, AI (CD version) and AI (HD version).
  - With the final files there was no AI Script Error. All three players played SWGB Classic AI's opening:
    - Prefab Shelter and Food Processing Center at 0:00, and a Carbon Center at about 2:00;
    - workers trained steadily;
    - `TECH-CCT-1` researched.

    The same was seen with the final layout in two more fresh DE sessions.
  - Before the change, "AI (CD version)" ran DE's own AI. It stopped with an AI Script Error on load (`Promisory\finalingConstants`, line 105, ERR2005 invalid identifier, from `cannon-galleon-line`/`dromon`). After that error, no AI with a later player number did anything for the rest of the match (9 minutes, no build or train command).
  - DE's lookup of mod files in `drs/gamedata_x2` was unreliable once SWBG-Data had more files there:
    - With stubs and an extra `RandomGame.per2` in that folder, DE ran its own `PromiDE.per2` instead of the mod's. A marker in `Promisory\customConstants`, which only DE's PromiDE loads, showed it.
    - In another session, DE took `elite petersen supplement.per2` from the game but the other stubs from the mod. That gave an AI Script Error (ERR2005 `YES` at line 2).

    The stubs therefore live in the ai folder, and `check_single_ai.py` allows only `PromiDE.per2` in `drs/gamedata_x2`.
  - Installing switched this PC's SWBG-Logic to the subscription. The 1.7 update reached the subscribed mod 549437 during the test, so its game files now match this release. The installer, as designed, enabled the subscription and removed its own local SWBG-Logic. The old local copy is backed up in `E:\swbg-round3\backup`.
- **Docs:** SWBG-Logic 1.7 was uploaded to mod 549437 on October 22, 2026 (still Unlisted). README_GENERATED.md (the detailed README), INSTALL.md, PUBLISHING.md and RELEASES.md now say so, and README_GENERATED.md and INSTALL.md say that online play with this release is untested. Links to the mod use the public listing URL.
- **Installer:** Install and `-Repair` delete `SWGB Land AI.ai`, `SWGB Land AI.per` and `SWGB Classic AI.ai` from an existing SWBG-Data (`$RetiredDataFiles`). Install already replaced the whole folder. Repair otherwise only edits `mod-status.json`; it now removes these files too, which was checked on this PC's real install. The lobby help says that every AI choice runs the Classic AI.
- **Tooling:**
  - `ai_entries.py` (new) writes the three entries and the 31 stubs and deletes the retired files. It also fixes a file name whose case differs. `port_classic_ai.py` no longer writes the `.ai` listing file.
  - `check_single_ai.py` (new; release workflow and `package_installer.py`) fails on:
    - any `.ai` file, or any Land AI file, in the payload or `recipe.tsv`;
    - an entry or stub that differs from `ai_entries.py`, or a missing Classic script or XS;
    - any other file in `ai/` or `drs/gamedata_x2/`, including a second file next to `PromiDE.per2` or a file name in another case;
    - an installer `$RetiredDataFiles` list that differs from `ai_entries.RETIRED`.

    With a DE install it also checks DE's side:
    - the exe still names PromiDE, RandomGame, "AI (HD version)" and E3-p2.ai;
    - the three labels are unchanged;
    - DE ships no other `.ai` file;
    - DE's `PromiDE.per2`/`randomgame.per2` load exactly `Promisory\defaultConstants` plus the stubbed files.

    It then runs on 14 mutated copies and catches each.
  - `check_faction_ai.py` lints four roots with the pinned parser: the mod's `PromiDE.per2` and `AI (HD version).per`, and DE's own `PromiDE.per2` and `randomgame.per2` over the stubs.
    - The only findings allowed are conditional duplicate loads. They come from SWGB Classic AI's random personality (42 per root, one per difficulty/mode branch) and from DE randomgame's branch loads of stubbed files. `check_classic_ai.py` lints every preprocessed configuration with zero findings.
    - The old check accepted any output containing `findings: 0`, which the Land AI root always printed, so the 42 were never reported.
  - Removed the Land AI generator and checks: `faction_ai.py`, `check_ai_difficulties.py`, `assemble_ai_difficulties.py` and `outputs/AI-DIFFICULTIES.md` (no longer in the installer's docs). `reserved_unit_ids.py` drops the Land AI symbol list, and `check_faction_clock.py` no longer reads the Land AI.
  - `recipe.tsv`: 3 rows removed and 32 added. `PromiDE.per2` is re-pinned because its comment changed.
  - `test_installer_fake_profile.ps1` has 4 new checks:
    - after an install, after Repair, and after an install over planted leftovers: no `.ai` or Land AI file, the three entries load Classic, and the 32 Promisory/elite files are present;
    - Repair deletes the planted files.
- **Checks:** all of the following pass:
  - `check_single_ai`, `check_faction_ai`;
  - `check_reserved_unit_ids`, `check_civ_tech_trees`, `check_transports`, `check_build_menu`;
  - `check_classic_ai` (775), `check_classic_ages` (144), `check_classic_opening` (267), `check_classic_map_identity` (36), `check_classic_extreme` (782), `check_classic_power_placement` (194) and `check_faction_clock`;
  - `package_installer.py`, including the exe extract self-test;
  - `test_installer_fake_profile.ps1` (123/123).
- Known leftover: `payload/SWBG-Logic/README.md` still says "SWGB Land AI". It was left alone so that SWBG-Logic stays identical to the 1.7 upload. `package_factions.py` now writes "SWGB Classic AI" for the next version.

## Unreleased: round 2 integration, Power Core count, Land AI power, tech tree layout, in-game verification (2026-10-22)

The four entries below (technology trees, transports, worker build menu, default "AI" / Power Core placement) were merged into one build on top of the round 1 integration, with the follow-ups listed here, and tested in DE (build 185872) on this PC with the local SWBG-Logic 1.7.

- **Merge.**
  - The payload DAT was not taken from any branch. It was rebuilt from the round 1 DAT with `transport_garrison.py` and then `fix_build_menu.py`, which keep the reserved-ID remap. Applying them in the other order gives the same bytes (SHA-256 `1a996fb4...`), so the two steps commute. Every branch's checker passes on it: `check_reserved_unit_ids.py`, `check_civ_tech_trees.py`, `check_transports.py` and `check_build_menu.py`. The genieutils-py round trip is exact and the compression is canonical. The DAT is 14,055,552 bytes.
  - `recipe.tsv` was re-pinned with `remap_reserved_unit_ids.refresh_recipe` after each change. Only the two tech tree rows are renamed; the other branches changed hashes only.
  - CHANGELOG, toolkit README and `release.yml` keep every branch's text and check steps.
  - **Bug fixed: `package_installer.py` failed after the transport check** (`dict() got multiple values for keyword argument 'transports'`). The release build would have stopped there. It now also runs `check_build_menu.py` and `check_classic_power_placement.py`.
- **Power Core count (Classic AI, `classic_ai_power_placement.py`).** The source's once-a-minute "too many unpowered buildings" rule (goal 101 > goal 100, which is 2, 1 and then 0 by Tech Level) kept adding cores: 5 extra between 22:00 and 33:00 in a Moderate match. The replay coordinates show three causes:
  - **Geometry.** DE's aura (range 10) reaches a building when the gap between the two collision boxes is under 10. It does not use the centre distance. Evidence from 12 recordings:
    - Troop Centers at offset (9, 9) from their core (centre distance 12.7, box gap 9.9) trained a trooper every 19 s, so they were powered.
    - One at (12, 1), box gap exactly 10.0, took 73 s, so it was unpowered.
    - Every first Troop Center with a larger gap trained at the 25 % rate.

    The observer used a centre distance of 10, so it counted powered Troop Centers as unpowered. It now uses DE's test, with the collision half-sizes from the DAT.
  - **Nurseries and Shipyards** are placed at food sites and on the shore. New cores keep normal placement, so they never reach them. The Moderate match's extra cores came from two nurseries 17-23 tiles from the base. On water maps a Shipyard would have bought a core every minute from Tech Level 3. Neither counts any more. They still work at 25 % speed when unpowered, as before.
  - **One core per unpowered building.** A building that was already unpowered when the newest core (finished or not) was placed no longer counts. Unit IDs grow in creation order, so the observer can tell. A building placed outside the aura after the zone has grown now triggers one core, not one a minute.
  - Cores are still never placed at unpowered buildings (that made it worse).
  - `check_classic_power_placement.py` (194 checks) also checks the geometry, the exclusions and the newest-core rule, compares the half-sizes with the DAT, and replays the in-game evidence. The former centre-distance test fails that replay.
  - In game, one Power Core per AI for the whole match: Hard 27 min, Moderate 35 min, Hardest 26 min.
- **Land AI power (`faction_ai.py`).** The Power Core now comes first. Troop Center, War Center, Spaceport, Research Center and Heavy Weapons Factory wait for it and are placed at it. The core is found with `up-find-local` over every core upgrade and placed with `up-build place-point` (zone 7, fail delta 1, reset above 20). Farms wait for the core, because otherwise they took every 50 carbon.
  - Hard match (before the farm change): core 12:23 and Troop Center 13:35 at offset (9, 9). After that, a trooper every 17-18 s (before: 68 s).
  - Easiest match (with the farm change): core 6:39 and Troop Center 10:31 at the core.
  - `check_ai_difficulties.py` (3,778 checks) covers the placement, the order and the farm gate.
- **Tech tree vs build menu IDs (follow-up a).** No ID change was needed. The tree's Fortress 82, Shield Generator 335 and Shipyard 45 are enabled by the same Tech Level technologies as the worker's foundations 1211, 213 and 1696, so DE shows them as available. In the lobby and in game the nodes show normally; none is greyed or crossed out.
- **Tech tree layout (new, `tech_tree_order.py`).** DE's tree panel stops scrolling at a fixed width. With the source order, the Sith/Jedi Temple (12 nodes), the Fortress (8) and the Prefab Shelter were past the end, for both factions. The building nodes are now ordered production first (Troop Center, Power Core, Mech Factory, factories, centres), then Temple and Fortress, economy, Shipyard, and defenses last. In the lobby and in game the Temple and Fortress columns now show (Jedi Padawan/Knight/Master, Bounty Hunter, Airspeeder, Air Cruiser). The cost is that the last defense nodes (turret and wall upgrades, Mine, Anti-Air Battery) are now cut off, and the panel draws its last columns past the parchment background. `faction_tree_ui.py` writes this order and `check_civ_tech_trees.py` checks it.
- **Checks:** all of the following pass on the payload:
  - `check_reserved_unit_ids`, `check_civ_tech_trees`, `check_transports` and `check_build_menu`;
  - `check_classic_ai` (711 checks, 81 parser configurations), `check_classic_ages` (144), `check_classic_opening` (267), `check_classic_map_identity` (36), `check_classic_extreme` (782) and `check_classic_power_placement` (194);
  - `check_ai_difficulties` (3,778) and `check_faction_ai` (0 findings);
  - the DAT round trip;
  - `package_installer.py`, including the exe extract self-test;
  - `test_installer_fake_profile.ps1` (119/119).
- **In game** (DE build 185872; SWGB Factions Savannah, Shoreline and Sea; small map, All Visible, Fast, sped up to 2.0):

  | Area | Result |
  | --- | --- |
  | Worker build menu (both factions) | Military page at Tech Level 1: Troop Center (Q), Shipyard (W), Light Wall, Sentry Post. At Tech Level 4: Troop Center, Shipyard, Light/Medium Wall, Mech Factory, Sith/Jedi Temple, Sentry Post, Gate, Heavy Weapons Factory, Airbase, Light Turret, Fortress, Anti-Air Turret, each at its own position. |
  | Shipyard foundation | Placed on the shore, it became a working Shipyard (Utility Trawler at Tech Level 1; Transport Ship and warships at Tech Level 4), for both factions. |
  | Layout switch | Both layout buttons appear on the Command Center. Defense layout hides the Shipyard, military layout brings it back. But each layout can be researched only once (see Open). |
  | Tech tree | Shows in the lobby and in game for both factions, including Temple and Fortress after the reorder. |
  | Transports | Troopers load and unload: Assault Mech 7/10 then Ungarrison, Air Transport 5/5 then Unload on the ground, Transport Ship 7/10 then sail and unload on land (Empire). Rebels: Air Transport 5/5 and Transport Ship 5/10, both unloaded on land. |
  | Crash fix | No `reserved group id` or Object Tracker lines in any DE log of the session, no new `AoE2DE*.dmp`, no AI script errors. |
  | Default "AI" (Classic), Hard, Savannah | Tech Level 2 10:00, Tech Level 3 20:56. Troop Center 7:18, 3 tiles from its core. One core in 27 minutes, no Shipyard. |
  | SWGB Land AI, Hard, same match | Tech Level 2 12:31. Core 12:23, Troop Center 13:35 at the core, one trooper per 17-18 s. Farms took the carbon until then; fixed afterwards (farms wait for the core) and checked in the Easiest match. |
  | Moderate, Savannah (2 x "AI") | Tech Level 2 13:32 / 14:07, Tech Level 3 29:58 / 32:22. Troop Centers at offset (9, 9) from their cores. One core each in 35 minutes (before: 5 extra), no Shipyard. |
  | Hardest, Sea (water map) | Shipyard 6:48 / 7:09, Utility Trawlers, Troop Center 9:01 / 10:00 at the core. Tech Level 2 9:28 / 9:53, Tech Level 3 18:25 / 21:26. One core each in 26 minutes. The Rebel AI built 5 Transport Ships (19:15-21:30); whether it loaded them was not observed. |
  | Easiest | Savannah, with the human using only resource cheats. The human clicked Tech Level 2 at 13:43 and the Classic AI researched it at 15:29, when the human's research finished. The human reached Tech Level 3 at about 33:20; the AI stayed at Tech Level 2 through 35:05. Troop Center 7:48, 9 tiles from its core. The SWGB Land AI (enemy, Easiest, with the farm change) built its core at 6:39 (before: 12:23) and its Troop Center at 10:31 at the core, trained a trooper every 32 s, as fast as the Classic AI at this difficulty, and followed the human to Tech Level 2 at 20:10. | |

  Recordings and summaries: `E:\swbg-round2\games`; screenshots: `E:\swbg-round2\shots` and `E:\swbg-inttest\tt*-lobby-*.png`.
- **Open:**
  - **The layout switch works once.** Each Command Center layout technology can be researched only once; DE has no repeatable technologies (its `repeatable` field is set on most normal technologies). After switching to the defense layout and back, both buttons are gone, and the player stays in the military layout without Anti-Air Battery, Shield Generator and Trip Mine. A player who stops in the defense layout has no Shipyard, Mech Factory or Temple. Making it repeatable needs a chain of technology copies, or giving up the layout system. This needs a decision.
  - Saved hotkey profile: this PC's `profile\HOTKEYS\Base Mod - SWBG-Logic.hkp` (kept) still binds the Sentry Post to Q, so in game it shares Q with the Troop Center. New profiles get S.
  - The Rebel Air Transport's sprite and icon render as a blocky blob; the Empire's is a proper shuttle. This build did not change graphics; not investigated.
  - DE's generic texts for the carrier classes: "Ungarrison from this ram" on the Assault Mech, "Transport Ship" on the Air Transport's Unload button.
  - The tech tree misses some lines (Jedi Knight to Jedi Master) and colours the Airspeeder as a common unit. The last defense nodes are cut off (see above).

## Unreleased: technology trees no longer empty (2026-10-21)

- **Bug (in 1.6 and 1.7):** the lobby and in-game technology trees were empty for both factions. The left panel (name, description) and the civ picker were fine.
- **Cause:** DE 101.103.54800 (build 185872) resolves `tech_tree_name` in `civilizations.json` only against its native civs. It never loaded `CivTechTrees/SWGB_EMPIRE.json` or `SWGB_REBELS.json`. It is the same kind of gate as the `data_name` one found in September. The tree files themselves were fine: their schema matches DE's 62 native trees, and every node exists in the DAT and becomes available to its civ. Evidence from three in-game tests in the lobby:
  - `SWGB_EMPIRE.json` replaced by DE's own Britons tree: still empty, so the content was not the cause.
  - `tech_tree_name` `BRITONS`, with the SWGB Empire tree as the mod's `CivTechTrees/BRITONS.json`: the full SWGB tree.
  - `tech_tree_name` `FRANKS` and no mod file: DE's Franks tree.
- **Fix:** each faction uses the native tech tree name of its slot, like `data_name`: Galactic Empire `BRITONS` (slot 1), Rebel Alliance `FRANKS` (slot 2). The trees are now `CivTechTrees/BRITONS.json` and `FRANKS.json`. Only their `civ_id` changed; the nodes are byte-identical. The display name, description, icons and tree content stay SWGB.
  - `faction_civs.py` (names) and `faction_tree_ui.py` (file names; removes the old files) produce this on the next rebuild.
  - The new `apply_native_tech_tree_names.py` applies the same change to an assembled SWBG-Logic. It is idempotent. It converted `payload/`, renamed the two `recipe.tsv` ship rows and re-pinned the three changed hashes with `remap_reserved_unit_ids.refresh_recipe`.
  - The development install still has the old names. Run `apply_native_tech_tree_names.py --logic <SWGB-DE-Factions-Draft>` on it before `package_installer.py --update-payload` or a recipe rebuild.
- **New check:** `check_civ_tech_trees.py` covers:
  - The names: native for the civ's slot, file present, `civ_id` matching, no unused tree files.
  - DE's tree schema: keys, types and enum values.
  - Links and icons: `icons.json` to `materials.json` to the atlas.
  - The DAT: nodes exist and become available to the civ.

  With a DE install, it also compares its pinned native names, keys and enum values with DE's own files and runs its rules on DE's 62 trees (0 problems). It fails on the 1.7 payload (both names) and on two mutated copies (all 8 injected faults found). The release workflow and `package_installer.py` run it.
- **Checks run:** `check_civ_tech_trees.py`, `check_reserved_unit_ids.py`, `check_classic_ai.py --root payload/SWBG-Data --logic payload/SWBG-Logic` (711 checks) and `check_faction_ai.py --root payload/SWBG-Data` (0 findings).
- **In game (DE build 185872, local SWBG-Logic):** the full SWGB trees show in the lobby and in a running skirmish, for both the Galactic Empire and the Rebel Alliance. The user's installed mod was restored afterwards.
- SWBG-Logic stays 1.7. The upload to 549437 is still pending, and it now carries the renamed tree files.

## Unreleased: transports can be loaded and unloaded (2026-10-21)

- **Bug: nothing could board an Assault Mech, Transport Mech or Air Transport.** Troops walked up to them and stopped, and Alt+right-click didn't work either, so no Unload button ever appeared. Garrisoning buildings worked. This was also broken in 1.6, before the reserved-ID remap.
- **Cause:**
  - DE matches garrison (action 3) tasks by the target's class only. Every native DE garrison task is class-targeted: Transport Ship class 20, buildings class 3, rams and the Siege Tower class 13.
  - Where SWGB classes collide in one DE class, the builder (`faction_classes.h` translateTasks) keeps source membership by expanding each class-targeted task into one task per member unit (ClassID -1, UnitID n). SWGB's transports all land in colliding classes: naval 17 and air 59 in class 20, mechs 53 in class 13, gunships and shuttles 48 in class 0, the AT-AT swimmer in class 22.
  - So every boarding task was per-unit, and DE ignores them: 1,150,038 tasks across the three civs. Most also kept SWGB's TargetDiplomacy 0, while DE garrison tasks use 1 or 4.
  - The reserved-ID remap only renumbered these targets.
- **Fix:** a new `transport_garrison.py` step, deterministic and idempotent, at the DE boundary next to the reserved-ID remap. It runs in `package_factions.py` and `install_parity_dat.py`, or on its own for an assembled mod with `--logic DIR`.
  - For each unit, the per-unit garrison tasks into DE-garrisonable units (type 70, trait bit 0, capacity > 0) of one class collapse into one class-targeted task, placed where the first one was. It uses DE's native diplomacy: 4 for class 20, like the Transport Ship, and 1 otherwise, like rams. Task IDs are renumbered and default tasks are kept.
  - Membership is exact in classes 20, 0 and 22. In class 13, four scenario or hero carriers become boardable too: UNIT-FLAKB, UNIT-GUBLCE, Super Star Destroyer and Resurgent Star Destroyer. The step stops if anything else would be added.
  - The `work/` intermediates keep source membership, so the source-parity checks are unaffected.
  - The payload DAT shrinks from 24.6 MB to 14.1 MB, with 230.6 MB raw. Unit IDs are unchanged.
- **New check:** `check_transports.py`, also run by `package_installer.py` and the release workflow. It checks that every targeted transport has class-targeted boarders with DE diplomacy and no per-unit garrison tasks, keeps its trait bit, capacity and ungarrison-capable interface, and that class-20 transports keep their Unload task. It also checks that in both civs every Assault Mech, Hvy Assault Mech, Transport Mech, Air Transport and Transport Ship can be boarded by workers and by trained units.
- **In game (DE build 185872), on SWGB Factions Shoreline:**
  - A diplomacy-only candidate still did not load an Air Transport.
  - With the shipped repair:
    - Workers and Dark Troopers boarded an Air Transport with a plain right-click (3/5). Its Unload button, then a click on the ground, unloaded them (0/5).
    - Dark Troopers boarded a Transport Mech with a plain right-click ("Right-click to garrison inside this ram", 3/6). Ungarrison brought them out (0/6).
  - Workers right-clicking a full-HP mech repair it instead of boarding. That matches SWGB, and Alt+right-click loads them.
  - The Assault Mech and naval Transport Ship were not tested in game, because Mech Factory and Shipyard are missing from the worker build menus (a separate bug). They use the same class-13 and class-20 tasks as the tested units.
  - For the test only, a scratch DAT let the Airbase train the Transport Mech. That change is not shipped.
- `recipe.tsv` was re-pinned with `remap_reserved_unit_ids.refresh_recipe`.

## Unreleased: worker build menu offers every building (2026-10-21)

- **Bug (present in 1.6):** a human player's worker never offered Troop Center, Shipyard, Mech Factory or Temple. The AI built them because it builds by unit ID; a replay shows it placing the Fortress (82) directly, which has no worker button at all. The integration test's guess (Troop Center and Prefab Shelter share button 1) was wrong: those two are on different pages.
- **Three causes, each confirmed in DE (build 185872) with probe DATs on SWGB Factions Shoreline and Sea:**
  - **Kind 11 is not hidden.** Sentry Post, Anti-Air Battery, Shield Generator and Trip Mine kept SWGB interface kind 11 on military positions 1, 2, 5 and 6, the positions of Troop Center, Shipyard, Mech Factory and Temple. The layout switch assumed DE hides kind 11. DE has no third page and shows every kind except 2 on the military page. When two available buildings share a position, one covers the other. The integration screenshot `E:\swbg-inttest\mil3.png` shows Sentry Post at 1, Shield Generator at 5 and Trip Mine at 6.
  - **The layout researches ran at game start.** A technology with no prerequisite and a research time of 0 is researched by DE at the start, even though it has a Command Center button. Both layouts were like that. Every game began in the defense layout, which was researched last, and the Command Center never offered the switch. With a research time of 1 second, the buttons appear and the default is the military layout.
  - **DE never shows the native Dock IDs 45, 133, 47 and 51 in a build menu.** SWGB's Shipyard uses exactly those IDs. Unit 45 stayed hidden on every page and position, also with a land placement, with a native terrain restriction, and as a full copy of the Troop Center. The same Shipyard data at a free ID showed up.
  - DE's page model, from native DE data: kind 2 is the economic page and 10 the military page. Buttons 1-13 are positions; 14 is the next-page arrow (`VILLAGER_BUILD_NEXT`) and 15 cancel; button 0 is never shown. That leaves 26 positions for 29 human-buildable buildings, so three positions still have to be swapped.
- **Fix (SWBG-Logic DAT and hotkeys.json; SWBG-Data strings):**
  - The worker builds the Shipyard through a new foundation, unit 1696 `BLDG-TRAINBOAT-BUILD`, at military position 2. Like the Fortress (1211 -> 82) and Command Center (621 -> 109) foundations, it turns into unit 45 when it is finished. Unit 45 keeps the player's Shipyard upgrades, trains the boats and is what the AI builds. The foundation is enabled together with the Shipyard (Tech Level 1) and reuses its strings, icon and hotkey (W). The Shipyard IDs (45, 133, 47, 51 and the Rebel 3586-3589) are set to button 0.
  - Sentry Post is always at military 7 (hotkey Q -> S).
  - Advanced Infantry Center: button 0. Only an SWGB cheat and hidden AI research enable it, and before this fix it showed as an empty button 7.
  - Anti-Air Battery, Shield Generator and Trip Mine: interface kind 10, button 0 by default.
  - The free Command Center layout research now takes 1 second and moves train buttons (DE attribute 43, "Train Button") instead of the interface kind (141). The defense layout puts the three defenses on W/T/A (2/5/6) in place of the Shipyard, Mech Factory and Temple; the military layout, the default, restores them. Troop Center (Q) and Sentry Post (S) are never displaced.
  - Layout help texts 919010/919011 updated.
  - DAT diff against the previous payload (genieutils-py), per faction: interface kind and button of the 7 defense units, the Advanced Infantry Center button and 8 Shipyard buttons (46 fields in total). Also unit 1696 in all 3 civs, one enable command in TECH-AGE1, both layout effects (36 -> 18 commands) and both layout research times. Restoring those reproduces the old DAT byte for byte. The genieutils-py round trip is exact and the compression canonical.
- **Generator:**
  - New `faction_build_menu.h` (`finalizeFactionBuildMenu()`, called after the hotkey import in `faction_builder.h` and in `extend-defense-menu`).
  - `faction_defense_extension.h`: Sentry at 7, kind 10, attribute-43 layouts with a 1-second research time.
  - Also `faction_defense_validation.h`, `main.cpp` (`construction-menu-report`, `audit-defense-extension`) and `faction_defense_ui.py` (help texts). `faction_hotkeys.py` reads the new Sentry position from the header.
  - The modified builder compiles (MSVC 19.44). A harness running `finalizeFactionBuildMenu()` on the previous payload gives byte for byte the DAT that `fix_build_menu.py` produces. A full `build-factions` run was not repeated.
- **Re-apply on another payload:** `python outputs/toolkit/fix_build_menu.py` (payload/ + `recipe.tsv`), or `--logic <dir> --data <dir>`. It is deterministic and idempotent. It needs unit slot 1696 free (it checks), and its unit IDs are outside 900-999, so it commutes with `remap_reserved_unit_ids.py`.
- **New check:** `check_build_menu.py`, also in the release workflow. It checks the default state and both layout researches, and fails on:
  - two building families sharing a builder/page/position;
  - native Dock IDs on a page;
  - zero-time technologies without prerequisites at a building;
  - buttons 14/15 and interface kinds other than 2/10;
  - a human-reachable building that no layout shows, directly, through its upgrade line or through a foundation;
  - hotkeys.json keys that do not match the position;
  - a military layout that does not restore the default.
  It reports 116 problems on the previous (1.7) payload and passes on this one.
- **In game** (DE build 185872, this exact DAT, SHA-256 `7288bb8c...`; Empire and Rebels): the default military page shows Troop Center, Shipyard, Light Wall and Sentry Post at Tech Level 1. Starting at Castle Age, all 13 positions are right (Troop Center, Shipyard, Light/Medium Wall, Mech Factory, Jedi Temple, Sentry Post, Gate, Heavy Weapons Factory, Airbase, Light Turret, Fortress, Anti-Air Turret), and the economic page shows positions 1-12 as expected. The Command Center offers both layouts. The defense layout shows Shield Generator (5) and Trip Mine (6) and hides Shipyard, Mech Factory and Temple, and the military layout brings them back. A Shipyard foundation placed on the shore became a working Shipyard (Create Utility Trawler). Tooltips were read with OCR; panel crops are in `E:\swbg-fix-a\`. The user's mod files were restored afterwards.
- **Known limit:** DE saves a per-mod hotkey profile (`profile/HOTKEYS/Base Mod - SWBG-Logic.hkp`). A profile saved with the old defaults keeps Q for the Sentry Post until the player resets the hotkeys or rebinds it; the new default S applies to new profiles.
- Other checks: `check_reserved_unit_ids.py` OK; `check_classic_ai.py --root payload/SWBG-Data --logic payload/SWBG-Logic` 711 checks pass; `check_faction_ai.py` 0 findings. `check_faction_hotkeys.py` cannot run: it compares stale work/ intermediates with the current DE `hotkeys.json`, which DE has since changed (its first assertion fails without this change too).

## Unreleased: default "AI" runs the Classic AI, Power Core placement, installer messages (2026-10-22)

Tested in DE (build 185872) on SWGB Factions Savannah, small map, All Visible, Fast (2.0 in game), with an idle human and the local SWBG-Logic 1.7. Recordings and summaries: `E:\swbg-fix-d`.

- **Default "AI" never advanced (Hard, 22 minutes, no research).** The plain "AI" choice ran SWGB Land AI through `PromiDE.per2`.
  - Cause, from an instrumented copy of the shipped Land AI (`cc-add-resource food 1-6` markers) in a new Hard match: its economy reached 500 food only at 14:35, and `(can-research-with-escrow 1)` first held at 14:38, but it researched Tech Level 2 only at 16:00. The worker rules came before the Tech Level rules, and both use the Command Center, which takes a new order only while it is idle. Every pass that found it idle trained another worker (one per 26-33 s; the 67-worker target was never reached). In the 22-minute match that never stopped, so `research` never got the building. Research IDs (1-3), `current-age` and the difficulty fact were fine (markers).
  - Also wrong in the Land AI: DE's new building system was on (25 Prefab Shelters in 15 s at 19:00, farm bursts). Its population fallback table always loaded, because DE's `#load-if-defined` ignores defconsts, so every constant was defined twice, with other values at caps other than 200.
  - Fixed in `faction_ai.py`: Tech Level rules before worker rules, `sn-enable-new-building-system 0`, one table per `POPULATION-CAP-*` symbol and no fallback (like the Classic AI's `ce-FARMCOUNT`). The fixed Land AI reached Tech Level 2 at 16:30 in the same match; its economy, not the rule order, was the limit there.
  - **Decision: `PromiDE.per2` now runs SWGB Classic AI** (`(load "SWGB Classic AI")`, three lines). The Land AI stays a small adapter: no air, naval, diplomacy or Power Core logic, and its Troop Center was unpowered (one trooper per 68 s). The Classic AI carries the source's economy, escrow, age advancement, armies, personalities and map branches and all of the port's DE fixes, and has been played at every difficulty. Like DE's own `PromiDE.per2` (`(load "Promisory\init")`), its load paths resolve in `resources/_common/ai`, so the Classic AI's personality loads and its `(include "swgb_classic_ai.xs")` work unchanged. In game the default "AI" researched the Classic AI's opening technology at 0:26, built its Power Core and then its Troop Center, and reached Tech Level 2 at 10:12 and Tech Level 3 at 20:12 on Hard, with no AI script error and no log errors. SWGB Land AI stays selectable by name.
- **Moderate Classic AI reached Tech Level 2 only at about 20:00: its Troop Center was unpowered.** SWGB buildings without power work at 25 % speed; the port emulates that with a quarter work rate plus a Power Core aura (range 10). The Troop Center (87) has work rate 0.25 and the trooper a 16 s train time. Every AI in the earlier recordings trained one Tech Level 1 trooper per 64-73 s (16 / 0.25 = 64 s, plus the per-difficulty rule delay that its workers show too). The BUILD coordinates show why: in all ten earlier Classic and Land AI games the first Troop Center stood 12-30 tiles from the Power Core. SWGB's engine placed it inside the core's radius when the core came first (the source builds the core first for that reason); DE's placement ignores power. So this is a port bug, not the source design.
  - Fix (`classic_ai_power_placement.py`, also applied by `port_classic_ai.py` and `classic_ai_observer.py`): the XS observer writes the position of the Power Core (finished or under construction) with the fewest power-dependent buildings in range to goals 121/122 (the Command Center if there is no core). The source's 100 `(build X)` actions for Troop Center, Mech Factory, Airbase, Heavy Weapons Factory, Temple, Shield Generator, War Center, Research Center and Spaceport become `(up-set-target-point 121) (up-build place-point 0 c: X)` (zone 7, fail delta 1, reset at 20 and whenever nothing is unpowered). Power Cores, `build-forward`, Shipyards, Nurseries and dropsites keep normal placement.
  - In game: Troop Centers 9-13 tiles from the core, one trooper per 17-19 s at Hard and Moderate. Moderate Tech Level 2 at 12:40 / 12:40, 13:27 / 13:03 and 17:48 / 15:43 (Rebel / Empire, three matches; before: 20:44 / 20:05). Tech Level 3 at 29:17-33:53 (before: 25:21, five minutes after its late Tech Level 2; with full-speed production it now spends more on its army first).
  - An intermediate version also placed new Power Cores at unpowered buildings. The source's once-a-minute "too many unpowered buildings" rule then built a core every minute (9 extra by 31:00), because goal 101 counts by centre distance 10, while DE's aura powered a Troop Center 12.7 tiles away. That part was dropped. With normal core placement one Moderate AI still added 5 cores between 22:00 and 33:00 (open, see below).
- **Hard Empire Troop Center at 10:01 (Rebels 7:42): faithful to the source, left alone.** Both factions run the same source farm rule, `EMPIRE/main/1625` (`farms < ce-FARMCOUNT`, `idle-farm-count == 0`, `sheep-and-forage-too-far`). It comes before the land Troop Center rule (`main/1742`) in source order, as in SWGB. Both AIs placed their first farm at 5:59, when their forage ran out. The Empire kept every new farm worked and placed 9 farms (450 carbon) before its 160-carbon Troop Center; the Rebels' second farm waited for a farmer, so their Troop Center came first. In the Hardest and Moderate matches neither faction built farms at Tech Level 1. No port difference was found.
- **Easiest (not played in game):** `check_classic_ages.py` resolves the Easiest configuration for both factions and all three personalities. Its only Tech Level research rule needs `(players-current-age every-human >= 1)` plus a Troop Center and its Tech Level 1 troopers, and no Tech Level 3/4 rule loads. So it follows the human to Tech Level 2 and stops. The default "AI" now runs the same rules.
- **Installer and Repair messages.** DE writes `"Enabled": false` for every data mod at each start but still lists data mods in the lobby, so telling players to tick SWBG-Logic in My Mods was misleading. The installer, Repair, the exe menu and help, INSTALLER.md and the README now say:
  - make sure **SWBG-Data** is enabled in My Mods;
  - choose **SWBG-Logic** as the Data Mod in the Skirmish lobby; it resets to Default each time;
  - if two SWBG-Logic entries appear, choose the local one (the version is read from the local copy's `info.json`: 1.7); the other is the 549437 subscription.

  `-Repair` still re-enables SWBG-Data, repoints mod 549437's entry and removes stale entries, and its messages say so. The lobby help also says that "AI" and "SWGB Classic AI" both run the Classic AI. INSTALLER.md has a new section, "My Mods, the lobby and Repair", and the garbled `mods\subscribed\549437_*` path is fixed.
- **Checks:**
  - `check_faction_ai.py`: the default entry is exactly the three-line loader. It is linted as a third root beside the AI scripts, so the pinned parser resolves `SWGB Classic AI` and its personalities (0 findings).
  - `check_ai_difficulties.py` (3,761 checks) now uses DE preprocessor semantics: a defconst is not a `#load-if` symbol, and no constant may be defined twice (the shipped Land AI fails this). It also checks that the Command Center's first order is the Tech Level research whenever that is possible, and that the new building system is off.
  - New `check_classic_power_placement.py` (128 checks, also in the release workflow). It checks that the placement settings follow the observer call, that no plain `(build X)` is left for those buildings and every placed build sets goal 121 first, and that cores, Shipyards, Nurseries, dropsites and `build-forward` are unchanged. It also checks the three identical XS copies (block called after the emitter scan, goals 121/122 only, xs-check clean) and idempotency.
  - `check_classic_ai.py` counts the three placement rules (4,540) and reserves goals 120-124; `check_classic_opening.py` accepts the placed Troop Center build.
  - `test_installer_fake_profile.ps1` asserts the new message text.
- **Open:**
  - The Classic AI can keep adding Power Cores (source rule, goal 101 geometry, DE placement).
  - The Land AI has no Power Core placement.
  - The observer does not model the exact range of the SWGB power aura in DE (a Troop Center 12.7 tiles from the core was powered).

## Unreleased: integration build, Classic AI map identity and Extreme fixes, in-game verification (2026-10-21)

The three entries below (reserved unit IDs, installer mod status, Classic AI clock and opening) were merged into one build and tested in DE (build 185872) on this PC: SWGB Factions Savannah, small map, All Visible, Fast (sped up to 2.0 in game), Rebel Classic AI (yellow, allied with an idle human) against Empire Classic AI (red).

- **Merge.**
  - `recipe.tsv` was re-pinned from the merged payload with `remap_reserved_unit_ids.refresh_recipe`, not hand-merged.
  - `SWGB Classic AI.per`: the automatic merge was byte-identical to running `classic_ai_age_clock.py` and `classic_ai_opening.py` on the remapped file.
  - The installer keeps both behaviours: a subscribed 549437 is only used when its game files match the release (shared `Get-SubscribedLogicDiff`), and install and `-Repair` share `Update-ModStatus`.
  - `-Repair` now applies the same matching rule. Before, it re-enabled a stale 1.6 subscription and switched off the local 1.7 copy. If no local copy exists, it refuses and points to Install.
  - `port_classic_ai.py` emits DE unit IDs and applies the age clock, the opening fix and the two new transformations below.
- **Bug: every SWGB map still played as a water map** (Shipyard at about 8:20, Utility Trawlers, transport ships, Troop Center only at 10:00 on Savannah). Two causes, both found with instrumented AI scripts whose `cc-add-resource` markers show up in the recording:
  - DE never applies the maps' `effect_amount 1 1997 0 N`. Resource 1997 stayed 0 for over three minutes in the AI and in AI XS. The `(game-time > 3)` guard only delayed the custom-map water branch. The XS observer now sets resource 1997 from `xsGetMapName(false)` and a table of the 20 maps, on the first rule pass (`classic_ai_map_identity.py`). A probe confirmed that the AI reads a value written with `xsSetPlayerAttribute`.
  - The source's Gaia water detection counts gas-vent types 6482/7091. No shipped map places them, but DE returned more than 10 for both on Savannah (also for 7500, an absent Tauntaun; the forest's 7067 palms are present). The two raw counts are dropped; the fish-line test stays.
  - Result on Hard: no Shipyard, fishing or transports at Tech Level 1, farms from about 6:00, one Prefab Shelter at 0:00.
- **Bug: Extreme opened "AI Script Error ... SWGB Classic AI.per2, Line 19634: ERR2005: Invalid identifier"** (`ce-unit-max`). The `(defconst DIFFICULTY-HARDEST 1)` alias for Extreme does not work, because DE's `#load-if-defined` ignores defconsts. So Extreme ran a mix of rule sets. Every DIFFICULTY-HARDEST conditional now has an Extreme twin (`classic_ai_extreme.py`). Extreme then showed no error, and it opens like Hardest (Power Core 3:35, Troop Center 5:23).
- **New checks:**
  - `check_classic_map_identity.py` (36 checks).
  - `check_classic_extreme.py` (782 checks): Extreme == Hardest under DE's preprocessor semantics for 60 configurations, and every other difficulty is unchanged.
  - Both run in the release workflow. `check_classic_opening.py`, `check_classic_ages.py` and `check_classic_ai.py` read the single-copy view (`untwin`).
  - `check_classic_ai.py` compares maps and unit lines in DE IDs.
- **Fake-profile installer test:** 115/115 checks pass. That includes 16 new ones for a stale (1.6) subscription through install, `-Repair` and a later matching update. Subscribed copies in the test are now full matching copies.
- **In game:**
  - **Crash fix:** a 51-minute Hard match had no `Object Tracker Error: ... reserved group id` lines. Earlier sessions logged 2 and 8. There was no crash and no new crash dump. Moved units were trained and fought: Medics 1636/1642, Bounty Hunters 1657/1663, Dark Trooper 1689, Destroyer 1603 and Anti-Air Destroyer 1615.
  - **Civ picker:** shows the Dark Trooper and Airspeeder unique-unit icons.
  - **Data mod:** the replays' unit IDs prove that the local 1.7 data mod was used. The lobby lists both SWBG-Logic entries, the subscribed 1.6 first.
  - **Difficulties** (Tech Level 2 / 3, Rebel / Empire):

    | Difficulty | Tech Level 2 | Tech Level 3 | Troop Center |
    | --- | --- | --- | --- |
    | Hard | 10:00 / 10:04 | 20:24 / 20:19 | 7:42 / 10:01 |
    | Hardest | 10:05 / 10:11 | 14:47 / 18:41 | 5:48 / 5:03 |
    | Extreme | 10:17 / 10:05 | 19:12 / 19:01 | 5:23 / 5:36 |
    | Moderate | 20:44 / 20:05 | 25:21 (Empire) | 7:25 / 6:41 |

  - Moderate trains its Tech Level 1 troopers slowly: 6-7 by 15:00, the 10th about 19:30. So it reaches Tech Level 2 at about 20:00, not 10-14.
  - **Standard** follows the human:
    - Both AIs stayed at Tech Level 1 for 33 minutes while the human did.
    - They researched Tech Level 2 at 33:03 and Tech Level 3 at 42:57, as the human finished each level (33:03-33:15 and 42:57-43:11). The human used only resource cheats.
    - Easiest was not played.
  - **Default "AI" slot** (`PromiDE`, i.e. SWGB Land AI), Hard:
    - Troop Center at 6:05/6:14 and 13 troopers each by 22:00.
    - No research at all in 22 minutes, not even Tech Level 2 (500 food plus three Level One buildings). Not investigated; the Land AI is unchanged by this build.
  - On Hard, the Empire spends its carbon on farms and builds its Troop Center at 10:00.
- **Found, not fixed (present in 1.6 too, unchanged by this build):**
  - The in-game and lobby technology trees are empty for both factions.
  - A human player's build menu never offers the Troop Center, Mech Factory, Temple or Shipyard. Troop Center (87) and Prefab Shelter share worker button 1; Mech Factory (101) and Power Core share button 5. The AI is not affected.
  - Nothing can garrison into the factions' Assault Mechs (500/514) or the Air Transport. Troopers walk up and stay outside, and there is no Unload button. Trait, capacity and garrison tasks are identical to 1.6. The Fortress works (Alt+right-click, Ungarrison).
  - The moved units 1600/1616 (Strike / Assault Mech variants of other SWGB factions) have no sprite in this Empire/Rebel port. They use the same graphics IDs as before.
  - DE writes `"Enabled": false` for every data mod (subscribed or local SWBG-Logic) at each start. The session logs show DE enabling only SWBG-Data at startup and SWBG-Logic when it is picked in the lobby. That is probably what the 2026-10-20 "re-sync" observation saw. The lobby still offers SWBG-Logic.
  - The `aegis` cheat speeds up the AIs too, so matches with it say nothing about AI timing.

## Unreleased: SWBG-Logic 1.7, reserved unit-ID crash fix (2026-10-21)

- **Crash fix.** DE reserves object IDs 900-999 for unit-class groups (900 + class). SWGB used 98 of them for ordinary units: transport and assault mechs, medics, bounty hunters, the Empire and Rebel unique units, warships, the Sandcrawler and more. Creating one logged `Object Tracker Error: Added object with reserved group id`, corrupted DE's object tracker and led to the intermittent crash at `AoE2DE_s.exe+0x1356be0`. All 98 now use free slots: 900 -> 1431 and 901-999 -> 1598-1695. Slot 1621 is skipped because unit 5012 has a dangling task reference to it; 929 and 956 were unused. The table is committed as `outputs/toolkit/reserved-unit-id-remap.json`.
- **What changed.** DAT: 292 unit slots (98 IDs in 3 civs) moved and 113,026 references rewritten: 110,613 task targets, 1,325 effect commands, 876 unit/copy/base IDs, 99 dead units, 33 transform units, 15 tracking units and 65 tech-tree entries. A structural diff against the 1.6 DAT shows that every changed field went from an old ID to its new ID and nothing else changed (same size). Also rewritten: `unitlines.json` (18), the unique units in `civilizations.json` (3), both CivTechTrees (19), the Classic AI unit constants (10), the `#const` tables of all 20 maps (1,080) and the XS Astromech list (1). Uses of 900-999 that are class groups on purpose stay: the XS building/villager/livestock queries, the aircraft categories and the AI worker count (904). String IDs stay derived from the SWGB IDs.
- **Task targets.** All 110,613 task targets in 900-999 had ClassID -1. They are explicit unit targets from the builder's class expansion (`faction_classes.h`), mostly garrison tasks into transport mechs and the Sandcrawler, plus combat, repair, hunt and aura tasks. None was a class target.
- **Survives a rebuild.** The builder and the work/ intermediates keep SWGB IDs, because the source-parity checks compare by ID. The table is applied where data reaches DE: `install_parity_dat.py` and `package_factions.py` remap the DAT before compressing; `faction_civs`, `faction_maps`, `faction_tree_ui`, `faction_nursery`/`faction_astromech`, `faction_ai`, `port_classic_ai`/`classic_ai_de_lines` and `classic_ai_observer` write the moved IDs; `remap_reserved_unit_ids.py` applies the table to any assembled mod pair and is idempotent. Evidence: applying it to the 1.6 payload reproduces the committed payload byte for byte, and `recipe.tsv` too. Re-running the generators reproduces the shipped IDs: `civilizations.json` byte for byte, all 30,340 map constants, `swgb_factions.xs`, the tech-tree IDs, the 52 Classic AI unit constants and all 111 unit lines after the faction split.
- **Guard.** `check_reserved_unit_ids.py` fails on any unit or unit reference in 900-999. It covers every DAT unit field, the JSON tables, AI, maps and XS, with an explicit class-group allowlist. It also fails on AI or JSON unit IDs that name no unit. `package_installer.py`, `build_installer_recipe.py` and the release workflow run it; CI now installs genieutils-py 0.1.2. It reports 2,002 problems on the 1.6 payload; the fixed payload passes.
- **Installer.** SWBG-Data's AI, maps and scripts name units by ID, so they only match the same SWBG-Logic game files. A subscribed 549437 is now used only if its game files are identical to this release's SWBG-Logic. Otherwise, for example for subscribers still on 1.6, the installer installs and enables the local SWBG-Logic, switches the subscription off and says that multiplayer needs the matching 549437 update. Tested on fake profile folders with matching, older and no subscription.
- SWBG-Logic `info.json` is now version 1.7, matching the next upload of mod 549437. `package_installer.py` keeps it, and SWBG-Data stays 0.0.2-dev. Mod 549437 is still 1.6 until 1.7 is uploaded.
- Tested in game on 2026-10-21 (see the integration entry above). The local development install still has the old IDs; run `remap_reserved_unit_ids.py --logic/--data` on it before rebuilding the recipe.

## Unreleased: installer keeps mod 549437 enabled across DE re-syncs (2026-10-21)

- **Bug (seen 2026-10-20):** the installer enabled `subscribed//549437_SWGB-DE-Factions-Publish`. On the next start DE picked up the listing's rename and downloaded the mod into `549437_SWBG-Logic`. It pointed the entry at that folder and set it to `Enabled: false`, so SWBG-Logic showed as off in My Mods. SWBG-Data (local) stayed enabled. DE's session log shows only SWBG-Data enabled at startup; SWBG-Logic was still offered in the Skirmish Data Mod dropdown.
- **What DE does, as far as the evidence goes.** Sources: DE build 185872, the `mod-status.json` backups, the installer log and DE's session log.
  - DE matches mod 549437's entry by WorkshopID. The entry kept its place in the list: Priority 7 of 8 became 5 of 6 after renumbering.
  - DE rewrote Path, Title and LastUpdate (1792424046017 to 1792519828003, the time of the rename) and reset Enabled to false.
  - The CheckSum did not change (2462092691, the same 1.6 files), so the reset does not need a CheckSum change.
  - The rename and the LastUpdate bump happened together, so which one triggers the reset is not known. A new version (1.7) also bumps LastUpdate, so expect the same reset.
  - The local SWBG-Data entry kept `Enabled: true`, even though DE replaced the installer's `CheckSum: "0"` with the real value.
  - The installer cannot prevent the reset offline. It would need the listing's current title and LastUpdate.
- **Installer:** install and repair now share one mod-status function.
  - If DE has written its own entry for the current `549437_*` folder, the installer enables that entry and removes stale entries whose folder is gone.
  - The pre-install state that `-Uninstall` restores moves from an older folder name to the current entry. Previously, a re-run after the player had re-enabled the mod by hand recorded "enabled" as the prior state.
  - Without such an entry, the stale one is pointed at the current folder, as before.
  - Duplicate entries for the same path are collapsed. Fields DE wrote (CheckSum, LastUpdate, Priority) are kept.
  - The mod is still matched by ID only, and only one Logic mod is ever enabled.
- **New `-Repair`** (exe menu **R**, `Repair-SWGB-DE.cmd`): re-enables SWBG-Data and the one Logic mod in `mod-status.json`, after backing it up, without regenerating anything. It refuses if nothing is installed. It records prior state in `state.json`, so `-Uninstall` still restores the original flags.
- **Messages:** the installer and Repair now tell players to check that SWBG-Data and SWBG-Logic are both enabled in Mods > My Mods, after the first DE start and after every update of mod 549437. They also say that the Skirmish Data Mod dropdown resets to Default every time, so SWBG-Logic must be picked again. If the subscribed folder still has an older title, the installer warns that DE will re-download it and switch it off. INSTALLER.md has a new section, "After an update of mod 549437 (Repair)".
- **Tests:** `outputs/toolkit/test_installer_fake_profile.ps1`, now in the repository, runs the installer against a fake USERPROFILE/LOCALAPPDATA. It covers:
  - migration and both folder names;
  - the 2026-10-20 re-sync (renamed folder plus a duplicate disabled entry), through install and through `-Repair`;
  - a folder already at `549437_SWBG-Logic`;
  - version re-syncs (v1.7 through `-Repair`, v1.8 through install);
  - two downloaded copies, repair after a crash, and repair without an install;
  - uninstall.

  Result: 99/99 checks pass, the original 46 among them. Eight full installs ran from a locally packaged build of this branch. The real DE profile was not touched. The launcher (with the new **R** menu entry) compiles with the .NET Framework `csc.exe`.

## Unreleased: Classic AI Tech Level 1 troopers (2026-10-21)

- **Investigated "no troopers early"** with the 2026-10-20 Moderate (15:13) and Hardest (19:34) recordings and the earlier Savannah ones. The pinned replay parser plus the start-state objects show what each AI built and gathered. None of the 2026-10-20 AIs built a Troop Center (unit 87) before 10:00, and Moderate built none at all. The building the earlier note read as a Troop Center at 3:20-5:38 is unit 12, the Power Core (in this DAT 12 is BLDG-TRAINFOOT1; the Troop Center is 87, where troopers 307/282 train). Troopers become available once a Troop Center exists, so the unit IDs and faction lines were never the problem. In the earlier Savannah recordings, too, the Troop Center appears at 10:00-10:01 in every match that reached ten minutes.
- **Cause 1: Savannah played as a water map.** Each SWGB map tells the AI its identity through resource 1997 (`effect_amount 1 1997 0 N`). DE applies that effect after the game is created: the recordings' start state already has Tech Level 1's effects but resource 1997 = 0. On the first rule pass, the source CUSTOM-MAP branch (identity 0) therefore set special-map WATER and disabled itself. The AIs built a Shipyard at 6:00-7:53 and fishing ships at Tech Level 1, which only the water branch does. On water maps the source builds the Troop Center only after the Shipyard or at 10:00. Every rule that an unset identity can enable now also waits for `(game-time > 3)` (66 rules; rules that need a real identity are unchanged).
- **Cause 2: DE's new building system.** The port's bootstrap set `sn-enable-new-building-system 1`, so every rule pass queued another copy of a requested building. Examples from the recordings: 3-4 Prefab Shelters at 0:00 from the source's single "no shelter yet" rule, four Shipyard placements in one second, eight farms in 28 seconds, and 32 shelters by 19 minutes. These cheap buildings come first in rule order and took the carbon that the Power Core (200), Carbon Center (100) and Troop Center (160) needed. It is now 0, which is SWGB's one-at-a-time queue.
- **Cause 3: the first Carbon Center.** The source's Tech Level 1 rule also needs `dropsite-min-distance carbon > 5`. In DE that counts the straggler trees the maps place 4-8 tiles from the Command Center, and DE's AI reference warns against using it for first dropsites. The Moderate Empire held 100-200 unspent carbon from about 3:00 to 5:38 without building one. The land Troop Center needs Power Core + Food + Carbon centres. Only the first-centre rule drops the distance test; the Tech Level 2 "build as needed" rules keep it.
- Applied with the idempotent `classic_ai_opening.py`; `port_classic_ai.py` applies the same transformation. One SWBG-Data file changes (`SWGB Classic AI.per`, +68/-3 lines), and its `recipe.tsv` hash is updated.
- **New `check_classic_opening.py`** (267 checks) checks that:
  - the building queue is set to 0 once;
  - every identity-0-enabled rule is guarded;
  - all 6 difficulties × 4 modes × 2 factions pass a replay of the map-setup rules with the identity arriving after the first pass. Savannah stays land, Sea stays water and an unmarked map keeps the custom branch. A self-test without the guards reproduces the water regression;
  - the land Tech Level 1 chain holds for every difficulty and faction: first Carbon Center, Troop Center after Power Core + Food + Carbon centres, and Tech Level 1 troopers.
- **`check_classic_ai.py`:** the "native groups preserved" failure was a stale check, not a unitlines bug. Since 104f8cb the mod's `unitlines.json` deliberately replaces DE's lines (they made `(can-train 83)` resolve to another unit). Neither AI uses a DE line name, and every unit-line constant in the shipped scripts resolves. The check now requires SWGB-only lines, no native names, resolving constants, and members in the DAT for every line. It also accepts `--root payload/SWBG-Data --logic payload/SWBG-Logic` puts the AI XS beside the lint copy (DE resolves it from `resources/_common/xs`), and runs xs-check by absolute path. On the payload it passes 711 checks and 81 parser configurations. `check_classic_ages.py` (144 checks, 18 parser configurations), `check_ai_difficulties.py` and `check_faction_ai.py` (0 findings for both AI packages) also pass.
- Expected in game: no Shipyard at Tech Level 1 on Savannah, one shelter at the start, then the Carbon Center, Power Core and Troop Center before 10:00, with Tech Level 1 troopers after that (10 at population 200). Moderate then researches Tech Level 2 once it has 10 troopers and 500 food. Not launched in game. If a Shipyard still appears at Tech Level 1 on Savannah, DE never exposes resource 1997 to the AI at all, rather than late, and the map identity needs another channel.

## Unreleased: Classic AI Tech Level clock (2026-10-21)

- **Investigated "Hardest stays at Tech Level 1"** (2026-10-20 test of a57b592, SWGB Factions Savannah, small map, Fast). The recording shows that both AIs did advance. They researched Tech Level 2 (technology 1) at 10:17 and 10:18. At 11:58 both received the Hardest bonuses that need `current-age == 1`, then researched Tech Level 2 technologies (Upgraded Motivator, Irrigation and others) and built gates and a Mech Factory. The 2026-09-29 Hard test researched Tech Level 2 at 10:12 and 10:24, and Tech Level 3 only at 22:46; the Hardest match ended at 19:34. The shipped AI scripts, DAT and unit lines are byte-identical to the 2026-09-29 install (55/55 payload hashes match). The Tech Level 1 reading came from DE's post-game timeline, which showed no age markers, and from the top bar, which shows the human's own age.
- **Fixed the Tech Level clock.** DE does not restart `current-age-time` for SWGB Tech Levels (technologies 1-3, not AoE2's 101-103). After Tech Level 1 it counts from the start of the game. That is why the Hardest "7 minutes into Tech Level 2" bonus fired at the moment the AIs reached it. All 66 source `current-age-time` conditions (main script and the feeder personality) now read a port clock in goals 114-116, which restarts when `current-age` changes. This restores:
  - the source's 7.5- and 5-minute grace periods before an AI saves for its next Tech Level;
  - the Tech Level 2 builder/gatherer split;
  - the Hardest bonus timing;
  - the Moderate Tech Level 3 economy switch;
  - feeder tributes and the personality-specific timing.
- Applied with `classic_ai_age_clock.py`, which is idempotent. `port_classic_ai.py` emits the same rules and translation. Three SWBG-Data files change: `SWGB Classic AI.per`, `ce-dip-feeder.per` and `cr-dip-feeder.per`. `recipe.tsv` is updated for them.
- **New `check_classic_ages.py`** runs on the payload. It checks that:
  - no raw `current-age-time` remains;
  - the clock is unconditional, precedes every use and owns its goals;
  - an interpreter run of the clock restarts it at each Tech Level;
  - every DE difficulty's age-advancement gates match the source design:
    - Hard, Hardest and Extreme share identical rules;
    - Moderate waits for its Tech Level 1 troopers;
    - Standard follows any human to each level;
    - Easiest follows every human to Tech Level 2 and stops.

  It passes 144 checks, including 18 pinned-parser configurations (6 difficulties × 3 personalities). `check_classic_ai.py` counts the air-dispatch and clock rules (4,537). That script still stops at its pre-existing "native groups preserved" check: since 104f8cb the payload `unitlines.json` no longer carries DE's native lines.
- **Open (resolved in the entry above):** in the 2026-10-20 Moderate match, neither AI trained a trooper in 15 minutes. Moderate's Tech Level 2 needs 10 troopers at population 200, so it could not advance. Hard and Hardest trained none before 10:00. The building first read as a Troop Center at about 3:30 is the Power Core (unit 12).

## 0.0.2-dev: CI-built releases, SWBG-Logic / SWBG-Data (2026-10-19)

- **Mods renamed.** SWBG-Logic is the data mod; it replaces SWGB-DE-Factions-Draft and SWGB-DE-Factions-Publish (their game files were already byte-identical; the published mod 549437 is SWBG-Logic). SWBG-Data is the media mod; it replaces SWGB-DE-Factions-Assets. The Draft-versus-Publish distinction is gone.
- **Installer.** Always generates SWBG-Data. If the player is subscribed to mod 549437 it enables that copy and installs no local SWBG-Logic (removing one an earlier run installed); otherwise it installs a local SWBG-Logic for single player. Exactly one Logic mod and SWBG-Data end up enabled, and it prints that multiplayer needs the subscribed 549437. Old SWGB-DE-Factions-Assets / -Draft / -Publish folders are moved to a backup and their `mod-status.json` entries removed; `-Uninstall` removes both old (if installed by an earlier installer) and new names and restores backed-up folders and entries. The subscription is found by mod ID (`549437_*` folder or WorkshopID), never by title, so the renamed listing (`549437_SWBG-Logic`) and the old folder name both work; a stale entry path is moved to the current folder and any other 549437 entry is switched off. `mod-status.json` priors are now keyed by full mod path (older state files still load). Tested against a fake DE profile: 46/46 checks.
- **Releases are built by GitHub Actions** (`.github/workflows/release.yml`, `windows-latest`) from a pushed `v*` tag or a manual run, and attached to a **draft** release (exe, ZIP, `.sha256`); the workflow never publishes. `package_installer.py` takes `--label`, `--out` and `--payload`, reads the payload from the committed `payload/SWBG-Logic` and `payload/SWBG-Data` (byte-exact, pinned by `recipe.tsv`; refresh with `--update-payload`) and downloads vgmstream r2117 from its official release, checked by SHA-256. `.gitattributes` keeps the payload and installer sources byte-stable across checkouts.
- The GitHub repository was squashed to a single commit; the full history is kept locally (`backup/pre-squash-20261019`).

## 0.0.2-dev: data mod 549437 version 1.6 (2026-10-19)

- Published the 6260af2 data (also labelled 104f8cb) to unlisted mod 549437 as version 1.6, replacing 1.5 / 998582f. Online lobbies now get the Classic AI, DE 185872 civ-gate fix, map/terrain fixes and parity DAT. The published files are byte-identical to the data mod the installer ships (then called the Draft, now SWBG-Logic); checked before upload and again after DE re-downloaded the subscription. The garbled listing description was replaced. Online play on 1.6 is untested.

## 0.0.2-dev: single-file installer exe (2026-10-19)

- `SWGB-DE-Installer-<ver>-<commit>.exe`: a C# launcher (`outputs/installer/exe/SwgbDeSetup.cs`, .NET Framework 4, compiled with Windows' own `csc.exe`) that embeds the installer ZIP unchanged. It verifies the ZIP's SHA-256, extracts it to `%TEMP%`, runs `Install-SWGB-DE.ps1` in its console, passes all options through, returns the exit code and removes the temporary copy. Double-clicked, it offers Install / Uninstall. `-ExtractTo <folder>` only extracts. Unsigned, so SmartScreen warns.
- `build_installer_exe.py` builds it (icon from the Draft's Galactic Empire emblem) and self-tests that `-ExtractTo` reproduces every ZIP member; `package_installer.py` now calls it unless `--no-exe`.
- Repository README added for the public GitHub repository.

## 0.0.2-dev: installer without game assets (2026-10-19)

- New `Install-SWGB-DE.cmd` / `Uninstall-SWGB-DE.cmd` (Windows PowerShell 5.1, no Python/Java). It detects AoE2 DE (Steam 813780 / Microsoft Store), the DE profile, and SWGB Saga (Steam 356500 / GOG) with Expanding Fronts. It refuses if a game or EF (including EF's First Run `_p1` archives) is missing, or if DE is running.
- `installer/SwgbDeBuilder.cs` regenerates the Assets media from the user's SWGB/EF files. It ports `PortSprites.java` plus the SMX Workshop subset it uses, the WAV-to-Wwise-PCM conversion, music slicing (bundled vgmstream r2117) and icon rendering. It also rebuilds the 12 DE icon atlases with DE's own texconv, relocating native textures to the Draft's frozen `materials.json` layout. On this machine, 4,190 generated files are byte- or pixel-identical to the installed 6260af2 reference: 2,414 SMX, 1,386 sound WEM, 38 music WEM, 344 icon DDS and 8 PNG. The atlases' SWGB icon regions are pixel-identical.
- `build_installer_recipe.py` writes the recipe (identifiers and SHA-256 only). `package_installer.py` builds `outputs/releases/SWGB-DE-Installer-<ver>-<commit>.zip` with the project-authored payload and asserts that no game media is included. The installer backs up foreign SWGB-DE folders and `mod-status.json`, enables the Assets mod, is re-runnable, and can uninstall/restore.
- Not regenerated or installed: 643 obsolete, unreferenced `widgetui/textures/swgb` DDS files.

## 0.0.2-dev: Classic AI playable on Hard (2026-09-29)

- **Engine-verified:** Hard, Small SWGB Factions Savannah, Classic AI Rebels vs Classic AI Empire (plus an idle human ally). Both reached Tech Level 2 (~15:00), 3 and 4 (by ~50:00 game time), trained their own faction's armies (troopers, anti-vehicle/missile troopers, mechs, fighters, Jedi, medics, Airspeeders / Dark Troopers, transports, warships) and attacked each other's towns repeatedly. Evidence came from the match recording's AI commands and chat. Other difficulties are untested; the match was not played to a win.
- **Unit lines per faction:** the source line groups listed every SWGB civ's variant, and DE resolved each line to `IDChain[0]`, so the AIs only ever tried to train units neither faction owns (Confederacy trooper 1552, Gungan padawan 183, Wookiee fighter 781...) and never built an army. `classic_ai_de_lines.split_faction_lines` keeps, in source upgrade order, only the members each faction can enable or upgrade into (e.g. Rebel trooper 282→460→422→432). 27 lines get Rebel copies with new LineIDs, and the Rebel constants and air dispatch rule use them. Applied with `apply_ai_faction_lines.py`.
- **Workers:** DE native lines and counting groups are removed from `unitlines.json` (they made `(can-train 83)` resolve to another unit). Worker counts come from the XS observer (goal 120).
- **Other fixes:** AI XS include path is now `swgb_classic_ai.xs` (the old path raised ERR7000). The DE 185872 DLC gate is avoided by giving Empire/Rebels native civ-slot `data_name`s; the picker keeps SWGB names, icons and bonus text. All 20 maps restore Nova/Ore, herds, hunt, predators and holocrons (three condition names were DE built-ins). Also fixed: Regicide, giant-map extras, and 9 SWGB terrains back in their own slots. Parity DAT: Harbor garrisons ships, DE formation categories, and the Classic AI can use its starting Command Center.
- **Known issue:** in one earlier match (before the line fix, with extra debug rules), neither AI started Tech Level 2 despite enough food. Not reproduced since; cause unknown.
- `record_installed_payload.py` refreshes the install report after in-place repairs. The data-upload packager now accepts the civ picker PNGs under `resources/_common/wpfg`.

## Unreleased: Classic AI Hard/Hardest air-attack percentage

- Audited every source `sn-percent-attack-air` rule: in all but one case it equals `sn-percent-attack-soldiers`, so DE's shared soldier pool (aircraft use native military classes) reproduces the source split exactly. The exception is the Hard/Hardest naval attacks (soldiers 0, air 100, boats 100), which previously dropped aircraft. Those rules (and the wonder-kill equivalents) now raise goal 112, and one dispatch rule sends every fighter/bomber/attacker/airspeeder/Air Cruiser (air transports excluded, as in the source) at the closest enemy's buildings. This removes the last no-op substitution in the Hard branch's attack logic.
- Installed into the local Assets Classic AI; pinned-parser lint passes for Hard and Hardest with all three personalities. `port_classic_ai.py` carries the same transformation, but can no longer regenerate from scratch: DE build 185872's native `unitlines.json` leaves too few free group IDs (StopIteration). Not launched in-game; data mod/Dropbox package not rebuilt.

## 0.0.2-dev-compat.1

- Refresh the installed Data mod's UI catalogues with entries from DE build 185872, retaining every previous Star Wars icon mapping and material definition. Keep the defenses.2 DAT, graphics, maps and scripts unchanged.
- Publish the completed defense menus, targeting changes, shield adaptation and matching AI unit-line catalogue to existing unlisted mod 549437 as service version 1.5 (build 998582f). Both players need the current Assets companion.
- Verified installed payload hashes and append-only/idempotent catalogue merging. The reported online dataset-loading failure is not yet confirmed resolved; no game was launched.

## Classic AI release checkpoints

| Git tag | Scope |
| --- | --- |
| `v0.0.2-dev-classic-ai.4-map.1` | `.4` AI/Data with Savannah primary Nova placement repair in Assets; game verification pending. |
| `v0.0.2-dev-classic-ai.4` | Source ground-soldier and warboat count groups, matching script bindings; game verification pending. |
| `v0.0.2-dev-classic-ai.3` | Individual idle-animal nursery commands, source nearest-building/fallback choices; game verification pending. |
| `v0.0.2-dev-classic-ai.2` | Nursery income variants/tooltips, bulk garrison requests, one shared personality draw. |
| `v0.0.2-dev-classic-ai.1` | Complete Computer Classic script translation for Empire/Rebels and source unit groups. |

These experimental checkpoints do not claim full original-engine parity.

## 0.0.2-dev-defenses.2

- Expose the remaining lookout, missile turret, shield generator and trip-mine families through free, repeatable Command Center construction-layout switches; expose sea lookouts on fishing ships. Preserve original costs, prerequisites, existing production and core-defense slots. Add matching hotkeys and descriptive tooltips.
- Restore ground-versus-air targeting through native combat-task selectors. Give visible trip mines the native Petard classification for demolition behavior; SWGB stealth/detector mechanics remain unimplemented.
- Add an explicitly labeled DE shield adaptation: powered, completed generator stacks project bonus maximum health and regeneration; no separate source shield-health pool. Source range/recharge resources feed the map controller. Requires an SWGB Factions map. Native aura overlap, health transitions, placement and demolition still need engine verification.
- Validate 323,456 target pairs, 13,760 aura tasks, construction access/collisions, exact DAT round-trip/collateral restoration, standalone XS and 98 mocked controller scenarios. No game launched. Empire TL4 crash remains unresolved; paused AI port excluded.

## 0.0.2-dev-defenses.1

- Core defensive construction menus: expose light walls, wall upgrades, gates, ground turrets and anti-air turrets in five vacant military-page slots for Empire/Rebels, including Rebel upgraded variants. Preserve costs, research, combat data, AI and Assets; update matching spatial hotkeys. DAT restoration/round-trip and collision checks pass; in-game verification pending. Lookouts, missile turrets, shield generators and mines still require a larger menu solution. See `outputs/DEFENSES.md`.
- Preserve unfinished AI placement work on `ai-port` (`4a09ba6`); fast-forward `master` to the last installed/playable checkpoint `8b5298d` before defensive-menu work.

## Unreleased

- Development attack groups now apply the original target-selection result to group state, preserving deferred searches, no-target waiting/return behavior, ground transport requests and callback mutation order. Original wrapper and composed XS group store match in 3,024 cases. Native task execution and scheduling remain unfinished; installed/share `.4` is unchanged.
- Added isolated building-state diagnostic export/candidate/audit modes for the reported final-age crash. Byte-exact restoration checks pass; the fault's field identity and crash cause remain unresolved. The candidate is excluded from normal builds and installation.

- Savannah map repair reserves seven primary Nova crystals per player on the protected starting terrain, 12–16 tiles from the start, before competing object groups. A Standard-resource replay confirmed the missing-start regression (nearest deposit 78 tiles away). Replacement syntax and recorded-terrain checks pass; installed after DE closed as `.4-map.1`, with AI/Data unchanged. Native placement remains unverified.

- Development visibility records now follow resolved movement, ownership changes and transformation remove/reinsert ordering. Original wrappers/prefix and XS agree on 3,208 compared states, including 520 transformations and subsequent scans. Native event integration remains unfinished; installed `.4` is unchanged.

- Development UnitAI search now preserves shared-cache behavior, normal/follow-target query parameters, enemy-sighting notification conditions and original RNG draw/reseed effects. Original routines and XS agree on 644 searches and 126 base-update entry cases. Native event delivery, RNG synchronization and full UnitAI scheduling remain unfinished; installed `.4` is unchanged.

- Development visibility pipeline now scans the maintained original-order category lists directly. All 3,960 source/XS update-then-scan cases match, including 2,024 retained-buffer returns. Native visibility events, movement-field updates and UnitAI scan-cache gating remain unfinished; installed `.4` is unchanged.

- Development visibility membership now preserves source mask changes, tail insertion, swap-with-last removal, capacity doubling and object-reference repair. Original constructor/update calls and XS replay match 3,960 events, including 26 list expansions. Visibility events still need to be connected to DE; installed `.4` remains unchanged.

- Development visibility filtering now preserves original category/record order, distance-table construction, conditional radius adjustment, LOS cap, five 256-record buffers and stale-buffer early returns. Native source routines and the XS host agree on the complete 1,024-cell table and focused scan cases. Visibility membership/cache updates and native command integration remain unfinished; installed `.4` is unchanged.

- Development Force-user conversion-target selection now follows the original ordered scan: enemy/lookup/state/eligibility gates, maximum-HP weighting, byte-distance clamping and the class-47 distance penalty. All 3,217 source/XS selection cases pass, including the original extended-precision comparison against a stored score. Live LOS scan delivery and conversion orders remain unfinished; installed `.4` is unchanged.

- Development conversion observer now resolves live unit identities, original Force-user ranks and mapped research permissions before applying the original conversion gate. Passed 22,165 getter-contract cases, including 22,137 original conversion calls with the original rank functions executing inside them. Force amount and target immunity remain explicit inputs; execution/chance and native validation are still open. Installed `.4` stays unchanged.

- Development Force-user rank and research observations now preserve separate original/copied unit IDs. Verified 132,440 rank pairs against both original predicates, 2,088 getter contracts, four master-copy probes and the four research-resource mappings. An upgrade audit exposed raw-ID-sensitive targeting; live scoring now preserves upgraded temples' victory priority and economic buildings' rank category. The combined controller passes 70 candidates, 61 source estimates and two ranking passes. Native conversion execution remains unfinished; installed/share `.4` is unchanged.

- Development combat controller now connects per-unit observations and source identity to outgoing/incoming damage aggregation and target scoring/ranking. Ordered pair submission, missing/no-AI enemy handling, incomplete-pass rejection and failure cleanup pass 50 candidate cases, including 41 original-routine estimates and two ranking passes. Native getters and eligibility/modifier delivery still require integration; installed `.4` stays unchanged.

- Development live-combat query adapter reads current attack, armor, base armor, reload and HP through DE XS getters for supplied units. Generated ordered layouts cover all 12,536 combat records; ambiguous duplicate/negative classes and invalid getter results fail explicitly and clear partial estimates. Passed 37,624 mocked-getter cases and 10,597 source damage comparisons. Native runtime verification and unsupported layouts remain open; playable `.4` was reverified in place and is unchanged.

- Development combat-data audit verifies 12,536 original/current combat records and 136,087 ordered effect applications. Ported original set/add/multiply attack and armor table semantics, including ordinal versus class selection, first-duplicate changes, missing-class no-ops, signed overflow and percent rounding; 8,240 source/XS mutation checks pass. Live native attribute observation remains open; installed/share `.4` is unchanged.

- Development combat dispatch now selects original UnitAI routines from source templates or a supplied live unit's identity. Factory-driven eligibility/damage/scoring passes 2,338 pair definitions, 160 estimates and 80 ranking evaluations; actor binding/state reset passes 43,941 identity cases. Recorded the source evaluator's low-damage/no-UnitAI precondition explicitly. Native dynamic observations and orders remain open; installed `.4` is unchanged.

- Development source-identity adapter now includes expected original UnitAI type, derived from source class/volley projectile, and resolves attack/neutrality/conversion kinds for a supplied live unit. All 43,941 adapter checks pass across 21,744 DAT records, with original factory calls validating the 80 distinct source combinations. Previous metadata and dispatch-bridge behavior remain unchanged; native gameplay and installation remain pending.

- Development-only siege, worker, predator, medic and neutrality gates now cover every attack/neutrality routine found in the source UnitAI tables. Added source UnitAI factory selection, including absent-AI classes and building volley-projectile distinctions; checked all signed-short class values plus replacement/allocation-failure branches. Native observation/order integration remains open; installed/share build stays `.4`.

- Development validation now composes base/building/tower/soldier/priest attack and priest-conversion gates with damage, combat estimates, scoring and ranking. All 2,338 pair definitions, 160 estimates and 80 rank evaluations match the original routines; every gate includes allowed and denied cases. This remains a fixture-driven host pipeline, not an installed native controller.

- Development-only original priest conversion eligibility: preserve Force-charge/ignore-Force rules, Padawan/medic exclusions, target immunity and Master/research requirements. All 7,920 source/XS cases match. Conversion execution/chance and live observations remain open; installed/share build stays `.4`.

- Development-only soldier and priest attack gates: preserve Gaia exclusions, action/held-resource restrictions and stance/patrol distance branches. Matched 7,826 soldier and 8,690 priest cases against the source executable and compiled XS, including range-rounding boundaries. Native observations, conversion and attack delivery remain separate; `.4` remains installed.

- Development-only base, tower and building attack eligibility, including the installed Expanded Fronts ground-to-air catalog. All 33,008 source/XS checks match: class domains, invisibility, Gaia restrictions, construction state and ordered exceptions. Specialized mobile-unit predicates and live observations remain open; no installed/share build changed.

- Development-only damage capability wrapper: preserve positive raw-strength fallback for a missing target or UnitAI, attack denial, and real target armor dispatch. Matched 1,616 source wrapper cases and retained the combined combat/ranking checks. Class-specific attack predicates and live observations remain open; installed/share release remains `.4`.

- Development-only armor/damage layer connected to combat estimates and target ranking. Preserve last-duplicate armor matching, repeated weapon contributions, missing-class base armor, terrain clamping, height/special-action/building modifiers and the empty-weapon/minimum-damage distinction. Exact XS host results match 3,728 source damage/modifier cases; a combined pipeline matches 160 combat cases and 80 ranking evaluations using 2,338 source armor-pair definitions. Live eligibility, native attribute queries and attack orders remain open; `.4` remains the installed/share release.

- Development-only combat estimator connected to target scoring/ranking: preserve reload-weighted damage, the source conversion estimate, missing-member/UnitAI handling and survival-time aggregation. Explicit zero-reload states avoid dividing by zero in XS. Exact estimates match 925 original-executable cases; 505 target batches match through 1,010 ranking evaluations. Live damage/visibility queries and orders remain open; installed/share release stays `.4`.

- Development-only source target scorer, connected to the seven-pass ranker. Preserve victory priorities, missing-target scores, the original survival-formula quirk and unordered comparisons; compensate arithmetic for the original x87 intermediate precision. Exact score components, final float32 scores and ranked IDs match 836 original-executable scenarios / 1,672 host evaluations. Combat observations and attack orders remain to be connected; no installed/share build changed.

- Development-only PER/XS dispatch bridge: read owned units' source identity, position and native map zone, then drain ordered stop requests with a fresh owner check. Bounded loops reject stale lookup data, missing/converted units and overlapping player passes. Passed 724 host scenarios / 1,448 dispatch calls plus clean XS and PER checks. Caller pool maintenance and later targeting still need integration; the bridge is not enabled in the installed AI.

- Development-only naval dispatch: preserve ground/boat/air ordering, naval duplicate counts, missing-first-unit cancellation and stale IDs consuming the original first-40 window. All 3,552 dispatch calls match original executable group state and stop requests; the composed XS host matches after each call. Refreshed the 3,261 source planner checks, 4,059 planner host cases and 760 pool host queues. Runtime targeting/commands remain pending; `.4` is still the installed/share release.

- Development-only combined ground/air attack dispatch: connect pool admission, spatial grouping and per-player group state, with the original group initialization, stop-request sequence and Easy/Easiest retreat count. Compared repeated dispatch against the original executable and the composed XS controller. Live observations, PER command delivery, naval dispatch and subsequent targeting remain open; installed/share release is still `.4`.

- Development-only tactical-group lifecycle: port ordered group creation/deletion, sequential IDs, 40-member add/remove behavior and source counters/timestamps. Compared 3,680 source mutations and 4,291 XS host transitions interleaved across eight players. XS reuses freed slots while preserving list order. This state component is not installed or issuing orders; `.4` remains the latest packaged build.

- Development-only army-pool controller: reproduce original tactical-group membership, attack-group totals and eligible ground/air selection. Original executable checks cover 1,582 cases; XS host checks cover 760 queues. Preserve source medic/force-user/transport exclusions, input order and duplicate-count behavior. Not connected to live orders; installed/share checkpoint stays `v0.0.2-dev-classic-ai.4` (`db57ca1`).

- Classic AI army-count follow-up (`v0.0.2-dev-classic-ai.4`): translate total soldier/warboat counts through groups matched to the original executable's class/trait dispatch. Preserve all 34 source comparisons; share identical group definitions so 90 names fit into 87 custom groups. Validated both factions against source classifications and all 81 parser configurations. Assets and Data must be updated together. Native count lifecycle and combat behavior still need game verification; attack/defend counts and separate aircraft commands remain open.
- Development checkpoint: source post-ranking path decisions pass 893 executable-oracle cases and 893 compiled XS controller cases. The unit-identity adapter covers 21,744 current DAT records. These controller components remain outside the installed mod.

- Development only: reproduced original target candidate admission and group validation. Passed 2,160 candidate and 489 group cases against source executable routines, plus 2,160 compiled XS gate cases. Preserves moving-unit exclusion, remembered-building visibility handling, Easy/Easiest worker protection and naval wall/dock exceptions. Live observations, path selection and orders are still pending; installed/delivered build remains `acec8b2`.

- Development only: reproduced original per-class armor damage and combat/building attack modifiers; 3,716 comparisons against isolated source routines pass. Live eligibility, cliff/height queries and shield behavior are still pending. Installed/delivered build remains `acec8b2`.

- Classic AI nursery control now follows the original idle-animal decisions: choose the nearest completed Nursery, try the next nearest when full, and move toward a Command Center/Food Processing Center when no Nursery exists. Individual orders replace bulk garrison requests and leave busy/housed animals alone. Validated against 1,553 isolated source cases and 964 controller host cases; live DE commands and timing remain unverified. Nursery income, DAT and default land AI are unchanged.

- Development only: reproduced original target scoring/sorting and combat-time aggregation, with 3,633 target and 2,562 combat comparisons against isolated source routines. Added a pure XS target ranker with 522 compiled-host cases. Preserve source victory priorities, stable ties, conversion estimates and score quirks. Live inputs/orders and EF's special-target hook remain open; this is not an installed AI update.

- Development only: added isolated original-executable AI checks and a source-derived aircraft selection planner. Verified 3,261 original-routine cases and 4,059 compiled planner cases, including difficulty scaling, separate unit classes, upward rounding and the original 40-candidate grouping limit. The XS planner is not connected to live orders yet; installed/released files remain at `51956db`. See CLASSIC-ENGINE.md.

- Classic AI nursery follow-up: request native garrisoning for 24 eligible animal species; share one weighted personality draw between faction variants; preserve all 4,522 source rule instances. Broaden nursery income to all eight age/Evacuation Protocols variants, add garrison controls to their tooltips, and repair Astromech queries after the aircraft class change. Seven Assets files change; DAT/default land AI stay unchanged. Added source-data checks and an 81-configuration parser matrix. Runtime and 100% engine behavior parity remain unverified; see NURSERIES.md and ORIGINAL-AI.md.

- Added a separately selectable **SWGB Classic AI**, translating the installed Computer Classic include graph for Empire/Rebels: source build orders, escrow, military choices, research, diplomacy personalities, taunt responses, naval/air production and difficulty/mode branches. Added source unit groups, complete worker counting, original chat text, map identity tags and AI-only power/nursery observations. Default land AI and binary DAT remain unchanged. This is an experimental source port; aircraft control and other engine differences prevent a verified 100% match. See ORIGINAL-AI.md.

- Release exports now deliver the latest verified full share package (Assets + local Data mod), matching data-upload ZIP and checksums to `E:\Dropbox\temp\SWBG`, removing older project builds only after copy verification. This is now a standing delivery rule.

- Added original Computer Classic difficulty rules to the Empire/Rebels land AI: population-scaled worker targets, age-following gates, combat reactions and attack timers for Easiest through Hardest. DE Standard maps to Easy; Extreme uses Hardest's strategy. Partial source port with explicit land-strategy adaptations; only the two Assets AI scripts change. Parser and offline decision checks pass; runtime testing remains pending. See AI-DIFFICULTIES.md.
- Added missing AI building requests for the two-building TL3/TL4 prerequisites, with source-graph checks for both factions, and adjusted economy thresholds for small population limits.

- Repaired damage shading across all installed SWGB sprites, including units, deaths, wreckage, projectiles and explosions. Cleared non-neutral mask values in 1,552 files / 77,850 frames while preserving visible pixels and animation geometry. The sprite converter now initializes neutral shading by default. Assets-only repair; runtime confirmation pending.

- Added neutral Ore damage masks at both resolutions and original SWGB resource-bar symbols at every UI scale; verified exact collateral preservation.
- Added a source-ID AI resource catalogue and removed exploration/distance gates that could stall gathering and construction. Requested the first Troop Center/Core earlier. Both AI entry points pass the pinned parser; runtime gathering and military buildup still need a fresh-match check.

- Corrected DE terrain-type bitmask handling, including all three farm-construction terrain stages. Added a narrow patch path and byte-exact collateral audit against the published two-faction checkpoint.
- Added explicit Gaia holocron placement to all 20 faction maps; Savannah places its five holocrons on open grass with less restrictive spacing. Matched the native relic formation sentinel. Replay inspection found no relics in the reported match; new generation and pickup remain to be tested.
- Added neutral damage masks to five Nova sprite variants at both resolutions, retaining bright source pixels and anchors. In-game shading still requires confirmation.

- Added DE behavior adapters for aircraft obstacle traversal and static directional flight graphics, scout auto-exploration, and worker/trooper garrison firepower. Removed incompatible SWGB trait flags that DE interpreted as unrelated abilities. Added serialized and byte-exact collateral checks; in-game behavior remains to be tested.
- Added explicit neutral damage masks to 374 building sprites at both resolutions, preserving every visible pixel and anchor and retaining source flames. Runtime darkening correction remains unverified.
- Confirmed published subscription 549437 and owner update access through Steam sign-in. Updates target that existing unlisted data mod; the asset companion remains a separate local install.
- Installed a separate clean SWGB-DE-Factions-Publish local copy for manual in-game publishing, with eight verified game files and normal mod metadata. Existing Draft/Assets and game rules remain unchanged; publication is pending.
- Added a separate game-files-only data upload ZIP with correct root paths, excluding local documentation and release wrappers implicated in upload validation. It preserves the b944fbf payload; service acceptance and multiplayer remain unverified. Corrected online-sharing instructions.
- Added a TIE Fighter movement-crash candidate: commanded aircraft now use native military classes instead of ambient Bird class. Preserved source flight/combat fields and explicit upgrade/task membership; added aircraft regression checks. Runtime crash resolution remains unverified; music is retained.
- Ported the installed shared SWGB/EF soundtrack, faction opening cues and menu/result music into 38 DE music slots; PCM continuity and decoding checks added. DE controls playlist order and transitions; playback needs runtime verification.
- Fixed Power Cores losing their aura at Tech Levels 2-4 by following the source upgrade family. Corrected work-rate bonus encoding and enabled one visible radius per emitter. Runtime production ratio, overlap and placement preview still require testing.
- Added a verified two-folder ZIP exporter and recipient installation instructions; pre-repair checkpoint 2e2d3d1 is preserved separately.
- Kept the correct faction worker portrait through all 24 worker/job records per faction, including building and resource gathering.
- Changed armed Force users from DE's monk class to infantry, restored ordinary combat task targeting, and added explicit conversion abilities for source units that could convert. Uses native Sun Ce charge behavior with source conversion task times/range; conversion balance and Holocron interactions still need runtime verification.
- Made nursery income proportional to elapsed game seconds, so delayed callbacks do not lose income. AI timers, attack/research times and custom scripts follow game time; game-speed and pause behavior still need runtime checks.
- Replaced 4,644 oversized source icon references and 3,265 source -2 values across Gaia and faction units with DE's -1 no-icon sentinel. Savannah trees in the latest crashing replay used unit icons 1783/1784 against a 757-entry table. Added whole-dataset icon bounds validation; crash resolution still needs an in-game test.
- Routed the normal DE "AI" choice to the faction land script through a mod-local PromiDE.per2 override. The three latest saved faction matches contained native Promisory AI instead of SWGB Land AI. Added pinned standalone parser validation and byte checks for both entry points; in-game load and behavior still need confirmation. Difficulty-specific strategy remains unimplemented.
- Replaced failed Savannah distance-only protection with dedicated GRASS2 starting clearings; the Command Center must spawn on that terrain and forest/water rules cannot replace it.
- Replaced extended icon IDs and custom materials with 72 native building slots, 122 native unit slots and 150 native technology slots. Source artwork now occupies the existing DE atlases at SD/HD/UHD quality; runtime confirmation pending.

- Added explicit 18-tile Savannah start exclusions for forest terrain and scattered palms after replay evidence showed trees within three to four tiles of the Command Centers.
- Resolved shared SWGB worker task graphic selectors to faction-specific animations; converted 32 additional sprites at both resolutions.
- Applied Empire/Rebel temple names to all six source temple variants, including upgraded buildings.
- Moved age advancement to Command Center slot 10 (default G), avoiding the source Imperial availability-tech slot collision; costs and prerequisites are preserved.
- Added companion-loaded custom icon textures/material registration. The preceding data-mod-only atlas failed the user test; this packaging change still needs runtime confirmation.
- Recorded a different in-play null-pointer crash at RVA 0xD103F0. Its exact cause and the build's stability remain unresolved.

- Removed three invalid TL3 upgrade commands matching the new repeated crash dumps.
- Restored native movement/waypoint graphics 2961/2962, previously occupied by SWGB building-fire composites.
- Set faction-specific starting scout resource IDs; Rebels no longer inherit the Stormtrooper ID in the built data.
- Rebuilt custom selection/command icons as a native-style DDS atlas. Pixel/reference checks pass; rendering requires a new game test.
- Identified Infinite Resources as the cause of missing deposits in the latest user test; use Standard/High for economy validation.

- Added the original SWGB/Expanding Fronts AI, prioritizing Easiest difficulty, to the requested TODO.
- Namespaced all map constants after replay evidence identified a DE TREE_C collision (401 becoming terrain 145). Added Savannah start and nearby-Nova placement safeguards; new-match validation pending.
- Reworked unit/technology text IDs into collision-free blocks with derived tooltip offsets. Replaced custom PNG texture references with lossless DDS. Both UI changes require runtime confirmation.

- Staged native flag graphic restoration at slot 1963, relocating the conflicting source graphic and its reference. Intended to address the right-click marker; runtime confirmation pending.

- Staged 585 unique spatial production hotkeys with QWERT/ASDFG/ZXCVB defaults. Serialized DAT bindings and unchanged native control definitions are verified; six special ship-availability buttons remain excluded. Runtime verification pending.

- Staged distinct mappings for all seven source forest types to prevent Savannah clearing rules from erasing unrelated carbon forests. DAT roundtrip and source forest spawn comparisons pass; installation/gameplay verification pending.

- Fixed sparse custom icon tables implicated in the match-start crash at icon 10359. Tables now contain every index in numeric order, with custom materials available in all three lookup categories. Runtime retest pending.

- Added eight source War Center equipment technologies to the experimental land AI. It waits for 12 military population and checks research availability; parser/gameplay verification remains pending.

- Extracted source air/ground target-domain rules and external ID-list exceptions, including technology-gated AT-AT targeting, as a reference for the pending DE combat adapter.

- Identified the external Expanding Fronts resource-producer list and source payout formula. Distinguished eight special map buildings from normal faction production; their generation remains unimplemented.

- Added pinned standalone XS syntax/type validation for the combined Nursery and Astromech script, including staged/package/install hash comparison. DE compilation and runtime remain unverified.

- Added an experimental Astromech Repairs XS adapter for normal-roster aircraft, with source-class eligibility and discrete one-HP recovery every two accumulated seconds. Preserves the existing Nova effect; runtime behavior remains unverified.

- Mapped Force Meditation to DE's native Theocracy resource after comparing source conversion logic and installed DE descriptions; group-conversion recovery still needs a runtime test.
- Added a reachable-resource audit to distinguish implemented native mappings from stored-only special mechanics.

- Set explicit native splash-damage multipliers for imported combat records. A byte-exact collateral audit confirms this is the only DAT change in the checkpoint; runtime damage remains unverified.
- Added a verified local installer that separates the experimental faction data from its checkbox media companion. It does not enable mods or change the base game.

- Added an experimental XS nursery adapter using the source one-second, per-animal food calculation and four applicable upgrades. All 20 faction maps load it; engine compilation and runtime income remain unverified.
- Expanded mechanics export to include flight, collision, blast levels, garrison flags, storage and detailed task parameters.

- Completed static conversion checks for 1,175 required sprites at both resolutions. Documented fixed-paint repairs in seven files, static-pose repetition in one animation, blank-placeholder expansion and four omitted missing fishing overlays.
- Added an experimental source-power adapter: unpowered production at one quarter rate, restored by core/droid auras. Source exemptions and multiplier-upgrade math are checked; engine behavior remains unverified.
- Separated Ore and Nova processing-center drop-off rules and adapted source building families.
- Added a basic land AI with source economy, age advances and faction trooper upgrades; static vocabulary/reference checks only.
- Assembled an uninstalled 0.0.2-dev faction draft with a SHA-256 manifest. Stable 0.0.1 remains unchanged.

- Added a Rebel starting-scout alias for the original map scripts, with source upgrade-equivalence checks.
- Converted 745 source icon references and staged 642 distinct data-mod icon/material bindings. Twenty shared technology icons currently use Imperial artwork.
- Imported the source legacy technology tree within checked native table limits and generated separate Empire/Rebel display panels. Static references and DAT roundtrip pass; UI rendering remains unverified.

- Staged original object-generation logic for 20 full-faction maps; source civilization selectors now use the verified-data scout alias.
- Translated terrain restrictions, placement and forest/resource spawns into native terrain roles, with independent reference checks.
- Added source unit/technology names and help, including faction-specific worker-name decoding, and draft civilization metadata.
- Imported source custom sound groups and frame cues. Converted 1,386 source clips to Wwise PCM containers with independently verified, lossless decoding; engine playback remains unverified.
- Added resource-pile/tree variants and map wildlife to the artwork pipeline. Full-faction output remains an uninstalled draft.

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
