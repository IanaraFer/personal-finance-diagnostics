import re
import csv
from pathlib import Path

SRC = Path('data/aibaccount.txt')
OUT = Path('data/aibaccount_clean.csv')

# Patterns
date_re = re.compile(r'^(\d{1,2} \w{3} \d{4})\s+(.*)$')
amount_re = re.compile(r'(-?\d+\.\d{2})')

# Lines to skip (headers/footers/noise)
skip_prefixes = [
    'Thisisaneligible', 'This is an eligible', 'Deposit Guarantee',
    'ForImportantInformation', 'For Important Information',
    'Thank you for banking', 'AlliedIrishBanks', 'Allied Irish Banks',
    'Personal Bank Account', 'Statement of Account', 'Branch', 'National Sort Code',
    'Telephone', 'Page Number', 'Account Name', 'Account Number',
    'Date of Statement', 'Forward', 'IBAN:', 'Authorised Limit', 'Date', 'Details',
    'Overdrawn balances', 'www.aib.ie', 'IBAN', 'BIC:',
]

# Heuristic to mark debit/credit based on description
DEBIT_HINTS = [
    'D/D', 'VDC-', 'WITHDRAWAL', 'FEE', 'eFlow', 'Electric', 'THREE IRELAND',
    'VIRGIN MEDIA', 'CLUBWISE', 'ROYAL LONDON', 'Netflix', 'NETFLIX', 'Circle K',
]
CREDIT_HINTS = [
    'HAP', 'Revolut', 'IE', 'V165', 'IANARA ARAUJO', 'BALANCE FORWARD'
]


def classify_type(desc: str) -> str:
    d = desc.upper()
    if any(h.upper() in d for h in DEBIT_HINTS):
        return 'debit'
    if any(h.upper() in d for h in CREDIT_HINTS):
        return 'credit'
    return 'unknown'


def clean_line_text(txt: str) -> str:
    # Fix common broken words
    return (
        txt.replace('Electric Irela', 'Electric Ireland')
           .replace('MOBI CARD IANAR', 'MOBI CARD IANARA')
           .replace('VDP-Netflix.com', 'VDP-NETFLIX.COM')
           .replace('VDP-NETFLIX INTERN', 'VDP-NETFLIX.COM')
           .replace('VDC-DUNNES CLONDAL', 'VDC-DUNNES CLONDALKIN')
           .replace('VDC-CIRCLE K NEWLA', 'VDC-CIRCLE K NEWLANDS')
           .replace('VDC-CLONDALKIN SER', 'VDC-CLONDALKIN SERVICES')
           .replace('VDC-LIDL DUBLIN -', 'VDC-LIDL DUBLIN ')
    )


def parse_records(lines):
    records = []
    current_date = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        # Skip obvious headers/footers
        if any(line.startswith(p) for p in skip_prefixes):
            continue
        # Capture date header
        m = date_re.match(line)
        if m:
            current_date, rest = m.group(1), m.group(2)
            # If rest already has amounts, record it
            nums = [float(x) for x in amount_re.findall(rest)]
            desc = clean_line_text(rest)
            if 'BALANCE FORWARD' in desc and nums:
                records.append({
                    'Date': current_date,
                    'Description': 'BALANCE FORWARD',
                    'Amount': '',
                    'Balance': nums[-1],
                    'Type': 'balance'
                })
                continue
            if nums:
                # If two numbers, treat first as amount, last as balance
                amount = nums[0]
                balance = nums[-1] if len(nums) > 1 else ''
                t = classify_type(desc)
                records.append({
                    'Date': current_date,
                    'Description': desc,
                    'Amount': amount,
                    'Balance': balance,
                    'Type': t
                })
            else:
                # Just set current date; details may follow
                continue
            continue
        # Non-date lines within current date context
        nums = [float(x) for x in amount_re.findall(line)]
        desc = clean_line_text(line)
        if not nums and not current_date:
            # Ignore stray lines before any date is set
            continue
        if 'Debit €' in line or 'Credit €' in line or 'Balance €' in line:
            # Column headers broken out, skip
            continue
        if nums:
            amount = nums[0]
            balance = nums[-1] if len(nums) > 1 else ''
            t = classify_type(desc)
            records.append({
                'Date': current_date,
                'Description': desc,
                'Amount': amount,
                'Balance': balance,
                'Type': t
            })
        else:
            # detail only line without amount; skip
            continue
    return records


def main():
    lines = SRC.read_text(encoding='utf-8', errors='ignore').splitlines()
    records = parse_records(lines)

    # Write CSV
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['Date', 'Description', 'Amount', 'Balance', 'Type'])
        w.writeheader()
        for r in records:
            w.writerow(r)
    print(f"✓ Cleaned AIB data written to: {OUT}")
    print(f"✓ Rows: {len(records)}")


if __name__ == '__main__':
    main()
