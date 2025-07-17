from pathlib import Path
from extract_pdf import extract_pdf_images
from extract_docx import extract_docx_images
from utils import log_info, log_warning, format_filename, generate_uuid, ensure_directory
import subprocess
import uuid
import sys
from markitdown import MarkItDown

def run_markitdown(file_path, output_path):
    try:
        md = MarkItDown(enable_plugins=False)
        result = md.convert(str(file_path))
        markdown_text = result.text_content

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        return True
    except Exception as e:
        print(f"MarkItDown failed: {e}")
        return False

def convert_all(source_root: Path, dest_root: Path, status_callback=None):
    count = 0
    for file in source_root.rglob("*"):
        if file.suffix.lower() not in [".pdf", ".docx"]:
            continue
        convert_file(file, source_root, dest_root, status_callback)
        count += 1
    return count

def convert_file(file_path, source_root, dest_root, status_callback=None):
    print(f"Running MarkItDown on: {file_path}")
    relative_path = file_path.parent.relative_to(source_root)
    dest_dir = dest_root / relative_path
    dest_dir.mkdir(parents=True, exist_ok=True)

    base_name = file_path.stem.lower().replace(" ", "-")
    md_path = dest_dir / f"{base_name}.md"
    file_uuid = uuid.uuid4().hex[:6].lower()
    media_dir = dest_root / "media" / file_uuid

    if status_callback:
        status_callback.set(f"Converting: {file_path.name}")

    success = run_markitdown(file_path, md_path)
    if not success or not md_path.exists():
        log_warning(dest_root / "conversion.log", f"Markdown NOT created for {file_path}")
        return

    ext = file_path.suffix.lower()
    if ext == ".pdf":
        extract_pdf_images(file_path, media_dir, file_uuid, md_path, dest_root / "image_warnings.log", dest_root / "image_processing.log")
    elif ext == ".docx":
        extract_docx_images(file_path, media_dir, file_uuid, md_path, dest_root / "image_warnings.log", dest_root / "image_processing.log")

    log_info(dest_root / "conversion.log", f"[{file_uuid}] Converted: {file_path} -> {md_path}")