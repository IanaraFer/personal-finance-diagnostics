# 🧪 Testing Guide - Personal Finance Diagnostics Platform

## Quick Start Testing

### 1️⃣ **Access the Application**
- Open your browser and go to: **http://127.0.0.1:5001**
- You should see the demo dashboard with sample data

### 2️⃣ **Test User Registration & Login**

#### Register a New Account:
1. Click "Logout" (if logged in)
2. Click "Register"
3. Enter:
   - Email: `test@example.com`
   - Password: `TestPassword123!`
4. Click "Register"
5. You'll be logged in automatically

#### Login with Existing Account:
1. Go to http://127.0.0.1:5001/login
2. Enter your credentials
3. Click "Login"

---

## 📤 Testing File Upload (Method 1: Use Your Revolut Data)

### Option A: Upload Real Revolut Data

1. **Navigate to Upload Page:**
   - Click **"Upload Data"** button in the dashboard
   - Or go to: http://127.0.0.1:5001/upload

2. **Upload Files:**
   - **Transactions File:** Select `data/transactions_from_pdf.csv` (3,575 real transactions)
   - **Accounts File:** Select `data/accounts_from_pdf.csv`
   - Click **"Upload & Analyze"**

3. **View Results:**
   - You'll see your personalized dashboard with:
     - ✅ Financial Health Score (43/100 - Grade D)
     - ✅ 10 Category Breakdown
     - ✅ Monthly trends and charts
     - ✅ Risk alerts
     - ✅ Recommendations

---

## 📤 Testing File Upload (Method 2: Sample Test Files)

### Option B: Use Sample Test Files

I've created sample CSV files in `data/test_samples/` for easy testing:

1. **Navigate to Upload Page:**
   - Click **"Upload Data"** button
   - Or go to: http://127.0.0.1:5001/upload

2. **Upload Sample Files:**
   - **Transactions File:** `data/test_samples/sample_transactions.csv`
   - **Accounts File:** `data/test_samples/sample_accounts.csv`
   - Click **"Upload & Analyze"**

3. **View Results:**
   - Dashboard with complete financial analysis
   - Charts showing income/expense trends
   - Diagnostic health score
   - Personalized recommendations

---

## 🎯 Testing All Features

### 1. **Financial Health Diagnostic**
- **Location:** Main dashboard (automatically visible)
- **What to check:**
  - ✅ Circular health score indicator (color-coded)
  - ✅ Overall score (0-100) and letter grade (A+ to F)
  - ✅ 10 category cards with individual scores
  - ✅ Risk alerts (red bordered cards)
  - ✅ Data gaps (yellow bordered cards)
  - ✅ Recommendations section

### 2. **Complete Your Profile (Questionnaire)**
- **Click:** "Complete Profile" button (if data gaps exist)
- **Fill out:** Dynamic questionnaire with 5 questions:
  - Insurance coverage
  - Financial goals
  - Risk tolerance
  - Debt confirmation
  - Credit score
- **Submit:** Click "Complete Profile & View Full Report"
- **Result:** Returns to dashboard with updated analysis

### 3. **Monthly Optimization Analysis**
- **Location:** Scroll down in dashboard
- **What to check:**
  - ✅ Current savings rate vs Potential savings rate
  - ✅ Month-by-month comparison table
  - ✅ Spending categories that can be cut
  - ✅ Potential monthly savings amount

### 4. **Charts & Visualizations**
- **Expense Breakdown:** Pie chart showing category distribution
- **Income vs Expenses:** Bar chart comparison
- **Monthly Trends:** Line chart showing spending over time
- **Recurring Transactions:** List of detected subscriptions

### 5. **Export Functionality**

#### Export PDF Report:
- **Click:** "📄 Export PDF Report" button
- **Result:** Downloads text file with:
  - Overall health score and grade
  - All 10 category scores
  - Financial summary
  - Risk alerts
  - Recommendations
- **Filename:** `financial_report_YYYYMMDD_HHMMSS.txt`

#### Export Your Data:
- **Click:** "📊 Export My Data" button
- **Result:** Downloads JSON file with:
  - All transactions
  - Summary statistics
  - Complete diagnostic report
  - Timestamp
- **Filename:** `financial_data_YYYYMMDD_HHMMSS.json`

### 6. **Dark Mode Toggle**
- **Location:** Top right corner
- **Click:** Dark mode toggle button
- **Result:** Theme switches between light/dark mode

---

## 🧾 Sample File Formats

