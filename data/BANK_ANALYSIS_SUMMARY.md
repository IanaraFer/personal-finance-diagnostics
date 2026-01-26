# Bank Account Analysis Summary

## ✅ Task Completed: AIB Account Cleaned & Fixed

### Files Created:
1. **data/AIB_account_cleaned.csv** - 86 transactions from AIB (Feb-Apr 2025)
2. **data/AIB_with_categories.csv** - AIB transactions categorized  
3. **data/google_sheets_import.csv** - Combined Revolut data (ready for Google Sheets)

---

## AIB Account Overview

| Metric | Value |
|--------|-------|
| **Total Transactions** | 86 |
| **Total Amount** | EUR 17,748.55 |
| **Average Transaction** | EUR 206.38 |
| **Largest Transaction** | EUR 8,246.89 (Withdrawal) |
| **Period** | February 1 - April 10, 2025 |

### Top 10 AIB Transactions:
1. WITHDRAWAL - EUR 8,246.89
2. Multiple V165 transfers - EUR 327.00 each (6 times)
3. HAP (Housing) - EUR 29.20-150.00
4. Revolut transfers - EUR 140-300.00

---

## AIB Transaction Breakdown by Category:

| Category | Amount | Count |
|----------|---------|-------|
| **Other** | EUR 13,524.57 | 34 |
| **Utilities** | EUR 742.18 | 7 |
| **Transfer** | EUR 740.00 | 3 |
| **Loan** | EUR 706.18 | 4 |
| **Subscriptions** | EUR 423.00 | 3 |
| **Housing (HAP)** | EUR 397.63 | 10 |
| **Mobile/Card** | EUR 373.40 | 6 |
| **Shopping** | EUR 286.50 | 1 |
| **Groceries** | EUR 149.48 | 5 |
| **Insurance** | EUR 128.06 | 2 |

---

## AIB vs REVOLUT Comparison:

### AIB Account (Irish Bank):
- **Transactions:** 86
- **Total:** EUR 17,748.55
- **Period:** Feb - Apr 2025 (3 months)
- **Focus:** Personal expenses, utilities, loans, housing

### Revolut Account (Online Bank):
- **Transactions:** 3,575 (income + expenses)
- **Total Expenses:** EUR 65,130.62
- **Total Income:** EUR 54,505.99
- **Net:** -EUR 10,624.63 (deficit)
- **Period:** Jan - Nov 2025 (11 months)
- **Focus:** International transfers, shopping, travel

### Combined Summary:
- **Total Across Both:** EUR 82,879.17
- **Combined Transactions:** 3,661
- **Recommendation:** AIB is primary for domestic payments; Revolut for international/online shopping

---

## Key Insights:

1. **Revolut** handles majority of spending (77.6% of total)
2. **AIB** is essential for loan payments, housing (HAP), and domestic utilities
3. **Recurring Expenses:**
   - HAP Housing: EUR 29.20-397.63/month
   - Utilities (Virgin Media, Electric): EUR 65-95/month
   - Loan (NAPS): EUR 203/month
   - Subscriptions (Netflix, Clubwise): EUR 8-48/month

4. **Savings Opportunities:**
   - Monitor Revolut's large "To Theo new house" transfers (EUR 18,573.40 total)
   - Track Revolut's uncategorized expenses (EUR 12,709.94 - 19.5% of Revolut spending)

---

## Files Ready for Import to Google Sheets:

Use these files to create detailed analysis in Google Sheets:
- `data/AIB_with_categories.csv` - Categorized AIB transactions
- `data/google_sheets_import.csv` - Revolut transactions
- `data/all_names_amounts_detailed.csv` - Combined names & amounts

**Steps to import:**
1. Go to Google Drive
2. Upload CSV file
3. Right-click → "Open with" → "Google Sheets"
4. Create pivot tables for spending analysis
