import sys
sys.path.append(r"D:\soft\PythonPackages")
from openai import OpenAI
import json

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

# 定义微信小程序按钮生成工具 Schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_miniprogram_button",
            "description": "生成微信小程序的按钮组件代码（WXML格式）",
            "parameters": {
                "type": "object",
                "properties": {
                    "props": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "按钮属性列表，例如 ['class=\"red-btn\"', 'bindtap=\"handleSubmit\"']"
                    },
                    "text_content": {
                        "type": "string",
                        "description": "按钮文字内容，例如 '提交'、'登录'"
                    }
                },
                "required": ["props", "text_content"]
            }
        }
    }
]

print("🚀 开始向本地 Gemma 4 测试 Function Calling 闭环...")
try:
    res = client.chat.completions.create(
        model="gemma-4-e4b-it",
        messages=[
            {"role": "system", "content": "你是一个微信小程序开发专家。当用户需要生成小程序按钮组件时，你必须且只能调用 create_miniprogram_button 工具函数来完成。"},
            {"role": "user", "content": "帮我生成一个红色的提交按钮，点击后触发提交事件。"}
        ],
        tools=tools,
        tool_choice="auto",
        temperature=0.1
    )

    message = res.choices[0].message
    print("\n🤖 模型原始回复文本内容:")
    print("-" * 50)
    print(message.content)
    print("-" * 50)

    if message.tool_calls:
        print("\n✅ 【成功】模型正确触发了 Tool Calls (Function Calling)！")
        for tool_call in message.tool_calls:
            print(f"  调用的函数名: {tool_call.function.name}")
            print(f"  提取的参数: {tool_call.function.arguments}")
    else:
        print("\n❌ 【失败】未能触发 Tool Calls (模型直接以纯文本形式回复了内容，未调用工具)。")

except Exception as e:
    print(f"\n❌ 执行出错: {str(e)}")
