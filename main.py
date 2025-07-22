from pathlib import Path
from extract_pdf import extract_pdf_images
from extract_docx import extract_docx_images
from utils import log_info, log_warning
import uuid
from markitdown import MarkItDown

# Centralize log configuration
logs_dir = Path("logs")
conversion_log = logs_dir / "conversion.log"
image_warnings_log = logs_dir / "image_warnings.log"
image_processing_log = logs_dir / "image_processing.log"

def run_markitdown(file_path: Path, output_path: Path, log_path: Path):
    try:
        md = MarkItDown(enable_plugins=False)
        result = md.convert(str(file_path))
        markdown_text = result.text_content

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        return True
    except Exception as e:
        log_warning(log_path, f"MarkItDown failed for {file_path}: {e}")
        return False

def convert_all(source_root: Path, dest_root: Path, status_callback=None):
    # Ensure log directory exists before starting
    logs_dir.mkdir(exist_ok=True)
    count = 0
    for file in source_root.rglob("*"):
        if file.suffix.lower() not in [".pdf", ".docx"]:
            continue
        convert_file(file, source_root, dest_root, status_callback,
                     conversion_log, image_warnings_log, image_processing_log)
        count += 1
    return count

def convert_file(file_path: Path, source_root: Path, dest_root: Path, status_callback,
                 conv_log: Path, warn_log: Path, proc_log: Path):
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

    success = run_markitdown(file_path, md_path, conv_log)
    if not success or not md_path.exists():
        return

    ext = file_path.suffix.lower()
    if ext == ".pdf":
        extract_pdf_images(file_path, media_dir, file_uuid, md_path, warn_log, proc_log)
    elif ext == ".docx":
        extract_docx_images(file_path, media_dir, file_uuid, md_path, warn_log, proc_log)

    log_info(conv_log, f"[{file_uuid}] Converted: {file_path} -> {md_path}")