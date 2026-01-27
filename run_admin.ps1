Param(
    [string]$Email = "information@analyticacoreai.ie",
    [string]$Password = "Maiaemolly22",
    [int]$Port = 5003,
    [switch]$OpenBrowser = $true
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

$venvPath = Join-Path $root ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$venvPip = Join-Path $venvPath "Scripts\pip.exe"
$waitressExe = Join-Path $venvPath "Scripts\waitress-serve.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment at $venvPath..."
    python -m venv $venvPath
}

Write-Host "Ensuring backend dependencies..."
& $venvPip install -r (Join-Path $root "backend-requirements.txt")

$env:ADMIN_EMAIL = $Email
$env:ADMIN_PASSWORD = $Password

Write-Host "Starting server on http://127.0.0.1:$Port as admin $Email"
# Start waitress and capture logs to help diagnose startup issues
$logOutPath = Join-Path $root "server.out.log"
$logErrPath = Join-Path $root "server.err.log"
if (Test-Path $logOutPath) { Remove-Item $logOutPath -Force }
if (Test-Path $logErrPath) { Remove-Item $logErrPath -Force }
$proc = Start-Process -FilePath $waitressExe -ArgumentList "--host=127.0.0.1 --port=$Port app:app" -WorkingDirectory $root -NoNewWindow -PassThru -RedirectStandardOutput $logOutPath -RedirectStandardError $logErrPath

# Wait for health endpoint to respond
$healthUrl = "http://127.0.0.1:$Port/health"
Write-Host "Waiting for server health at $healthUrl ..."
$maxAttempts = 20
for ($i = 1; $i -le $maxAttempts; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 3
        if ($resp.StatusCode -eq 200) {
            Write-Host "Server is healthy (HTTP 200)."
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

# If not healthy yet, check port and show recent logs
try {
    $resp = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 3
} catch {
    Write-Host "Health check failed after $maxAttempts attempts. Checking port and logs..." -ForegroundColor Yellow
    $net = Test-NetConnection -ComputerName 127.0.0.1 -Port $Port
    Write-Host ("Port {0} Listening: {1}" -f $Port, $net.TcpTestSucceeded)
    if (Test-Path $logOutPath) {
        Write-Host "--- server.out.log (last 50 lines) ---" -ForegroundColor Cyan
        Get-Content $logOutPath -Tail 50 | ForEach-Object { Write-Host $_ }
    }
    if (Test-Path $logErrPath) {
        Write-Host "--- server.err.log (last 50 lines) ---" -ForegroundColor Cyan
        Get-Content $logErrPath -Tail 50 | ForEach-Object { Write-Host $_ }
    }
    Write-Host "--- end logs ---" -ForegroundColor Cyan
}

if ($OpenBrowser) {
    Start-Process "http://127.0.0.1:$Port/"
    Start-Process "http://127.0.0.1:$Port/admin"
    Write-Host "Opened http://127.0.0.1:$Port/ and /admin in your default browser."
} else {
    Write-Host "Server should be up at http://127.0.0.1:$Port/"
}
