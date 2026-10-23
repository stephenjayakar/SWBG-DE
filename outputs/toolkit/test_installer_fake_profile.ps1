# Fake-profile test of Install-SWGB-DE.ps1: migration, subscription detection, mod-status.json
# handling (including DE's re-sync of mod 549437), -Repair and -Uninstall, and the one-AI rule
# (Install and -Repair delete the AI files of earlier releases from SWBG-Data).
#
# Everything happens under -Root (a fake USERPROFILE + LOCALAPPDATA that must not exist yet); the
# real DE profile and the real %LOCALAPPDATA%\SWGB-DE-Installer are never touched. Full installs
# convert the real SWGB/EF files (1-3 minutes each), so the whole run takes 15-25 minutes.
#
#   python outputs/toolkit/package_installer.py --label test --out <dir> [--no-exe]
#   powershell -NoProfile -ExecutionPolicy Bypass -File outputs/toolkit/test_installer_fake_profile.ps1 `
#       -Root E:\tmp\swbg-fake -InstallerDir <dir>\SWGB-DE-Installer-0.0.2-dev-test
param(
    [Parameter(Mandatory)] [string]$Root,
    [Parameter(Mandatory)] [string]$InstallerDir,
    [string]$SwgbPath = 'E:\GOG Games\Star Wars - Galactic Battlegrounds',
    [string]$DePath = 'E:\SteamLibrary\steamapps\common\AoE2DE'
)
$ErrorActionPreference = 'Stop'
$Pid_ = '76561190000000001'
$Home_ = Join-Path $Root 'home'
$Lad = Join-Path $Root 'localappdata'
$Prof = Join-Path $Home_ "Games\Age of Empires 2 DE\$Pid_"
$Local = Join-Path $Prof 'mods\local'
$Sub = Join-Path $Prof 'mods\subscribed'
$StatusPath = Join-Path $Prof 'mods\mod-status.json'
$StateDir = Join-Path $Lad 'SWGB-DE-Installer'
$OldPath = 'subscribed//549437_SWGB-DE-Factions-Publish'
$NewPath = 'subscribed//549437_SWBG-Logic'
$oldSub = Join-Path $Sub '549437_SWGB-DE-Factions-Publish'
$newSub = Join-Path $Sub '549437_SWBG-Logic'
$script:fails = 0
$script:checks = 0
$script:out = ''

