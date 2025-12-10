# extract_pdf.py
import os, re
from pathlib import Path
from typing import Dict, Iterable, Tuple
from utils import log_info, log_warning, ensure_directory

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered


def _normalize_images(images) -> Iterable[Tuple[str, object, str]]:
    """
    Normalize Marker image structures into (original_name, payload, ext).
    Handles dicts, lists/tuples, or pydantic objects with .name/.image/.content.
    """
    if images is None:
        return []

    if isinstance(images, dict):
        items = images.items()
    else:
        items = images

    out = []
    for item in items:
        if isinstance(images, dict):
            orig_name, obj = item
        else:
            if isinstance(item, (tuple, list)) and len(item) >= 2:
                orig_name, obj = item[0], item[1]
            else:
                # pydantic-ish
                orig_name = getattr(item, "name", getattr(item, "filename", f"image_{len(out)+1}"))
                obj = getattr(item, "image", getattr(item, "content", None))
        ext = Path(orig_name).suffix.lower() or ".png"
        out.append((orig_name, obj, ext))
    return out


def _save_image(obj, dest: Path) -> bool:
    """
    Save a Marker image payload to disk. Supports PIL.Image or raw bytes.
    """
    try:
        # PIL.Image path
        if hasattr(obj, "save"):
            obj.save(dest)
            return True
        # raw bytes
        if isinstance(obj, (bytes, bytearray)):
            dest.write_bytes(obj)
            return True
    except Exception:
        pass
    return False


_IMG_LINK_RE = re.compile(r'(!\[[^\]]*\]\()([^)]+)\)')

def _rewrite_md_links(md_text: str, mapping: Dict[str, Path], md_dir: Path) -> str:
    """
    Replace only image link targets that match Marker’s original filenames.
    mapping: original_name -> new_abs_path
    """
    def repl(m):
        target = m.group(2)
        # exact match first
        new_path = mapping.get(target)
        if not new_path:
            # try by basename (Marker sometimes prefixes ./)
            tgt_name = Path(target).name
            for k, p in mapping.items():
                if Path(k).name == tgt_name:
                    new_path = p
                    break
        if new_path:
            rel = os.path.relpath(new_path, start=md_dir).replace(os.sep, '/')
            return f"{m.group(1)}{rel})"
        return m.group(0)

    return _IMG_LINK_RE.sub(repl, md_text)


def process_pdf(pdf_path: Path,
                media_dir: Path,
                uuid: str,
                md_path: Path,
                warn_log: Path,
                info_log: Path,
                proc_log: Path,
                model_dict=None):
    """
    Fully Marker-based PDF conversion:
      - runs PdfConverter (markdown output)
      - saves images under /media/<uuid>/ as <uuid>-NNN.ext
      - rewrites image links in the markdown to the new relative paths
    """
    log_info(info_log, f"Starting PDF processing with Marker: {pdf_path}")
    ensure_directory(media_dir)

    # 1) Run Marker
    try:
        if model_dict is None:
            model_dict = create_model_dict()
        converter = PdfConverter(artifact_dict=model_dict)
        rendered = converter(str(pdf_path))
        md_text, _, images = text_from_rendered(rendered)  # md_text is already Markdown
    except Exception as e:
        log_warning(warn_log, f"Marker failed for {pdf_path}: {e}")
        return

    # 2) Save images to UUID folder and build rewrite map
    mapping: Dict[str, Path] = {}
    counter = 1
    for orig_name, payload, ext in _normalize_images(images):
        filename = f"{uuid}-{counter:03d}{ext or '.png'}"
        dest = media_dir / filename
        try:
            if _save_image(payload, dest):
                mapping[orig_name] = dest
                log_info(proc_log, f"Saved image {counter}: {dest}")
                counter += 1
            else:
                log_warning(warn_log, f"{pdf_path}: could not save image payload for {orig_name}")
        except Exception as e:
            log_warning(warn_log, f"{pdf_path}: error saving image {orig_name} — {e}")

    # 3) Rewrite image links in Markdown to relative paths
    try:
        md_text = _rewrite_md_links(md_text, mapping, md_path.parent)
    except Exception as e:
        log_warning(warn_log, f"{pdf_path}: link rewrite error — {e}")

    # 4) Write final Markdown
    try:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md_text, encoding="utf-8")
        log_info(info_log, f"Markdown written to: {md_path}")
    except Exception as e:
        log_warning(warn_log, f"Writing markdown failed for {pdf_path}: {e}")
