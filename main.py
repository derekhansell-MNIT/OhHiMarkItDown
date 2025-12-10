# main.py
from pathlib import Path
from extract_docx import process_docx
from utils import log_info
import uuid

# Centralize log configuration
logs_dir = Path("logs")
conversion_log = logs_dir / "conversion.log"
image_warnings_log = logs_dir / "image_warnings.log"
image_processing_log = logs_dir / "image_processing.log"

def convert_all(source_root: Path, dest_root: Path, status_callback=None):
    logs_dir.mkdir(exist_ok=True)
    count = 0

    for file in source_root.rglob("*"):
        # DOCX-only pipeline
        if file.suffix.lower() != ".docx":
            continue

        if status_callback and status_callback.should_stop():
            log_info(Path("logs") / "setup.log", "Conversion stopped by user.")
            break

        convert_file(
            file_path=file,
            source_root=source_root,
            dest_root=dest_root,
            status_callback=status_callback,
            conv_log=conversion_log,
            warn_log=image_warnings_log,
            proc_log=image_processing_log,
        )
        count += 1

    return count


def convert_file(file_path: Path, source_root: Path, dest_root: Path, status_callback,
                 conv_log: Path, warn_log: Path, proc_log: Path):

    # Recreate folder structure
    relative_path = file_path.parent.relative_to(source_root)
    dest_dir = dest_root / relative_path
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Markdown output path
    base_name = file_path.stem.lower().replace(" ", "-")
    md_path = dest_dir / f"{base_name}.md"

    # UUID for this DOCX
    file_uuid = uuid.uuid4().hex[:6].lower()

    # /media/<UUID>
    media_dir = dest_root / "media" / file_uuid

    if status_callback:
        status_callback.set(f"Converting: {file_path.name}")

    # DOCX-only
    process_docx(file_path, media_dir, file_uuid, md_path, warn_log, proc_log)

    log_info(conv_log, f"[{file_uuid}] Converted: {file_path} -> {md_path}")