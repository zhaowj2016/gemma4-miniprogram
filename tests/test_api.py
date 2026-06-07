import os
import json
import urllib.request
import urllib.error

desktop_path = r"E:\file+desktop\gemma_key.txt"
api_key = None
if os.path.exists(desktop_path):
    with open(desktop_path, "r", encoding="utf-8-sig") as f:
        content = f.read().strip()
        if "GEMMA_API_KEY=" in content:
            for line in content.split('\n'):
                if line.strip().startswith("GEMMA_API_KEY="):
                    api_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                    break
        else:
            api_key = content.split('\n')[0].strip().strip('"').strip("'")

if not api_key:
    print("FAILED: Could not find or read API Key from Desktop.")
else:
    print(f"SUCCESS: Read API Key (length: {len(api_key)}) from Desktop.")
    print("Testing Google AI Studio API for gemma-4-31b-it...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Reply with a valid JSON containing 'hello': 'world'."}]}],
        "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            print("API CALL SUCCESS!")
            print(result['candidates'][0]['content']['parts'][0]['text'])
    except urllib.error.HTTPError as e:
        print(f"API CALL FAILED: HTTP Error {e.code}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"API CALL FAILED: {str(e)}")
