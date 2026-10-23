# Current faction build: testing

Latest change: **remaining defenses and construction layouts**. The worker's
military page always shows Q = Troop Center and S = Sentry Post. At the Command
Center, choose Advanced defense construction layout (default X), then open a
worker's military page: W = anti-air battery (missile turret), T = shield
generator, A = trip mine. Command Center Military construction layout (Z) restores
Shipyard, Mech Factory and Temple at W/T/A. The fishing ship also gains sea lookout access.
Shield protection is a DE bonus-health/regeneration adaptation on SWGB Factions
maps; mines are visible. Test native behavior using [DEFENSES.md](DEFENSES.md).

Core defenses remain on the worker's military construction
page: E = light wall, R = heavier wall, D = gate, Z = ground turret, C = anti-air
turret with default spatial hotkeys. Availability follows original research and
tech levels. Test placement and combat for both factions; see [DEFENSES.md](DEFENSES.md)
for limits. The unfinished AI branch is not included; the Empire TL4 crash remains
unresolved. No game was launched to verify this change.

Current update: optional **SWGB Classic AI**, translating the original source script graph. For this test, install both current Data and Assets folders and use the local **SWGB-DE-Factions-Draft** dataset; published data version 1.4 lacks the new AI unit groups. See [ORIGINAL-AI.md](ORIGINAL-AI.md). The global sprite-shading repair remains present. (Since October 2026 the land AI is removed and every AI choice runs SWGB Classic AI.) The current share ZIP identifies its payload in BUILD.json.

Nursery follow-up: select a captured nerf/bantha and **Alt + right-click a completed
Animal Nursery**. Ten unupgraded animals should generate about 78 food per game
minute. Test age advancement and ungarrisoning; see [NURSERIES.md](NURSERIES.md).
Classic AI now requests animal garrisoning, shares one source personality draw,
and the shared Astromech script finds the current aircraft classes. Runtime checks
are still needed.

Build: 0.0.2-dev, flight/garrison/auto-scout/building-shading candidate. See FLIGHT-GARRISON-SCOUT.md for the focused five-item test. Retains music/Power Core repair 310ed21, worker/Force/time repair 69338c1, icon bounds commit ba04fb3, AI routing commit 97b0f68 and map/icon commit 18dbaf4. The share ZIP's BUILD.json identifies its exact Git commit and payload checksums. Gameplay remains unverified.

1. Fully close DE, then launch through Steam. Start a fresh match.
2. Enable SWGB-DE-Factions-Assets. Select SWGB-DE-Factions-Draft in the Skirmish Data Mod dropdown; its gear icon is expected.
3. Choose Galactic Empire versus Rebel Alliance and custom map SWGB Factions Savannah. These maps require the matching faction dataset.
4. Choose **AI**, **Hard**, and 200 population for the original-AI test (every AI choice runs SWGB Classic AI). Easiest/Standard intentionally wait for human advancement and delay timed attacks. Use Standard starting resources, Tech Level 1, and no cheats for economy/AI testing. Infinite Resources removes resource deposits.
5. Press Enter, type `ninjalui`, then Enter for 100,000 of every resource. `aegis` enables instant building/gathering. `marco` and `polo` reveal the map and remove fog.

Check these requirements:

- Aircraft crash: in a fresh match, select two TIE Fighters and repeatedly move across forests/water, change formation, and attack. Keep music enabled and play past six game minutes. See AIRCRAFT-CRASH.md for the evidence, limitations and focused retest.
- Music: use Standard soundtrack playlist and nonzero Music volume. Empire/Rebels should have their own short opening theme, followed by shared SWGB/EF music. See MUSIC-POWER.md for playlist limitations.
- Power: enable Building and Aura Range Indicator. Compare Troop Center training and War Center research with/without a completed core at each tech level, with aegis off. Powered time should be one quarter of unpowered time. Check placement radius, overlap and core destruction; see MUSIC-POWER.md.
- Select a worker while idle, building, repairing and gathering. Its faction worker portrait should remain correct after every job change.
- Train an Imperial Sith Knight/Master or Rebel Jedi Knight/Master. Right-click an enemy: it should approach and use melee attacks. Separately select **Force Conversion**, then an enemy, to convert. Padawans should attack without a conversion ability. Conversion energy/balance is an experimental DE adaptation; Holocron pickup/drop-off remains a separate test.
- At different speed settings, compare against the in-game clock. Production and AI delays are measured in game seconds. A continuously stocked nursery should credit the same food over the same game-time interval, and none while paused.
- First confirm a fresh match reaches the map without crashing. The current repair removes invalid icon references from Gaia/environmental and unmapped editor records; those objects may have no portrait until their icons are converted. Existing converted faction portraits are retained. This is a candidate crash repair, not an engine-verified fix.
- Selecting workers and buildings displays icons, build-button names and tooltips.
- Workers remain visible while constructing a building and gathering resources.
- Imperial temple variants say Sith Temple; Rebel variants say Jedi Temple.
- Right-click and shift-waypoint markers have no fire or overlapping source graphics.
- The Rebel starting scout is a Rebel scout, not a Stormtrooper. Test trained troops separately.
- Production keys follow QWERT / ASDFG / ZXCVB rows.
- Advancing to Tech Level 3 works; a separate fresh match starting at Tech Level 3/4 also works.
- Age advancement occupies the Command Center's second row, far-right slot (default G). Original prerequisites still apply. From TL3, complete two different qualifying building types, for example a Research Center and Hvy Weapons Factory, before trying TL4.
- Ore and Nova appear with finite resources and can be collected. Source ore is magenta; Nova is green.
- Command Centers start on usable dry ground.

Savannah intentionally contains forests, scattered trees and water. The source script allocates approximately 31% forest and 3% water. Native DE terrain textures remain substitutes. Distance-only protection failed the 12:40 test. The new script creates protected GRASS2 player clearings and restricts Command Centers to them; its forest and water rules only target other terrain. Verify a clear, usable base in a fresh match.

Icons now use DE's existing slots and atlases. The enabled companion changes those UI images, so disable SWGB-DE-Factions-Assets when returning to the normal DE dataset.

The companion also overrides DE's built-in AI entries (AI, AI (CD version), AI (HD version)) with SWGB Classic AI. Disable the companion for normal DE games to restore native AI. In a fresh faction match, verify there is no AI script error and the opponent trains workers, builds prefabs and gathers resources. Engine behavior parity remains unfinished. Passing the standalone parser does not establish engine compatibility. If an error appears, record its file name, line number and error code.

The automated capture tool fails and accessibility exposes no game controls. Static checks cannot verify these gameplay requirements. New local replays and crash dumps can be inspected without uploading them.

References: [official cheats](https://support.ageofempires.com/hc/en-us/articles/24726304415892-Cheat-codes-for-Age-of-Empires-II-Definitive-Edition), [Infinite Resources behavior](https://www.ageofempires.com/news/aoe2de-update-34699/).
