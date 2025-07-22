# extract_pdf.py
import os, fitz, sys
from utils import log_info, log_warning, format_filename, generate_uuid, ensure_directory

def extract_pdf_images(pdf_path, media_dir, uuid, md_path, warn_log, info_log):
    log_info(info_log, f"Starting PDF processing: {pdf_path}")
    doc = fitz.open(pdf_path)
    rel_paths = []
    count = 1

    os.makedirs(media_dir, exist_ok=True)
    log_info(info_log, f"Media directory created: {media_dir}")

    for page_number in range(len(doc)):
        for img_index, img in enumerate(doc.get_page_images(page_number)):
            try:
                image = doc.extract_image(img[0])
                ext = image["ext"]
                img_data = image["image"]
                if len(img_data) < 1000:
                    log_info(info_log, f"Skipped small PDF image (under 1KB): p{page_number+1}")
                    continue
                filename = f"{uuid}-{count:03d}.{ext}"
                file_path = os.path.join(media_dir, filename)

                with open(file_path, "wb") as img_file:
                    img_file.write(img_data)

                rel_path = os.path.relpath(file_path, start=os.path.dirname(md_path)).replace(os.sep, '/')
                rel_paths.append(rel_path)
                log_info(info_log, f"Saved image {count}: {file_path}")
                count += 1
            except Exception as e:
                log_warning(warn_log, f"{pdf_path} p{page_number+1}: {e}")
                log_info(info_log, f"Failed to extract image p{page_number+1}: {e}")
    doc.close()

    # Inject links inline
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        updated_lines = []
        img_counter = 1

        for line in lines:
            trimmed = line.strip()
            if "](data:image/" in trimmed and trimmed.startswith("!["):
                img_path = rel_paths[img_counter - 1]
                updated_lines.append(f"![]({img_path})\n")
                log_info(info_log, f"Injected image link {img_counter}: {img_path}")
                img_counter += 1
            else:
                updated_lines.append(line)

        with open(md_path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)

        log_info(info_log, f"Completed PDF image injection for: {pdf_path}")
    except Exception as e:
        log_warning(warn_log, f"{pdf_path} inline injection error: {e}")
        log_info(info_log, f"Failed image injection: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 8:
        print("Usage: extract_pdf.py <file> <output_dir> <md_path> <warn_log> <dest_root> <uuid> <info_log>")
        sys.exit(1)

    file_path, output_dir, md_path, warn_log, dest_root, uuid, info_log = sys.argv[1:8]
    media_dir = os.path.join(dest_root, "media", uuid)
    extract_pdf_images(file_path, media_dir, uuid, md_path, warn_log, info_log)