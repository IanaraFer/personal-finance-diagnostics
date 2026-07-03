import csv
import re
from pathlib import Path

raw = Path("raw_statement_input.txt").read_text(encoding="utf-8", errors="ignore")

# Keep only content starting from first known transaction token
m0 = re.search(r"(Transfer|Card Payment|Topup|Charge|Card Refund)\d{1,2}/\d{1,2}/(?:\d{4}|\d{2})", raw)
if not m0:
    raise SystemExit("No transactions found")
text = raw[m0.start():]

start_re = re.compile(r"(Transfer|Card Payment|Topup|Charge|Card Refund)(\d{1,2}/\d{1,2}/(?:\d{4}|\d{2}))")
amount_balance_re = re.compile(r"(-?\d+(?:\.\d{1,2})?)(-?\d+(?:\.\d{1,2})?)$")

matches = list(start_re.finditer(text))
rows = []
for i, m in enumerate(matches):
    typ = m.group(1)
    date = m.group(2)
    start = m.end()
    end = matches[i+1].start() if i + 1 < len(matches) else len(text)
    body = text[start:end].strip()

    desc = body
    amount = ""
    balance = ""

    mb = amount_balance_re.search(body)
    if mb:
        amount = mb.group(1)
        balance = mb.group(2)
        desc = body[:mb.start()].strip()

    rows.append({
        "type": typ,
        "date": date,
        "description": desc,
        "amount": amount,
        "balance": balance,
        "raw_body": body,
    })

out = Path("cliente_files") / "Ianara" / "transactions_from_text_2026.csv"
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["type", "date", "description", "amount", "balance", "raw_body"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {out}")
