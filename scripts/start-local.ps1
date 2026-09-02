$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $projectRoot 'artifacts/runtime'
foreach ($port in @(3100, 8100)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        throw "Port $port is occupied. Stop the known demo process before launching."
    }
}
$pythonPath = Join-Path $projectRoot 'backend/.venv/Scripts/python.exe'
$nextPath = Join-Path $projectRoot 'frontend/node_modules/next/dist/bin/next'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run backend setup first.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend/.next/BUILD_ID'))) { throw 'Run npm run build first.' }
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
$backendDir = Join-Path $projectRoot 'backend'
$frontendDir = Join-Path $projectRoot 'frontend'
$backendProcess = Start-Process -FilePath $pythonPath -ArgumentList @('-m','uvicorn','app.main:app','--app-dir', ('"' + $backendDir + '"'),'--host','127.0.0.1','--port','8100') -WorkingDirectory $backendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'backend.out.log') -RedirectStandardError (Join-Path $runtimeDir 'backend.err.log')
try {
    $nodePath = (Get-Command node).Source
    $frontendProcess = Start-Process -FilePath $nodePath -ArgumentList @(('"' + $nextPath + '"'),'start','--hostname','127.0.0.1','--port','3100') -WorkingDirectory $frontendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'frontend.out.log') -RedirectStandardError (Join-Path $runtimeDir 'frontend.err.log')
} catch {
    Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
    throw
}
@{ backend = $backendProcess.Id; frontend = $frontendProcess.Id; root = $projectRoot } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeDir 'processes.json') -Encoding utf8
Write-Output 'Started FINAL CHECK: http://127.0.0.1:3100 (API: http://127.0.0.1:8100/docs)'
