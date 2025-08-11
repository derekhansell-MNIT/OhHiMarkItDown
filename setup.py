#setup.py
# This script sets up the environment for OhHiMarkItDown, including creating a virtual environment,
# installing dependencies, and initializing Marker models.
import subprocess, sys, os, json, shutil
from utils import log_info, log_warning, log_and_print, get_conversion_mode
from pathlib import Path
from env_check import verify_venv_components, ensure_valid_environment

venv_dir = Path("venv")
requirements = Path("requirements.txt")
app_entry = Path("app.py")
logs_dir = Path("logs")
setup_log = logs_dir / "setup.log"
logs_dir.mkdir(exist_ok=True)

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


def install_local_package(pip_exe, path, name):
    if path.exists():
        log_and_print(setup_log, f"[*] Installing local {name}...")
        result = subprocess.run([str(pip_exe), "install", "-e", str(path)], capture_output=True, text=True)
        log_info(setup_log, f"{name} install stdout:\n{result.stdout}")
        log_warning(setup_log, f"{name} install stderr:\n{result.stderr}")
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args)
    else:
        log_and_print(setup_log, f"[!] {name} install path not found: {path}")
        raise FileNotFoundError(f"{name} install path missing")

def initialize_marker_models(python_exe):
    code = r"""
import sys, json
try:
    from marker.models import create_model_dict
    model_names = sorted(list(create_model_dict().keys()))
    payload = {"ok": True, "models": model_names}
except Exception as e:
    payload = {"ok": False, "error": str(e)}
payload["sys_path"] = sys.path
try:
    import pkg_resources
    payload["packages"] = [str(d) for d in pkg_resources.working_set]
except:
    pass
print(json.dumps(payload))
"""
    result = subprocess.run([str(python_exe), "-c", code], capture_output=True, text=True)
    if result.returncode != 0:
        log_warning(setup_log, f"Marker init subprocess failed (rc={result.returncode}): {result.stderr.strip()}")
        raise RuntimeError("Failed to initialize Marker models")

    try:
        payload = json.loads(result.stdout.strip())
    except Exception as e:
        log_warning(setup_log, f"Marker init JSON error: {e}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        raise RuntimeError("Failed to parse Marker model output")

    if not payload.get("ok"):
        log_warning(setup_log, f"Marker model error: {payload.get('error')}")
        raise RuntimeError("Marker model initialization failed")

    log_info(setup_log, f"Marker models initialized:\n{json.dumps(payload, indent=2)}")
    log_and_print(setup_log, f"[*] Marker models initialized: {', '.join(payload['models'])}")

def create_venv():
    log_and_print(setup_log, "[*] Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    python_exe = venv_dir / "Scripts" / "python.exe"
    pip_exe = venv_dir / "Scripts" / "pip.exe"

    if not requirements.exists():
        log_and_print(setup_log, "[!] Missing requirements.txt")
        raise FileNotFoundError("requirements.txt not found")

    with requirements.open() as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    install_packages(pip_exe, packages)

    clone_repo("MarkItDown", "https://github.com/microsoft/markitdown.git", Path("markitdown"))
    clone_repo("Marker", "https://github.com/vikparuchuri/marker-pdf.git", marker_path)

    install_local_package(pip_exe, markitdown_path, "MarkItDown")
    install_local_package(pip_exe, marker_path, "Marker")

    initialize_marker_models(python_exe)
    mode = get_conversion_mode()
    log_info(setup_log, f"Conversion mode: {mode}")

def run_app():
    python_exe = venv_dir / "Scripts" / "python.exe"
    log_and_print(setup_log, "[*] Launching app...")
    subprocess.run([str(python_exe), str(app_entry)])

if __name__ == "__main__":
    if not venv_dir.exists():
        log_and_print(setup_log, "[setup] Virtual environment not found — creating...")
        create_venv()

    if not ensure_valid_environment(venv_dir, requirements, setup_log):
        log_and_print(setup_log, "[setup] Setup failed — environment not usable")
        sys.exit(1)

    log_and_print(setup_log, "[setup] Environment verified — launching application")
    run_app()