# Gemma Match — 多 Agent 协作总览

**截止时间：2026-06-08 23:59**（还剩约 2 天）

## 角色分工

| 角色 | 工具 | 工作目录 | 分支 |
|------|------|----------|------|
| **总控（Master）** | 当前 Claude Code 会话 | `gemma_match/` | `master` |
| **cc-worker** | 新开的 Claude Code | `gemma_match_cc/` | `agent/cc-worker` |
| **codex** | Codex | `gemma_match_codex/` | `agent/codex` |

## 协调协议

1. 总控在 `coordination/tasks/` 写任务文件
2. 各 agent 读自己的任务文件，执行，完成后更新 `coordination/status/<name>.md`，然后 git commit
3. 总控定期读 status 文件，推进或解锁阻塞，执行 merge

## 防冲突规则

- **cc-worker** 只操作：`app.py`, `gemma_client.py`, `test_*.py`，以及任何以 `_cc` 结尾的新文件
- **codex** 只操作：`gemma_core/` 目录下的文件（新建或修改），以及 `coordination/status/codex.md`
- **master（总控）** 操作：merge、`coordination/` 目录、`requirements.txt`、`README.md`（最终版）

## 当前任务状态

- [ ] cc-worker：Function Calling 打通 + app.py 集成
- [ ] codex：gemma_core/ 黄金样例 + eval_harness + prompt_builder
- [ ] master：最终 merge + README + 提交
