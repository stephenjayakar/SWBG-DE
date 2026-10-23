<#
.SYNOPSIS
  Installs the "SWGB in AoE2 DE" mods: SWBG-Data (graphics, sound, music,
  strings, maps, AI), generated from your own Star Wars Galactic Battlegrounds
  Saga + Expanding Fronts installation, and SWBG-Logic (the data mod). No game
  assets are included in this download.

  If you are subscribed to the published SWBG-Logic (mod 549437) and its game
  files match this release, that copy is enabled and no local SWBG-Logic is
  installed; otherwise a local SWBG-Logic is installed (single player).
  Multiplayer needs the subscribed mod 549437 at the matching version.
  Older installs (SWGB-DE-Factions-Assets / -Draft / -Publish folders) are
  moved to a backup and their mod-status.json entries removed.

.PARAMETER SwgbPath
  Star Wars Galactic Battlegrounds Saga folder (the one containing "Game", or
  the Game folder itself). Auto-detected from Steam (app 356500) and GOG.
.PARAMETER DePath
  Age of Empires II: Definitive Edition install folder (contains AoE2DE_s.exe).
  Auto-detected from Steam (app 813780) and the Microsoft Store.
.PARAMETER ProfileId
  DE profile number under %USERPROFILE%\Games\Age of Empires 2 DE\. Asked for
  when several exist (unless -Yes, which picks the most recently used one).
.PARAMETER Uninstall
  Remove the SWBG mods (also older SWGB-DE-Factions-* installs made by this
  installer) and put back whatever this installer backed up.
.PARAMETER Repair
  Only fix DE's mods\mod-status.json, without regenerating anything: enable
  SWBG-Data again, point the entry of mod 549437 at its current folder (DE
  renames the folder when the listing is renamed) and remove stale entries.
  Also deletes the AI files of earlier releases from SWBG-Data (SWGB Land AI
  and the separate "SWGB Classic AI" entry), so the lobby lists one SWBG AI.
  SWBG-Logic itself is a data mod; DE lists it as disabled in My Mods after
  every start, and it is chosen as the Data Mod in the lobby. Run with DE
  closed. Needs an existing install.
.PARAMETER NoEnable
  Do not edit DE's mods\mod-status.json (enable SWBG-Data yourself in My Mods
  and remove old SWGB-DE-Factions-* entries).
.PARAMETER Yes
  Non-interactive: accept defaults, no prompts.
