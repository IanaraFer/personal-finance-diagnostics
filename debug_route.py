import sys, time, traceback
sys.path.insert(0, '.')
import requests

s = requests.Session()
r = s.post('http://127.0.0.1:5001/login',
    data={'email': 'admin@local.test', 'password': 'Admin1234!'},
    allow_redirects=True)
print('Login:', r.url, r.status_code)

# Check the file list endpoint first
r2 = s.get('http://127.0.0.1:5001/clients/Ianara', timeout=10)
print('Client page:', r2.status_code)
import re
# Extract error
m = re.search(r'alert alert-error[^>]*>(.*?)</div>', r2.text, re.DOTALL)
print('Error on files page:', m.group(1).strip() if m else 'none')

# Check if file exists via internal API
import client_manager
path = client_manager.get_client_file_path('Ianara', 'Ianara_account-statement_2025-01-01_2025-12-31_en-ie_e4d161_20260625_113739.pdf')
import os
print('File path:', path)
print('File exists:', os.path.isfile(path) if path else 'path is None')

# Now hit the analyze route and get the error
print('\nHitting analyze route...')
t0 = time.time()
r3 = s.get('http://127.0.0.1:5001/clients/Ianara/analyze/Ianara_account-statement_2025-01-01_2025-12-31_en-ie_e4d161_20260625_113739.pdf', timeout=120)
print(f'Status: {r3.status_code}, time: {time.time()-t0:.1f}s')

body = r3.text
m = re.search(r'alert alert-error[^>]*>(.*?)</div>', body, re.DOTALL)
if m:
    print('ERROR:', m.group(1).strip())
elif 'Stored Files' in body:
    print('SHOWS FILES PAGE (no error message shown) - first redirect hit (path not found?)')
elif 'dashboard' in body.lower() or 'income' in body.lower():
    print('SUCCESS: Dashboard loaded')
else:
    print('Unknown response, title contains:', re.search(r'<title>(.*?)</title>', body, re.DOTALL))
