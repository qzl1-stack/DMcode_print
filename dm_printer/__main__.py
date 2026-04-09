"""允许通过 python -m dm_printer 启动."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from dm_printer.backend import Backend
from dm_printer.local_socket_client import LocalSocketClient


def main() -> None:
    """包入口，行为与 main.py 保持一致."""
    QQuickStyle.setStyle("Fusion")
    app = QGuiApplication(sys.argv)
    app.setApplicationName("DM码打印工具")
    app.setApplicationVersion("2.0")

    engine = QQmlApplicationEngine()
    backend = Backend()
    ipc_client = LocalSocketClient(
        sender_id=app.applicationName(),
        process_name=app.applicationName(),
        version=app.applicationVersion(),
        parent=app,
    )
    ipc_client.status_message.connect(backend.setExternalStatus)
    ipc_client.graceful_shutdown_requested.connect(app.quit)
    app.aboutToQuit.connect(ipc_client.stop)

    engine.rootContext().setContextProperty("backend", backend)
    qml_file = str(Path(__file__).resolve().parent.parent / "main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    QTimer.singleShot(0, ipc_client.start)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
