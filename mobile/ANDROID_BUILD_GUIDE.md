# Android App Build Guide

Your Android app is now ready to build! Follow these steps to create and run your app.

## Prerequisites

1. **Android Studio** - Download and install from [developer.android.com/studio](https://developer.android.com/studio)
2. **Java Development Kit (JDK)** - Android Studio includes JDK, or install JDK 17+ separately
3. **Android SDK** - Install via Android Studio SDK Manager

## Quick Start

### Option 1: Open in Android Studio (Recommended)

1. Open Android Studio
2. Click "Open an Existing Project"
3. Navigate to: `mobile/android`
4. Wait for Gradle sync to complete
5. Click the green "Run" button or press `Shift+F10`

### Option 2: Command Line Build

```powershell
cd mobile\android
.\gradlew assembleDebug
```

The APK will be generated at: `mobile\android\app\build\outputs\apk\debug\app-debug.apk`

## Running on Device/Emulator

### Using Android Studio:
1. Connect your Android device via USB (enable USB debugging)
2. Or create/start an Android Virtual Device (AVD) from Android Studio
3. Click the "Run" button in Android Studio
4. Select your device/emulator from the list

### Using Command Line:
```powershell
cd mobile\android
.\gradlew installDebug
```

## Building Release APK

For a release build (signed APK):

1. **Generate a keystore** (first time only):
```powershell
keytool -genkey -v -keystore my-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias my-key-alias
```

2. **Create `mobile/android/key.properties`**:
```properties
storePassword=your-store-password
keyPassword=your-key-password
keyAlias=my-key-alias
storeFile=../my-release-key.jks
```

3. **Update `mobile/android/app/build.gradle`** to use the keystore (see Android documentation)

4. **Build release APK**:
```powershell
cd mobile\android
.\gradlew assembleRelease
```

## App Configuration

### Set Default Platform URL

Edit `mobile/www/app-config.json` to set your default full platform URL:

```json
{
  "defaultFullPlatformUrl": "https://your-app.onrender.com"
}
```

Then run:
```powershell
cd mobile
npm run prepare:web
npx cap sync
```

### App Details

- **Package Name**: `com.financediag.app`
- **App Name**: Finance Diagnostics
- **Min SDK**: 22 (Android 5.1)
- **Target SDK**: 34 (Android 14)

## Updating the App

When you make changes to the web content:

1. Update `demo.html` in the root directory
2. Run:
```powershell
cd mobile
npm run prepare:web
npx cap sync
```
3. Rebuild in Android Studio or run `.\gradlew assembleDebug`

## Troubleshooting

### Gradle Sync Failed
- Ensure you have internet connection (Gradle downloads dependencies)
- Check that Android Studio has the latest Android SDK installed
- Try: `File > Invalidate Caches / Restart` in Android Studio

### Build Errors
- Make sure Java JDK 17+ is installed and configured
- Check that `ANDROID_HOME` environment variable is set (if using command line)
- Ensure all dependencies are installed: `cd mobile && npm install`

### App Crashes on Launch
- Check Android Studio Logcat for error messages
- Ensure web assets are synced: `npx cap sync`
- Verify `mobile/www/index.html` exists

### Capacitor Plugin Issues
- Run `npx cap sync` to update native plugins
- Check that `@capacitor/browser` is installed: `npm list @capacitor/browser`

## Next Steps

1. **Test the app** on a physical device or emulator
2. **Configure your backend URL** in `app-config.json`
3. **Customize app icon** in `mobile/android/app/src/main/res/mipmap-*/`
4. **Add app signing** for Play Store distribution
5. **Test offline functionality** - the app works offline for file analysis

## Distribution

### Google Play Store
1. Build a signed release APK or AAB
2. Create a Google Play Console account
3. Follow Google's publishing guidelines
4. Upload your app bundle

### Direct Distribution
- Share the APK file directly
- Users need to enable "Install from Unknown Sources" on their device

## Support

For issues or questions:
- Check Capacitor documentation: [capacitorjs.com](https://capacitorjs.com)
- Android development guide: [developer.android.com](https://developer.android.com)


