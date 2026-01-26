import csv
import re

# Manually extract key data points from the AIB file
# Since it's a formatted text dump from a PDF, we'll parse it carefully

transactions_data = [
    ("04/02/2025", "Interest Rate Lending", 140.00),
    ("04/02/2025", "V165158435040225NA", 140.00),
    ("04/02/2025", "HAP", 29.20),
    ("04/02/2025", "CLUBWISE SOFTW", 48.00),
    ("04/02/2025", "Electric Ireland", 65.28),
    ("04/02/2025", "NAPS LOAN AIB", 203.41),
    ("04/02/2025", "VIRGIN MEDIA", 70.00),
    ("05/02/2025", "TRANSFER", 45.00),
    ("05/02/2025", "THREE IRELAND", 35.39),
    ("06/02/2025", "V165179435060225NA", 327.00),
    ("07/02/2025", "VDP-Revolut**9877*", 140.00),
    ("07/02/2025", "MOBI CARD IANARA", 100.00),
    ("07/02/2025", "Electric Ireland", 95.43),
    ("07/02/2025", "CIRCLE K NEWLA", 40.00),
    ("10/02/2025", "HAP", 29.20),
    ("13/02/2025", "V165179435130225NA", 327.00),
    ("13/02/2025", "MOBI RENT MILLPAR", 250.00),
    ("17/02/2025", "HAP", 29.20),
    ("17/02/2025", "MOBI CARD IANARA", 55.00),
    ("18/02/2025", "eFlow", 121.00),
    ("18/02/2025", "IANARA ARAUJO FERN", 247.00),
    ("18/02/2025", "NETFLIX.COM", 8.99),
    ("18/02/2025", "MOBI CARD IANARA", 29.20),
    ("20/02/2025", "V165179435200225NA", 327.00),
    ("20/02/2025", "MOBI CARD IANARA", 10.00),
    ("24/02/2025", "IANARA ARAUJO FERN", 83.41),
    ("24/02/2025", "HAP", 64.03),
    ("24/02/2025", "MOBI CARD IANARA", 29.20),
    ("24/02/2025", "NAPS LOAN AIB", 203.41),
    ("24/02/2025", "ROYAL LONDON", 64.03),
    ("27/02/2025", "V165179435270225NA", 327.00),
    ("03/03/2025", "HAP", 100.00),
    ("03/03/2025", "CLUBWISE SOFTW", 327.00),
    ("03/03/2025", "NAPS LOAN AIB", 95.95),
    ("04/03/2025", "V165158435040325NA", 140.00),
    ("05/03/2025", "VDC-TOWER MEDICAL", 35.00),
    ("06/03/2025", "V165179435060325NA", 327.00),
    ("07/03/2025", "VIRGIN MEDIA", 70.00),
    ("07/03/2025", "HICKEYS PHARMA", 155.00),
    ("10/03/2025", "HAP", 29.20),
    ("10/03/2025", "THREE IRELAND", 35.39),
    ("11/03/2025", "DUNNES CLONDAL", 41.67),
    ("12/03/2025", "CONT BOM DIA", 20.10),
    ("12/03/2025", "MCDONALDS AERO", 17.80),
    ("12/03/2025", "TD COIMBRA", 26.30),
    ("13/03/2025", "V165179435130325NA", 327.00),
    ("13/03/2025", "FLIXBUS.COM", 33.95),
    ("13/03/2025", "MOBI RENT MILLPAR", 250.00),
    ("14/03/2025", "EUROGIANT CLON", 8.00),
    ("14/03/2025", "SUMUP  *MBEAUT", 48.75),
    ("18/03/2025", "IANARA ARAUJO FERN", 54.00),
    ("18/03/2025", "NETFLIX INTERN", 10.99),
    ("18/03/2025", "HAP", 29.20),
    ("18/03/2025", "MOBI CARD IANARA", 150.00),
    ("20/03/2025", "V165179435200325NA", 327.00),
    ("21/03/2025", "IKEA IRELAND", 286.50),
    ("21/03/2025", "VDP-Revolut**9877*", 300.00),
    ("21/03/2025", "CLONDALKIN WAS", 9.00),
    ("21/03/2025", "D Nail", 45.00),
    ("24/03/2025", "HAP", 29.20),
    ("24/03/2025", "ROYAL LONDON", 64.03),
    ("24/03/2025", "CIRCLE K NEWLA", 20.00),
    ("24/03/2025", "MCDONALDS 7091", 5.05),
    ("24/03/2025", "NYA*Gough Brot", 1.00),
    ("25/03/2025", "DUNNES CLONDAL", 5.58),
    ("26/03/2025", "LIDL DUBLIN", 23.88),
    ("27/03/2025", "V165179435270325NA", 327.00),
    ("27/03/2025", "Electric Ireland", 192.43),
    ("28/03/2025", "FEE-QTR TO 28FEB25", 19.10),
    ("28/03/2025", "TESCO STORES", 28.56),
    ("31/03/2025", "VDP-Revolut**9877*", 300.00),
    ("31/03/2025", "HAP", 29.20),
    ("31/03/2025", "CLONDALKIN SER", 33.01),
    ("01/04/2025", "V165158435010425NA", 140.00),
    ("01/04/2025", "CLUBWISE SOFTW", 48.00),
    ("01/04/2025", "DUNNES CLONDAL", 49.79),
    ("03/04/2025", "V165179435030425NA", 327.00),
    ("03/04/2025", "NAPS LOAN AIB", 203.41),
    ("04/04/2025", "VIRGIN MEDIA", 70.00),
    ("04/04/2025", "CLONDALKIN SER", 30.01),
    ("07/04/2025", "HAP", 29.20),
    ("07/04/2025", "THREE IRELAND", 34.99),
    ("08/04/2025", "CIRCLE K NEWLA", 35.00),
    ("10/04/2025", "V165179435100425NA", 294.00),
    ("10/04/2025", "WITHDRAWAL", 8246.89),
    ("10/04/2025", "Electric Ireland", 179.04),
]

# Write to CSV
output_file = 'data/AIB_account_cleaned.csv'
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Date', 'Description', 'Amount (€)'])
    writer.writeheader()
    for date, desc, amount in transactions_data:
        writer.writerow({
            'Date': date,
            'Description': desc[:80],
            'Amount (€)': f"{amount:.2f}"
        })

print(f"✓ AIB account cleaned and converted to CSV")
print(f"✓ File saved: {output_file}")
print(f"✓ Total transactions extracted: {len(transactions_data)}")

# Summary
total = sum(t[2] for t in transactions_data)
print(f"\n--- SUMMARY ---")
print(f"Total Amount: €{total:,.2f}")
print(f"Number of transactions: {len(transactions_data)}")
print(f"Period: February - April 2025")

print(f"\n--- First 15 Transactions ---")
for date, desc, amount in transactions_data[:15]:
    print(f"  {date} | {desc:<40} | €{amount:>8.2f}")
