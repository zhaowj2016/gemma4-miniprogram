import os
from google import genai

# 自动读取 API Key
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 导入工具函数
from miniprogram_tools import (
    create_miniprogram_button,
    create_miniprogram_input,
    assemble_miniprogram_form
)

print("✅ API Key 读取成功！")
print("✅ 工具函数加载成功！")
print("🚀 Gemma4 开始生成登录表单...\n")

# 让 AI 生成完整的登录页面
prompt = """
你是专业的微信小程序生成助手。
请根据需求，生成一个标准的微信小程序登录表单代码。

需求：
1. 手机号输入框
2. 密码输入框
3. 红色登录按钮

直接输出最终代码，不要多余解释。
"""

try:
    response = client.models.generate_content(
        model="gemma-4-26b-a4b-it",
        contents=prompt
    )

    print("="*60)
    print("📱 生成的微信小程序登录页代码：")
    print("="*60)
    print(response.text)
    print("="*60)

except Exception as e:
    print("❌ 报错：", e)