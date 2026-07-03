import csv, re
from pathlib import Path

p = Path('cliente_files/Ianara/transactions_from_text_2026.csv')
rows = list(csv.DictReader(p.open(encoding='utf-8')))

transfer_from = []
for r in rows:
    t = (r.get('type') or '').strip()
    desc = (r.get('description') or '').strip()
    raw = (r.get('raw_body') or '').strip()
    if t == 'Transfer' and desc.startswith('Transfer from '):
        name = desc.replace('Transfer from ', '', 1).strip()
        m = re.search(r'^(.*?)(-?\d+(?:\.\d{1,2})?)(-?\d+\.\d{2})$', raw)
        amount = None
        if m:
            try:
                amount = float(m.group(2))
            except Exception:
                amount = None
        transfer_from.append({'date': r.get('date',''), 'name': name, 'amount': amount, 'raw': raw})

seen = set()
unique = []
for x in transfer_from:
    k = (x['date'], x['name'], x['raw'])
    if k in seen:
        continue
    seen.add(k)
    unique.append(x)

valid_amounts = [x['amount'] for x in unique if isinstance(x['amount'], float)]
print(f'Transfer from rows: {len(unique)}')
print(f'Total amount (parsed): {sum(valid_amounts):.2f}')
print('--- FIRST 40 TRANSFER FROM ---')
for x in unique[:40]:
    amt = '' if x['amount'] is None else f"{x['amount']:.2f}"
    print(f"{x['date']} | {x['name']} | {amt}")

service_keywords = ['STRIPE', 'GOOGLE PAYMENT', 'XENEO']
service_rows = []
for r in rows:
    typ = (r.get('type') or '').strip()
    desc = (r.get('description') or '').strip()
    if typ in ('Topup','Transfer') and ('Payment from ' in desc or 'Transfer from ' in desc):
        u = desc.upper()
        if any(k in u for k in service_keywords):
            raw = (r.get('raw_body') or '').strip()
            m = re.search(r'^(.*?)(-?\d+(?:\.\d{1,2})?)(-?\d+\.\d{2})$', raw)
            amt = None
            if m:
                try:
                    amt = float(m.group(2))
                except Exception:
                    amt = None
            service_rows.append((r.get('date',''), typ, desc, amt))

print('--- POSSIBLE SERVICE PAYMENTS ---')
for d,t,desc,amt in service_rows:
    a = '' if amt is None else f"{amt:.2f}"
    print(f"{d} | {t} | {desc} | {a}")