function Check([string]$What, [bool]$Ok) {
    $script:checks++
    if ($Ok) { Write-Host "  PASS $What" -ForegroundColor Green } else { Write-Host "  FAIL $What" -ForegroundColor Red; $script:fails++ }
}
function Section([string]$Title) { Write-Host "`n=== $Title ===" -ForegroundColor Cyan }
function Mods { if (Test-Path -LiteralPath $StatusPath) { @((Get-Content -LiteralPath $StatusPath -Raw | ConvertFrom-Json).Mods) } else { @() } }
function Entry([string]$Path) { Mods | Where-Object { $_.Path -eq $Path } | Select-Object -First 1 }
function Entries549437 { @(Mods | Where-Object { "$($_.WorkshopID)" -eq '549437' -or $_.Path -like 'subscribed//549437_*' }) }
function LocalDirs { @(Get-ChildItem -LiteralPath $Local -Directory | ForEach-Object Name | Sort-Object) }
function Write-Status($All) { [IO.File]::WriteAllText($StatusPath, '{"Mods":[' + ((@($All) | ForEach-Object { $_ | ConvertTo-Json -Compress }) -join ',') + '],"Unsub":[]}') }
function LogicEnabled { @(Mods | Where-Object { $_.Enabled -and ($_.Path -eq 'local//SWBG-Logic' -or $_.Path -like 'subscribed//549437_*' -or "$($_.WorkshopID)" -eq '549437' -or $_.Path -like 'local//SWGB-DE-Factions-*') }).Count }
function State { Get-Content -LiteralPath (Join-Path $StateDir 'state.json') -Raw | ConvertFrom-Json }
function SubEntry([string]$Path, [bool]$Enabled, [int]$Priority, [string]$CheckSum = '2462092691', [string]$LastUpdate = '1792424046017') {
    $title = $Path.Substring('subscribed//549437_'.Length)
    [pscustomobject][ordered]@{ CheckSum = $CheckSum; Enabled = $Enabled; LastUpdate = $LastUpdate; Path = $Path; Priority = $Priority; PublishID = 0; Title = $title; WorkshopID = 549437 }
}
function Run-Installer([string[]]$Extra, [string]$ProfileId = $Pid_) {
    $ErrorActionPreference = 'Continue'
    $env:USERPROFILE = $Home_; $env:LOCALAPPDATA = $Lad
    Remove-Item Env:\SWGB_DE_LAUNCHER -ErrorAction SilentlyContinue
    $lines = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallerDir 'installer\Install-SWGB-DE.ps1') -SwgbPath $SwgbPath -DePath $DePath -ProfileId $ProfileId -Yes @Extra 2>&1
    $rc = $LASTEXITCODE
    $script:out = ($lines | ForEach-Object { "$_" }) -join "`n"
    $lines | ForEach-Object { Write-Host "    | $_" -ForegroundColor DarkGray }
    return $rc
}
# SWBG ships one AI: no .ai file in SWBG-Data (each would add a lobby entry), and DE's three built-in
# entries (AI, AI (CD version), AI (HD version)) reach SWGB Classic AI through these three files
# (ai_entries.py); the other files DE's PromiDE/randomgame load are 31 comment-only stubs in the ai folder.
$DataAi = Join-Path $Local 'SWBG-Data\resources\_common\ai'
$Retired = @('SWGB Land AI.ai', 'SWGB Land AI.per', 'SWGB Classic AI.ai')
$AiEntries = @('resources\_common\drs\gamedata_x2\PromiDE.per2', 'resources\_common\ai\AI (HD version).per', 'resources\_common\ai\Promisory\defaultConstants.per')
function Plant-RetiredAi { foreach ($n in $Retired) { [IO.File]::WriteAllText((Join-Path $DataAi $n), "left over from an earlier release") } }
function RetiredAiLeft { @($Retired | Where-Object { Test-Path -LiteralPath (Join-Path $DataAi $_) }).Count }
function OneAi {
    # (-Include is unreliable with -LiteralPath in Windows PowerShell 5.1, so filter on the extension.)
    $ai = @(Get-ChildItem -LiteralPath (Join-Path $Local 'SWBG-Data') -Recurse -File | Where-Object { $_.Extension -in '.ai', '.ai2' }).Count
    $land = @(Get-ChildItem -LiteralPath (Join-Path $Local 'SWBG-Data') -Recurse -File -Filter '*Land AI*').Count
    $loads = @($AiEntries | Where-Object {
        $f = Join-Path $Local "SWBG-Data\$_"
        (Test-Path -LiteralPath $f) -and (@(Get-Content -LiteralPath $f | Where-Object { $_ -match '^\s*[^;\s]' }) -join '|') -eq '(load "SWGB Classic AI")'
    }).Count
    $stubs = @(Get-ChildItem -LiteralPath (Join-Path $DataAi 'Promisory') -File).Count + @(Get-ChildItem -LiteralPath $DataAi -File -Filter 'elite*.per').Count
    return ($ai -eq 0 -and $land -eq 0 -and $loads -eq 3 -and $stubs -eq 32 -and (Test-Path -LiteralPath (Join-Path $DataAi 'SWGB Classic AI.per')))
}
function Make-Mod([string]$Dir, [string]$Title, [string]$Author = 'Local SWGB port project') {
    New-Item -ItemType Directory -Force -Path (Join-Path $Dir 'resources\_common\dat') | Out-Null
    [IO.File]::WriteAllText((Join-Path $Dir 'info.json'), (@{ Title = $Title; Author = $Author; Version = 'old' } | ConvertTo-Json))
    [IO.File]::WriteAllText((Join-Path $Dir 'marker.txt'), "old $Title")
}
function Make-Subscribed([string]$Dir, [string]$Version, [switch]$Stale) {
    # A downloaded copy of mod 549437 plus a version marker. By default its game files equal this
    # release's SWBG-Logic (the installer only uses a matching subscription); -Stale changes the DAT,
    # like a subscriber still on an older version (1.6 kept unit IDs in DE's reserved range).
    New-Item -ItemType Directory -Force -Path $Dir | Out-Null
    Copy-Item -Path (Join-Path $InstallerDir 'payload\SWBG-Logic\*') -Destination $Dir -Recurse -Force
    $dat = Join-Path $Dir 'resources\_common\dat\empires2_x2_p1.dat'
    if ($Stale) { $fs = [IO.File]::Open($dat, 'Append'); $fs.WriteByte(0); $fs.Close() }
    (Get-Item -LiteralPath $dat).LastWriteTimeUtc = [datetime]::UtcNow
    [IO.File]::WriteAllText((Join-Path $Dir 'version.txt'), $Version)
}

