import sys, time
sys.path.insert(0, '.')

# Print which file is loaded
import file_parsers
print('file_parsers loaded from:', file_parsers.__file__)

# Check if pymupdf path is in the code
with open(file_parsers.__file__, 'r') as f:
    content = f.read()
if 'pymupdf' in content:
    print('pymupdf IS in file_parsers.py')
else:
    print('WARNING: pymupdf NOT in file_parsers.py - old code')

# Verify the new parser is actually there
if '_try_parse_revolut_pdf' in content:
    print('_try_parse_revolut_pdf IS in file')
    
# Time the parse
pdf_path = r'cliente_files\Ianara\Ianara_account-statement_2025-01-01_2025-12-31_en-ie_e4d161_20260625_113739.pdf'
with open(pdf_path, 'rb') as f:
    pdf_content = f.read()

t0 = time.time()
df = file_parsers.parse_file(pdf_content, 'test.pdf', file_type='transactions')
print(f'Parse time: {time.time()-t0:.1f}s, rows: {len(df)}')
