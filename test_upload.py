"""
Quick test script to verify file upload and analysis works
"""
import pandas as pd
from analytics import analyze_finances

print("=" * 80)
print("TESTING FILE UPLOAD FUNCTIONALITY")
print("=" * 80)

# Test 1: Sample test files
print("\n1. Testing with sample test files...")
try:
    tx_df = pd.read_csv('data/test_samples/sample_transactions.csv')
    acct_df = pd.read_csv('data/test_samples/sample_accounts.csv')
    
    print(f"   ✓ Loaded {len(tx_df)} transactions")
    print(f"   ✓ Loaded {len(acct_df)} accounts")
    
    # Verify required columns
    required_tx_cols = ['date', 'amount', 'type']
    required_acct_cols = ['balance', 'type']
    
    assert all(col in tx_df.columns for col in required_tx_cols), "Missing required transaction columns"
    assert all(col in acct_df.columns for col in required_acct_cols), "Missing required account columns"
    print("   ✓ All required columns present")
    
    # Run analysis
    results = analyze_finances(tx_df, acct_df)
    print(f"   ✓ Analysis completed successfully")
    print(f"   • Income: €{results['income']:,.2f}")
    print(f"   • Expenses: €{results['expenses']:,.2f}")
    print(f"   • Savings Rate: {results['savings_rate']:.1f}%")
    print(f"   • Health Score: {results['diagnostic_report']['overall_score']:.0f}/100 (Grade {results['diagnostic_report']['grade']})")
    
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Test 2: Revolut real data
print("\n2. Testing with Revolut real data...")
try:
    tx_df = pd.read_csv('data/transactions_from_pdf.csv')
    acct_df = pd.read_csv('data/accounts_from_pdf.csv')
    
    print(f"   ✓ Loaded {len(tx_df)} transactions")
    print(f"   ✓ Loaded {len(acct_df)} accounts")
    
    results = analyze_finances(tx_df, acct_df)
    print(f"   ✓ Analysis completed successfully")
    print(f"   • Income: €{results['income']:,.2f}")
    print(f"   • Expenses: €{results['expenses']:,.2f}")
    print(f"   • Savings Rate: {results['savings_rate']:.1f}%")
    print(f"   • Health Score: {results['diagnostic_report']['overall_score']:.0f}/100 (Grade {results['diagnostic_report']['grade']})")
    
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\n" + "=" * 80)
print("UPLOAD TESTING INSTRUCTIONS")
print("=" * 80)
print("""
To test the web upload functionality:

1. Open browser: http://127.0.0.1:5001/upload

2. Upload Sample Test Files:
   • Transactions: data/test_samples/sample_transactions.csv
   • Accounts: data/test_samples/sample_accounts.csv
   
3. Or Upload Your Real Revolut Data:
   • Transactions: data/transactions_from_pdf.csv
   • Accounts: data/accounts_from_pdf.csv

4. Click "Upload & Analyze"

5. View your personalized dashboard with:
   ✓ Financial Health Score
   ✓ 10 Category Analysis
   ✓ Charts and Visualizations
   ✓ Risk Alerts
   ✓ Recommendations
   ✓ Export Options

For detailed testing guide, see: TEST_GUIDE.md
""")
print("=" * 80)
