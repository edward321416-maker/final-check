$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$statePath = Join-Path $projectRoot 'artifacts/runtime/processes.json'
if (-not (Test-Path -LiteralPath $statePath)) { Write-Output 'No launcher state found.'; exit 0 }
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
if ($state.root -ne $projectRoot) { throw 'Launcher state does not match this workspace.' }
foreach ($processId in @($state.frontend, $state.backend)) {
    $entry = Get-CimInstance Win32_Process -Filter ("ProcessId = " + [int]$processId)
    if ($entry) {
        if (-not $entry.CommandLine -or -not $entry.CommandLine.Contains($projectRoot)) { throw "Process $processId does not belong to this launcher; refusing to stop it." }
        Stop-Process -Id $processId
    }
}
Write-Output 'Stopped the recorded FINAL CHECK launcher processes.'