if (Test-Path -LiteralPath $Root) { throw "Root exists: $Root" }
if (-not (Test-Path -LiteralPath (Join-Path $InstallerDir 'installer\Install-SWGB-DE.ps1'))) { throw "Not an extracted installer: $InstallerDir" }
New-Item -ItemType Directory -Force -Path $Local, $Sub, $StateDir | Out-Null
$realUser = [Environment]::GetFolderPath('UserProfile')
$realLad = [Environment]::GetFolderPath('LocalApplicationData')
if ($Prof -like "$realUser\Games\*" -or $StateDir -like "$realLad\SWGB-DE-Installer*") { throw 'Fake root must not overlap the real DE profile or installer state' }

# --- Initial state: an install by the previous installer version + a local publishing copy ---
foreach ($n in 'SWGB-DE-Factions-Draft', 'SWGB-DE-Factions-Assets', 'SWGB-DE-Factions-Publish') { Make-Mod (Join-Path $Local $n) $n }
Make-Mod (Join-Path $Local 'Unrelated Mod') 'Unrelated Mod' 'Someone'
Write-Status @(
    [ordered]@{ CheckSum = '1'; Enabled = $true; LastUpdate = '0'; Path = 'local//Unrelated Mod'; Priority = 1; PublishID = 0; Title = 'Unrelated Mod'; WorkshopID = 0 },
    [ordered]@{ CheckSum = '2'; Enabled = $true; LastUpdate = '0'; Path = 'local//SWGB-DE-Factions-Assets'; Priority = 2; PublishID = 0; Title = 'SWGB-DE-Factions-Assets'; WorkshopID = 0 },
    [ordered]@{ CheckSum = '3'; Enabled = $false; LastUpdate = '0'; Path = 'local//SWGB-DE-Factions-Draft'; Priority = 3; PublishID = 0; Title = 'SWGB-DE-Factions-Draft'; WorkshopID = 0 },
    [ordered]@{ CheckSum = '4'; Enabled = $false; LastUpdate = '0'; Path = 'local//SWGB-DE-Factions-Publish'; Priority = 4; PublishID = 0; Title = 'SWGB-DE-Factions-Publish'; WorkshopID = 0 }
)
$oldState = [ordered]@{ InstalledAt = '2026-10-19T10:12:29'; Profile = $Prof
    Installed = @((Join-Path $Local 'SWGB-DE-Factions-Draft'), (Join-Path $Local 'SWGB-DE-Factions-Assets'))
    Backups = [ordered]@{}; ModStatusPrior = [ordered]@{ 'SWGB-DE-Factions-Assets' = [ordered]@{ Existed = $true; Enabled = $false } } }
$oldState | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $StateDir 'state.json') -Encoding UTF8

Section '1. Install over the old install, not subscribed (migration)'
$rc = Run-Installer @()
Check 'exit code 0' ($rc -eq 0)
Check 'local folders = SWBG-Data, SWBG-Logic, Unrelated Mod' (((LocalDirs) -join '|') -eq 'SWBG-Data|SWBG-Logic|Unrelated Mod')
Check 'SWBG-Logic info.json title' ((Get-Content -LiteralPath (Join-Path $Local 'SWBG-Logic\info.json') -Raw | ConvertFrom-Json).Title -eq 'SWBG-Logic')
Check 'SWBG-Logic has the DAT' (Test-Path -LiteralPath (Join-Path $Local 'SWBG-Logic\resources\_common\dat\empires2_x2_p1.dat'))
Check 'SWBG-Data has generated sprites' (@(Get-ChildItem -LiteralPath (Join-Path $Local 'SWBG-Data\resources\_common\drs\graphics') -Filter *.smx).Count -eq 2414)
Check 'no legacy mod-status entries' (@(Mods | Where-Object { $_.Path -like 'local//SWGB-DE-Factions-*' }).Count -eq 0)
Check 'SWBG-Data enabled' ((Entry 'local//SWBG-Data').Enabled -eq $true)
Check 'SWBG-Logic enabled' ((Entry 'local//SWBG-Logic').Enabled -eq $true)
Check 'unrelated entry unchanged' ((Entry 'local//Unrelated Mod').Enabled -eq $true -and (Entry 'local//Unrelated Mod').CheckSum -eq '1')
$st = State
Check 'Draft+Assets superseded (backup kept)' ($st.Superseded.'SWGB-DE-Factions-Draft' -and (Test-Path -LiteralPath (Join-Path $st.Superseded.'SWGB-DE-Factions-Assets' 'marker.txt')))
Check 'Publish copy in Backups' ($st.Backups.'SWGB-DE-Factions-Publish' -and (Test-Path -LiteralPath (Join-Path $st.Backups.'SWGB-DE-Factions-Publish' 'marker.txt')))
Check 'Publish entry recorded for restore' ($st.ModStatusRemoved.'local//SWGB-DE-Factions-Publish' -ne $null)
Check 'old-style prior key carried over as local// path' ($st.ModStatusPrior.'local//SWGB-DE-Factions-Assets' -ne $null)
Check 'mod-status.json backed up' (@(Get-ChildItem -LiteralPath (Join-Path $StateDir 'backups') -Recurse -Filter mod-status.json).Count -ge 1)
Check 'final message: make sure SWBG-Data is enabled in My Mods' ($script:out -match 'In Mods > My Mods, make sure SWBG-Data is enabled')
Check 'final message: SWBG-Logic shows as disabled in My Mods, chosen in the lobby' ($script:out -match 'My Mods shows it as disabled after every DE start' -and $script:out -notmatch 'check that BOTH')
Check 'final message: choose SWBG-Logic as the Data Mod, resets to Default' ($script:out -match 'choose SWBG-Logic as the Data Mod. It resets to Default each time')
Check 'final message: two SWBG-Logic entries -> the local version 1.7' ($script:out -match 'If two SWBG-Logic entries appear, choose the local one \(version 1\.7\)')
Check 'final message: every AI choice runs the Classic AI' ($script:out -match 'every AI choice \("AI", "AI \(CD version\)", "AI \(HD version\)"\) runs the SWGB Classic AI' -and $script:out -notmatch 'SWGB Land AI')
Check 'one AI: no .ai file or Land AI in SWBG-Data; AI, AI (CD version), AI (HD version) load SWGB Classic AI' (OneAi)

