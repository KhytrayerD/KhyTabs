from __future__ import annotations

import json
import time
import urllib.request


class AlmanaxClient:
    def __init__(self) -> None:
        self.almanax_item_id = None

    def get_almanax_data(self) -> tuple[str, str]:
        try:
            day = time.strftime("%Y-%m-%d")
            url = f"https://api.dofusdu.de/dofus3/v1/es/almanax/{day}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as response:
                payload = response.read().decode("utf-8")
            data = json.loads(payload)

            try:
                self.almanax_item_id = data.get("tribute", {}).get("item", {}).get("image_urls", {}).get("icon")
            except Exception:
                self.almanax_item_id = None

            offer = ""
            bonus = ""
            try:
                offer = str(data.get("tribute", {}).get("quantity")) + "x " + data.get("tribute", {}).get("item", {}).get("name") or ""
            except Exception:
                offer = ""
            try:
                bonus = data.get("bonus", {}).get("description") or ""
            except Exception:
                bonus = ""

            offer = offer.replace("🥖", "").strip()
            bonus = bonus.strip()
            if not offer:
                offer = "(Sin datos de ofrenda)"
            if not bonus:
                bonus = "(Sin datos de bonus)"

            return offer, bonus
        except Exception:
            try:
                self.almanax_item_id = None
            except Exception:
                pass
            return "(Error cargando Almanax)", ""

    def fetch_dolmanax_icon_bytes(self, size: int = 44) -> bytes | None:
        try:
            icon_src = getattr(self, "almanax_item_id", None)
            if not icon_src:
                return None

            if isinstance(icon_src, str) and icon_src.startswith("http"):
                url = icon_src
            else:
                url = f"https://api.dofusdu.de/dofus3/v1/img/item/{icon_src}-64.png"

            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as response:
                raw = response.read()
            return raw
        except Exception:
            return None
