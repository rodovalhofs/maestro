[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = "Medium")]
param(
    [Parameter(Mandatory = $true)]
    [string]$TargetRepo,

    [switch]$Apply,

    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Source = (Resolve-Path (Join-Path $PSScriptRoot "..\templates")).Path
$Target = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $TargetRepo).Path)
$GitMarker = Join-Path $Target ".git"

if (-not (Test-Path -LiteralPath $GitMarker)) {
    throw "TargetRepo must be a Git repository or worktree: $Target"
}

$Mappings = @()
$GithubSource = Join-Path $Source ".github"
Get-ChildItem -LiteralPath $GithubSource -File -Recurse | ForEach-Object {
    $Relative = $_.FullName.Substring($GithubSource.Length).TrimStart("\", "/")
    $Mappings += [pscustomobject]@{
        Source = $_.FullName
        Destination = Join-Path (Join-Path $Target ".github") $Relative
    }
}
$Mappings += [pscustomobject]@{
    Source = Join-Path $Source "CONTRIBUTING.md"
    Destination = Join-Path $Target "CONTRIBUTING.md"
}
$Mappings += [pscustomobject]@{
    Source = Join-Path $Source "pull_request_template.md"
    Destination = Join-Path $Target ".github\pull_request_template.md"
}

Write-Host "Template plan for $Target"
foreach ($Mapping in $Mappings) {
    $Destination = [System.IO.Path]::GetFullPath($Mapping.Destination)
    $TargetPrefix = $Target.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    $PathComparison = if ([System.IO.Path]::DirectorySeparatorChar -eq "\") {
        [System.StringComparison]::OrdinalIgnoreCase
    } else {
        [System.StringComparison]::Ordinal
    }
    if (-not $Destination.StartsWith($TargetPrefix, $PathComparison)) {
        throw "Refusing destination outside TargetRepo: $Destination"
    }

    $Exists = Test-Path -LiteralPath $Destination
    if ($Exists -and -not $Force) {
        Write-Warning "Skip existing file (use -Force to replace): $Destination"
        continue
    }
    $Action = if ($Exists) { "replace template file" } else { "create template file" }
    if (-not $Apply) {
        Write-Host "Would $Action`: $Destination"
        continue
    }
    if ($PSCmdlet.ShouldProcess($Destination, $Action)) {
        $Parent = Split-Path -Parent $Destination
        New-Item -ItemType Directory -Path $Parent -Force | Out-Null
        Copy-Item -LiteralPath $Mapping.Source -Destination $Destination -Force
    }
}

if (-not $Apply) {
    Write-Host "Dry run only. Re-run with -Apply; add -Force only to replace mapped files."
} else {
    Write-Host "Complete. Existing unrelated repository files were preserved."
}
