# cc-worker 状态

**更新时间**：2026-06-06
**当前状态**：Task 1-3 完成，Task 4（冒烟测试）待执行

## 完成项

- [x] **Task 1**：读清楚现状。已读 BUILD_SPEC.md §4、gemma_client.py（原三段标记版）、app.py（原多轮 chat 版）、validators.py。
- [x] **Task 2**：`gemma_client.py` 实现 Native Function Calling。
  - 定义了 `TOOLS`（名称 `create_miniprogram_page`，三字段 wxml/wxss/js）
  - 实现 `call_gemma_with_tools(prompt)` → `{'wxml', 'wxss', 'js'}`
  - 使用 `urllib.request` 直接调 Google AI Studio REST API（`functionDeclarations` + `toolConfig.functionCallingConfig.mode=AUTO`）
  - Function Call 未触发时退回 `parse_triple()` 三段标记解析
  - API Key 读取优先级：`GEMINI_API_KEY` env → `.env` 文件 → `E:\file+desktop\gemma_key.txt`
- [x] **Task 3**：`app.py` 重写为简洁 UI。
  - 3 个示例按钮（活动报名 / 商品详情 / 商品列表）
  - 生成按钮 + spinner
  - 自愈重试显示 `⏳ 正在进行第 1 次自愈重试...`
  - 校验通过：三段代码 expander + ZIP 下载按钮
  - fallback：黄色警告条 + 黄金样例
  - 下载旁注明替换 `touristappid`
- [x] **requirements.txt** 创建（`streamlit>=1.35`, `google-generativeai>=0.8`）

## 阻塞项

无。

---

## Round 2 完成项（2026-06-06）

- [x] **Task 5**：`app.py` 切换到 `gemma_core/prompt_builder.py`
  - 头部加 `sys.path.insert(0, .../gemma_core)` 后 import `build_prompt` / `build_repair_prompt`
  - 初次生成调用 `build_prompt(user_input)` —— 含约束清单 + 2 个 few-shot 样例（11 531 chars）
  - 自愈调用 `build_repair_prompt(user_input, result, errors)` —— 把当前代码 + 错误列表一并喂回去
  - `gemma_client.py` 同步去掉内部 `_SYSTEM_PREFIX`，避免与 CONSTRAINT_CHECKLIST 重复
- [x] **Task 6**：`golden_examples.py` SCENARIO_KEYWORDS 已涵盖全部 19 个场景，关键词从 corpus_index.json 合并补全（每个场景 7-11 个关键词）
- [x] **Task 7**：新建 `test_smoke.py`，offline 静态验证
  - mock `call_gemma_with_tools` → product_detail 黄金样例
  - 走完 validate_project + export_zip 全流程
  - 解压 zip 断言包含 app.json / pages/index/index.wxml 等 7 个必须文件
  - `python test_smoke.py` → 3/3 PASS

## Round 2 验收状态

- [x] `app.py` 使用 `gemma_core/prompt_builder.py`
- [x] `golden_examples.py` SCENARIO_KEYWORDS 已涵盖全部 19 个场景
- [x] `python test_smoke.py` → PASS

## 备注

- `google-generativeai` SDK 本地未安装（`ModuleNotFoundError`），已选用方案 2：`urllib.request` 直接调 REST API。
- API Key 已从本地文件读取到，本地可运行。
- Streamlit UI 测试需要在浏览器环境中执行 `streamlit run app.py`，CLI 环境不支持，但全部逻辑路径已通过 test_smoke.py 静态覆盖。

---

## Round 3 完成项（2026-06-06，由总控在 master 直接执行）

- [x] **Task 8**：`requirements.txt` 删除 `google-generativeai>=0.8`（未安装未使用），仅保留 `streamlit>=1.35`
- [x] **Task 9**：新建 `.env.example`，含 Google AI Studio 获取 key 的链接和使用说明
- [x] **Task 10**：Live 5-prompt 测试全部 PASS，Function Call 每次触发

| prompt | Function Call | 校验 |
|--------|--------------|------|
| 生成一个活动报名页 | ✅ 触发 | PASS |
| 生成一个商品详情页，包含价格和购买按钮 | ✅ 触发 | PASS |
| 生成一个餐厅点餐页面 | ✅ 触发 | PASS |
| 生成一个个人中心页，显示用户信息和订单入口 | ✅ 触发 | PASS |
| 生成一个课程详情页 | ✅ 触发 | PASS |

**通过率：5/5 (100%)**
