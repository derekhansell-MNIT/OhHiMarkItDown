import subprocess
import sys
import os
from pathlib import Path

venv_dir = Path("venv")
requirements = Path("requirements.txt")
app_entry = Path("app.py")
markitdown_path = Path("markitdown") / "packages" / "markitdown"

def install_local_markitdown(pip_exe):
    
    if markitdown_path.exists():
        print("[*] Installing local MarkItDown...")
        result = subprocess.run(
            [str(pip_exe), "install", "-e", f"{markitdown_path}[all]"],
            capture_output=True,
            text=True
        )
        print("stdout:\n", result.stdout)
        print("stderr:\n", result.stderr)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args)
    else:
        print("[!] MarkItDown install path not found:", markitdown_path)

def create_venv():
    print("[*] Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    pip_exe = venv_dir / "Scripts" / "pip.exe"
    print("[*] Installing dependencies...")
    subprocess.run([str(pip_exe), "install", "-r", str(requirements)], check=True)

    install_local_markitdown(pip_exe)

def run_app():
    python_exe = venv_dir / "Scripts" / "python.exe"
    print("[*] Launching OhHiMarkItDown...")
    subprocess.run([str(python_exe), str(app_entry)])

if __name__ == "__main__":
    if not venv_dir.exists():
        create_venv()
    run_app()