Section '1r. DE switched both mods off (e.g. after a crash); -Repair'
$dataStamp = (Get-Item -LiteralPath (Join-Path $Local 'SWBG-Data')).LastWriteTimeUtc
Write-Status @(Mods | ForEach-Object { if ($_.Path -like 'local//SWBG-*') { $_.Enabled = $false }; $_ })
Plant-RetiredAi  # an SWBG-Data from an earlier release (SWGB Land AI, separate SWGB Classic AI entry)
$rc = Run-Installer @('-Repair')
Check 'exit code 0' ($rc -eq 0)
Check 'repair deleted SWGB Land AI.ai/.per and SWGB Classic AI.ai' ((RetiredAiLeft) -eq 0 -and $script:out -match 'Removed .*SWGB Land AI\.per')
Check 'repair: one AI left (Classic script and the three DE entries kept)' (OneAi)
Check 'SWBG-Data enabled again' ((Entry 'local//SWBG-Data').Enabled -eq $true)
Check 'local SWBG-Logic enabled again' ((Entry 'local//SWBG-Logic').Enabled -eq $true)
Check 'nothing regenerated (no conversion run)' ($script:out -notmatch 'Converting' -and (Get-Item -LiteralPath (Join-Path $Local 'SWBG-Data')).LastWriteTimeUtc -eq $dataStamp)
Check 'install-time prior kept (SWBG-Logic did not exist before install)' ((State).ModStatusPrior.'local//SWBG-Logic'.Existed -eq $false)

Section '2. Subscribe to 549437 under its old folder name (disabled entry), install again'
Make-Subscribed $oldSub 'v1.6'
Write-Status (@(Mods) + (SubEntry $OldPath $false 9))
Plant-RetiredAi
$rc = Run-Installer @()
Check 'exit code 0' ($rc -eq 0)
Check 'install over an SWBG-Data with retired AI files: none left, one AI' ((RetiredAiLeft) -eq 0 -and (OneAi))
Check 'local folders = SWBG-Data, Unrelated Mod (no local Logic)' (((LocalDirs) -join '|') -eq 'SWBG-Data|Unrelated Mod')
Check 'subscribed 549437 (old name) enabled' ((Entry $OldPath).Enabled -eq $true)
Check 'no local//SWBG-Logic entry' ((Entry 'local//SWBG-Logic') -eq $null)
Check 'SWBG-Data enabled' ((Entry 'local//SWBG-Data').Enabled -eq $true)
Check 'exactly one Logic mod enabled' ((LogicEnabled) -eq 1)
Check 'subscribed folder untouched' (Test-Path -LiteralPath (Join-Path $oldSub 'resources\_common\dat\empires2_x2_p1.dat'))
Check 'warns that DE will re-download the renamed listing' ($script:out -match "still named 'SWGB-DE-Factions-Publish'")
Check 'final message: choose the subscribed SWBG-Logic in the lobby' ($script:out -match 'Choose the subscribed SWBG-Logic \(mod 549437\)' -and $script:out -notmatch 'If two SWBG-Logic entries appear')

