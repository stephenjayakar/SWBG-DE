# Star Wars Galactic Battlegrounds / Expanding Fronts → AoE II DE

Prepared 8 September 2026. **Recommendation: proceed with a small, locally generated data mod, using 2× nearest-neighbor sprites.** Existing trooper animations cover the basic states. The immediate deliverable is an experimental graphics-and-map slice; a faithful SWGB conversion requires additional gameplay work.

## What exists now

| Item | Result |
|---|---|
| Source installation | `E:\GOG Games\Star Wars - Galactic Battlegrounds\Game` |
| Target installation | `E:\SteamLibrary\steamapps\common\AoE2DE` |
| Source data | `genie_x2.dat`, version `VER 5.9`; 16 civilizations including Gaia; 29,106 graphic slots |
| Target data | `VER 8.9`; 60 civilizations including Gaia; 17,068 original graphic slots |
| Runtime observed | DE build 180059; Steam build ID 24094652 |
| Asset inventory | 35,178 DRS entries across installed archives, including duplicate/base/override entries—not that many unique required assets |
| Graphics prototype | Empire and Rebel troopers: idle, walk, attack, death, decay; ten graphics records |
| Resolution | Standard variants at 2× source dimensions; enhanced variants at 4× source dimensions |
| Data prototype | Native DE Archer, Crossbowman and Arbalester lines use the imported graphics. Franks use Rebels; other civ slots use Empire. Original unit names, costs, stats, technology availability, UI, audio and arrows remain. |
| Maps | 18 terrain-layout adaptations, including Savannah; native terrain substitutes and a new DE resource distribution |
| Installed packages | `SWGB-DE-Trooper-MVP` and `SWGB-DE-Maps`, under the primary DE profile’s `mods/local` directory |
| Validation | Native DAT byte-for-byte round trip passes; generated DAT reloads; SMX frame geometry, anchors and pixels survive serialization; map symbols and basic structure checked |
| Outstanding | **No completed in-game load, animation, map-generation or match test.** DE launched, but the computer-use screenshot API failed with `SetIsBorderRequired … 0x80004002`; accessibility exposes no game menus. |

Do not label this build a completed total conversion. It is the first testable slice and a reusable foundation. See `PLAY-ME.md` for selection and rollback instructions.

**Staged follow-up:** `SWGB-DE-Blaster-MVP` adds separate Empire/Rebel projectile records, source bolt graphics, a small impact animation, straight flight, source projectile speeds and source release frames. It has 13 imported graphic records and 26 resolution variants. Serialization and reference checks pass; it remains uninstalled and unverified in the engine while the original local-mod visibility issue is being checked. See `blaster-build-report.json`.

## Scope and acceptance gates

**Gate 0 — Prove the installed prototype.** Select the dataset and Savannah. Check blue Empire and red Rebel troops at normal and enhanced resolution. Move in all eight directions, attack a stationary and moving target, kill units, observe corpses, save and reload. Run a 20-minute skirmish through unit upgrades. Any invisible graphic, direction mismatch, broken player color, startup failure or crash blocks expansion.

**Gate 1 — Recognizable Star Wars skirmish.** Add Empire and Rebel workers, Command Centers, shelters, troop centers, resource processing buildings, a light mech, a heavy weapon, a turret, blaster projectiles and explosions. Retain enough DE behavior to keep gathering, construction, training, upgrades, victory and AI functional. Include replacement names and icons so players can identify what they build. Full worker gather/carry/build/repair states are required, not just an idle worker sprite.

**Gate 2 — SWGB rules MVP.** Implement four resources, Tech Levels 1–4, source costs/build times, a small source technology tree, faction differences and power. Acceptance: Empire vs Rebels can complete an ordinary economic game from TL1 to TL4, with correct production rates, combat counters, upgrades, save/load and victory. A playable fallback with power omitted should be clearly named an approximation.

**Gate 3 — Engine-dependent systems.** Prototype air targeting, shields, stealth/detection, transports and naval behavior separately. Each needs a small test scenario before roster expansion. Keep unproven systems out of the stable dataset.

