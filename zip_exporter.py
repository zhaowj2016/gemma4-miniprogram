import io
import re
import zipfile
from pathlib import Path
from scaffold import get_scaffold_files
from miniprogram_assets import decode_asset_bytes

ROOT = Path(__file__).resolve().parent
LIBRARY_ROOT = ROOT / "assets" / "library"


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


def _write_library_assets(zip_file: zipfile.ZipFile, page_files: dict) -> None:
    if not LIBRARY_ROOT.exists():
        return
    for rel_path in _referenced_library_assets(page_files):
        path = ROOT / rel_path
        try:
            path.relative_to(LIBRARY_ROOT)
        except ValueError:
            continue
        if not path.is_file():
            continue
        zip_file.writestr(rel_path, path.read_bytes())


def export_zip(page_files: dict) -> bytes:
    """
    page_files = {'wxml': '...', 'wxss': '...', 'js': '...'}
    Merges page_files with the scaffold and exports to a zip byte array.
    """
    # Create in-memory bytes buffer
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        # 1. Add scaffold files
        scaffolds = get_scaffold_files()
        for filepath, content in scaffolds.items():
            zip_file.writestr(filepath, content.encode('utf-8'))
            
        # 2. Add page files
        if 'wxml' in page_files:
            zip_file.writestr('pages/index/index.wxml', page_files['wxml'].encode('utf-8'))
        if 'wxss' in page_files:
            zip_file.writestr('pages/index/index.wxss', page_files['wxss'].encode('utf-8'))
        if 'js' in page_files:
            zip_file.writestr('pages/index/index.js', page_files['js'].encode('utf-8'))

        # 3. Add user-uploaded mini-program assets as real project files.
        for asset in page_files.get("assets", []) or []:
            asset_path = (asset.get("path") or asset.get("wxml_path", "").lstrip("/")).replace("\\", "/").lstrip("/")
            if not asset_path or not asset.get("data_b64"):
                continue
            zip_file.writestr(asset_path, decode_asset_bytes(asset))

        # 4. Add only referenced curated library assets. Keeping the package small
        # matters for WeChat's preview/source package limits.
        _write_library_assets(zip_file, page_files)
            
    return zip_buffer.getvalue()
