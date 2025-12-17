# env_check.py
import subprocess, re
from pathlib import Path
from utils import check_gpu_available, log_and_print, log_info, log_warning

def verify_venv_components(venv_dir, setup_log, log_and_print, requirements_path=None):
    missing = []
    pip_exe = venv_dir / "Scripts" / "pip.exe"
    python_exe = venv_dir / "Scripts" / "python.exe"

    if not pip_exe.exists():
        missing.append("pip.exe")
    if not python_exe.exists():
        missing.append("python.exe")

    gpu_status = check_gpu_available()
    if gpu_status is None:
        missing.append("torch (required for GPU check)")
    elif not gpu_status:
        log_warning(setup_log, "GPU not available – Marker will run in CPU mode")
        log_info(setup_log, "Running in CPU-only mode")
    else:
        try:
            import torch
            gpu_name = torch.cuda.get_device_name(0)
            cuda_version = torch.version.cuda
            log_info(setup_log, f"GPU detected: {gpu_name}")
            log_info(setup_log, f"CUDA version: {cuda_version}")
        except Exception as e:
            log_warning(setup_log, f"GPU detected but name lookup failed: {e}")
            log_info(setup_log, "Running in CPU-only mode due to GPU query failure")

    # Check for required Python modules
    try:
        subprocess.run([str(python_exe), "-c", "import markitdown"], check=True)
    except subprocess.CalledProcessError:
        missing.append("markitdown")

    try:
        subprocess.run([str(python_exe), "-c", "import marker"], check=True)
    except subprocess.CalledProcessError:
        missing.append("marker")

    # Check all packages in requirements.txt
    if requirements_path and Path(requirements_path).exists():
        with open(requirements_path, "r") as f:
            for line in f:
                pkg = line.strip()
                if not pkg or pkg.startswith("#"):
                    continue
                # Strip extras like [full]
                base_pkg = re.split(r"\[.*\]", pkg)[0]
                try:
                    subprocess.run([str(pip_exe), "show", base_pkg], check=True, stdout=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    missing.append(pkg)

    if missing:
        log_and_print(setup_log, f"[!] Missing components in venv: {', '.join(missing)}")
        return False
    return True