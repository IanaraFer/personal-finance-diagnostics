"""Convert bank statement PDF to CSV format."""
import pdfplumber
import pandas as pd
import sys
import re
from datetime import datetime

def parse_bank_statement_pdf(pdf_path):
    """Parse bank statement PDF and extract transactions."""
    transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Processing {len(pdf.pages)} pages...")
        
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"\nPage {page_num}:")
            
            # Extract tables
            tables = page.extract_tables()
            
            if not tables:
                # Try text extraction if no tables
                text = page.extract_text()
                print("No tables found, using text extraction...")
                print(text[:500])
                continue
            
            for table_idx, table in enumerate(tables):
                print(f"  Table {table_idx + 1}: {len(table)} rows")
                
                # Skip empty tables
                if not table or len(table) < 2:
                    continue
                
                # Show header for debugging
                if table[0]:
                    print(f"  Header: {table[0]}")
                
                # Process rows (skip header)
                for row_idx, row in enumerate(table[1:], 1):
                    if not row or len(row) < 3:
                        continue
                    
                    # Try to identify date, description, amount pattern
                    date_str = None
                    description = ""
                    amount = None
                    
                    for cell in row:
                        if not cell or cell.strip() == "":
                            continue
                        
                        cell = str(cell).strip()
                        
                        # Check if cell looks like a date
                        if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', cell):
                            date_str = cell
                        # Check if cell looks like an amount
                        elif re.match(r'[-+]?[\d,]+\.\d{2}', cell):
                            try:
                                amount = float(cell.replace(',', ''))
                            except:
                                pass
                        # Otherwise it's probably description
                        else:
                            if description:
                                description += " " + cell
                            else:
                                description = cell
                    
                    # If we found date and amount, add transaction
                    if date_str and amount is not None:
                        transaction_type = 'expense' if amount < 0 else 'income'
                        transactions.append({
                            'date': date_str,
                            'description': description,
                            'amount': abs(amount),
                            'type': transaction_type,
                            'category': 'Uncategorized'
                        })
                        
                        if row_idx <= 3:  # Show first few
                            print(f"    Transaction: {date_str} | {description[:30]} | {amount}")
    
    return transactions

if __name__ == "__main__":
    pdf_path = r"c:\Users\35387\Downloads\account-statement_2025-01-01_2025-11-27_en-ie_b8eae1.pdf"
    output_csv = r"c:\Users\35387\Desktop\contabil\data\transactions_from_pdf.csv"
    
    print(f"Converting PDF: {pdf_path}")
    print("=" * 60)
    
    transactions = parse_bank_statement_pdf(pdf_path)
    
    print("\n" + "=" * 60)
    print(f"Extracted {len(transactions)} transactions")
    
    if transactions:
        df = pd.DataFrame(transactions)
        df.to_csv(output_csv, index=False)
        print(f"\nSaved to: {output_csv}")
        print("\nFirst 5 transactions:")
        print(df.head())
        print("\nColumn names:", list(df.columns))
    else:
        print("\nNo transactions found. The PDF might have a different format.")
        print("Please check the debug output above to see what was extracted.")
