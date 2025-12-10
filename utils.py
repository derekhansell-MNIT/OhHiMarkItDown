# utils.py
import datetime
import os
import sys
import subprocess

def timestamp() -> str:
    """Return a UTC timestamp string for logs."""
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def log_info(log_file, message: str):
    """Log informational messages to file and stdout."""
    line = f"[INFO] {timestamp()} {message}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def log_warning(log_file, message: str):
    """Log warning messages to file and stdout."""
    line = f"[WARN] {timestamp()} {message}"
    print(line, file=sys.stderr)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def log_and_print(log_file, message: str):
    """Log and print a message (neutral severity)."""
    line = f"{timestamp()} {message}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def install_packages(pip_exe, packages, setup_log):
    for pkg in packages:
        log_and_print(setup_log, f"[*] Installing package: {pkg}")
        result = subprocess.run(
            [str(pip_exe), "install", pkg],
            capture_output=True,
            text=True
        )
        log_info(setup_log, f"{pkg} stdout:\n{result.stdout.strip()}")
        log_warning(setup_log, f"{pkg} stderr:\n{result.stderr.strip()}")
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args)
        

def install_local_package(pip_exe, path, extras, setup_log):
    if not path.exists():
        log_and_print(setup_log, f"[!] Local package path not found: {path}")
        raise FileNotFoundError(f"Local package path missing")

    extras_suffix = f"[{extras}]" if extras else ""
    target = f"{path}{extras_suffix}"

    log_and_print(setup_log, f"[*] Installing local package: {target}")
    result = subprocess.run(
        [str(pip_exe), "install", "-e", target],
        capture_output=True,
        text=True
    )

    log_info(setup_log, f"Local install stdout:\n{result.stdout}")
    log_warning(setup_log, f"Local install stderr:\n{result.stderr}")

    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, result.args)

    
        
def run_pip(pip_exe, args, setup_log):
    """Run pip with full argument control and logging."""
    result = subprocess.run(
        [str(pip_exe)] + args,
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        log_info(setup_log, result.stdout.strip())
    if result.stderr.strip():
        log_warning(setup_log, result.stderr.strip())

    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, result.args)


def run_git(args, cwd):
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True
    )


def clone_repo(name, url, dest_path, setup_log):
    if not dest_path.exists():
        log_and_print(setup_log, f"[*] Cloning {name} from {url}...")
        run_git(["clone", url, str(dest_path)], cwd=dest_path.parent)
        return

    log_and_print(setup_log, f"[INFO] {name} already exists at {dest_path}. Pulling updates...")
    try:
        result = subprocess.run(
            ["git", "remote", "show", "origin"],
            cwd=dest_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        default_branch = "main"
        for line in result.stdout.splitlines():
            if "HEAD branch:" in line:
                default_branch = line.split(":")[1].strip()
                break

        run_git(["pull", "origin", default_branch], cwd=dest_path)
        log_and_print(setup_log, f"[INFO] Updated {name}.")
    except subprocess.CalledProcessError as e:
        log_warning(setup_log, f"[ERROR] Git pull failed:\n{e.stderr}")