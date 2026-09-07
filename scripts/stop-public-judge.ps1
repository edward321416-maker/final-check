$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $projectRoot 'artifacts/runtime'
$manifestPath = Join-Path $runtimeDir 'public-processes.json'

if (-not (Test-Path -LiteralPath $manifestPath)) {
    Write-Output 'No public judge runtime manifest exists.'
    exit 0
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
foreach ($name in @('ngrok', 'frontend', 'backend')) {
    $record = $manifest.$name
    if (-not $record) { continue }
    $process = Get-Process -Id $record.id -ErrorAction SilentlyContinue
    if (-not $process) { continue }
    $sameName = $process.ProcessName -eq $record.name
    $sameStart = $process.StartTime.ToUniversalTime().Ticks -eq [long]$record.start_time_utc_ticks
    if (-not ($sameName -and $sameStart)) {
        throw "Refusing to stop PID $($record.id): the process no longer matches the $name manifest entry."
    }
    Stop-Process -Id $process.Id
}

$resolvedRuntime = (Resolve-Path -LiteralPath $runtimeDir).Path
$resolvedManifest = (Resolve-Path -LiteralPath $manifestPath).Path
if (-not $resolvedManifest.StartsWith($resolvedRuntime, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Refusing to remove a manifest outside the runtime directory.'
}
Remove-Item -LiteralPath $resolvedManifest
Write-Output 'Stopped the FINAL CHECK public judge runtime.'
