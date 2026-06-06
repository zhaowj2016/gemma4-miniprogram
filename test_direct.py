import urllib.request
import urllib.error
import json
import os

api_key = os.environ.get("GEMMA_API_KEY")
if not api_key:
    with open(".env", "r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip().startswith("GEMMA_API_KEY="):
                api_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                break

cloud_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent?key={api_key}"

prompt = """You are a senior WeChat Mini Program developer. Write a highly complex, 1000-line commercial WeChat Mini Program for a Restaurant Ordering App.
Start your response EXACTLY with ===WXML=== followed by the code.
Do NOT output any conversational text.
===WXML===
"""

cloud_data = {
    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 8192}
}

req_cloud = urllib.request.Request(
    cloud_url,
    data=json.dumps(cloud_data).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req_cloud, timeout=600) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(len(result['candidates'][0]['content']['parts'][0]['text']))
except Exception as e:
    print(e)
