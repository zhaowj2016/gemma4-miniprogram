import urllib.request
import json
import os

api_key = open(r'E:\file+desktop\gemma_key.txt', encoding='utf-8-sig').read().strip().split('=', 1)[-1].strip('"\'')
url = f'https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent?key={api_key}'
data = {
    'contents': [{'parts': [{'text': 'Write a 1000 word essay about the ocean.'}]}],
    'generationConfig': {'maxOutputTokens': 8192}
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req) as response:
        res = response.read().decode('utf-8')
        result = json.loads(res)
        print('finishReason:', result['candidates'][0]['finishReason'])
        print('length:', len(result['candidates'][0]['content']['parts'][0]['text']))
except Exception as e:
    print('Error:', e)
