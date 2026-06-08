from __future__ import annotations

import ctypes
from platform import system


def enable_dpi_awareness() -> str:
    if system() != "Windows":
        return "non_windows"

    try:
        shcore = ctypes.windll.shcore
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        result = shcore.SetProcessDpiAwareness(2)
        if result == 0:
            return "per_monitor_v1"
    except Exception:
        pass

    try:
        user32 = ctypes.windll.user32
        result = user32.SetProcessDPIAware()
        if result:
            return "system_dpi_aware"
    except Exception:
        pass

    return "unavailable"
