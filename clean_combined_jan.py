import csv
from pathlib import Path

p = Path('cliente_files/Ianara/combined_transactions_chronological.csv')
rows = list(csv.DictReader(p.open(encoding='utf-8')))

# 1) Remove all 2025 rows
rows_2026 = [r for r in rows if not (r.get('date_iso', '').startswith('2025-') or r.get('date', '').endswith('/2025'))]

# 2) Remove repeated January rows (exact duplicates by business columns)
seen_jan = set()
cleaned = []
removed_jan_duplicates = 0
for r in rows_2026:
    d = r.get('date_iso', '')
    if d.startswith('2026-01-'):
        key = (
            r.get('date_iso', ''),
            r.get('source', ''),
            r.get('type', ''),
            r.get('description', ''),
            r.get('amount', ''),
            r.get('balance', ''),
        )
        if key in seen_jan:
            removed_jan_duplicates += 1
            continue
        seen_jan.add(key)
    cleaned.append(r)

with p.open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['date', 'date_iso', 'source', 'type', 'description', 'amount', 'balance', 'raw_body'])
    w.writeheader()
    w.writerows(cleaned)

print(f'original={len(rows)}')
print(f'after_remove_2025={len(rows_2026)}')
print(f'removed_january_duplicates={removed_jan_duplicates}')
print(f'final={len(cleaned)}')
