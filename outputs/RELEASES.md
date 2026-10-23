# Releases

Extracted game assets, dependencies, raw DATs and generated packages are excluded from Git. Built installers are not committed either: GitHub Actions builds them (see below).

## How releases are built and cut

Installer releases are built by GitHub Actions (`.github/workflows/release.yml`) from the repository alone, never by hand on a PC. On a pushed `v*` tag, or a manual run with a tag input, the workflow runs `outputs/toolkit/package_installer.py` on `windows-latest`. It packages `payload/` (SWBG-Logic and the shipped part of SWBG-Data, checked against `recipe.tsv`), the installer sources and docs, downloads the official vgmstream r2117 `vgmstream-win64.zip` (SHA-256 `6c4a8a3813864fefed081bbd337dbc0ad93bf88e0b92f5db98d7ab258b22dc6c`, the same build as the earlier hand-built installers), compiles the launcher with the runner's .NET Framework `csc.exe`, self-tests `-ExtractTo` and verifies the `.sha256` files. It then creates or updates a **draft** GitHub release with `SWGB-DE-Installer-<version>-<commit>.exe`, `.zip` and both `.sha256` files, removing stale assets from earlier runs. It refuses to touch a release that is already published and never publishes one itself.

To cut a release:

1. Commit the change. While GitHub still holds a single commit, amend that commit and force-push `master` (over SSH: `git push --force git@github.com:stephenjayakar/SWBG-DE.git master`).
2. Move the tag and push it: `git tag -f v0.0.2-dev` then `git push -f origin v0.0.2-dev`. Pushing over SSH (`git push --force git@github.com:stephenjayakar/SWBG-DE.git v0.0.2-dev`) avoids the credential popup, and an HTTPS token without the `workflow` scope is rejected whenever `.github/workflows/` changes.
3. Watch the run (`gh run watch`), then download the draft's assets and check them (checksums; `<exe> -ExtractTo <empty folder>`).
4. The maintainer reviews the draft, polishes the notes and publishes it by hand. Until then it stays a draft.

To rebuild locally (same contents, Windows with Python 3.12 + Pillow): `python outputs/toolkit/package_installer.py --label <name> --out <folder>`.

## Build labels and the history squash

Commit hashes in this file, CHANGELOG.md and the other notes (6260af2, 998582f, a328cd1 and so on) are build labels from the local development history. On October 19, 2026 the GitHub repository was reset to a single commit, so none of these hashes exist on GitHub. The full pre-squash history is kept on the development machine only, under the local tag `backup/pre-squash-20261019`. Earlier the same day, the last five commits of that history had been rewritten to drop an AI co-author trailer (trees unchanged), so some builds have two labels: 6260af2 = 104f8cb, acf62f6 = ce25942, 23e3f63 = eaa3a93, 449339b = 057c37e, 6f91302 = 7d2d7c3. Archive names such as `SWGB-DE-0.0.2-dev-6260af2.zip` keep the older label.

Published data mod 549437 (SWBG-Logic, formerly SWGB-DE-Factions-Publish) by version:

| Mod 549437 version | Date | Data build |
| --- | --- | --- |
| 1.7 | October 22, 2026 | 907e0f9 (local label; the game files in `payload/SWBG-Logic`) |
| 1.6 | October 19, 2026 | 6260af2 (pre-squash local history; = 104f8cb) |
| 1.5 | September 25, 2026 | 998582f (pre-squash local history) |
| 1.4 | September 15, 2026 | f8e11f9 (pre-squash local history); builds 05646c4 and b9ca555 were Assets-only and kept 1.4 |
| 1.3 | September 15, 2026 | 6a6b7cf (pre-squash local history) |
| 1.2 | September 15, 2026 | e6cf77a (pre-squash local history) |

The 16 game files in the installer's SWBG-Logic (`payload/SWBG-Logic`) are version 1.7, uploaded on October 22, 2026 (the reserved unit-ID crash fix, see CHANGELOG.md); they differ from 1.6 in the DAT, `unitlines.json`, `civilizations.json` and both CivTechTrees. The tech trees are now `CivTechTrees/BRITONS.json` and `FRANKS.json` (1.6: `SWGB_EMPIRE.json`, `SWGB_REBELS.json`), the fix for the empty technology trees. Its `README.md`, `VERSION` and `info.json` are not part of the upload.

