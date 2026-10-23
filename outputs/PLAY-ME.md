> Historical prototype guide: these Trooper-MVP mods were retired from the local mod folder. Use [FACTION-TESTING.md](FACTION-TESTING.md) for the currently installed faction dataset.

# Play the SWGB DE prototype — v2

Installed locally; conversion and file checks passed. In-game rendering is still unverified. The previous match showed an ordinary Archer; lobby dataset selection has not yet been confirmed. A gear icon indicates a data mod, not an error.

1. Finish your match, then restart DE through Steam.
2. In Mods → Installed/My Mods, enable **SWGB-DE-Assets** and **SWGB-DE-Maps** using their checkboxes. Restart again if requested.
3. Start a NEW Skirmish. Select **SWGB-DE-Trooper-MVP** in the **Data Mod** dropdown. This is the gear-marked mod.
4. Choose Britons versus Franks, Starting Age: Castle Age, Allow Cheats. Select Custom → SWGB Savannah, or a standard DE map to isolate graphics testing.
5. Train an Archer and a Scorpion. Briton archers should look like Imperial Troopers; Frank archers should look like Rebels. Scorpions should show an Imperial mech for either faction. Move and attack to test animations.
6. In English, selected-unit names should read Imperial Trooper, Rebel Trooper, or Imperial Mech. Icons and creation tooltips remain native.

For resources: Enter, type `ninjalui`, Enter adds 100,000 of each resource; repeat as needed. `aegis` toggles instant construction/training/research for everyone, including AI. Choose Starting Age to skip advancement.

## Included

- Empire/Rebel idle, walk, attack, death and corpse graphics for Archer/Crossbowman/Arbalester.
- Trooper blaster bolts and impact animation.
- Imperial mech idle, walk, attack, death and wreck for Scorpion/Heavy Scorpion. Mechs retain native Scorpion projectiles and gameplay.
- 20 adapted map layouts including Savannah, with native DE terrain and replacement starting/resource placement; not exact SWGB ecology or balance.
- 18 imported graphics, 36 standard/enhanced sprite variants, 1,360 frames across variants.

Economy, technology availability, stats, buildings, most units, sounds and most UI remain DE. This is an early prototype, not a full rules port. SWGB-DE-Blaster-MVP is an older staged intermediate; use the installed Trooper-MVP + Assets pairing.

## Troubleshooting

- Normal Archer appearance/name: check the Skirmish Data Mod selection. Artwork alone does not replace Archer data references.
- Trooper name but missing graphics: check SWGB-DE-Assets is enabled and restart; report whether enhanced graphics is enabled.
- Changed graphics but native/missing names: English strings may not have loaded, or the game uses another language.
- Existing matches retain loaded data. Start a new match after restarting.
- Return to standard play by choosing the default dataset and disabling companions. Original game files are unchanged.

Installed under C:\Users\aj12a\Games\Age of Empires 2 DE\76561198022514833\mods\local.
Current evidence: build-report.json. Automated game capture fails on this machine; successful visual testing still needs user confirmation.

Latest fix: the initial map converter used numeric entity arguments, which RMS requires as named constants. All 20 maps now declare/use constants. The previous empty Savannah report is a failed engine test of the old scripts; the corrected scripts require a fresh test. Current validator includes a regression check for this parser requirement.

## Full-direction correction

User confirmed dataset/artwork loaded, but units were oversized, disappeared in some directions, faced incorrectly and did not attack. The converter now expands SWGB's five stored S/SW/W/NW/N groups into eight explicit DE E/SE/S/SW/W/NW/N/NE groups, with horizontal flips for east-facing groups. All image/shadow/outline layers and anchors follow the flip. Standard graphics now use 1x source pixels; enhanced graphics use 2x, halving the previous on-screen dimensions. DAT graphic offsets were reduced correspondingly. Attack animations now have all eight frame groups. Damage/firing behavior needs a new-match test; this is not yet proof the reported inability to attack is completely fixed. Restart DE and start a new match using the same working dataset selection.
