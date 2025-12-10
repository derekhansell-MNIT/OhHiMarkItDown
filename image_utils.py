# image_utils.py
import os, shutil, re
from pathlib import Path
from PIL import Image
from utils import log_info, log_warning

# Match inline base64 images
DATA_IMG_RE = re.compile(r'!\[[^\]]*\]\(data:image/[^)]+\)', re.IGNORECASE)

# Match DOCX-style image placeholders (image1.png, image2.jpg, etc.)
LOCAL_DOCX_IMG_RE = re.compile(r'!\[[^\]]*\]\(\s*(?:\.?/)?(?:image\d+\.(?:png|jpe?g|gif|bmp|webp))\s*\)',
    re.IGNORECASE
)

def save_and_rename_images(src_dir: Path, media_root: Path, uuid: str, md_path: Path, info_log: Path, warn_log: Path):
    """
    Save images into /media/<UUID>/ with UUID-based filenames.
    Returns a list of relative paths for Markdown injection.
    """
    media_dir = media_root / uuid
    media_dir.mkdir(parents=True, exist_ok=True)

    rel_paths = []
    counter = 1

    for img_path in sorted(Path(src_dir).iterdir()):
        src = Path(src_dir) / img_path
        try:
            with Image.open(src) as img:
                img = img.convert("RGB")
                width, height = img.size

            # Skip solid-color images
            if len(img.getcolors(width * height)) == 1:
                log_info(info_log, f"Skipped solid color image: {src}")
                continue

            ext = src.suffix or ".jpg"
            dest = media_dir / f"{uuid}-{counter:03d}{ext}"
            shutil.move(str(src), dest)

            # Correct relative path: media/<UUID>/<UUID>-001.jpg
            rel_path = Path(os.path.relpath(dest, md_path.parent)).as_posix()
            rel_paths.append(rel_path)

            log_info(info_log, f"Saved image {counter}: {dest}")
            counter += 1

        except Exception as e:
            log_warning(warn_log, f"{md_path} — error processing image {src}: {e}")

    return rel_paths


def rewrite_markdown_images(md_path: Path, rel_paths: list, info_log: Path, warn_log: Path):
    """
    Replace Markdown image links with our saved /media/UUID/... paths.
    - First pass: inline data:image blobs
    - Second pass: DOCX-style local filenames (image1.png, image2.jpg)
    """
    try:
        text = Path(md_path).read_text(encoding="utf-8")
    except Exception as e:
        log_warning(warn_log, f"{md_path} — could not read for image rewrite: {e}")
        return

    idx = 0

    def repl(_match):
        nonlocal idx
        if idx < len(rel_paths):
            out = f"![]({rel_paths[idx]})"
            log_info(info_log, f"Injected image link {idx+1}: {rel_paths[idx]}")
            idx += 1
            return out
        else:
            log_warning(warn_log, f"{md_path} — Not enough extracted images while rewriting")
            return "[[IMAGE MISSING]]"

    # Pass 1: replace inline base64 images
    text = DATA_IMG_RE.sub(repl, text)

    # Pass 2: replace DOCX-style image placeholders
    text = LOCAL_DOCX_IMG_RE.sub(repl, text)

    try:
        Path(md_path).write_text(text, encoding="utf-8")
        log_info(info_log, f"Completed image injection for: {md_path} (used {idx}/{len(rel_paths)} images)")
    except Exception as e:
        log_warning(warn_log, f"{md_path} — failed to write rewritten markdown: {e}")
