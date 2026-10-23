# Aircraft movement crash candidate — 2026-09-14

The reported crash occurred on the music/Power Core build, while commanding TIE Fighters. It is not treated as a crash from an older installed build.

The local crash report records world time 335442 ms, exception `0xc0000005`, and a null read at address `0x44`, executable RVA `0xD103F0`. The replay's final action is a player-one MOVE at that same game tick, toward (5.396, 76.354). Its raw selection payload contains instance IDs 5307 and 5306; register R12 contains 5306. Earlier train orders request TIE Fighter unit 773. The generic replay parser reads this build's selected IDs two bytes out of alignment, so the IDs were checked against the raw action bytes.

An older dump shares the fault location, but that alone does not establish a shared cause. The initial scenery hypothesis relied on 5306 also being a graphic ID; this is not evidence that the game was loading that graphic. No speculative scenery additions are included in this repair.

The imported fighters were assigned native DE class 38 (ambient birds). The candidate maps fighters, Geonosian Warriors and Jedi Starfighters to native archers (0), and bombers/air cruisers to siege weapons (13). Source class effects and task selectors are expanded to explicit unit IDs wherever native classes overlap, preserving their original target membership. The change preserves source flight flags, height, terrain permissions, movement settings, weapons, costs, training and research times. It does not implement the remaining SWGB air/ground targeting restrictions.

This is a compatibility repair candidate. Without engine symbols or a runtime reproduction, the class choice is not proven to be the null-pointer cause. Music and Power Core implementations are retained. A matching command/crash timestamp is stronger evidence than a guess about a track transition, but does not prove audio played no role.

## Focused retest

1. Restart DE and start a **fresh** SWGB-DE-Factions-Draft match. Old saves/replays retain old game data and are unsuitable for testing this repair.
2. Play Empire. Train two TIE Fighters, select both, and repeatedly move them across open land, forests and water. Try changing formation, moving one fighter alone, and attacking an enemy.
3. Leave music enabled and play beyond six game minutes. Repeat with Rebel fighters if the Imperial test succeeds.
4. If it crashes, report the approximate action and whether one or several aircraft were selected. The next local dump/replay can be compared to this exact case.

The user handles launching and testing. No runtime success is claimed.

## Offline validation

`check_faction_aircraft.py` covers 1,185 aircraft records, including 20 producible faction aircraft, preserves exported movement/combat fields, and verifies their 120 graphic dependencies against both-resolution conversion hashes. Full source parity checks compare class-effect/task membership after expansion. The binary collateral audit restores only classes and selector tables before comparing against the preserved music-build DAT; power and Force tasks have separate checks.

Further audit item: source SWGB trait bits have different DE meanings (for example detector versus transform and mechanical versus auto-scout). TIE Fighter 773 has trait zero, so these were not changed as part of this focused candidate.
