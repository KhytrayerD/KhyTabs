from __future__ import annotations

import os
from typing import Any

import pygetwindow as gw
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QCursor, QGuiApplication, QIcon, QPixmap
from PySide6.QtWidgets import QBoxLayout, QFrame, QGraphicsDropShadowEffect, QLabel, QMenu, QVBoxLayout, QWidget

from khy_dofus_tabs.core.almanax import AlmanaxClient
from khy_dofus_tabs.core.config import save_config
from khy_dofus_tabs.core.hotkeys import HotkeyManager
from khy_dofus_tabs.core.icons import IconRepository
from khy_dofus_tabs.core.window_focus import WindowFocuser
from khy_dofus_tabs.core.window_scanner import WindowEntry, WindowScanner
from khy_dofus_tabs.ui.animations import AnimationFactory
from khy_dofus_tabs.ui.character_item import CharacterItem, CharacterItemState
from khy_dofus_tabs.ui.organizer_window import OrganizerWindow
from khy_dofus_tabs.ui.settings_window import SettingsWindow


UI_SIZES: dict[str, dict[str, Any]] = {
    "xsmall": {"icon": 18, "row_pad_x": 8, "row_pad_y": 6, "row_gap": 8, "name_px": 11, "hotkey_px": 10, "header_font": 10, "header_txt": "Khy"},
    "small": {"icon": 24, "row_pad_x": 10, "row_pad_y": 8, "row_gap": 10, "name_px": 12, "hotkey_px": 11, "header_font": 11, "header_txt": "Khy"},
    "medium": {"icon": 32, "row_pad_x": 10, "row_pad_y": 8, "row_gap": 10, "name_px": 13, "hotkey_px": 12, "header_font": 12, "header_txt": "Khy"},
    "large": {"icon": 48, "row_pad_x": 12, "row_pad_y": 10, "row_gap": 12, "name_px": 14, "hotkey_px": 13, "header_font": 14, "header_txt": "KhyDofus"},
}


