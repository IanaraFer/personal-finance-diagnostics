"""
File parsers for CSV, Excel, PDF, JSON, and TXT bank statements.
Converts various file formats into standardized DataFrames.
"""
import pandas as pd
import pdfplumber
from io import BytesIO
import json
import re
import numpy as np


def parse_csv(file_content):
    """Parse CSV file content into DataFrame with robust encoding/separator handling."""
    last_error = None
    # Try multiple encodings and let pandas infer the delimiter when possible
    for encoding in ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1', 'iso-8859-1']:
        try:
            # sep=None triggers automatic delimiter inference; engine='python' required for sep=None
            return pd.read_csv(
                BytesIO(file_content),
                sep=None,
                engine='python',
                encoding=encoding,
                encoding_errors='replace'
            )
        except UnicodeDecodeError as e:
            last_error = e
            continue
        except Exception as e:
            # Keep trying other encodings; capture last error for context
            last_error = e
            continue

    # Try common Excel CSV variants (semicolon separator, different encodings)
    for sep in [';', '\t', '|']:
        for encoding in ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1', 'iso-8859-1']:
            try:
                return pd.read_csv(
                    BytesIO(file_content),
                    sep=sep,
                    engine='python',
                    encoding=encoding,
                    encoding_errors='replace'
                )
            except Exception:
                continue

    # If all CSV attempts fail, try parsing as Excel (sometimes files are misnamed)
    try:
        return parse_excel(file_content)
    except Exception:
        pass

    # Final fallback: try default comma with most lenient encoding
    try:
        return pd.read_csv(
            BytesIO(file_content),
            sep=',',
            engine='python',
            encoding='latin-1',
            encoding_errors='replace'
        )
    except Exception as e:
        raise ValueError(f"CSV parsing failed: {str(last_error or e)}")


def parse_excel(file_content):
    """Parse Excel file content into DataFrame with sheet and header detection."""
    bio = BytesIO(file_content)
    # Try reading all sheets first
    try:
        sheets = pd.read_excel(bio, sheet_name=None, engine='openpyxl', header=None)
    except Exception:
        # Fallback without specifying engine
        bio.seek(0)
        sheets = pd.read_excel(bio, sheet_name=None, header=None)

    # Pick the sheet that looks most like transactions (most columns/rows)
    candidate_df = None
    max_score = -1
    for name, df in sheets.items():
        # Score: rows * cols
        score = (len(df.index)) * (len(df.columns))
        if score > max_score:
            max_score = score
            candidate_df = df

    if candidate_df is None:
        # As a last resort, read the first sheet normally
        bio.seek(0)
        return pd.read_excel(bio)

    # Detect header row by scanning first 15 rows for likely column names
    def _norm(s):
        return ''.join(ch if ch.isalnum() else '_' for ch in str(s).strip().lower())

    likely_cols = {
        'date','transaction_date','transactiondate','posted_date','post_date','postingdate',
        'valuedate','value_date','datetime','date_time','description','details','narrative',
        'memo','reference','amount','debit','credit','money_in','money_out','deposit','withdrawal',
        'value','transaction_amount','dr_cr','dc'
    }

    header_row_idx = None
    scan_limit = min(15, len(candidate_df.index))
    for i in range(scan_limit):
        row_vals = candidate_df.iloc[i].tolist()
        normalized = [_norm(v) for v in row_vals]
        if any(col in likely_cols for col in normalized):
            header_row_idx = i
            break

    if header_row_idx is not None:
        # Use detected header row
        candidate_df.columns = [_norm(v) for v in candidate_df.iloc[header_row_idx].tolist()]
        candidate_df = candidate_df.iloc[header_row_idx+1:].reset_index(drop=True)
    else:
        # Fallback: use first row as header
        candidate_df.columns = [_norm(v) for v in candidate_df.iloc[0].tolist()]
        candidate_df = candidate_df.iloc[1:].reset_index(drop=True)

    # Drop completely empty columns
    candidate_df = candidate_df.dropna(axis=1, how='all')
    # Remove columns named like 'unnamed' (typical Excel artifacts)
    candidate_df = candidate_df[[c for c in candidate_df.columns if not str(c).startswith('unnamed')]]

    return candidate_df


