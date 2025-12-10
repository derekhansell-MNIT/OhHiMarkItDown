# extract_docx.py
import os, docx2txt, shutil
from pathlib import Path
from markitdown import MarkItDown
from utils import log_info, log_warning
from image_utils import save_and_rename_images, rewrite_markdown_images

def process_docx(docx_path, media_dir, uuid, md_path, warn_log, info_log):
    log_info(info_log, f"Starting DOCX processing: {docx_path}")
    temp_dir = media_dir.parent / (media_dir.name + "_tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Convert DOCX → Markdown
    try:
        md = MarkItDown(enable_plugins=False)
        result = md.convert(str(docx_path))
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(result.text_content)
        log_info(info_log, f"Markdown written to: {md_path}")
    except Exception as e:
        log_warning(warn_log, f"MarkItDown failed: {e}")
        return

    # Step 2: Extract embedded images to temp_dir
    try:
        docx2txt.process(docx_path, temp_dir)
        log_info(info_log, f"Extracted images to temp dir: {temp_dir}")
    except Exception as e:
        log_warning(warn_log, f"{docx_path} docx2txt error: {e}")
        return

    # Step 3: Rename, move to /media/uuid/, rewrite links
    rel_paths = save_and_rename_images(temp_dir, media_dir, uuid, md_path, info_log, warn_log)
    shutil.rmtree(temp_dir, ignore_errors=True)
    rewrite_markdown_images(md_path, rel_paths, info_log, warn_log)

    log_info(info_log, f"Completed DOCX processing: {docx_path}")