import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict

p = Path('cliente_files/Ianara/combined_transactions_chronological.csv')
rows = list(csv.DictReader(p.open(encoding='utf-8')))


def dt(x):
    try:
        return datetime.strptime(x, '%Y-%m-%d')
    except Exception:
        return None


def fl(x):
    try:
        return float(x)
    except Exception:
        return None

monthly = defaultdict(lambda: {'in': 0.0, 'out': 0.0, 'in_n': 0, 'out_n': 0})

for r in rows:
    d = dt(r.get('date_iso', ''))
    if not d:
        continue
    m = d.strftime('%Y-%m')
    src = (r.get('source') or '').strip()
    typ = (r.get('type') or '').strip()
    desc = (r.get('description') or '').strip()
    a = fl(r.get('amount', ''))
    if a is None:
        continue

    # Sanity cut for OCR-heavy combined table
    # Keep values in realistic transaction range
    if abs(a) > 5000:
        continue

    sign = None
    if src == 'aib_statement':
        if typ == 'credit':
            sign = 'in'
        elif typ == 'debit':
            sign = 'out'
    else:
        if desc.startswith('Transfer from '):
            sign = 'in'
        elif typ in ('Card Payment', 'Charge'):
            sign = 'out'
        elif typ == 'Card Refund':
            sign = 'in'
        elif typ == 'Topup':
            sign = 'in'
        elif typ == 'Transfer':
            if desc.startswith('From '):
                sign = 'in'
            elif desc.startswith('To '):
                sign = 'out'
            else:
                sign = 'in' if a > 0 else 'out'

    if sign is None:
        continue

    if sign == 'in':
        monthly[m]['in'] += abs(a)
        monthly[m]['in_n'] += 1
    else:
        monthly[m]['out'] += abs(a)
        monthly[m]['out_n'] += 1

for m in sorted(monthly):
    inc = monthly[m]['in']
    out = monthly[m]['out']
    print(f"{m}|in={inc:.2f}|out={out:.2f}|net={inc-out:.2f}|n_in={monthly[m]['in_n']}|n_out={monthly[m]['out_n']}")