## CI-built installer and renamed mods - October 19, 2026

- The mods are renamed: **SWBG-Logic** (data mod; replaces both SWGB-DE-Factions-Draft and SWGB-DE-Factions-Publish, whose files were already byte-identical) and **SWBG-Data** (media; replaces SWGB-DE-Factions-Assets). The installer always generates SWBG-Data; it enables the subscribed mod 549437 when present and otherwise installs a local SWBG-Logic, so exactly one Logic mod is enabled. It migrates old SWGB-DE-Factions-* folders and `mod-status.json` entries to a backup, and `-Uninstall` handles both old and new names. The subscription is found by mod ID (the `549437_` folder prefix or the WorkshopID in `mod-status.json`), never by title, so it works with both `549437_SWGB-DE-Factions-Publish` and the renamed `549437_SWBG-Logic`. A fake-profile test (temporary USERPROFILE/LOCALAPPDATA on E:, real GOG SWGB + Steam DE as sources, five full installs) passed all 46 checks: migration from an earlier-installer state with a local publishing copy; re-install after subscribing under the old folder name (local SWBG-Logic removed, subscription enabled, one Logic mod); re-install after the folder was renamed to `549437_SWBG-Logic` with a stale `mod-status.json` path (entry moved to the new path, prior state carried over); uninstall (publishing copy and its entry restored, subscription kept but back to disabled, superseded folders not restored); the new uninstaller over an old-version install; and uninstall after DE itself renamed the folder and entry (matched by ID). The live profile and `%LOCALAPPDATA%\SWGB-DE-Installer` were not touched (hashes unchanged).
- The installer payload is committed in `payload/` (57 files, 38.3 MB of shipped files plus two `info.json`), taken from installer build a328cd1: the 18 data-mod files and 37 project-authored SWBG-Data files are byte-identical to that build; the two `info.json` files carry the new titles. vgmstream is downloaded from the official r2117 release by SHA-256, so the bundled decoder files are byte-identical to a328cd1's.
- The hand-built a328cd1 draft release was deleted and replaced by the CI-built draft on tag `v0.0.2-dev`. The GitHub repository now holds a single commit; the build label in the asset names is that commit's short hash.


## Data mod 549437 (now SWBG-Logic) updated to version 1.6 - October 19, 2026

