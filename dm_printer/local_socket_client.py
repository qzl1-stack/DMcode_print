"""本地套接字客户端：发送 HELLO / HEARTBEAT，处理 COMMAND."""

from __future__ import annotations

import json
import time
import uuid

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtNetwork import QLocalSocket

IPC_SERVER_NAME = "master_ipc_server"
IPC_RECEIVER_ID = "main_process"
HELLO_TYPE = 0
HEARTBEAT_TYPE = 2
HEARTBEAT_ACK_TYPE = 3
COMMAND_TYPE = 5
RECONNECT_INTERVAL_MS = 5000
HEARTBEAT_INTERVAL_MS = 10000


class LocalSocketClient(QObject):
    """本地 IPC 客户端."""

    graceful_shutdown_requested = Signal()
    status_message = Signal(str)

    def __init__(
        self,
        sender_id: str,
        process_name: str,
        version: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._sender_id = sender_id
        self._process_name = process_name
        self._version = version
        self._buffer = ""

        self._socket = QLocalSocket(self)
        self._socket.connected.connect(self._on_connected)
        self._socket.disconnected.connect(self._on_disconnected)
        self._socket.readyRead.connect(self._on_ready_read)
        self._socket.errorOccurred.connect(self._on_error_occurred)

        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setInterval(RECONNECT_INTERVAL_MS)
        self._reconnect_timer.timeout.connect(self._connect_to_server)

        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.setInterval(HEARTBEAT_INTERVAL_MS)
        self._heartbeat_timer.timeout.connect(self._send_heartbeat)

    @Slot()
    def start(self) -> None:
        """启动客户端并尝试连接服务端."""
        self._connect_to_server()

    @Slot()
    def stop(self) -> None:
        """停止客户端."""
        self._reconnect_timer.stop()
        self._heartbeat_timer.stop()
        if self._socket.state() != QLocalSocket.UnconnectedState:
            self._socket.disconnectFromServer()

    def _timestamp_ms(self) -> int:
        return int(time.time() * 1000)

    def _build_message(self, msg_type: int, topic: str, body: dict) -> dict:
        return {
            "type": msg_type,
            "topic": topic,
            "msg_id": uuid.uuid4().hex,
            "timestamp": self._timestamp_ms(),
            "sender_id": self._sender_id,
            "receiver_id": IPC_RECEIVER_ID,
            "body": body,
        }

    def _write_message(self, message: dict) -> None:
        payload = json.dumps(message, ensure_ascii=False) + "\n"
        self._socket.write(payload.encode("utf-8"))
        self._socket.flush()

    @Slot()
    def _connect_to_server(self) -> None:
        state = self._socket.state()
        if state in (
            QLocalSocket.ConnectedState,
            QLocalSocket.ConnectingState,
        ):
            return
        self._socket.abort()
        self._socket.connectToServer(IPC_SERVER_NAME)

    @Slot()
    def _on_connected(self) -> None:
        self._reconnect_timer.stop()
        self.status_message.emit("IPC 已连接，已发送注册消息")
        self._send_hello()
        self._heartbeat_timer.start()

    @Slot()
    def _on_disconnected(self) -> None:
        self._heartbeat_timer.stop()
        self.status_message.emit("IPC 已断开，正在等待重连")
        if not self._reconnect_timer.isActive():
            self._reconnect_timer.start()

    @Slot()
    def _send_hello(self) -> None:
        message = self._build_message(
            HELLO_TYPE,
            "registration",
            {
                "version": self._version,
                "process_name": self._process_name,
            },
        )
        self._write_message(message)

    @Slot()
    def _send_heartbeat(self) -> None:
        if self._socket.state() != QLocalSocket.ConnectedState:
            return
        message = self._build_message(
            HEARTBEAT_TYPE,
            "heartbeat",
            {
                "process_state": "running",
                "process_name": self._process_name,
                "timestamp": self._timestamp_ms(),
            },
        )
        self._write_message(message)

    @Slot()
    def _on_ready_read(self) -> None:
        chunk = bytes(self._socket.readAll()).decode("utf-8", errors="ignore")
        if not chunk:
            return
        self._buffer += chunk
        while "\n" in self._buffer:
            raw_line, self._buffer = self._buffer.split("\n", 1)
            line = raw_line.strip()
            if line:
                self._handle_message(line)

    def _handle_message(self, line: str) -> None:
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            self.status_message.emit("IPC 收到非法 JSON 消息")
            return

        msg_type = int(message.get("type", -1))
        body = message.get("body", {})
        if not isinstance(body, dict):
            return

        if msg_type == HEARTBEAT_ACK_TYPE:
            self.status_message.emit("IPC 心跳确认已收到")
            return

        if msg_type != COMMAND_TYPE:
            return

        command = str(body.get("command", "")).strip()
        if command != "graceful_shutdown":
            return

        self.status_message.emit("IPC 收到 graceful_shutdown，正在关闭界面")
        self.graceful_shutdown_requested.emit()

    @Slot(QLocalSocket.LocalSocketError)
    def _on_error_occurred(self, _: QLocalSocket.LocalSocketError) -> None:
        if self._socket.state() == QLocalSocket.ConnectedState:
            return
        self.status_message.emit("IPC 连接失败，正在等待重连")
        if not self._reconnect_timer.isActive():
            self._reconnect_timer.start()
