import csv
import pandas as pd

# Read AIB CSV
aib_df = pd.read_csv('data/AIB_account_cleaned.csv')
aib_df['Bank'] = 'AIB'
aib_df['Amount (EUR)'] = pd.to_numeric(aib_df['Amount (€)'], errors='coerce')

print('='*80)
print('AIB vs REVOLUT ACCOUNT ANALYSIS')
print('='*80)
print()

print('AIB ACCOUNT SUMMARY:')
print('-' * 80)
print('Total Transactions: {}'.format(len(aib_df)))
print('Total Amount: EUR {:,.2f}'.format(aib_df['Amount (EUR)'].sum()))
print('Period: {} to {}'.format(aib_df['Date'].min(), aib_df['Date'].max()))
print('Average Transaction: EUR {:.2f}'.format(aib_df['Amount (EUR)'].mean()))
print('Largest Transaction: EUR {:.2f}'.format(aib_df['Amount (EUR)'].max()))
print()

print('TOP 10 AIB TRANSACTIONS:')
print('-' * 80)
top_aib = aib_df.nlargest(10, 'Amount (EUR)')[['Date', 'Description', 'Amount (EUR)']]
for idx, row in top_aib.iterrows():
    print('{} | {:<35} | EUR {:.2f}'.format(row['Date'], row['Description'][:35], row['Amount (EUR)']))
print()

print('='*80)
print('REVOLUT ACCOUNT (From Previous Analysis):')
print('-' * 80)
print('Total Transactions: 3,575')
print('Total Expenses: EUR 65,130.62')
print('Total Income: EUR 54,505.99')
print('Net Balance: -EUR 10,624.63')
print('Period: 01 Jan 2025 to 27 Nov 2025')
print()

print('='*80)
print('COMBINED ACCOUNTS COMPARISON:')
print('-' * 80)
aib_total = aib_df['Amount (EUR)'].sum()
print('AIB Total:       EUR {:>12,.2f}  ({} transactions)'.format(aib_total, len(aib_df)))
print('Revolut Expense: EUR {:>12,.2f}  (2,188 transactions)'.format(65130.62))
print('GRAND TOTAL:     EUR {:>12,.2f}'.format(aib_total + 65130.62))
print()

# Categorize AIB transactions
recurring_keywords = {
    'VIRGIN MEDIA': 'Utilities',
    'Electric Ireland': 'Utilities',
    'HAP': 'Housing',
    'NAPS LOAN': 'Loan',
    'ROYAL LONDON': 'Insurance',
    'CLUBWISE': 'Subscriptions',
    'THREE IRELAND': 'Communications',
    'REVOLUT': 'Transfer',
    'NETFLIX': 'Entertainment',
    'MOBI CARD': 'Mobile',
    'CIRCLE K': 'Fuel',
    'DUNNES': 'Groceries',
    'TESCO': 'Groceries',
    'LIDL': 'Groceries',
    'MCDONALDS': 'Dining',
    'IKEA': 'Shopping',
    'FLIXBUS': 'Transport',
}

aib_df['Category'] = 'Other'
for keyword, category in recurring_keywords.items():
    aib_df.loc[aib_df['Description'].str.contains(keyword, case=False, na=False), 'Category'] = category

print('AIB TRANSACTIONS BY CATEGORY:')
print('-' * 80)
category_summary = aib_df.groupby('Category')['Amount (EUR)'].sum().sort_values(ascending=False)
for cat, amount in category_summary.items():
    trans_count = len(aib_df[aib_df['Category'] == cat])
    print('{:<20} EUR {:>10,.2f}  ({:>3} transactions)'.format(cat, amount, trans_count))
print('-' * 80)
print('{:<20} EUR {:>10,.2f}'.format('TOTAL', category_summary.sum()))
print()

# Export combined data
combined_df = aib_df[['Date', 'Description', 'Amount (EUR)', 'Category', 'Bank']]
combined_df.to_csv('data/AIB_with_categories.csv', index=False)

print('Files created:')
print('  1. data/AIB_account_cleaned.csv - Raw AIB transactions')
print('  2. data/AIB_with_categories.csv - AIB with categories')
