# extract_pdf.py
import os
import fitz  # PyMuPDF
from pathlib import Path
from bs4 import BeautifulSoup
from utils import log_info, log_warning
from markitdown import MarkItDown
from marker.models import create_model_dict
from marker.convert import convert_pdf

def extract_pdf_images(pdf_path, media_dir, uuid, proc_log, info_log, warn_log):
    doc = fitz.open(pdf_path)
    os.makedirs(media_dir, exist_ok=True)
    log_info(info_log, f"Media directory created: {media_dir}")

    image_map = {}  # page_num → list of image paths
    count = 1

    for page_num in range(len(doc)):
        for img in doc.get_page_images(page_num):
            try:
                image = doc.extract_image(img[0])
                ext = image["ext"]
                img_data = image["image"]
                if len(img_data) < 1000:
                    log_info(proc_log, f"Skipped small image on page {page_num+1}")
                    continue
                filename = f"{uuid}-{count:03d}.{ext}"
                file_path = os.path.join(media_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(img_data)
                rel_path = os.path.relpath(file_path, start=os.path.dirname(pdf_path)).replace(os.sep, '/')
                image_map.setdefault(page_num, []).append(rel_path)
                log_info(proc_log, f"Saved image {count}: {file_path}")
                count += 1
            except Exception as e:
                log_warning(warn_log, f"{pdf_path} p{page_num+1}: {e}")
    doc.close()
    return image_map

def inject_images_into_html(html_blocks, image_map):
    updated_html = ""
    for page_num, html in enumerate(html_blocks):
        soup = BeautifulSoup(html, "html.parser")
        if page_num in image_map:
            for img_path in image_map[page_num]:
                img_tag = soup.new_tag("img", src=img_path)
                soup.append(img_tag)
        updated_html += str(soup)
    return updated_html

def convert_html_to_markdown(html_string: str) -> str:
    md = MarkItDown(enable_plugins=False)
    result = md.convert_local(html_string.encode("utf-8"), input_format="html")
    return result.text_content

def process_pdf(pdf_path, media_dir, uuid, md_path, warn_log, info_log, proc_log, model_dict=None):
    log_info(info_log, f"Starting PDF processing: {pdf_path}")

    if model_dict is None:
        log_info(info_log, "Initializing Marker models...")
        model_dict = create_model_dict()

    image_map = extract_pdf_images(pdf_path, media_dir, uuid, proc_log, info_log, warn_log)

    html_blocks = convert_pdf(
        pdf_path=str(pdf_path),
        model_dict=model_dict,
        return_blocks=True,
        return_plaintext=False
    )

    full_html = inject_images_into_html(html_blocks, image_map)
    markdown = convert_html_to_markdown(full_html)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    log_info(info_log, f"Markdown written to: {md_path}")