def parse_json(file_content):
    """Parse JSON file content into DataFrame."""
    try:
        data = json.loads(file_content.decode('utf-8'))
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            # Check for common data structures
            if 'transactions' in data and isinstance(data['transactions'], list):
                return pd.DataFrame(data['transactions'])
            elif 'data' in data and isinstance(data['data'], list):
                return pd.DataFrame(data['data'])
            else:
                return pd.DataFrame([data])
        else:
            raise ValueError("JSON must contain list or dict with transaction data")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")


def parse_txt(file_content):
    """Parse TXT file content into DataFrame."""
    # Try to parse as tab or pipe-separated values
    try:
        content = file_content.decode('utf-8')
        # Try different separators
        for separator in ['\t', '|', ',', ' ']:
            try:
                df = pd.read_csv(BytesIO(content.encode()), sep=separator)
                if len(df.columns) > 1:  # Ensure we got multiple columns
                    return df
            except:
                continue
        # If no separator worked, try as CSV with flexible parsing
        return pd.read_csv(
            BytesIO(file_content),
            sep=None,
            engine='python',
            encoding='utf-8',
            encoding_errors='replace'
        )
    except Exception as e:
        raise ValueError(f"Could not parse TXT file: {str(e)}")


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
        elif filename_lower.endswith('.json'):
            return parse_json(file_content)
        elif filename_lower.endswith('.txt'):
            return parse_txt(file_content)
        else:
            raise ValueError(f"Unsupported file format: {filename}")
    except Exception as e:
        raise ValueError(f"Error parsing {filename}: {str(e)}")


# --- Heuristic transaction column inference ---
def _norm_col(name):
    return ''.join(ch if ch.isalnum() else '_' for ch in str(name).strip().lower())

def _clean_amount_str(v: str) -> str:
    if v is None:
        return ''
    s = str(v).strip()
    if not s or s.lower() in ('nan', 'none', 'null'):
        return ''
    neg = False
    # Parentheses indicate negative
    if re.match(r"^\(.*\)$", s):
        neg = True
        s = s[1:-1]
    # Remove currency symbols and spaces/non-breaking spaces
    s = s.replace('\u00a0', '').replace(' ', '')
    s = re.sub(r"[€$£]", "", s)
    # Handle decimal comma
    if s.count(',') == 1 and s.count('.') == 0:
        s = s.replace(',', '.')
    else:
        # Remove thousand separators
        s = s.replace(',', '')
    try:
        val = float(s)
        if neg:
            val = -val
        return str(val)
    except Exception:
        return ''

def _to_numeric(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).map(_clean_amount_str)
    return pd.to_numeric(cleaned, errors='coerce')

