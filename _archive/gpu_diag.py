# gpu_diag.py

import torch
import torchvision

print("torch version:", torch.__version__)
print("torch cuda is_available:", torch.cuda.is_available())
print("torch cuda device_count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("torch cuda device 0:", torch.cuda.get_device_name(0))

print("torchvision version:", torchvision.__version__)

try:
    import torchvision.ops as ops
    print("has torchvision.ops.nms:", hasattr(ops, "nms"))
except Exception as e:
    print("import torchvision.ops failed:", repr(e))

import subprocess
import re

def get_cuda_driver_version():
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            return None
        # Look for: "CUDA Version: 12.8"
        match = re.search(r"CUDA Version:\s+(\d+\.\d+)", result.stdout)
        if match:
            return match.group(1)
        return None
    except FileNotFoundError:
        return None