Section '2b. Listing renamed: folder is now 549437_SWBG-Logic, mod-status still has the old path; install again'
Move-Item -LiteralPath $oldSub -Destination $newSub
$rc = Run-Installer @()
Check 'exit code 0' ($rc -eq 0)
Check 'entry moved to subscribed//549437_SWBG-Logic and enabled' ((Entry $NewPath).Enabled -eq $true -and (Entry $NewPath).WorkshopID -eq 549437)
Check 'no stale old-path entry' ((Entry $OldPath) -eq $null)
Check 'exactly one Logic mod enabled' ((LogicEnabled) -eq 1)
$st = State
Check 'original prior (disabled) carried to the new path' ($st.ModStatusPrior.$NewPath.Existed -eq $true -and $st.ModStatusPrior.$NewPath.Enabled -eq $false)
Check 'state Logic = new path' ($st.Logic -eq $NewPath)
Check 'no re-download warning once the folder has the current title' ($script:out -notmatch 'still named')

Section '3. Uninstall'
$rc = Run-Installer @('-Uninstall')
Check 'exit code 0' ($rc -eq 0)
Check 'local folders = SWGB-DE-Factions-Publish (restored), Unrelated Mod' (((LocalDirs) -join '|') -eq 'SWGB-DE-Factions-Publish|Unrelated Mod')
Check 'restored Publish copy content' ((Get-Content -LiteralPath (Join-Path $Local 'SWGB-DE-Factions-Publish\marker.txt') -Raw) -eq 'old SWGB-DE-Factions-Publish')
Check 'Publish entry restored (disabled)' ((Entry 'local//SWGB-DE-Factions-Publish') -ne $null -and (Entry 'local//SWGB-DE-Factions-Publish').Enabled -eq $false)
Check 'no SWBG entries' (@(Mods | Where-Object { $_.Path -like 'local//SWBG-*' }).Count -eq 0)
Check 'subscribed entry kept, back to disabled' ((Entry $NewPath) -ne $null -and (Entry $NewPath).Enabled -eq $false)
Check 'subscribed folder untouched' (Test-Path -LiteralPath (Join-Path $newSub 'resources\_common\dat\empires2_x2_p1.dat'))
Check 'superseded Draft/Assets not restored' (-not (Test-Path -LiteralPath (Join-Path $Local 'SWGB-DE-Factions-Draft')))
Check 'unrelated entry unchanged' ((Entry 'local//Unrelated Mod').Enabled -eq $true)
Check 'state.json archived' (-not (Test-Path -LiteralPath (Join-Path $StateDir 'state.json')))

Section '4. New uninstaller over an old-version install (no migration yet)'
foreach ($n in 'SWGB-DE-Factions-Draft', 'SWGB-DE-Factions-Assets') { Make-Mod (Join-Path $Local $n) $n }
$oldState | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $StateDir 'state.json') -Encoding UTF8
$rc = Run-Installer @('-Uninstall')
Check 'exit code 0' ($rc -eq 0)
Check 'old installer folders removed, own Publish copy left' (((LocalDirs) -join '|') -eq 'SWGB-DE-Factions-Publish|Unrelated Mod')

Section '5. Install with the subscription under its old name, then DE renames folder + entry, then uninstall'
Move-Item -LiteralPath $newSub -Destination $oldSub
Write-Status (@(Mods | Where-Object { $_.Path -notlike 'subscribed//549437_*' }) + (SubEntry $OldPath $false 9))
$rc = Run-Installer @()
Check 'exit code 0' ($rc -eq 0)
Check 'Publish copy migrated again, no local Logic' (((LocalDirs) -join '|') -eq 'SWBG-Data|Unrelated Mod')
Check 'subscription (old name) enabled, one Logic' ((Entry $OldPath).Enabled -eq $true -and (LogicEnabled) -eq 1)
# DE renames the folder and rewrites the entry in place; the player ticks it again in My Mods.
Move-Item -LiteralPath $oldSub -Destination $newSub
Write-Status @(Mods | ForEach-Object { if ($_.Path -eq $OldPath) { $_.Path = $NewPath; $_.Title = 'SWBG-Logic' }; $_ })
$rc = Run-Installer @('-Repair')
Check 'repair: exit code 0, entry still enabled' ($rc -eq 0 -and (Entry $NewPath).Enabled -eq $true)
$st = State
Check 'repair: pre-install prior (disabled) moved from the old path, not re-recorded as enabled' ($st.ModStatusPrior.$NewPath.Existed -eq $true -and $st.ModStatusPrior.$NewPath.Enabled -eq $false -and $st.ModStatusPrior.$OldPath -eq $null)
$rc = Run-Installer @('-Uninstall')
Check 'exit code 0' ($rc -eq 0)
Check 'renamed subscription entry restored to disabled (matched by ID)' ((Entry $NewPath) -ne $null -and (Entry $NewPath).Enabled -eq $false)
Check 'Publish copy restored again' (((LocalDirs) -join '|') -eq 'SWGB-DE-Factions-Publish|Unrelated Mod')
Check 'no SWBG entries' (@(Mods | Where-Object { $_.Path -like 'local//SWBG-*' }).Count -eq 0)

