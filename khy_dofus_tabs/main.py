import sys
from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from khy_dofus_tabs.core.config import load_config
from khy_dofus_tabs.core.window_scanner import WindowScanner
from khy_dofus_tabs.core.window_focus import WindowFocuser
from khy_dofus_tabs.core.hotkeys import HotkeyManager
from khy_dofus_tabs.core.icons import IconRepository
from khy_dofus_tabs.core.almanax import AlmanaxClient
from khy_dofus_tabs.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    try:
        app.setStyle("Fusion")
        pal = QPalette()
        pal.setColor(QPalette.Window, QColor(14, 14, 18))
        pal.setColor(QPalette.WindowText, QColor(232, 232, 240))
        pal.setColor(QPalette.Base, QColor(18, 18, 22))
        pal.setColor(QPalette.AlternateBase, QColor(22, 22, 28))
        pal.setColor(QPalette.Text, QColor(232, 232, 240))
        pal.setColor(QPalette.Button, QColor(24, 24, 30))
        pal.setColor(QPalette.ButtonText, QColor(232, 232, 240))
        pal.setColor(QPalette.Highlight, QColor(255, 200, 74))
        pal.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        app.setPalette(pal)
    except Exception:
        pass

    try:
        qss_path = Path(__file__).resolve().parent / "assets" / "qss" / "theme.qss"
        if qss_path.exists():
            app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    except Exception:
        pass

    config = load_config()

    scanner = WindowScanner()
    focuser = WindowFocuser()
    icons = IconRepository()
    almanax = AlmanaxClient()

    hotkeys = HotkeyManager()

    window = MainWindow(
        config=config,
        scanner=scanner,
        focuser=focuser,
        hotkeys=hotkeys,
        icons=icons,
        almanax=almanax,
    )
    window.show()

    exit_code = 0
    try:
        exit_code = app.exec()
    finally:
        try:
            window.shutdown()
        except Exception:
            pass

    sys.exit(exit_code)
