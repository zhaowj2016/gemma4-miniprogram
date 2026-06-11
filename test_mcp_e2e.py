"""
MCP 端到端验证
================
用标准 MCP 客户端库测试 Server，不走 curl 歪路。
"""

import asyncio
import json
from mcp import ClientSession
from mcp.client.sse import sse_client


async def main():
    print("正在连接 MCP Server (http://127.0.0.1:8001/sse)...")

    async with sse_client("http://127.0.0.1:8001/sse") as (read, write):
        async with ClientSession(read, write) as session:

            # 1. 握手
            await session.initialize()
            print("✅ 握手成功")

            # 2. 列出工具
            tools = await session.list_tools()
            print(f"\n可用工具 ({len(tools.tools)} 个):")
            for t in tools.tools:
                print(f"  - {t.name}")

            # 3. 调用生成工具
            print("\n调用 generate_miniprogram_page...")
            result = await session.call_tool(
                "generate_miniprogram_page",
                arguments={
                    "description": "咖啡店点单页面，要有商品列表和购物车",
                    "style": "简约风"
                }
            )

            # 4. 解析结果
            for content in result.content:
                if content.type == "text":
                    data = json.loads(content.text)
                    print(f"\nProvider: {data.get('provider')}")
                    print(f"Parse Method: {data.get('parse_method')}")
                    print(f"Validation: {'PASS' if data.get('validation_passed') else 'FAIL'}")
                    print(f"WXML: {len(data.get('wxml', ''))} 字符")
                    print(f"WXSS: {len(data.get('wxss', ''))} 字符")
                    print(f"JS: {len(data.get('js', ''))} 字符")

                    # 断言：必须有代码
                    assert len(data.get("wxml", "")) > 0, "WXML 为空"
                    assert len(data.get("wxss", "")) > 0, "WXSS 为空"
                    assert len(data.get("js", "")) > 0, "JS 为空"

                    print("\n✅ MCP 端到端验证通过！Server 不是摆设。")


if __name__ == "__main__":
    asyncio.run(main())