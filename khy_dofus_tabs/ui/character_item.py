from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, Qt, Signal, QVariantAnimation
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import QBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget, QGraphicsDropShadowEffect


@dataclass
class CharacterItemState:
    title: str
    class_name: str
    char_name: str
    hotkey: str | None


class CharacterItem(QWidget):
    activated = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CharacterItem")
        self.setProperty("active", False)
        self.setProperty("textMode", "always")

        self._active_strength = 0.0
        self._active_anim: QVariantAnimation | None = None

        self._title = ""
        self._text_mode = "always"
        self._orientation = "vertical"
        self._base_pix: QPixmap | None = None
        self._contour_pix: QPixmap | None = None

        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setBlurRadius(22)
        self._glow.setOffset(0, 0)
        self._glow.setColor(Qt.transparent)
        self.setGraphicsEffect(self._glow)

        self._icon = QLabel(self)
        self._icon.setFixedSize(44, 44)
        self._icon.setAlignment(Qt.AlignCenter)

        self._name = QLabel(self)
        self._name.setObjectName("CharacterName")
        self._name.setTextInteractionFlags(Qt.NoTextInteraction)
        self._name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._hotkey = QLabel(self)
        self._hotkey.setObjectName("CharacterHotkey")
        self._hotkey.setTextInteractionFlags(Qt.NoTextInteraction)

        self._text_col = QVBoxLayout()
        self._text_col.setContentsMargins(0, 0, 0, 0)
        self._text_col.setSpacing(2)
        self._text_col.addWidget(self._name)
        self._text_col.addWidget(self._hotkey)

        self._root = QBoxLayout(QBoxLayout.LeftToRight, self)
        self._root.setContentsMargins(10, 8, 10, 8)
        self._root.setSpacing(10)
        self._root.addWidget(self._icon, 0, Qt.AlignCenter)
        self._root.addLayout(self._text_col, 1)

        self.setCursor(Qt.PointingHandCursor)

    def set_state(self, state: CharacterItemState) -> None:
        self._title = state.title
        self._name.setText(state.char_name)
        if state.hotkey:
            self._hotkey.setText(state.hotkey)
        else:
            self._hotkey.setText("")

    def set_text_mode(self, text_mode: str) -> None:
        self._text_mode = text_mode
        self.setProperty("textMode", text_mode)

        show_text_inline = text_mode == "always"
        self._name.setVisible(show_text_inline)
        self._hotkey.setVisible(show_text_inline)

        self._rebuild_layout()

        try:
            self._apply_active_style()
        except Exception:
            pass

    def set_orientation(self, orientation: str) -> None:
        self._orientation = orientation
        self._rebuild_layout()

    def set_metrics(self, *, icon_px: int, row_pad_x: int, row_pad_y: int, row_gap: int, name_px: int, hotkey_px: int) -> None:
        self._icon.setFixedSize(int(icon_px), int(icon_px))
        self._root.setContentsMargins(int(row_pad_x), int(row_pad_y), int(row_pad_x), int(row_pad_y))
        self._root.setSpacing(int(row_gap))
        self._name.setStyleSheet(f"font-size: {int(name_px)}px;")
        self._hotkey.setStyleSheet(f"font-size: {int(hotkey_px)}px;")
        self._apply_icon_for_active(bool(self.property("active")))

    def _rebuild_layout(self) -> None:
        try:
            while self._root.count():
                self._root.takeAt(0)
        except Exception:
            pass

        show_text_inline = self._text_mode == "always"

        if self._orientation == "vertical":
            self._root.setDirection(QBoxLayout.LeftToRight)
            self._root.addWidget(self._icon, 0, Qt.AlignCenter)
            if show_text_inline:
                self._root.addLayout(self._text_col, 1)
        else:
            self._root.setDirection(QBoxLayout.TopToBottom)
            self._root.addWidget(self._icon, 0, Qt.AlignCenter)
            if show_text_inline:
                self._root.addLayout(self._text_col, 1)

    def set_tooltip_text(self, text: str | None) -> None:
        self.setToolTip(text or "")

    def set_icon_pixmaps(self, base: QPixmap | None) -> None:
        self._base_pix = base
        self._contour_pix = None
        self._apply_icon_for_active(False)

    def set_active(self, active: bool) -> None:
        target = 1.0 if active else 0.0
        self.setProperty("active", bool(active))

        try:
            self.style().unpolish(self)
            self.style().polish(self)
        except Exception:
            pass

        try:
            if self._active_anim is not None:
                self._active_anim.stop()
        except Exception:
            pass

        anim = QVariantAnimation(self)
        anim.setStartValue(float(self._active_strength))
        anim.setEndValue(float(target))
        anim.setDuration(180)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _on(v):
            try:
                self._active_strength = float(v)
            except Exception:
                self._active_strength = target
            self._apply_active_style()

        anim.valueChanged.connect(_on)
        anim.finished.connect(lambda: self._apply_active_style())
        self._active_anim = anim
        anim.start()

        self._apply_icon_for_active(active)

    def _apply_active_style(self) -> None:
        s = float(self._active_strength)
        if s <= 0.001:
            try:
                self._glow.setColor(Qt.transparent)
            except Exception:
                pass
            return

        a = max(0, min(255, int(round(235 * s))))
        try:
            from PySide6.QtGui import QColor

            self._glow.setColor(QColor(120, 120, 255, a))
            self._glow.setBlurRadius(34)
        except Exception:
            pass

    def _apply_icon_for_active(self, active: bool) -> None:
        pix = self._base_pix
        if pix:
            try:
                target = self._icon.size()
                try:
                    dpr = float(pix.devicePixelRatioF())
                except Exception:
                    dpr = 1.0

                try:
                    logical_w = float(pix.width()) / dpr
                    logical_h = float(pix.height()) / dpr
                except Exception:
                    logical_w = float(pix.width())
                    logical_h = float(pix.height())

                if abs(logical_w - float(target.width())) <= 0.75 and abs(logical_h - float(target.height())) <= 0.75:
                    self._icon.setPixmap(pix)
                    return

                if logical_w > target.width() or logical_h > target.height():
                    mode = Qt.SmoothTransformation
                    if target.width() <= 22 or target.height() <= 22:
                        mode = Qt.FastTransformation
                    self._icon.setPixmap(pix.scaled(target, Qt.KeepAspectRatio, mode))
                else:
                    self._icon.setPixmap(pix)
            except Exception:
                self._icon.setPixmap(pix)
        else:
            self._icon.setPixmap(QPixmap())

    def _build_contour_pixmap(self, base: QPixmap | None) -> QPixmap | None:
        if base is None or base.isNull():
            return None

        img = base.toImage().convertToFormat(QImage.Format_ARGB32)
        out = QImage(img.size(), QImage.Format_ARGB32)
        out.fill(Qt.transparent)

        painter = QPainter(out)
        painter.setRenderHint(QPainter.Antialiasing)

        green = QImage(img.size(), QImage.Format_ARGB32)
        green.fill(Qt.transparent)

        gp = QPainter(green)
        gp.setCompositionMode(QPainter.CompositionMode_Source)
        gp.drawImage(0, 0, img)
        gp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        gp.fillRect(green.rect(), Qt.green)
        gp.end()

        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]
        for dx, dy in offsets:
            painter.drawImage(dx, dy, green)

        painter.drawImage(0, 0, img)
        painter.end()

        return QPixmap.fromImage(out)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.activated.emit(self._title)
        super().mousePressEvent(event)
