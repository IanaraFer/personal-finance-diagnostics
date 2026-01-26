import re
import csv

# Read the AIB account file
with open('data/aibaccount.txt', 'r', encoding='utf-8') as f:
    content = f.read()

transactions = []
months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
          'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

# Split by dates - key pattern: "DD MMM YYYY" at start of transaction block
# This is the main separator between transactions
date_pattern = r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})'

# Find all date positions
for match in re.finditer(date_pattern, content):
    start_pos = match.start()
    
    # Get date components
    day = int(match.group(1))
    month = months[match.group(2)]
    year = int(match.group(3))
    date_str = f"{day:02d}/{month:02d}/{year}"
    
    # Find the text between this date and the next date
    next_match = None
    for m in re.finditer(date_pattern, content[match.end():]):
        next_match = m
        break
    
    if next_match:
        end_pos = match.end() + next_match.start()
        block = content[match.end():end_pos]
    else:
        block = content[match.end():match.end() + 500]  # Take next 500 chars if last transaction
    
    # Remove header garbage - look for lines with just numbers (balances)
    lines = block.split('\n')
    
    transaction_lines = []
    for line in lines:
        line = line.strip()
        if not line or len(line) < 2:
            continue
        # Skip IBAN codes and other non-relevant lines
        if 'IE25' in line or 'Personal Bank' in line or 'IANARA' in line or 'For Important' in line or \
           'Thank you' in line or 'Deposit Guarantee' in line or 'www.aib' in line or 'Telephone' in line or \
           'Branch' in line or 'Page' in line or 'DUBLIN' in line or 'Sort Code' in line or 'MILLPARK' in line:
            continue
        transaction_lines.append(line)
    
    # Join the transaction lines
    full_text = ' '.join(transaction_lines)
    
    if not full_text.strip():
        continue
    
    # Extract all amounts (decimal numbers)
    amounts = re.findall(r'(\d+(?:\.\d{2})?)', full_text)
    
    # Clean description - remove amounts and codes
    desc = re.sub(r'IE\d{24}', '', full_text)
    desc = re.sub(r'V\d+NA', '', desc)
    desc = re.sub(r'VD[PC]-', '', desc)
    desc = re.sub(r'\*MOBI\s+', '', desc)
    desc = re.sub(r'D/D\s+', '', desc)
    desc = re.sub(r'LN\s+\d+', '', desc)
    desc = re.sub(r'TxnDate:\s+\d+\s*\w+\s*\d{4}', '', desc)
    desc = re.sub(r'Fee-QTR\s+TO\s+\d+\w+\d{2}', '', desc)
    desc = re.sub(r'\d+(?:\.\d{2})?', '', desc)  # Remove all numbers
    desc = re.sub(r'\s+', ' ', desc).strip()
    desc = desc[:100]
    
    # Get amount (first found number)
    amount = amounts[0] if amounts else ''
    
    # Skip empty or useless descriptions
    if desc and len(desc) > 3 and 'Interest' not in desc and 'Lending' not in desc and 'BALANCE' not in desc:
        transactions.append({
            'Date': date_str,
            'Description': desc,
            'Amount (€)': amount
        })

# Write to CSV
output_file = 'data/AIB_account_cleaned.csv'
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Date', 'Description', 'Amount (€)'])
    writer.writeheader()
    for trans in transactions:
        writer.writerow(trans)

print(f"✓ AIB account cleaned and converted to CSV")
print(f"✓ File saved: {output_file}")
print(f"✓ Total transactions extracted: {len(transactions)}")

if transactions:
    print(f"\n--- First 15 Transactions ---")
    for trans in transactions[:15]:
        print(f"  {trans['Date']} | {trans['Description'][:45]:<45} | €{trans['Amount (€)']}")
    
    # Summary
    try:
        total = sum(float(t['Amount (€)']) for t in transactions if t['Amount (€)'])
        print(f"\n--- SUMMARY ---")
        print(f"Total Amount: €{total:,.2f}")
        print(f"Number of transactions: {len(transactions)}")
    except Exception as e:
        print(f"Error calculating summary: {e}")
