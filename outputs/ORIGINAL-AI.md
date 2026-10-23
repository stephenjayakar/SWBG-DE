# Original Computer Classic AI port

**SWGB Classic AI** is the only AI of the two-faction Empire/Rebel port. DE's Skirmish
lobby always lists its built-in **AI**, **AI (CD version)** and **AI (HD version)**; a mod
cannot remove them, so SWBG-Data routes each one here (`outputs/toolkit/ai_entries.py`):
`PromiDE.per2` ("AI") and `AI (HD version).per` contain only `(load "SWGB Classic AI")`.
DE always runs its own `randomgame.per2` for "AI (CD version)", but takes the files it loads
from the mod's ai folder first: its first load, `Promisory\defaultConstants`, loads this AI
and every other file it loads is an empty stub. SWBG-Data ships no `.ai` file, so no further
entry appears. Every choice runs this AI at every difficulty (checked in game on
2026-10-22). The partial SWGB Land AI was
removed in October 2026. This is an experimental source translation, **not a verified
100% behavioral match**.

## Try it

1. Install the matching Data and Assets folders from this release.
2. Start a **new Skirmish** with **SWGB-DE-Factions-Draft** as the Data Mod.
3. Leave the computer player on **AI** (any of the three AI choices runs this AI).
4. Start with **Hard**, 200 population, Tech Level 1, normal starting resources,
   and **SWGB Factions Savannah**. Use Empire against Rebels, then swap factions.
5. Check initial gathering/construction, continued worker production, advancement,
   faction-appropriate military production, and attacks. Rebels randomly favor
   aircraft; Empire randomly favors mechs/heavy weapons. Test a water map next.

Easiest and Standard intentionally delay aggression and follow human advancement.
Standard corresponds to the source's Easy; Extreme uses the Hardest branch.
Existing saves retain their previous script state. The game was not launched
during this update.

The new AI requires this build's **unitlines.json** in the Data mod as well as its
Assets scripts. The existing published subscription is not automatically updated
by installing a local release. Until the new data package is published, use the
local Draft for this test. For online play, every player needs the matching
published data revision and matching Assets; copying only the new AI is insufficient.

## Source and coverage

Source: the installed Expanding Fronts **Computer Classic.per** and its
**Computer Classic/CC_*.per** graph, not a newly written generic opponent and not
the distinct modern EF default AI. All 44 referenced files are included in the
translation, including the three randomized diplomacy personalities.

The compiler preserves 4,522 faction-specialized source rule instances, their
order, original goals/timers, random weights and source population tables.
This total includes alternate difficulty, map and game-mode branches; it does
not mean every rule runs in one match.

Ported script systems include:

- Opening build orders, worker production, resource allocation and escrow.
- Age advancement, building placement requests, research and unit upgrades.
- Empire/Rebel combat-arm choices, supporting armies, aircraft and naval production.
- Rushes, attacks, defense settings, resignation and the source's guarded bonuses.
- Bully, boomer and feeder personalities, diplomacy, tribute and taunt responses.
- Source difficulty branches and population tables from 25 to 1,000 in steps of 25.
- Random-map, Death Match, Wonder Race and Defend the Wonder script branches.

The unit groups include source groups and additional compatibility groups.
Worker counting includes every current job/gender variant while training still
requests the ordinary worker. Faction upgrade aliases resolve to distinct source
technologies: for example, Trooper is tech 261 for Empire and 264 for Rebels.
Source goal constants remain case-sensitive: `FOOD=2` must never replace the
engine's `food` resource identifier.

The army-count follow-up translates total `soldier-count` and `warboat-count`
conditions into groups selected by original SWGB classes and boat traits. This
prevents DE's different classification of aircraft from inflating the ground
army count. Both factions retain all 17 affected source comparisons and their
thresholds. Ninety named groups share 87 distinct definitions, preserving the
native groups and staying within DE's custom-group range. Install the matching
Assets and Data together: the group IDs and script bindings change together.
The original classification routine verifies membership offline; DE's live count
updates after training, death, upgrades, conversion and garrisoning still need
in-game checks. Attack/defend counts require tactical group membership and remain
separate work.

