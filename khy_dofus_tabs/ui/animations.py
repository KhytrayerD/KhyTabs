from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, QObject


class AnimationFactory:
    def __init__(self) -> None:
        self._running: list[QObject] = []

    def fade_window(self, window, start: float, end: float, duration_ms: int = 200):
        anim = QPropertyAnimation(window, b"windowOpacity")
        anim.setStartValue(float(start))
        anim.setEndValue(float(end))
        anim.setDuration(int(duration_ms))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        self._retain(anim)
        anim.start()
        return anim

    def _retain(self, obj: QObject) -> None:
        self._running.append(obj)
        try:
            obj.finished.connect(lambda: self._release(obj))
        except Exception:
            pass

    def _release(self, obj: QObject) -> None:
        try:
            self._running.remove(obj)
        except ValueError:
            pass
