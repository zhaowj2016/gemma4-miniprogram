import os
import google.generativeai as genai

# 自动从你电脑读取 API Key，不用手动填写！
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("✅ API Key 读取成功！")
print("🚀 AI 开始工作...\n")

# 最简单的AI对话测试
model = genai.GenerativeModel("gemini-1.5-flash")
model = genai.GenerativeModel("gemma-4-26b-a4b-it")
response = model.generate_content("你好，请回复一句话")

print("="*50)
print("🤖 AI 回复：")
print(response.text)
print("="*50)