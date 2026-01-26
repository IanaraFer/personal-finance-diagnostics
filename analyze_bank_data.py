import csv
import pandas as pd

# Create comprehensive summary
print("="*90)
print("BANK STATEMENT ANALYSIS - ALL NAMES & AMOUNTS DETECTED")
print("="*90)
print()

# All detected names and amounts from diagnostic report
all_transactions = {
    "Large Transactions": [
        ("07 Oct 2025", "To Theo new house", 4600.00),
        ("07 Oct 2025", "To Theo new house", 4600.00),
        ("09 Oct 2025", "To Ianara Fernandes", 2900.00),
        ("24 Jul 2025", "Booking.com", 1059.68),
        ("12 Oct 2025", "IKEA", 761.00),
        ("20 Jan 2025", "Pocket Withdrawal", 613.00),
        ("31 Oct 2025", "Google Pay top-up by *8687", 600.00),
        ("21 Jan 2025", "Allianz", 612.71),
        ("21 Jul 2025", "To Holiday", 445.00),
    ],
    "Recurring/High Frequency": [
        ("To Theo new house", 18573.40, 710, 26.16),
        ("To Holiday", 7068.00, 346, 20.43),
        ("Pocket Withdrawal", 7850.80, 144, 54.52),
        ("Saving vault topup prefunding wallet", 4148.00, 277, 14.97),
        ("Circle K Gas Station", 1458.43, 53, 27.52),
        ("Savings Vault topup", 1228.00, 208, 5.90),
        ("Temu", 994.58, 30, 33.15),
        ("To Instant Access Savings", 920.00, 76, 12.11),
        ("Dunnes Stores", 886.20, 22, 40.28),
        ("Amazon", 577.58, 19, 30.40),
    ],
    "Category Totals": [
        ("Transfer", 38273.88),
        ("Savings", 14146.80),
        ("Uncategorized", 12709.94),
        ("Interest", 2.41),
    ]
}

# Print Large Transactions
print("1. LARGE TRANSACTIONS (Individual High-Value):")
print("-" * 90)
print(f"{'Date':<15} {'Name/Description':<45} {'Amount (EUR)':>20}")
print("-" * 90)
large_sum = 0
for date, name, amount in all_transactions["Large Transactions"]:
    print(f"{date:<15} {name:<45} {amount:>20,.2f}")
    large_sum += amount
print(f"{'SUBTOTAL':<15} {'':<45} {large_sum:>20,.2f}")
print()

# Print Recurring
print("2. RECURRING/HIGH FREQUENCY EXPENSES:")
print("-" * 90)
print(f"{'Name/Description':<45} {'Total (EUR)':>15} {'Count':>10} {'Avg/Trans (EUR)':>15}")
print("-" * 90)
recurring_sum = 0
for name, total, count, avg in all_transactions["Recurring/High Frequency"]:
    print(f"{name:<45} {total:>15,.2f} {count:>10} {avg:>15,.2f}")
    recurring_sum += total
print(f"{'SUBTOTAL':<45} {recurring_sum:>15,.2f}")
print()

# Print Categories
print("3. EXPENSE CATEGORIES (Breakdown):")
print("-" * 90)
print(f"{'Category':<45} {'Amount (EUR)':>30}")
print("-" * 90)
category_sum = 0
for category, amount in all_transactions["Category Totals"]:
    print(f"{category:<45} {amount:>30,.2f}")
    category_sum += amount
print(f"{'TOTAL':<45} {category_sum:>30,.2f}")
print()

print("="*90)
print(f"GRAND TOTAL (All Expenses): EUR {category_sum:,.2f}")
print("="*90)

# Create CSV for Google Sheets
df_data = []

# Add large transactions
for date, name, amount in all_transactions["Large Transactions"]:
    df_data.append({
        "Type": "Large Transaction",
        "Date": date,
        "Name/Description": name,
        "Amount (EUR)": amount,
        "Frequency": 1,
        "Total Amount (EUR)": amount
    })

# Add recurring
for name, total, count, avg in all_transactions["Recurring/High Frequency"]:
    df_data.append({
        "Type": "Recurring Expense",
        "Date": "",
        "Name/Description": name,
        "Amount (EUR)": avg,
        "Frequency": count,
        "Total Amount (EUR)": total
    })

df = pd.DataFrame(df_data)
df.to_csv('data/google_sheets_import.csv', index=False, encoding='utf-8')

print("\n✓ CSV file created: data/google_sheets_import.csv")
print("✓ Ready to import into Google Sheets!")
