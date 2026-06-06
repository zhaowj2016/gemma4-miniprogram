import io
import zipfile
from scaffold import get_scaffold_files

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
            
    return zip_buffer.getvalue()
