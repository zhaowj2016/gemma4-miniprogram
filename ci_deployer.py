from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deploy_config.json")
_ROOT = Path(__file__).resolve().parent
_LIBRARY_ROOT = _ROOT / "assets" / "library"
_LOG_ROOT = _ROOT / "demo_cache" / "wechat_ci"
_LOG_ROOT.mkdir(parents=True, exist_ok=True)


def load_deploy_config() -> dict | None:
    """Load saved WeChat deploy credentials from a local gitignored file."""
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_deploy_config(appid: str, private_key: str):
    """Persist WeChat deploy credentials locally. The file is gitignored."""
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"appid": appid, "private_key": private_key}, f, ensure_ascii=False, indent=2)


def clear_deploy_config():
    """Delete saved WeChat deploy credentials."""
    if os.path.exists(_CONFIG_PATH):
        os.remove(_CONFIG_PATH)


def _write_log(payload: dict) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = _LOG_ROOT / f"wechat-preview-{timestamp}.json"
    log_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return log_path


def _classify_ci_error(output: str) -> str:
    text = (output or "").lower()
    quota_words = [
        "quota",
        "rate limit",
        "ratelimit",
        "frequency",
        "too many",
        "daily",
        "preview count",
        "exceed",
        "次数",
        "频率",
        "上限",
        "限制",
    ]
    if any(word in text for word in quota_words):
        return (
            "可能是微信 CI 预览次数或频率限制。可先换 robot(1-30) 再试；如果仍失败，"
            "通常需要等微信侧限额恢复或更换 AppID。"
        )
    if "ip" in text and ("white" in text or "白名单" in text or "whitelist" in text):
        return "可能是微信小程序后台的 CI IP 白名单未放行当前出口 IP。"
    if "private" in text or "key" in text or "signature" in text or "签名" in text:
        return "可能是 private key 内容、格式或 AppID 与密钥不匹配。"
    if "appid" in text or "unauthorized" in text or "permission" in text or "权限" in text:
        return "可能是 AppID、CI 权限或账号权限问题。"
    if "-1" in text:
        return "微信 CI 返回了泛化错误码 -1；这不一定代表 25 次用完，请查看日志里的原始 stderr/stdout。"
    return "未能从错误文本判断具体原因，请查看日志里的原始 stderr/stdout。"


def get_local_preview_summary() -> dict:
    """Count successful-looking QR files created on this machine today."""
    temp_root = Path(tempfile.gettempdir())
    today = datetime.now().date()
    qr_files = []
    for path in temp_root.glob("gemma_qr_*/preview.jpg"):
        try:
            stat = path.stat()
        except OSError:
            continue
        modified = datetime.fromtimestamp(stat.st_mtime)
        if modified.date() == today:
            qr_files.append(
                {
                    "path": str(path),
                    "modified": modified.strftime("%Y-%m-%d %H:%M:%S"),
                    "bytes": stat.st_size,
                    "looks_successful": stat.st_size > 1024,
                }
            )
    qr_files.sort(key=lambda item: item["modified"], reverse=True)
    return {
        "date": today.isoformat(),
        "successful_qr_files": sum(1 for item in qr_files if item["looks_successful"]),
        "all_qr_files": len(qr_files),
        "recent": qr_files[:8],
        "log_dir": str(_LOG_ROOT),
    }


def _referenced_library_assets(page_files: dict) -> list[str]:
    text = "\n".join(str(page_files.get(key, "") or "") for key in ("wxml", "wxss", "js"))
    refs = {
        match.group(0).replace("\\", "/").lstrip("/")
        for match in re.finditer(r"/?assets/library/[A-Za-z0-9_./-]+\.(?:jpg|jpeg|png|webp|gif)", text, flags=re.I)
    }
    for asset in page_files.get("library_assets", []) or []:
        asset_path = (asset.get("path") or asset.get("wxml_path") or "").replace("\\", "/").lstrip("/")
        if asset_path and (asset_path in text or f"/{asset_path}" in text):
            refs.add(asset_path)
    return sorted(refs)


def _copy_referenced_library_assets(workspace: str, page_files: dict) -> list[str]:
    copied: list[str] = []
    if not _LIBRARY_ROOT.exists():
        return copied
    for rel_path in _referenced_library_assets(page_files):
        src = _ROOT / rel_path
        try:
            src.relative_to(_LIBRARY_ROOT)
        except ValueError:
            continue
        if not src.is_file():
            continue
        dst = Path(workspace) / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        copied.append(rel_path)
    return copied


def _directory_size(path: str) -> int:
    total = 0
    root = Path(path)
    if not root.exists():
        return total
    for item in root.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                pass
    return total


