"""Convert Revolut bank statement PDF to CSV format."""
import pdfplumber
import pandas as pd
import re
from datetime import datetime

def parse_revolut_statement(pdf_path):
    """Parse Revolut bank statement PDF and extract transactions."""
    transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Processing {len(pdf.pages)} pages...")
        
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            
            if not text:
                continue
            
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                # Look for lines that start with a date pattern
                # Revolut format: "16 Mar 2025 Description €5.00 €82.90"
                match = re.match(r'(\d{1,2}\s+\w+\s+\d{4})\s+(.+)', line)
                
                if match:
                    date_str = match.group(1)
                    rest_of_line = match.group(2)
                    
                    # Find all euro amounts in the line
                    amounts = re.findall(r'€([\d,]+\.\d{2})', rest_of_line)
                    
                    if len(amounts) >= 2:
                        # Revolut format: Description Money_out Money_in Balance
                        # or: Description Money_in Balance
                        description_match = re.match(r'(.+?)\s*€', rest_of_line)
                        description = description_match.group(1).strip() if description_match else 'Unknown'
                        
                        # Determine transaction type and amount
                        # If there are 3 amounts, format is: money_out, money_in, balance
                        # If there are 2 amounts, format is: money_in/out, balance
                        if len(amounts) == 3:
                            money_out = float(amounts[0].replace(',', ''))
                            money_in = float(amounts[1].replace(',', ''))
                            
                            if money_out > 0:
                                amount = money_out
                                trans_type = 'expense'
                            else:
                                amount = money_in
                                trans_type = 'income'
                        elif len(amounts) == 2:
                            # Check if it's income or expense based on keywords
                            if any(word in description.lower() for word in ['from', 'to', 'interest', 'received', 'deposit']):
                                amount = float(amounts[0].replace(',', ''))
                                if 'from' in description.lower() or 'interest' in description.lower():
                                    trans_type = 'income'
                                else:
                                    trans_type = 'expense'
                            else:
                                amount = float(amounts[0].replace(',', ''))
                                trans_type = 'expense'
                        else:
                            continue
                        
                        # Categorize based on description
                        category = categorize_transaction(description)
                        
                        transactions.append({
                            'date': date_str,
                            'description': description,
                            'amount': amount,
                            'type': trans_type,
                            'category': category
                        })
                        
                        if page_num <= 2 and len(transactions) <= 10:
                            print(f"  {date_str} | {description[:40]:40} | €{amount:8.2f} | {trans_type}")
    
    return transactions

def categorize_transaction(description):
    """Categorize transaction based on description."""
    desc_lower = description.lower()
    
    if any(word in desc_lower for word in ['savings', 'vault', 'pocket']):
        return 'Savings'
    elif any(word in desc_lower for word in ['interest']):
        return 'Interest'
    elif any(word in desc_lower for word in ['atm', 'withdrawal']):
        return 'Cash Withdrawal'
    elif any(word in desc_lower for word in ['transfer', 'to', 'from']):
        return 'Transfer'
    elif any(word in desc_lower for word in ['holiday', 'travel']):
        return 'Travel'
    else:
        return 'Uncategorized'

if __name__ == "__main__":
    pdf_path = r"c:\Users\35387\Downloads\account-statement_2025-01-01_2025-11-27_en-ie_b8eae1.pdf"
    output_csv = r"c:\Users\35387\Desktop\contabil\data\transactions_from_pdf.csv"
    
    print(f"Converting Revolut PDF: {pdf_path}")
    print("=" * 80)
    
    transactions = parse_revolut_statement(pdf_path)
    
    print("\n" + "=" * 80)
    print(f"Extracted {len(transactions)} transactions")
    
    if transactions:
        df = pd.DataFrame(transactions)
        df.to_csv(output_csv, index=False)
        print(f"\nSaved to: {output_csv}")
        print(f"\nSummary:")
        print(f"  Total transactions: {len(df)}")
        print(f"  Date range: {df['date'].iloc[0]} to {df['date'].iloc[-1]}")
        print(f"  Total income: €{df[df['type']=='income']['amount'].sum():,.2f}")
        print(f"  Total expenses: €{df[df['type']=='expense']['amount'].sum():,.2f}")
        print(f"\nFirst 10 transactions:")
        print(df.head(10).to_string(index=False))
        print(f"\nCategories breakdown:")
        print(df.groupby(['category', 'type'])['amount'].sum().to_string())
    else:
        print("\nNo transactions found.")
