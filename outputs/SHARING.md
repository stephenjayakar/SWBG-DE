# Sharing the experimental faction mod

The game is two mods: **SWBG-Logic** (the data mod, published as unlisted [mod 549437](https://www.ageofempires.com/mods/details/549437/)) and **SWBG-Data** (graphics, sounds, music, icons, strings, maps and AI, built from the player's own SWGB files). Earlier notes call them SWGB-DE-Factions-Draft / SWGB-DE-Factions-Publish and SWGB-DE-Factions-Assets.

## Preferred: subscription + installer (no game assets)

1. Subscribe to [mod 549437](https://www.ageofempires.com/mods/details/549437/) and start DE once so it downloads (needed for multiplayer; single player works without it).
2. Download the installer from the repository's GitHub Releases (`SWGB-DE-Installer-0.0.2-dev-<build>.exe` or `.zip`). Releases are built by CI from a tag and stay drafts until the maintainer publishes them; see RELEASES.md.
3. Run it. It regenerates SWBG-Data from the player's SWGB + Expanding Fronts 1.5.5 install and enables it together with the subscribed mod 549437, or installs a local SWBG-Logic if there is no subscription. It migrates old SWGB-DE-Factions-* folders to a backup.

The download is small and contains no SWGB/EF or DE artwork, sound or music. The recipient needs AoE2 DE, SWGB Saga (Steam or GOG) and Expanding Fronts 1.5.5 installed and run once. See [INSTALLER.md](INSTALLER.md) (shipped as `INSTALL.md`) for requirements, options, uninstall and the known differences.

In the lobby, set Data Mod to SWBG-Logic (the subscribed mod 549437 online, listed as SWBG-Logic, formerly SWGB-DE-Factions-Publish), pick Empire/Rebels, an **SWGB Factions** map and leave the computer players on **AI**: every AI choice in the lobby runs SWGB Classic AI (verified through all four tech levels and attacks on Hard). Use finite resources and Tech Level 1. Disable SWBG-Data for ordinary DE games: it changes native portrait textures and the default AI while enabled.

## Full share ZIP (development; contains converted game assets; private use only)

`outputs/toolkit/share_factions.py` packs the development install, which still uses the old folder names (`SWGB-DE-Factions-Assets` and the local `SWGB-DE-Factions-Draft` data mod), with installation instructions and checksums. The Git repository does not contain the converted game assets. These ZIPs, the matching game-files-only data-upload ZIP, checksums and manifest are copied to `E:\Dropbox\temp\SWBG` (latest verified pair only). The data-upload ZIP is for the mod publishing form (PUBLISHING.md). Prefer the installer for anyone else: if a recipient copies the old-name folders into `mods\local` and later runs the installer, it moves them to a backup and installs SWBG-Data / SWBG-Logic instead.

The ZIP is a local export, not an online publication. Keep its build/checksum file with it so test reports identify the exact snapshot. Original SWGB/Expanding Fronts AI, air mechanics and several other systems remain unfinished; see FACTION-TESTING.md and TODO.md.

Mod layout reference: [AoE2DE UGC Guide](https://ugc.aoe2.rocks/mods/). [Official mod installation overview](https://support.ageofempires.com/hc/en-us/articles/360050397471-Scenario-Mods-Download-and-Installation-Instructions).
