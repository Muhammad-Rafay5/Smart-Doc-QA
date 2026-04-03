import os, requests, tempfile
path = os.path.join(tempfile.gettempdir(), 'copilot_test_doc.txt')
with open(path, 'w', encoding='utf-8') as f:
    f.write('This is a test document to verify upload pipeline.\n' * 20)
print('temp file', path, 'exists', os.path.exists(path))
url = 'http://127.0.0.1:8000/documents/upload-document'
with open(path, 'rb') as f:
    files = {'file': ('copilot_test_doc.txt', f, 'text/plain')}
    r = requests.post(url, files=files)
print('upload status', r.status_code)
print('upload body', r.text)
r2 = requests.get('http://127.0.0.1:8000/documents/')
print('list status', r2.status_code)
print('list body', r2.text)
