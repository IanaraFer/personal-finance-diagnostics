import pandas as pd
import csv

# Read AIB data
aib_df = pd.read_csv('data/AIB_account_cleaned.csv')
aib_df['Amount (EUR)'] = pd.to_numeric(aib_df['Amount (€)'], errors='coerce')

# Create combined export with all transaction details
all_transactions = []

# Add AIB transactions
for idx, row in aib_df.iterrows():
    all_transactions.append({
        'Bank': 'AIB',
        'Date': row['Date'],
        'Description': row['Description'],
        'Amount (EUR)': float(row['Amount (EUR)']),
        'Type': 'Expense'
    })

# Add Revolut large transactions
revolut_large = [
    ('07/10/2025', 'To Theo new house', 4600.00),
    ('07/10/2025', 'To Theo new house', 4600.00),
    ('09/10/2025', 'To Ianara Fernandes', 2900.00),
    ('24/07/2025', 'Booking.com', 1059.68),
    ('12/10/2025', 'IKEA', 761.00),
    ('20/01/2025', 'Pocket Withdrawal', 613.00),
    ('31/10/2025', 'Google Pay top-up', 600.00),
    ('21/01/2025', 'Allianz', 612.71),
    ('21/07/2025', 'To Holiday', 445.00),
]

for date, desc, amount in revolut_large:
    all_transactions.append({
        'Bank': 'Revolut',
        'Date': date,
        'Description': desc,
        'Amount (EUR)': amount,
        'Type': 'Large Transaction'
    })

# Add Revolut recurring (sample entries)
revolut_recurring = [
    ('Recurring', 'To Theo new house', 18573.40, 710),
    ('Recurring', 'To Holiday', 7068.00, 346),
    ('Recurring', 'Pocket Withdrawal', 7850.80, 144),
    ('Recurring', 'Saving vault topup', 4148.00, 277),
    ('Recurring', 'Circle K Gas Station', 1458.43, 53),
    ('Recurring', 'Savings Vault topup', 1228.00, 208),
    ('Recurring', 'Temu', 994.58, 30),
    ('Recurring', 'To Instant Access Savings', 920.00, 76),
    ('Recurring', 'Dunnes Stores', 886.20, 22),
    ('Recurring', 'Amazon', 577.58, 19),
]

# Save to CSV
export_df = pd.DataFrame(all_transactions)
export_df.to_csv('data/COMBINED_BANKS_ALL_TRANSACTIONS.csv', index=False)

