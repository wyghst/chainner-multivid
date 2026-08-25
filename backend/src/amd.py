from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field

from logger import logger
from system import is_windows

# Electron spawns the Python backend with a restricted PATH that often excludes
# the PowerShell directory, so we build the absolute path from %SystemRoot%.
_POWERSHELL = os.path.join(
    os.environ.get("SystemRoot", r"C:\Windows"),
    "System32",
    "WindowsPowerShell",
    "v1.0",
    "powershell.exe",
)

# GPU name substrings that indicate a ROCm-compatible AMD card on Windows.
# RDNA 2 (RX 6000), RDNA 3 (RX 7000), RDNA 4 (RX 9000), Vega 20 (Radeon VII).
_ROCM_COMPATIBLE_PATTERNS = [
    "Radeon RX 6",
    "Radeon RX 7",
    "Radeon RX 9",
    "Radeon VII",
    "Radeon Pro W6",
    "Radeon Pro W7",
]

HIP_SDK_URL = "https://www.amd.com/en/developer/resources/rocm-hub/hip-sdk.html"
ROCM_PYTORCH_DOCS_URL = (
    "https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest"
    "/docs/install/installrad/windows/install-pytorch.html"
)


@dataclass(frozen=True)
class AmdInfo:
    gpu_names: list[str] = field(default_factory=list)

    @property
    def is_available(self) -> bool:
        return len(self.gpu_names) > 0

    @property
    def has_rocm_compatible_gpu(self) -> bool:
        return bool(self.rocm_compatible_names)

    @property
    def rocm_compatible_names(self) -> list[str]:
        return [
            name
            for name in self.gpu_names
            if any(pattern in name for pattern in _ROCM_COMPATIBLE_PATTERNS)
        ]

    @staticmethod
    def unavailable() -> AmdInfo:
        return AmdInfo(gpu_names=[])


def _get_amd_gpu_names_windows() -> list[str]:
    try:
        result = subprocess.run(
            [
                _POWERSHELL,
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty Name",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip() and ("AMD" in line or "Radeon" in line)
        ]
    except Exception as e:
        logger.warning("Failed to query AMD GPU info via WMI (path: %s): %s", _POWERSHELL, e)
        return []


def _get_amd_info() -> AmdInfo:
    if not is_windows:
        return AmdInfo.unavailable()
    gpu_names = _get_amd_gpu_names_windows()
    if gpu_names:
        logger.info("Detected AMD GPU(s): %s", ", ".join(gpu_names))
        rocm_names = [
            n for n in gpu_names if any(p in n for p in _ROCM_COMPATIBLE_PATTERNS)
        ]
        if rocm_names:
            logger.info("ROCm-compatible AMD GPU(s): %s", ", ".join(rocm_names))
        else:
            logger.info(
                "AMD GPU(s) found but none match ROCm-compatible patterns: %s",
                gpu_names,
            )
    else:
        logger.info("No AMD GPU detected via WMI (or WMI query failed).")
    return AmdInfo(gpu_names=gpu_names)


amd = _get_amd_info()

__all__ = ["AmdInfo", "HIP_SDK_URL", "ROCM_PYTORCH_DOCS_URL", "amd"]
