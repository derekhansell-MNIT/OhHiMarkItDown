# setup.py
# Environment setup for OhHiMarkItDown:
# - Create virtual environment
# - Install dependencies
# - Clone and install MarkItDown (local editable install)

import subprocess
import sys
from pathlib import Path

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

venv_dir = Path("venv")
requirements = Path("requirements.txt")
app_entry = Path("app.py")

logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)
setup_log = logs_dir / "setup.log"

markitdown_repo_path = Path("markitdown")
markitdown_pkg_path = markitdown_repo_path / "packages" / "markitdown"


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

    # Install MarkItDown (editable)
    install_local_package(
        pip_exe,
        markitdown_pkg_path,
        extras="docx",
        setup_log=setup_log
    )


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
    create_venv()
    run_app()