def deploy_to_wechat(page_files: dict, appid: str, private_key_content: str, robot: int = 1) -> str:
    """
    Write a real Mini Program project, then call miniprogram-ci to create a preview QR code.

    The projectPath used by miniprogram-ci is the same directory that receives generated
    page files and user/library assets. This keeps QR preview behavior aligned with Zip export.
    """
    from scaffold import get_scaffold_files
    from miniprogram_assets import decode_asset_bytes

    robot = int(robot)
    if robot < 1 or robot > 30:
        raise ValueError("robot must be an integer from 1 to 30")

    qr_dir = tempfile.mkdtemp(prefix="gemma_qr_")
    qr_code_path = os.path.join(qr_dir, "preview.jpg")
    log_payload = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "appid": appid,
        "robot": robot,
        "qr_code_path": qr_code_path,
        "status": "started",
    }

    with tempfile.TemporaryDirectory() as workspace:
        log_payload["project_path"] = workspace
        scaffolds = get_scaffold_files()

        p_config = json.loads(scaffolds["project.config.json"])
        p_config["appid"] = appid
        scaffolds["project.config.json"] = json.dumps(p_config, ensure_ascii=False)

        for filepath, content in scaffolds.items():
            full_path = os.path.join(workspace, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        page_dir = os.path.join(workspace, "pages", "index")
        os.makedirs(page_dir, exist_ok=True)
        for key, filename in (("wxml", "index.wxml"), ("wxss", "index.wxss"), ("js", "index.js")):
            if key in page_files:
                with open(os.path.join(page_dir, filename), "w", encoding="utf-8") as f:
                    f.write(page_files[key])

        written_assets = []
        for asset in page_files.get("assets", []) or []:
            asset_path = (asset.get("path") or asset.get("wxml_path", "").lstrip("/")).replace("\\", "/").lstrip("/")
            if not asset_path or not asset.get("data_b64"):
                continue
            full_path = os.path.join(workspace, *asset_path.split("/"))
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(decode_asset_bytes(asset))
            written_assets.append(asset_path)

        written_assets.extend(_copy_referenced_library_assets(workspace, page_files))
        log_payload["written_assets"] = written_assets
        log_payload["project_bytes_before_ci"] = _directory_size(workspace)

        cleaned_key = private_key_content.strip()
        if "-----BEGIN RSA PRIVATE KEY-----" in cleaned_key and not cleaned_key.startswith("-----BEGIN RSA PRIVATE KEY-----\n"):
            cleaned_key = cleaned_key.replace("-----BEGIN RSA PRIVATE KEY-----", "-----BEGIN RSA PRIVATE KEY-----\n")
            cleaned_key = cleaned_key.replace("-----END RSA PRIVATE KEY-----", "\n-----END RSA PRIVATE KEY-----")
            cleaned_key = "\n".join([line.strip() for line in cleaned_key.split("\n") if line.strip()])

        key_path = os.path.join(workspace, f"private.{appid}.key")
        with open(key_path, "w", encoding="utf-8") as f:
            f.write(cleaned_key)

        upload_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload.js")
        cmd = ["node", upload_script, workspace, appid, key_path, qr_code_path, str(robot)]
        log_payload["command"] = ["node", "upload.js", "<projectPath>", appid, "<privateKeyPath>", qr_code_path, str(robot)]

        env = os.environ.copy()
        env["NODE_OPTIONS"] = "--openssl-legacy-provider"

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
                timeout=120,
            )
            log_payload.update(
                {
                    "status": "success",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "finished_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
            log_path = _write_log(log_payload)
            print(result.stdout)
            print(f"WeChat CI log: {log_path}")
        except subprocess.CalledProcessError as e:
            output = (e.stderr or "") + "\n" + (e.stdout or "")
            log_payload.update(
                {
                    "status": "failed",
                    "returncode": e.returncode,
                    "stdout": e.stdout,
                    "stderr": e.stderr,
                    "finished_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
            log_path = _write_log(log_payload)
            hint = _classify_ci_error(output)
            excerpt = output.strip()[:1200] or "(no stderr/stdout captured)"
            raise Exception(f"微信预览上传失败。\n原因判断：{hint}\n日志：{log_path}\n原始输出：\n{excerpt}") from e

    if not os.path.exists(qr_code_path) or os.path.getsize(qr_code_path) <= 1024:
        log_path = _write_log(
            {
                **log_payload,
                "status": "failed",
                "finished_at": datetime.now().isoformat(timespec="seconds"),
                "reason": "QR code image missing or too small",
            }
        )
        raise Exception(f"QR code generation failed: image not found or invalid. 日志：{log_path}")

    return qr_code_path
