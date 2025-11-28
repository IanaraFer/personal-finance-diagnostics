# Quick Start Guide - Finance Analytics Platform

## 🚀 Getting Started in 3 Steps

### 1. Start the Server
```powershell
cd c:\Users\35387\Desktop\contabil
.\.venv\Scripts\python.exe app.py
```

### 2. Open the Dashboard
- **Demo (no login)**: http://127.0.0.1:5001/demo
- **Full app (with login)**: http://127.0.0.1:5001

### 3. Upload Your Data
- Navigate to http://127.0.0.1:5001/upload
- Upload transactions CSV/Excel/PDF file
- Upload accounts CSV/Excel file
- Click "Upload and Analyze"

## 📊 What You'll See

### Dashboard Overview
The enhanced dashboard shows:

1. **Financial Summary Cards**
   - 💰 Total Income
   - 💸 Total Expenses
   - 📈 Savings Rate %
   - 🔮 Next Month Forecast

2. **Monthly Trends Chart**
   - Income (green line)
   - Expenses (red line)
   - Savings (blue line)
   - Last 6 months of data

3. **Recurring Transactions**
   - Detected subscriptions and bills
   - Amount and frequency
   - Next due date
   - Overdue indicators

4. **Category Breakdown**
   - Pie chart of spending by category
   - Top 5 categories
   - Percentage of total

5. **Unusual Spending Alerts**
   - Transactions that deviate significantly
   - Typical amount vs actual
   - Deviation percentage

6. **Spending Timeline**
   - Bar chart of expenses over time
   - Daily/weekly/monthly view

## 🎨 Features

### Dark Mode
- Click the moon/sun icon in the top right
- Setting is saved automatically
- Complete theme for all elements

### Export Options
- **Export PDF**: Generate a report (coming soon)
- **Export Data**: Download all your data (GDPR)
- **Delete Account**: Remove all data permanently

## 📤 Supported File Formats

### Transactions File
Required columns:
- `date`: Transaction date (various formats supported)
- `amount`: Transaction amount (numeric)
- `type`: "income" or "expense"
- `category`: Category name (optional)
- `description`: Transaction description

### Accounts File
Required columns:
- `account_name`: Name of account
- `balance`: Current balance
- `type`: Account type

### Supported Formats
- ✅ CSV (UTF-8, Latin-1, ISO-8859-1, CP1252)
- ✅ Excel (.xlsx, .xls)
- ✅ PDF (Revolut format)

## 🔍 Analytics Explained

### 1. Recurring Transaction Detection
**How it works:**
- Analyzes transaction descriptions
- Looks for similar amounts (±10%)
- Detects regular intervals
- Identifies frequency (weekly, monthly, bi-weekly)

**Example Output:**
```
Netflix: €13.99 Monthly (Next due: Dec 5)
Spotify: €9.99 Monthly (Next due: Dec 10)
```

### 2. Next Month Prediction
**How it works:**
- Uses linear regression on past 6 months
- Calculates trend (increasing/decreasing/stable)
- Provides confidence score (High/Medium/Low)

**Confidence Levels:**
- High: R² > 0.7 (70%+ accuracy)
- Medium: R² 0.4-0.7
- Low: R² < 0.4

### 3. Unusual Spending Detection
**How it works:**
- Calculates average for each category
- Computes standard deviation
- Flags transactions > 2σ above average

**Example:**
```
⚠️ Groceries: €250 (typical: €80, 212% deviation)
```

### 4. Monthly Trends
**What it shows:**
- Last 6 months of income/expenses
- Month-over-month % changes
- Savings trend
- Visual patterns

## 🐛 Troubleshooting

### Server Won't Start
```powershell
# Kill any existing Python processes
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force

# Restart the server
.\.venv\Scripts\python.exe app.py
```

### File Upload Fails
**Check:**
- File has required columns
- Date format is readable (DD/MM/YYYY or DD-MM-YYYY)
- Amounts are numeric
- File encoding is UTF-8 or Latin-1

### Page Not Loading
**Try:**
1. Refresh the page (Ctrl+R)
2. Clear browser cache (Ctrl+Shift+Del)
3. Check Flask console for errors
4. Try the /demo route: http://127.0.0.1:5001/demo

### Charts Not Displaying
**Solutions:**
- Check internet connection (Plotly loads from CDN)
- Disable browser extensions (ad blockers)
- Enable JavaScript
- Try a different browser

## 💻 Development

### Run Tests
```powershell
.\.venv\Scripts\python.exe test_analytics.py
```

### View Sample Data
```powershell
.\.venv\Scripts\python.exe -c "import pandas as pd; df = pd.read_csv('data/transactions_from_pdf.csv'); print(df.head())"
```

### Check Dependencies
```powershell
.\.venv\Scripts\pip list
```

## 📚 File Structure
```
contabil/
├── app.py                          # Flask application
├── analytics.py                    # Main analytics engine
├── advanced_analytics.py           # Advanced insights
├── file_parsers.py                 # File parsing utilities
├── convert_revolut_pdf.py          # Revolut PDF parser
├── user_store.py                   # User authentication
├── requirements.txt                # Python dependencies
├── data/
│   ├── transactions_from_pdf.csv   # Sample data (3,575 transactions)
│   ├── accounts_from_pdf.csv       # Sample accounts
│   └── sample/                     # Demo data
├── templates/
│   ├── dashboard_enhanced.html     # New dashboard ⭐
│   ├── dashboard.html              # Original dashboard
│   ├── login.html                  # Login page
│   └── register.html               # Registration page
└── static/
    └── style.css                   # Custom styles
```

## 🎯 Best Practices

### Data Upload
1. Always use UTF-8 encoding for CSV files
2. Include all required columns
3. Use consistent date formats
4. Avoid special characters in descriptions

### Regular Usage
1. Upload new transactions weekly/monthly
2. Review recurring transactions for accuracy
3. Check unusual spending alerts
4. Monitor monthly trends
5. Use predictions for budgeting

### Privacy
1. Use strong passwords
2. Export data regularly (backups)
3. Delete account when done
4. Don't share login credentials

## 🌟 Tips & Tricks

1. **Compare months**: Use the trends chart to spot seasonal patterns
2. **Track subscriptions**: Review recurring transactions to find unused subscriptions
3. **Set savings goals**: Use the forecast to plan future savings
4. **Category budgets**: Use category breakdown to identify overspending
5. **Dark mode**: Easier on eyes during nighttime use

## 📞 Support

### Common Questions

**Q: How accurate are the predictions?**
A: Confidence score indicates accuracy. High confidence (70%+) predictions are quite reliable.

**Q: Can I edit transactions?**
A: Not yet - currently view-only. Re-upload corrected file to update.

**Q: Is my data secure?**
A: Yes - stored locally in SQLite. Passwords are hashed. GDPR compliant.

**Q: Can I use multiple currencies?**
A: Not yet - single currency per analysis. Multi-currency support coming soon.

**Q: How many transactions can I upload?**
A: Tested with 3,575 transactions successfully. Should handle 10,000+ easily.

---

**Have fun analyzing your finances!** 🎉

For issues or feedback, check the Flask console for error messages.
