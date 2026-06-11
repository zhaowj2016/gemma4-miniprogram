"""
LMStudio 本地集成测试
====================
作用：在接入 MCP / Streamlit 之前，独立验证 LMStudio 链路是否跑通。
运行方式：
    python test_lmstudio_integration.py
预期结果：
    3 个测试用例全部通过，终端显示 WXML/WXSS/JS 行数
"""

import sys

sys.path.insert(0, ".")  # 确保能导入当前目录的模块

from gemma_client_lmstudio import call_lmstudio

# 测试用例：覆盖项目 README 中推荐的典型 Prompt
TEST_CASES = [
    {
        "name": "咖啡店点单",
        "prompt": "帮我生成一个咖啡店点单小程序页面，要有商品列表、购物车和底部结算按钮",
    },
    {
        "name": "活动报名",
        "prompt": "帮我生成一个活动报名页，要有活动介绍、姓名手机号输入框和报名按钮",
    },
    {
        "name": "电商商品详情",
        "prompt": "生成一个电商商品详情页，包含商品主图、价格、规格选择、优惠信息和底部购买按钮",
    },
]


def run_test():
    print("=" * 70)
    print("MiniPilot LMStudio 本地集成测试")
    print("=" * 70)
    print(f"模型: google/gemma-4-e4b @ http://127.0.0.1:1234/v1")
    print("-" * 70)

    all_passed = True

    for i, case in enumerate(TEST_CASES, 1):
        print(f"\n【测试 {i}】{case['name']}")
        print(f"  Prompt: {case['prompt'][:40]}...")

        try:
            # 调用 LMStudio 生成代码
            result = call_lmstudio(prompt=case["prompt"])

            wxml = result.get("wxml", "")
            wxss = result.get("wxss", "")
            js = result.get("js", "")

            wxml_lines = len(wxml.splitlines()) if wxml else 0
            wxss_lines = len(wxss.splitlines()) if wxss else 0
            js_lines = len(js.splitlines()) if js else 0

            print(f"  Provider: {result.get('provider')}")
            print(f"  Parse Method: {result.get('parse_method')}")
            print(f"  代码量: WXML={wxml_lines}行 | WXSS={wxss_lines}行 | JS={js_lines}行")

            # 断言：三个文件都不能为空
            assert wxml_lines > 0, "WXML 为空"
            assert wxss_lines > 0, "WXSS 为空"
            assert js_lines > 0, "JS 为空"

            # 断言：JS 必须包含 Page({}) 或 Component({})（小程序入口要求）
            assert "Page(" in js or "Component(" in js, "JS 缺少 Page/Component 构造"

            print(f"  ✅ 通过")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 全部测试通过！LMStudio 链路已跑通，可以接入 MCP Server。")
    else:
        print("⚠️ 部分测试失败，请检查 LMStudio 是否开启、模型是否加载、端口是否正确。")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)