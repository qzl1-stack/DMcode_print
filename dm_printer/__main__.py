"""允许通过 python -m dm_printer 启动."""

import sys
from pathlib import Path

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

from dm_printer.backend import Backend


def main() -> None:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("DM码打印工具")
    app.setApplicationVersion("2.0")

    engine = QQmlApplicationEngine()

    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)

    qml_file = str(Path(__file__).resolve().parent.parent / "main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
