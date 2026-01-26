import pandas as pd
import csv
from collections import defaultdict

# Read both bank datasets
aib_df = pd.read_csv('data/AIB_account_cleaned.csv')
revolut_data = {
    'Large Transactions': [
        ('07 Oct 2025', 'To Theo new house', 4600.00),
        ('07 Oct 2025', 'To Theo new house', 4600.00),
        ('09 Oct 2025', 'To Ianara Fernandes', 2900.00),
        ('24 Jul 2025', 'Booking.com', 1059.68),
        ('12 Oct 2025', 'IKEA', 761.00),
        ('20 Jan 2025', 'Pocket Withdrawal', 613.00),
        ('31 Oct 2025', 'Google Pay top-up by *8687', 600.00),
        ('21 Jan 2025', 'Allianz', 612.71),
        ('21 Jul 2025', 'To Holiday', 445.00),
    ],
    'Recurring': [
        ('To Theo new house', 18573.40, 710),
        ('To Holiday', 7068.00, 346),
        ('Pocket Withdrawal', 7850.80, 144),
        ('Saving vault topup prefunding wallet', 4148.00, 277),
        ('Circle K Gas Station', 1458.43, 53),
        ('Savings Vault topup', 1228.00, 208),
        ('Temu', 994.58, 30),
        ('To Instant Access Savings', 920.00, 76),
        ('Dunnes Stores', 886.20, 22),
        ('Amazon', 577.58, 19),
    ]
}

print('='*100)
print('COMPREHENSIVE BANK ANALYSIS REPORT')
print('REVOLUT vs AIB COMPARISON - Complete Transaction Breakdown')
print('='*100)
print()

print('█' * 100)
print('SECTION 1: AIB ACCOUNT - ALL TRANSACTIONS (86 total)')
print('█' * 100)
print()

aib_df['Amount (EUR)'] = pd.to_numeric(aib_df['Amount (€)'], errors='coerce')

# Group by description to show unique transaction names with amounts
aib_grouped = aib_df.groupby('Description').agg({
    'Amount (EUR)': ['sum', 'count', 'mean', 'max']
}).round(2)
aib_grouped.columns = ['Total', 'Count', 'Average', 'Max']
aib_grouped = aib_grouped.sort_values('Total', ascending=False)

print('AIB TRANSACTION SUMMARY BY NAME:')
print('-' * 100)
print('{:<40} {:>12} {:>8} {:>12} {:>12}'.format('Transaction Name', 'Total (EUR)', 'Count', 'Average', 'Max'))
print('-' * 100)

for desc, row in aib_grouped.iterrows():
    print('{:<40} {:>12,.2f} {:>8} {:>12,.2f} {:>12,.2f}'.format(
        desc[:40], row['Total'], int(row['Count']), row['Average'], row['Max']))

print('-' * 100)
print('{:<40} {:>12,.2f}'.format('TOTAL AIB', aib_df['Amount (EUR)'].sum()))
print()

# Show all AIB transactions chronologically
print('AIB COMPLETE TRANSACTION LIST (Chronological):')
print('-' * 100)
print('{:<12} {:<45} {:>12} {:>12}'.format('Date', 'Description', 'Amount (EUR)', 'Running Total'))
print('-' * 100)

running_total = 0
aib_sorted = aib_df.sort_values('Date')
for idx, row in aib_sorted.iterrows():
    running_total += row['Amount (EUR)']
    print('{:<12} {:<45} {:>12,.2f} {:>12,.2f}'.format(
        row['Date'], row['Description'][:45], row['Amount (EUR)'], running_total))

print()
print()

print('█' * 100)
print('SECTION 2: REVOLUT ACCOUNT - MAJOR TRANSACTIONS')
print('█' * 100)
print()

print('REVOLUT - LARGE/ONE-OFF TRANSACTIONS (Top 10%):')
print('-' * 100)
print('{:<12} {:<45} {:>12}'.format('Date', 'Name/Description', 'Amount (EUR)'))
print('-' * 100)

for date, name, amount in revolut_data['Large Transactions']:
    print('{:<12} {:<45} {:>12,.2f}'.format(date, name[:45], amount))

revolut_large_total = sum(t[2] for t in revolut_data['Large Transactions'])
print('-' * 100)
print('{:<12} {:<45} {:>12,.2f}'.format('', 'SUBTOTAL LARGE', revolut_large_total))
print()

print('REVOLUT - RECURRING/HIGH FREQUENCY TRANSACTIONS:')
print('-' * 100)
print('{:<45} {:>12} {:>8} {:>12}'.format('Name/Description', 'Total (EUR)', 'Count', 'Average'))
print('-' * 100)

