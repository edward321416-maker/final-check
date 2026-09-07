param(
    [string]$PublicUrl = 'https://uncoy-joelle-macrodont.ngrok-free.dev',
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $projectRoot 'artifacts/runtime'
$manifestPath = Join-Path $runtimeDir 'public-processes.json'

if (Test-Path -LiteralPath $manifestPath) {
    throw 'A public runtime manifest already exists. Run scripts/stop-public-judge.ps1 first.'
}
foreach ($port in @(3100, 8100)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        throw "Port $port is occupied. Stop the known process before launching."
    }
}

$pythonPath = Join-Path $projectRoot 'backend/.venv/Scripts/python.exe'
$nextPath = Join-Path $projectRoot 'frontend/node_modules/next/dist/bin/next'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run backend setup first.' }
if (-not (Test-Path -LiteralPath $nextPath)) { throw 'Run frontend npm install first.' }
$nodePath = (Get-Command node -ErrorAction Stop).Source
$ngrokPath = (Get-Command ngrok -ErrorAction Stop).Source
$null = Get-Command codex -ErrorAction Stop
$null = Get-Command ffprobe -ErrorAction Stop

$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
if (-not (Test-Path -LiteralPath (Join-Path $codexHome 'auth.json'))) {
    throw 'Existing ChatGPT-authenticated Codex CLI credentials are unavailable.'
}

$env:FINAL_CHECK_ENV = 'production'
$env:FINAL_CHECK_AI_PROVIDER = 'codex'
$env:FINAL_CHECK_AI_MODEL = 'gpt-5.6-sol'
$env:FINAL_CHECK_AI_REASONING = 'high'
$env:FINAL_CHECK_AI_TIMEOUT_SECONDS = '600'
$env:FINAL_CHECK_DATA_DIR = Join-Path $projectRoot '.final-check/runtime'
$env:FINAL_CHECK_PUBLIC_GUARD = '1'
$env:FINAL_CHECK_AI_MAX_CONCURRENT_WORKFLOWS = '2'
$env:FINAL_CHECK_AI_MAX_OPERATIONS_PER_HOUR = '40'
$env:FINAL_CHECK_AI_MAX_OPERATIONS_PER_SESSION_HOUR = '6'
$env:FINAL_CHECK_MAX_FILE_BYTES = '16777216'
$env:FINAL_CHECK_MAX_PACKAGE_BYTES = '25165824'
$env:FINAL_CHECK_MAX_FILES = '8'
$env:API_ORIGIN = 'http://127.0.0.1:8100'
$env:NEXT_TELEMETRY_DISABLED = '1'

if (-not $SkipBuild) {
    Push-Location (Join-Path $projectRoot 'frontend')
    try {
        & npm run build
        if ($LASTEXITCODE -ne 0) { throw "Frontend production build failed with exit code $LASTEXITCODE." }
    } finally {
        Pop-Location
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend/.next/BUILD_ID'))) {
    throw 'The frontend production build is unavailable.'
}

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
$started = [ordered]@{}
try {
    $backendDir = Join-Path $projectRoot 'backend'
    $backend = Start-Process -FilePath $pythonPath -ArgumentList @(
        '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8100', '--workers', '1'
    ) -WorkingDirectory $backendDir -WindowStyle Hidden -PassThru `
      -RedirectStandardOutput (Join-Path $runtimeDir 'backend.out.log') `
      -RedirectStandardError (Join-Path $runtimeDir 'backend.err.log')
    $started.backend = $backend

    $backendReady = $false
    foreach ($attempt in 1..60) {
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8100/api/health' -TimeoutSec 3
            if ($health.status -eq 'ok') { $backendReady = $true; break }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    if (-not $backendReady) { throw 'Backend production health did not become ready.' }

    $frontendDir = Join-Path $projectRoot 'frontend'
    $frontend = Start-Process -FilePath $nodePath -ArgumentList @(
        ('"' + $nextPath + '"'), 'start', '--hostname', '127.0.0.1', '--port', '3100'
    ) -WorkingDirectory $frontendDir -WindowStyle Hidden -PassThru `
      -RedirectStandardOutput (Join-Path $runtimeDir 'frontend.out.log') `
      -RedirectStandardError (Join-Path $runtimeDir 'frontend.err.log')
    $started.frontend = $frontend

    $frontendReady = $false
    foreach ($attempt in 1..60) {
        try {
            $response = Invoke-WebRequest -Uri 'http://127.0.0.1:3100/' -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200) { $frontendReady = $true; break }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    if (-not $frontendReady) { throw 'Frontend production server did not become ready.' }

    $ngrok = Start-Process -FilePath $ngrokPath -ArgumentList @(
        'http', '3100', "--url=$PublicUrl", '--log=stdout', '--log-format=json', '--log-level=info'
    ) -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru `
      -RedirectStandardOutput (Join-Path $runtimeDir 'ngrok.out.log') `
      -RedirectStandardError (Join-Path $runtimeDir 'ngrok.err.log')
    $started.ngrok = $ngrok

    $publicReady = $false
    foreach ($attempt in 1..90) {
        try {
            $publicHealth = Invoke-RestMethod -Uri "$PublicUrl/api/health" `
                -Headers @{ 'ngrok-skip-browser-warning' = '1' } -TimeoutSec 5
            if ($publicHealth.status -eq 'ok') { $publicReady = $true; break }
        } catch {}
        Start-Sleep -Milliseconds 750
    }
    if (-not $publicReady) { throw 'The ngrok public health endpoint did not become ready.' }

    $manifest = [ordered]@{ public_url = $PublicUrl; started_at = (Get-Date).ToUniversalTime().ToString('o') }
    foreach ($name in @('backend', 'frontend', 'ngrok')) {
        $process = $started[$name]
        $manifest[$name] = [ordered]@{
            id = $process.Id
            name = $process.ProcessName
            start_time_utc_ticks = $process.StartTime.ToUniversalTime().Ticks
        }
    }
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding utf8
    $publicHealth | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runtimeDir 'public-health.json') -Encoding utf8
    Write-Output "FINAL CHECK public judge runtime is ready: $PublicUrl"
} catch {
    foreach ($process in $started.Values) {
        if ($process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -ErrorAction SilentlyContinue
        }
    }
    throw
}