**Gate 4 — Broad EF content.** Expand shared building/unit families, then faction-specific units, bonuses and technology matrices. The installed source has 15 playable civ records. Reuse DE slots; verify menu, tech-tree, AI and localization behavior before trying to hide unused slots. Changing DAT civ count alone is not proof that the selection UI will behave correctly.

**Gate 5 — Scenarios, campaigns and polish.** Convert scenario terrain, objects and triggers through explicit mappings. Port UI, sound events, music and campaign presentation after the skirmish loop is stable. Do not rename SWGB scenario files to `.aoe2scenario` and expect them to work.

## Asset pipeline

1. **Resolve archive precedence.** Index by `(archive, type, resource ID)` and choose the active source override. For graphics, prefer EF’s `graphics_x2.drs`, then `graphics_x1_p1.drs`, then `graphics_p1.drs` where appropriate. The active main palette comes from `interfac_x2.drs`, resource 50500. An older archive’s resource 50500 produces incorrect colors.
2. **Traverse dependencies from actual units.** Record standing/walking/attack/death/decay graphics, graphic deltas, worker tasks, construction phases, damage graphics, projectiles, explosion units, icons, sounds and technologies. Traverse graph edges with cycle protection. Missing files must produce a manifest error, not a silent placeholder.
3. **Decode by offsets.** The tested SMX Workshop SLP loader assumed a sequential layout and failed on these files. The prototype uses an offset-aware SLP reader, following each frame’s boundary and command-row offsets. Unknown opcodes fail explicitly. Extend this reader for other sprite versions only after encountering and documenting them.
4. **Preserve semantic layers.** Normal palette pixels, player-color pixels, shadow pixels, outline pixels and transparency stay distinct. The prototype maps ordinary colors into DE’s standard palette and player colors into its player palette; this can quantize colors. A later dedicated palette or carefully selected DE palette could improve fidelity.
5. **Scale geometry together.** Standard sprites: pixels, mask dimensions, hotspots and pixel-space delta offsets ×2. Enhanced sprites: ×4. Do not scale tile footprints, collision dimensions, movement speed, range or terrain coordinates merely because art resolution doubled.
6. **Keep timing metadata coherent.** Preserve frames per direction, direction count, mirror mode, sequence flags and total animation duration. Retarget projectile release frames and unit attack delay to the new animation; unchanged frame indices can put a shot after the last frame. Validate walk speed against animation cadence.
7. **Emit named assets.** Use stable names such as `swgb_6981_x1.smx` and `_x2.smx`, with matching DE graphic records. The tested trooper sources store five direction groups for eight logical angles. Preserve that arrangement initially; do not duplicate angles speculatively.
8. **Validate and preview.** Check frame count against angle/mirror metadata, dimensions and anchors, palette bounds, delta targets and file existence. Render contact sheets with multiple player colors and ground-aligned anchors. Binary round trips are necessary but do not replace an in-game direction and draw-order test.

