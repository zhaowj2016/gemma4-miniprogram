# Gemma Match — Agent 任务包（已含比赛提交规范）

**Agent 请按以下顺序处理：**

1. 先读 `BUILD_SPEC.md`，严格按它执行。
2. `validators.py` 和 `golden_examples/` **已写好，直接复用，不要重写**。
3. 你要做的是补齐：`app.py / gemma_client.py / prompt_builder.py / scaffold.py / zip_exporter.py / golden_examples.py / requirements.txt / README.md`。

⚠️ **关键：建的是 Streamlit 生成器应用，不是一个小程序。**
⚠️ **核心亮点：必须用 Gemma 4 Native Function Calling 输出代码（BUILD_SPEC 第 4 节），不要用三段标记或 JSON manifest——这是评分 25% 的技术分来源。**
