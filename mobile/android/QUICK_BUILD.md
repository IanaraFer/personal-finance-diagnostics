# Quick Build Instructions

## Option 1: Build in Android Studio (Easiest)

Since you have Android Studio open:

1. **Open the project**: File > Open > Navigate to `mobile\android` folder
2. **Wait for Gradle sync** to complete (bottom status bar)
3. **Click the green "Run" button** (or press Shift+F10)
4. **Select your device/emulator** and click OK

That's it! Android Studio will handle everything automatically.

## Option 2: Set SDK Path and Build from Command Line

### Step 1: Find Your Android SDK Location

In Android Studio:
1. Go to: **File > Settings** (or **File > Project Structure** on Mac)
2. Navigate to: **Appearance & Behavior > System Settings > Android SDK**
3. Copy the **"Android SDK Location"** path (e.g., `C:\Users\YourName\AppData\Local\Android\Sdk`)

### Step 2: Update local.properties

Run this command (replace with your actual SDK path):

```powershell
$sdkPath = "YOUR_SDK_PATH_HERE"
$content = "sdk.dir=$sdkPath"
$content | Out-File -FilePath "local.properties" -Encoding ASCII -NoNewline
```

Or manually edit `local.properties` and add:
```
sdk.dir=YOUR_SDK_PATH_HERE
```

### Step 3: Build the APK

```powershell
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
.\gradlew.bat assembleDebug
```

The APK will be at: `app\build\outputs\apk\debug\app-debug.apk`

## Troubleshooting

- **"SDK location not found"**: Make sure `local.properties` has the correct SDK path
- **"JAVA_HOME not set"**: Android Studio includes Java, but if building from command line, set JAVA_HOME to Android Studio's JDK
- **Gradle sync failed**: Make sure you have internet connection for downloading dependencies


