import urllib.request, urllib.parse

data = urllib.parse.urlencode({
    'email': 'newtest101@example.com',
    'password': 'TestPass123',
    'confirm_password': 'TestPass123',
    'plan': 'monthly'
}).encode()

req = urllib.request.Request('http://127.0.0.1:5001/register', data=data, method='POST')
req.add_header('Content-Type', 'application/x-www-form-urlencoded')

try:
    resp = urllib.request.urlopen(req)
    body = resp.read().decode()
    # Find error div
    start = body.find('class="error"')
    if start >= 0:
        print('ERROR DIV:', body[start:start+300])
    else:
        print('No error class found - status:', resp.status, 'url:', resp.url)
        start2 = body.find('<form')
        print('FORM AREA:', body[start2:start2+400])
except Exception as e:
    print('Exception:', type(e).__name__, e)
