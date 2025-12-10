# 🚀 Azure Deployment - Step by Step Guide

## Prerequisites
- Azure account (free tier available at https://azure.microsoft.com/free)
- GitHub account (https://github.com)
- Your code ready to push

---

## ✅ STEP 1: Push Your Code to GitHub

### 1a. Create GitHub Repository
1. Go to https://github.com/new
2. Name: `personal-finance-diagnostics`
3. Description: `Personal Finance Diagnostics Platform`
4. Keep it **Public** (easier for Azure to access)
5. Click **"Create repository"**

### 1b. Push Your Code
Run these commands in PowerShell (in your project directory):

```powershell
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Personal Finance Diagnostics Platform"

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/personal-finance-diagnostics.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

**Verify:** Go to your GitHub repo URL - you should see all your files there.

---

## ✅ STEP 2: Create Azure App Service

### 2a. Log into Azure Portal
1. Go to https://portal.azure.com
2. Sign in with your Microsoft account (create free account if needed)

### 2b. Create Resource Group (Optional but Recommended)
1. Click **"Resource groups"** in the sidebar
2. Click **"+ Create"**
3. Fill in:
   - **Subscription:** Select your subscription
   - **Resource group name:** `finance-diagnostics-rg`
   - **Region:** Choose closest to you (e.g., `Europe (Ireland)`)
4. Click **"Review + Create"** → **"Create"**

### 2c. Create App Service
1. Click **"Create a resource"** (top left)
2. Search for: `App Service`
3. Click **"Create"**
4. Fill in the form:

```
Subscription: [Your Subscription]
Resource Group: finance-diagnostics-rg (the one you created)
Name: finance-diagnostics-app (must be unique globally)
Publish: Code
Runtime stack: Python 3.11
Operating System: Linux
Region: Europe (Ireland) [or closest to you]
App Service Plan: Create new
  - Name: finance-diagnostics-plan
  - Sku: Free F1 (free tier, perfect for testing)
```

5. Click **"Review + Create"**
6. Review the settings
7. Click **"Create"**
8. **Wait 2-3 minutes** for deployment to complete

---

## ✅ STEP 3: Connect GitHub for Auto-Deploy

### 3a. Go to Deployment Center
1. Once app is created, click on it to open
2. In the left sidebar, scroll down to **"Deployment"** section
3. Click **"Deployment Center"**

### 3b. Configure GitHub
1. Click the **"GitHub"** tab
2. Click **"Authorize"**
3. Sign in to GitHub (if prompted)
4. GitHub will ask permissions - **Click "Authorize"**
5. Back on Azure, fill in:
   - **Organization:** Your GitHub username
   - **Repository:** `personal-finance-diagnostics`
   - **Branch:** `main`
6. Click **"Save"**

**Azure now watches your GitHub repository!**
- Every time you push to `main`, Azure auto-deploys
- Your app goes live automatically

---

## ✅ STEP 4: Configure App Settings

### 4a. Set Environment Variables
1. Still in your App Service, click **"Configuration"** (left sidebar)
2. Click **"+ New application setting"**
3. Add these settings:

```
Name: FLASK_ENV
Value: production

Name: FLASK_DEBUG
Value: False

Name: APP_SECRET_KEY
Value: [generate a random string - use this: your-super-secret-key-12345]
```

4. Click **"Save"** button at the top

### 4b. Add Startup Command
1. Still in **"Configuration"** page
2. Click the **"General settings"** tab
3. Find **"Startup Command"** field
4. Enter:
```
gunicorn --bind 0.0.0.0 wsgi:app
```
5. Click **"Save"**

---

## ✅ STEP 5: Deploy and Test

### 5a. Trigger Deployment
Option 1 (Automatic):
```powershell
# Make a small change to your code, then:
git add .
git commit -m "Update for Azure deployment"
git push origin main
# Azure automatically deploys!
```

Option 2 (Manual Sync):
1. In Azure portal, go to **Deployment Center**
2. Click **"Sync"** button
3. Wait for deployment to complete

### 5b. Check Deployment Status
1. In Azure, look for **"Activity log"** or **"Deployments"**
2. You should see a successful deployment
3. Status will show: ✅ **Active**

---

## ✅ STEP 6: Get Your Live URL

### 6a. Find Your App URL
1. In Azure App Service overview page (main page)
2. Look for **"Default domain"** or **"URL"**
3. It should look like:
```
https://finance-diagnostics-app.azurewebsites.net
```

4. **Copy this URL** - this is what you send to your client!

### 6b. Test It
1. Open the URL in your browser
2. You should see:
   - Your login page
   - Or demo dashboard (if you set that as default)
3. Try registering and uploading a test file

---

## ✅ STEP 7: Send to Your Client

Send your client this information:

```
📊 Personal Finance Diagnostics Platform

Website: https://finance-diagnostics-app.azurewebsites.net

Instructions:
1. Open the link in your browser
2. Click "Register" to create an account
3. Login with your credentials
4. Click "Upload Data" to upload your financial data
5. View your complete financial health analysis!

Features:
✓ Financial Health Score (0-100)
✓ 10-Category Analysis
✓ Risk Alerts
✓ Personalized Recommendations
✓ Export Reports
✓ Secure & Private
```

---

## 🔧 Troubleshooting

### Issue: App won't start or shows error
**Solution:**
1. Go to **"Log Stream"** in Azure (left sidebar)
2. Look for error messages
3. Common issue: Missing `gunicorn` in requirements.txt (should be fixed now)
4. Push a fix to GitHub, Azure will redeploy

### Issue: Upload not working
**Solution:**
1. Check if file upload directory has correct permissions
2. In Azure, go to **"Advanced Tools"** (Kudu)
3. Check `/home/site/wwwroot/data/uploads/` directory exists
4. If not, create it manually

### Issue: Database errors
**Solution:**
1. App uses SQLite by default (stored in `/home/site/wwwroot/`)
2. For production, use Azure Database for PostgreSQL:
   - Create new PostgreSQL database in Azure
   - Update connection string in app settings
   - Update `user_store.py` to use PostgreSQL

### Issue: Page doesn't load
**Solution:**
1. Check Azure **"Application logs"** (Settings → Diagnostics)
2. Look for Python errors
3. Click **"Restart"** button to restart the app
4. Try again

---

## 📈 Scale Your App (If Needed)

If you get many users:
1. Go to **"Scale up"** in Azure
2. Change from **Free (F1)** to **Shared (D1)** or higher
3. Azure handles scaling automatically
4. More features available with higher tiers

---

## 🔐 Security Best Practices

Once deployed, consider:

1. **Enable HTTPS:**
   - Azure automatically provides SSL certificate
   - Already configured in `web.config`

2. **Add Custom Domain:**
   - Go to **"Custom domains"** in Azure
   - Add your domain (e.g., finance-diagnostics.com)

3. **Set Up Database:**
   - Use Azure Database for PostgreSQL instead of SQLite
   - More secure and scalable

4. **Enable Monitoring:**
   - Use Azure Application Insights
   - Monitor app performance and errors

5. **Backup Data:**
   - Set up regular backups in Azure
   - Protect user data

---

## 💰 Cost Estimate

**Free Tier (F1):**
- Recommended for testing/demo
- $0/month
- Limited resources
- Shared infrastructure

**Shared Tier (D1):**
- Recommended for small production
- ~$10-15/month
- Better performance
- Custom domain support

**Standard Tier (S1+):**
- For high-traffic production
- $50+/month
- Auto-scaling
- Premium features

---

## ✨ What's Next?

After deployment, you can:

1. **Add more features:**
   - Bank account auto-sync (Plaid API)
   - SMS/Email alerts
   - Scheduled reports

2. **Improve analytics:**
   - Machine learning predictions
   - Advanced visualizations
   - Comparative benchmarking

3. **Scale the business:**
   - Premium subscription tier
   - Financial advisor integrations
   - Enterprise features

---

## 📞 Support

### Azure Docs:
- Getting Started: https://docs.microsoft.com/azure/app-service/
- Python Deployment: https://docs.microsoft.com/azure/app-service/quickstart-python
- Troubleshooting: https://docs.microsoft.com/azure/app-service/troubleshoot-common-app-service-errors

### Your App Monitoring:
- **Logs:** Azure portal → Your App → "Log stream"
- **Errors:** Application Insights (if enabled)
- **Performance:** Azure portal → Metrics

---

## 🎉 You're Done!

Your platform is now **live and accessible worldwide**!

**Timeline:**
- Setup: 15-20 minutes
- GitHub push: 2-3 minutes
- First deployment: 5-10 minutes
- Total: ~30 minutes

**Send this to your client:**
```
https://finance-diagnostics-app.azurewebsites.net
```

They can now start analyzing their finances! 🚀

---

**Last Updated:** December 10, 2025