The nursery follow-up adds individual native animal-garrison requests for all 24 eligible
species, recognizes every nursery age/Evacuation Protocols variant for income, and documents the
player controls in NURSERIES.md. Personality selection now makes one source
weighted draw and shares it between the guarded faction variants. This removes
the previous extra random draw. The source rules and their order remain intact.

All 20 faction RMS maps carry an isolated map identity in unused resource 1997.
Only this metadata line changes; terrain, placement and resource distribution
remain unchanged. The AI uses it to preserve each source map branch without
depending on DE recognizing SWGB map names. Unmarked maps take the generic custom
map branch. Original AI response strings use a separate string-ID range.

DE never applies the maps' `effect_amount 1 1997 0 N`. A probe on 2026-10-21 (Savannah,
SWBG-Logic 1.7) read resource 1997 from the AI and from AI XS: both stayed 0 for over three
minutes, while resource 2018, which the DAT sets, read 10 through both. So the AI took the
custom branch, which sets special-map WATER and disables itself, and every SWGB map,
Savannah included, played as a water map (see the Troop Center row below). The same probe
showed that AI XS reads the map's file name (`xsGetMapName(false)`) and that a value written
with `xsSetPlayerAttribute` is what `up-resource-amount 1997` reads. The XS observer, which
the AI calls at the top of every rule pass, now sets resource 1997 from a table of the 20
maps while it is still 0 (`classic_ai_map_identity.py`, checked by
`check_classic_map_identity.py`). The RMS lines stay as the source of that table. Rules that
a still-unset identity can enable also wait for `(game-time > 3)` (66 rules,
`classic_ai_opening.py`), so a map outside the table still takes the custom branch, after 3 s.

The source's Gaia water detection was the second way into the water branch. It tests
`(cc-players-unit-type-count 0 7091 > 0)`, `(... 6482 > 0)` (carbon gas vents) or at least
30 fish. No SWGB Factions map places gas vents, but in DE both raw counts read more than 10
on Savannah at 0:04, and so did 7500 (a Tauntaun, also absent) and the 7067 palms that the
forest terrain places; 4000-6000 read 0. Raw counts of these high type IDs are not reliable
in DE, while the fish line (an exact unitlines.json group) read 20-29. The two vent tests are
dropped from the rule (`classic_ai_map_identity.py`), which is what the source engine
evaluates on the shipped maps.

## Remaining differences and unverified behavior

