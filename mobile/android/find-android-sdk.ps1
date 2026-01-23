# Script to find Android SDK location
Write-Host "Searching for Android SDK..." -ForegroundColor Yellow

$sdkPaths = @(
    "$env:LOCALAPPDATA\Android\Sdk",
    "$env:USERPROFILE\AppData\Local\Android\Sdk",
    "$env:ANDROID_HOME",
    "C:\Android\Sdk"
)

$found = $null
foreach ($path in $sdkPaths) {
    if ($path -and (Test-Path $path)) {
        if (Test-Path "$path\platform-tools\adb.exe") {
            $found = $path
            Write-Host "Found Android SDK at: $found" -ForegroundColor Green
            break
        }
    }
}

if (-not $found) {
    Write-Host "`nAndroid SDK not found in common locations." -ForegroundColor Red
    Write-Host "`nTo find your SDK location in Android Studio:" -ForegroundColor Yellow
    Write-Host "1. Open Android Studio"
    Write-Host "2. Go to: File > Settings > Appearance & Behavior > System Settings > Android SDK"
    Write-Host "3. Copy the 'Android SDK Location' path"
    Write-Host "4. Update local.properties with: sdk.dir=<your-path>"
    Write-Host "`nOr set environment variable: `$env:ANDROID_HOME = '<your-sdk-path>'"
} else {
    $content = "sdk.dir=$found"
    $content | Out-File -FilePath "local.properties" -Encoding ASCII -NoNewline
    Write-Host "`nUpdated local.properties with SDK path!" -ForegroundColor Green
}

return $found