The prototype uses [Tapsa/genieutils](https://github.com/Tapsa/genieutils) for current DAT schemas and [SMX Workshop](https://github.com/ImWG/SMX-Workshop) for SMX serialization. The older sandsmark fork referenced in the supplied context did not cover the installed DE 8.9 schema. Pin dependency commits and target-data hashes rather than assuming any library called “genieutils” is interchangeable.

## Data architecture

Keep DE’s current DAT as the target foundation. Copying the SWGB DAT wholesale would import incompatible structures and references. Use a canonical manifest to describe intended behavior independently of either binary format:

```text
source files + hashes + override order
  → units / graphics / tasks / techs / effects / maps
  → explicit source-to-target ID registry
  → DE dataset + SMX files + localization + maps
  → structural checks + engine smoke tests
```

For every converted object, store its source civ/unit ID, target civ/unit ID, source archive IDs, graphic states, dependencies, source and target costs, tech prerequisites, unsupported fields, compatibility approximation and validation status. Allocate IDs centrally. Duplicate target corpse/projectile records when variants must differ; do not accidentally mutate a shared native record.

Preserve stable ID mappings between builds if save compatibility is desired. Rebuild against each new DE DAT version and refuse to overwrite an installed mod when the source hash or schema changes unexpectedly. Retain the previous package and build report.

The current dataset keeps native DE gameplay to minimize initial changes. That means Britons and Franks retain different DE bonuses and tech availability: they are visual stand-ins, not balanced Empire/Rebel implementations.

## Gameplay translation and experiments

| System | Intended implementation | Required check |
|---|---|---|
| Food, carbon, nova, ore | DE food, wood, gold, stone | Gather, carry, drop-off, trade, tribute, UI and AI all agree |
| TL1–TL4 | Native four age progression with source costs/prerequisites | Every age unlock and upgrade checked |
| Troops, mechs, weapons | DE unit types with translated attack/armor tables | Counter matrix, minimum damage, projectile timing, area damage |
| Temple/holocron | Monk/monastery/relic base | Conversion restrictions, pickup, drop and income |
| Power | Candidate production-rate aura | Train and research rates, radius, overlap, ownership, destruction |
| Shielding | Initially regeneration/defense approximation | State clearly that it is not a second damage-absorbing HP pool |
| Aircraft | Permissive movement plus explicit targeting design | Ground weapons must not acquire air targets just because damage is low |
| Stealth | Dedicated visibility/detection prototype | Enemy vision, reveal, attack, conversion and multiplayer consistency |
| Audio | Map source events to DE custom sound plumbing | Voices, attacks, hits, selection and cooldowns; no event storms |

**Power is plausible, not yet implemented or proven.** Official documentation describes Task 155, Combat Ability 32, an attribute selector, range, diplomacy and multiplier options. Test a building operating at 0.25 normal rate with a 4× restoring aura, but first establish which attribute actually controls both training and research in this build. Test two overlapping cores, core destruction mid-queue, leaving range, upgrades, captured buildings and save/load. Do not assume the effect is non-stacking. [Official modding documentation](https://www.ageofempires.com/news/a-sneak-peek-at-new-content-coming-to-age-of-empires-ii-definitive-edition/)

**Air movement is only part of aircraft support.** The same documentation describes ignoring hard obstructions. This does not establish correct air-vs-ground attack acquisition, formation behavior, landing, transport or terrain transitions. Use a fighter, ground trooper and AA unit in a three-way targeting test before adding an Airbase roster. Armor classes alone do not prevent a unit from choosing an invalid target. [Official obstruction and task notes](https://www.ageofempires.com/news/a-sneak-peek-at-new-content-coming-to-age-of-empires-ii-definitive-edition/)

Shields should stay outside the first faithful-economy gate. Regeneration can approximate durability but changes burst damage, healing and focus-fire behavior. A transformed shielded/unshielded pair may approximate shield depletion, but needs testing for target retention, orders, veterancy and recharge. A second visible HP bar is a separate engine/UI question.

## Map strategy

The shipped pack contains **Desert, WaterMass, Sea, Forest, Shoreline, LandMass, Nova Lake, Nova Assault, Precipice, Islands, Large Sea, Rivers, Team Islands, Tundra, Flats, Swamp, Savannah and Ice Lake**.

These are adaptations of the source generation scripts, not screenshots recreated as maps. They retain the source land/terrain/connection generation rules and substitute native DE terrain IDs. Their object-generation sections are replaced with DE starts and resources: TC, three villagers, scout, six archers, food sources, wood, gold, stone, relics and fish. The six archers make the graphics test immediate; they are an intentional departure from ordinary starts.

**Limits:** resource distribution, fauna and decoration are not faithful ports. Nova Lake and Nova Assault in particular need their signature central deposits restored. Space maps need a distinct terrain/pathing design and were excluded. Fortress, Arena, Forced Deployment and special-mode maps need their starts, walls or objectives translated. The original Savannah script uses grass/forest/water; its name does not imply that the DE Savannah terrain should replace every grass tile.

Next map pass: recursively inline shared includes, translate each object by meaning, retain its count/group/range constraints, and preserve the original source credits. Use native substitutions first; only introduce SWGB terrain textures after terrain restrictions and blending are proven. Keep a compatibility ledger of every changed terrain and object.

Test each map with 2, 4 and 8 players, small/medium/large sizes and several fixed seeds. Check every player has a usable start, reachable four-resource economy, enough build space and a viable route to the enemy (or a naval route for islands). Review chokepoints, shallow-water crossings and forest density visually. A balanced-brace check cannot establish that the DE RMS engine accepted the script.

## Test and release workflow

Keep local content and data packages separate so maps can be tested against ordinary DE. For every build, emit checksums, parser versions, conversion errors, ID mappings and test results. Reject dangling graphics, unexpected schema versions, illegal frame indices and unconverted required states.

Use one tiny test scenario containing all representative units, a building, projectile, wreck and differently colored players. Keep fixed-seed Savannah games for economy and performance checks. Add actual behavioral tests when implementing power, targeting and technologies. Once single-player passes, test two clients with identical package hashes, save/rejoin behavior and a full multiplayer match.

Do not publish this local package automatically. Keep the converter and mapping work separate from installed game artwork. A future installer can build the mod from a user-provided SWGB/EF installation. Review distribution terms and EF contributor permissions before a public asset release.

## Suggested work allocation

Planning estimates for an experienced modder, not delivery promises:

| Work package | Focused effort estimate | Exit criterion |
|---|---:|---|
| Engine check and first corrections | 1–3 days | Troopers render, move, fight, die and survive save/load |
| Representative art and DE-based slice | 5–10 days | Worker, base, troops, mech and effects form a full skirmish |
| Two-faction source economy/tech tree | 10–20 days | TL1–TL4 game with documented rules and AI |
| Power and mechanic spikes | 5–15 days | Measured behavior or explicit fallback decision |
| Maps and multiplayer stabilization | 5–10 days | Seed matrix and full-match tests pass |
| Full roster, factions and presentation | Additional months | Content coverage and balance review |
| Campaign conversion | Separate project | Scenario-by-scenario acceptance |

Prioritize the first three gates. Batch extraction of the entire catalog should follow a proven representative set, not precede it. The next concrete action is the installed Savannah/trooper game test; the next implementation milestone is a worker and a Command Center with complete state coverage.
`nV2 follow-up: Installed Trooper-MVP data plus separate Assets companion: 18 graphics/36 variants, trooper bolts and impacts, Imperial mech Scorpion line and English names. Gear icon is expected. Previous test showed ordinary Archer; lobby dataset selection and new-build rendering remain unverified. See PLAY-ME.md and build-report.json for current instructions/evidence.

Current map coverage update: 20 layouts are installed, including Arena and Motherlode. The Nova maps now preserve their special deposit placement blocks using DE gold. Arena keeps source wall placement with DE stone walls. MAP-COVERAGE.md supersedes the earlier 18-map counts and Nova-deposit omission notes. Engine behavior remains unverified.

Runtime correction: the user's Savannah test was nearly empty. Earlier static tests did not detect invalid raw numeric entity arguments. The converter now emits named constants for object/terrain references across all 20 maps. This concrete parser fix supersedes earlier claims that structural validation established usable map scripts. See COMPLETION-AUDIT.md and replay-diagnostic.json for current evidence.

## Civilization additions

Official DE mod documentation states that the maximum civ count is the official dataset's count. The local additive serialization probe produces 62 entries (Gaia + 59 native + 2 new), but is NOT installed or included in 0.0.1 because serialization does not bypass the engine limit. No additional selectable civilization is claimed. A dedicated Star Wars dataset can use existing slots while leaving normal DE available through its default dataset. Source: https://support.ageofempires.com/hc/en-us/articles/15607286588948-Return-of-Rome-Mod-Updates

## Building work after 0.0.1

Converted six original faction dwelling structures and shadows: graphics 913–924, three frames each, standard/enhanced variants. Staged only in building-assets-staged. Parent graphics 883–888 refer to missing/nonexistent SLP IDs 0–5 and have two real child graphics, so importing the parents as ordinary sprite files is invalid. The converter correctly stopped instead of silently creating blank buildings. Structure preview inspected; construction, damage states and DAT integration remain outstanding.
