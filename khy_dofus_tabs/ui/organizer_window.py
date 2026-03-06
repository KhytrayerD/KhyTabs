from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIntValidator, QPainter, QPixmap, QDrag
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
)

from khy_dofus_tabs.core.icons import IconRepository
from khy_dofus_tabs.core.window_scanner import WindowEntry
from khy_dofus_tabs.ui.animations import AnimationFactory


class _OrganizerList(QListWidget):
    orderChanged = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_item: QListWidgetItem | None = None
        self._drop_item: QListWidgetItem | None = None

    def startDrag(self, supportedActions) -> None:
        try:
            self._drag_item = self.currentItem()
        except Exception:
            self._drag_item = None

        w = None
        if self._drag_item is not None:
            try:
                w = self.itemWidget(self._drag_item)
            except Exception:
                w = None

        if w is None:
            super().startDrag(supportedActions)
            return

        try:
            w.setProperty("dragging", True)
            try:
                w.style().unpolish(w)
                w.style().polish(w)
            except Exception:
                pass

            dpr = 1.0
            try:
                dpr = float(self.window().devicePixelRatioF())
            except Exception:
                dpr = 1.0

            grab = QPixmap(int(w.width() * dpr), int(w.height() * dpr))
            grab.setDevicePixelRatio(dpr)
            grab.fill(Qt.transparent)

            p = QPainter()
            try:
                p.begin(grab)
                p.setRenderHint(QPainter.Antialiasing)
                w.render(p)
            finally:
                try:
                    p.end()
                except Exception:
                    pass

            mime = None
            try:
                mime = self.model().mimeData(self.selectedIndexes())
            except Exception:
                mime = None

            drag = QDrag(self)
            if mime is not None:
                drag.setMimeData(mime)
            drag.setPixmap(grab)
            drag.setHotSpot(w.rect().center())

            drag.exec(supportedActions)
        except Exception:
            super().startDrag(supportedActions)

    def dropEvent(self, event) -> None:
        super().dropEvent(event)
        try:
            if self._drag_item is not None:
                w = self.itemWidget(self._drag_item)
                if w is not None:
                    w.setProperty("dragging", False)
                    try:
                        w.setGraphicsEffect(None)
                    except Exception:
                        pass
                    try:
                        w.style().unpolish(w)
                        w.style().polish(w)
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            if self._drop_item is not None:
                dw = self.itemWidget(self._drop_item)
                if dw is not None:
                    dw.setProperty("dropTarget", False)
                    try:
                        dw.style().unpolish(dw)
                        dw.style().polish(dw)
                    except Exception:
                        pass
        except Exception:
            pass
        self._drag_item = None
        self._drop_item = None
        QTimer.singleShot(0, self.orderChanged.emit)

    def dragMoveEvent(self, event) -> None:
        try:
            item = self.itemAt(event.position().toPoint())
        except Exception:
            item = None

        if item is not self._drop_item:
            try:
                if self._drop_item is not None:
                    old = self.itemWidget(self._drop_item)
                    if old is not None:
                        old.setProperty("dropTarget", False)
                        try:
                            old.style().unpolish(old)
                            old.style().polish(old)
                        except Exception:
                            pass
            except Exception:
                pass

            self._drop_item = item

            try:
                if self._drop_item is not None:
                    nw = self.itemWidget(self._drop_item)
                    if nw is not None:
                        nw.setProperty("dropTarget", True)
                        try:
                            nw.style().unpolish(nw)
                            nw.style().polish(nw)
                        except Exception:
                            pass
            except Exception:
                pass

        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event) -> None:
        try:
            if self._drop_item is not None:
                old = self.itemWidget(self._drop_item)
                if old is not None:
                    old.setProperty("dropTarget", False)
                    try:
                        old.style().unpolish(old)
                        old.style().polish(old)
                    except Exception:
                        pass
        except Exception:
            pass
        self._drop_item = None
        super().dragLeaveEvent(event)


