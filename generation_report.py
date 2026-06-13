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
    actual_provider: str | None = None,
    actual_model: str | None = None,
    requested_mode: str | None = None,
    fallback_used: bool | None = None,
    fallback_reason: str | None = None,
    live_provider_called: bool | None = None,
    source_case: str | None = None,
    provider_latency_ms: int | None = None,
    provider_latency_source: str = "not_measured",
    tool_name: str = "create_miniprogram_page",
    tool_call_detected: bool = False,
    parse_method: str | None = None,
    line_counts: dict | None = None,
    files_generated: dict | None = None,
    validator_result: dict | None = None,
    repair_loop: dict | None = None,
    assets: dict | None = None,
    preview: dict | None = None,
    export: dict | None = None,
    durations: dict | None = None,
    raw_status: dict | None = None,
) -> dict:
    """Assemble the structured Generation Report.

    Missing measurements stay explicitly unmeasured instead of being coerced to
    zero. Older top-level keys are kept for existing saved sessions/UI readers.
    """
    actual_provider = actual_provider or provider or "unknown"
    actual_model = actual_model or model or "unknown"
    measured_durations = durations or {
        "total_ms": None,
        "model_call_ms": None,
        "validation_ms": None,
        "repair_ms": None,
        "duration_source": "not_measured",
    }
    validator_payload = validator_result or normalize_validator_result(None)
    repair_payload = repair_loop or {
        "attempted": False,
        "triggered": False,
        "success": None,
        "rounds": 0,
        "before_errors_count": 0,
        "after_errors_count": 0,
        "reason": "not_measured",
    }
    assets_payload = assets or {
        "asset_grounding_source": "unknown",
        "assets_used": [],
        "invalid_assets": [],
        "grounding_status": "unknown",
    }
    preview_payload = preview or {
        "preview_ready": False,
        "preview_type": "web_low_fidelity",
        "preview_html_path": "",
        "source_files": [],
    }
    export_payload = export or {"zip_ready": False, "zip_path": ""}
    return {
        "job_id": job_id or "unknown",
        "created_at": created_at or "unknown",
        "project_name": "MiniPilot Agent",
        "user_prompt": user_prompt or "",
        "mode": generation_mode or "unknown",
        "actual_provider": actual_provider,
        "actual_model": actual_model,
        "requested_mode": requested_mode or backend_mode or generation_mode or "unknown",
        "fallback_used": bool(fallback_used) if fallback_used is not None else False,
        "fallback_reason": fallback_reason or "",
        "live_provider_called": bool(live_provider_called) if live_provider_called is not None else (generation_mode != "replay"),
        "source_case": source_case or "",
        "provider_latency_ms": provider_latency_ms,
        "provider_latency_source": provider_latency_source or "not_measured",
        # Backward-compatible aliases.
        "provider": actual_provider,
        "model": actual_model,
        "generation_mode": generation_mode or "unknown",
        "backend_mode": backend_mode or "unknown",
        "tool": {
            "name": tool_name or "create_miniprogram_page",
            "tool_call_detected": bool(tool_call_detected),
            "parse_method": parse_method or "unknown",
        },
        "parse_method": parse_method or "unknown",
        "tool_call_detected": bool(tool_call_detected),
        "line_counts": line_counts or {"wxml": 0, "wxss": 0, "js": 0, "total": 0},
        "files_generated": files_generated or {"wxml": False, "wxss": False, "js": False},
        "validator": validator_payload,
        "validator_errors": validator_payload.get("hard_errors", []),
        "validator_warnings": validator_payload.get("warnings", []),
        "repair_loop": repair_payload,
        "repair_loop_triggered": bool(repair_payload.get("triggered") or repair_payload.get("attempted")),
        "repair_loop_reason": repair_payload.get("reason", ""),
        "assets": assets_payload,
        "asset_grounding_source": assets_payload.get("asset_grounding_source") or assets_payload.get("grounding_status", "unknown"),
        "preview": preview_payload,
        "preview_html_path": preview_payload.get("preview_html_path", ""),
        "screenshots_path": preview_payload.get("screenshots_path", ""),
        "export": export_payload,
        "zip_path": export_payload.get("zip_path", ""),
        "durations": measured_durations,
        "raw_status": raw_status or {"success": False, "error_message": ""},
    }
