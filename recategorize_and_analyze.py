#!/usr/bin/env python3
"""
Recategorize transactions and generate updated analysis
Clarifications:
- "To Theo new house" = Savings for son Theo (not an expense, but savings transfer)
- Identify online shopping (Amazon, Temu, Shein, etc.)
- Identify groceries (Dunnes, Lidl, Aldi, Tesco)
- Identify gas stations (Circle K, Topaz, Applegreen)
- Identify loans (Loan, emprestado)
"""

import pandas as pd
import re

# Load data
tx = pd.read_csv('data/transactions_from_pdf.csv')

# Parse dates and amounts
tx['date'] = pd.to_datetime(tx['date'], format='mixed', dayfirst=True, errors='coerce')
tx = tx.dropna(subset=['date'])
tx['amount'] = pd.to_numeric(tx['amount'], errors='coerce')
tx = tx.dropna(subset=['amount'])

print("Total transactions loaded:", len(tx))

# Create a copy for recategorization
tx['original_category'] = tx['category']
tx['new_category'] = tx['category']

# Function to categorize based on description
def recategorize(row):
    desc = str(row['description']).lower()
    
    # SAVINGS FOR THEO (Clarification: This is savings, not expense)
    if 'to theo new house' in desc:
        return 'Savings - Theo Future Home'
    
    # ONLINE SHOPPING - Kids/Clothes/Accessories
    if any(shop in desc for shop in ['amazon', 'temu', 'shein', 'asos', 'zara', 'h&m', 'primark']):
        return 'Online Shopping - Clothes & Accessories'
    
    # GROCERIES - Supermarkets
    if any(shop in desc for shop in ['dunnes', 'lidl', 'aldi', 'tesco', 'supervalu', 'spar']):
        return 'Groceries - Supermarket'
    
    # GAS STATIONS - Combustível (Fuel)
    if any(gas in desc for gas in ['circle k', 'topaz', 'applegreen', 'gas station', 'petrol', 'fuel']):
        return 'Fuel - Gas Station'
    
    # LOANS - Money borrowed from bank
    if any(loan in desc for loan in ['loan', 'emprestado', 'banco', 'bank loan', 'credit']):
        return 'Loan - Bank'
    
    # KIDS - Childcare, school, activities
    if any(kid in desc for kid in ['creche', 'childcare', 'school', 'kids', 'children', 'montessori', 'daycare']):
        return 'Kids - Education & Care'
    
    # POCKET SAVINGS (Internal transfers to savings pockets)
    if 'to pocket eur' in desc or 'pocket withdrawal' in desc:
        return 'Internal - Pocket Savings'
    
    # Keep original category if already categorized
    if row['category'] != 'Uncategorized':
        return row['category']
    
    return 'Uncategorized'

# Apply recategorization
tx['new_category'] = tx.apply(recategorize, axis=1)

# Save recategorized data
tx.to_csv('data/transactions_recategorized.csv', index=False)

print("\n" + "="*80)
print("RECATEGORIZATION COMPLETE")
print("="*80)

# Show changes
changes = tx[tx['new_category'] != tx['original_category']]
print(f"\nTotal transactions recategorized: {len(changes)}")

# Count by new category
print("\n" + "="*80)
print("CATEGORY BREAKDOWN (After Recategorization)")
print("="*80)

category_summary = tx.groupby(['type', 'new_category'])['amount'].agg(['count', 'sum']).round(2)
category_summary.columns = ['Transactions', 'Total Amount (EUR)']
print(category_summary.to_string())

# Specific analysis for key categories
print("\n" + "="*80)
print("KEY INSIGHTS")
print("="*80)

# 1. Theo Savings (Clarification)
theo_savings = tx[tx['new_category'] == 'Savings - Theo Future Home']
theo_total = theo_savings['amount'].sum()
theo_count = len(theo_savings)
print(f"\n1. SAVINGS FOR THEO'S FUTURE HOME")
print(f"   - Total saved: EUR {theo_total:,.2f}")
print(f"   - Number of transactions: {theo_count}")
print(f"   - This is SAVINGS for your son Theo's future, NOT an expense")
print(f"   - Average per transaction: EUR {theo_total/theo_count:.2f}")

# 2. Online Shopping
online = tx[tx['new_category'] == 'Online Shopping - Clothes & Accessories']
online_total = online['amount'].sum()
online_count = len(online)
if online_count > 0:
    print(f"\n2. ONLINE SHOPPING (Amazon, Temu, Shein, etc.)")
    print(f"   - Total spent: EUR {online_total:,.2f}")
    print(f"   - Number of orders: {online_count}")
    print(f"   - Average order: EUR {online_total/online_count:.2f}")
    print(f"   - Top merchants:")
    for merchant in ['amazon', 'temu', 'shein']:
        merchant_tx = online[online['description'].str.lower().str.contains(merchant, na=False)]
        if len(merchant_tx) > 0:
            print(f"     * {merchant.title()}: {len(merchant_tx)} orders, EUR {merchant_tx['amount'].sum():.2f}")

