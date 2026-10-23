param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$Build
)
$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$releaseRoot = (Resolve-Path -LiteralPath (Join-Path $workspaceRoot 'outputs/releases')).Path
$deliveryDirectory = 'E:\Dropbox\temp\SWBG'
if (-not (Test-Path -LiteralPath $deliveryDirectory)) {
    New-Item -ItemType Directory -Path $deliveryDirectory -Force | Out-Null
}
$deliveryRoot = (Resolve-Path -LiteralPath $deliveryDirectory).Path
$prefix = 'SWGB-DE-0.0.2-dev-' + $Build.Substring(0, 7)
$names = @("$prefix.zip", "$prefix.zip.sha256", "$prefix-upload-data.zip",
           "$prefix-upload-data.zip.sha256", "$prefix-upload-data.manifest.json")

function Assert-DeliveryPath([string]$Path) {
    $resolved = [System.IO.Path]::GetFullPath($Path)
    if (Test-Path -LiteralPath $resolved) {
        $resolved = (Resolve-Path -LiteralPath $resolved).Path
    }
    if (-not $resolved.StartsWith($deliveryRoot.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the Dropbox delivery directory: $resolved"
    }
    return $resolved
}

# The exporters reach this helper only after ZIP CRC and every payload hash pass.
# Recheck source checksums here and hash all staged copies before publishing them.
$manifest = Get-Content -LiteralPath (Join-Path $releaseRoot "$prefix-upload-data.manifest.json") -Raw | ConvertFrom-Json
if ($manifest.build -ne $Build -or -not $manifest.archive_integrity_verified -or -not $manifest.matches_installed_and_full_share) {
    throw 'The data archive does not have a verified matching release manifest.'
}
$sourceHashes = @{}
foreach ($name in $names) {
    $source = Join-Path $releaseRoot $name
    $sourceHashes[$name] = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($name.EndsWith('.zip')) {
        $expected = (Get-Content -LiteralPath ($source + '.sha256') -Raw).Trim().Split(' ')[0]
        if ($sourceHashes[$name] -ne $expected) { throw "Source checksum mismatch: $name" }
    }
}
if ($sourceHashes["$prefix-upload-data.zip"] -ne $manifest.sha256) { throw 'Data manifest checksum mismatch.' }
$staging = Assert-DeliveryPath (Join-Path $deliveryRoot ('.incoming-' + $Build))
New-Item -ItemType Directory -Path $staging -Force | Out-Null
foreach ($name in $names) {
    $copy = Assert-DeliveryPath (Join-Path $staging $name)
    Copy-Item -LiteralPath (Join-Path $releaseRoot $name) -Destination $copy -Force
    if ((Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sourceHashes[$name]) {
        throw "Copied file failed verification: $name"
    }
}
foreach ($name in $names) {
    $copy = Assert-DeliveryPath (Join-Path $staging $name)
    $destination = Assert-DeliveryPath (Join-Path $deliveryRoot $name)
    Move-Item -LiteralPath $copy -Destination $destination -Force
}
foreach ($name in $names) {
    $destination = Assert-DeliveryPath (Join-Path $deliveryRoot $name)
    if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sourceHashes[$name]) {
        throw "Final Dropbox file failed verification: $name"
    }
}
$removed = @()
foreach ($item in Get-ChildItem -LiteralPath $deliveryRoot -File) {
    if ($item.Name -in $names) { continue }
    if ($item.Name -notmatch '^SWGB-DE-.+(\.zip|\.sha256|\.manifest\.json)$') { continue }
    $target = Assert-DeliveryPath $item.FullName
    Remove-Item -LiteralPath $target
    $removed += $item.Name
}
# No recursive deletion: this removes only our now-empty staging directory.
$staging = Assert-DeliveryPath $staging
Remove-Item -LiteralPath $staging
@{ directory = $deliveryRoot; build = $Build; files = $names; verified = $true; removed = $removed } | ConvertTo-Json -Depth 4
