param([switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$mainStage = Join-Path $projectRoot 'dist-latest'
$installerStage = Join-Path $projectRoot 'installer\dist-latest'
$releaseDir = Join-Path $projectRoot 'release'

if (-not $SkipBuild) {
    Push-Location (Join-Path $projectRoot 'web')
    try { npm run build; if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' } }
    finally { Pop-Location }
    Push-Location $projectRoot
    try { & $python -m PyInstaller --noconfirm --distpath $mainStage wordmaster.spec; if ($LASTEXITCODE -ne 0) { throw 'Main build failed' } }
    finally { Pop-Location }
    $env:WORDMASTER_RELEASE_DIST = $mainStage
    Push-Location (Join-Path $projectRoot 'installer')
    try { & $python -m PyInstaller --noconfirm --distpath $installerStage installer.spec; if ($LASTEXITCODE -ne 0) { throw 'Installer build failed' } }
    finally { Pop-Location; Remove-Item Env:WORDMASTER_RELEASE_DIST -ErrorAction SilentlyContinue }
}

$mainExe = Join-Path $mainStage 'WordMaster.exe'
$setupExe = Join-Path $installerStage 'WordMaster_Setup.exe'
if (Test-Path -LiteralPath $mainExe) {
    $metadata = Get-Content (Join-Path $mainStage 'WordMaster.build.json') -Raw | ConvertFrom-Json
    if ((Get-FileHash -LiteralPath $mainExe -Algorithm SHA256).Hash -ne $metadata.exe_sha256) { throw 'Main EXE checksum mismatch' }
    if (-not (Test-Path -LiteralPath $setupExe)) { throw 'Installer missing' }
    New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
    Copy-Item -LiteralPath $mainExe -Destination (Join-Path $releaseDir 'WordMaster.exe') -Force
    Copy-Item -LiteralPath $setupExe -Destination (Join-Path $releaseDir 'WordMaster_Setup.exe') -Force
    if ((Get-FileHash -LiteralPath (Join-Path $releaseDir 'WordMaster.exe') -Algorithm SHA256).Hash -ne $metadata.exe_sha256) { throw 'Published EXE checksum mismatch' }
} elseif (-not $SkipBuild) {
    throw 'Main EXE missing after build'
}
if (-not (Test-Path -LiteralPath (Join-Path $releaseDir 'WordMaster.exe')) -or
    -not (Test-Path -LiteralPath (Join-Path $releaseDir 'WordMaster_Setup.exe'))) {
    throw 'Published release is incomplete'
}

$lockedPackages = @()
function Remove-OldPackage([string]$target) {
    if (-not (Test-Path -LiteralPath $target)) { return }
    $resolved = (Resolve-Path -LiteralPath $target).Path
    if (-not $resolved.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe package path: $resolved"
    }
    try { Remove-Item -LiteralPath $resolved -Recurse -Force }
    catch {
        $script:lockedPackages += $resolved
        Write-Warning "Package is in use; close WordMaster and rerun: $resolved"
    }
}

Get-ChildItem -LiteralPath $projectRoot -Directory | Where-Object { $_.Name -like 'dist-*' -or $_.Name -eq 'dist' } | ForEach-Object { Remove-OldPackage $_.FullName }
Get-ChildItem -LiteralPath (Join-Path $projectRoot 'installer') -Directory | Where-Object { $_.Name -like 'dist-*' -or $_.Name -eq 'bundle' } | ForEach-Object { Remove-OldPackage $_.FullName }
Remove-OldPackage (Join-Path $projectRoot 'installer\dist\WordMaster_Setup.exe')
if ($lockedPackages.Count -gt 0) { throw "Old packages still in use: $($lockedPackages -join ', ')" }
Write-Output "Published latest release: $releaseDir"
