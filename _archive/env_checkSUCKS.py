# env_check.py
import subprocess, re, shlex
from pathlib import Path
from utils import check_gpu_available, log_and_print, log_info, log_warning

# Import names the app actually uses at runtime
ESSENTIAL_IMPORTS = [
    "bs4",            # beautifulsoup4
    "markdownify",
    "docx2txt",
    "fitz",           # PyMuPDF
    "pygments",
    "requests",
    "markitdown",
    "marker.models",  # be strict about marker import path
]

def _parse_requirements(requirements_path: Path) -> list[str]:
    """
    Returns install names for pip show. Handles versions, extras, inline comments.
    Skips -e, -r, VCS, and local paths (these are verified via import checks).
    """
    names = []
    text = requirements_path.read_text(encoding="utf-8").splitlines()
    for raw in text:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-e ", "--editable", "-r ", "--requirement")):
            continue
        if "://" in line or " @ " in line:
            # VCS or direct URL; rely on import checks
            continue
        # strip inline comments
        line = line.split("#", 1)[0].strip()
        # strip extras like pkg[extra]
        base = re.split(r"\[.*\]", line)[0]
        # strip version specifiers (==, >=, <=, ~=, !=, ===, >, <)
        base = re.split(r"[><=!~]=?|;|\s", base)[0]
        if base:
            names.append(base)
    return names

def _import_check(python_exe: Path, module: str) -> tuple[bool, str]:
    cmd = [str(python_exe), "-c", f"import {module}"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode == 0, (proc.stderr or proc.stdout or "").strip()

def ensure_valid_environment(
    venv_dir: Path,
    requirements_path: Path,
    setup_log: Path,
    log_func=log_and_print,
    max_attempts: int = 2
) -> bool:
    """
    Verifies that the venv environment is intact and importable.
    Attempts remediation (install -r requirements.txt) if verification fails.
    Returns True if environment passes verification, False otherwise.
    """
    pip_exe = venv_dir / "Scripts" / "pip.exe"

    attempt = 1
    while attempt <= max_attempts:
        log_func(setup_log, f"[env-check] Attempt {attempt}: verifying environment")
        verified = verify_venv_components(
            venv_dir,
            setup_log,
            log_func,
            requirements_path=requirements_path
        )
        if verified:
            return True

        if not requirements_path.exists():
            log_func(setup_log, "[env-check] requirements.txt not found — cannot attempt remediation")
            return False

        log_func(setup_log, f"[env-check] Verification failed — attempting remediation using {requirements_path}")
        result = subprocess.run(
            [str(pip_exe), "install", "-r", str(requirements_path)],
            capture_output=True,
            text=True
        )
        log_info(setup_log, f"[remediation] stdout:\n{result.stdout.strip()}")
        log_warning(setup_log, f"[remediation] stderr:\n{result.stderr.strip()}")

        attempt += 1

    log_func(setup_log, "[env-check] Final verification failed after remediation attempts")
    return False

def verify_venv_components(venv_dir: Path, setup_log: Path, log_func=log_and_print, requirements_path: Path | None = None) -> bool:
    pip_exe = venv_dir / "Scripts" / "pip.exe"
    python_exe = venv_dir / "Scripts" / "python.exe"

    missing: list[str] = []
    problems: list[str] = []

    if not pip_exe.exists():
        missing.append("pip.exe")
    if not python_exe.exists():
        missing.append("python.exe")

    # GPU probe (informational)
    gpu_status = check_gpu_available()
    if gpu_status is None:
        log_warning(setup_log, "torch not installed — skipping GPU check")
    elif not gpu_status:
        log_warning(setup_log, "GPU not available — running in CPU mode")
    else:
        try:
            import torch  # type: ignore
            log_info(setup_log, f"GPU detected: {torch.cuda.get_device_name(0)}")
            log_info(setup_log, f"CUDA version: {torch.version.cuda}")
        except Exception as e:
            log_warning(setup_log, f"GPU detected but query failed: {e}")

    # requirements.txt presence checks via pip show
    if requirements_path and Path(requirements_path).exists():
        for name in _parse_requirements(Path(requirements_path)):
            proc = subprocess.run([str(pip_exe), "show", name], capture_output=True, text=True)
            if proc.returncode != 0:
                missing.append(f"pip: {name}")
    else:
        log_warning(setup_log, "No requirements.txt provided — relying on import checks")

    # Runtime importability checks
    for mod in ESSENTIAL_IMPORTS:
        ok, msg = _import_check(python_exe, mod)
        if not ok:
            problems.append(f"import: {mod} -> {msg or 'failed'}")

    if missing or problems:
        log_func(setup_log, "[!] Missing/failed components in venv:")
        print("Missing or broken components:")
        for item in missing:
            print(f"  [pip]    {item}")
            log_info(setup_log, f"   - {item}")
        for item in problems:
            print(f"  [import] {item}")
            log_info(setup_log, f"   - {item}")
        return False  # ← this is the fix

    log_info(setup_log, "[✓] Environment verified: packages present and importable")
    return True
