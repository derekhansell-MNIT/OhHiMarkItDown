# marker_setup.py
# Initialization logic for Marker using the PyPI package (marker-pdf).
# This version:
#   - Uses the Python API (PdfConverter + create_model_dict)
#   - Ensures models are downloaded
#   - Verifies GPU availability for logging
#   - Integrates with your utils logging

from utils import log_info, log_warning, check_gpu_available
from marker.models import create_model_dict


def initialize_marker(python_exe, setup_log):
    """
    Initialize Marker by:
      - Verifying GPU availability (optional)
      - Triggering model download via create_model_dict()
      - Logging status
    """
    # GPU check (optional but useful for diagnostics)
    gpu_status = check_gpu_available()
    if gpu_status is None:
        log_warning(setup_log, "PyTorch not installed; Marker will run CPU-only.")
    elif gpu_status is False:
        log_warning(setup_log, "GPU detected but CUDA unavailable; running CPU-only.")
    else:
        log_info(setup_log, "CUDA GPU available for Marker.")

    log_info(setup_log, "Initializing Marker models...")

    try:
        # This triggers model download if missing
        artifact_dict = create_model_dict()
        if not artifact_dict:
            log_warning(setup_log, "Marker model dictionary is empty.")
            return False

        log_info(setup_log, "Marker models initialized successfully.")
        return True

    except Exception as e:
        log_warning(setup_log, f"Marker model initialization failed: {e}")
        return False
