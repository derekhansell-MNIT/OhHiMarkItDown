# extract_pdf.py
import os
import fitz
from pathlib import Path

from utils import log_info, log_warning
from image_utils import rewrite_markdown_images

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered


# ---------------------------------------------------------------------------
# GPU-accelerated Marker conversion (Python API)
# ---------------------------------------------------------------------------

def run_marker_single(pdf_path):
    """
    Convert a PDF to Markdown using Marker (GPU-accelerated if available).
    Returns the Markdown text.
    """
    try:
        # Load models (GPU or CPU automatically)
        artifact_dict = create_model_dict()

        # Create converter
        converter = PdfConverter(
            artifact_dict=artifact_dict,
        )

        # Run conversion
        rendered = converter(str(pdf_path))

        # Extract text + images
        text, _, images = text_from_rendered(rendered)

        return text

    except Exception as e:
        raise RuntimeError(f"Marker conversion failed: {e}")


# ---------------------------------------------------------------------------
# Image extraction (unchanged)
# ---------------------------------------------------------------------------

def extract_pdf_images(pdf_path, media_dir, info_log, warn_log):
    """
    Extract images from the PDF using PyMuPDF.
    Returns a list of relative paths to the extracted images.
    """
    rel_paths = []
    try:
        doc = fitz.open(pdf_path)
        counter = 1

        for page_index in range(len(doc)):
            for img in doc.get_page_images(page_index):
                xref = img[0]
                base_image = doc.extract_image(xref)
                img_bytes = base_image["image"]
                ext = base_image["ext"]

                filename = f"{counter:03d}.{ext}"
                dest = os.path.join(media_dir, filename)

                with open(dest, "wb") as img_file:
                    img_file.write(img_bytes)

                rel_paths.append(filename)
                log_info(info_log, f"Saved PDF image {counter}: {dest}")
                counter += 1

        doc.close()
    except Exception as e:
        log_warning(warn_log, f"{pdf_path}: error extracting images: {e}")

    return rel_paths


# ---------------------------------------------------------------------------
# Full PDF processing pipeline
# ---------------------------------------------------------------------------

def process_pdf(pdf_path, media_dir, uuid, md_path, warn_log, info_log, proc_log, model_dict=None):
    """
    Full PDF processing pipeline:
    1. Convert PDF to Markdown using Marker (GPU-accelerated)
    2. Extract images with PyMuPDF
    3. Rewrite Markdown image links to point to extracted images
    """
    log_info(info_log, f"Starting PDF processing: {pdf_path}")
    os.makedirs(media_dir, exist_ok=True)

    # Step 1: Run Marker to get Markdown
    try:
        md_result = run_marker_single(pdf_path)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_result)
        log_info(info_log, f"Marker wrote Markdown: {md_path}")
    except Exception as e:
        log_warning(warn_log, f"Marker failed for {pdf_path}: {e}")
        return

    # Step 2: Extract images
    rel_paths = extract_pdf_images(pdf_path, media_dir, info_log, warn_log)

    # Step 3: Rewrite Markdown image links
    if rel_paths:
        rewrite_markdown_images(md_path, rel_paths, info_log, warn_log)
        log_info(info_log, f"Completed image rewriting for: {md_path}")
