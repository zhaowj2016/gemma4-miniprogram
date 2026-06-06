"""
Offline smoke test — no network, no Streamlit, no API key needed.

Steps:
1. Mock call_gemma_with_tools → returns product_detail golden example content
2. Run validate_project on the result
3. Run export_zip
4. Assert zip bytes non-empty + zip contains required files
5. Print PASS / FAIL
"""

import sys
import os
import zipfile
import io
import traceback

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "gemma_core"))


def _mock_call_gemma_with_tools(prompt: str) -> dict:
    """Return the product_detail golden example instead of calling the API."""
    from golden_examples import load_golden_from_folder
    return load_golden_from_folder("product_detail")


def _run_smoke(prompt: str) -> None:
    from validators import validate_project
    from zip_exporter import export_zip

    # --- Step 1: generate (mocked) ---
    result = _mock_call_gemma_with_tools(prompt)
    assert isinstance(result, dict), "mock must return dict"
    for key in ("wxml", "wxss", "js"):
        assert key in result, f"missing key: {key}"
        assert result[key], f"empty value for key: {key}"

    # --- Step 2: validate ---
    val_files = {
        "pages/index/index.wxml": result["wxml"],
        "pages/index/index.wxss": result["wxss"],
        "pages/index/index.js": result["js"],
    }
    val_result = validate_project(val_files, full_project=False)
    assert val_result.ok, (
        "validate_project FAIL on golden product_detail:\n"
        + "\n".join(val_result.hard_errors)
    )

    # --- Step 3: export zip ---
    zip_bytes = export_zip(result)
    assert isinstance(zip_bytes, bytes), "export_zip must return bytes"
    assert len(zip_bytes) > 0, "zip bytes must be non-empty"

    # --- Step 4: inspect zip contents ---
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = set(zf.namelist())

    required = {
        "app.json",
        "app.js",
        "app.wxss",
        "pages/index/index.wxml",
        "pages/index/index.wxss",
        "pages/index/index.js",
        "pages/index/index.json",
    }
    missing = required - names
    assert not missing, f"zip missing files: {missing}\nActual: {sorted(names)}"


def main() -> None:
    failures = []

    tests = [
        "生成一个活动报名页",
        "生成一个商品详情页，包含价格和购买按钮",
        "生成一个商品列表页",
    ]

    for prompt in tests:
        try:
            _run_smoke(prompt)
            print(f"  OK  {prompt}")
        except Exception as exc:
            failures.append((prompt, exc))
            print(f"  FAIL  {prompt}")
            traceback.print_exc()

    print()
    if failures:
        print(f"FAIL — {len(failures)}/{len(tests)} tests failed")
        sys.exit(1)
    else:
        print("PASS")


if __name__ == "__main__":
    main()