Published build **6260af2** (pre-squash local history; also labelled 104f8cb) to the existing unlisted [mod 549437](https://www.ageofempires.com/mods/details/549437/) through the website, signed in via Steam as **stephen**. The site now shows **version 1.6**, 18.62 MB, update date 10/19/2026. Title, tags (Data Mod, User Interface) and Unlisted visibility are unchanged. The description garbled by the failed September 29 attempt was fully replaced and checked against the intended text, and a Change List entry was added.

- Uploaded `SWGB-DE-0.0.2-dev-6260af2-upload-data.zip` from Dropbox (identical to the `outputs/releases` copy), 19,522,379 bytes, SHA-256 `f71ef4df302d8e19a1bef9f5e9473653bc335b57aee3faa1d63af322281f607c`. The site accepted the 16 files, including the six civ-picker PNGs under `resources/_common/wpfg`. No rebuild was needed: no data changed after 104f8cb.
- Before upload, all 16 files were byte-identical to the installer a328cd1 Draft payload (extracted ZIP and `outputs/releases` payload folder; the ZIP sits unchanged inside the exe) and to the installed `SWGB-DE-Factions-Draft`. Installer ZIP and exe SHA-256 matched their checksum files.
- After upload, DE on this PC was started once and re-downloaded the subscription. All 16 files in `mods/subscribed/549437_SWGB-DE-Factions-Publish` are byte-identical to the installer's Draft. DE was then closed; it did not exit on a close signal and was force-terminated (download was already complete). No match was played.
- Not tested: online play on 1.6 with a second PC.

## Single-file installer exe and public repository - October 19, 2026

Installer build commit **a328cd1**. Same data and converter as eaa3a93 (old 23e3f63); the ZIP differs only in `BUILD.json`, `CHANGELOG.md`, `INSTALL.md` and one message line in `Install-SWGB-DE.ps1`. Pushed to https://github.com/stephenjayakar/SWBG-DE (public). A hand-made draft GitHub release `v0.0.2-dev` (unpublished) carried the exe, the ZIP and both checksums; it was later replaced by the CI-built draft (see above). Not copied to Dropbox.

- Exe: `SWGB-DE-Installer-0.0.2-dev-a328cd1.exe`, 25,488,384 bytes, SHA-256 `c5a83dff5f1659ec676b83a347aa80dd35d1fc859451af5d5bd768baa4705a16`. Unsigned .NET Framework 4 launcher embedding the ZIP below; the build self-test checked that `-ExtractTo` reproduces all 85 ZIP members.
- ZIP: `SWGB-DE-Installer-0.0.2-dev-a328cd1.zip`, 25,393,159 bytes, 85 files, SHA-256 `7f30e94c99a97edaba846e2e6b8ccd5d57779e9692b1c2bcca49e9fab541b12f`. No game media (packager extension check; gitleaks clean).
- Exe test on this PC (GOG SWGB + EF 1.5.5, Steam DE): `-Yes` with DE running stopped with exit code 1 and cleaned its temp folder. With DE closed, `-Yes` replaced the installer-generated install in 87 s: 4,202 files generated, 4,190 byte-identical to the reference, 12 atlases rebuilt, 0 errors. All 4,259 installed files match the previous installer-generated install except the two `info.json` files, which DE had rewritten; the new ones equal the payload. `mod-status.json` SWGB entries are unchanged. `-Uninstall -Yes` restored the original 6260af2 folders (exit 0); a further `-Yes` reinstall backed them up to `%LOCALAPPDATA%\SWGB-DE-Installer\backups\20261019-101229` and produced an install identical to the first exe run. The machine is left with the exe-generated install. DE was not launched (file-level check only).
- Not tested: double-click mode (Install/Uninstall menu and closing pause), SmartScreen behaviour of a downloaded copy, other PCs.
- The superseded 23e3f63 installer ZIP, checksum and folder were removed from `outputs/releases`; the 6260af2 full-share/data pair stays as the current data build.

## Installer without game assets - October 19, 2026

Installer build commit **23e3f63**. It carries the same 0.0.2-dev data as 6260af2, and the 6260af2 full share and data pair remain the current data build. This package is new and sits beside them; nothing was deleted. It was **not** copied to Dropbox or uploaded anywhere.

- Package: `SWGB-DE-Installer-0.0.2-dev-23e3f63.zip`, 25,392,319 bytes, 85 files, SHA-256 `f10c7c8eaf520bb56f0c916f5be11e7b2a96df6c05c973ab227a937e1d414d3d`. The extracted folder sits next to it. The packager rejects SMX/SLP/DRS/WEM/WAV/OGG/MP3/DDS files. The payload is the 18 Draft files, 37 project-authored Assets files (AI, maps, XS, strings, per2, morematerials) and both `info.json` files.
- Fresh-install test from the extracted ZIP: the original mods were moved aside and both `mod-status.json` entries removed. `Install-SWGB-DE.cmd -Yes` finished in 86 s, generating 4,202 files with no errors. Against the moved-aside 6260af2 install, 4,219 Assets files and 18 Draft files are byte-identical. That covers all 2,414 SMX, 1,386 sound WEM, 38 music WEM, 344 icon DDS and every shipped file.
- Remaining differences: 8 resource PNGs are pixel-identical but use different PNG encoder bytes. The 12 atlases are rebuilt from the current DE build; their SWGB icon regions are pixel-identical after decode, and the panels atlas is now BC3 instead of BC7. Both `info.json` files gain the `Version` field. 643 obsolete, unreferenced `widgetui/textures/swgb` DDS files are omitted. Evidence is in `outputs/installer-verification/` (per-file report, atlas summary, screenshots).
- In game (DE 101.103.54800.0 / 185872): DE accepted the installer's `mod-status.json` entry, recomputed its checksum and kept the Assets mod enabled. The lobby offered SWGB Classic AI and the SWGB-DE-Factions-Draft data mod. Galactic Empire vs Rebel Alliance plus Classic AI (Hard) started on SWGB Factions Savannah. SWGB units, Command Center, Nova crystals, flora/fauna, resource and command icons all render. The match was closed after a few game minutes; a full game was not played.
- Re-run replaced the installer's own folders without backups. `-Uninstall` removed the folders and restored the moved-aside originals: all 4,900 files matched `faction-install-report.json` and the prior `mod-status.json` flags came back. The machine was left with the installer-generated install. The original 6260af2 folders are restorable with `Uninstall-SWGB-DE.cmd` from `%LOCALAPPDATA%\SWGB-DE-Installer\backups\20261019-011317`.
- Not tested: Steam copy of SWGB, Microsoft Store DE, a PC without the EF First Run files, the interactive profile prompt and online play.

## Current Classic AI release - September 29, 2026

Build commit **6260af2**. SWGB Classic AI verified in-game on Hard (AI vs AI through Tech Level 4, armies and attacks); includes the DE 185872 civ-gate fix, map resource/terrain fixes and the parity DAT. See CHANGELOG.md. Published to mod 549437 as version 1.6 on October 19, 2026 (see above); until then the mod served 1.5 / `998582f`, which lacks these data changes (DLC-gate civ names, parity DAT, per-faction unit lines).

- Full share: `SWGB-DE-0.0.2-dev-6260af2.zip`, 1,670,184,554 bytes, SHA-256 `7046b03ca581fafa802b6acac7a8a29ef45d81fe10fda0eda559140030866361`.
- Data upload: `SWGB-DE-0.0.2-dev-6260af2-upload-data.zip`, 19,522,379 bytes, SHA-256 `f71ef4df302d8e19a1bef9f5e9473653bc335b57aee3faa1d63af322281f607c`.
- ZIP integrity and all 4,900 payload hashes passed; data archive matches the installed and full-share files. Dropbox holds only this pair (plus the old empty staging directory). Older local archives were removed after verification.

## Previous UI compatibility update - September 25, 2026

Release tag: `v0.0.2-dev-compat.1`. Includes the defenses.2 gameplay data and
current DE UI catalogue additions while retaining existing SWGB icon mappings.
The verified full Data/Assets pair is delivered to `E:\Dropbox\temp\SWBG`.
Read `BUILD.json` in the full ZIP for its exact commit. Offline verification does
not establish that the reported online dataset-loading error is fixed.
The current release retains the existing defense and shield runtime limitations.

Published to existing unlisted mod **549437**, service version **1.5**. The site
confirmed the new description, build `998582f`, and 18.41 MB size. Game subscription
delivery and runtime behavior remain unverified; the game was not launched.

- Full share: `SWGB-DE-0.0.2-dev-998582f.zip`, 1,669,956,344 bytes, SHA-256 `a9ae7b5bc206a05dde1a2d5bd8be7b60b925f6a0069598e583013190a8c926cd`.
- Data upload: `SWGB-DE-0.0.2-dev-998582f-upload-data.zip`, 19,302,319 bytes, SHA-256 `8807dc3929d89a4924993028c58deea5405fab0540bcf1122aa2cd59e16af818`.
- ZIP integrity and all 4,892 payload hashes passed. Dropbox copies match source hashes; only this build pair and supporting files remain there, plus an empty staging directory locked during cleanup. Cloud synchronization is not independently confirmed.
- Automatic approval review blocked direct removal of the leftover staging directory and older local release archives ("blocked by policy"). Those cleanup items remain; no deletion workaround was used.

## Previous retained AI difficulty update - September 16, 2026

Payload commit: **b9ca555a1ad73a6bcaf043d2bacdae20f9e73def**. Installed locally as an **Assets-only update**. The two AI entry-point files changed; every other payload file matches 05646c4. All nine data files still match published mod **549437 version 1.4**, so no new data publication was needed. The game was not launched.

- Full share: `SWGB-DE-0.0.2-dev-b9ca555.zip`, 1,669,507,843 bytes, SHA-256 `3903560354eaf3e02776ef58c788328cafd1b6bb5ec5f46dab6acfc67773ff21`.
- Matching data archive: `SWGB-DE-0.0.2-dev-b9ca555-upload-data.zip`, 19,157,621 bytes, SHA-256 `f0f07d996e9207f748783164ae10565551701113993e4599d1959b37ecc5f0ca`.
- CRC and every payload hash verified; all 4,882 installed files verified. Both AI entry points pass the pinned independent parser and are byte-identical, SHA-256 `266fc8ee957250293530009725f4a774073b36733b334aea4b3d23757e9a17e9`.
- 3,736 offline checks cover six DE selections, 40 population tables, worker/age/attack gates and both factions' source age-building prerequisites. Runtime behavior remains unverified. See AI-DIFFICULTIES.md for the partial-port scope and exact differences.
- Friends need the refreshed Assets companion. The complete share ZIP contains both Assets and local Data mod; the matching upload ZIP contains only the nine game data files.
- Release delivery also targets `E:\Dropbox\temp\SWBG`, with verified copies of both archives, checksums and the data manifest. This confirms local copies, not completion of Dropbox cloud syncing. The release tools now automatically deliver future verified pairs there.
- Superseded 05646c4 archives/checksums/sidecar are removed only after the new build passes verification, using native PowerShell resolved-path containment checks. Git and this log preserve history.
- Additional factions remain paused on `codex/all-factions-paused`.

## Previous global shading repair (archives superseded) - September 16, 2026

Payload commit: **05646c49c445a1931b81f806953e8e376b2b074b**. Installed locally as an **Assets-only update**. All nine data files match the previously published unlisted mod [549437](https://www.ageofempires.com/mods/details/549437/) version **1.4**, so no new data publication was needed. The game was not opened; renderer confirmation remains pending.

- Full share: `SWGB-DE-0.0.2-dev-05646c4.zip`, 1,669,484,128 bytes, SHA-256 `31cb886a875e30caf52ac502ad49185c064499f76025fac08e8a23bce4f410a1`.
- Matching data archive: `SWGB-DE-0.0.2-dev-05646c4-upload-data.zip`, 19,157,621 bytes, SHA-256 `f0f07d996e9207f748783164ae10565551701113993e4599d1959b37ecc5f0ca`.
- CRC and every payload hash verified. All 4,882 installed files verified; 1,552 sprite files changed and all other files are identical to f8e11f9.
- Independent decoder compared 2,414 files / 82,352 frames and 324,833,980 visible pixels, including shadows, player colors, palettes and geometry. All visible damage masks are neutral; converter regression and binary encoding checks pass.
- Friends need the refreshed local Assets folder from this full share ZIP. Published data remains v1.4. See ALL-SPRITE-SHADING.md.
- The f8e11f9 archives/checksums/sidecar were superseded after the new archives passed integrity and payload verification, with native PowerShell resolved-path retention cleanup.
- The extra-faction branch remains paused and was not rebuilt.

## Previous worker/resource UI repair (archives superseded) - September 15, 2026

Payload commit: **f8e11f94bfa7574c5d90300ceeec8aec245d8b6a**. Installed locally and published to existing unlisted mod [549437](https://www.ageofempires.com/mods/details/549437/) as service version **1.4**. The website redirected and displayed version 1.4 and build f8e11f9. The game was not opened; runtime behavior and subscription delivery remain unverified.

- Full share: `SWGB-DE-0.0.2-dev-f8e11f9.zip`, 1,668,948,083 bytes, SHA-256 `328e1d3cb7c1a1483a58646b29ccd4ab68139cbed51895f4438cfd128ec3c727`.
- Nine-file data upload: `SWGB-DE-0.0.2-dev-f8e11f9-upload-data.zip`, 19,157,621 bytes, SHA-256 `f0f07d996e9207f748783164ae10565551701113993e4599d1959b37ecc5f0ca`.
- CRC and every payload hash passed. All 4,882 installed files verified. Eighteen changed/new payload files; compressed DAT and all other files unchanged. See WORKER-RESOURCE-UI.md.
- Both players need the updated Assets companion, containing the AI scripts, Ore masks and HUD icons. The published data adds the AI resource catalogue.
- Removed the five superseded 6a6b7cf archive/checksum/manifest files after new archive integrity/payload verification and a final SHA-256 check, using native PowerShell and resolved containment checks. The economy archive records below are historical.
- The additional-faction branch remains paused at 78879ea on `codex/all-factions-paused`.

## Previous economy repair (archives superseded) - September 15, 2026

Payload commit: **6a6b7cf2c9ee80f2e1c803d517e958fd895c56fd**. Installed locally and published to existing unlisted mod [549437](https://www.ageofempires.com/mods/details/549437/) as service version **1.3**. The site confirmed the redirect, version 1.3 and build description. The game was not launched; runtime and subscription-download verification remain pending.

- Full share: `SWGB-DE-0.0.2-dev-6a6b7cf.zip`, 1,660,191,493 bytes, SHA-256 `5ca37170ee4f357dc1f771be2547c73689575c09c122e329eedbfac52b5ba988`.
- Data upload: `SWGB-DE-0.0.2-dev-6a6b7cf-upload-data.zip`, 19,155,423 bytes, SHA-256 `2e8638cf69c4cb4d023bfe5b5afad62a040804713b16479c64752c312c8ddb03`.
- Verified CRC and every payload hash, all 4,870 installed files, 5,502 terrain cells, exact DAT roundtrip and collateral audit. Changed 31 payload files; see ECONOMY-REPAIR.md.
- Both players need matching data and the updated local Assets companion. The published data does not deliver the Nova sprites or map changes.
- After both new archives passed verification, removed the five e6cf77a archives/checksum/manifest files using native PowerShell and resolved-path containment checks; freed 1,679,347,613 bytes. Prior source and checksums remain in Git/history below.
- The 15-faction expansion remains paused at **78879ea** on **codex/all-factions-paused** and is not installed or published.

## 0.0.1

Tag: v0.0.1. Release package: SWGB-DE-0.0.1.zip, with SWGB-DE-0.0.1.sha256 alongside it. Contains the data, Assets and Maps local-mod folders, PLAY-ME.md, CHANGELOG.md and VERSION. Already installed on this machine. Nothing has been pushed or published remotely.

Future changes go under Unreleased in CHANGELOG.md, then receive a new VERSION and a release built by CI from a tag. The tags listed in CHANGELOG.md (v0.0.1, v0.0.2-dev-*) and the history before the October 19, 2026 squash exist only in the local repository. Retain only the newest verified build archives and their supporting files in outputs/releases; delete older archives after successful verification of the new build.

## Unreleased development build

0.0.2-dev is assembled under SWGB-DE-Factions-Draft with faction-package-manifest.json hashes. The experimental build is now installed locally as separate Factions-Draft and Factions-Assets mods, but is not enabled or engine verified. It has no release tag and does not supersede 0.0.1. See FACTION-STATUS.md.

Previous payload checkpoint (archives superseded): **e6cf77a755d9382b0f668f9318099323017ba1e1**. Published to existing unlisted mod [549437](https://www.ageofempires.com/mods/details/549437/) as service version **1.2** on September 15, 2026 (local date). The website redirected successfully and displayed the new build description, version and 18.27 MB size. In-game download and behavior remain unverified; the game was not launched.

- Full share: `SWGB-DE-0.0.2-dev-e6cf77a.zip`, 1,660,191,048 bytes, SHA-256 `e541061cf1cd127534d3f6e75c625fd4e3e531f878162ac007d08e7776752140`.
- Data upload: `SWGB-DE-0.0.2-dev-e6cf77a-upload-data.zip`, 19,154,606 bytes, SHA-256 `729b0e49a4c5419e075deb7f1ab4b009e61fdb5391dbd78dad3fcd9e7e2a347c`.
- CRC and every payload hash verified. All 4,870 installed files verified; local publishing copy updated with metadata preserved. The subscribed directory is managed by DE and was not modified.
- Friends need the matching Assets folder from the full share ZIP for the building-mask change. The published data ZIP cannot update that local companion.

After both e6cf77a archives passed verification, removed the five superseded b944fbf archive/checksum/manifest files using resolved-path containment checks. Source history remains in Git.

Retention cleanup on 2026-09-15: after verifying both retained b944fbf archives, removed superseded 2e2d3d1, 310ed21 and 69338c1 ZIPs and their checksum sidecars, freeing 2,298,437,956 bytes. Their source history and historical checksums remain in Git and REPAIR-TRACKER.md.