def infer_transaction_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a loosely parsed table (e.g., col1..colN), try to infer standard
    transaction columns: date, description, amount, type, category.
    Returns a new DataFrame with best-effort mappings added/renamed.
    """
    if df is None or df.empty:
        return df
    # Normalize column names
    df = df.copy()
    df.columns = [_norm_col(c) for c in df.columns]

    cols = set(df.columns)

    # Date detection
    if 'date' not in cols:
        best_col = None
        best_hits = -1
        for c in df.columns:
            try:
                # Try two parses: month/day-first and day-first
                s = df[c].astype(str)
                d1 = pd.to_datetime(s, errors='coerce', dayfirst=False, infer_datetime_format=True)
                d2 = pd.to_datetime(s, errors='coerce', dayfirst=True, infer_datetime_format=True)
                hits = max(d1.notna().sum(), d2.notna().sum())
                if hits > best_hits and hits >= max(3, int(0.2*len(df))):
                    best_hits = hits
                    best_col = c
            except Exception:
                continue
        if best_col:
            s = df[best_col].astype(str)
            d1 = pd.to_datetime(s, errors='coerce', dayfirst=False, infer_datetime_format=True)
            d2 = pd.to_datetime(s, errors='coerce', dayfirst=True, infer_datetime_format=True)
            date_series = d1
            if d2.notna().sum() > d1.notna().sum():
                date_series = d2
            df['date'] = date_series
            cols.add('date')

    # Amount detection
    if 'amount' not in cols:
        # Handle paired debit/credit and money in/out with synonyms first
        if {'debit', 'credit'}.issubset(cols):
            df['amount'] = _to_numeric(df['credit']).fillna(0) - _to_numeric(df['debit']).fillna(0)
        elif {'money_in', 'money_out'}.issubset(cols):
            df['amount'] = _to_numeric(df['money_in']).fillna(0) - _to_numeric(df['money_out']).fillna(0)
        elif {'moneyin', 'moneyout'}.issubset(cols):
            df['amount'] = _to_numeric(df['moneyin']).fillna(0) - _to_numeric(df['moneyout']).fillna(0)
        elif {'credit_amount', 'debit_amount'}.issubset(cols):
            df['amount'] = _to_numeric(df['credit_amount']).fillna(0) - _to_numeric(df['debit_amount']).fillna(0)
        elif {'cr_amount', 'dr_amount'}.issubset(cols):
            df['amount'] = _to_numeric(df['cr_amount']).fillna(0) - _to_numeric(df['dr_amount']).fillna(0)
        elif {'deposit', 'withdrawal'}.issubset(cols):
            df['amount'] = _to_numeric(df['deposit']).fillna(0) - _to_numeric(df['withdrawal']).fillna(0)
        else:
            # Scan for best numeric column candidate among generic cols
            best_col = None
            best_hits = -1
            for c in df.columns:
                if c in ('date', 'description', 'category', 'type'):
                    continue
                ser = _to_numeric(df[c])
                hits = ser.notna().sum()
                # Require some variation and at least a few numeric entries
                if hits > best_hits and hits >= max(3, int(0.2*len(df))) and ser.var(skipna=True) not in (None, 0, np.nan):
                    best_hits = hits
                    best_col = c
            if best_col:
                df['amount'] = _to_numeric(df[best_col])
        cols = set(df.columns)

    # Description detection
    if 'description' not in cols:
        # Prefer common names
        for alt in ['details', 'narrative', 'memo', 'reference', 'description1', 'transaction_description', 'text']:
            if alt in df.columns:
                df['description'] = df[alt]
                break
        if 'description' not in df.columns:
            # Heuristic: pick the non-numeric column with longest average length
            best_col = None
            best_len = -1
            for c in df.columns:
                if c in ('date', 'amount', 'type', 'category'):
                    continue
                sample = df[c].astype(str).fillna('')
                # Skip columns that are predominantly numeric
                if _to_numeric(sample).notna().mean() > 0.7:
                    continue
                avg_len = sample.map(len).mean()
                if avg_len > best_len:
                    best_len = avg_len
                    best_col = c
            if best_col:
                df['description'] = df[best_col]
        if 'description' not in df.columns:
            df['description'] = 'Unknown'
        cols = set(df.columns)

    # Type detection
    if 'type' not in cols:
        if 'dc' in df.columns:
            df['type'] = df['dc'].astype(str).str.upper().map({'C': 'income', 'CR': 'income', 'D': 'expense', 'DR': 'expense'})
        elif 'dr_cr' in df.columns:
            df['type'] = df['dr_cr'].astype(str).str.upper().map({'CR': 'income', 'DR': 'expense'})
        elif 'amount' in df.columns:
            df['type'] = _to_numeric(df['amount']).fillna(0).apply(lambda x: 'income' if x > 0 else 'expense')
        cols = set(df.columns)

    # Category default
    if 'category' not in cols:
        df['category'] = 'Uncategorized'

    return df