# 3. Groceries
groceries = tx[tx['new_category'] == 'Groceries - Supermarket']
grocery_total = groceries['amount'].sum()
grocery_count = len(groceries)
if grocery_count > 0:
    print(f"\n3. GROCERIES (Dunnes, Lidl, Aldi, Tesco)")
    print(f"   - Total spent: EUR {grocery_total:,.2f}")
    print(f"   - Number of trips: {grocery_count}")
    print(f"   - Average per trip: EUR {grocery_total/grocery_count:.2f}")
    print(f"   - Monthly average: EUR {grocery_total/11:.2f}")
    print(f"   - Top stores:")
    for store in ['dunnes', 'lidl', 'aldi', 'tesco']:
        store_tx = groceries[groceries['description'].str.lower().str.contains(store, na=False)]
        if len(store_tx) > 0:
            print(f"     * {store.title()}: {len(store_tx)} visits, EUR {store_tx['amount'].sum():.2f}")

# 4. Fuel/Gas
fuel = tx[tx['new_category'] == 'Fuel - Gas Station']
fuel_total = fuel['amount'].sum()
fuel_count = len(fuel)
if fuel_count > 0:
    print(f"\n4. FUEL/GAS (Circle K, Topaz, Applegreen)")
    print(f"   - Total spent: EUR {fuel_total:,.2f}")
    print(f"   - Number of fill-ups: {fuel_count}")
    print(f"   - Average per fill-up: EUR {fuel_total/fuel_count:.2f}")
    print(f"   - Monthly average: EUR {fuel_total/11:.2f}")

# 5. Kids expenses
kids = tx[tx['new_category'] == 'Kids - Education & Care']
kids_total = kids['amount'].sum()
kids_count = len(kids)
if kids_count > 0:
    print(f"\n5. KIDS - EDUCATION & CARE")
    print(f"   - Total spent: EUR {kids_total:,.2f}")
    print(f"   - Number of transactions: {kids_count}")
    print(f"   - Monthly average: EUR {kids_total/11:.2f}")

# 6. Remaining uncategorized
uncategorized = tx[tx['new_category'] == 'Uncategorized']
uncat_total = uncategorized['amount'].sum()
uncat_count = len(uncategorized)
print(f"\n6. STILL UNCATEGORIZED")
print(f"   - Total: EUR {uncat_total:,.2f}")
print(f"   - Number of transactions: {uncat_count}")
print(f"   - Percentage of total: {(uncat_total/tx['amount'].sum())*100:.1f}%")

# Export summary
print("\n" + "="*80)
print("EXPENSE BREAKDOWN (Excluding Internal Savings)")
print("="*80)

# Only real expenses (type='expense' and not internal savings)
real_expenses = tx[(tx['type'] == 'expense') & (~tx['new_category'].str.contains('Internal|Savings', case=False, na=False))]
expense_by_cat = real_expenses.groupby('new_category')['amount'].sum().sort_values(ascending=False)

print("\nREAL EXPENSES BY CATEGORY:")
total_real_expenses = expense_by_cat.sum()
for cat, amount in expense_by_cat.items():
    pct = (amount / total_real_expenses) * 100
    print(f"  {cat:40s}: EUR {amount:10,.2f} ({pct:5.1f}%)")

print(f"\n  {'TOTAL REAL EXPENSES':40s}: EUR {total_real_expenses:10,.2f} (100.0%)")

# Monthly breakdown
print("\n" + "="*80)
print("MONTHLY EXPENSE BREAKDOWN BY CATEGORY")
print("="*80)

real_expenses['month'] = real_expenses['date'].dt.strftime('%Y-%m')
monthly_cat = real_expenses.pivot_table(
    index='month', 
    columns='new_category', 
    values='amount', 
    aggfunc='sum', 
    fill_value=0
).round(2)

print(monthly_cat.to_string())

# Save detailed report
with open('RECATEGORIZATION_REPORT.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("TRANSACTION RECATEGORIZATION REPORT\n")
    f.write("="*80 + "\n\n")
    
    f.write("CLARIFICATION:\n")
    f.write(f"  'To Theo new house' = Savings for son Theo's future home\n")
    f.write(f"  Total saved for Theo: EUR {theo_total:,.2f} ({theo_count} transactions)\n")
    f.write(f"  This is SAVINGS, not an expense\n\n")
    
    f.write("="*80 + "\n")
    f.write("EXPENSE CATEGORIES IDENTIFIED:\n")
    f.write("="*80 + "\n\n")
    
    for cat, amount in expense_by_cat.items():
        pct = (amount / total_real_expenses) * 100
        f.write(f"  {cat:40s}: EUR {amount:10,.2f} ({pct:5.1f}%)\n")
    
    f.write(f"\n  {'TOTAL':40s}: EUR {total_real_expenses:10,.2f}\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("KEY INSIGHTS:\n")
    f.write("="*80 + "\n\n")
    
    if online_count > 0:
        f.write(f"ONLINE SHOPPING: EUR {online_total:,.2f} ({online_count} orders)\n")
        f.write(f"  - Potential savings opportunity by reducing online orders\n\n")
    
    if grocery_count > 0:
        f.write(f"GROCERIES: EUR {grocery_total:,.2f} ({grocery_count} trips)\n")
        f.write(f"  - Monthly average: EUR {grocery_total/11:.2f}\n\n")
    
    if fuel_count > 0:
        f.write(f"FUEL: EUR {fuel_total:,.2f} ({fuel_count} fill-ups)\n")
        f.write(f"  - Monthly average: EUR {fuel_total/11:.2f}\n\n")

print("\n" + "="*80)
print("Report saved to: RECATEGORIZATION_REPORT.txt")
print("Recategorized data saved to: data/transactions_recategorized.csv")
print("="*80)
