import os
from datetime import datetime
from pathlib import Path

def log_info(log_path, message):
    _write_log(log_path, "INFO", message)

def log_warning(log_path, message):
    _write_log(log_path, "WARNING", message)

def _write_log(log_path, level, message):
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} - {level}: {message}\n")

def format_filename(name: str) -> str:
    """Convert a filename to lowercase, dash-separated format."""
    return name.lower().replace(" ", "-")

def generate_uuid(length=6) -> str:
    """Generate a short UUID string."""
    import uuid
    return uuid.uuid4().hex[:length].lower()

def ensure_directory(path: Path):
    """Create a directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)