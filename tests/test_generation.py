import os
import json
import urllib.request
import urllib.error
from prompt_builder import build_prompt

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
    print("FAILED to read API Key")
    exit(1)

prompt = build_prompt("帮我做一个三栏的打卡页面")
print(f"Prompt length: {len(prompt)}")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent?key={api_key}"
payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"temperature": 0.0, "maxOutputTokens": 8192, "responseMimeType": "application/json"}
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=180) as response:
        result = json.loads(response.read().decode('utf-8'))
        text = result['candidates'][0]['content']['parts'][0]['text']
        with open("raw_model_output.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("Model output saved to raw_model_output.txt")
except Exception as e:
    print(f"API CALL FAILED: {str(e)}")
