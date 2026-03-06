from __future__ import annotations

import copy
import threading
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Qt, Signal, QSize, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QIntValidator, QPixmap
from PySide6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QGraphicsDropShadowEffect,
    QScrollArea,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from khy_dofus_tabs.core.almanax import AlmanaxClient
from khy_dofus_tabs.core.icons import IconRepository
from khy_dofus_tabs.core.config import DEFAULT_CONFIG
from khy_dofus_tabs.core.window_scanner import WindowEntry
from khy_dofus_tabs.ui.animations import AnimationFactory
from khy_dofus_tabs.ui.organizer_window import OrganizerWindow


class SettingsWindow(QDialog):
    configApplied = Signal(dict)
    windowsApplied = Signal(list)
    configSaved = Signal(dict, list)
    reorderRequested = Signal(list)
    almanaxLoaded = Signal(str, str, object)

    def __init__(
        self,
        parent: QWidget,
        config: dict[str, Any],
        active_config: dict[str, Any],
        windows: list[WindowEntry],
        almanax: AlmanaxClient,
        icons: IconRepository,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("SettingsDialog")

        self.setWindowTitle("Configuración KhyDofus")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.resize(640, 680)

        self._config = config
        self._temp_config = copy.deepcopy(config)
        self._temp_windows = list(windows)
        self._almanax = almanax
        self._icons = icons
        self._button_groups: list[QButtonGroup] = []
        self._seg_groups: dict[str, QButtonGroup] = {}
        self._ui_scale_slider: QSlider | None = None
        self._opacity_slider: QSlider | None = None
        self._chk_lock: QCheckBox | None = None
        self._chk_smart: QCheckBox | None = None
        self._chk_compact: QCheckBox | None = None
        self._chk_indicators: QCheckBox | None = None
        self._chk_auto_rescan: QCheckBox | None = None
        self._anim = AnimationFactory()

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        header = QFrame(self)
        header.setObjectName("SettingsHeader")
        try:
            sh = QGraphicsDropShadowEffect(header)
            sh.setBlurRadius(22)
            sh.setOffset(0, 8)
            sh.setColor(QColor(0, 0, 0, 180))
            header.setGraphicsEffect(sh)
        except Exception:
            pass
        hdr_l = QVBoxLayout(header)
        hdr_l.setContentsMargins(12, 10, 12, 10)

        top_row = QFrame(header)
        top_row_l = QHBoxLayout(top_row)
        top_row_l.setContentsMargins(0, 0, 0, 0)
        top_row_l.setSpacing(8)

        title = QLabel("KHYDOFUS TABS - CONFIGURACIÓN", top_row)
        title.setObjectName("SettingsTitle")
        top_row_l.addWidget(title, 1)

        def _open(url: str) -> None:
            try:
                QDesktopServices.openUrl(QUrl(url))
            except Exception:
                pass

        assets_dir = Path(__file__).resolve().parents[1] / "assets" / "icons"
        yt_path = assets_dir / "youtube.png"
        kofi_path = assets_dir / "kofi.png"

        btn_yt = QPushButton("", top_row)
        btn_yt.setObjectName("LinkIcon")
        btn_yt.setProperty("kind", "youtube")
        btn_yt.setToolTip("YouTube: @KhytrayerDofus")
        btn_yt.setCursor(Qt.PointingHandCursor)
        btn_yt.setFixedSize(30, 30)
        try:
            if yt_path.exists():
                pix = QPixmap(str(yt_path))
                if not pix.isNull():
                    btn_yt.setIcon(QIcon(pix))
                    btn_yt.setIconSize(QSize(18, 18))
            else:
                btn_yt.setText("YT")
        except Exception:
            btn_yt.setText("YT")
        btn_yt.clicked.connect(lambda: _open("https://www.youtube.com/@KhytrayerDofus"))

        btn_kofi = QPushButton("", top_row)
        btn_kofi.setObjectName("LinkIcon")
        btn_kofi.setProperty("kind", "kofi")
        btn_kofi.setToolTip("Ko-fi: tradexapp")
        btn_kofi.setCursor(Qt.PointingHandCursor)
        btn_kofi.setFixedSize(30, 30)
        try:
            if kofi_path.exists():
                pix = QPixmap(str(kofi_path))
                if not pix.isNull():
                    btn_kofi.setIcon(QIcon(pix))
                    btn_kofi.setIconSize(QSize(18, 18))
            else:
                btn_kofi.setText("KO")
        except Exception:
            btn_kofi.setText("KO")
        btn_kofi.clicked.connect(lambda: _open("https://ko-fi.com/tradexapp"))

        top_row_l.addWidget(btn_yt, 0)
        top_row_l.addWidget(btn_kofi, 0)
        hdr_l.addWidget(top_row)
        root.addWidget(header)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll, 1)

        content = QWidget(scroll)
        scroll.setWidget(content)
        content_l = QVBoxLayout(content)
        content_l.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget(content)
        tabs.setObjectName("SettingsTabs")
        content_l.addWidget(tabs)

        tab_general = QWidget(tabs)
        tab_hotkeys = QWidget(tabs)
        tab_profiles = QWidget(tabs)
        tab_advanced = QWidget(tabs)

        tabs.addTab(tab_general, "General & Apariencia")
        tabs.addTab(tab_hotkeys, "Atajos de Teclado")
        tabs.addTab(tab_profiles, "Perfiles & Orden")
        tabs.addTab(tab_advanced, "Avanzado")

        self._build_general(tab_general)
        self._build_hotkeys(tab_hotkeys)
        self._build_profiles(tab_profiles)
        self._build_advanced(tab_advanced)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self._on_cancel)
        try:
            btn_save = buttons.button(QDialogButtonBox.Save)
            if btn_save:
                btn_save.setText("Guardar")
            btn_cancel = buttons.button(QDialogButtonBox.Cancel)
            if btn_cancel:
                btn_cancel.setText("Cancelar")
        except Exception:
            pass
        root.addWidget(buttons)

        self._emit_preview()
        self.almanaxLoaded.connect(self._apply_almanax)
        self._load_almanax_async()

    def showEvent(self, event) -> None:
        try:
            self.setWindowOpacity(0.0)
            self._anim.fade_window(self, 0.0, 1.0, 160)
        except Exception:
            pass
        super().showEvent(event)

    def _emit_preview(self) -> None:
        self.configApplied.emit(self._temp_config)

    def _on_reordered(self, updated: list[WindowEntry]) -> None:
        try:
            self._temp_windows[:] = list(updated)
        except Exception:
            self._temp_windows = list(updated)
        self.windowsApplied.emit(list(self._temp_windows))
        self._emit_preview()

    def _build_general(self, parent: QWidget) -> None:
        root = QVBoxLayout(parent)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        scale_slider: QSlider | None = None

        def segmented(label: str, options: list[tuple[str, str]], key: str) -> None:
            wrap = QFrame(parent)
            lay = QVBoxLayout(wrap)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(6)

            lab = QLabel(label, wrap)
            lab.setStyleSheet("color: rgba(232,232,240,255); font-weight: 700;")
            lay.addWidget(lab)

            row = QFrame(wrap)
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.setSpacing(6)

            group = QButtonGroup(self)
            group.setExclusive(True)
            self._button_groups.append(group)
            self._seg_groups[key] = group

            current = str(self._temp_config.get(key, options[0][0]))

            for val, text in options:
                btn = QPushButton(text, row)
                btn.setCheckable(True)
                btn.setProperty("_seg_value", val)
                btn.setStyleSheet(
                    "QPushButton{background:rgba(255,255,255,14);color:rgba(232,232,240,255);border:1px solid rgba(255,255,255,16);border-radius:10px;padding:8px 10px;font-weight:600;}"
                    "QPushButton:checked{background:rgba(255,255,255,26);border:1px solid rgba(255,255,255,26);}" 
                    "QPushButton:hover{background:rgba(255,255,255,20);}"
                )
                if val == current:
                    btn.setChecked(True)

                group.addButton(btn)
                row_l.addWidget(btn, 1)

                def _make_handler(v: str):
                    def _h(checked: bool = False):
                        if not checked:
                            return
                        self._temp_config[key] = v

                        nonlocal scale_slider
                        if key == "ui_scale" and scale_slider is not None:
                            try:
                                scale_slider.blockSignals(True)
                                scale_slider.setValue(100)
                            except Exception:
                                pass
                            try:
                                self._temp_config["ui_scale_factor"] = 1.0
                            except Exception:
                                pass
                            try:
                                scale_slider.blockSignals(False)
                            except Exception:
                                pass

                        self._emit_preview()
                    return _h

                btn.toggled.connect(_make_handler(val))

            lay.addWidget(row)
            root.addWidget(wrap)

        segmented(
            "Tamaño de Interfaz",
            [("xsmall", "Extra pequeño"), ("small", "Pequeño"), ("medium", "Medio"), ("large", "Grande")],
            "ui_scale",
        )

        scale_wrap = QFrame(parent)
        scale_l = QVBoxLayout(scale_wrap)
        scale_l.setContentsMargins(0, 0, 0, 0)
        scale_l.setSpacing(6)

        scale_lab = QLabel("Escala (personalizable)", scale_wrap)
        scale_lab.setStyleSheet("color: rgba(232,232,240,255); font-weight: 700;")
        scale_l.addWidget(scale_lab)

        scale_slider = QSlider(Qt.Horizontal, scale_wrap)
        scale_slider.setMinimum(50)
        scale_slider.setMaximum(160)
        scale_slider.setSingleStep(1)
        try:
            curr_factor = float(self._temp_config.get("ui_scale_factor", 1.0))
        except Exception:
            curr_factor = 1.0
        scale_slider.setValue(int(round(curr_factor * 100)))

        def on_scale(v: int):
            self._temp_config["ui_scale_factor"] = float(v) / 100.0
            self._emit_preview()

        scale_slider.valueChanged.connect(on_scale)
        scale_l.addWidget(scale_slider)
        root.addWidget(scale_wrap)
        self._ui_scale_slider = scale_slider
        segmented(
            "Orientación",
            [("vertical", "Vertical"), ("horizontal", "Horizontal")],
            "orientation",
        )
        segmented(
            "Modo de Texto",
            [("always", "Siempre"), ("hover", "Tooltip"), ("never", "Nunca")],
            "text_mode",
        )

        op_wrap = QFrame(parent)
        op_l = QVBoxLayout(op_wrap)
        op_l.setContentsMargins(0, 0, 0, 0)
        op_l.setSpacing(6)
        op_lab = QLabel("Opacidad", op_wrap)
        op_lab.setStyleSheet("color: rgba(232,232,240,255); font-weight: 700;")
        op_l.addWidget(op_lab)

        slider = QSlider(Qt.Horizontal, op_wrap)
        slider.setMinimum(2)
        slider.setMaximum(10)
        slider.setSingleStep(1)
        slider.setValue(int(round(float(self._temp_config.get("opacity", 1.0)) * 10)))

        def on_move(v: int):
            self._temp_config["opacity"] = float(v) / 10.0
            self._emit_preview()

        slider.valueChanged.connect(on_move)
        op_l.addWidget(slider)
        root.addWidget(op_wrap)
        al = QFrame(parent)
        al.setObjectName("AlmanaxCard")
        try:
            sh2 = QGraphicsDropShadowEffect(al)
            sh2.setBlurRadius(18)
            sh2.setOffset(0, 6)
            sh2.setColor(QColor(0, 0, 0, 170))
            al.setGraphicsEffect(sh2)
        except Exception:
            pass
        al_l = QVBoxLayout(al)
        al_l.setContentsMargins(12, 12, 12, 12)
        al_l.setSpacing(8)

        al_h = QLabel("ALMANAX", al)
        al_h.setObjectName("AlmanaxTitle")
        al_l.addWidget(al_h)

        al_row = QFrame(al)
        al_row_l = QHBoxLayout(al_row)
        al_row_l.setContentsMargins(0, 0, 0, 0)
        al_row_l.setSpacing(10)

        self._almanax_icon = QLabel(al_row)
        self._almanax_icon.setObjectName("AlmanaxIcon")
        self._almanax_icon.setFixedSize(46, 46)
        self._almanax_icon.setAlignment(Qt.AlignCenter)
        al_row_l.addWidget(self._almanax_icon, 0)

        text_col = QFrame(al_row)
        text_col_l = QVBoxLayout(text_col)
        text_col_l.setContentsMargins(0, 0, 0, 0)
        text_col_l.setSpacing(6)

        self._almanax_offer = QLabel("Cargando Almanax...", text_col)
        self._almanax_offer.setWordWrap(True)
        self._almanax_offer.setObjectName("AlmanaxOffer")
        text_col_l.addWidget(self._almanax_offer)

        self._almanax_bonus = QLabel("", text_col)
        self._almanax_bonus.setWordWrap(True)
        self._almanax_bonus.setObjectName("AlmanaxBonus")
        text_col_l.addWidget(self._almanax_bonus)

        al_row_l.addWidget(text_col, 1)
        al_l.addWidget(al_row)

        root.addWidget(al)
        root.addStretch(1)
        root.addStretch(1)

    def _build_advanced(self, parent: QWidget) -> None:
        root = QVBoxLayout(parent)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        checks = QFrame(parent)
        chk_l = QVBoxLayout(checks)
        chk_l.setContentsMargins(0, 0, 0, 0)
        chk_l.setSpacing(8)

        lock = QCheckBox("🔒 Bloquear Movimiento", checks)
        lock.setChecked(bool(self._temp_config.get("locked", False)))
        lock.stateChanged.connect(lambda _: self._set_bool("locked", lock.isChecked()))

        smart = QCheckBox("👁 Smart Hide (Ocultar Display): Ctrl + Shift + H", checks)
        smart.setChecked(bool(self._temp_config.get("smart_hide", False)))
        smart.stateChanged.connect(lambda _: self._set_bool("smart_hide", smart.isChecked()))

        compact = QCheckBox("🧷 Modo Compact Dock (solo iconos)", checks)
        compact.setChecked(bool(self._temp_config.get("compact_dock", False)))
        compact.stateChanged.connect(lambda _: self._set_bool("compact_dock", compact.isChecked()))

        indicators = QCheckBox("🟣 Indicadores de estado (activo / faltante)", checks)
        indicators.setChecked(bool(self._temp_config.get("status_indicators", True)))
        indicators.setEnabled(False)

        ind_row = QFrame(checks)
        ind_row_l = QHBoxLayout(ind_row)
        ind_row_l.setContentsMargins(0, 0, 0, 0)
        ind_row_l.setSpacing(8)
        ind_row_l.addWidget(indicators, 1)
        ind_soon = QLabel("Próximamente", ind_row)
        ind_soon.setStyleSheet("color: rgba(160,160,172,210); font-weight: 700;")
        ind_row_l.addWidget(ind_soon, 0, Qt.AlignRight | Qt.AlignVCenter)

        auto_rescan = QCheckBox("🔄 Auto-detección (re-scan si faltan ventanas)", checks)
        auto_rescan.setChecked(bool(self._temp_config.get("auto_rescan_missing", False)))
        auto_rescan.setEnabled(False)

        res_row = QFrame(checks)
        res_row_l = QHBoxLayout(res_row)
        res_row_l.setContentsMargins(0, 0, 0, 0)
        res_row_l.setSpacing(8)
        res_row_l.addWidget(auto_rescan, 1)
        res_soon = QLabel("Próximamente", res_row)
        res_soon.setStyleSheet("color: rgba(160,160,172,210); font-weight: 700;")
        res_row_l.addWidget(res_soon, 0, Qt.AlignRight | Qt.AlignVCenter)

        self._chk_lock = lock
        self._chk_smart = smart
        self._chk_compact = compact
        self._chk_indicators = indicators
        self._chk_auto_rescan = auto_rescan

        for cb in (lock, smart, compact, indicators, auto_rescan):
            cb.setStyleSheet("color: rgba(232,232,240,255); font-weight: 600;")

        chk_l.addWidget(lock)
        chk_l.addWidget(smart)
        chk_l.addWidget(compact)
        chk_l.addWidget(ind_row)
        chk_l.addWidget(res_row)
        root.addWidget(checks)

        reset_row = QFrame(parent)
        reset_l = QHBoxLayout(reset_row)
        reset_l.setContentsMargins(0, 0, 0, 0)

        btn_reset = QPushButton("↺ Restablecer (menos organización)", reset_row)

        def _do_reset_ui() -> None:
            try:
                keep_profiles = copy.deepcopy(self._temp_config.get("profiles", {}))
            except Exception:
                keep_profiles = {}

            try:
                self._temp_config = copy.deepcopy(DEFAULT_CONFIG)
                self._temp_config["profiles"] = keep_profiles
            except Exception:
                self._temp_config = dict(DEFAULT_CONFIG)
                try:
                    self._temp_config["profiles"] = keep_profiles
                except Exception:
                    pass

            try:
                if self._ui_scale_slider is not None:
                    self._ui_scale_slider.blockSignals(True)
                    self._ui_scale_slider.setValue(100)
                    self._ui_scale_slider.blockSignals(False)
            except Exception:
                pass

            try:
                if self._opacity_slider is not None:
                    self._opacity_slider.blockSignals(True)
                    self._opacity_slider.setValue(int(round(float(self._temp_config.get("opacity", 1.0)) * 10)))
                    self._opacity_slider.blockSignals(False)
            except Exception:
                pass

            try:
                if self._chk_lock is not None:
                    self._chk_lock.blockSignals(True)
                    self._chk_lock.setChecked(bool(self._temp_config.get("locked", False)))
                    self._chk_lock.blockSignals(False)
                if self._chk_smart is not None:
                    self._chk_smart.blockSignals(True)
                    self._chk_smart.setChecked(bool(self._temp_config.get("smart_hide", False)))
                    self._chk_smart.blockSignals(False)
                if self._chk_compact is not None:
                    self._chk_compact.blockSignals(True)
                    self._chk_compact.setChecked(bool(self._temp_config.get("compact_dock", False)))
                    self._chk_compact.blockSignals(False)
                if self._chk_indicators is not None:
                    self._chk_indicators.blockSignals(True)
                    self._chk_indicators.setChecked(bool(self._temp_config.get("status_indicators", True)))
                    self._chk_indicators.blockSignals(False)
                if self._chk_auto_rescan is not None:
                    self._chk_auto_rescan.blockSignals(True)
                    self._chk_auto_rescan.setChecked(bool(self._temp_config.get("auto_rescan_missing", False)))
                    self._chk_auto_rescan.blockSignals(False)
            except Exception:
                pass

            try:
                for k in ("ui_scale", "orientation", "text_mode"):
                    g = self._seg_groups.get(k)
                    if g is None:
                        continue
                    want = str(self._temp_config.get(k, ""))
                    for b in g.buttons():
                        if b.property("_seg_value") == want:
                            b.setChecked(True)
                            break
            except Exception:
                pass

            try:
                self._key_next.setText(str(self._temp_config.get("key_next", "pagedown")))
                self._key_prev.setText(str(self._temp_config.get("key_prev", "pageup")))
            except Exception:
                pass

            try:
                slots = list(self._temp_config.get("slots", []))
                while len(slots) < 8:
                    slots.append("")
                for i, ed in enumerate(getattr(self, "_slot_edits", [])):
                    try:
                        ed.setText(str(slots[i]))
                    except Exception:
                        pass
            except Exception:
                pass

            self._emit_preview()

        btn_reset.clicked.connect(_do_reset_ui)
        reset_l.addWidget(btn_reset, 1)
        root.addWidget(reset_row)
        root.addStretch(1)

    def _build_hotkeys(self, parent: QWidget) -> None:
        root = QVBoxLayout(parent)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        nav = QFrame(parent)
        nav_l = QFormLayout(nav)
        nav_l.setContentsMargins(0, 0, 0, 0)

        self._key_next = QLineEdit(nav)
        self._key_prev = QLineEdit(nav)
        self._key_next.setText(str(self._temp_config.get("key_next", "pagedown")))
        self._key_prev.setText(str(self._temp_config.get("key_prev", "pageup")))

        for e in (self._key_next, self._key_prev):
            e.setAlignment(Qt.AlignCenter)
            e.installEventFilter(self)
            e.setStyleSheet("background: rgba(255,255,255,14); color: rgba(232,232,240,255); border: 1px solid rgba(255,255,255,14); border-radius: 10px; padding: 8px;")

        nav_l.addRow("Siguiente >>", self._key_next)
        nav_l.addRow("Anterior <<", self._key_prev)
        root.addWidget(QLabel("Navegación", parent))
        root.addWidget(nav)

        root.addWidget(QLabel("Slots Personajes", parent))

        self._slot_edits: list[QLineEdit] = []
        slots = list(self._temp_config.get("slots", []))
        while len(slots) < 8:
            slots.append("")

        for i in range(8):
            ed = QLineEdit(parent)
            ed.setAlignment(Qt.AlignCenter)
            ed.setText(str(slots[i]))
            ed.installEventFilter(self)
            ed.setStyleSheet("background: rgba(255,255,255,14); color: rgba(232,232,240,255); border: 1px solid rgba(255,255,255,14); border-radius: 10px; padding: 8px;")
            self._slot_edits.append(ed)
            row = QFrame(parent)
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.addWidget(QLabel(f"Personaje {i+1}", parent))
            row_l.addWidget(ed, 1)
            root.addWidget(row)

        root.addStretch(1)

    def _build_profiles(self, parent: QWidget) -> None:
        root = QVBoxLayout(parent)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        btn_reorder = QPushButton("↕️REORDENAR VENTANAS", parent)
        def _open_reorder() -> None:
            try:
                org = OrganizerWindow(self, self._temp_windows, icons=self._icons)
                org.windowsChanged.connect(self._on_reordered)
                org.exec()
            except Exception:
                self.reorderRequested.emit(self._temp_windows)

        btn_reorder.clicked.connect(_open_reorder)
        btn_reorder.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,18);color:rgba(232,232,240,255);border:1px solid rgba(255,255,255,18);border-radius:12px;padding:10px 12px;font-weight:800;}"
            "QPushButton:hover{background:rgba(255,255,255,24);}" 
        )
        root.addWidget(btn_reorder)

        root.addWidget(QLabel("Gestión de Perfiles (Teams)", parent))

        self._profiles = QListWidget(parent)
        self._profiles.setStyleSheet("background: rgba(255,255,255,10); color: rgba(232,232,240,255); border: 1px solid rgba(255,255,255,14); border-radius: 12px;")
        root.addWidget(self._profiles, 1)

        self._refresh_profiles()

        btns = QFrame(parent)
        btns_l = QHBoxLayout(btns)
        btns_l.setContentsMargins(0, 0, 0, 0)

        save = QPushButton("💾 Guardar", parent)
        load = QPushButton("📂 Cargar", parent)
        for b in (save, load):
            b.setStyleSheet(
                "QPushButton{background:rgba(255,255,255,18);color:rgba(232,232,240,255);border:1px solid rgba(255,255,255,18);border-radius:12px;padding:10px 12px;font-weight:800;}"
                "QPushButton:hover{background:rgba(255,255,255,24);}"
            )

        save.clicked.connect(self._save_profile)
        load.clicked.connect(self._load_profile)

        btns_l.addWidget(save, 1)
        btns_l.addWidget(load, 1)
        root.addWidget(btns)

    def _refresh_profiles(self) -> None:
        self._profiles.clear()
        for name in self._temp_config.get("profiles", {}):
            self._profiles.addItem(QListWidgetItem(name))

    def _save_profile(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Guardar Perfil", "Nombre del Team (ej: PvM):")
        if not ok:
            return
        if name:
            order_names = [w.char_name for w in self._temp_windows]
            self._temp_config.setdefault("profiles", {})[name] = order_names
            self._refresh_profiles()

    def _load_profile(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        item = self._profiles.currentItem()
        if not item:
            return
        p_name = item.text()
        saved_order = self._temp_config.get("profiles", {}).get(p_name, [])

        current_pool = list(self._temp_windows)
        new_list: list[WindowEntry] = []

        for saved_char in saved_order:
            found = next((w for w in current_pool if w.char_name == saved_char), None)
            if found:
                new_list.append(found)
                current_pool.remove(found)

        new_list.extend(current_pool)
        self._temp_windows[:] = new_list
        QMessageBox.information(self, "Cargado", f"Perfil '{p_name}' aplicado.")
        self.windowsApplied.emit(list(self._temp_windows))
        self._emit_preview()

    def _set_bool(self, key: str, val: bool) -> None:
        self._temp_config[key] = bool(val)
        self._emit_preview()

    def eventFilter(self, watched: QObject, event) -> bool:
        from PySide6.QtCore import QEvent

        if event.type() == QEvent.KeyPress:
            key = event.key()
            text = event.text()

            mapped = {
                Qt.Key_PageUp: "pageup",
                Qt.Key_PageDown: "pagedown",
                Qt.Key_Return: "enter",
                Qt.Key_Enter: "enter",
            }

            final_key = mapped.get(key)
            if final_key is None:
                if Qt.Key_F1 <= key <= Qt.Key_F24:
                    final_key = f"f{int(key - Qt.Key_F1) + 1}"
                elif text:
                    final_key = text.lower()
                else:
                    try:
                        final_key = event.keyCombination().toString().lower()
                    except Exception:
                        final_key = ""

            if isinstance(watched, QLineEdit):
                watched.setText(final_key)
                self._sync_hotkeys()
                return True

        return super().eventFilter(watched, event)

    def _sync_hotkeys(self) -> None:
        self._temp_config["key_next"] = self._key_next.text().strip()
        self._temp_config["key_prev"] = self._key_prev.text().strip()
        self._temp_config["slots"] = [e.text().strip() for e in self._slot_edits]
        self._emit_preview()

    def _on_save(self) -> None:
        self._sync_hotkeys()
        self.configSaved.emit(self._temp_config, self._temp_windows)
        self.accept()

    def _on_cancel(self) -> None:
        self.reject()

    def _load_almanax_async(self) -> None:
        def bg():
            offer, bonus = self._almanax.get_almanax_data()
            try:
                icon_raw = None
                try:
                    icon_raw = self._almanax.fetch_dolmanax_icon_bytes(size=46)
                except Exception:
                    icon_raw = None
                self.almanaxLoaded.emit(offer, bonus, icon_raw)
            except Exception:
                pass

        threading.Thread(target=bg, daemon=True).start()

    def _apply_almanax(self, offer: str, bonus: str, icon_raw: object) -> None:
        try:
            self._almanax_offer.setText(offer)
            self._almanax_bonus.setText(bonus)
        except Exception:
            pass

        try:
            from PySide6.QtGui import QPixmap

            if isinstance(icon_raw, (bytes, bytearray)) and icon_raw:
                pix = QPixmap()
                if pix.loadFromData(bytes(icon_raw)):
                    pix = pix.scaled(46, 46, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self._almanax_icon.setPixmap(pix)
                else:
                    self._almanax_icon.setPixmap(QPixmap())
            else:
                self._almanax_icon.setPixmap(QPixmap())
        except Exception:
            pass
