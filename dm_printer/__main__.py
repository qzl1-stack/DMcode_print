"""允许通过 python -m dm_printer 启动."""

from dm_printer.main_window import MainWindow

from PyQt6.QtWidgets import QApplication
import sys


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
