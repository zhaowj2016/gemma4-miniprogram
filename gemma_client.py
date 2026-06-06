import urllib.request
import urllib.error
import json
import os

import time

def call_gemma(prompt: str, history: list = None, api_key: str = None) -> str:
    """
    Call Gemma model via Google AI Studio API.
    Model: gemma-4-31b-it
    """
    api_key = api_key or os.environ.get("GEMMA_API_KEY") or os.environ.get("GEMINI_API_KEY")
    print(f"--- Backend Monitor: Received a request to call Gemma. Length of prompt: {len(prompt)} ---")
    
    # Check local .env file natively to bypass Windows environment variable propagation issues
    if not api_key and os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8-sig") as f:
                for line in f:
                    if line.strip().startswith("GEMMA_API_KEY="):
                        api_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass
            
    # Ultimate fallback: Read from Desktop text file
    if not api_key:
        desktop_path = r"E:\file+desktop\gemma_key.txt"
        if os.path.exists(desktop_path):
            try:
                with open(desktop_path, "r", encoding="utf-8-sig") as f:
                    content = f.read().strip()
                    if "GEMMA_API_KEY=" in content:
                        for line in content.split('\n'):
                            if line.strip().startswith("GEMMA_API_KEY="):
                                api_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                                break
                    else:
                        api_key = content.split('\n')[0].strip().strip('"').strip("'")
            except Exception:
                pass
            
    if not api_key:
        return "ERROR: GEMMA_API_KEY is not set. Please create E:\\file+desktop\\gemma_key.txt and paste your key inside."
        
    cloud_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent?key={api_key}"
    contents = []
    if history:
        for msg in history:
            contents.append({
                "role": msg.get("role", "user"),
                "parts": [{"text": msg.get("text", "")}]
            })
    
    contents.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    cloud_data = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 8192
        }
    }
    
    req_cloud = urllib.request.Request(
        cloud_url,
        data=json.dumps(cloud_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    max_retries = 3
    base_delay = 3
    
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req_cloud, timeout=600) as response:
                result = json.loads(response.read().decode('utf-8'))
                print("--- Backend Monitor: API Call Successful! ---")
                return result['candidates'][0]['content']['parts'][0]['text']
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"--- Backend Monitor: API Error {e.code} (Attempt {attempt+1}/{max_retries}) ---")
            if e.code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                sleep_time = base_delay * (2 ** attempt)
                print(f"--- Backend Monitor: Retrying in {sleep_time} seconds due to {e.code}... ---")
                time.sleep(sleep_time)
                continue
            return f"ERROR: Google AI Studio API Error ({e.code}). Details: {error_body}"
        except Exception as e:
            print(f"--- Backend Monitor: Request Failed: {e} ---")
            return f"ERROR: Failed to call Gemma. {str(e)}"
