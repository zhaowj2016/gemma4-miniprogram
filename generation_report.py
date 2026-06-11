"""
Generation Report builder + sanitizer for Replay storage.

Turns the existing in-memory generation state (page_files / ValidationResult /
agent trace / timings) into a single structured, JSON-serialisable dict that
serves as auditable evidence for the Gemma 4 Function Calling pipeline.

Nothing here replaces existing modules (validators.py, zip_exporter.py,
render_wxml.py) - it only normalizes / aggregates their outputs.
"""
from __future__ import annotations

# Keys that must never be written to a report / replay record on disk.
SENSITIVE_KEY_HINTS = [
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "dsw_gateway_cookie",
    "google_api_key",
    "openai_api_key",
    "gemma_api_key",
    "private_key",
    "secret",
    "token",
]


def sanitize(value):
    """Recursively drop dict keys that look like credentials/secrets.

    Safe to call on arbitrary nested dict/list/scalar structures - used right
    before anything is written to generation_records / live_sessions.
    """
    if isinstance(value, dict):
        cleaned = {}
        for key, val in value.items():
            key_l = str(key).lower()
            if any(hint in key_l for hint in SENSITIVE_KEY_HINTS):
                continue
            cleaned[key] = sanitize(val)
        return cleaned
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def normalize_validator_result(validation) -> dict:
    """Adapt validators.ValidationResult (or a dict / None) to the report shape.

    Output:
        {"status": "passed"|"warning"|"failed"|"unknown",
         "hard_errors_count": int, "warnings_count": int,
         "hard_errors": [...], "warnings": [...]}
    """
    if validation is None:
        return {
            "status": "unknown",
            "hard_errors_count": 0,
            "warnings_count": 0,
            "hard_errors": [],
            "warnings": [],
        }
    if isinstance(validation, dict):
        hard_errors = list(validation.get("hard_errors") or [])
        warnings = list(validation.get("warnings") or [])
    else:
        hard_errors = list(getattr(validation, "hard_errors", []) or [])
        warnings = list(getattr(validation, "warnings", []) or [])

    if hard_errors:
        status = "failed"
    elif warnings:
        status = "warning"
    else:
        status = "passed"

    return {
        "status": status,
        "hard_errors_count": len(hard_errors),
        "warnings_count": len(warnings),
        "hard_errors": hard_errors,
        "warnings": warnings,
    }


def build_generation_report(
    *,
    job_id: str = "unknown",
    created_at: str = "unknown",
    user_prompt: str = "",
    provider: str | None = None,
    model: str | None = None,
    generation_mode: str = "live",
    backend_mode: str | None = None,
    tool_name: str = "create_miniprogram_page",
    tool_call_detected: bool = False,
    parse_method: str | None = None,
    files_generated: dict | None = None,
    validator_result: dict | None = None,
    repair_loop: dict | None = None,
    assets: dict | None = None,
    preview: dict | None = None,
    export: dict | None = None,
    durations: dict | None = None,
    raw_status: dict | None = None,
) -> dict:
    """Assemble the structured Generation Report. Every field has a safe default
    so a partially-known pipeline state never raises - missing data shows up as
    "unknown" / 0 / [] / false instead of breaking the report."""
    return {
        "job_id": job_id or "unknown",
        "created_at": created_at or "unknown",
        "project_name": "MiniPilot Agent",
        "user_prompt": user_prompt or "",
        "provider": provider or "unknown",
        "model": model or "unknown",
        "generation_mode": generation_mode or "unknown",
        "backend_mode": backend_mode or "unknown",
        "tool": {
            "name": tool_name or "create_miniprogram_page",
            "tool_call_detected": bool(tool_call_detected),
            "parse_method": parse_method or "unknown",
        },
        "files_generated": files_generated or {"wxml": False, "wxss": False, "js": False},
        "validator": validator_result or normalize_validator_result(None),
        "repair_loop": repair_loop or {
            "attempted": False, "success": None, "rounds": 0,
            "before_errors_count": 0, "after_errors_count": 0,
        },
        "assets": assets or {"assets_used": [], "invalid_assets": [], "grounding_status": "unknown"},
        "preview": preview or {"preview_ready": False, "preview_type": "web_low_fidelity"},
        "export": export or {"zip_ready": False, "zip_path": ""},
        "durations": durations or {"total_ms": 0, "model_call_ms": 0, "validation_ms": 0, "repair_ms": 0},
        "raw_status": raw_status or {"success": False, "error_message": ""},
    }
