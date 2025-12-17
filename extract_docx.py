# extract_docx.py
import os, docx2txt, shutil
from pathlib import Path
from markitdown import MarkItDown
from utils import log_info, log_warning
from image_utils import save_and_rename_images, rewrite_markdown_images

def process_docx(docx_path: Path, media_dir: Path, uuid: str,
                 md_path: Path, warn_log: Path, info_log: Path):

    log_info(info_log, f"Starting DOCX processing: {docx_path}")

    # media_dir = /output/media/<UUID>
    media_root = media_dir.parent  # /output/media

    temp_dir = media_root / f"{uuid}_tmp"
    os.makedirs(temp_dir, exist_ok=True)

    log_info(info_log, f"Media directory will be: {media_dir}")

    # Step 1: Run MarkItDown for text
    try:
        md = MarkItDown(enable_plugins=False)
        result = md.convert(str(docx_path))
        markdown_text = result.text_content
        md_path.write_text(markdown_text, encoding="utf-8")
        log_info(info_log, f"Markdown written to: {md_path}")
    except Exception as e:
        log_warning(warn_log, f"MarkItDown failed for {docx_path}: {e}")
        return

    # Step 2: Extract images using docx2txt
    rel_paths = []
    try:
        docx2txt.process(str(docx_path), str(temp_dir))
        log_info(info_log, f"docx2txt processed images to temp dir: {temp_dir}")

        # Pass media_root, not media_dir
        rel_paths = save_and_rename_images(
            temp_dir,
            media_root,
            uuid,
            md_path,
            info_log,
            warn_log
        )

    except Exception as e:
        log_warning(warn_log, f"{docx_path} docx2txt error: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Step 3: Rewrite Markdown image links
    try:
        rewrite_markdown_images(md_path, rel_paths, info_log, warn_log)
    except Exception as e:
        log_warning(warn_log, f"{md_path} inline injection error: {e}")
        log_info(info_log, f"Failed image injection: {e}")