Section '6. Folder already at 549437_SWBG-Logic with its own (disabled) entry; install'
# As DE leaves it after re-syncing the renamed listing: one entry, current path, Enabled false.
Write-Status (@(Mods | Where-Object { $_.Path -notlike 'subscribed//549437_*' }) + (SubEntry $NewPath $false 5 '2462092691' '1792519828003'))
$rc = Run-Installer @()
Check 'exit code 0' ($rc -eq 0)
Check 'subscribed//549437_SWBG-Logic enabled' ((Entry $NewPath).Enabled -eq $true)
Check 'one 549437 entry, DE fields kept (CheckSum, LastUpdate, Priority, Title)' (@(Entries549437).Count -eq 1 -and (Entry $NewPath).CheckSum -eq '2462092691' -and (Entry $NewPath).LastUpdate -eq '1792519828003' -and (Entry $NewPath).Priority -eq 5 -and (Entry $NewPath).Title -eq 'SWBG-Logic')
Check 'entry not renamed (already current)' ($script:out -notmatch 'Updating the mod-status.json entry')
Check 'no re-download warning' ($script:out -notmatch 'still named')
Check 'SWBG-Data enabled, exactly one Logic' ((Entry 'local//SWBG-Data').Enabled -eq $true -and (LogicEnabled) -eq 1)
Check 'Publish copy migrated, no local Logic' (((LocalDirs) -join '|') -eq 'SWBG-Data|Unrelated Mod')

Section '7. The 2026-10-20 bug: installed under the old name, DE renamed the folder and added a disabled entry; install again'
# State as the installer left it with the old folder name: old-path entry enabled.
Move-Item -LiteralPath $newSub -Destination $oldSub
Write-Status @(Mods | ForEach-Object { if ($_.Path -eq $NewPath) { $_.Path = $OldPath; $_.Title = 'SWGB-DE-Factions-Publish'; $_.Enabled = $true; $_.Priority = 7 }; $_ })
# DE re-syncs: new folder name, its own new entry (disabled), the old entry left behind.
Move-Item -LiteralPath $oldSub -Destination $newSub
Write-Status (@(Mods) + (SubEntry $NewPath $false 9 '2462092691' '1792519828003'))
Check 'setup: two 549437 entries, the current one disabled' (@(Entries549437).Count -eq 2 -and (Entry $NewPath).Enabled -eq $false -and (Entry $OldPath).Enabled -eq $true)
$rc = Run-Installer @()
Check 'exit code 0' ($rc -eq 0)
Check "DE's entry (current folder) enabled" ((Entry $NewPath).Enabled -eq $true)
Check "DE's entry kept as written (Priority 9, LastUpdate)" ((Entry $NewPath).Priority -eq 9 -and (Entry $NewPath).LastUpdate -eq '1792519828003')
Check 'stale old-path entry removed' ((Entry $OldPath) -eq $null -and @(Entries549437).Count -eq 1)
Check 'exactly one Logic mod enabled, SWBG-Data enabled' ((LogicEnabled) -eq 1 -and (Entry 'local//SWBG-Data').Enabled -eq $true)
Check 'reported the stale entry' ($script:out -match 'Removed the stale mod-status.json entry subscribed//549437_SWGB-DE-Factions-Publish')

