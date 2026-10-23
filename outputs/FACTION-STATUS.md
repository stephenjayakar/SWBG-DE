# Empire and Rebels development status

Current build: **0.0.2-dev, experimental, installed but not enabled**. Stable release **0.0.1** remains installed and unchanged. The full source-game port is not complete.

| Area | Current result | Remaining verification or work |
|---|---|---|
| Unit and technology data | Source costs, prerequisites, production, upgrades and tasks translated; explicit splash multipliers added; raw DE DAT reads back exactly | Cross-engine effect semantics and runtime behavior |
| Artwork | 1,175 required graphics, each at standard and enhanced resolution; pixel/anchor conversion checks | Engine rendering; explicit repairs below |
| Audio | 1,386 losslessly converted clips and source sound bindings | Engine playback; one absent Harbor source clip |
| Maps | 20 original map scripts adapted, including Savannah; source object distributions retained | Individual map generation and play tests; native terrain textures |
| Interface | Source names/help, 642 icon bindings, 181/176 Empire/Rebel technology-panel nodes | Engine UI rendering, civilization emblems, command/hotkey compatibility |
| Economy | Source resource roles, terrain restrictions and separate processing-center drop-off rules | Runtime harvesting, construction and deposit behavior |
| Power | Experimental native aura restores source quarter-speed unpowered buildings to normal production | Overlap, timing, construction state, tile-mask differences and garrisoned droids |
| Opponent AI | Basic land economy, age progression, eight source trooper records, six unit upgrades and eight War Center equipment technologies | DE parser and gameplay; advanced strategy, navy and aircraft |
| Nursery | Source-rate XS adapter attached to all 20 faction maps | Engine compilation, garrison queries, save/load and income verification; see NURSERY-ADAPTER.md |
| Special mechanics | Source data preserved where possible | Aircraft movement/targeting, shields, blast-level semantics and other executable behavior |
| Civilization selection | Separate dataset with Gaia, Empire and Rebels | Does not add factions alongside all native DE civilizations |

## Explicit artwork compromises

Seven source files contain player-color command values outside the source eight-color ramp. Those exceptional pixels use fixed source-palette paint; normal player-color pixels still recolor. Graphic 5582 repeats its static directional poses across its declared animation frames. Four truly blank source placeholders expand into blank declared frames. Four missing fishing overlay files are omitted while retaining the available boat hulls, records, timing and sound references. These are documented repairs, not exact recovery of missing source artwork.

## Power evidence and limits

Read-only inspection of the installed source executable identified normal versus quarter-speed production at addresses 0x555256–0x555286, with training/research consuming that runtime work rate. Power-core and droid ranges come from source resources 18 and 30. The adapter uses DE task 155 with work-rate attribute 13 and multiplier flags, following the [official modding documentation](https://support.ageofempires.com/hc/en-us/articles/15607286588948-Return-of-Rome-Mod-Updates). It preserves exemptions and multiplicative upgrades in static checks. This does not prove that the engine applies multiple explicit target tasks or overlapping emitters as intended.

Source executable SHA-256: `D64E7F0ECC546C3BD833C5C6A7BC97B75EE74940D89B1CB22349B0ACE0F3FC58`.

## Validation boundary

Automated conversion, reference, source-field comparisons and DAT roundtrip checks pass. The combined Nursery/Astromech XS script also passes the standalone XS Check 0.2.29 syntax/type checker; staged, packaged and installed script hashes match. This is not compilation by the DE engine (see faction-xs-validation.json). They cannot establish complete SWGB gameplay in DE. The latest screenshot attempt failed with `SetIsBorderRequired failed: No such interface supported (0x80004002)`. A fresh accessibility-only retry returned the DE window but no game controls. Earlier selection attempts also failed with `foreground window did not report a process id`. No blind menu input or base-game modification was used. The full draft is installed as separate Factions-Draft data and Factions-Assets media mods. All copied file hashes pass; it is not enabled or verified in a match.

## Next development gates

1. Obtain working automated game-window access and verify draft loading, faction selection, UI, worker gathering and basic troop combat.
2. Verify power with one/two cores, mixed recipients, destroyed cores and moving/garrisoned droids; adjust the adapter based on observed behavior.
3. Audit every source-only effect/flag and implement or explicitly bound aircraft, shields and remaining nursery edge cases.
4. Exercise both faction technology paths and the custom AI on Savannah, then broaden map and unit coverage.
5. Create a new tested release only after runtime checks; retain immutable 0.0.1.

The package folder is `SWGB-DE-Factions-Draft`; its file hashes are in `faction-package-manifest.json`. Historical checkpoints in FACTION-PORT.md describe intermediate states and are superseded by this status page.

Installation hashes and paths are recorded in faction-install-report.json. Source splash-damage evidence and the collateral audit are described in COMBAT-ADAPTER.md. The combined assembly folder is installed through toolkit/install_factions.py, which splits media into its checkbox companion.

Force Meditation now targets native Theocracy resource 193; source and native descriptions agree on group conversion recovery. This is a data mapping with pending runtime verification. MECHANICS-AUDIT.md lists reachable resource effects that still lack a native behavior mapping.

Astromech Repairs now has an experimental XS adapter for normal-roster bombers, fighters and air transports. It uses discrete recovery and persistent per-unit remainders. See ASTROMECH-NOTES.md; engine behavior is unverified.

## Latest runtime-access finding

The second DE window exposes a launch dialog stating that the game was started outside Steam and is attempting to restart through Steam. Its accessibility tree includes an OK button, but the supported click failed with `element 1 is not available in cached app state for AoE2DE_s.exe`. A fresh dialog observation followed by Enter failed with `window is not a usable app window`. Both DE windows still fail screenshot capture with `SetIsBorderRequired failed: No such interface supported (0x80004002)`. No successful dismissal or restart has been verified. This launch-dialog/tool targeting issue must be resolved before interpreting the lack of game controls as a mod-loading failure.

On the next fresh window enumeration, the Steam launch dialog was gone. The remaining DE window still failed screenshot capture with 0x80004002, and its accessibility tree exposed only the window itself. Dialog disappearance does not verify a successful game restart or dataset load. Runtime verification remains blocked by supported tool access.

## Match-start crash repair (September 9)

The latest local dump (AoE2DEFR4T6FB6.dmp) records access violation 0xC0000005 at game RVA 0x1AB5518. Captured instructions index a string table by 10359 times 32; 10359 is the custom icon assigned to source unit 359. The generated icon dictionaries had only hundreds of entries but sparse keys above 10000. The repair fills all indexes through the maximum custom ID in Units, Buildings and Techs, uses consistent five-digit keys for numeric/lexical order, and binds each custom material in all three categories. Validation now checks dense ordering and all 642 material/texture references. This addresses the dump-supported table overrun; successful match startup still requires a runtime retest. The earlier dump has a different fault location and is not independently explained by this repair.
