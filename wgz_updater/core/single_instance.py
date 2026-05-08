from __future__ import annotations

import ctypes
from ctypes import wintypes

from .paths import SINGLETON_MUTEX_NAME

ERROR_ALREADY_EXISTS = 183


class SingleInstance:
    def __init__(self, name: str = SINGLETON_MUTEX_NAME) -> None:
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create = self._kernel32.CreateMutexW
        create.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        create.restype = wintypes.HANDLE
        self._handle = create(None, False, name)
        self._already_running = ctypes.get_last_error() == ERROR_ALREADY_EXISTS

    @property
    def already_running(self) -> bool:
        return self._already_running

    def focus_existing(self, window_title_substr: str = "WGZ Game Updater") -> bool:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        EnumWindows = user32.EnumWindows
        IsWindowVisible = user32.IsWindowVisible
        GetWindowTextW = user32.GetWindowTextW
        SetForegroundWindow = user32.SetForegroundWindow
        ShowWindow = user32.ShowWindow

        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        target_hwnd = wintypes.HWND(0)

        def enum_proc(hwnd, _lparam):
            if not IsWindowVisible(hwnd):
                return True
            buf = ctypes.create_unicode_buffer(512)
            GetWindowTextW(hwnd, buf, 512)
            if window_title_substr.lower() in buf.value.lower():
                target_hwnd.value = hwnd
                return False
            return True

        EnumWindows(EnumWindowsProc(enum_proc), 0)
        if target_hwnd.value:
            ShowWindow(target_hwnd, 9)
            SetForegroundWindow(target_hwnd)
            return True
        return False

    def release(self) -> None:
        if self._handle:
            self._kernel32.ReleaseMutex(self._handle)
            self._kernel32.CloseHandle(self._handle)
            self._handle = None
