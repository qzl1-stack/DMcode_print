"""DM码打印工具 — 入口文件.

用法：
    python main.py
"""

import sys

from PySide6.QtWidgets import QApplication

from dm_printer.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
