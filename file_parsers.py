"""
File parsers for CSV, Excel, and PDF bank statements.
Converts various file formats into standardized DataFrames.
"""
import pandas as pd
import pdfplumber
from io import BytesIO


def parse_csv(file_content):
    """Parse CSV file content into DataFrame."""
    return pd.read_csv(BytesIO(file_content))


def parse_excel(file_content):
    """Parse Excel file content into DataFrame."""
    return pd.read_excel(BytesIO(file_content))


def parse_pdf_transactions(file_content):
    """
    Parse PDF bank statement into transactions DataFrame.
    This is a basic parser that extracts tables from PDF.
    
    Expected DataFrame columns: date, description, amount, type, category
    
    Note: PDF parsing is complex and depends on bank statement format.
    This implementation tries to extract tables and assumes common formats.
    You may need to customize this for specific bank statement layouts.
    """
    transactions = []
    
    with pdfplumber.open(BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            # Try to extract tables
            tables = page.extract_tables()
            
            if tables:
                for table in tables:
                    # Skip header row if present
                    for row in table[1:] if len(table) > 1 else table:
                        if not row or len(row) < 3:
                            continue
                        
                        # Try to parse common bank statement formats
                        # Format 1: [Date, Description, Debit, Credit, Balance]
                        # Format 2: [Date, Description, Amount, Type]
                        # Format 3: [Date, Reference, Description, Amount]
                        
                        try:
                            # Assume: date in first column, description in middle, amount somewhere
                            date = row[0] if row[0] else None
                            description = row[1] if len(row) > 1 else 'Unknown'
                            
                            # Try to find amount (look for numeric values)
                            amount = None
                            transaction_type = 'expense'
                            
                            for cell in row[2:]:
                                if cell and isinstance(cell, (str, float)):
                                    try:
                                        # Clean and parse amount
                                        amount_str = str(cell).replace(',', '').replace('€', '').replace('$', '').strip()
                                        if amount_str and amount_str != '':
                                            parsed = float(amount_str)
                                            if parsed != 0:
                                                amount = abs(parsed)
                                                # Negative usually means expense, positive means income
                                                transaction_type = 'expense' if parsed < 0 else 'income'
                                                break
                                    except (ValueError, AttributeError):
                                        continue
                            
                            if date and amount:
                                transactions.append({
                                    'date': date,
                                    'description': description,
                                    'amount': amount,
                                    'type': transaction_type,
                                    'category': 'Uncategorized'
                                })
                        except Exception:
                            continue
    
    if not transactions:
        # If table extraction failed, try text extraction (fallback)
        # This is very basic and may need customization
        raise ValueError(
            "Could not extract transaction data from PDF. "
            "Please ensure the PDF contains a transaction table, "
            "or convert to CSV/Excel format for better compatibility."
        )
    
    return pd.DataFrame(transactions)


def parse_pdf_accounts(file_content):
    """
    Parse PDF into accounts DataFrame.
    Expected columns: account_name, type, balance
    
    This is simplified - most PDFs contain transactions, not account summaries.
    """
    accounts = []
    
    with pdfplumber.open(BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            # Look for account summary information
            text = page.extract_text()
            
            # Try to find balance information (very basic)
            if 'balance' in text.lower() or 'total' in text.lower():
                lines = text.split('\n')
                for line in lines:
                    if 'balance' in line.lower() or 'total' in line.lower():
                        try:
                            # Very basic extraction - customize based on your PDF format
                            parts = line.split()
                            for part in parts:
                                try:
                                    balance = float(part.replace(',', '').replace('€', '').replace('$', ''))
                                    accounts.append({
                                        'account_name': 'Main Account',
                                        'type': 'checking',
                                        'balance': balance
                                    })
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            continue
    
    if not accounts:
        # Return default account structure if not found
        accounts.append({
            'account_name': 'Imported from PDF',
            'type': 'checking',
            'balance': 0.0
        })
    
    return pd.DataFrame(accounts)


def parse_file(file_content, filename, file_type='transactions'):
    """
    Parse file based on extension.
    
    Args:
        file_content: Raw file bytes
        filename: Original filename to detect extension
        file_type: 'transactions' or 'accounts'
    
    Returns:
        pandas DataFrame with parsed data
    """
    filename_lower = filename.lower()
    
    try:
        if filename_lower.endswith('.csv'):
            return parse_csv(file_content)
        elif filename_lower.endswith(('.xlsx', '.xls')):
            return parse_excel(file_content)
        elif filename_lower.endswith('.pdf'):
            if file_type == 'transactions':
                return parse_pdf_transactions(file_content)
            else:
                return parse_pdf_accounts(file_content)
        else:
            raise ValueError(f"Unsupported file format: {filename}")
    except Exception as e:
        raise ValueError(f"Error parsing {filename}: {str(e)}")
