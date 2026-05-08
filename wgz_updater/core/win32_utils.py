from __future__ import annotations

import ctypes
import sys
from contextlib import contextmanager
from ctypes import wintypes

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWM_SYSTEMBACKDROP_MAINWINDOW = 2
DWM_SYSTEMBACKDROP_TABBED = 4

DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate_and_relaunch(argv: list[str] | None = None) -> bool:
    if is_admin():
        return False
    params = " ".join(f'"{a}"' for a in (argv or sys.argv))
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    return rc > 32


def enable_mica(hwnd: int, dark: bool = True) -> None:
    if not hwnd:
        return
    try:
        dwmapi = ctypes.WinDLL("dwmapi")
        set_attr = dwmapi.DwmSetWindowAttribute
        set_attr.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
        set_attr.restype = ctypes.c_long

        dark_v = ctypes.c_int(1 if dark else 0)
        set_attr(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(dark_v), ctypes.sizeof(dark_v))

        backdrop = ctypes.c_int(DWM_SYSTEMBACKDROP_MAINWINDOW)
        set_attr(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, ctypes.byref(backdrop), ctypes.sizeof(backdrop))

        corner = ctypes.c_int(DWMWCP_ROUND)
        set_attr(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(corner), ctypes.sizeof(corner))
    except OSError:
        pass


@contextmanager
def prevent_sleep(keep_display_on: bool = False):
    flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    if keep_display_on:
        flags |= ES_DISPLAY_REQUIRED
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(flags)
        yield
    finally:
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
