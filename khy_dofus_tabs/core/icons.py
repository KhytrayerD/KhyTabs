from __future__ import annotations

import urllib.request

from khy_dofus_tabs.core.window_scanner import CLASES_NAMES_LOWER


class IconRepository:
    def __init__(self) -> None:
        self._raw_icon_cache: dict[int, bytes] = {}

    def fetch_class_icon_bytes(self, class_name: str) -> bytes | None:
        class_id = CLASES_NAMES_LOWER.get(class_name.lower())
        if not class_id:
            return None

        if class_id in self._raw_icon_cache:
            return self._raw_icon_cache[class_id]

        url = f"https://api.dofusdb.fr/img/breeds/symbol_{class_id}.png"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = response.read()
            self._raw_icon_cache[class_id] = data
            return data
        except Exception:
            return None
