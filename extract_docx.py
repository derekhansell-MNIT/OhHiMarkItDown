# extract_docx.py
import os, docx2txt, shutil, re, sys
from PIL import Image
from utils import log_info, log_warning, format_filename, generate_uuid, ensure_directory

def split_embedded_images(line):
    # Find all Markdown image tags
    parts = re.split(r'(!\[[^\]]*\]\([^)]+\))', line)
    return [part.strip() for part in parts if part.strip()]

def extract_docx_images(docx_path, media_dir, uuid, md_path, warn_log, info_log):
    log_info(info_log, f"Starting DOCX processing: {docx_path}")
    temp_dir = temp_dir = media_dir.parent / (media_dir.name + "_tmp")
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(media_dir, exist_ok=True)
    log_info(info_log, f"Media directory created: {media_dir}")

    try:
        docx2txt.process(docx_path, temp_dir)
        log_info(info_log, f"docx2txt processed images to temp dir: {temp_dir}")
    except Exception as e:
        log_warning(warn_log, f"{docx_path} docx2txt error: {e}")
        log_info(info_log, f"Failed to process DOCX: {e}")
        return

    rel_paths = []
    counter = 1
    for img_file in sorted(os.listdir(temp_dir)):
    #for img_file in sorted(os.listdir(temp_dir), key=lambda f: os.path.getmtime(os.path.join(temp_dir, f))):

        src = os.path.join(temp_dir, img_file)
        try:
            with Image.open(src) as img:
                img = img.convert("RGB")
                width, height = img.size

            # Solid color test
            if len(img.getcolors(width * height)) == 1:
                log_info(info_log, f"Skipped solid color image: {src}")
                continue

            # #if os.path.getsize(src) < 1000:
            #     log_info(info_log, f"Skipped image under 1KB (likely artifact): {src}")
            #     continue

            # if width <= 60 or height <= 60:
            #     log_info(info_log, f"Skipped image with small dimensions ({width}x{height}): {src}")
            #     continue

            ext = os.path.splitext(img_file)[1]
            dest = os.path.join(media_dir, f"{uuid}-{counter:03d}{ext}")
            shutil.move(src, dest)
            rel_path = os.path.relpath(dest, start=os.path.dirname(md_path)).replace(os.sep, '/')
            rel_paths.append(rel_path)
            log_info(info_log, f"Saved image {counter}: {dest}")
            counter += 1
        except Exception as e:
            log_warning(warn_log, f"{docx_path}: {e}")
            log_info(info_log, f"Failed to process DOCX image: {src} — {e}")

    shutil.rmtree(temp_dir, ignore_errors=True)

    # Inject links inline
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines(keepends=True)

        updated_lines = []
        img_counter = 1

        for line in lines:
            if "](data:image/" in line and line.startswith("!["):
                # Line contains only an image tag
                if img_counter <= len(rel_paths):
                    img_path = rel_paths[img_counter - 1]
                    updated_lines.append(f"![]({img_path})\n")
                    log_info(info_log, f"Injected image link {img_counter}: {img_path}")
                    img_counter += 1
                else:
                    log_warning(warn_log, f"{md_path} — Not enough extracted images for embedded image at line: {line.strip()}")
                    updated_lines.append("[[IMAGE MISSING]]\n")

            elif "](data:image/" in line:
            # Line contains embedded image(s) mixed with text
                parts = re.split(r'(!\[[^\]]*\]\([^)]+\))', line)
                for part in parts:
                    if "](data:image/" in part and part.startswith("!["):
                        if img_counter <= len(rel_paths):
                            img_path = rel_paths[img_counter - 1]
                            # ✅ Ensure image starts on a new line
                            updated_lines.append(f"\n![]({img_path})\n")
                            log_info(info_log, f"Injected image link {img_counter}: {img_path}")
                            img_counter += 1
                        else:
                            log_warning(warn_log, f"{md_path} — Not enough extracted images for embedded image at part: {part}")
                            updated_lines.append("\n[[IMAGE MISSING]]\n")
                    else:
                        updated_lines.append(part)  # preserve original formatting

            else:
                updated_lines.append(line)  # untouched non-image line

        with open(md_path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)

        log_info(info_log, f"Completed image injection for: {md_path}")

    except Exception as e:
        log_warning(warn_log, f"{md_path} inline injection error: {e}")
        log_info(info_log, f"Failed image injection: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 8:
        print("Usage: extract_docx.py <file> <output_dir> <md_path> <warn_log> <dest_root> <uuid> <info_log>")
        sys.exit(1)

    file_path, output_dir, md_path, warn_log, dest_root, uuid, info_log = sys.argv[1:8]
    media_dir = os.path.join(dest_root, "media", uuid)
    ext = os.path.splitext(file_path)[1].lower()
    extract_docx_images(file_path, media_dir, uuid, md_path, warn_log, info_log)