# Create summary statistics file
with open('data/BANK_SUMMARY_STATISTICS.txt', 'w', encoding='utf-8') as f:
    f.write('='*100 + '\n')
    f.write('COMPREHENSIVE BANK ANALYSIS REPORT\n')
    f.write('REVOLUT vs AIB COMPARISON - Summary Statistics\n')
    f.write('='*100 + '\n\n')
    
    # AIB Summary
    f.write('AIB ACCOUNT SUMMARY\n')
    f.write('-'*100 + '\n')
    f.write('Total Transactions: {}\n'.format(len(aib_df)))
    f.write('Total Amount: EUR {:,.2f}\n'.format(aib_df['Amount (EUR)'].sum()))
    f.write('Average Transaction: EUR {:.2f}\n'.format(aib_df['Amount (EUR)'].mean()))
    f.write('Largest Transaction: EUR {:.2f}\n'.format(aib_df['Amount (EUR)'].max()))
    f.write('Period: February 1 - April 10, 2025\n')
    f.write('Bank: Allied Irish Bank (AIB)\n')
    f.write('\n')
    
    # AIB Top transactions
    f.write('TOP 10 AIB TRANSACTIONS:\n')
    f.write('-'*100 + '\n')
    top_aib = aib_df.nlargest(10, 'Amount (EUR)')[['Date', 'Description', 'Amount (EUR)']]
    for idx, row in top_aib.iterrows():
        f.write('{} | {:<40} | EUR {:.2f}\n'.format(row['Date'], row['Description'][:40], row['Amount (EUR)']))
    f.write('\n')
    
    # Revolut Summary
    f.write('REVOLUT ACCOUNT SUMMARY\n')
    f.write('-'*100 + '\n')
    f.write('Total Transactions: 3,575 (income + expenses combined)\n')
    f.write('Total Expenses: EUR 65,130.62\n')
    f.write('Total Income: EUR 54,505.99\n')
    f.write('Net Balance: -EUR 10,624.63\n')
    f.write('Average Transaction: EUR 29.77\n')
    f.write('Period: January 1 - November 27, 2025\n')
    f.write('Bank: Revolut (Online Bank)\n')
    f.write('\n')
    
    # Revolut Top Recurring
    f.write('TOP 10 REVOLUT RECURRING TRANSACTIONS:\n')
    f.write('-'*100 + '\n')
    revolut_recurring_sorted = sorted(revolut_recurring, key=lambda x: x[2], reverse=True)[:10]
    for trans_type, name, total, count in revolut_recurring_sorted:
        avg = total / count if count > 0 else 0
        f.write('{:<45} Total: EUR {:<12,.2f} Count: {:<5} Avg: EUR {:.2f}\n'.format(
            name[:45], total, count, avg))
    f.write('\n')
    
    # Combined Analysis
    f.write('='*100 + '\n')
    f.write('COMBINED ANALYSIS\n')
    f.write('='*100 + '\n\n')
    
    aib_total = aib_df['Amount (EUR)'].sum()
    revolut_total = 65130.62
    combined_total = aib_total + revolut_total
    
    f.write('TOTAL SPENDING BREAKDOWN:\n')
    f.write('-'*100 + '\n')
    f.write('AIB Total:       EUR {:>12,.2f}  ({:>6.2f}% of combined)\n'.format(aib_total, (aib_total/combined_total)*100))
    f.write('Revolut Total:   EUR {:>12,.2f}  ({:>6.2f}% of combined)\n'.format(revolut_total, (revolut_total/combined_total)*100))
    f.write('COMBINED TOTAL:  EUR {:>12,.2f}\n'.format(combined_total))
    f.write('\n')
    
    f.write('TRANSACTION COUNT:\n')
    f.write('-'*100 + '\n')
    f.write('AIB Transactions:      {}\n'.format(len(aib_df)))
    f.write('Revolut Transactions:  2,188 (expenses only)\n')
    f.write('Total Transactions:    {:,}\n'.format(len(aib_df) + 2188))
    f.write('\n')
    
    # Key Insights
    f.write('='*100 + '\n')
    f.write('KEY INSIGHTS\n')
    f.write('='*100 + '\n\n')
    
    f.write('1. ACCOUNT USAGE PATTERN:\n')
    f.write('   - AIB: Domestic, recurring expenses (21.4% of total spending)\n')
    f.write('   - Revolut: International transfers, online shopping, cash (78.6% of total spending)\n\n')
    
    f.write('2. LARGEST TRANSACTIONS:\n')
    f.write('   - AIB: EUR 8,246.89 (Withdrawal)\n')
    f.write('   - Revolut: EUR 4,600.00 (To Theo new house - appears twice)\n\n')
    
    f.write('3. MOST FREQUENT TRANSACTIONS:\n')
    f.write('   - AIB: HAP (Housing) - 10 times\n')
    f.write('   - Revolut: To Theo new house - 710 times (EUR 18,573.40 total)\n\n')
    
    f.write('4. MONTHLY EXPENSE BREAKDOWN:\n')
    f.write('   AIB Regular Costs:\n')
    f.write('   - Utilities (Virgin Media + Electric): EUR 135-260/month\n')
    f.write('   - Housing (HAP): EUR 29.20-397.63 per occurrence\n')
    f.write('   - Loan (NAPS): EUR 203.41/month\n')
    f.write('   - Mobile/Card: EUR 62-150/month\n\n')
    
    f.write('5. UNCATEGORIZED SPENDING:\n')
    f.write('   - Revolut Uncategorized: EUR 12,709.94 (19.5% of expenses)\n')
    f.write('   - Recommendation: Review and categorize for better financial tracking\n\n')
    
    f.write('6. SPENDING PATTERNS:\n')
    f.write('   - Peak spending month (Revolut): October (EUR -783.65 net)\n')
    f.write('   - Revolut deficit: EUR 10,624.63 (spending > income)\n')
    f.write('   - Main transfer: EUR 18,573.40 to Theo new house\n\n')
    
    f.write('='*100 + '\n')
    f.write('RECOMMENDATIONS\n')
    f.write('='*100 + '\n\n')
    
    recommendations = [
        'Monitor Revolut uncategorized expenses (EUR 12,709.94) - 19.5% of spending',
        'Consolidate utility payments on AIB for better tracking',
        'Verify "To Theo new house" transfers (EUR 18,573.40 total) for proper categorization',
        'Review monthly withdrawal pattern (EUR 7,850.80 across 144 withdrawals)',
        'Consider setting up direct debits for recurring payments',
        'Set spending alerts for transactions over EUR 300',
        'Track income sources in Revolut (EUR 54,505.99 total)',
        'Analyze reason for spending deficit (EUR -10,624.63 on Revolut)',
        'Create separate budget for savings accounts (EUR 6,296 total)',
    ]
    
    for i, rec in enumerate(recommendations, 1):
        f.write('{}. {}\n'.format(i, rec))
    
    f.write('\n')

print('Files generated:')
print('1. data/COMBINED_BANKS_ALL_TRANSACTIONS.csv')
print('2. data/BANK_SUMMARY_STATISTICS.txt')
