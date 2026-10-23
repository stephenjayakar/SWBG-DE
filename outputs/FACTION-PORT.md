# Imperial/Rebel full port — working contract

User confirmed the building/trail preview works and lasers look great. User now requests autonomous completion of all Imperial/Rebel logic and assets with SWGB/Expanding Fronts behavior, and will be AFK. Do not request manual checks. Preserve 0.0.1 and Git release history. User revised the stop threshold to 10% remaining usage; check account usage periodically and stop at that threshold.

The next implementation is a dedicated faction dataset, not a claim that the current DE Archer/Scorpion reskins reproduce SWGB. Existing DE remains available by selecting the default dataset. Extra civ slots beyond the official count are not a supported solution; a dedicated roster is permitted by the documented civilization-count limit.

Required work covers source economic units, resources, production buildings, technologies/upgrades/civ bonuses, all ordinary faction military lines, projectiles/trails, workers and their work animations, icons/names/help, sounds, death/rubble/construction/damage, map starting objects, and source-specific mechanics such as air units, power and shields. Missing engine semantics must be explicitly implemented or remain marked incomplete; copying numeric task/effect IDs is not proof of equivalent behavior.

## Source extraction

Run `work/dat-build/Release/portdat.exe source-manifest work/ef.raw work/faction-source`.

The exporter writes civs, unit properties, costs, production locations/times/buttons, technologies, prerequisite edges, effect commands, civ resources, task actions/graphics, graphic metadata and composite edges. Units cover Gaia plus source civs 1 and 3; shared technology/effect/task/graphic tables cover the installed source dataset. Source civ entries still contain other-faction/scenario units, so table size must not be presented as the faction's playable roster.

Measured extraction: 1,249 technologies, 5,339 effect commands, 22,351 task rows, 29,061 populated graphics, 30,911 graphic-child edges and 21,744 populated unit entries across the three inspected civs. The next importer must derive reachable faction production/upgrade dependencies, map source tasks into DE's per-unit task storage, translate resource/armor/effect semantics, and retain the native schema envelope.

Current confirmed source mechanics include projectile tracking mode 2 / density 0.035 and building composite parent/child structures. Current preview's source-cost and technology parity is incomplete. Runtime automation remains limited by the capture error; use direct artifact/replay/schema checks where they establish evidence and do not claim they establish behavior they cannot measure.

## Source-rule intermediate

`build-factions work/de.raw work/factions.raw` now constructs a native-DE-schema intermediate with source Gaia/Empire/Rebels, 7,966 source unit slots per civ, 1,249 source technology records, source costs/production/prerequisites/effects, source graphics indices and migrated per-unit task lists. `roundtrip` rereads and reproduces it byte exactly. `de-manifest work/factions.raw work/faction-target` plus `python outputs/toolkit/check_faction_parity.py` verifies exported source fields after civ-ID remapping. The intermediate is NOT installed: numeric parity is not equivalent engine behavior.

The AGE source at commit 0bd1b417ca6d77aa0b8a2e84a37f2d5f178944de confirms concrete incompatible semantics in AGE_Frame/Lists.cpp: SWGB class 58 is Workers while DE class 4 is Civilian; SWGB 29 is Nova while DE 32 is Gold Mine; SWGB resource 18 is Power Core Range. Tasks 132/136 are Pickup/Deposit Unit, not shield/power operations. Therefore source class/resource IDs cannot be copied blindly. The next conversion stage must translate units, task class filters and class-targeted effects consistently, and implement power/shield mechanics separately. Audio is deliberately unresolved in the intermediate rather than referring source IDs into unrelated DE sounds.

Additional outstanding work: native terrain restrictions/placement, tech-tree display, icons and localized names, legacy effect attribute semantics, source faction membership and accessibility, full asset dependency conversion, map start/resource IDs, source behaviors unsupported by native tasks, AI, and runtime validation through available automation. No AFK user checks will be requested.

## Class conversion checkpoint

The intermediate now maps source unit classes to native roles, including workers, food/carbon/ore/nova resources, Jedi and holocrons. Where source classes share a native class, class-targeted effects and tasks expand into explicit source unit targets to avoid broadening their membership. The builder rejects ambiguous combined selectors and inconsistent cross-civ effect membership, enforces the signed 16-bit task limit, and remaps default task IDs after expansion.

624 class effect commands and 40,245 class-filtered task instances (including legacy headers and the three civs) expand. The independent verifier checks resulting effect targets and per-civ task order/defaults, in addition to costs, production, prerequisites and exact DAT roundtrip. The raw intermediate is about 304 MB; engine load/performance is unverified. Aircraft and special-unit class choices remain provisional: this conversion does not establish flight, power or shielding. Installed playable packages are unchanged by this checkpoint.

## Economy and artwork checkpoint

Age technology resource IDs now map from source 59/60/61/63 to native 58/25/23/24; source Nova mining productivity 214 maps to native gold mining productivity 47. Verified common economic/conversion resources retain their native equivalents. Unimplemented source mechanics are stored at resource IDs 2000+source to prevent them activating unrelated DE bonuses. This preserves their data, not their behavior. Resources in costs, effects, storages and tasks are translated consistently; initial resource values and task resource selectors are checked independently.

