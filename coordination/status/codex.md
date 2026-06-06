# codex 状态

**更新时间**：2026-06-06
**当前状态**：已完成

## 完成项
- [x] 读取 `coordination/tasks/codex.md`、`gemma_core/BUILD_SPEC.md`、`gemma_core/validators.py`
- [x] 确认 `gemma_core/golden_examples/` 已有 19 个黄金样例
- [x] 跑通 `python verify_golden.py`，19 个样例全部通过静态校验
- [x] 修复 `gemma_core/prompt_builder.py` 的 corpus index 路径，改为读取 `gemma_core/corpus_index.json`
- [x] 增强 prompt 检索逻辑，支持中文关键词子串命中
- [x] 修复 `gemma_core/eval_harness.py` 的 benchmark 路径，改为读取 `gemma_core/benchmark_prompts.json`
- [x] 跑通 `python gemma_core\eval_harness.py`，通过率 19/19 (100.0%)
- [x] 验证 `build_prompt` / `build_repair_prompt` 可导入并正常构造 prompt
- [x] Round 2：替换根目录 `README.md` 为比赛提交格式
- [x] Round 2：更新 `gemma_core/README.md`，补充目录用途、评测命令、import 示例和 19 个场景
- [x] Round 2：复跑 `python gemma_core\eval_harness.py`，通过率 19/19 (100.0%)

## 阻塞项
- 无

## 备注
- 当前 Python 启用了 `safe_path`，`python -c` 不会自动把当前目录放入 `sys.path`；验证 prompt 模块时使用了 `sys.path.insert(0, '.')`。
- 未清理根目录、未修改 app/gemma_client/deploy 相关文件；这些超出 codex worksheet 的 `gemma_core` 基建范围。