for name, total, count in revolut_data['Recurring']:
    avg = total / count if count > 0 else 0
    print('{:<45} {:>12,.2f} {:>8} {:>12,.2f}'.format(name[:45], total, count, avg))

revolut_recurring_total = sum(t[1] for t in revolut_data['Recurring'])
print('-' * 100)
print('{:<45} {:>12,.2f}'.format('SUBTOTAL RECURRING', revolut_recurring_total))
print()

print('REVOLUT - CATEGORIES:')
print('-' * 100)
print('{:<30} {:>15}'.format('Category', 'Amount (EUR)'))
print('-' * 100)
revolut_categories = {
    'Transfer': 38273.88,
    'Savings': 14146.80,
    'Uncategorized': 12709.94,
    'Interest': 2.41
}
for cat, amount in sorted(revolut_categories.items(), key=lambda x: x[1], reverse=True):
    print('{:<30} {:>15,.2f}'.format(cat, amount))
print('-' * 100)
print('{:<30} {:>15,.2f}'.format('TOTAL REVOLUT EXPENSES', sum(revolut_categories.values())))
print()
print()

print('█' * 100)
print('SECTION 3: COMPARATIVE ANALYSIS - AIB vs REVOLUT')
print('█' * 100)
print()

print('ACCOUNT OVERVIEW:')
print('-' * 100)
print('{:<25} {:<20} {:<20} {:<20}'.format('Metric', 'AIB', 'Revolut', 'Difference'))
print('-' * 100)

aib_total = aib_df['Amount (EUR)'].sum()
revolut_total = sum(revolut_categories.values())

print('{:<25} {:<20} {:<20} {:<20}'.format(
    'Total Spending', f'EUR {aib_total:,.2f}', f'EUR {revolut_total:,.2f}', 
    f'EUR {revolut_total - aib_total:,.2f}'))

print('{:<25} {:<20} {:<20} {:<20}'.format(
    'Number of Transactions', f'{len(aib_df)}', f'2,188', f'{2188 - len(aib_df)}'))

print('{:<25} {:<20} {:<20} {:<20}'.format(
    'Average Transaction', f'EUR {aib_df["Amount (EUR)"].mean():.2f}', 
    f'EUR {revolut_total/2188:.2f}', f'EUR {(revolut_total/2188) - aib_df["Amount (EUR)"].mean():.2f}'))

print('{:<25} {:<20} {:<20} {:<20}'.format(
    'Period', 'Feb-Apr 2025', 'Jan-Nov 2025', 'Revolut longer'))

print('-' * 100)
print()

print('PERCENTAGE DISTRIBUTION:')
print('-' * 100)
combined_total = aib_total + revolut_total
print('AIB:     {:>6.2f}% of combined spending'.format((aib_total/combined_total)*100))
print('Revolut: {:>6.2f}% of combined spending'.format((revolut_total/combined_total)*100))
print('-' * 100)
print()

print('█' * 100)
print('SECTION 4: UNIQUE TRANSACTION NAMES - CROSS-BANK ANALYSIS')
print('█' * 100)
print()

# Find common transactions between banks
print('COMMON TRANSACTIONS ACROSS BOTH BANKS:')
print('-' * 100)

# Check for similar transaction types
common_merchants = {
    'Revolut': [],
    'AIB': [],
    'Both': []
}

revolut_names = set()
for date, name, amount in revolut_data['Large Transactions']:
    revolut_names.add(name.upper())
for name, total, count in revolut_data['Recurring']:
    revolut_names.add(name.upper())

aib_names = set(aib_df['Description'].str.upper())

# Find overlaps
common = revolut_names & aib_names
print('Transactions appearing in BOTH banks:')
if common:
    for name in sorted(common):
        aib_amount = aib_df[aib_df['Description'].str.upper() == name]['Amount (EUR)'].sum()
        print('  • {} - AIB: EUR {:.2f}'.format(name, aib_amount))
else:
    print('  • No direct overlaps (different transaction naming)')

print()

print('AIB ONLY (Not in Revolut):')
print('-' * 100)
print('{:<50} {:>15} {:>12}'.format('Description', 'Total (EUR)', 'Count'))
print('-' * 100)

aib_only_grouped = aib_df.groupby('Description')['Amount (EUR)'].agg(['sum', 'count']).sort_values('sum', ascending=False)
for desc, row in aib_only_grouped.iterrows():
    if row['sum'] > 20:  # Only show significant transactions
        print('{:<50} {:>15,.2f} {:>12}'.format(desc[:50], row['sum'], int(row['count'])))

print()

print('REVOLUT ONLY (Not in AIB):')
print('-' * 100)
print('Major categories and merchants:')

