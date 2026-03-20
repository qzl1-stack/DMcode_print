"""QML 后端桥接 — 将业务逻辑暴露给 QML 层."""

from __future__ import annotations

import os
import tempfile
import time
from typing import Optional

from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl

from dm_printer.label_renderer import render_label, CODES_PER_LABEL
from dm_printer.code_generator import generate_batch_codes
from dm_printer.zpl_generator import generate_zpl
from dm_printer.printer_backend import get_available_printers, send_zpl


class Backend(QObject):
    """QML 后端：码号生成、标签预览、打印."""

    codeValueChanged = Signal()
    batchCountChanged = Signal()
    previewImageUrlsChanged = Signal()
    statusChanged = Signal()
    printerListChanged = Signal()

    kMaxPreviewLabels = 10

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._code_value: str = "1"
        self._batch_count: int = 1
        self._preview_image_urls: list[str] = []
        self._status: str = "就绪"
        self._printers: list[str] = get_available_printers()
        self._preview_dir = tempfile.mkdtemp(prefix="dm_preview_")

    @Property(str, notify=codeValueChanged)
    def codeValue(self) -> str:
        return self._code_value

    @codeValue.setter
    def codeValue(self, value: str) -> None:
        if self._code_value != value:
            self._code_value = value
            self.codeValueChanged.emit()

    @Property(int, notify=batchCountChanged)
    def batchCount(self) -> int:
        return self._batch_count

    @batchCount.setter
    def batchCount(self, value: int) -> None:
        if self._batch_count != value:
            self._batch_count = max(1, value)
            self.batchCountChanged.emit()

    @Property("QStringList", notify=previewImageUrlsChanged)
    def previewImageUrls(self) -> list[str]:
        return self._preview_image_urls

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property("QStringList", notify=printerListChanged)
    def printerList(self) -> list[str]:
        return self._printers

    def _set_status(self, msg: str) -> None:
        self._status = msg
        self.statusChanged.emit()

    @Slot()
    def generatePreview(self) -> None:
        code = self._code_value.strip()
        if not code:
            self._set_status("请输入码值")
            return
        if not code.isdigit():
            self._set_status("码值必须为纯数字（例如 1）")
            return
        try:
            codes = generate_batch_codes(code, self._batch_count)
            total = len(codes)
            show_n = min(total, self.kMaxPreviewLabels)
            show_codes = codes[:show_n]
            ts = int(time.time() * 1000)
            urls: list[str] = []
            for i, c in enumerate(show_codes):
                path = os.path.join(
                    self._preview_dir, f"preview_label_{i}.png"
                )
                render_label(c, path)
                urls.append(
                    QUrl.fromLocalFile(path).toString() + f"?t={ts}"
                )
            self._preview_image_urls = urls
            self.previewImageUrlsChanged.emit()

            if total > self.kMaxPreviewLabels:
                self._set_status(
                    f"预览已生成 — 显示前 {show_n} 张（共 {total} 张），"
                    f"每张 {CODES_PER_LABEL} 个相同 DM 码"
                )
            else:
                self._set_status(
                    f"预览已生成 — 共 {total} 张标签，"
                    f"每张 {CODES_PER_LABEL} 个相同 DM 码"
                )
        except Exception as exc:
            self._set_status(f"预览生成失败: {exc}")

    @Slot(str)
    def printLabels(self, printer_name: str) -> None:
        """打印标签（真实打印机）."""
        code = self._code_value.strip()
        if not code:
            self._set_status("请输入码值")
            return
        if not code.isdigit():
            self._set_status("码值必须为纯数字（例如 1）")
            return

        printer = (printer_name or "").strip()
        if not printer:
            self._set_status("请先选择打印机")
            return

        codes = generate_batch_codes(code, self._batch_count)
        total = len(codes)
        success = 0

        for idx, c in enumerate(codes, start=1):
            self._set_status(f"正在打印 {idx}/{total} ...")
            zpl_list = generate_zpl(c)
            for zpl in zpl_list:
                msg = send_zpl(zpl, printer)
                if "错误" in msg or "出错" in msg:
                    self._set_status(f"第 {idx} 张打印失败: {msg}")
                    return
            success += 1

        self._set_status(f"打印完成: {success}/{total} 张标签")

    @Slot(str, str)
    def saveZpl(self, printer_name: str, save_path: str) -> None:
        code = self._code_value.strip()
        if not code:
            self._set_status("请输入码值")
            return
        if not code.isdigit():
            self._set_status("码值必须为纯数字（例如 1）")
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

    @Slot()
    def refreshPrinters(self) -> None:
        self._printers = get_available_printers()
        self.printerListChanged.emit()
        self._set_status("打印机列表已刷新")
