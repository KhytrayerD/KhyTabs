from __future__ import annotations

import ctypes

import pygetwindow as gw


class WindowFocuser:
    def __init__(self) -> None:
        self._user32 = ctypes.windll.user32
        self._kernel32 = ctypes.windll.kernel32

    def force_focus(self, window_title: str) -> None:
        try:
            windows = gw.getWindowsWithTitle(window_title)
            if not windows:
                return

            t_win = windows[0]
            hwnd_t = t_win._hWnd
            hwnd_a = self._user32.GetForegroundWindow()

            tid_a = self._user32.GetWindowThreadProcessId(hwnd_a, None)
            tid_t = self._user32.GetWindowThreadProcessId(hwnd_t, None)
            tid_c = self._kernel32.GetCurrentThreadId()

            if hwnd_t == hwnd_a:
                return

            if tid_a != tid_c:
                self._user32.AttachThreadInput(tid_c, tid_a, True)
            if tid_t != tid_c:
                self._user32.AttachThreadInput(tid_c, tid_t, True)

            if self._user32.IsIconic(hwnd_t):
                self._user32.ShowWindow(hwnd_t, 9)
            else:
                self._user32.ShowWindow(hwnd_t, 5)

            self._user32.SetForegroundWindow(hwnd_t)
            self._user32.SetFocus(hwnd_t)

            if tid_a != tid_c:
                self._user32.AttachThreadInput(tid_c, tid_a, False)
            if tid_t != tid_c:
                self._user32.AttachThreadInput(tid_c, tid_t, False)
        except Exception:
            return