| Area | Current handling / remaining work |
| --- | --- |
| Separate aircraft control | Source aircraft attack percentages are retained in goal 102, but DE has no equivalent separate native aircraft army pool. Aircraft production is translated; attack grouping/counting still follows DE. Implement and compare a dedicated controller before claiming parity. |
| Power observation | An AI-only XS observer counts eligible buildings outside the installed emitters' radius and exposes the result to the original rules. Source threshold and timers are retained. Boundary geometry, completed-building detection and observer execution need in-game verification. |
| Power Core placement | SWGB's engine placed a building inside a Power Core's radius when the core came first, so the source never places buildings itself; DE's placement ignores power. In all ten 2026-10-21 Savannah games before this fix, the first Troop Center stood 12-30 tiles from the Power Core and worked at the unpowered quarter rate: one Tech Level 1 trooper per 64-73 s instead of 16 s, so Moderate (10 troopers before Tech Level 2) reached Tech Level 2 only at about 20:00. `classic_ai_power_placement.py`: the XS observer also writes the position of the Power Core (finished or under construction) with the fewest power-dependent buildings in range (goals 121/122, else the Command Center), and the source's `(build X)` for Troop Center, Mech Factory, Airbase, Heavy Weapons Factory, Temple, Shield Generator, War Center, Research Center and Spaceport become `up-build place-point` there (zone 7, growing by 1 on failure, reset at 20). Power Cores, `build-forward`, Shipyards, Nurseries and dropsites keep normal placement. In game (Moderate, 3 matches) the Troop Center went up 9-13 tiles from the core and trained a trooper every 18-19 s; Tech Level 2 came at 12:40-17:48. The source's once-a-minute "too many unpowered buildings" rule (goal 101 > goal 100) kept adding Power Cores (5 extra between 22:00 and 33:00 in one Moderate match). The count now follows DE: a building is powered when the gap between its collision box and the core's is under the aura range of 10 (a Troop Center at offset (9, 9), centre distance 12.7, trained at full speed; one at (12, 1), gap 10.0, at the quarter rate). Nurseries and Shipyards, which a normally placed core never reaches, are not counted, and a building that was already unpowered when the newest core was placed does not count again. Placing cores at unpowered buildings did not help (9 extra cores by 31:00 in one test) and stays dropped. In game (2026-10-22) every Hard, Moderate and Hardest AI kept one core for 26-35 minutes. Checked by `check_classic_power_placement.py`. |
| Nursery handling | XS reports nursery capacity. Classic individually tasks idle animals to the nearest completed nursery, with the source second-nursery and economic-building fallbacks. Replaces bulk commands with a once-per-game-second PER/XS bridge. Native idle/action reports, orders/pathfinding, source per-animal scheduling and delayed headroom accounting still need comparison in game. See NURSERIES.md. |
| Legacy strategic numbers | Nine old settings are retained at their documented numeric IDs. DE may ignore or implement them differently: support escorts, defense priorities/distances, transport escorts and alliance-hit thresholds. |
| Legacy submarine alias | `SUB-ARTILLERY-LINE` is absent from the installed EF UnitLines table. The candidate interprets it as the Gungan Cruiser/Advanced Cruiser pair (818/805), based on its naval-siege use. Its original built-in binding remains unverified. |
| Loader compatibility | SWGB game-mode names are normalized to DE names. This also activates intended branches whose old AoE spelling could be dormant in SWGB. Extreme aliases Hardest because SWGB has no Extreme. |
| Engine startup | DE's initial exploration gate is cleared so source construction requests can run in this dataset. DE's new building system stays off (`sn-enable-new-building-system 0`): like SWGB, the engine queues a building type only when none is waiting or under construction. With it on, every rule pass queued another copy, for example 3-4 Prefab Shelters at 0:00 from the source's single "no shelter yet" rule and 32 shelters by 19 minutes. Original economy percentages remain in control. |
| Troop Center at Tech Level 1 | The 2026-10-20 recordings showed no Troop Center before 10:00 on Hard/Hardest and none in 15 minutes on Moderate, so no Tech Level 1 troopers and no Moderate Tech Level 2. Three causes, fixed by `classic_ai_opening.py` and `classic_ai_map_identity.py`: the missing map identity above (Savannah ran the water branch: Shipyard and fishing ships at Tech Level 1, Troop Center only after the Shipyard or 10:00); the new building system's duplicate queueing, which spent the carbon the Power Core, Carbon Center and Troop Center needed; and the first Carbon Center's `dropsite-min-distance carbon > 5` test. In DE that test counts the straggler trees the maps place 4-8 tiles from the Command Center (DE's AI reference warns against it for first dropsites), so only the first-centre rule drops it; the land Troop Center needs that centre. `check_classic_opening.py` replays the map-setup rules and checks the chain. Not yet confirmed in a match. |
| Tech Level timing | DE only restarts its age clock for AoE2's own age technologies. SWGB Tech Levels 2-4 (technologies 1-3) do not restart it, so the native `current-age-time` fact would count from the start of the game. The port keeps its own clock (goals 114-116) and translates all 66 source `current-age-time` conditions to use it. DE's post-game timeline also showed no age markers in the 2026-10-20 Hardest test, although both AIs reached Tech Level 2 at 11:58, so don't use the timeline or the age shown for your own player as evidence of an AI's Tech Level. To see an AI's Tech Level, look at the replay's research commands (technologies 1-3) or at the AI's Tech Level 2+ buildings and research. `current-age` itself is correct. |
| Random sequence | Both guarded faction variants reuse one personality draw, with the original weights. This fixes the port's extra draw; different engine random-number consumption can still produce different matches from identical seeds. |
| Engine behavior | Navigation, targeting, army classification, difficulty scaling, force-user abilities, holocron collection and transport/garrison control are still DE/mod behavior. Source rules alone cannot guarantee original engine behavior. |
| Taunt presentation | Original AI response text is included. DE's taunt audio and player-facing taunt numbering have not been replaced. |
| Runtime and multiplayer | Not tested in the running game. Parser success is not proof of loading, stability, useful play or synchronization. |

This port deliberately retains source decisions that can be weak or surprising.
For example, specific-unit enemy checks remain faction-specific rather than being
silently changed to count all factions' versions.

## Rebuild and audit

The next aircraft controller has a source-bytecode differential-test foundation
and checked XS selection/target-ranking layers; see **CLASSIC-ENGINE.md**. Those
combat layers are not wired into the installed AI yet. The nursery command bridge
is a separate, narrower runtime update.

`outputs/toolkit/main.cpp` adds a read-only `source-ai-lines` export command.
The source/raw and current-DAT exports must already exist in `work/original-ai`.
Generate with `port_classic_ai.py`, then `classic_ai_observer.py`; validate with
`check_classic_ai.py`. The latter uses the pinned independent PER parser and
XS checker, checks map collateral and group/technology references, and exercises
the difficulty/mode/population preprocessor matrix. It does not simulate a match.

The follow-up exercises **81 independent parser configurations**, resolving loaded
files and all personality choices, all 240 difficulty/population combinations, and the XS checker
without warnings. It includes **88 SWGB/compatibility unit groups** and **109 source
AI response strings**. No engine or multiplayer test was performed.

`work/original-ai/translation.json` records source hashes, translated rule hashes,
bindings, map identities and legacy settings. `outputs/original-ai-validation.json`
records verified payload hashes and the offline results. The assembler permits
only the Classic scripts, new unit-group JSON, map identity lines and AI chat
strings; unrelated payload changes are rejected.

The nursery follow-up uses `stage_classic_parity.py`, `check_classic_parity.py`,
and `assemble_classic_parity.py` after generating and checking Classic scripts.
Generate the shared XS with `faction_nursery.py --root work/classic-parity/patch`
and a staged copy of the current 20 maps; do not rebuild from the paused expansion
cache. Its additional report is `outputs/classic-parity-validation.json`. The
follow-up changes exactly seven Assets files; binary DAT, unit groups, maps,
graphics and default land AI are unchanged.

The individual nursery controller uses `classic_nursery_bridge.py` and
`classic_nursery_controller.xs`, emitted by the usual compiler/observer generators.
After source-oracle/controller checks and the full Classic parser matrix,
`assemble_classic_nursery_engine.py` permits exactly two PER/XS replacements.
The prior bulk-garrison build is **51956db** (`v0.0.2-dev-classic-ai.2`); its global
nursery income and tooltip improvements are preserved.

The pre-nursery checkpoint is **26a84f0** (`v0.0.2-dev-classic-ai.1`). The earlier
rollback checkpoint is **d5131ec** on `master`; this experiment is on
**codex/original-ai-port**. The paused all-faction expansion is not included.

References: [SWGB AI scripting differences](https://airef.github.io/resources/articles/swgb-scripting.html),
[PER command reference](https://airef.github.io/commands/commands-details.html),
[official DE XS reference](https://www.forgottenempires.net/age-of-empires-ii-definitive-edition/xs-scripting-in-age-of-empires-ii-definitive-edition).
