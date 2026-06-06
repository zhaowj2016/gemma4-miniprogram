# Gemma Match

用 Gemma 4 Native Function Calling 生成微信小程序源码的 AI 应用。用户在 Streamlit 页面输入自然语言需求，系统调用 Gemma 4 生成 `pages/index/index` 的 WXML、WXSS、JS，经过静态校验后打包成可导入微信开发者工具的 ZIP。

## 快速启动

```bash
pip install -r requirements.txt
streamlit run app.py
```

运行前请配置环境变量 `GEMINI_API_KEY` 或复制 `.env.example` 为 `.env` 填入 key。生成结果下载后可用微信开发者工具游客模式打开，或将 `project.config.json` 中的 `touristappid` 替换为真实 AppID。

## 架构说明

核心链路由 `app.py` 驱动：前端收集用户需求后调用 `gemma_client.call_gemma_with_tools`。`gemma_client.py` 中定义了 `TOOLS`，其中 `create_miniprogram_page` 要求 Gemma 4 通过 Function Calling 返回结构化的 `wxml`、`wxss`、`js` 三个字段；如果工具调用没有触发，系统才回退到三段标记文本解析。生成结果会交给 `validators.validate_project` 做静态门禁，拦截 HTML 标签、危险 `wx.*` API、WXML 绑定函数调用、JS 构造缺失等高频错误。若首次校验失败，应用会把 hard errors 反馈给模型进行一次自愈重试；仍失败时，使用 `golden_examples.py` 按关键词选择最接近的黄金样例作为 fallback。最终 `zip_exporter.export_zip` 合并固定脚手架和页面三件套，输出完整小程序 ZIP。

## 黄金样例语料

`gemma_core/golden_examples/` 包含 19 个预验证场景，覆盖商品、报名、预约、门店、课程、新闻、个人中心、订单、优惠券、报价、招聘、房源、点餐、作品集、问卷、联系页等常见需求。所有样例均通过 `gemma_core/validators.py` 静态校验，并由 `gemma_core/eval_harness.py` 作为离线评测与 few-shot 检索语料使用。

## Demo

启动后访问 `http://localhost:8501`，在输入框描述目标页面（或点击示例按钮），
点击「生成代码」即可在约 5-10 秒内看到 WXML / WXSS / JS 三段代码及 ZIP 下载按钮。

生成的 ZIP 可直接导入[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)，
选择「游客模式」或将 `project.config.json` 中的 `touristappid` 替换为真实 AppID。

## 项目结构

```text
app.py                  # Streamlit 入口，负责输入、生成、校验、下载
gemma_client.py         # Gemma 4 API 调用与 Native Function Calling 工具定义
validators.py           # 根目录静态校验器，出站前检查页面三件套
scaffold.py             # 固定小程序脚手架文件
zip_exporter.py         # 合并脚手架与生成页面并打包 ZIP
golden_examples.py      # 根目录 fallback 黄金样例选择器
gemma_core/             # 语料、评测、prompt 模块和语义 block 实验区
gemma_core/golden_examples/  # 19 个已校验页面样例
gemma_core/eval_harness.py   # 离线评测入口
requirements.txt        # Python 运行依赖
```
