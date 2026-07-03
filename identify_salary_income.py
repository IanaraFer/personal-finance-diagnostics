import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path("cliente_files/Ianara")
SRC = BASE / "combined_transactions_chronological.csv"
OUT_TX = BASE / "salary_income_transactions_identified.csv"
OUT_MONTH = BASE / "salary_income_monthly_totals.csv"


def parse_date(date_iso: str):
    try:
        return datetime.strptime(date_iso, "%Y-%m-%d")
    except Exception:
        return None


def parse_float(x: str):
    try:
        return float(x)
    except Exception:
        return None


def infer_transfer_from_amount(raw_body: str, fallback_amount: str):
    # OCR text often concatenates amount+balance like: 600108.23 (= amount 600 + balance 108.23)
    raw = (raw_body or "").strip()
    m = re.search(r"(\d+)\.(\d{2})$", raw)
    if m:
        int_part = m.group(1)
        # Try splits where the tail is balance integer part (2-4 digits)
        for bal_digits in (2, 3, 4):
            if len(int_part) <= bal_digits:
                continue
            amount_s = int_part[:-bal_digits]
            bal_s = int_part[-bal_digits:]
            amount = int(amount_s)
            bal_int = int(bal_s)
            if 50 <= amount <= 5000 and 0 <= bal_int <= 2500 and amount % 50 == 0:
                return float(amount)
    # If OCR line is simple (e.g., ...1100), keep numeric fallback if available
    f = parse_float(fallback_amount)
    if f is not None:
        # Some parsed values come inflated by malformed split; use as-is only for small values
        if -10000 < f < 10000:
            return f
    digits = re.findall(r"\d+", raw)
    if digits:
        val = int(digits[-1])
        if 50 <= val <= 5000:
            return float(val)
    return None


rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
identified = []
monthly = defaultdict(lambda: {"transfer_from": 0.0, "government_v16517943": 0.0, "total": 0.0})

for r in rows:
    date_iso = (r.get("date_iso") or "").strip()
    dt = parse_date(date_iso)
    if dt is None:
        continue

    source = (r.get("source") or "").strip()
    desc = (r.get("description") or "").strip()
    typ = (r.get("type") or "").strip()

    group = None
    amount = None

    if desc.startswith("Transfer from "):
        group = "transfer_from"
        if source == "revolut_text":
            amount = infer_transfer_from_amount(r.get("raw_body", ""), r.get("amount", ""))
        else:
            amount = parse_float(r.get("amount", ""))

    elif desc.startswith("V16517943"):
        group = "government_v16517943"
        amount = parse_float(r.get("amount", ""))

    if group is None:
        continue

    if amount is None:
        continue

    month = dt.strftime("%Y-%m")
    monthly[month][group] += amount
    monthly[month]["total"] += amount

    identified.append(
        {
            "date": r.get("date", ""),
            "date_iso": date_iso,
            "month": month,
            "source": source,
            "type": typ,
            "income_group": group,
            "description": desc,
            "amount_identified": f"{amount:.2f}",
            "amount_raw": r.get("amount", ""),
            "raw_body": r.get("raw_body", ""),
        }
    )

identified.sort(key=lambda x: (x["date_iso"], x["income_group"], x["description"]))

with OUT_TX.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(
        f,
        fieldnames=[
            "date",
            "date_iso",
            "month",
            "source",
            "type",
            "income_group",
            "description",
            "amount_identified",
            "amount_raw",
            "raw_body",
        ],
    )
    w.writeheader()
    w.writerows(identified)

month_rows = []
for m in sorted(monthly.keys()):
    tf = monthly[m]["transfer_from"]
    gv = monthly[m]["government_v16517943"]
    tot = monthly[m]["total"]
    month_rows.append(
        {
            "month": m,
            "transfer_from_total": f"{tf:.2f}",
            "government_v16517943_total": f"{gv:.2f}",
            "monthly_income_total": f"{tot:.2f}",
        }
    )

with OUT_MONTH.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(
        f,
        fieldnames=["month", "transfer_from_total", "government_v16517943_total", "monthly_income_total"],
    )
    w.writeheader()
    w.writerows(month_rows)

print(f"Identified income rows: {len(identified)}")
print(f"Months summarized: {len(month_rows)}")
print(f"Transactions file: {OUT_TX}")
print(f"Monthly totals file: {OUT_MONTH}")
