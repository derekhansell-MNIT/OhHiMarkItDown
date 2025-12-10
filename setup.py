# setup.py
# Environment setup for OhHiMarkItDown:
# - Create virtual environment
# - Install dependencies
# - Clone and install MarkItDown (local editable install)

import subprocess
import sys
from pathlib import Path
<<<<<<< Updated upstream
from env_check import verify_venv_components, ensure_valid_environment
=======

from utils import (
    log_info,
    log_warning,
    log_and_print,
    clone_repo,
    install_packages,
    install_local_package
)

#from torch_setup import install_torch_stack
#from marker_setup import initialize_marker


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
>>>>>>> Stashed changes

venv_dir = Path("venv")
requirements = Path("requirements.txt")
app_entry = Path("app.py")

logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)
setup_log = logs_dir / "setup.log"

<<<<<<< Updated upstream
markitdown_path = Path("markitdown") / "packages" / "markitdown"
marker_path = Path("marker")  # Local clone target for marker-pdf

def install_packages(pip_exe, packages):
    for pkg in packages:
        log_and_print(setup_log, f"[*] Installing package: {pkg}")
        result = subprocess.run([str(pip_exe), "install", pkg], capture_output=True, text=True)
        log_info(setup_log, f"{pkg} stdout:\n{result.stdout.strip()}")
        log_warning(setup_log, f"{pkg} stderr:\n{result.stderr.strip()}")
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args)

def clone_repo(name, url, dest_path):
    if dest_path.exists():
        print(f"[*] {name} already exists at {dest_path}. Removing and recloning...")
        try:
            shutil.rmtree(dest_path)
        except Exception as e:
            print(f"[!] Failed to remove {dest_path}: {e}")
            raise
    try:
        result = subprocess.run(
            ["git", "clone", url, str(dest_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"[✓] Cloned {name} successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[✗] Failed to clone {name}. Git said:\n{e.stderr}")
        raise
=======
markitdown_repo_path = Path("markitdown")
markitdown_pkg_path = markitdown_repo_path / "packages" / "markitdown"
>>>>>>> Stashed changes


# ---------------------------------------------------------------------------
# Virtual environment creation
# ---------------------------------------------------------------------------

def create_venv():
    log_and_print(setup_log, "[*] Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    python_exe = venv_dir / "Scripts" / "python.exe"
    pip_exe = venv_dir / "Scripts" / "pip.exe"

    # Upgrade pip
    log_and_print(setup_log, "[*] Upgrading pip in the virtual environment...")
    result = subprocess.run(
        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
        capture_output=True,
        text=True
    )
    log_info(setup_log, f"pip upgrade stdout:\n{result.stdout.strip()}")
    log_warning(setup_log, f"pip upgrade stderr:\n{result.stderr.strip()}")
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    # Install correct PyTorch stack (GPU or CPU)
    #log_and_print(setup_log, "[*] Installing PyTorch stack (GPU-aware)...")
    #install_torch_stack(python_exe, pip_exe, setup_log)
    
    # Install requirements.txt
    with requirements.open() as f:
        packages = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]
    install_packages(pip_exe, packages, setup_log)

    # Clone MarkItDown repo
    clone_repo(
        "MarkItDown",
        "https://github.com/microsoft/markitdown.git",
        markitdown_repo_path,
        setup_log
    )

<<<<<<< Updated upstream
    clone_repo("MarkItDown", "https://github.com/microsoft/markitdown.git", Path("markitdown"))
    clone_repo("Marker", "https://github.com/vikparuchuri/marker-pdf.git", marker_path)
=======
    # Install MarkItDown (editable)
    install_local_package(
        pip_exe,
        markitdown_pkg_path,
        extras="docx",
        setup_log=setup_log
    )
>>>>>>> Stashed changes


    log_info(setup_log, "Setup complete.")


# ---------------------------------------------------------------------------
# Launch application
# ---------------------------------------------------------------------------

def run_app():
    python_exe = venv_dir / "Scripts" / "python.exe"
    log_and_print(setup_log, "[*] Launching app...")
    subprocess.run([str(python_exe), str(app_entry)])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
<<<<<<< Updated upstream
    if not venv_dir.exists():
        log_and_print(setup_log, "[setup] Virtual environment not found — creating...")
        create_venv()

    if not ensure_valid_environment(venv_dir, requirements, setup_log):
        log_and_print(setup_log, "[setup] Setup failed — environment not usable")
        sys.exit(1)

    log_and_print(setup_log, "[setup] Environment verified — launching application")
    run_app()
=======
    create_venv()
    run_app()
>>>>>>> Stashed changes
