import sys, time
sys.path.insert(0, '.')
import requests

s = requests.Session()
s.post('http://127.0.0.1:5001/login', data={'email': 'admin@local.test', 'password': 'Admin1234!'}, allow_redirects=True)

t0 = time.time()
r = s.get('http://127.0.0.1:5001/clients/Ianara/report/Ianara_account-statement_2025-01-01_2025-12-31_en-ie_e4d161_20260625_113739.pdf', timeout=30)
print(f'Report status: {r.status_code}, time: {time.time()-t0:.1f}s')
print('Content-Type:', r.headers.get('Content-Type'))
print('Content-Disposition:', r.headers.get('Content-Disposition'))
if r.status_code == 200 and 'text/plain' in r.headers.get('Content-Type',''):
    print('Report preview (first 500 chars):')
    print(r.text[:500])
else:
    print('Response body (first 500):', r.text[:500])
