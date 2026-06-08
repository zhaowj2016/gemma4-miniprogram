import io
import zipfile
from pathlib import Path
from scaffold import get_scaffold_files
from miniprogram_assets import decode_asset_bytes

ROOT = Path(__file__).resolve().parent
LIBRARY_ROOT = ROOT / "assets" / "library"


def _write_library_assets(zip_file: zipfile.ZipFile) -> None:
    if not LIBRARY_ROOT.exists():
        return
    for path in sorted(LIBRARY_ROOT.rglob("*")):
        if not path.is_file():
            continue
        arcname = path.relative_to(ROOT).as_posix()
        zip_file.writestr(arcname, path.read_bytes())


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

        # 4. Add curated local asset library as real mini-program project files.
        _write_library_assets(zip_file)
            
    return zip_buffer.getvalue()