Section '7r. Same re-sync, but DE rewrote the entry in place (what DE did on 2026-10-20); -Repair'
Write-Status @(Mods | ForEach-Object { if ($_.Path -eq $NewPath) { $_.Enabled = $false; $_.LastUpdate = '1792519828004' }; $_ })
$rc = Run-Installer @('-Repair')
Check 'exit code 0' ($rc -eq 0)
Check 'subscription enabled again, one entry' ((Entry $NewPath).Enabled -eq $true -and @(Entries549437).Count -eq 1)
Check 'SWBG-Data still enabled, one Logic' ((Entry 'local//SWBG-Data').Enabled -eq $true -and (LogicEnabled) -eq 1)

Section '7d. -Repair with a duplicate disabled entry (stale old path still enabled)'
Write-Status (@(Mods | ForEach-Object { if ($_.Path -eq $NewPath) { $_.Enabled = $false }; $_ }) + (SubEntry $OldPath $true 3))
$rc = Run-Installer @('-Repair')
Check 'exit code 0' ($rc -eq 0)
Check 'current entry enabled, stale entry removed' ((Entry $NewPath).Enabled -eq $true -and (Entry $OldPath) -eq $null -and @(Entries549437).Count -eq 1)
Check 'exactly one Logic mod enabled' ((LogicEnabled) -eq 1)

Section '8. Version re-sync (v1.7): same folder, new files, DE switched the entry off; -Repair'
Make-Subscribed $newSub 'v1.7'
Write-Status @(Mods | ForEach-Object { if ($_.Path -eq $NewPath) { $_.Enabled = $false; $_.CheckSum = '1111111111'; $_.LastUpdate = '1793000000000' }; $_ })
$rc = Run-Installer @('-Repair')
Check 'exit code 0' ($rc -eq 0)
Check 'subscription enabled again' ((Entry $NewPath).Enabled -eq $true)
Check "DE's new CheckSum/LastUpdate kept" ((Entry $NewPath).CheckSum -eq '1111111111' -and (Entry $NewPath).LastUpdate -eq '1793000000000')
Check 'one 549437 entry, one Logic, SWBG-Data enabled' (@(Entries549437).Count -eq 1 -and (LogicEnabled) -eq 1 -and (Entry 'local//SWBG-Data').Enabled -eq $true)
Check 'subscribed v1.7 files untouched' ((Get-Content -LiteralPath (Join-Path $newSub 'version.txt') -Raw) -eq 'v1.7')
Check 'repair explains that SWBG-Logic is chosen in the lobby' ($script:out -match 'My Mods shows it as disabled after every DE start' -and $script:out -match 'Repair complete: SWBG-Data is enabled')

Section '8b. Another version re-sync (v1.8); full install over it'
Make-Subscribed $newSub 'v1.8'
Write-Status @(Mods | ForEach-Object { if ($_.Path -eq $NewPath) { $_.Enabled = $false; $_.CheckSum = '2222222222'; $_.LastUpdate = '1794000000000' }; $_ })
$rc = Run-Installer @()
Check 'exit code 0' ($rc -eq 0)
Check 'subscription enabled, DE fields kept' ((Entry $NewPath).Enabled -eq $true -and (Entry $NewPath).CheckSum -eq '2222222222')
Check 'one 549437 entry, one Logic, SWBG-Data enabled' (@(Entries549437).Count -eq 1 -and (LogicEnabled) -eq 1 -and (Entry 'local//SWBG-Data').Enabled -eq $true)

Section '9. Two downloaded copies of 549437 (old folder left behind); -Repair'
Make-Subscribed $oldSub 'v1.6'
(Get-Item -LiteralPath (Join-Path $oldSub 'resources\_common\dat\empires2_x2_p1.dat')).LastWriteTimeUtc = [datetime]::UtcNow.AddDays(-2)
Write-Status (@(Mods) + (SubEntry $OldPath $true 11))
$rc = Run-Installer @('-Repair')
Check 'exit code 0' ($rc -eq 0)
Check 'newest copy (549437_SWBG-Logic) enabled' ((Entry $NewPath).Enabled -eq $true)
Check 'older copy kept but disabled' ((Entry $OldPath) -ne $null -and (Entry $OldPath).Enabled -eq $false)
Check 'exactly one Logic mod enabled' ((LogicEnabled) -eq 1)
# DE drops the entry of a folder that is gone.
Remove-Item -LiteralPath $oldSub -Recurse -Force
Write-Status @(Mods | Where-Object { $_.Path -ne $OldPath })

