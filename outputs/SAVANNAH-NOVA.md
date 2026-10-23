# Savannah starting Nova repair

Status: installed map repair over Classic AI `.4` on September 17, after DE closed. Native game generation is unverified. The matching release checkpoint is `v0.0.2-dev-classic-ai.4-map.1`.

The reported Standard-resource replay contains no Nova close to player one's Command Center: the nearest crystal is 78.054 tiles away. The other player's nearest is 33.682 tiles away. Both Command Centers are correctly centered in their protected GRASS2 clearings. This is a resource-placement regression, not the Infinite-resource setting.

`toolkit/faction_savannah_nova.py` reserves the original seven primary crystals per player before any other object group. The group is restricted to protected GRASS2, 12–16 tiles from the player start, with radius 2 and a relaxed group-spacing requirement. Secondary deposits and all other object instructions retain their previous order and values. Only Savannah invokes this transformation.

Validation with `toolkit/check_savannah_nova.py` checks the captured regression, idempotence, namespaced/unprefixed conversion parity, preservation of other instructions, and the replacement block through aoe2-rms-parser 2.0.1. Each recorded clearing has 364 terrain-only eligible group centers. This does not emulate DE's object collisions, random choices, or resource-setting overrides. The independent parser cannot parse all of the original map's conditional syntax; only the new block is parser-verified.

Local fixtures and staged RMS are under `work/age-crash`; reports are `savannah-nova-validation.json` and `savannah-nova-installation.json`. Installation verified all 4892 payload files, changed only the Savannah RMS, then verified the updated payload again. AI, Data and base-game files are unchanged. Installed map SHA-256: `5fb1ea0dab98bcda9fcb25a232b9e0e4106004904aefd8add95a53a51f158f47`.

The full share ZIP contains the map repair in Assets and the existing `.4` Data mod. Its companion data-upload ZIP remains the same game-file payload as `.4`; online players still need the matching published dataset and updated Assets. This release does not contain the uninstalled development targeting controllers or claim to resolve the final-age crash.

Native acceptance: generate several new Savannah starts with Standard resources and varied seeds, sizes and player counts; confirm seven nearby Nova crystals for each player, an unobstructed Command Center, and the retained secondary deposits. Test with the matching data mod because Nova uses its imported object ID. Existing saved maps do not regenerate their resource deposits.
