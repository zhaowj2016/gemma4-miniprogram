import sys
sys.path.append(r"D:\soft\PythonPackages")
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

res = client.chat.completions.create(
    model="gemma-4-e4b-it",
    messages=[{"role": "user", "content": "你好,请介绍一下你自己。"}],
    temperature=0.6,
    max_tokens=512,
    top_p=0.9
)
print(res.choices[0].message.content)