from __future__ import annotations

import json
import os
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "slots": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"],
    "key_next": "pagedown",
    "key_prev": "pageup",
    "text_mode": "always",
    "ui_scale": "medium",
    "ui_scale_factor": 1.0,
    "orientation": "vertical",
    "window_x": 10,
    "window_y": 100,
    "opacity": 1.0,
    "locked": False,
    "smart_hide": False,
    "compact_dock": False,
    "status_indicators": False,
    "auto_rescan_missing": False,
    "profiles": {},
}


def _default_config_path() -> str:
    try:
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    except Exception:
        base = os.path.expanduser("~")
    return os.path.join(base, "KhyDofusTabs", "config.json")


def load_config(path: str | None = None) -> dict[str, Any]:
    if not path:
        path = _default_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            if isinstance(loaded, dict):
                merged.update(loaded)
            if "profiles" not in merged or not isinstance(merged.get("profiles"), dict):
                merged["profiles"] = {}
            return merged
        except Exception:
            return dict(DEFAULT_CONFIG)
    return dict(DEFAULT_CONFIG)


def save_config(config: dict[str, Any], window_pos: tuple[int, int], path: str | None = None) -> None:
    if not path:
        path = _default_config_path()
    try:
        config["window_x"] = int(window_pos[0])
        config["window_y"] = int(window_pos[1])
    except Exception:
        pass

    try:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
    except Exception:
        pass

    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