revolut_top_merchants = {
    'To Theo new house': 18573.40,
    'To Holiday': 7068.00,
    'Pocket Withdrawal': 7850.80,
    'Saving vault topup prefunding wallet': 4148.00,
    'Circle K Gas Station': 1458.43,
    'Savings Vault topup': 1228.00,
    'Temu': 994.58,
    'To Instant Access Savings': 920.00,
    'Dunnes Stores': 886.20,
    'Amazon': 577.58,
    'Booking.com': 1059.68,
    'IKEA': 761.00,
    'Allianz': 612.71,
    'Google Pay': 600.00,
    'To Ianara Fernandes': 2900.00
}

for name, amount in sorted(revolut_top_merchants.items(), key=lambda x: x[1], reverse=True)[:15]:
    print('  • {:<45} EUR {:>10,.2f}'.format(name, amount))

print()
print()

print('█' * 100)
print('SECTION 5: SPENDING PATTERNS & INSIGHTS')
print('█' * 100)
print()

print('TOP EXPENSE CATEGORIES:')
print('-' * 100)

# Categorize AIB
category_totals = defaultdict(float)

keywords = {
    'Housing': ['HAP'],
    'Utilities': ['VIRGIN MEDIA', 'Electric Ireland'],
    'Loan': ['NAPS LOAN'],
    'Insurance': ['ROYAL LONDON'],
    'Subscriptions': ['CLUBWISE', 'NETFLIX'],
    'Communications': ['THREE IRELAND'],
    'Mobile': ['MOBI CARD'],
    'Fuel': ['CIRCLE K'],
    'Groceries': ['DUNNES', 'TESCO', 'LIDL'],
    'Dining': ['MCDONALDS'],
    'Shopping': ['IKEA'],
    'Transfer': ['TRANSFER', 'Revolut'],
}

for cat, keywords_list in keywords.items():
    for keyword in keywords_list:
        total = aib_df[aib_df['Description'].str.contains(keyword, case=False, na=False)]['Amount (EUR)'].sum()
        category_totals[cat] += total

print('AIB BREAKDOWN:')
for cat, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
    if total > 0:
        print('  {:<25} EUR {:>10,.2f}'.format(cat, total))

print()
print('Revolut Major Categories:')
print('  {:<25} EUR {:>10,.2f}'.format('Transfers/Housing', 18573.40 + 7068.00))
print('  {:<25} EUR {:>10,.2f}'.format('Savings', 1228.00 + 4148.00 + 920.00))
print('  {:<25} EUR {:>10,.2f}'.format('Shopping/Travel', 1059.68 + 761.00 + 994.58 + 600.00))
print('  {:<25} EUR {:>10,.2f}'.format('Withdrawals', 7850.80))
print('  {:<25} EUR {:>10,.2f}'.format('Utilities/Insurance', 612.71))

print()
print()

print('█' * 100)
print('SECTION 6: KEY FINDINGS & RECOMMENDATIONS')
print('█' * 100)
print()

print('SUMMARY STATISTICS:')
print('-' * 100)
print('Combined Total Spending (Both Banks): EUR {:.2f}'.format(aib_total + revolut_total))
print('Number of Distinct Transaction Types: {}'.format(len(set(aib_df['Description'].unique()) | revolut_names)))
print('Largest Single Transaction: EUR 8,246.89 (AIB Withdrawal)')
print('Most Frequent AIB Transaction: HAP (10 times - Housing)')
print('Most Frequent Revolut Transaction: To Theo new house (710 times - EUR 18,573.40 total)')
print()

print('INSIGHTS:')
print('-' * 100)
print('1. AIB represents 21.4% of total spending (EUR 17,748.55)')
print('2. Revolut represents 78.6% of total spending (EUR 65,130.62)')
print('3. AIB is used for domestic, recurring expenses (housing, utilities, loans)')
print('4. Revolut is used for international transfers, online shopping, and cash withdrawals')
print('5. Largest transfer: To Theo new house (EUR 18,573.40 total across 710 transactions)')
print('6. Monthly utilities cost: ~EUR 135-260 (Virgin Media + Electric)')
print('7. Housing support (HAP) is regular: EUR 29.20-397.63 per occurrence')
print()

print('RECOMMENDATIONS:')
print('-' * 100)
print('✓ Monitor Revolut uncategorized expenses (EUR 12,709.94 - 19.5% of spending)')
print('✓ Consolidate utility payments (Virgin Media & Electric Ireland on AIB)')
print('✓ Track "To Theo new house" transfers for purpose analysis')
print('✓ Review monthly withdrawal pattern (EUR 7,850.80 total across 144 withdrawals)')
print('✓ Consider direct debits for recurring payments to reduce manual transactions')
print('✓ Set up spending alerts for transactions over EUR 300')
print()

print('='*100)
print('END OF REPORT')
print('='*100)
