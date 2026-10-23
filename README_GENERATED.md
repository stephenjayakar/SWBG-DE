# SWGB in Age of Empires II: DE

A port of **Star Wars Galactic Battlegrounds** to **Age of Empires II: Definitive Edition**. It currently has two factions, the Galactic Empire and the Rebel Alliance, using the Expanding Fronts 1.5.5 data. Each faction has its own units, buildings, tech tree, sounds, music, icons and SWGB-style random maps, plus a port of the original SWGB AI ("SWGB Classic AI").

It is two DE mods:

- **SWBG-Logic**: the data mod (DAT, tech trees, UI tables, civ picker images). It is published on ageofempires.com as [mod 549437](https://www.ageofempires.com/mods/details/549437/) (unlisted); the installer also carries a local copy for single player.
- **SWBG-Data**: the media mod (sprites, sounds, music, icons, AI scripts, maps, strings). The installer builds it from your own copies of the games.

In short: **subscribe to SWBG-Logic (mod 549437), then run the installer for SWBG-Data.**

This repository and the installer contain **no Star Wars or DE art, sound or music**.

## Requirements

- **Age of Empires II: Definitive Edition**. Steam is tested; the Microsoft Store version is detected but untested.
- **Star Wars Galactic Battlegrounds Saga** (Steam or GOG).
- **Expanding Fronts 1.5.5**, the free fan expansion ("Full" download). Merge its `GAME` folder into your SWGB `Game` folder as its Manual Installation Guide describes, then start `battlegrounds_x2.exe` **once** so its First Run step converts the original art.
- Windows 10 or 11 and about 4 GB of free disk space. No Python, Java or other tools are needed.

## Install

1. Open the [SWBG-Logic mod page (549437)](https://www.ageofempires.com/mods/details/549437/), sign in with the account you play DE on and subscribe. Start DE once so it downloads the mod, then quit. (Single player also works without this step.)
2. Close Age of Empires II: DE.
3. Download `SWGB-DE-Installer-<version>-<build>.exe` from [Releases](../../releases) and run it.
4. Windows SmartScreen will warn because the exe is not code-signed: click **More info > Run anyway**.
5. Press **I** to install (or **U** to uninstall). The installer finds DE, your DE profile and SWGB, converts about 4,200 files from your SWGB/EF install (1-2 minutes) and installs **SWBG-Data** into `%USERPROFILE%\Games\Age of Empires 2 DE\<profile>\mods\local\`. If you are subscribed to mod 549437 and its files match this release, it enables that copy of SWBG-Logic; otherwise (not subscribed, or an older version) it installs a local **SWBG-Logic** (single player only) and switches the subscription off. Either way exactly one Logic mod and SWBG-Data end up enabled.
6. Upgrading from an older installer or share ZIP: the old `SWGB-DE-Factions-Assets`, `-Draft` and `-Publish` folders in `mods\local` are moved to a backup and their `mod-status.json` entries removed. Uninstall puts back what was there before.

SWBG-Logic is a data mod: DE marks every data mod as disabled in **Mods > My Mods** each time it starts, but still offers it in the lobby, so it is chosen there (see [Play](#play)). Only **SWBG-Data** has to be enabled in My Mods. If it is off (after a crash or an update), enable it, or close DE, run the exe again and press **R** (Repair). Repair only re-enables SWBG-Data and tidies up stale mod entries.

Command-line options (`-SwgbPath`, `-DePath`, `-ProfileId`, `-NoEnable`, `-Yes`, `-Repair`, `-Uninstall`) are passed through; run the exe with `-?` for the list. Details, logs and the uninstall/backup behaviour are described in [outputs/INSTALLER.md](outputs/INSTALLER.md).

## Play

1. Start DE. In **Mods > My Mods**, make sure **SWBG-Data** is enabled. (SWBG-Logic shows as disabled there; that is normal for a data mod.)
2. **Single Player > Skirmish**: choose **SWBG-Logic** as the **Data Mod**. It resets to Default each time, so choose it every time. If two SWBG-Logic entries appear, choose the local one (version 1.7), which the installer set up; the other is a mod 549437 subscription that is an older version. With an up-to-date subscription there is only one entry.
3. Choose **Galactic Empire** or **Rebel Alliance** and a **SWGB Factions** map (e.g. SWGB Factions Savannah). For computer players, leave **AI** (the default). SWBG has one AI, the SWGB Classic AI, and every AI choice in the list runs it at every difficulty: DE always lists its built-in **AI**, **AI (CD version)** and **AI (HD version)**, and SWBG-Data makes all three load the Classic AI. Tech Level 1 and finite resources are recommended.
4. Disable SWBG-Data for ordinary DE games; while enabled it replaces some DE icons and all of DE's built-in AIs.

## Multiplayer

**Online play with this release has not been tested; treat it as experimental.** It should work if every player subscribes to SWBG-Logic 1.7 and installs SWBG-Data with the same installer release, but that has not been verified (see [Multiplayer status](#multiplayer-status)).

A DE multiplayer lobby only offers *published* data mods in its **Data Mod** dropdown, so online games use the published **SWBG-Logic**, [mod 549437](https://www.ageofempires.com/mods/details/549437/) on ageofempires.com. It is unlisted: the in-game mod browser does not find it, so open it with the link. Its listing title is SWBG-Logic (formerly SWGB-DE-Factions-Publish). A local SWBG-Logic copy is never offered online.

SWBG-Logic contains only the game rules (the DAT, JSON tables and civ picker images). The graphics, sounds, music, icons, maps and AI scripts are in **SWBG-Data**, which cannot be published because the installer builds it from each player's own SWGB files. Every player needs both, and they must match:

- **SWBG-Data**, enabled, from the **same installer release** as the other players.
- The subscription to mod 549437 at the version that matches that installer. For the current installer (0.0.2-dev) that is **version 1.7**, the reserved unit-ID crash fix, whose files are byte-identical to the installer's SWBG-Logic. Version 1.7 was uploaded to mod 549437 on October 22, 2026; the listing is still unlisted. Versions 1.6 and older use the old unit IDs and do not match this installer's SWBG-Data (see [Troubleshooting](#multiplayer-troubleshooting)). The installer only enables a subscription whose files match. Otherwise it installs the local SWBG-Logic, which works in single player only.

Subscribing does not update anyone's SWBG-Data, and re-running the installer does not update the subscription. A mismatched pair was never tested. At the least, graphics, icons and the AI scripts will not match the rules.

### Every player

1. Subscribe to [mod 549437](https://www.ageofempires.com/mods/details/549437/) with the account you play DE on and check that the listing shows version 1.7.
2. Quit and restart DE. The mod downloads to `mods\subscribed\549437_<title>` in your DE profile. A download that finishes while DE is running does not show up in the lobby until you restart.
3. Close DE and run the installer (see [Install](#install)). Everyone should use the same installer release. Because you are subscribed, it enables mod 549437 and SWBG-Data and does not install a local SWBG-Logic. If you installed before subscribing, run the installer again: it removes its local SWBG-Logic so that only one Logic mod is enabled.

### Host

1. **Multiplayer > Host Game**. Use a private or password-protected lobby if you want.
2. **Data Mod**: SWBG-Logic, the subscribed mod 549437.
3. Map: **Custom >** a **SWGB Factions** map (e.g. SWGB Factions Savannah). Civilizations: **Galactic Empire** or **Rebel Alliance**.
4. Use the single-player settings: Standard (finite) resources and Tech Level 1. Avoid starting in Tech Level 4 (see below).
5. Computer players: leave **AI**, as in single player (every AI choice runs the SWGB Classic AI). AI in online games has not been tested.

### Joining

Subscribe and run the installer as above, then join the host's lobby. DE's announcement says unlisted data mods can download through the lobby, but this was not tried here. Subscribe beforehand.

### Multiplayer status

- **Tested (September 16, 2026):** two players played online with the published data at the time (version 1.4) and no AI, on SWGB Factions Savannah. A match that started in Castle Age (Tech Level 3) ran about 31 game minutes, until a player resigned. No out-of-sync problem was reported. However, the game crashed when the Galactic Empire advanced to **Tech Level 4**, and also when a match was started directly in Tech Level 4. The cause was never found ([outputs/FINAL-AGE-INVESTIGATION.md](outputs/FINAL-AGE-INVESTIGATION.md)). In a later single-player test with build 6260af2, both AIs (Empire included) reached Tech Level 4 without crashing. That suggests the crash may be gone, but it has not been rechecked online.
- **Broken by a DE update (September 25, 2026):** after DE build 185872, an online lobby using the published data failed to load. Since that build, DE rejects civilizations whose internal `data_name` it does not recognise. Build 6260af2 fixes this: the Empire and Rebels use the Britons and Franks internal names, while the picker still shows the SWGB names, icons and bonus text. Versions 1.5 and older do not have the fix.
- **Not tested:** any online play with this release (SWBG-Logic 1.7 and installer-built SWBG-Data) or with version 1.6 (build 6260af2), more than two players, AI players online, full-length games, and saving or restoring multiplayer games.

### Multiplayer troubleshooting

- **SWGB is missing from the Data Mod dropdown when hosting.** A local SWBG-Logic is never offered online; pick the subscribed mod 549437. If that is missing too, check that a `mods\subscribed\549437_*` folder exists, then restart DE.
- **"A selected civilization is available in the Lords of the West DLC".** This is not a DLC-ownership problem; it appeared on a PC that owns Lords of the West. It means the selected data is older than build 6260af2 on DE build 185872 or later. Update the subscription (version 1.7 for this installer) and restart DE. Every player needs the same version.
- **"Problem Loading Data Mod".** This was seen when a mod's files changed while DE was running. Restart DE.
- **AoE icons or graphics, missing Nova/Ore, or an AI that idles.** One player's SWBG-Data does not match the published data. Everyone should re-run the same installer release, keep SWBG-Data enabled and restart DE.
- **Crash on reaching or starting in Tech Level 4.** Known from the September tests (see above). Report it with the build numbers if it still happens on version 1.7 or later.
- **Intermittent crash during a match (`AoE2DE_s.exe+0x1356be0`, log line `Object Tracker Error: Added object with reserved group id`).** SWGB units with IDs 900-999, which DE reserves for unit-class groups. Fixed in SWBG-Logic 1.7, which needs the SWBG-Data from the same installer release.

Publishing updates (owner only) are described in [outputs/PUBLISHING.md](outputs/PUBLISHING.md).

## Status and known issues

Experimental (0.0.2-dev).

- Only the Galactic Empire and Rebel Alliance are ported; the other SWGB factions are not.
- SWGB Classic AI was played in game on October 21-22, 2026 (SWGB Factions Savannah, small map). Hard, Hardest and Extreme reach Tech Level 2 at about 10:00 and Tech Level 3 at 15-20 minutes; Hard reaches Tech Level 4 at about 31 minutes. Since its Troop Center is placed at a Power Core (full-speed troopers), Moderate reaches Tech Level 2 at 12:40-17:48 and Tech Level 3 at about 29-34 minutes. See CHANGELOG.md for the Easiest/Standard results.
- One AI: every AI choice in the lobby ("AI", "AI (CD version)", "AI (HD version)") runs SWGB Classic AI. The partial SWGB Land AI and the separate "SWGB Classic AI" entry were removed; the installer (also `-Repair`) deletes their files from an existing SWBG-Data. Before, "AI (CD version)" and "AI (HD version)" ran DE's own AIs; the CD one stopped with an AI script error on load, and then no computer player after it in the list did anything.
- The Classic AI's "too many unpowered buildings" rule now counts power the way DE applies it, so it no longer adds a Power Core every minute (one core per AI in 26-35 minute matches on October 22).
- Fixed in this release (also broken in SWBG-Logic 1.6): the technology trees are no longer empty; the worker build menu offers the Troop Center, Shipyard, Mech Factory and Temple; troops can board and leave Assault Mechs, Transport Mechs, Air Transports and Transport Ships.
- Known gaps:
  - The Command Center's build-menu layout switch works only once each way. DE cannot research a technology twice, so after switching to the defense layout and back the buttons are gone (you keep the military layout).
  - The technology tree panel is wider than DE allows; the last defense nodes (turret and wall upgrades, Mine, Anti-Air Battery) are cut off.
  - If you played an earlier version, DE's saved hotkey profile for SWBG-Logic may still put the Sentry Post on Q (same as the Troop Center). Reset the hotkeys or rebind it; the new default is S.
- Online play needs SWBG-Logic 1.7 from mod 549437 (uploaded October 22, 2026) and SWBG-Data from the same installer release on every PC. It has not been tested with this release; see [Multiplayer](#multiplayer).
- Some SWGB systems are approximated or missing (air units, some defenses and shields). See [outputs/TODO.md](outputs/TODO.md) and [outputs/FACTION-TESTING.md](outputs/FACTION-TESTING.md).
- The installer is tested with the GOG copy of SWGB and Steam DE. The Steam copy of SWGB and the Microsoft Store DE are untested.

## Repository layout

- `outputs/installer/`: the installer (PowerShell + a C# converter compiled on the fly) and `exe/`, the single-file launcher.
- `payload/`: the files the installer ships, byte-exact: `SWBG-Logic/` (the data mod; the same game files as published mod 549437) and the project-authored part of `SWBG-Data/` (AI scripts, maps, XS, strings). `outputs/installer/installer/recipe.tsv` pins each one by SHA-256.
- `.github/workflows/release.yml`: builds the installer release.
- `outputs/toolkit/`: the conversion, data-patching, AI-porting and packaging scripts used to build the mods.
- `outputs/*.md`: design notes, audits and release records. `CHANGELOG.md` has the history. Older notes use the mods' former names: SWGB-DE-Factions-Draft and SWGB-DE-Factions-Publish (now SWBG-Logic), SWGB-DE-Factions-Assets (now SWBG-Data). The development scripts in `outputs/toolkit/` still use those folder names for the development install.
- Commit hashes in the docs (such as 6260af2, 104f8cb or a328cd1) are build labels from the project's local history before it was squashed into a single commit for GitHub. They do not exist on GitHub.

## Building a release

Releases are built by GitHub Actions ([.github/workflows/release.yml](.github/workflows/release.yml)), not on a developer PC. Pushing a `v*` tag, or running the workflow by hand, builds the installer ZIP and exe from this repository on `windows-latest` and attaches them, with their `.sha256` files, to a **draft** GitHub release. The workflow never publishes; the maintainer reviews the draft and publishes it by hand.

To cut one (the tag is moved while the release is still a draft):

```
git tag -f v0.0.2-dev
git push -f origin v0.0.2-dev
```

The build uses only the repository (`payload/`, `outputs/installer/`, the docs) plus the official vgmstream r2117 Windows release, which is downloaded and checked against a pinned SHA-256. The launcher is compiled with the .NET Framework `csc.exe` that ships with Windows. Asset names carry the version and the commit: `SWGB-DE-Installer-<version>-<commit>.exe` and `.zip`.

The same build runs locally on Windows with Python 3.12 and Pillow: `python outputs/toolkit/package_installer.py [--label <name>] [--out <folder>]`. See [outputs/INSTALLER.md](outputs/INSTALLER.md) and [outputs/RELEASES.md](outputs/RELEASES.md).

## Credits

- Star Wars Galactic Battlegrounds by LucasArts and Ensemble Studios. Age of Empires II: Definitive Edition by Forgotten Empires, World's Edge and Microsoft. Star Wars is a trademark of Lucasfilm. This is an unofficial fan project; you need to own the games.
- The **Expanding Fronts** team, whose expansion provides the Empire/Rebel data, artwork, sounds and music this port uses.
- [SMX Workshop](https://github.com/ImWG/SMX-Workshop) by ImWG (SMX sprite format; the converter ports the parts it needs) and [genieutils](https://github.com/Tapsa/genieutils) by Tapsa (DAT editing).
- [vgmstream](https://github.com/vgmstream/vgmstream), bundled with the installer to decode the SWGB/EF music (see its `COPYING`).

Built with help from an LLM coding assistant.
