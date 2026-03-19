"""QML 后端桥接 — 将业务逻辑暴露给 QML 层."""

from __future__ import annotations

import math
import os
import tempfile
import time
from typing import Optional

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QUrl

from dm_printer.label_renderer import render_label, CODES_PER_LABEL
from dm_printer.code_generator import generate_batch_codes
from dm_printer.zpl_generator import generate_zpl
from dm_printer.printer_backend import get_available_printers, send_zpl


class Backend(QObject):
    """QML 后端：码号生成、标签预览、打印."""

    codeValueChanged = pyqtSignal()
    batchCountChanged = pyqtSignal()
    previewUrlChanged = pyqtSignal()
    statusChanged = pyqtSignal()
    printerListChanged = pyqtSignal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._code_value: str = "00090001"
        self._batch_count: int = 1
        self._preview_url: str = ""
        self._status: str = "就绪"
        self._printers: list[str] = get_available_printers()
        self._preview_dir = tempfile.mkdtemp(prefix="dm_preview_")

    @pyqtProperty(str, notify=codeValueChanged)
    def codeValue(self) -> str:
        return self._code_value

    @codeValue.setter
    def codeValue(self, value: str) -> None:
        if self._code_value != value:
            self._code_value = value
            self.codeValueChanged.emit()

    @pyqtProperty(int, notify=batchCountChanged)
    def batchCount(self) -> int:
        return self._batch_count

    @batchCount.setter
    def batchCount(self, value: int) -> None:
        if self._batch_count != value:
            self._batch_count = max(1, value)
            self.batchCountChanged.emit()

    @pyqtProperty(str, notify=previewUrlChanged)
    def previewUrl(self) -> str:
        return self._preview_url

    @pyqtProperty(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @pyqtProperty("QStringList", notify=printerListChanged)
    def printerList(self) -> list[str]:
        return self._printers

    def _set_status(self, msg: str) -> None:
        self._status = msg
        self.statusChanged.emit()

    @pyqtSlot()
    def generatePreview(self) -> None:
        code = self._code_value.strip()
        if not code:
            self._set_status("请输入码值")
            return
        try:
            path = os.path.join(self._preview_dir, "preview.png")
            render_label(code, path)
            ts = int(time.time() * 1000)
            self._preview_url = (
                QUrl.fromLocalFile(path).toString() + f"?t={ts}"
            )
            self.previewUrlChanged.emit()

            labels = math.ceil(self._batch_count * 1.0)
            self._set_status(
                f"预览已生成 — 码值: {code}, "
                f"每张标签 {CODES_PER_LABEL} 个码, "
                f"共 {self._batch_count} 张标签"
            )
        except Exception as exc:
            self._set_status(f"预览生成失败: {exc}")

    @pyqtSlot(str)
    def printLabels(self, printer_name: str) -> None:
        code = self._code_value.strip()
        if not code:
            self._set_status("请输入码值")
            return
        if not printer_name.strip():
            self._set_status("请选择打印机")
            return

        codes = generate_batch_codes(code, self._batch_count)
        total = len(codes)
        success = 0

        for idx, c in enumerate(codes):
            self._set_status(f"正在打印 {idx + 1}/{total} ...")
            zpl_list = generate_zpl(c)
            for zpl in zpl_list:
                msg = send_zpl(zpl, printer_name)
                if "错误" in msg or "出错" in msg:
                    self._set_status(f"第 {idx + 1} 张打印失败: {msg}")
                    return
            success += 1

        self._set_status(f"打印完成: {success}/{total} 张标签")

    @pyqtSlot(str, str)
    def saveZpl(self, printer_name: str, save_path: str) -> None:
        code = self._code_value.strip()
        if not code:
            self._set_status("请输入码值")
            return

        codes = generate_batch_codes(code, self._batch_count)
        all_zpl: list[str] = []
        for c in codes:
            all_zpl.extend(generate_zpl(c))

        target = save_path if save_path else "dm_labels.zpl"
        if target.startswith("file://"):
            target = QUrl(target).toLocalFile()
        if not target:
            target = "dm_labels.zpl"

        try:
            with open(target, "w", encoding="utf-8") as fh:
                fh.write("\n\n".join(all_zpl))
            self._set_status(f"ZPL 已保存: {os.path.abspath(target)}")
        except Exception as exc:
            self._set_status(f"保存失败: {exc}")

    @pyqtSlot()
    def refreshPrinters(self) -> None:
        self._printers = get_available_printers()
        self.printerListChanged.emit()
        self._set_status("打印机列表已刷新")