### Transactions CSV Format:
```csv
date,description,amount,type,category
2025-01-01,Salary Deposit,3500.00,income,Salary
2025-01-02,Grocery Store,-85.50,expense,Food
2025-01-03,Electric Bill,-120.00,expense,Utilities
2025-01-05,Coffee Shop,-4.50,expense,Food
2025-01-10,Freelance Payment,500.00,income,Freelance
```

**Required Columns:**
- `date` - Transaction date (YYYY-MM-DD format)
- `amount` - Amount (positive for income, negative/positive for expense)
- `type` - Transaction type (`income` or `expense`)

**Optional Columns:**
- `description` - Transaction description
- `category` - Category name (Food, Utilities, etc.)

### Accounts CSV Format:
```csv
account_name,type,balance
Main Checking,checking,2500.00
Savings Account,savings,10000.00
Credit Card,credit,-850.00
```

**Required Columns:**
- `balance` - Current account balance
- `type` - Account type (checking, savings, investment, credit)

**Optional Columns:**
- `account_name` - Name of the account

---

## 🔍 Expected Test Results

### With Revolut Data (3,575 transactions):
- **Overall Score:** 43/100 (Grade D)
- **Income:** €54,505.99
- **Expenses:** €65,130.62
- **Savings Rate:** -9.0% (current) → 28.3% (potential)
- **Risks Identified:** 4 alerts
- **Data Gaps:** 4 missing items
- **Recommendations:** 3 priority actions

### With Sample Test Data:
- **Overall Score:** ~60-70/100 (Grade C/C+)
- **Balanced budget scenario**
- **Some optimization opportunities**
- **Fewer risks and gaps**

---

## 🐛 Troubleshooting

### Upload Not Working?
1. Check file format (CSV, Excel .xlsx/.xls, or PDF)
2. Ensure required columns exist:
   - Transactions: `date`, `amount`, `type`
   - Accounts: `balance`, `type`
3. Check for error messages displayed on upload page

### Dashboard Not Loading?
1. Verify Flask server is running (check terminal)
2. Refresh browser page
3. Check browser console for errors (F12)

### Export Not Working?
1. Check if you're logged in
2. Ensure browser allows downloads
3. Check terminal for any Python errors

### Charts Not Displaying?
1. Ensure JavaScript is enabled
2. Check browser console for Plotly errors
3. Try refreshing the page

---

## 📊 Test Scenarios

### Scenario 1: High Earner with Overspending
- **Upload:** Your Revolut data
- **Expected:** Low health score, high expense warnings
- **Test:** Check if recommendations suggest expense reduction

### Scenario 2: Balanced Budget
- **Upload:** Sample test files
- **Expected:** Moderate health score, few warnings
- **Test:** Verify optimization shows smaller improvements

### Scenario 3: Complete Profile
- **Start:** Any upload with data gaps
- **Click:** "Complete Profile" button
- **Fill:** All questionnaire fields
- **Expected:** Updated health score, fewer gaps

---

## ✅ Verification Checklist

- [ ] Can register new account
- [ ] Can login successfully
- [ ] Can upload CSV files
- [ ] Can upload Excel files (if available)
- [ ] Dashboard displays after upload
- [ ] Health score shows correctly
- [ ] All 10 categories display scores
- [ ] Charts render properly
- [ ] Risk alerts visible (if applicable)
- [ ] Recommendations show up
- [ ] Questionnaire button appears (if gaps exist)
- [ ] Can complete questionnaire
- [ ] Can export PDF report
- [ ] Can export JSON data
- [ ] Downloads have correct filenames
- [ ] Dark mode toggle works
- [ ] Can logout

---

## 🎓 Tips for Testing

1. **Test with Different Data:**
   - Try different CSV formats
   - Test with large files (1000+ transactions)
   - Test with minimal data (10-20 transactions)

2. **Test Error Handling:**
   - Upload file with missing columns
   - Upload invalid file format
   - Upload empty files

3. **Test User Flow:**
   - Complete flow: Register → Upload → View Dashboard → Complete Profile → Export
   - Multiple uploads to see how data updates

4. **Performance Testing:**
   - Time how long analysis takes
   - Check if browser remains responsive
   - Monitor memory usage with large files

---

## 📝 Notes

- **Demo Mode:** Visit `/demo` to see pre-loaded sample data without uploading
- **Session Management:** Data persists during your session
- **Privacy:** All data processed locally, nothing sent to external servers
- **File Storage:** Uploaded files temporarily stored in `data/uploads/`

---

## 🆘 Support

If you encounter issues:
1. Check the terminal where Flask is running for error messages
2. Look for Python tracebacks
3. Verify file formats match requirements
4. Ensure all dependencies are installed (`pip install -r requirements.txt`)

---

**Last Updated:** November 28, 2025
