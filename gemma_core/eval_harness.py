"""Evaluation harness for the mini-program code generator."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable


BASE_DIR = Path(__file__).resolve().parent
GOLDEN_DIR = BASE_DIR / "golden_examples"
BENCHMARK_PATH = GOLDEN_DIR / "benchmark_prompts.json"

sys.dont_write_bytecode = True
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from prompt_builder import build_prompt
from validators import validate_project

GenerateFn = Callable[[str], dict[str, str] | str]


def run_eval(generate_fn: GenerateFn | None = None) -> list[dict[str, Any]]:
    """Run benchmark prompts, or fallback golden examples when no benchmark exists."""
    cases = _load_cases()
    results: list[dict[str, Any]] = []

    for case in cases:
        prompt = build_prompt(case["prompt"])
        generator = generate_fn or _make_stub(case)
        generated = generator(prompt)
        page_files = _to_validator_files(generated)
        result = validate_project(page_files, full_project=False)

        results.append(
            {
                "scenario": case["scenario"],
                "passed": result.ok,
                "hard_errors": len(result.hard_errors),
            }
        )

    _print_table(results)
    return results


def main() -> None:
    run_eval()


def _load_cases() -> list[dict[str, str]]:
    benchmark = _load_json(BENCHMARK_PATH)
    cases = _cases_from_benchmark(benchmark)
    if cases:
        return cases
    return _fallback_cases_from_golden()


def _cases_from_benchmark(benchmark: Any) -> list[dict[str, str]]:
    raw_cases: Any
    if isinstance(benchmark, dict):
        raw_cases = (
            benchmark.get("cases")
            or benchmark.get("prompts")
            or benchmark.get("benchmarks")
            or benchmark.get("items")
            or []
        )
    else:
        raw_cases = benchmark

    if not isinstance(raw_cases, list):
        return []

    cases: list[dict[str, str]] = []
    for idx, item in enumerate(raw_cases, start=1):
        if isinstance(item, str):
            cases.append(
                {
                    "scenario": f"benchmark_{idx}",
                    "prompt": item,
                    "golden_id": _guess_golden_id(item),
                }
            )
            continue

        if not isinstance(item, dict):
            continue

        prompt = str(
            item.get("prompt")
            or item.get("user_prompt")
            or item.get("requirement")
            or item.get("input")
            or ""
        ).strip()
        if not prompt:
            continue

        scenario = str(
            item.get("scenario")
            or item.get("name")
            or item.get("id")
            or f"benchmark_{idx}"
        )
        golden_id = str(
            item.get("golden_id")
            or item.get("example_id")
            or item.get("expected")
            or _guess_golden_id(prompt)
        )
        cases.append({"scenario": scenario, "prompt": prompt, "golden_id": golden_id})

    return cases


def _fallback_cases_from_golden() -> list[dict[str, str]]:
    cases: list[dict[str, str]] = []
    if not GOLDEN_DIR.exists():
        return cases

    for sample_dir in sorted(path for path in GOLDEN_DIR.iterdir() if path.is_dir()):
        scenario = sample_dir.name
        cases.append(
            {
                "scenario": scenario,
                "prompt": f"生成一个 {scenario.replace('_', ' ')} 微信小程序页面",
                "golden_id": scenario,
            }
        )
    return cases


def _make_stub(case: dict[str, str]) -> GenerateFn:
    def generate_stub(_prompt: str) -> dict[str, str]:
        golden_id = case.get("golden_id") or case["scenario"]
        files = _load_golden(golden_id)
        if not files and golden_id != case["scenario"]:
            files = _load_golden(case["scenario"])
        if not files:
            raise FileNotFoundError(f"No golden example found for {golden_id!r}")
        return files

    return generate_stub


def _load_golden(example_id: str) -> dict[str, str]:
    sample_dir = GOLDEN_DIR / example_id
    if not sample_dir.is_dir():
        return {}
    return {
        "wxml": _read_first(sample_dir, ("index.wxml", "wxml.txt")),
        "wxss": _read_first(sample_dir, ("index.wxss", "wxss.txt")),
        "js": _read_first(sample_dir, ("index.js", "js.txt")),
    }


def _read_first(sample_dir: Path, names: tuple[str, ...]) -> str:
    for name in names:
        path = sample_dir / name
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace")
    return ""


def _to_validator_files(generated: dict[str, str] | str) -> dict[str, str]:
    if isinstance(generated, str):
        generated = json.loads(generated)

    return {
        "pages/index/index.wxml": generated.get("wxml")
        or generated.get("pages/index/index.wxml")
        or generated.get("index.wxml")
        or "",
        "pages/index/index.wxss": generated.get("wxss")
        or generated.get("pages/index/index.wxss")
        or generated.get("index.wxss")
        or "",
        "pages/index/index.js": generated.get("js")
        or generated.get("pages/index/index.js")
        or generated.get("index.js")
        or "",
    }


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _guess_golden_id(prompt: str) -> str:
    prompt_lower = prompt.lower()
    candidates = [path.name for path in GOLDEN_DIR.iterdir() if path.is_dir()] if GOLDEN_DIR.exists() else []
    for candidate in sorted(candidates, key=len, reverse=True):
        words = candidate.lower().split("_")
        if candidate.lower() in prompt_lower or all(word in prompt_lower for word in words):
            return candidate
    return candidates[0] if candidates else ""


def _print_table(results: list[dict[str, Any]]) -> None:
    print("场景 | 首次 PASS/FAIL | hard_errors 数量")
    print("--- | --- | ---")
    for row in results:
        status = "PASS" if row["passed"] else "FAIL"
        print(f"{row['scenario']} | {status} | {row['hard_errors']}")

    total = len(results)
    passed = sum(1 for row in results if row["passed"])
    rate = (passed / total * 100) if total else 0.0
    print(f"\n通过率: {passed}/{total} ({rate:.1f}%)")


if __name__ == "__main__":
    main()
