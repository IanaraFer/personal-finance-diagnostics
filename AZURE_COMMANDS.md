# 🚀 Azure Deployment - Copy & Paste Commands

## Step 1: Update Requirements (Already Done ✓)
```
gunicorn added to requirements.txt
flask-cors added to requirements.txt
```

---

## Step 2: Push to GitHub

### IMPORTANT: Replace `YOUR_USERNAME` with your actual GitHub username!

Run these commands in PowerShell (one at a time):

```powershell
cd C:\Users\35387\Desktop\contabil
```

```powershell
git init
```

```powershell
git add .
```

```powershell
git commit -m "Initial commit: Personal Finance Diagnostics Platform"
```

```powershell
git remote add origin https://github.com/YOUR_USERNAME/personal-finance-diagnostics.git
```

```powershell
git branch -M main
```

```powershell
git push -u origin main
```

**After pushing, go to:** https://github.com/YOUR_USERNAME/personal-finance-diagnostics
- Verify all your files are there ✓

---

## Step 3: Azure Portal Setup

### 3a. Create Resource Group (Optional)
```
1. Go to https://portal.azure.com
2. Search "Resource groups"
3. Click "+ Create"
4. Name: finance-diagnostics-rg
5. Region: Europe (Ireland) [or closest to you]
6. Click "Review + Create" → "Create"
```

### 3b. Create App Service
```
1. Go to https://portal.azure.com
2. Click "+ Create a resource"
3. Search "App Service"
4. Click "Create"

Fill in form:
- Subscription: [Your subscription]
- Resource Group: finance-diagnostics-rg
- Name: finance-diagnostics-app (MUST BE UNIQUE)
- Publish: Code
- Runtime stack: Python 3.11
- Operating System: Linux
- Region: Europe (Ireland)
- App Service Plan: Create new
  - Name: finance-diagnostics-plan
  - SKU: Free F1

5. Click "Review + Create"
6. Click "Create"
7. Wait 2-3 minutes for deployment
```

---

## Step 4: Connect GitHub to Azure

### 4a. Open Deployment Center
```
1. App is now created, click on it to open
2. Left sidebar → scroll down → "Deployment"
3. Click "Deployment Center"
4. Click the "GitHub" tab
5. Click "Authorize"
6. Sign in to GitHub (if needed)
7. Click "Authorize" for permissions
```

### 4b. Configure Repository
```
Back on Azure:
- Organization: YOUR_GITHUB_USERNAME
- Repository: personal-finance-diagnostics
- Branch: main
- Click "Save"
```

**Azure now auto-deploys on every push!**

---

## Step 5: Set Environment Variables

### In Azure Portal:
```
1. Your App Service page
2. Left sidebar → "Configuration"
3. Click "+ New application setting"
4. Add these ONE BY ONE:

Setting 1:
- Name: FLASK_ENV
- Value: production
- Click OK

Setting 2:
- Name: FLASK_DEBUG
- Value: False
- Click OK

Setting 3:
- Name: APP_SECRET_KEY
- Value: my-super-secret-key-finance-2025
- Click OK

5. Click "Save" button at the top
6. Wait for app to restart
```

---

## Step 6: Set Startup Command

### In Azure Portal:
```
1. Still in "Configuration" page
2. Click "General settings" tab
3. Find "Startup Command" field
4. Paste this:

gunicorn --bind 0.0.0.0 wsgi:app

5. Click "Save"
```

---

## Step 7: Deploy Your App

### Option A: Automatic (Recommended)
```powershell
# This triggers Azure to deploy automatically:
git add .
git commit -m "Ready for Azure deployment"
git push origin main

# Azure deploys automatically! Check status in Azure portal
```

### Option B: Manual Sync
```
In Azure portal:
1. Deployment Center
2. Click "Sync" button
3. Wait for deployment to complete
```

---

## Step 8: Get Your Live URL

### In Azure Portal:
```
1. App Service overview page
2. Look for "Default domain" or "URL"
3. Should look like: https://finance-diagnostics-app.azurewebsites.net
4. COPY THIS - this is your client's URL!
```

---

## Step 9: Test Your App

```
1. Open in browser: https://finance-diagnostics-app.azurewebsites.net
2. You should see login page
3. Click "Register"
4. Create test account
5. Click "Upload Data"
6. Upload sample files from data/test_samples/
7. View dashboard
8. Test export buttons
```

If something doesn't work:
```
In Azure portal:
1. Left sidebar → "Log stream"
2. Look for error messages
3. Python tracebacks will show here
4. Fix in your code, push to GitHub, Azure redeploys
```

---

## Step 10: Send to Client

Copy this and send:

```
Hi,

Your Financial Diagnostics Platform is ready!

🌍 URL: https://finance-diagnostics-app.azurewebsites.net

📝 First Time:
1. Go to the URL
2. Click "Register"
3. Create account with email & password
4. Login

📤 Upload Your Data:
1. Click "Upload Data"
2. Select your bank transactions (CSV/Excel file)
3. Select your accounts file
4. Click "Upload & Analyze"

📊 Your Dashboard Shows:
- Financial Health Score (0-100)
- 10 Category Analysis
- Monthly Trends
- Risk Alerts
- Recommendations
- Export Reports

Let me know if you need help!

Thanks
```

---

## 🎯 Summary

**Total Steps:** 10 easy steps  
**Total Time:** ~30-40 minutes  
**Result:** Your app is **LIVE** and **WORLDWIDE ACCESSIBLE** 🚀

---

## ⚠️ Troubleshooting

### App shows error/doesn't load
```
Fix: 
1. Azure portal → Log stream
2. Look for Python errors
3. Fix code locally
4. Push to GitHub: git push
5. Azure redeploys automatically
6. Refresh browser
```

### Says "Deployment not found"
```
Fix:
1. Wait 5 minutes for Azure to complete deployment
2. Check "Deployment Center" → Refresh
3. Or manually click "Sync" button
```

### "The resource group is full"
```
Fix:
1. Delete free-tier app
2. Try again with unique name
3. Example: finance-diagnostics-2025
```

---

## ✅ Success Indicators

You'll know it's working when:
- ✓ Azure shows green checkmark
- ✓ Browser shows your login page
- ✓ Can create account
- ✓ Can upload files
- ✓ Can see dashboard
- ✓ Charts display

---

## 📞 Quick Reference

**Your App URLs:**
- Admin/Logs: https://portal.azure.com
- Client Access: https://finance-diagnostics-app.azurewebsites.net
- GitHub: https://github.com/YOUR_USERNAME/personal-finance-diagnostics

**Key Commands:**
```powershell
# Update and redeploy
git add .
git commit -m "Update description"
git push origin main

# Check status
git status
git log --oneline -5
```

---

**You've got this! 🚀 Deploy now and share with your client!**