Section '10. Uninstall after the re-syncs'
$rc = Run-Installer @('-Uninstall')
Check 'exit code 0' ($rc -eq 0)
Check 'subscription kept, back to disabled (its state before install)' ((Entry $NewPath) -ne $null -and (Entry $NewPath).Enabled -eq $false)
Check 'no SWBG entries, Publish copy restored' (@(Mods | Where-Object { $_.Path -like 'local//SWBG-*' }).Count -eq 0 -and ((LocalDirs) -join '|') -eq 'SWGB-DE-Factions-Publish|Unrelated Mod')
Check 'subscribed folder untouched' ((Get-Content -LiteralPath (Join-Path $newSub 'version.txt') -Raw) -eq 'v1.8')

Section '11. -Repair without an install (second, empty profile)'
$prof2 = Join-Path $Home_ 'Games\Age of Empires 2 DE\76561190000000002'
New-Item -ItemType Directory -Force -Path (Join-Path $prof2 'mods\local') | Out-Null
$rc = Run-Installer @('-Repair') '76561190000000002'
Check 'refuses (exit 1)' ($rc -eq 1)
Check 'tells the player to install first' ($script:out -match 'Run the installer first')
Check 'no mod-status.json written' (-not (Test-Path -LiteralPath (Join-Path $prof2 'mods\mod-status.json')))
Check 'first profile untouched' ((Entry $NewPath).Enabled -eq $false)

Section '12. Subscription is a different version (stale 1.6) and enabled; install'
Make-Subscribed $newSub 'v1.6' -Stale
Write-Status @(Mods | ForEach-Object { if ($_.Path -eq $NewPath) { $_.Enabled = $true }; $_ })
$rc = Run-Installer @()
Check 'exit code 0' ($rc -eq 0)
Check 'reports the version mismatch' ($script:out -match 'is a different version than this release')
Check 'local folders = SWBG-Data, SWBG-Logic, Unrelated Mod' (((LocalDirs) -join '|') -eq 'SWBG-Data|SWBG-Logic|Unrelated Mod')
Check 'local SWBG-Logic enabled' ((Entry 'local//SWBG-Logic').Enabled -eq $true)
Check 'stale subscription switched off' ((Entry $NewPath) -ne $null -and (Entry $NewPath).Enabled -eq $false)
Check 'exactly one Logic mod enabled, SWBG-Data enabled' ((LogicEnabled) -eq 1 -and (Entry 'local//SWBG-Data').Enabled -eq $true)
Check 'multiplayer note about the mismatched subscription' ($script:out -match 'copy is a different version, so it was switched off')
Check 'lobby help: choose the local SWBG-Logic (1.7) when two are listed' ($script:out -match 'If two SWBG-Logic entries appear, choose the local one \(version 1\.7\)')
Check 'stale subscribed folder untouched' ((Get-Content -LiteralPath (Join-Path $newSub 'version.txt') -Raw) -eq 'v1.6')

Section '12r. Player ticked the stale subscription again; -Repair keeps the local copy'
Write-Status @(Mods | ForEach-Object { if ($_.Path -eq $NewPath) { $_.Enabled = $true }; if ($_.Path -eq 'local//SWBG-Logic') { $_.Enabled = $false }; $_ })
$rc = Run-Installer @('-Repair')
Check 'exit code 0' ($rc -eq 0)
Check 'local SWBG-Logic enabled, stale subscription off' ((Entry 'local//SWBG-Logic').Enabled -eq $true -and (Entry $NewPath).Enabled -eq $false)
Check 'exactly one Logic mod enabled' ((LogicEnabled) -eq 1)
Check 'repair reports the version mismatch' ($script:out -match 'is a different version than this release')

Section '12m. The subscription is updated to the matching version (DE switched it off); install'
Make-Subscribed $newSub 'v1.7'
Write-Status @(Mods | ForEach-Object { if ($_.Path -eq $NewPath) { $_.Enabled = $false; $_.LastUpdate = '1795000000000' }; $_ })
$rc = Run-Installer @()
Check 'exit code 0' ($rc -eq 0)
Check 'subscription enabled, local SWBG-Logic removed' ((Entry $NewPath).Enabled -eq $true -and ((LocalDirs) -join '|') -eq 'SWBG-Data|Unrelated Mod')
Check 'exactly one Logic mod enabled, SWBG-Data enabled' ((LogicEnabled) -eq 1 -and (Entry 'local//SWBG-Data').Enabled -eq $true)
$rc = Run-Installer @('-Uninstall')
Check 'uninstall: exit code 0, no SWBG entries' ($rc -eq 0 -and @(Mods | Where-Object { $_.Path -like 'local//SWBG-*' }).Count -eq 0)

Write-Host "`nChecks: $script:checks, failures: $script:fails" -ForegroundColor $(if ($script:fails) { 'Red' } else { 'Green' })
exit $script:fails
