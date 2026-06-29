from file_parsers import parse_pdf_transactions

with open(r'cliente_files\Ianara\Ianara_account-statement_2025-01-01_2025-12-31_en-ie_e4d161_20260625_113739.pdf', 'rb') as f:
    content = f.read()

df = parse_pdf_transactions(content)
print(f'Total transactions: {len(df)}')
print(f'Columns: {list(df.columns)}')
print()
print('Type breakdown:')
print(df['type'].value_counts().to_string())
print()
print('Category breakdown:')
print(df['category'].value_counts().to_string())
print()
print('First 15 transactions:')
print(df.head(15).to_string(index=False))
print()
print(f'Total income:   EUR {df[df["type"]=="income"]["amount"].sum():.2f}')
print(f'Total expenses: EUR {df[df["type"]=="expense"]["amount"].sum():.2f}')
