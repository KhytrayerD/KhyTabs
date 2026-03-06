from __future__ import annotations

import ctypes
from dataclasses import dataclass, field

import pygetwindow as gw

try:
    import psutil
except Exception:
    psutil = None


CLASS_ID_MAP: dict[int, str] = {
    1: "Feca",
    2: "Osamodas",
    3: "Anutrof",
    4: "Sram",
    5: "Xelor",
    6: "Zurkarak",
    7: "Aniripsa",
    8: "Yopuka",
    9: "Ocra",
    10: "Sadida",
    11: "Sacrogrito",
    12: "Pandawa",
    13: "Tymador",
    14: "Zobal",
    15: "Steamer",
    16: "Selotrop",
    17: "Hipermago",
    18: "Uginak",
    19: "Forjalanza",
}

CLASES_NAMES_LOWER: dict[str, int] = {v.lower(): k for k, v in CLASS_ID_MAP.items()}


@dataclass
class WindowEntry:
    window_title: str
    class_name: str
    char_name: str
    time: float
    initiative: int = 0
    _ui: dict = field(default_factory=dict, repr=False)


class WindowScanner:
    def __init__(self) -> None:
        self._user32 = ctypes.windll.user32

    def parse_window_title(self, title: str) -> tuple[str | None, str | None]:
        parts = title.split(" - ")
        if len(parts) < 2:
            return None, None

        detected_class = None
        detected_name = None

        for i, part in enumerate(parts):
            clean_part = part.strip().lower()
            if clean_part in CLASES_NAMES_LOWER:
                detected_class = CLASS_ID_MAP[CLASES_NAMES_LOWER[clean_part]]
                detected_name = " - ".join(parts[:i]).strip()
                break

        return detected_name, detected_class

    def get_window_creation_time(self, title: str) -> float:
        if psutil is None:
            return 0.0
        try:
            wins = gw.getWindowsWithTitle(title)
            if not wins:
                return 0.0
            hwnd = wins[0]._hWnd
            pid = ctypes.c_ulong()
            self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            return float(psutil.Process(pid.value).create_time())
        except Exception:
            return 0.0

    def scan_windows(self) -> list[WindowEntry]:
        found: list[WindowEntry] = []
        all_titles = gw.getAllTitles()
        for title in all_titles:
            if " - " not in title:
                continue
            char_name, detected_class = self.parse_window_title(title)
            if char_name and detected_class:
                found.append(
                    WindowEntry(
                        window_title=title,
                        class_name=detected_class,
                        char_name=char_name,
                        time=self.get_window_creation_time(title),
                    )
                )

        found.sort(key=lambda x: x.time)
        return found
