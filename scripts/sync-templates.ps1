param(
    [Parameter(Mandatory = $true)]
    [string]$TargetRepo
)

$ErrorActionPreference = "Stop"
$Source = Join-Path $PSScriptRoot "..\templates"
$Target = Resolve-Path $TargetRepo

Write-Host "Sincronizando templates de $Source para $Target"

$githubSrc = Join-Path $Source ".github"
$githubDst = Join-Path $Target ".github"
if (Test-Path $githubDst) {
    Remove-Item $githubDst -Recurse -Force
}
Copy-Item $githubSrc $githubDst -Recurse -Force

Copy-Item (Join-Path $Source "CONTRIBUTING.md") (Join-Path $Target "CONTRIBUTING.md") -Force
Copy-Item (Join-Path $Source "pull_request_template.md") (Join-Path $Target ".github\pull_request_template.md") -Force

Write-Host "Concluido. Revise workflows e adapte comandos de test/build ao seu stack."
