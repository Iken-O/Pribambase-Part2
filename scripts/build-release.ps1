[CmdletBinding()]
param(
    [string]$BlenderPath,
    [string]$OutputDir = "dist/release",
    [switch]$Clean,
    [switch]$SkipBlender,
    [switch]$SkipAseprite
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BlenderSourceDir = Join-Path $RepoRoot "blender/pribambase"
$AsepriteSourceDir = Join-Path $RepoRoot "aseprite-extension"
$OutputDir = if ([System.IO.Path]::IsPathRooted($OutputDir)) {
    $OutputDir
} else {
    Join-Path $RepoRoot $OutputDir
}

function Get-ManifestValue {
    param(
        [string]$Path,
        [string]$Key
    )

    $content = Get-Content -Path $Path -Raw
    $match = [regex]::Match($content, "(?m)^$([regex]::Escape($Key))\s*=\s*""([^""]+)""")
    if (-not $match.Success) {
        throw "Could not find '$Key' in $Path"
    }

    return $match.Groups[1].Value
}

function Resolve-BlenderExecutable {
    param([string]$PreferredPath)

    if ($PreferredPath) {
        $resolved = Resolve-Path -LiteralPath $PreferredPath -ErrorAction Stop
        return $resolved.Path
    }

    $command = Get-Command blender -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $stableRoot = "C:\blender\app\stable"
    if (Test-Path -LiteralPath $stableRoot) {
        $candidates = foreach ($dir in Get-ChildItem -LiteralPath $stableRoot -Directory) {
            $exe = Join-Path $dir.FullName "blender.exe"
            if (-not (Test-Path -LiteralPath $exe)) {
                continue
            }

            $versionMatch = [regex]::Match($dir.Name, "^blender-(\d+\.\d+\.\d+)")
            if (-not $versionMatch.Success) {
                continue
            }

            [pscustomobject]@{
                Path = $exe
                Version = [version]$versionMatch.Groups[1].Value
            }
        }

        $selected = $candidates | Sort-Object Version -Descending | Select-Object -First 1
        if ($selected) {
            return $selected.Path
        }
    }

    throw "Could not resolve blender.exe. Pass -BlenderPath explicitly."
}

function New-AsepriteExtensionArchive {
    param(
        [string]$SourceDir,
        [string]$DestinationPath
    )

    $sourceRoot = (Resolve-Path -LiteralPath $SourceDir).Path.TrimEnd([char[]]@([char]'\', [char]'/'))
    $destinationDir = Split-Path -Parent $DestinationPath
    if (-not (Test-Path -LiteralPath $destinationDir)) {
        New-Item -ItemType Directory -Path $destinationDir | Out-Null
    }

    if (Test-Path -LiteralPath $DestinationPath) {
        Remove-Item -LiteralPath $DestinationPath -Force
    }

    $files = Get-ChildItem -LiteralPath $SourceDir -Recurse -File |
        Where-Object {
            $_.FullName -notmatch '[\\/]__pycache__[\\/]' -and
            $_.Name -notmatch '\.(zip|aseprite-extension)$'
        } |
        Sort-Object FullName

    $stream = [System.IO.File]::Open($DestinationPath, [System.IO.FileMode]::CreateNew)
    try {
        $archive = New-Object System.IO.Compression.ZipArchive($stream, [System.IO.Compression.ZipArchiveMode]::Create, $false)
        try {
            foreach ($file in $files) {
                $relativePath = $file.FullName.Substring($sourceRoot.Length).TrimStart([char[]]@([char]'\', [char]'/')).Replace("\", "/")
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                    $archive,
                    $file.FullName,
                    $relativePath,
                    [System.IO.Compression.CompressionLevel]::Optimal
                ) | Out-Null
            }
        }
        finally {
            $archive.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

if (-not (Test-Path -LiteralPath $BlenderSourceDir)) {
    throw "Blender source directory not found: $BlenderSourceDir"
}

if (-not (Test-Path -LiteralPath $AsepriteSourceDir)) {
    throw "Aseprite source directory not found: $AsepriteSourceDir"
}

if ($Clean -and (Test-Path -LiteralPath $OutputDir)) {
    Remove-Item -LiteralPath $OutputDir -Recurse -Force
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$blenderManifestPath = Join-Path $BlenderSourceDir "blender_manifest.toml"
$blenderId = Get-ManifestValue -Path $blenderManifestPath -Key "id"
$blenderVersion = Get-ManifestValue -Path $blenderManifestPath -Key "version"

$asepritePackagePath = Join-Path $AsepriteSourceDir "package.json"
$asepritePackage = Get-Content -Path $asepritePackagePath -Raw | ConvertFrom-Json
$asepriteVersion = [string]$asepritePackage.version
$asepriteName = [string]$asepritePackage.name

if ($blenderVersion -ne $asepriteVersion) {
    Write-Warning "Version mismatch: Blender=$blenderVersion, Aseprite=$asepriteVersion"
}

$artifacts = New-Object System.Collections.Generic.List[string]

if (-not $SkipBlender) {
    $resolvedBlender = Resolve-BlenderExecutable -PreferredPath $BlenderPath
    Write-Host "Building Blender extension with: $resolvedBlender"

    & $resolvedBlender --factory-startup --command extension build `
        --source-dir $BlenderSourceDir `
        --output-dir $OutputDir `
        --split-platforms

    if ($LASTEXITCODE -ne 0) {
        throw "Blender extension build failed with exit code $LASTEXITCODE"
    }

    $blenderArtifacts = Get-ChildItem -LiteralPath $OutputDir -File |
        Where-Object { $_.Name -like "$blenderId-$blenderVersion*.zip" } |
        Sort-Object Name

    if (-not $blenderArtifacts) {
        throw "Blender build completed, but no artifact matching $blenderId-$blenderVersion*.zip was found in $OutputDir"
    }

    foreach ($artifact in $blenderArtifacts) {
        $artifacts.Add($artifact.FullName) | Out-Null
    }
}

if (-not $SkipAseprite) {
    $asepriteArtifactName = "{0}_aseprite-{1}.aseprite-extension" -f $asepriteName, $asepriteVersion
    $asepriteArtifactPath = Join-Path $OutputDir $asepriteArtifactName

    Write-Host "Packaging Aseprite extension: $asepriteArtifactPath"
    New-AsepriteExtensionArchive -SourceDir $AsepriteSourceDir -DestinationPath $asepriteArtifactPath
    $artifacts.Add($asepriteArtifactPath) | Out-Null
}

Write-Host ""
Write-Host "Artifacts:"
foreach ($artifact in $artifacts) {
    Write-Host " - $artifact"
}