#>
[CmdletBinding()]
param(
    [string]$SwgbPath,
    [string]$DePath,
    [string]$ProfileId,
    [switch]$Uninstall,
    [switch]$Repair,
    [switch]$NoEnable,
    [switch]$Yes,
    [switch]$KeepTemp
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $Here
$LogicMod = 'SWBG-Logic'
$DataMod = 'SWBG-Data'
$ModNames = @($LogicMod, $DataMod)
# Folder names used by earlier releases; migrated (backed up and removed) on install.
$LegacyMods = @('SWGB-DE-Factions-Draft', 'SWGB-DE-Factions-Assets', 'SWGB-DE-Factions-Publish')
$PublishedLogicId = 549437
# AI files that earlier releases shipped in SWBG-Data. Every .ai file there adds an entry to the
# lobby's AI list, and SWBG ships one AI (SWGB Classic AI, run by DE's own entries), so Install and
# -Repair delete these from an existing SWBG-Data. Same list as RETIRED in
# outputs/toolkit/ai_entries.py (check_single_ai.py compares them).
$RetiredDataFiles = @('resources\_common\ai\SWGB Land AI.ai', 'resources\_common\ai\SWGB Land AI.per', 'resources\_common\ai\SWGB Classic AI.ai')
# Current listing title of mod 549437. Only used for a hint (DE has not picked up a rename yet);
# the subscription itself is always matched by ID.
$PublishedLogicTitle = 'SWBG-Logic'
$Author = 'Local SWGB port project'
$StateDir = Join-Path $env:LOCALAPPDATA 'SWGB-DE-Installer'
$StatePath = Join-Path $StateDir 'state.json'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

function Say([string]$Text, [string]$Color = 'Gray') { Write-Host $Text -ForegroundColor $Color }
function Fail([string]$Text) {
    Write-Host ''
    Write-Host $Text -ForegroundColor Red
    Write-Host ''
    exit 1
}

function Read-Vdf-Paths([string]$File) {
    $paths = @()
    if (Test-Path -LiteralPath $File) {
        foreach ($m in [regex]::Matches((Get-Content -LiteralPath $File -Raw), '"path"\s+"([^"]+)"')) {
            $paths += $m.Groups[1].Value.Replace('\\', '\')
        }
    }
    return $paths
}

function Get-SteamLibraries {
    $roots = @()
    foreach ($key in 'HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam', 'HKLM:\SOFTWARE\Valve\Steam') {
        try {
            $item = Get-ItemProperty -LiteralPath $key -ErrorAction Stop
            foreach ($name in 'SteamPath', 'InstallPath') {
                if ($item.PSObject.Properties[$name] -and $item.$name) { $roots += ($item.$name -replace '/', '\') }
            }
        } catch { }
    }
    $libs = @()
    foreach ($r in ($roots | Select-Object -Unique)) {
        $libs += $r
        $libs += Read-Vdf-Paths (Join-Path $r 'steamapps\libraryfolders.vdf')
        $libs += Read-Vdf-Paths (Join-Path $r 'config\libraryfolders.vdf')
    }
    return $libs | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | ForEach-Object { (Resolve-Path -LiteralPath $_).Path } | Select-Object -Unique
}

function Find-SteamApp([string]$AppId) {
    foreach ($lib in Get-SteamLibraries) {
        $acf = Join-Path $lib "steamapps\appmanifest_$AppId.acf"
        if (Test-Path -LiteralPath $acf) {
            $m = [regex]::Match((Get-Content -LiteralPath $acf -Raw), '"installdir"\s+"([^"]+)"')
            if ($m.Success) {
                $dir = Join-Path $lib ("steamapps\common\" + $m.Groups[1].Value)
                if (Test-Path -LiteralPath $dir) { return $dir }
            }
        }
    }
    return $null
}

function Resolve-SwgbGame([string]$Path) {
    if (-not $Path) { return $null }
    foreach ($c in @((Join-Path $Path 'Game'), $Path)) {
        if (Test-Path -LiteralPath (Join-Path $c 'Data')) { return (Resolve-Path -LiteralPath $c).Path }
    }
    return $null
}

function Find-Swgb {
    if ($SwgbPath) {
        $g = Resolve-SwgbGame $SwgbPath
        if (-not $g) { Fail "No SWGB 'Game\Data' folder found under -SwgbPath '$SwgbPath'." }
        return $g
    }
    $candidates = @()
    $steam = Find-SteamApp '356500'
    if ($steam) { $candidates += $steam }
    foreach ($key in 'HKLM:\SOFTWARE\WOW6432Node\GOG.com\Games\1421404646', 'HKLM:\SOFTWARE\GOG.com\Games\1421404646') {
        try { $candidates += (Get-ItemProperty -LiteralPath $key -ErrorAction Stop).PATH } catch { }
    }
    foreach ($drive in (Get-PSDrive -PSProvider FileSystem | ForEach-Object { $_.Root })) {
        $candidates += (Join-Path $drive 'GOG Games\Star Wars - Galactic Battlegrounds')
        $candidates += (Join-Path $drive 'GOG Games\STAR WARS - Galactic Battlegrounds Saga')
    }
    $found = @()
    foreach ($c in $candidates) { $g = Resolve-SwgbGame $c; if ($g -and ($found -notcontains $g)) { $found += $g } }
    if ($found.Count -eq 0) { return $null }
    # Prefer an install that already has Expanding Fronts.
    $ef = @($found | Where-Object { Test-Path -LiteralPath (Join-Path $_ 'Data\graphics_x2.drs') })
    if ($ef.Count -gt 0) { return $ef[0] }
    return $found[0]
}

function Find-De {
    $c = @()
    if ($DePath) { $c += $DePath }
    else {
        $s = Find-SteamApp '813780'
        if ($s) { $c += $s }
        try {
            $pkg = Get-AppxPackage -Name '*AgeofEmpiresIIDefinitiveEdition*' -ErrorAction Stop | Select-Object -First 1
            if ($pkg) { $c += $pkg.InstallLocation }
        } catch { }
    }
    foreach ($d in $c) {
        if ($d -and (Test-Path -LiteralPath (Join-Path $d 'resources\_common\palettes\original.pal'))) { return (Resolve-Path -LiteralPath $d).Path }
    }
    if ($DePath) { Fail "-DePath '$DePath' does not look like an Age of Empires II: DE install (resources\_common\palettes missing)." }
    return $null
}

function Find-Profile {
    $base = Join-Path $env:USERPROFILE 'Games\Age of Empires 2 DE'
    if (-not (Test-Path -LiteralPath $base)) { Fail "DE profile folder not found: $base`nStart Age of Empires II: DE once (and reach the main menu), then run this installer again." }
    if ($ProfileId) {
        $p = Join-Path $base $ProfileId
        if (-not (Test-Path -LiteralPath $p)) { Fail "Profile folder not found: $p" }
        return $p
    }
    $dirs = @(Get-ChildItem -LiteralPath $base -Directory | Where-Object { $_.Name -match '^\d+$' -and $_.Name -ne '0' })
    if ($dirs.Count -eq 0) { $dirs = @(Get-ChildItem -LiteralPath $base -Directory | Where-Object { $_.Name -match '^\d+$' }) }
    if ($dirs.Count -eq 0) { Fail "No DE profile found in $base. Start DE once, then rerun." }
    $scored = foreach ($d in $dirs) {
        $status = Join-Path $d.FullName 'mods\mod-status.json'
        $hasOurs = (Test-Path -LiteralPath (Join-Path $d.FullName "mods\local\$DataMod")) -or (Test-Path -LiteralPath (Join-Path $d.FullName 'mods\local\SWGB-DE-Factions-Assets'))
        $time = if (Test-Path -LiteralPath $status) { (Get-Item -LiteralPath $status).LastWriteTime } else { $d.LastWriteTime }
        [pscustomobject]@{ Path = $d.FullName; Name = $d.Name; HasOurs = $hasOurs; Time = $time }
    }
    $sorted = @($scored | Sort-Object -Property @{Expression = 'HasOurs'; Descending = $true }, @{Expression = 'Time'; Descending = $true })
    if ($sorted.Count -eq 1 -or $Yes) { return $sorted[0].Path }
    Say 'Several DE profiles were found:' 'Yellow'
    for ($i = 0; $i -lt $sorted.Count; $i++) {
        $note = if ($sorted[$i].HasOurs) { ' (has SWGB mods)' } else { '' }
        Say ("  [{0}] {1}  last used {2}{3}" -f ($i + 1), $sorted[$i].Name, $sorted[$i].Time, $note)
    }
    $answer = Read-Host "Install into which profile? [1]"
    if (-not $answer) { $answer = '1' }
    $n = 0
    if (-not [int]::TryParse($answer, [ref]$n) -or $n -lt 1 -or $n -gt $sorted.Count) { Fail 'Invalid choice.' }
    return $sorted[$n - 1].Path
}

function Assert-DeClosed {
    $running = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^AoE2DE' })
    if ($running.Count -gt 0) { Fail 'Age of Empires II: Definitive Edition is running. Close the game completely, then run this again.' }
}

function Read-State {
    if (Test-Path -LiteralPath $StatePath) { return (Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json) }
    return $null
}

function Test-OurMod([string]$Folder, [string]$Name) {
    $info = Join-Path $Folder 'info.json'
    if (-not (Test-Path -LiteralPath $info)) { return $false }
    try { $j = Get-Content -LiteralPath $info -Raw | ConvertFrom-Json } catch { return $false }
    return ($j.Title -eq $Name -and $j.Author -eq $Author)
}

function Read-ModStatus([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return [pscustomobject]@{ Mods = @(); Unsub = @() } }
    return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json)
}

function Write-ModStatus([string]$Path, $Status) {
    $mods = @($Status.Mods)
    $unsub = @()
    if ($Status.PSObject.Properties['Unsub'] -and $Status.Unsub) { $unsub = @($Status.Unsub) }
    $parts = @()
    foreach ($m in $mods) { $parts += ($m | ConvertTo-Json -Compress -Depth 5) }
    $unsubJson = if ($unsub.Count -gt 0) { ($unsub | ForEach-Object { $_ | ConvertTo-Json -Compress -Depth 5 }) -join ',' } else { '' }
    $text = '{"Mods":[' + ($parts -join ',') + '],"Unsub":[' + $unsubJson + ']}'
    [IO.File]::WriteAllText($Path, $text, (New-Object Text.UTF8Encoding($false)))
}

function Get-Sha256([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }

function Get-StateList($State, [string]$Name) {
    if ($State -and $State.PSObject.Properties[$Name] -and $State.$Name) { return @($State.$Name) }
    return @()
}

function Get-StateMap($State, [string]$Name) {
    # State maps are JSON objects; keys without "//" are mod-status paths of local mods (older state files).
    $map = [ordered]@{}
    if ($State -and $State.PSObject.Properties[$Name] -and $State.$Name) {
        foreach ($p in $State.$Name.PSObject.Properties) {
            $key = if ($p.Name -like '*//*') { $p.Name } else { "local//$($p.Name)" }
            $map[$key] = $p.Value
        }
    }
    return $map
}

function Find-SubscribedLogic([string]$ProfileDir) {
    # The published SWBG-Logic, downloaded by DE into mods\subscribed\<id>_<title>. Found by the
    # mod ID only: the title part changes when the listing is renamed. If DE left several folders,
    # the one with the newest DAT wins.
    $sub = Join-Path $ProfileDir 'mods\subscribed'
    if (-not (Test-Path -LiteralPath $sub)) { return $null }
    $best = $null; $bestTime = [datetime]::MinValue
    foreach ($d in @(Get-ChildItem -LiteralPath $sub -Directory | Where-Object { $_.Name -like "$($PublishedLogicId)_*" })) {
        $dat = Join-Path $d.FullName 'resources\_common\dat\empires2_x2_p1.dat'
        if (Test-Path -LiteralPath $dat) {
            $t = (Get-Item -LiteralPath $dat).LastWriteTimeUtc
            if ($t -gt $bestTime) { $best = $d; $bestTime = $t }
        }
    }
    if (-not $best) { return $null }
    return [pscustomobject]@{ Folder = $best.FullName; Path = "subscribed//$($best.Name)"; Title = $best.Name.Substring(("$PublishedLogicId").Length + 1) }
}

function Test-PublishedLogicEntry($Entry) {
    # mod-status.json entry of mod 549437, matched by ID (WorkshopID or the "<id>_" folder prefix), never by title.
    if (-not $Entry) { return $false }
    if ($Entry.PSObject.Properties['WorkshopID'] -and "$($Entry.WorkshopID)" -eq "$PublishedLogicId") { return $true }
    return ("$($Entry.Path)" -like "subscribed//$($PublishedLogicId)_*")
}

function Get-PriorFor($PriorMap, $Entry) {
    # Prior enabled state recorded at install time. Mod 549437's entry may have been renamed since
    # (new listing title), so fall back to any recorded entry of the same mod ID.
    if ($PriorMap.Contains($Entry.Path)) { return $PriorMap[$Entry.Path] }
    if (Test-PublishedLogicEntry $Entry) {
        foreach ($k in @($PriorMap.Keys)) { if ($k -like "subscribed//$($PublishedLogicId)_*") { return $PriorMap[$k] } }
    }
    return $null
}

function Show-Multiplayer-Note($Subscribed, $Stale) {
    Say ''
    if ($Subscribed) {
        Say "Multiplayer: every player needs SWBG-Data from this installer release (enabled in My Mods) and the subscribed SWBG-Logic" 'Cyan'
        Say "(mod $PublishedLogicId), which the host chooses as the Data Mod." 'Cyan'
    } elseif ($Stale) {
        Say "Multiplayer needs mod $PublishedLogicId at the version that matches this installer release; your subscribed" 'Yellow'
        Say 'copy is a different version, so it was switched off. Once the listing has the matching update, start DE so it' 'Yellow'
        Say 're-downloads the mod, close it and run this installer again. It then enables the subscribed copy.' 'Yellow'
    } else {
        Say "Multiplayer needs the published SWBG-Logic: subscribe to mod $PublishedLogicId (unlisted) at" 'Yellow'
        Say "  https://www.ageofempires.com/mods/details/$PublishedLogicId/" 'Yellow'
        Say 'restart DE once so it downloads, close it and run this installer again. It then enables the subscribed' 'Yellow'
        Say 'copy instead of the local SWBG-Logic, which works in single player only.' 'Yellow'
    }
}

function Remove-RetiredDataFiles([string]$DataDir) {
    foreach ($rel in $RetiredDataFiles) {
        $p = Join-Path $DataDir $rel
        if (Test-Path -LiteralPath $p -PathType Leaf) {
            Remove-Item -LiteralPath $p -Force
            Say "Removed $p (earlier releases' AI; SWBG now has one AI, SWGB Classic AI)"
        }
    }
}

function Get-RepairHint {
    if ($env:SWGB_DE_LAUNCHER) { return "close DE, run $($env:SWGB_DE_LAUNCHER) again and choose R (Repair)" }
    return 'close DE and run Repair-SWGB-DE.cmd'
}

function Get-LocalLogicVersion {
    # Version of the local SWBG-Logic this installer sets up (installed copy, else the payload).
    foreach ($dir in @((Join-Path $Local $LogicMod), (Join-Path $Root "payload\$LogicMod"))) {
        $info = Join-Path $dir 'info.json'
        if (Test-Path -LiteralPath $info) {
            try { $v = (Get-Content -LiteralPath $info -Raw | ConvertFrom-Json).Version; if ($v) { return "$v" } } catch { }
        }
    }
    return $null
}

function Show-Lobby-Help($Subscribed) {
    # DE writes "Enabled": false for every data mod (SWBG-Logic, local or subscribed) at each start,
    # yet still lists data mods in the lobby. So only SWBG-Data has to be enabled in My Mods.
    Say ''
    Say 'How to play:' 'Cyan'
    Say "  1. Start Age of Empires II: DE. In Mods > My Mods, make sure $DataMod is enabled."
    Say "     $LogicMod is a data mod: My Mods shows it as disabled after every DE start. That is normal; it is chosen in the lobby."
    Say "     If $DataMod is off (for example after a crash or an update), enable it again, or $(Get-RepairHint)."
    Say "  2. Single Player > Skirmish: choose $LogicMod as the Data Mod. It resets to Default each time, so choose it every time."
    if ($Subscribed) {
        Say "     Choose the subscribed $LogicMod (mod $PublishedLogicId)."
    } else {
        $version = Get-LocalLogicVersion
        $which = if ($version) { "the local one (version $version)" } else { 'the local one' }
        Say "     If two $LogicMod entries appear, choose $which. That is the one this installer set up;"
        Say "     the other is the mod $PublishedLogicId subscription."
    }
    Say '  3. Pick Galactic Empire / Rebel Alliance, map "SWGB Factions Savannah" (or another SWGB Factions map).'
    Say '     Computer players: every AI choice ("AI", "AI (CD version)", "AI (HD version)") runs the SWGB Classic AI.'
    Say '     Tech Level 1 / finite resources are recommended.'
    Say "  4. Disable $DataMod again for ordinary (non-SWGB) DE games."
}

function Get-ModFolder([string]$ModPath) {
    # mod-status.json paths are "local//<folder>" or "subscribed//<folder>", relative to the mods folder.
    return Join-Path (Split-Path -Parent $StatusPath) ($ModPath -replace '//', '\')
}

function Update-ModStatus($Subscribed, [string[]]$DropPaths, $Prior, $Removed, [string]$BackupRoot) {
    # Exactly one Logic mod (subscribed 549437 or the local SWBG-Logic) and SWBG-Data end up enabled.
    # $Prior / $Removed are the state maps (path -> recorded state); they are updated in place.
    #
    # How DE treats mod 549437's entry (seen 2026-10-20 on DE build 185872): when the listing changes
    # (new version, or a new title), DE downloads it into mods\subscribed\549437_<current title>, points
    # the entry (matched by WorkshopID) at that folder and sets "Enabled": false. Entries whose folder
    # has gone are stale. So the entry for the folder that exists now is the one to enable; stale ones
    # are adopted (if there is no entry for the current folder) or removed.
    $logicPath = if ($Subscribed) { $Subscribed.Path } else { "local//$LogicMod" }
    $logicTitle = if ($Subscribed) { $Subscribed.Title } else { $LogicMod }
    if (Test-Path -LiteralPath $StatusPath) {
        New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
        Copy-Item -LiteralPath $StatusPath -Destination (Join-Path $BackupRoot 'mod-status.json')
    }
    $status = Read-ModStatus $StatusPath
    $mods = @()
    foreach ($m in @($status.Mods)) {
        if ($DropPaths -contains $m.Path) {
            if (-not $Removed.Contains($m.Path) -and -not $Prior.Contains($m.Path)) { $Removed[$m.Path] = $m }
            Say "Removed the mod-status.json entry for $($m.Path)"
            continue
        }
        $mods += $m
    }
    if ($Subscribed) {
        $current = @($mods | Where-Object { $_.Path -eq $logicPath })
        foreach ($dup in @($current | Select-Object -Skip 1)) {
            $mods = @($mods | Where-Object { -not [object]::ReferenceEquals($_, $dup) })
            Say "Removed a duplicate mod-status.json entry for $logicPath"
        }
        $current = $current | Select-Object -First 1
        foreach ($o in @($mods | Where-Object { $_.Path -ne $logicPath -and (Test-PublishedLogicEntry $_) })) {
            # Another downloaded copy of 549437 that still exists is switched off further down.
            if ("$($o.Path)" -like '*//*' -and (Test-Path -LiteralPath (Get-ModFolder $o.Path))) { continue }
            if (-not $current) {
                Say "Updating the mod-status.json entry $($o.Path) to $logicPath"
                $o.Path = $logicPath
                $o.Title = $logicTitle
                $current = $o
            } else {
                # DE has already written its own entry for the current folder: prefer that one.
                $mods = @($mods | Where-Object { -not [object]::ReferenceEquals($_, $o) })
                Say "Removed the stale mod-status.json entry $($o.Path) (its folder is gone; DE's entry for $logicPath is used)"
            }
        }
        # The state recorded before the first install (for -Uninstall) may be keyed by an older folder
        # name of 549437: move it to the current one rather than recording the present flag as "prior".
        if (-not $Prior.Contains($logicPath)) {
            foreach ($k in @($Prior.Keys)) {
                if ($k -like "subscribed//$($PublishedLogicId)_*" -and -not (Test-Path -LiteralPath (Get-ModFolder $k))) {
                    $Prior[$logicPath] = $Prior[$k]
                    $Prior.Remove($k)
                    break
                }
            }
        }
    }
    $enable = @(
        [pscustomobject]@{ Path = "local//$DataMod"; Title = $DataMod; WorkshopID = 0 },
        [pscustomobject]@{ Path = $logicPath; Title = $logicTitle; WorkshopID = $(if ($Subscribed) { $PublishedLogicId } else { 0 }) }
    )
    foreach ($e in $enable) {
        $entry = $mods | Where-Object { $_.Path -eq $e.Path } | Select-Object -First 1
        if (-not $Prior.Contains($e.Path)) {
            $Prior[$e.Path] = [ordered]@{ Existed = [bool]$entry; Enabled = $(if ($entry) { [bool]$entry.Enabled } else { $false }) }
        }
        if ($entry) {
            if ($entry.Enabled) { Say "Kept $($e.Path) enabled in $StatusPath" }
            else { $entry.Enabled = $true; Say "Enabled $($e.Path) in $StatusPath" }
        } else {
            $maxPriority = 0
            foreach ($m in $mods) { if ([int]$m.Priority -gt $maxPriority) { $maxPriority = [int]$m.Priority } }
            $mods += [pscustomobject][ordered]@{ CheckSum = '0'; Enabled = $true; LastUpdate = '0'; Path = $e.Path; Priority = $maxPriority + 1; PublishID = 0; Title = $e.Title; WorkshopID = $e.WorkshopID }
            Say "Enabled $($e.Path) in $StatusPath"
        }
    }
    # Never two Logic mods: switch off any other entry of mod 549437 (another downloaded copy) and
    # the local SWBG-Logic when the subscription is used.
    foreach ($m in $mods) {
        if ($m.Path -eq $logicPath -or -not $m.Enabled) { continue }
        if ((Test-PublishedLogicEntry $m) -or $m.Path -eq "local//$LogicMod") {
            if (-not $Prior.Contains($m.Path)) { $Prior[$m.Path] = [ordered]@{ Existed = $true; Enabled = $true } }
            $m.Enabled = $false
            Say "Disabled $($m.Path) (only one Logic mod may be enabled)"
        }
    }
    $status.Mods = $mods
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StatusPath) | Out-Null
    Write-ModStatus $StatusPath $status
    return [pscustomobject]@{ Path = $logicPath; Title = $logicTitle }
}

function Show-Resync-Note($Subscribed) {
    # The folder still carries an older listing title: DE re-downloads the mod on its next start
    # and renames the folder, which leaves a stale mod-status.json entry behind.
    if ($Subscribed -and $Subscribed.Title -ne $PublishedLogicTitle) {
        Say ''
        Say "Note: your copy of mod $PublishedLogicId is still named '$($Subscribed.Title)'. The listing is now called $PublishedLogicTitle," 'Yellow'
        Say "so DE will download it again the next time it starts and rename its folder. Choose it in the lobby as usual." 'Yellow'
        Say "If $DataMod is off in Mods > My Mods afterwards, enable it again (or $(Get-RepairHint))." 'Yellow'
    }
}

function Get-ShipList([string]$RecipePath) {
    $list = @()
    foreach ($line in Get-Content -LiteralPath $RecipePath) {
        $f = $line.Split("`t")
        if ($f[0] -eq 'ship') { $list += , $f }
    }
    return , $list
}

function Get-SubscribedLogicDiff($Subscribed, $Ship) {
    # SWBG-Data's AI, maps and scripts name units by ID, so they only work with the exact SWBG-Logic
    # game files of this release (data mod 1.7 moved 98 unit IDs out of DE's reserved range 900-999).
    # Returns the SWBG-Logic game files of this release that the subscribed copy lacks or has changed.
    $differs = @()
    foreach ($f in $Ship) {
        if ($f[1] -ne $LogicMod -or $f[2] -eq 'README.md' -or $f[2] -eq 'VERSION') { continue }
        $p = Join-Path $Subscribed.Folder ($f[2].Replace('/', '\'))
        if (-not (Test-Path -LiteralPath $p) -or (Get-Sha256 $p) -ne $f[3]) { $differs += $f[2] }
    }
    return $differs  # callers wrap the result in @(); nothing is returned when all files match
}

# ---------------------------------------------------------------------------
Say ''
Say '=== SWGB in Age of Empires II: DE - installer ===' 'Cyan'
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
$LogDir = Join-Path $StateDir 'logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Assert-DeClosed
# Clear leftovers of an interrupted earlier run.
Get-ChildItem -LiteralPath $StateDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^(staging|temp)-\d{8}-\d{6}$' } |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
$DeProfile = Find-Profile
$Local = Join-Path $DeProfile 'mods\local'
$StatusPath = Join-Path $DeProfile 'mods\mod-status.json'
Say "DE profile: $DeProfile"

if ($Uninstall) {
    $state = Read-State
    $installed = Get-StateList $state 'Installed'
    # Current names: any folder this project made. Older names (SWGB-DE-Factions-*): only
    # folders an earlier installer version installed (state.json), never your own copies.
    foreach ($name in ($ModNames + $LegacyMods)) {
        $dir = Join-Path $Local $name
        if (Test-Path -LiteralPath $dir) {
            if (-not (Test-OurMod $dir $name)) { Say "Skipping $dir (not an SWGB-DE mod folder)." 'Yellow'; continue }
            if (($LegacyMods -contains $name) -and ($installed -notcontains $dir)) { Say "Leaving $dir (not installed by this installer)." 'Yellow'; continue }
            Say "Removing $dir"
            Remove-Item -LiteralPath $dir -Recurse -Force
        }
    }
    if ($state -and $state.PSObject.Properties['Backups'] -and $state.Backups) {
        foreach ($p in $state.Backups.PSObject.Properties) {
            $src = $p.Value
            $dst = Join-Path $Local $p.Name
            if ((Test-Path -LiteralPath $src) -and -not (Test-Path -LiteralPath $dst)) {
                Say "Restoring your previous $($p.Name) from $src"
                Move-Item -LiteralPath $src -Destination $dst
            }
        }
    }
    $priorMap = Get-StateMap $state 'ModStatusPrior'
    $removedMap = Get-StateMap $state 'ModStatusRemoved'
    if ($state -and (Test-Path -LiteralPath $StatusPath) -and ($priorMap.Count -or $removedMap.Count)) {
        $status = Read-ModStatus $StatusPath
        $keep = @()
        foreach ($m in @($status.Mods)) {
            $prior = Get-PriorFor $priorMap $m
            if ($prior -ne $null) {
                if (-not $prior.Existed) {
                    # Entries the installer added. A subscription is never dropped, only switched off.
                    if (Test-PublishedLogicEntry $m) { $m.Enabled = $false; $keep += $m }
                    continue
                }
                $m.Enabled = [bool]$prior.Enabled
            }
            $keep += $m
        }
        # Entries removed when older folders were migrated come back with their restored folders.
        foreach ($path in $removedMap.Keys) {
            if (@($keep | Where-Object { $_.Path -eq $path }).Count) { continue }
            $folder = if ($path -like 'local//*') { Join-Path $Local ($path -replace '^local//', '') } else { Join-Path (Split-Path -Parent $StatusPath) ($path -replace '//', '\') }
            if (Test-Path -LiteralPath $folder) {
                Say "Restoring the mod-status.json entry for $path"
                $keep += $removedMap[$path]
            }
        }
        $status.Mods = $keep
        Write-ModStatus $StatusPath $status
    }
    if (Test-Path -LiteralPath $StatePath) { Move-Item -LiteralPath $StatePath -Destination (Join-Path $LogDir "state-uninstalled-$Stamp.json") }
    Say 'Uninstall complete.' 'Green'
    exit 0
}

if ($Repair) {
    # Re-enable SWBG-Data and the one Logic mod after DE switched them off (new version or renamed
    # listing of mod 549437, or a crash). Edits mod-status.json and deletes retired AI files only; nothing is regenerated.
    if ($NoEnable) { Fail '-Repair only edits mod-status.json, so it cannot be combined with -NoEnable.' }
    if (-not (Test-Path -LiteralPath (Join-Path $Local $DataMod))) {
        Fail "$DataMod is not installed in $Local.`nRun the installer first (Install, without -Repair)."
    }
    Remove-RetiredDataFiles (Join-Path $Local $DataMod)
    $Subscribed = Find-SubscribedLogic $DeProfile
    if ($Subscribed) {
        # Same rule as Install: the subscription is only used when its game files match this release.
        $differs = @(Get-SubscribedLogicDiff $Subscribed (Get-ShipList (Join-Path $Here 'recipe.tsv')))
        if ($differs.Count -gt 0) {
            if (-not (Test-Path -LiteralPath (Join-Path $Local $LogicMod))) {
                Fail ("The subscribed mod $PublishedLogicId ($($Subscribed.Folder)) is a different version than this release ($($differs.Count) game files differ),`n" +
                      "and no local $LogicMod is installed. Run the installer (Install, without -Repair): it installs a matching local $LogicMod.")
            }
            Say "SWBG-Logic: the subscribed mod $PublishedLogicId ($($Subscribed.Folder)) is a different version than this release ($($differs.Count) game files differ)." 'Yellow'
            Say "  The local copy ($(Join-Path $Local $LogicMod)) is used and the subscription is switched off." 'Yellow'
            $Subscribed = $null
        }
    }
    if ($Subscribed) {
        Say "SWBG-Logic: subscribed mod $PublishedLogicId ($($Subscribed.Folder))"
    } elseif (Test-Path -LiteralPath (Join-Path $Local $LogicMod)) {
        Say "SWBG-Logic: local copy ($(Join-Path $Local $LogicMod)); not subscribed to mod $PublishedLogicId"
    } else {
        Fail "Neither the subscribed mod $PublishedLogicId nor a local $LogicMod was found.`nRun the installer first (Install, without -Repair)."
    }
    $state = Read-State
    # state.json belongs to the profile the installer last installed into; leave it alone for others.
    $sameProfile = (-not $state) -or (-not $state.PSObject.Properties['Profile']) -or ("$($state.Profile)" -eq $DeProfile)
    $prior = if ($sameProfile) { Get-StateMap $state 'ModStatusPrior' } else { [ordered]@{} }
    $removed = if ($sameProfile) { Get-StateMap $state 'ModStatusRemoved' } else { [ordered]@{} }
    $logic = Update-ModStatus $Subscribed @() $prior $removed (Join-Path $StateDir "backups\$Stamp")
    if ($sameProfile) {
        $newState = [ordered]@{}
        if ($state) { foreach ($p in $state.PSObject.Properties) { $newState[$p.Name] = $p.Value } }
        else { $newState['Profile'] = $DeProfile; $newState['Installed'] = @() }
        $newState['RepairedAt'] = (Get-Date).ToString('s')
        $newState['Logic'] = $logic.Path
        $newState['ModStatusPrior'] = $prior
        $newState['ModStatusRemoved'] = $removed
        $newState | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $StatePath -Encoding UTF8
    }
    Say ''
    Say "Repair complete: $DataMod is enabled and the SWBG-Logic entry is $($logic.Path); no other copy of SWBG-Logic is enabled." 'Green'
    Show-Resync-Note $Subscribed
    Show-Lobby-Help $Subscribed
    exit 0
}

# --- Detect games ------------------------------------------------------------
$De = Find-De
if (-not $De) { Fail "Age of Empires II: Definitive Edition was not found (Steam app 813780 or Microsoft Store).`nInstall it, or pass -DePath ""<DE folder>""." }
Say "AoE2 DE:    $De"
$Game = Find-Swgb
if (-not $Game) { Fail "Star Wars Galactic Battlegrounds Saga was not found (Steam app 356500 or GOG).`nInstall it, or pass -SwgbPath ""<SWGB folder>""." }
Say "SWGB Saga:  $Game"

$data = Join-Path $Game 'Data'
$base = @('GRAPHICS.DRS', 'SOUNDS.DRS', 'INTERFAC.DRS', 'graphics_x1.drs', 'sounds_x1.drs')
$ef = @('graphics_x2.drs', 'sounds_x2.drs', 'interfac_x2.drs')
$firstRun = @('graphics_p1.drs', 'graphics_x1_p1.drs')
$missing = @($base | Where-Object { -not (Test-Path -LiteralPath (Join-Path $data $_)) })
if ($missing.Count) { Fail ("This SWGB install is incomplete (missing " + ($missing -join ', ') + "). Saga / Clone Campaigns is required.") }
$missing = @($ef | Where-Object { -not (Test-Path -LiteralPath (Join-Path $data $_)) })
if ($missing.Count -or -not (Test-Path -LiteralPath (Join-Path $Game 'Sound\Stream\ef_civ1.mp3'))) {
    Fail ("Expanding Fronts is not installed in $Game.`n" +
          "This port uses the Expanding Fronts 1.5.5 artwork and sounds. Download the free 'Full' version of Expanding Fronts,`n" +
          "merge its GAME folder into your SWGB 'Game' folder (see its Manual Installation Guide), run battlegrounds_x2.exe once,`n" +
          "then run this installer again.")
}
$missing = @($firstRun | Where-Object { -not (Test-Path -LiteralPath (Join-Path $data $_)) })
if ($missing.Count) {
    Fail ("Expanding Fronts has not completed its First Run (missing " + ($missing -join ', ') + ").`n" +
          "Start battlegrounds_x2.exe once and let it convert the original assets, quit, then run this installer again.")
}

$recipe = Join-Path $Here 'recipe.tsv'
$texconv = Join-Path $De 'Tools_Builds\texconv.exe'
if (-not (Test-Path -LiteralPath $texconv) -and -not (Test-Path -LiteralPath (Join-Path $Here 'tools\texconv.exe'))) {
    Fail "texconv.exe was not found in $De\Tools_Builds. Put Microsoft's texconv.exe (github.com/microsoft/DirectXTex releases) into $Here\tools and rerun."
}
$archives = @{}
foreach ($line in Get-Content -LiteralPath $recipe) {
    $f = $line.Split("`t")
    if ($f[0] -eq 'smx' -or $f[0] -eq 'wem') { $archives[$f[3]] = 1 }
}
foreach ($a in $archives.Keys) {
    if (-not (Test-Path -LiteralPath (Join-Path $data $a))) { Fail "Required SWGB/EF archive missing: $(Join-Path $data $a)" }
}

# --- Payload check -------------------------------------------------------------
$ship = Get-ShipList $recipe
foreach ($f in $ship) {
    $p = Join-Path $Root ("payload\" + $f[1] + "\" + $f[2].Replace('/', '\'))
    if (-not (Test-Path -LiteralPath $p)) { Fail "Installer payload incomplete (missing $p). Re-extract the installer ZIP." }
}

# --- Space ---------------------------------------------------------------------
$needGB = 4
foreach ($probe in @($StateDir, $Local)) {
    $qual = Split-Path -Qualifier ([IO.Path]::GetFullPath($probe))
    $drive = Get-PSDrive -Name $qual.TrimEnd(':') -ErrorAction SilentlyContinue
    if ($drive -and $drive.Free -lt ($needGB * 1GB)) { Fail ("Not enough free space on {0} ({1:N1} GB free, about {2} GB needed)." -f $qual, ($drive.Free / 1GB), $needGB) }
}

# --- Logic source --------------------------------------------------------------
$Subscribed = Find-SubscribedLogic $DeProfile
$StaleSubscription = $null
if ($Subscribed) {
    $differs = @(Get-SubscribedLogicDiff $Subscribed $ship)
    if ($differs.Count -gt 0) {
        Say "SWBG-Logic: the subscribed mod $PublishedLogicId ($($Subscribed.Folder)) is a different version than this release ($($differs.Count) game files differ, e.g. $($differs[0]))." 'Yellow'
        Say '  It would not match this SWBG-Data, so a local SWBG-Logic is installed instead and the subscription is switched off.' 'Yellow'
        $StaleSubscription = $Subscribed
        $Subscribed = $null
    }
}
if ($Subscribed) {
    Say "SWBG-Logic: subscribed mod $PublishedLogicId found ($($Subscribed.Folder)); no local copy will be installed."
    $InstallNames = @($DataMod)
} else {
    if (-not $StaleSubscription) { Say "SWBG-Logic: not subscribed to mod $PublishedLogicId; a local SWBG-Logic will be installed (single player)." }
    $InstallNames = @($LogicMod, $DataMod)
}

if (-not $Yes) {
    Say ''
    Say ("This will generate the SWGB artwork/sound/music from your SWGB install and install " + ($InstallNames -join ' + ') + " into:")
    Say "  $Local"
    Say "Existing SWBG / SWGB-DE mod folders that this installer did not create are moved to a backup first."
    $null = Read-Host 'Press Enter to continue (Ctrl+C to cancel)'
}

# --- Build -----------------------------------------------------------------------
$staging = Join-Path $StateDir "staging-$Stamp"
$temp = Join-Path $StateDir "temp-$Stamp"
New-Item -ItemType Directory -Force -Path $staging, $temp | Out-Null
try {
    Say ''
    Say 'Copying the mod data...' 'Cyan'
    # Both payload mods are staged: SWBG-Logic's materials.json drives the atlas rebuild even
    # when the subscribed copy is used.
    foreach ($name in $ModNames) {
        $src = Join-Path $Root "payload\$name"
        Copy-Item -LiteralPath $src -Destination (Join-Path $staging $name) -Recurse
    }
    $bad = 0
    foreach ($f in $ship) {
        $p = Join-Path $staging ($f[1] + "\" + $f[2].Replace('/', '\'))
        if ((Get-Sha256 $p) -ne $f[3]) { Say "Payload file damaged: $($f[1])/$($f[2])" 'Red'; $bad++ }
    }
    if ($bad) { Fail "$bad payload files failed their checksum. Re-download the installer." }

    Say 'Compiling the converter...' 'Cyan'
    Add-Type -Path (Join-Path $Here 'SwgbDeBuilder.cs') -ReferencedAssemblies System.Drawing
    $runner = New-Object SwgbDe.Runner
    $runner.GameDir = $Game
    $runner.DeDir = $De
    $runner.DataOut = Join-Path $staging $DataMod
    $runner.ToolsDir = Join-Path $Here 'tools'
    $runner.TempDir = $temp
    $runner.RecipePath = $recipe
    $runner.LogicMaterials = Join-Path $staging "$LogicMod\widgetui\materials.json"
    $runner.ReportPath = Join-Path $LogDir "generated-$Stamp.tsv"
    $ok = $runner.Run()
    if (-not $ok) { Fail "Asset generation failed ($($runner.Errors) errors). Nothing was installed. Details: $($runner.ReportPath)" }
    if ($runner.Differs -gt 0) {
        Say "Note: $($runner.Differs) generated files differ from the reference build although their sources match. See $($runner.ReportPath)." 'Yellow'
    }
    if ($runner.SourceDiffers -gt 0) {
        Say "Note: $($runner.SourceDiffers) files were converted from SWGB/EF files that differ from the reference install (other EF version?). They were still converted." 'Yellow'
    }

    # --- Swap into place -------------------------------------------------------
    Assert-DeClosed
    $state = Read-State
    $installed = Get-StateList $state 'Installed'
    $backups = [ordered]@{}
    if ($state -and $state.PSObject.Properties['Backups'] -and $state.Backups) {
        foreach ($p in $state.Backups.PSObject.Properties) { if (Test-Path -LiteralPath $p.Value) { $backups[$p.Name] = $p.Value } }
    }
    $superseded = [ordered]@{}
    if ($state -and $state.PSObject.Properties['Superseded'] -and $state.Superseded) {
        foreach ($p in $state.Superseded.PSObject.Properties) { if (Test-Path -LiteralPath $p.Value) { $superseded[$p.Name] = $p.Value } }
    }
    $prior = Get-StateMap $state 'ModStatusPrior'
    $removed = Get-StateMap $state 'ModStatusRemoved'
    $dropPaths = @()
    New-Item -ItemType Directory -Force -Path $Local | Out-Null
    $backupRoot = Join-Path $StateDir "backups\$Stamp"
    function Move-ToBackup([string]$Name, [string]$Dest) {
        New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
        $bk = Join-Path $backupRoot $Name
        Move-Item -LiteralPath $Dest -Destination $bk
        return $bk
    }

    # Older folder names are always backed up and removed (never deleted). Folders that an
    # earlier version of this installer created are recorded as superseded and are not put
    # back by -Uninstall; anything else (a hand-installed share ZIP, a local publishing copy)
    # is recorded as a backup and restored by -Uninstall.
    foreach ($name in $LegacyMods) {
        $dest = Join-Path $Local $name
        if (-not (Test-Path -LiteralPath $dest)) { continue }
        $earlier = ($installed -contains $dest) -and (Test-OurMod $dest $name)
        $bk = Move-ToBackup $name $dest
        if ($earlier) {
            Say "Migrating: moved the earlier installer's $name to $bk"
            $superseded[$name] = $bk
        } else {
            Say "Migrating: backed up existing $name to $bk"
            $backups[$name] = $bk
        }
        $dropPaths += "local//$name"
    }

    foreach ($name in $ModNames) {
        $dest = Join-Path $Local $name
        $want = $InstallNames -contains $name
        if (Test-Path -LiteralPath $dest) {
            $ours = ($installed -contains $dest) -and (Test-OurMod $dest $name)
            if ($ours) {
                if ($want) { Say "Replacing the previous installer-generated $name" }
                else { Say "Removing the previous installer-generated $name (the subscribed mod $PublishedLogicId replaces it)" }
                Remove-Item -LiteralPath $dest -Recurse -Force
            } else {
                $bk = Move-ToBackup $name $dest
                Say "Backing up existing $name to $bk"
                $backups[$name] = $bk
            }
            if (-not $want) { $dropPaths += "local//$name" }
        }
        if ($want) { Move-Item -LiteralPath (Join-Path $staging $name) -Destination $dest }
    }
    # The old SWBG-Data was replaced or backed up above; this keeps the rule explicit for any copy left.
    Remove-RetiredDataFiles (Join-Path $Local $DataMod)

    # --- Enable in mod-status.json -------------------------------------------------
    # Exactly one Logic mod (subscribed 549437 or the local SWBG-Logic) and SWBG-Data end up enabled.
    $logicPath = if ($Subscribed) { $Subscribed.Path } else { "local//$LogicMod" }
    if (-not $NoEnable) {
        $logic = Update-ModStatus $Subscribed $dropPaths $prior $removed $backupRoot
        $logicPath = $logic.Path
    }

    $newState = [ordered]@{
        InstalledAt = (Get-Date).ToString('s'); Profile = $DeProfile; De = $De; Swgb = $Game
        Installed = @($InstallNames | ForEach-Object { Join-Path $Local $_ })
        Logic = $logicPath
        Backups = $backups; Superseded = $superseded; ModStatusPrior = $prior; ModStatusRemoved = $removed; Report = $runner.ReportPath
    }
    $newState | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $StatePath -Encoding UTF8
}
finally {
    if (-not $KeepTemp) {
        foreach ($d in @($staging, $temp)) { if (Test-Path -LiteralPath $d) { Remove-Item -LiteralPath $d -Recurse -Force -ErrorAction SilentlyContinue } }
    }
}

Say ''
Say ("Installed: {0} files generated from your SWGB install ({1} byte-identical to the reference build, {2} DE interface atlases rebuilt)." -f ($runner.Exact + $runner.Rebuilt + $runner.Differs + $runner.SourceDiffers), $runner.Exact, $runner.Rebuilt) 'Green'
if ($backups.Count) { Say "Your previous SWBG / SWGB-DE folders are backed up in: $((@($backups.Values) | Select-Object -Unique) -join ', ')" }
if ($superseded.Count) { Say "Folders from an earlier version of this installer were moved to: $((@($superseded.Values) | Select-Object -Unique) -join ', ') (safe to delete)" }
if ($NoEnable) { Say "mod-status.json was not changed (-NoEnable): enable $DataMod yourself in Mods > My Mods." 'Yellow' }
else { Show-Resync-Note $Subscribed }
Show-Lobby-Help $Subscribed
Show-Multiplayer-Note $Subscribed $StaleSubscription
Say ''
if ($env:SWGB_DE_LAUNCHER) { Say "To uninstall later, run $($env:SWGB_DE_LAUNCHER) again and choose Uninstall (or pass -Uninstall)." }
else { Say 'To uninstall later, run Uninstall-SWGB-DE.cmd.' }
exit 0
