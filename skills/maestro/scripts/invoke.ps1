# Maestro script wrapper — PowerShell-safe paths (use $env:USERPROFILE, not %USERPROFILE%)
param(
    [Parameter(Position = 0, Mandatory)]
    [ValidateSet("search", "route", "manifest")]
    [string]$Command,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Rest
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$map = @{
    search   = "search_skills.py"
    route    = "route_tasks.py"
    manifest = "build_manifest.py"
}

$target = Join-Path $ScriptDir $map[$Command]

if (Get-Command py -ErrorAction SilentlyContinue) {
    $py = @("py", "-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $py = @("python")
} else {
    Write-Error "Python not found. Install Python 3.12+ or use: npx maestro-skills search"
    exit 1
}

& @py @($target) @Rest
exit $LASTEXITCODE
