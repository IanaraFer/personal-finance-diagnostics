# Build Your Android App - Simple Steps

## ✅ Easiest Way: Build in Android Studio

Since you already have Android Studio open, this is the simplest method:

### Step 1: Open the Project
1. In Android Studio, go to **File > Open**
2. Navigate to: `C:\Users\35387\Desktop\contabil\mobile\android`
3. Click **OK**

### Step 2: Wait for Gradle Sync
- Android Studio will automatically sync Gradle
- Wait for the "Gradle sync finished" message in the bottom status bar
- This may take a few minutes the first time (downloading dependencies)

### Step 3: Build and Run
1. Click the **green "Run" button** (▶️) in the toolbar
   - Or press **Shift + F10**
   - Or go to **Run > Run 'app'**
2. Select your device:
   - **Physical device**: Connect via USB (enable USB debugging)
   - **Emulator**: Create/start an Android Virtual Device (AVD)
3. Click **OK**

Android Studio will:
- Build the APK automatically
- Install it on your device/emulator
- Launch the app

### That's it! 🎉

Your app will be installed and running on your device.

---

## 📱 Alternative: Get APK File

If you just want the APK file (to share or install manually):

1. In Android Studio, go to **Build > Build Bundle(s) / APK(s) > Build APK(s)**
2. Wait for build to complete
3. Click **locate** in the notification
4. The APK will be at: `app\build\outputs\apk\debug\app-debug.apk`

---

## 🔧 If You Get SDK Errors

If Android Studio shows "SDK location not found":

1. Go to **File > Settings** (or **File > Project Structure**)
2. Navigate to **Appearance & Behavior > System Settings > Android SDK**
3. Note the **"Android SDK Location"** path
4. Run this command in PowerShell (replace with your path):

```powershell
cd C:\Users\35387\Desktop\contabil\mobile\android
.\set-sdk-path.ps1 -SdkPath "YOUR_SDK_PATH_HERE"
```

Then try building again in Android Studio.

---

## 💡 Tips

- **First build takes longer** - Gradle downloads all dependencies
- **Use an emulator** if you don't have a physical device
- **Check Logcat** in Android Studio to see app logs and debug issues


