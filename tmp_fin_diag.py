import csv
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

p = Path('cliente_files/Ianara/combined_transactions_chronological.csv')
rows = list(csv.DictReader(p.open(encoding='utf-8')))

INCOME_TRANSFER_FROM = 'Transfer from '
INCOME_GOV_PREFIX = 'V16517943'


def parse_date(s):
    try:
        return datetime.strptime(s, '%Y-%m-%d')
    except Exception:
        return None


def parse_float(x):
    try:
        return float(x)
    except Exception:
        return None


def infer_amount_from_raw(raw):
    raw = (raw or '').strip()
    m = re.search(r'^(.*?)(-?\d+(?:\.\d{1,2})?)(-?\d+\.\d{2})$', raw)
    if m:
        try:
            return float(m.group(2))
        except Exception:
            pass

    m2 = re.search(r'(\d+)\.(\d{2})$', raw)
    if m2:
        intpart = m2.group(1)
        dec = m2.group(2)
        for bal_digits in (2, 3, 4):
            if len(intpart) <= bal_digits:
                continue
            amount = int(intpart[:-bal_digits])
            bal_int = int(intpart[-bal_digits:])
            if 0 <= bal_int <= 3000 and 1 <= amount <= 20000:
                return float(amount)
    return None


monthly = defaultdict(lambda: {'in': 0.0, 'out': 0.0, 'in_n': 0, 'out_n': 0})
cat_month = defaultdict(lambda: defaultdict(float))

for r in rows:
    d = parse_date(r.get('date_iso', ''))
    if not d:
        continue

    month = d.strftime('%Y-%m')
    src = (r.get('source') or '').strip()
    typ = (r.get('type') or '').strip()
    desc = (r.get('description') or '').strip()
    raw = (r.get('raw_body') or '').strip()

    amount = None
    sign = None

    if src == 'aib_statement':
        a = parse_float(r.get('amount', ''))
        if a is None:
            continue
        amount = abs(a)
        if typ == 'credit':
            sign = 'in'
        elif typ == 'debit':
            sign = 'out'
        else:
            continue
    else:
        a = parse_float(r.get('amount', ''))
        ai = infer_amount_from_raw(raw)

        if desc.startswith(INCOME_TRANSFER_FROM):
            amount = abs(ai) if ai is not None else (abs(a) if a is not None else None)
            sign = 'in'
        elif desc.startswith(INCOME_GOV_PREFIX):
            amount = abs(ai) if ai is not None else (abs(a) if a is not None else None)
            sign = 'in'
        else:
            if typ in ('Card Payment', 'Charge'):
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
                    if a is not None and a < 0:
                        sign = 'out'
                    elif a is not None and a > 0:
                        sign = 'in'
            if sign is None:
                continue

            amount = abs(ai) if ai is not None else (abs(a) if a is not None else None)

    if amount is None:
        continue

    if sign == 'in':
        monthly[month]['in'] += amount
        monthly[month]['in_n'] += 1
    else:
        monthly[month]['out'] += amount
        monthly[month]['out_n'] += 1

    u = desc.upper()
    if sign == 'in':
        if desc.startswith('Transfer from '):
            cat = 'Entradas - Transfer from'
        elif desc.startswith('V16517943'):
            cat = 'Entradas - Governo'
        elif 'TOP-UP' in u or 'PAYMENT FROM' in u:
            cat = 'Entradas - Topup/Payment'
        else:
            cat = 'Entradas - Outras'
    else:
        if 'CIRCLE K' in u or 'GOCAR' in u or 'PARK' in u or 'RATP' in u or 'SNCF' in u or 'AIRPORT' in u:
            cat = 'Saidas - Transporte'
        elif 'LIDL' in u or 'DUNNES' in u or 'MR PRICE' in u or 'MCDONALD' in u or 'BURGER' in u or 'JUST EAT' in u:
            cat = 'Saidas - Alimentacao e Compras'
        elif 'NETFLIX' in u or 'NETLIFY' in u or 'CURSOR' in u or 'WIX' in u or 'STACKBLITZ' in u or 'GOOGLE PLAY' in u:
            cat = 'Saidas - Assinaturas/Apps'
        elif 'NAPS LOAN' in u or 'ROYAL LONDON' in u or 'STAMP DUTY' in u or 'FEE' in u:
            cat = 'Saidas - Dividas e Taxas'
        elif 'THEO' in u or 'RENT' in u:
            cat = 'Saidas - Familia/Habitacao'
        elif 'EMERGENCY FUNDO' in u or '50Y BDAY SAVING' in u or 'HOLIDAY' in u:
            cat = 'Saidas - Poupancas internas'
        else:
            cat = 'Saidas - Outras'

    cat_month[month][cat] += amount

print('MONTHLY_SUMMARY')
for m in sorted(monthly):
    inc = monthly[m]['in']
    out = monthly[m]['out']
    net = inc - out
    print(f"{m}|in={inc:.2f}|out={out:.2f}|net={net:.2f}|n_in={monthly[m]['in_n']}|n_out={monthly[m]['out_n']}")

print('TOP_CATEGORIES_BY_MONTH')
for m in sorted(cat_month):
    top = sorted(cat_month[m].items(), key=lambda x: x[1], reverse=True)[:5]
    joined = '; '.join([f"{k}:{v:.2f}" for k, v in top])
    print(f"{m}|{joined}")
