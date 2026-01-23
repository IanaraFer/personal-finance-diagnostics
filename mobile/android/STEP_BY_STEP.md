# Step-by-Step: Build Your Android App

## You're Almost There! Follow These Steps:

### Step 1: Make Sure Project is Open ✅
- You should see the project files in Android Studio
- Look at the left sidebar (Project view) - you should see folders like `app`, `gradle`, etc.

### Step 2: Wait for Gradle Sync ⏳
- Look at the bottom of Android Studio
- You should see "Gradle sync" or "Indexing" in the status bar
- **Wait until it says "Gradle sync finished"** (this may take 2-5 minutes the first time)
- If you see errors, scroll down to see what they are

### Step 3: Set Up a Device/Emulator 📱

**Option A: Use Your Physical Phone**
1. Connect your Android phone to computer via USB
2. On your phone, enable **Developer Options** and **USB Debugging**
   - Go to Settings > About Phone > Tap "Build Number" 7 times
   - Go back to Settings > Developer Options > Enable "USB Debugging"
3. Your phone should appear in Android Studio's device list

**Option B: Use an Emulator (Virtual Phone)**
1. In Android Studio, click the device dropdown (top toolbar, shows "No devices")
2. Click "Device Manager" or "AVD Manager"
3. Click "Create Device" or the "+" button
4. Select a phone (e.g., "Pixel 5")
5. Click "Next" > Select a system image (e.g., "API 34") > Click "Download" if needed
6. Click "Finish"
7. Click the ▶️ play button next to your emulator to start it

### Step 4: Build and Run! 🚀

1. **Look at the top toolbar** - find the green **▶️ Run button** (or press **Shift + F10**)
2. **Click the Run button**
3. **Select your device** from the list (your phone or emulator)
4. **Click OK**

### Step 5: Watch It Build! 👀
- Android Studio will show "Building..." in the bottom status bar
- This takes 1-3 minutes the first time
- You'll see progress in the "Build" tab at the bottom

### Step 6: App Launches! 🎉
- The app will automatically install on your device
- It will launch automatically
- You should see "Finance Diagnostics" app running!

---

## What You Should See:

✅ **In Android Studio:**
- Bottom status bar shows "Gradle sync finished"
- Top toolbar has a green Run button
- Device dropdown shows your phone/emulator

✅ **On Your Device:**
- App installs automatically
- App opens showing "Finance Diagnostics" with a purple gradient background
- You can upload CSV/Excel files to analyze finances

---

## Common Issues & Fixes:

### ❌ "Gradle sync failed"
- **Fix**: Check internet connection, wait a bit, then click "Sync Project with Gradle Files" button (elephant icon)

### ❌ "No devices found"
- **Fix**: 
  - For phone: Enable USB debugging on your phone
  - For emulator: Create and start an emulator first

### ❌ "SDK location not found"
- **Fix**: 
  1. File > Settings > Appearance & Behavior > System Settings > Android SDK
  2. Note the SDK location path
  3. Create/edit `local.properties` file in `android` folder
  4. Add: `sdk.dir=YOUR_SDK_PATH`

### ❌ Build takes forever
- **Normal**: First build downloads all dependencies (2-5 minutes)
- **If stuck**: Check internet connection, close and reopen Android Studio

---

## Need Help?

If you see any error messages, copy them and I can help you fix them!