class OrganizerWindow(QDialog):
    windowsChanged = Signal(list)

    def __init__(self, parent: QWidget, windows: list[WindowEntry], *, icons: IconRepository) -> None:
        super().__init__(parent)
        self.setWindowTitle("Organizador")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.resize(460, 520)

        self._target_list = windows
        self._icons = icons
        self._pix_cache: dict[str, QPixmap] = {}
        self._anim = AnimationFactory()

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        hdr = QFrame(self)
        hdr.setObjectName("OrganizerHeader")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(12, 10, 12, 10)
        title = QLabel("Organizador de Ventanas", hdr)
        title.setObjectName("OrganizerTitle")
        hl.addWidget(title)

        self._show_initiative = QCheckBox("Mostrar iniciativa", hdr)
        self._show_initiative.setObjectName("OrganizerInitiativeToggle")
        self._show_initiative.setChecked(False)
        self._show_initiative.stateChanged.connect(self._refresh)
        hl.addWidget(self._show_initiative)
        hl.setStretch(0, 1)

        root.addWidget(hdr)

        info = QLabel("Arrastra para reordenar — suelta para aplicar", self)
        info.setObjectName("OrganizerHint")
        root.addWidget(info)

        self._list = _OrganizerList(self)
        self._list.setDragDropMode(QListWidget.InternalMove)
        self._list.setDefaultDropAction(Qt.MoveAction)
        self._list.setSpacing(6)
        self._list.setObjectName("OrganizerList")
        self._list.setSelectionMode(QListWidget.SingleSelection)
        self._list.setDragEnabled(True)
        self._list.setAcceptDrops(True)
        self._list.setDropIndicatorShown(False)
        self._list.setDragDropOverwriteMode(False)
        self._list.setMovement(QListWidget.Snap)
        self._list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._list.orderChanged.connect(self._apply_list_order)
        root.addWidget(self._list, 1)

        self._refresh()

    def _refresh(self) -> None:
        show_init = self._show_initiative.isChecked()

        self._list.clear()
        for idx, w in enumerate(self._target_list):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, w)

            row = QFrame(self._list)
            row.setObjectName("OrganizerRow")
            row.setMouseTracking(True)
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(10, 10, 10, 10)
            row_l.setSpacing(10)

            row_h = 56 if show_init else 52
            row.setMinimumHeight(row_h)

            ico = QLabel(row)
            ico.setFixedSize(28, 28)
            ico.setAlignment(Qt.AlignCenter)
            pix = self._get_class_pixmap(w.class_name)
            if pix is not None and not pix.isNull():
                ico.setPixmap(pix)
            else:
                ico.setText("?")
            row_l.addWidget(ico, 0)

            lbl = QLabel(f"{idx+1}. {w.class_name} - {w.char_name}", row)
            lbl.setObjectName("OrganizerRowText")
            row_l.addWidget(lbl, 1)

            ent = None
            if show_init:
                ent = QLineEdit(row)
                ent.setObjectName("OrganizerInitiative")
                ent.setText(str(int(getattr(w, "initiative", 0) or 0)))
                ent.setAlignment(Qt.AlignCenter)
                ent.setValidator(QIntValidator(0, 10**9, ent))
                ent.setFixedWidth(92)
                ent.setMinimumHeight(36)

                def _save(i: int, e: QLineEdit):
                    try:
                        val = int(e.text())
                    except Exception:
                        val = 0
                        e.setText("0")
                    if 0 <= i < len(self._target_list):
                        self._target_list[i].initiative = val
                    self._sort_by_initiative()

                ent.editingFinished.connect(lambda i=idx, e=ent: _save(i, e))
                row_l.addWidget(ent, 0)

            handle = QLabel("☰", row)
            handle.setObjectName("OrganizerHandle")
            row_l.addWidget(handle, 0)

            item.setSizeHint(row.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, row)

            hint = item.sizeHint()
            hint.setHeight(row_h)
            item.setSizeHint(hint)

    def showEvent(self, event) -> None:
        try:
            self.setWindowOpacity(0.0)
            self._anim.fade_window(self, 0.0, 1.0, 160)
        except Exception:
            pass
        super().showEvent(event)

    def closeEvent(self, event) -> None:
        try:
            self._apply_list_order()
        except Exception:
            pass
        super().closeEvent(event)

    def _get_class_pixmap(self, class_name: str) -> QPixmap | None:
        key = (class_name or "").lower().strip()
        if not key:
            return None

        if key in self._pix_cache:
            return self._pix_cache[key]

        raw = None
        try:
            raw = self._icons.fetch_class_icon_bytes(class_name)
        except Exception:
            raw = None

        if not raw:
            return None

        pix = QPixmap()
        if not pix.loadFromData(raw):
            return None

        pix = pix.scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._pix_cache[key] = pix
        return pix

    def _apply_list_order(self) -> None:
        new_list: list[WindowEntry] = []
        for i in range(self._list.count()):
            item = self._list.item(i)
            w = item.data(Qt.UserRole)
            if w is not None:
                new_list.append(w)

        if len(new_list) == len(self._target_list):
            self._target_list[:] = new_list
            self.windowsChanged.emit(list(self._target_list))

        QTimer.singleShot(0, self._refresh)

    def _sort_by_initiative(self) -> None:
        try:
            self._target_list.sort(key=lambda it: int(getattr(it, "initiative", 0)), reverse=True)
        except Exception:
            def _safe(it):
                try:
                    return int(getattr(it, "initiative", 0))
                except Exception:
                    return 0
            self._target_list.sort(key=_safe, reverse=True)

        self.windowsChanged.emit(list(self._target_list))
        self._refresh()
