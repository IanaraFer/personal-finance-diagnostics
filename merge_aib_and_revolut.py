import csv
import re
from datetime import datetime
from pathlib import Path

BASE = Path("cliente_files/Ianara")
AIB_TEXT = BASE / "aib_statement_parsed_text.txt"
AIB_CSV = BASE / "aib_statement_transactions.csv"
REVOLUT_CSV = BASE / "transactions_from_text_2026.csv"
COMBINED_CSV = BASE / "combined_transactions_chronological.csv"

MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

DATE_LINE_RE = re.compile(r"^(\d{1,2})\s([A-Za-z]{3})\s(\d{4})\s+(.*)$")

SKIP_PREFIXES = (
    "IANARA FERNANDES",
    "Personal Bank Account",
    "Statement of Account",
    "Date Details Debit",
    "Interest Rate",
    "Lending @",
    "This is an eligible",
    "For Important Information",
    "Thank you for banking",
    "Overdrawn balances",
    "Allied Irish Banks",
    "Branch",
    "National Sort Code",
    "Telephone",
    "Page Number",
    "Account Name",
    "Account Number",
    "Date of Statement",
    "Forward",
    "IBAN:",
    "Authorised Limit",
)


def normalize_date(d, mmm, y):
    return datetime(int(y), MONTHS[mmm.title()], int(d))


def parse_ddmmyyyy(s):
    parts = s.strip().split("/")
    if len(parts) != 3:
        return None
    d, m, y = parts
    if len(y) == 2:
        y = "20" + y
    try:
        return datetime(int(y), int(m), int(d))
    except ValueError:
        return None


def guess_direction(desc):
    upper = desc.upper()
    if upper.startswith("V165"):
        return "credit"
    if upper.startswith("IANARA ARAUJO FERN"):
        return "credit"
    if "FEE REFUND" in upper:
        return "credit"
    return "debit"


def parse_amounts(line):
    # Use decimal-looking values only to avoid tokens like 7025 in merchant names.
    decs = re.findall(r"-?\d+\.\d{2}", line)
    if not decs:
        return "", ""
    if len(decs) == 1:
        return decs[0], ""
    return decs[-2], decs[-1]


def clean_description(line):
    # Remove trailing decimal amounts from description.
    return re.sub(r"\s*-?\d+\.\d{2}(\s+-?\d+\.\d{2})?\s*$", "", line).strip()


def build_aib_csv():
    lines = [ln.strip() for ln in AIB_TEXT.read_text(encoding="utf-8", errors="ignore").splitlines()]
    rows = []
    current_date = None

    for ln in lines:
        if not ln:
            continue
        if ln.startswith("IE") and re.search(r"\d", ln):
            continue
        if ln.startswith("TxnDate:"):
            continue
        if any(ln.startswith(p) for p in SKIP_PREFIXES):
            continue

        m = DATE_LINE_RE.match(ln)
        if m:
            d, mmm, y, rest = m.groups()
            if mmm.title() not in MONTHS:
                continue
            current_date = normalize_date(d, mmm, y)
            ln = rest.strip()
            if not ln:
                continue

        if current_date is None:
            continue

        desc = clean_description(ln)
        amount, balance = parse_amounts(ln)

        # Keep balance forward lines as anchors.
        if "BALANCE FORWARD" in ln.upper():
            if not balance:
                balance = amount
                amount = ""
            rows.append(
                {
                    "date": current_date.strftime("%d/%m/%Y"),
                    "date_iso": current_date.strftime("%Y-%m-%d"),
                    "source": "aib_statement",
                    "type": "balance_forward",
                    "description": desc,
                    "amount": amount,
                    "balance": balance,
                    "raw_body": ln,
                }
            )
            continue

        if not amount and not balance:
            continue

        rows.append(
            {
                "date": current_date.strftime("%d/%m/%Y"),
                "date_iso": current_date.strftime("%Y-%m-%d"),
                "source": "aib_statement",
                "type": guess_direction(desc),
                "description": desc,
                "amount": amount,
                "balance": balance,
                "raw_body": ln,
            }
        )

    with AIB_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["date", "date_iso", "source", "type", "description", "amount", "balance", "raw_body"],
        )
        w.writeheader()
        w.writerows(rows)

    return rows


def load_revolut_rows():
    rows = []
    for r in csv.DictReader(REVOLUT_CSV.open(encoding="utf-8")):
        dt = parse_ddmmyyyy(r.get("date", ""))
        if dt is None:
            continue
        rows.append(
            {
                "date": dt.strftime("%d/%m/%Y"),
                "date_iso": dt.strftime("%Y-%m-%d"),
                "source": "revolut_text",
                "type": r.get("type", ""),
                "description": r.get("description", ""),
                "amount": r.get("amount", ""),
                "balance": r.get("balance", ""),
                "raw_body": r.get("raw_body", ""),
            }
        )
    return rows


def write_combined(aib_rows, revolut_rows):
    combined = aib_rows + revolut_rows
    combined.sort(key=lambda x: (x["date_iso"], x["source"], x["description"]))
    with COMBINED_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["date", "date_iso", "source", "type", "description", "amount", "balance", "raw_body"],
        )
        w.writeheader()
        w.writerows(combined)
    return combined


def main():
    aib_rows = build_aib_csv()
    revolut_rows = load_revolut_rows()
    combined = write_combined(aib_rows, revolut_rows)
    print(f"AIB rows: {len(aib_rows)}")
    print(f"Revolut rows: {len(revolut_rows)}")
    print(f"Combined rows: {len(combined)}")
    print(f"AIB CSV: {AIB_CSV}")
    print(f"Combined CSV: {COMBINED_CSV}")


if __name__ == "__main__":
    main()