class MainWindow(QWidget):
    def __init__(
        self,
        *,
        config: dict[str, Any],
        scanner: WindowScanner,
        focuser: WindowFocuser,
        hotkeys: HotkeyManager,
        icons: IconRepository,
        almanax: AlmanaxClient,
    ) -> None:
        super().__init__()

        self._config = config
        self._active_config = config

        self._scanner = scanner
        self._focuser = focuser
        self._hotkeys = hotkeys
        self._icons = icons
        self._almanax = almanax

        self._windows: list[WindowEntry] = []
        self._items: list[CharacterItem] = []
        self._class_pix_cache: dict[tuple[str, int, int], QPixmap] = {}
        self._is_visible_globally = True
        self._manual_hidden = False
        self._smart_hide_active = False
        self._smart_hide_hold = False
        self._last_active_title = ""

        self._missing_timer = QTimer(self)
        self._missing_timer.setInterval(1500)
        self._missing_timer.timeout.connect(self._auto_rescan_if_missing)
        self._missing_timer.start()

        self._drag_start: QPoint | None = None
        self._drag_origin: QPoint | None = None

        self._anim = AnimationFactory()

        self.setObjectName("OverlayRoot")
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setWindowFlag(Qt.Tool, True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        if os.path.exists("icono.ico"):
            try:
                self.setWindowIcon(QIcon("icono.ico"))
            except Exception:
                pass

        self._card = QFrame(self)
        self._card.setObjectName("Card")

        try:
            shadow = QGraphicsDropShadowEffect(self._card)
            shadow.setBlurRadius(28)
            shadow.setOffset(0, 10)
            shadow.setColor(QColor(0, 0, 0, 180))
            self._card.setGraphicsEffect(shadow)
        except Exception:
            pass

        self._header = QFrame(self._card)
        self._header.setObjectName("Header")
        self._header_title = QLabel(self._header)
        self._header_title.setObjectName("HeaderTitle")

        self._header_layout = QBoxLayout(QBoxLayout.LeftToRight, self._header)
        self._header_layout.setContentsMargins(12, 10, 12, 10)
        self._header_layout.setSpacing(0)
        self._header_layout.addWidget(self._header_title, 0, Qt.AlignLeft | Qt.AlignVCenter)

        self._list_host = QWidget(self._card)
        self._list_layout = QBoxLayout(QBoxLayout.TopToBottom, self._list_host)
        self._list_layout.setContentsMargins(8, 8, 8, 10)
        self._list_layout.setSpacing(6)

        self._card_layout = QBoxLayout(QBoxLayout.TopToBottom, self._card)
        self._card_layout.setContentsMargins(0, 0, 0, 0)
        self._card_layout.setSpacing(0)
        self._card_layout.addWidget(self._header)
        self._card_layout.addWidget(self._list_host)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.addWidget(self._card)

        try:
            self.setWindowOpacity(float(self._config.get("opacity", 1.0)))
        except Exception:
            pass

        try:
            x = int(self._config.get("window_x", 10))
            y = int(self._config.get("window_y", 100))
            self.move(x, y)
        except Exception:
            pass

        self._context_menu = QMenu(self)
        self._act_settings = QAction("⚙ Configuración", self)
        self._act_legal = QAction("⚖ Aviso Legal", self)
        self._act_refresh = QAction("↻ Refrescar", self)
        self._act_close = QAction("✕ Cerrar App", self)

        self._context_menu.addAction(self._act_settings)
        self._context_menu.addSeparator()
        self._context_menu.addAction(self._act_legal)
        self._context_menu.addSeparator()
        self._context_menu.addAction(self._act_refresh)
        self._context_menu.addAction(self._act_close)

        self._act_settings.triggered.connect(self.open_settings)
        self._act_legal.triggered.connect(self.show_legal)
        self._act_refresh.triggered.connect(self.scan_windows)
        self._act_close.triggered.connect(self.close_app)

        self._hotkeys.register_toggle_visibility(self.toggle_interface_phantom)

        self.scan_windows()

        self._timer = QTimer(self)
        self._timer.setInterval(150)
        self._timer.timeout.connect(self.check_active_window_logic)
        self._timer.start()

    def _get_current_titles(self) -> set[str]:
        try:
            return {t for t in gw.getAllTitles() if t}
        except Exception:
            return set()

    def _is_missing_any(self) -> bool:
        titles = self._get_current_titles()
        if not titles:
            return False
        for w in self._windows:
            if w.window_title not in titles:
                return True
        return False

    def _auto_rescan_if_missing(self) -> None:
        try:
            if not bool(self._active_config.get("auto_rescan_missing", False)):
                return
            if self._is_missing_any():
                self.scan_windows()
        except Exception:
            pass

    def shutdown(self) -> None:
        try:
            self._hotkeys.shutdown()
        except Exception:
            pass

    def get_current_ui_params(self) -> dict[str, Any]:
        scale = self._active_config.get("ui_scale", "medium")
        base = dict(UI_SIZES.get(scale, UI_SIZES["medium"]))
        try:
            factor = float(self._active_config.get("ui_scale_factor", 1.0))
        except Exception:
            factor = 1.0

        if factor <= 0:
            factor = 1.0

        for k in ("icon", "row_pad_x", "row_pad_y", "row_gap", "name_px", "hotkey_px", "header_font"):
            try:
                base[k] = int(round(float(base.get(k, 0)) * factor))
            except Exception:
                pass
        return base

    def contextMenuEvent(self, event) -> None:
        try:
            self._smart_hide_hold = True
            try:
                self.show()
                self.raise_()
                self._smart_hide_active = False
            except Exception:
                pass
            self._context_menu.exec(QCursor.pos())
        except Exception:
            pass
        try:
            self._smart_hide_hold = False
            self.check_active_window_logic()
        except Exception:
            pass

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            if self._active_config.get("locked", False):
                return
            self._drag_start = event.globalPosition().toPoint()
            self._drag_origin = self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._active_config.get("locked", False):
            return
        if self._drag_start is None or self._drag_origin is None:
            return
        cur = event.globalPosition().toPoint()
        delta = cur - self._drag_start
        self.move(self._drag_origin + delta)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_start = None
        self._drag_origin = None
        super().mouseReleaseEvent(event)

    def toggle_interface_phantom(self) -> None:
        try:
            if self._is_visible_globally:
                self.hide()
                self._is_visible_globally = False
                self._manual_hidden = True
            else:
                self.show()
                self.raise_()
                self._is_visible_globally = True
                self._manual_hidden = False
                self._smart_hide_active = False
        except Exception:
            pass

    def show_legal(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        legal_text = (
            "KhyDofus Tabs - Herramienta de Organización Visual\n\n"
            "Esta aplicación es una herramienta de terceros gratuita y sin ánimo de lucro.\n"
            "NO modifica los archivos del juego.\n"
            "NO automatiza acciones (no es un bot).\n"
            "NO intercepta paquetes de red.\n\n"
            "Simplemente ayuda a cambiar entre ventanas usando atajos de teclado estándar de Windows.\n\n"
            "AVISO DE COPYRIGHT:\n"
            "Dofus y Ankama son marcas registradas de Ankama Games.\n"
            "Todas las imágenes, logotipos y nombres de clases son propiedad exclusiva de Ankama Games.\n"
            "Esta aplicación no está afiliada, respaldada ni patrocinada por Ankama Games."
        )

        QMessageBox.information(self, "Aviso Legal", legal_text)

    def close_app(self) -> None:
        try:
            save_config(self._config, (self.x(), self.y()))
        except Exception:
            pass
        try:
            self.shutdown()
        except Exception:
            pass
        QGuiApplication.quit()

    def scan_windows(self) -> None:
        try:
            self._windows = self._scanner.scan_windows()
        except Exception:
            self._windows = []
        self.render_ui()

    def _on_settings_windows_preview(self, temp_windows: list[WindowEntry]) -> None:
        self._windows = temp_windows
        self.render_ui()

    def render_ui(self) -> None:
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(self)
                w.hide()
                w.deleteLater()

        self._items = []

        params = self.get_current_ui_params()
        header_text = params["header_txt"]

        orientation = self._active_config.get("orientation", "vertical")
        compact = bool(self._active_config.get("compact_dock", False))
        if orientation == "vertical":
            self._card_layout.setDirection(QBoxLayout.TopToBottom)
            self._list_layout.setDirection(QBoxLayout.TopToBottom)
            try:
                self._list_layout.setAlignment(Qt.AlignHCenter)
            except Exception:
                pass
            self._header_layout.setDirection(QBoxLayout.LeftToRight)
            try:
                self._header_layout.setAlignment(self._header_title, Qt.AlignHCenter | Qt.AlignVCenter)
            except Exception:
                pass
        else:
            self._card_layout.setDirection(QBoxLayout.LeftToRight)
            self._list_layout.setDirection(QBoxLayout.LeftToRight)
            try:
                self._list_layout.setAlignment(Qt.AlignVCenter)
            except Exception:
                pass
            self._header_layout.setDirection(QBoxLayout.TopToBottom)
            try:
                self._header_layout.setAlignment(self._header_title, Qt.AlignHCenter | Qt.AlignVCenter)
            except Exception:
                pass

        if orientation != "vertical" and len(header_text) > 3:
            header_text = "K\nH\nY"

        self._header_title.setText(header_text)
        self._header_title.setStyleSheet(f"font-size: {int(params['header_font'])}px;")

        text_mode = self._active_config.get("text_mode", "always")
        if compact:
            text_mode = "hover"

        slots = self._active_config.get("slots", [])
        key_next = self._active_config.get("key_next")
        key_prev = self._active_config.get("key_prev")

        self._hotkeys.register_dynamic(
            key_next=key_next,
            key_prev=key_prev,
            slots=list(slots),
            on_next=lambda: self.cycle_windows(1),
            on_prev=lambda: self.cycle_windows(-1),
            on_slot=self._on_slot_hotkey,
        )

        try:
            if compact:
                self._header.hide()
                self._header.setFixedHeight(0)
                self._header.setContentsMargins(0, 0, 0, 0)
                self._header_layout.setContentsMargins(0, 0, 0, 0)
                self._list_layout.setContentsMargins(6, 6, 6, 8)
                self._list_layout.setSpacing(4)
                self._card_layout.setSpacing(0)
                self._card_layout.setContentsMargins(0, 0, 0, 0)
                try:
                    self._card.setFixedWidth(int(params.get("icon", 18)) + 26)
                except Exception:
                    pass
            else:
                self._header.show()
                self._header.setFixedHeight(16777215)
                self._header_layout.setContentsMargins(12, 10, 12, 10)
                self._list_layout.setContentsMargins(8, 8, 8, 10)
                self._list_layout.setSpacing(6)
                self._card_layout.setSpacing(0)
                self._card_layout.setContentsMargins(0, 0, 0, 0)
                try:
                    self._card.setFixedWidth(16777215)
                except Exception:
                    pass
        except Exception:
            pass

        titles = self._get_current_titles() if bool(self._active_config.get("status_indicators", True)) else set()

        for idx, win in enumerate(self._windows):
            hotkey = slots[idx] if idx < len(slots) else None

            item = CharacterItem(self)
            item.set_text_mode(text_mode)
            item.set_orientation(orientation)

            pad_x = int(params["row_pad_x"])
            pad_y = int(params["row_pad_y"])
            gap = int(params["row_gap"])
            if compact:
                pad_x = 0
                pad_y = 0
                gap = 0
            item.set_metrics(
                icon_px=int(params["icon"]),
                row_pad_x=pad_x,
                row_pad_y=pad_y,
                row_gap=gap,
                name_px=int(params["name_px"]),
                hotkey_px=int(params["hotkey_px"]),
            )

            if text_mode == "hover" or compact:
                tt = f"{win.char_name} [{hotkey}]" if hotkey else win.char_name
                item.set_tooltip_text(tt)
            else:
                item.set_tooltip_text(None)

            try:
                if titles:
                    item.setProperty("missing", win.window_title not in titles)
                else:
                    item.setProperty("missing", False)
            except Exception:
                pass

            item.set_state(
                CharacterItemState(
                    title=win.window_title,
                    class_name=win.class_name,
                    char_name=win.char_name,
                    hotkey=hotkey,
                )
            )

            pix = self._load_class_pixmap(win.class_name, icon_px=int(params["icon"]))
            item.set_icon_pixmaps(pix)
            item.activated.connect(self.force_focus)

            try:
                if orientation == "vertical":
                    self._list_layout.addWidget(item, 0, Qt.AlignHCenter)
                else:
                    self._list_layout.addWidget(item, 0, Qt.AlignVCenter)
            except Exception:
                self._list_layout.addWidget(item)
            self._items.append(item)

        try:
            self._card.adjustSize()
            self._list_host.adjustSize()
            self._header.adjustSize()
            self._card.updateGeometry()
            self._card_layout.invalidate()
            self._list_layout.invalidate()
            self.adjustSize()
            self.resize(self.sizeHint())
        except Exception:
            pass
        self._last_active_title = ""
        self.check_active_window_logic()

    def _load_class_pixmap(self, class_name: str, icon_px: int) -> QPixmap | None:
        key_name = (class_name or "").lower().strip()
        if not key_name:
            return None

        try:
            dpr = float(self.devicePixelRatioF())
        except Exception:
            dpr = 1.0

        dpr_key = int(round(dpr * 100))
        cache_key = (key_name, int(icon_px), dpr_key)
        if cache_key in self._class_pix_cache:
            return self._class_pix_cache[cache_key]

        raw = self._icons.fetch_class_icon_bytes(class_name)
        if not raw:
            return None

        pix = QPixmap()
        if not pix.loadFromData(raw):
            return None

        if icon_px > 0:
            mode = Qt.SmoothTransformation
            if icon_px <= 24:
                mode = Qt.FastTransformation
            target = max(1, int(round(icon_px * dpr)))
            pix = pix.scaled(target, target, Qt.KeepAspectRatio, mode)
            try:
                pix.setDevicePixelRatio(dpr)
            except Exception:
                pass
        try:
            self._class_pix_cache[cache_key] = pix
        except Exception:
            pass
        return pix

    def _on_slot_hotkey(self, idx: int) -> None:
        try:
            if idx < 0 or idx >= len(self._windows):
                return
            self.conditional_activate(self._windows[idx].window_title)
        except Exception:
            pass

    def cycle_windows(self, direction: int) -> None:
        if not self._windows:
            return
        if not self.is_safe_context():
            return

        active = gw.getActiveWindow()
        curr_t = active.title if active else ""

        curr_idx = -1
        for i, item in enumerate(self._windows):
            if item.window_title == curr_t:
                curr_idx = i
                break

        if curr_idx == -1:
            next_idx = 0
        else:
            next_idx = (curr_idx + direction) % len(self._windows)

        self.force_focus(self._windows[next_idx].window_title)

    def conditional_activate(self, target: str) -> None:
        if self.is_safe_context():
            self.force_focus(target)

    def is_safe_context(self) -> bool:
        try:
            active = gw.getActiveWindow()
            if not active:
                return False

            if any(item.window_title == active.title for item in self._windows):
                return True

            if "KhyDofus" in active.title:
                return True

            return False
        except Exception:
            return False

    def force_focus(self, window_title: str) -> None:
        try:
            self._focuser.force_focus(window_title)
        except Exception:
            pass

    def check_active_window_logic(self) -> None:
        try:
            active = gw.getActiveWindow()
            curr = active.title if active else ""

            try:
                if self._manual_hidden:
                    return
            except Exception:
                pass

            if self._is_visible_globally and self._active_config.get("smart_hide", False) and not self._smart_hide_hold:
                is_dofus = any(item.window_title == curr for item in self._windows)
                is_me = "KhyDofus" in curr or "Configuración" in curr or "Organizador" in curr

                if is_dofus or is_me:
                    if self._smart_hide_active:
                        self.show()
                        self.raise_()
                        self._smart_hide_active = False
                else:
                    if not self._smart_hide_active:
                        self.hide()
                        self._smart_hide_active = True

            if not self._is_visible_globally or self._smart_hide_active:
                return

            if curr == self._last_active_title:
                return
            self._last_active_title = curr

            text_mode = self._active_config.get("text_mode", "always")
            try:
                if bool(self._active_config.get("compact_dock", False)):
                    text_mode = "hover"
            except Exception:
                pass
            show_text = text_mode == "always"

            for i, w in enumerate(self._items):
                if i >= len(self._windows):
                    continue

                target_title = self._windows[i].window_title
                is_active = target_title == curr
                w.set_text_mode(text_mode)
                w.set_active(is_active)

                if show_text:
                    w.set_tooltip_text(None)
                else:
                    if text_mode == "hover":
                        slots = self._active_config.get("slots", [])
                        hotkey = slots[i] if i < len(slots) else None
                        tt = f"{self._windows[i].char_name} [{hotkey}]" if hotkey else self._windows[i].char_name
                        w.set_tooltip_text(tt)
                    else:
                        w.set_tooltip_text(None)

        except Exception:
            pass

    def open_settings(self) -> None:
        dlg = SettingsWindow(
            parent=self,
            config=self._config,
            active_config=self._active_config,
            windows=self._windows,
            almanax=self._almanax,
            icons=self._icons,
        )

        dlg.configApplied.connect(self._on_settings_preview)
        dlg.windowsApplied.connect(self._on_settings_windows_preview)
        dlg.configSaved.connect(self._on_settings_saved)
        dlg.reorderRequested.connect(self._open_organizer)

        result = dlg.exec()
        if result == 0:
            self._on_settings_cancel()

    def _on_settings_preview(self, temp_config: dict) -> None:
        self._active_config = temp_config
        try:
            self.setWindowOpacity(float(self._active_config.get("opacity", 1.0)))
        except Exception:
            pass
        try:
            self.setProperty("compactDock", bool(self._active_config.get("compact_dock", False)))
            self.style().unpolish(self)
            self.style().polish(self)
        except Exception:
            pass
        try:
            x = int(self._active_config.get("window_x", self.x()))
            y = int(self._active_config.get("window_y", self.y()))
            self.move(x, y)
        except Exception:
            pass
        self.render_ui()

    def _on_settings_cancel(self) -> None:
        self._active_config = self._config
        try:
            self.setWindowOpacity(float(self._config.get("opacity", 1.0)))
        except Exception:
            pass
        self.scan_windows()

    def _on_settings_saved(self, final_config: dict, final_windows: list[WindowEntry]) -> None:
        self._config = final_config
        self._active_config = final_config
        self._windows = final_windows
        try:
            save_config(self._config, (self.x(), self.y()))
        except Exception:
            pass
        try:
            self.setProperty("compactDock", bool(self._active_config.get("compact_dock", False)))
            self.style().unpolish(self)
            self.style().polish(self)
        except Exception:
            pass
        self.render_ui()

    def _open_organizer(self, temp_windows: list[WindowEntry]) -> None:
        org = OrganizerWindow(self, temp_windows, icons=self._icons)
        org.windowsChanged.connect(self._on_organizer_changed)
        org.exec()

    def _on_organizer_changed(self, updated: list[WindowEntry]) -> None:
        self._windows = updated
        self.render_ui()
