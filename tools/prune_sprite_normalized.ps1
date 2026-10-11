param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$normalized = Join-Path $workspace 'output/sprite-normalized'
$archive = Join-Path $workspace 'output/sprite-normalized-excluded-20261011'
$targetsCsv = Join-Path $workspace 'tools/data/pmd_aura_targets.csv'
$rootItem = Get-Item -LiteralPath $normalized
$outputItem = Get-Item -LiteralPath (Join-Path $workspace 'output')
if ($rootItem.Parent.FullName -ne $outputItem.FullName -or
    ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'Unexpected normalized output path.'
}
if (Test-Path -LiteralPath $archive) {
    $archiveItem = Get-Item -LiteralPath $archive
    if (-not $archiveItem.PSIsContainer -or
        ($archiveItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Unexpected archive path: $archive"
    }
}
$archiveFull = [IO.Path]::GetFullPath($archive)
if (-not $archiveFull.StartsWith($outputItem.FullName + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Archive is outside the output directory.'
}
$targetIds = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach ($row in (Import-Csv -LiteralPath $targetsCsv)) {
    if ($row.enabled -eq '1') { [void]$targetIds.Add($row.dex_id) }
}
$species = @(Get-ChildItem -LiteralPath $rootItem.FullName -Directory |
    Where-Object { $_.Name -match '^\d{4}$' })
$removeSpecies = @($species | Where-Object { -not $targetIds.Contains($_.Name) })
$removeForms = @(foreach ($s in $species) {
    if ($targetIds.Contains($s.Name)) {
        Get-ChildItem -LiteralPath $s.FullName -Directory |
            Where-Object { $_.Name -match '(?i)Altcolor|Alternate|Cutscene|Shadow|Skytemple|Primal|Baby|Three' }
    }
})
foreach ($s in $removeSpecies) {
    if ($s.Parent.FullName -ne $rootItem.FullName -or
        ($s.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Unsafe species path: $($s.FullName)"
    }
}
foreach ($f in $removeForms) {
    if ($f.Parent.Parent.FullName -ne $rootItem.FullName -or
        ($f.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Unsafe form path: $($f.FullName)"
    }
}
"species_to_move=$($removeSpecies.Count) excluded_forms_to_move=$($removeForms.Count)"
if (-not $Apply) { return }
New-Item -ItemType Directory -Path (Join-Path $archive 'species') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $archive 'forms') -Force | Out-Null
foreach ($f in $removeForms) {
    $parent = Join-Path (Join-Path $archive 'forms') $f.Parent.Name
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $destination = Join-Path $parent $f.Name
    if (-not [IO.Path]::GetFullPath($destination).StartsWith($archiveFull + [IO.Path]::DirectorySeparatorChar,
            [StringComparison]::OrdinalIgnoreCase)) { throw "Unsafe destination: $destination" }
    if (Test-Path -LiteralPath $destination) { throw "Destination already exists: $destination" }
    Move-Item -LiteralPath $f.FullName -Destination $destination
}
foreach ($s in $removeSpecies) {
    $destination = Join-Path (Join-Path $archive 'species') $s.Name
    if (-not [IO.Path]::GetFullPath($destination).StartsWith($archiveFull + [IO.Path]::DirectorySeparatorChar,
            [StringComparison]::OrdinalIgnoreCase)) { throw "Unsafe destination: $destination" }
    if (Test-Path -LiteralPath $destination) { throw "Destination already exists: $destination" }
    Move-Item -LiteralPath $s.FullName -Destination $destination
}
"moved_species=$($removeSpecies.Count) moved_excluded_forms=$($removeForms.Count)"