The source roster analysis follows technology prerequisites, enabled construction/training, unit upgrades, building-triggered technologies, corpses, projectiles, annexes, task-swap worker variants, and composite graphics. It is a conservative asset inventory, not a simulation of mutually exclusive research paths. Source engine civ-unit mapping identifies Imperial/Rebel starting scouts as 550/556. Current inventory: 169/222 production and upgrade records, 304/352 dependent units, 1086/1064 graphic references respectively. Counts include intermediate stages, not distinct combat lines.

The converter now supports non-mirrored eight-direction files, mirrored sixteen-direction missiles, and five-part wall layouts. Readback checks compare rendered pixels relative to anchors, allowing empty-layer bounds to normalize without accepting displaced artwork. Standard conversion has passed for 1012 files cumulatively (two belong to the older generic-scout inventory); enhanced conversion is in progress. Seven source files have unsupported player-color values, five have inconsistent frame metadata, and four source fishing-boat sprite references are missing from the archives. Empty/composite source sprite IDs 0..5 now remain sprite-less in the target. None of this full-faction work is installed yet.

Source engine behavior reference: rva2895/efpatch (https://github.com/rva2895/efpatch), particularly civunit.cpp, langdll.cpp and shield.cpp. These confirm that faction-dependent unit selection, worker names, and shield eligibility include executable logic outside the DAT. Porting the DAT alone cannot reproduce them.

## World, localization and audio checkpoint

The draft now translates 42 source terrain-restriction rows into 131 native columns and copies source object spawning for 24 mapped terrain roles. Unmapped native terrains have generic land/water restrictions and no object spawning. Placement fields and 5,502 restriction cells pass independent source comparisons. Native textures remain in use.

Source language DLLs are read as resources without executing their code. The generated English string file contains unit and technology names, descriptions and help. Faction-specific worker names use the source executable's dynamic indexing. Reachable production entries have source names and help; unused/scenario entries may use reported fallbacks. Three-entry civilization metadata is staged, but icons and technology-tree panels remain unfinished.

Source sound groups are appended behind native sounds, with source probabilities, delays, voices, work sounds and graphic-frame cues translated to their new indices. The current source audio inventory contains 1,386 PCM files. Each generated Wwise PCM container has been independently decoded by vgmstream r2117 and compared against the original sample bytes. This verifies media conversion, not DE playback. Missing source audio is enumerated in faction-audio-report.json; broader map branches include additional unresolved references.

Twenty separate full-faction map drafts now inline the original shared resource scripts and retain their object distributions and conditional branches. The confirmed native-economy map pack is unchanged. Original match_player_civ scout selection still requires adaptation. Map asset roots include 51 Gaia records and 111 dependent units, conservatively including alternate environments. Resource variants with 6, 10, 12 and 24 stored frames now preserve their original variant ordering instead of treating them as directions.

Rebuild and validation scripts live in toolkit; current reports remain local JSON artifacts. None of this checkpoint establishes flight, power, shielding, AI compatibility, technology-tree rendering or complete source gameplay. The full-source dataset remains uninstalled while these issues are unresolved. Release 0.0.1 and its tag/archive remain unchanged.

## Scout, icon and tree checkpoint

The original map scout selector is now replaced by a dataset adapter: Rebel unit 550 aliases the fully translated Rebel scout 556, including graphics, sounds, tasks and icon. Its own ID fields remain 550. Normal Rebel training stays on 556 through source availability technology. The builder verifies equal direct upgrades and class membership before allowing this substitution; independent parity and audio checks account for it. All 20 map drafts have zero unresolved source civilization selectors. Runtime behavior remains unverified.

745 source icon references render from six original interface sheets with exact PNG pixel checks. The data-mod UI uses 642 distinct custom icon IDs, materials and textures. All references resolve against the built DAT. Twenty shared technologies have faction-specific source artwork but a shared DE icon slot; their staged icon uses the Imperial artwork. Original portraits retain their source resolution.

The source legacy technology tree uses at most three active links per node, below DE's ten-link limit. The importer retains source ages, building and research connections, filters unit connections to the combined faction roster, and rejects link/list/zone counts that would truncate in DE. The full raw DAT roundtrips exactly. Empire and Rebel JSON panels contain 181 and 176 nodes respectively, with all predecessor, name/help and icon references validated. Source display nodes omit internal production-stage records. Engine UI rendering remains unverified.

Current artwork staging covers 1,158 required converted sprites at standard and enhanced resolutions. Four source sprite references are missing, seven have unsupported player-color values, and ten have unhandled frame/variant metadata. Each is reported rather than silently substituted. The full-faction draft is still not installed.

Primary support for data-mod icon/material and civilization metadata files: https://support.ageofempires.com/hc/en-us/articles/15607286588948-Return-of-Rome-Mod-Updates . Source-specific interface-sheet selection follows AGE_Frame/Units.cpp and Lists.cpp from the pinned AGE checkout.

## Current checkpoint

See FACTION-STATUS.md for the current consolidated state. The earlier sprite/audio/UI gaps above describe historical checkpoints. Required sprite conversion is now complete with explicit repairs, and power/drop-site/land-AI adapters are staged; runtime and special-mechanic work remains incomplete.
