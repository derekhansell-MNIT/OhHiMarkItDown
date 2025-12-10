import subprocess
import sys
import re

from utils import (
    log_info,
    log_warning,
    log_and_print,
    run_pip,
)


# -----------------------------
# GPU + CUDA detection
# -----------------------------

def has_nvidia_gpu():
    """Return True if nvidia-smi is available and reports a GPU."""
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def has_nvidia_gpu_wmi():
    """Fallback detection using Windows WMI."""
    try:
        result = subprocess.run(
            ["wmic", "path", "win32_VideoController", "get", "name"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return "NVIDIA" in result.stdout
    except Exception:
        return False


def get_cuda_driver_version():
    """
    Parse CUDA driver version from nvidia-smi output.
    Example: "CUDA Version: 12.8"
    """
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            return None

        match = re.search(r"CUDA Version:\s+(\d+\.\d+)", result.stdout)
        if match:
            return match.group(1)
        return None

    except FileNotFoundError:
        return None


def select_cuda_suffix(cuda_driver_version):
    """
    Map CUDA driver version to the correct PyTorch cuXX wheel suffix.
    """
    if cuda_driver_version is None:
        return None

    major, minor = map(int, cuda_driver_version.split("."))

    if major == 12:
        if minor <= 1:
            return "cu121"
        elif minor <= 4:
            return "cu124"
        else:
            return "cu128"

    if major == 13:
        return "cu13x"  # placeholder for future wheels

    return None


# -----------------------------
# Python ABI detection
# -----------------------------

def get_python_abi_tag():
    """
    Return cp310, cp311, cp312, cp313, etc.
    """
    major, minor = sys.version_info[:2]
    return f"cp{major}{minor}"


# -----------------------------
# Torch + Torchvision installer
# -----------------------------

def install_torch_stack(python_exe, pip_exe, setup_log):
    """
    Install the correct torch + torchvision stack based on:
    - Python ABI
    - GPU presence
    - CUDA driver version
    """

    # Detect Python ABI
    py_tag = get_python_abi_tag()
    log_and_print(setup_log, f"[*] Python ABI detected: {py_tag}")

    # Detect GPU + CUDA
    gpu_present = has_nvidia_gpu() or has_nvidia_gpu_wmi()
    cuda_driver = get_cuda_driver_version()

    if gpu_present:
        log_and_print(setup_log, "[*] NVIDIA GPU detected.")
        log_and_print(setup_log, f"[*] CUDA driver version: {cuda_driver or 'unknown'}")

        cuda_suffix = select_cuda_suffix(cuda_driver)

        if cuda_suffix is None:
            log_warning(setup_log, "Unable to determine CUDA suffix. Falling back to CPU-only install.")
            gpu_present = False
        else:
            log_and_print(setup_log, f"[*] Selecting PyTorch wheels for {cuda_suffix}.")

    # -----------------------------
    # GPU path: install CUDA wheels
    # -----------------------------
    if gpu_present:
        torch_wheel = (
            f"https://download.pytorch.org/whl/{cuda_suffix}/"
            f"torch-2.9.1%2B{cuda_suffix}-{py_tag}-{py_tag}-win_amd64.whl"
        )
        torchvision_wheel = (
            f"https://download.pytorch.org/whl/{cuda_suffix}/"
            f"torchvision-0.24.1%2B{cuda_suffix}-{py_tag}-{py_tag}-win_amd64.whl"
        )

        log_and_print(setup_log, f"[*] Installing torch ({cuda_suffix})...")
        run_pip(pip_exe, ["install", torch_wheel], setup_log)

        log_and_print(setup_log, f"[*] Installing torchvision ({cuda_suffix})...")
        run_pip(pip_exe, ["install", torchvision_wheel], setup_log)

    # -----------------------------
    # CPU fallback path
    # -----------------------------
    else:
        log_and_print(setup_log, "[*] Installing CPU-only PyTorch...")
        run_pip(pip_exe, ["install", "torch==2.9.1", "torchvision==0.24.1"], setup_log)

    # -----------------------------
    # Post-install verification
    # -----------------------------
    verify_script = r"""
        import torch, torchvision
        print("torch:", torch.__version__)
        print("torchvision:", torchvision.__version__)
        print("cuda available:", torch.cuda.is_available())
        if torch.cuda.is_available():
            print("device:", torch.cuda.get_device_name(0))
        """

    result = subprocess.run(
        [str(python_exe), "-c", verify_script],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        log_info(setup_log, result.stdout.strip())
    if result.stderr.strip():
        log_warning(setup_log, result.stderr.strip())
