# Script to set Android SDK path in local.properties
param(
    [Parameter(Mandatory=$true)]
    [string]$SdkPath
)

$sdkPath = $SdkPath.Trim()
if (-not (Test-Path $sdkPath)) {
    Write-Host "Error: SDK path does not exist: $sdkPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "$sdkPath\platform-tools\adb.exe")) {
    Write-Host "Warning: This doesn't look like an Android SDK directory (adb.exe not found)" -ForegroundColor Yellow
    $confirm = Read-Host "Continue anyway? (y/n)"
    if ($confirm -ne 'y') {
        exit 1
    }
}

# Normalize path (use forward slashes for Gradle)
$normalizedPath = $sdkPath -replace '\\', '/'

$content = "sdk.dir=$normalizedPath"
$content | Out-File -FilePath "local.properties" -Encoding ASCII -NoNewline

Write-Host "`n✓ Updated local.properties with SDK path: $normalizedPath" -ForegroundColor Green
Write-Host "`nYou can now build the app with:" -ForegroundColor Yellow
Write-Host "  .\gradlew.bat assembleDebug" -ForegroundColor Cyan


