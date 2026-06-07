"""
Live API multi-scenario test (Task 10, Round 3).
Calls call_gemma_with_tools(build_prompt(...)) for 5 prompts,
runs validate_project on each result, prints a summary table.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "gemma_core"))

from gemma_client import call_gemma_with_tools
from prompt_builder import build_prompt
from validators import validate_project

PROMPTS = [
    "生成一个活动报名页",
    "生成一个商品详情页，包含价格和购买按钮",
    "生成一个餐厅点餐页面",
    "生成一个个人中心页，显示用户信息和订单入口",
    "生成一个课程详情页",
]

results = []

for i, p in enumerate(PROMPTS, 1):
    print(f"\n[{i}/{len(PROMPTS)}] {p}")
    record = {"prompt": p, "fc_triggered": False, "status": "ERROR", "errors": []}
    try:
        raw = call_gemma_with_tools(build_prompt(p))
        # Detect whether Function Call was used (logged by gemma_client)
        # We infer from the returned dict being non-empty and having all 3 keys
        record["fc_triggered"] = all(raw.get(k) for k in ("wxml", "wxss", "js"))

        val = validate_project(
            {
                "pages/index/index.wxml": raw.get("wxml", ""),
                "pages/index/index.wxss": raw.get("wxss", ""),
                "pages/index/index.js": raw.get("js", ""),
            },
            full_project=False,
        )
        record["status"] = "PASS" if val.ok else "FAIL"
        record["errors"] = val.hard_errors[:3]
        print(f"  -> {'PASS' if val.ok else 'FAIL'}  fc={record['fc_triggered']}")
        if not val.ok:
            for e in val.hard_errors[:3]:
                print(f"     ! {e}")
    except Exception as exc:
        record["errors"] = [str(exc)[:120]]
        print(f"  -> ERROR: {exc}")

    results.append(record)

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
pass_count = sum(1 for r in results if r["status"] == "PASS")
fc_count = sum(1 for r in results if r["fc_triggered"])
for r in results:
    tag = "OK" if r["status"] == "PASS" else "NG"
    fc = "FC" if r["fc_triggered"] else "fb"
    print(f"  {tag} [{fc}] {r['prompt']}")
print(f"\nPASS: {pass_count}/{len(results)}   Function-Call triggered: {fc_count}/{len(results)}")

# Machine-readable output for status file
print("\nJSON_RESULTS:")
print(json.dumps(results, ensure_ascii=False, indent=2))
