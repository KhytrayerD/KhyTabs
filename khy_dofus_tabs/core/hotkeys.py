from __future__ import annotations

from typing import Callable

import keyboard


class HotkeyManager:
    def __init__(self) -> None:
        self._hotkey_ids: dict[str, object] = {"slots": []}

    def register_toggle_visibility(self, callback: Callable[[], None]):
        try:
            hk_id = keyboard.add_hotkey("ctrl+shift+h", callback)
            self._hotkey_ids["toggle_visibility"] = hk_id
            return hk_id
        except Exception:
            self._hotkey_ids["toggle_visibility"] = None
            return None

    def clear_dynamic(self) -> None:
        try:
            for k in ("key_next", "key_prev"):
                hk_id = self._hotkey_ids.get(k)
                if hk_id:
                    try:
                        keyboard.remove_hotkey(hk_id)
                    except Exception:
                        pass
                    self._hotkey_ids[k] = None
        except Exception:
            pass

        try:
            slot_ids = self._hotkey_ids.get("slots")
            if isinstance(slot_ids, list):
                for hk_id in slot_ids:
                    try:
                        keyboard.remove_hotkey(hk_id)
                    except Exception:
                        pass
            self._hotkey_ids["slots"] = []
        except Exception:
            self._hotkey_ids["slots"] = []

    def register_dynamic(
        self,
        *,
        key_next: str | None,
        key_prev: str | None,
        slots: list[str],
        on_next: Callable[[], None],
        on_prev: Callable[[], None],
        on_slot: Callable[[int], None],
    ) -> None:
        self.clear_dynamic()

        if key_next:
            try:
                self._hotkey_ids["key_next"] = keyboard.add_hotkey(key_next, on_next)
            except Exception:
                self._hotkey_ids["key_next"] = None

        if key_prev:
            try:
                self._hotkey_ids["key_prev"] = keyboard.add_hotkey(key_prev, on_prev)
            except Exception:
                self._hotkey_ids["key_prev"] = None

        ids = []
        for idx, hotkey in enumerate(slots):
            if not hotkey:
                continue
            try:
                hk_id = keyboard.add_hotkey(hotkey, lambda i=idx: on_slot(i))
                ids.append(hk_id)
            except Exception:
                pass

        self._hotkey_ids["slots"] = ids

    def shutdown(self) -> None:
        try:
            keyboard.unhook_all()
        except Exception:
            pass
