"""DM码打印工具 — PySide6 主窗口."""

from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIntValidator
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from dm_printer.code_generator import (
    generate_big_codes,
    generate_small_codes,
)
from dm_printer.printer_backend import (
    get_available_printers,
    send_zpl,
)
from dm_printer.zpl_generator import (
    CODES_PER_LABEL,
    generate_zpl,
)


class MainWindow(QMainWindow):
    """应用主窗口：码号生成 → 列表编辑 → 直接打印."""

    _CODE_TYPE_BIG = 0
    _CODE_TYPE_SMALL = 1

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("DM码打印工具 v1.0")
        self.setMinimumSize(560, 720)
        self.resize(600, 780)

        self._current_zpl_list: list[str] = []

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setSpacing(10)

        root_layout.addWidget(self._build_code_type_group())
        root_layout.addWidget(self._build_big_code_group())
        root_layout.addWidget(self._build_small_code_group())
        root_layout.addWidget(self._build_generate_button())
        root_layout.addWidget(self._build_code_list_group())
        root_layout.addWidget(self._build_options_group())
        root_layout.addWidget(self._build_printer_group())
        root_layout.addLayout(self._build_action_buttons())

        self.statusBar().showMessage("就绪")

        self._on_code_type_changed()

    # ── UI 构建 ──────────────────────────────────

    def _build_code_type_group(self) -> QGroupBox:
        group = QGroupBox("① 选择码类型")
        layout = QHBoxLayout(group)
        self._radio_big = QRadioButton("大码（8位数字递增）")
        self._radio_small = QRadioButton("小码（XY坐标+A）")
        self._radio_big.setChecked(True)

        self._type_group = QButtonGroup(self)
        self._type_group.addButton(
            self._radio_big, self._CODE_TYPE_BIG
        )
        self._type_group.addButton(
            self._radio_small, self._CODE_TYPE_SMALL
        )
        self._type_group.idToggled.connect(
            self._on_code_type_changed
        )

        layout.addWidget(self._radio_big)
        layout.addWidget(self._radio_small)
        return group

    def _build_big_code_group(self) -> QGroupBox:
        self._big_group = QGroupBox("大码参数")
        layout = QGridLayout(self._big_group)

        layout.addWidget(QLabel("起始编号:"), 0, 0)
        self._big_start = QLineEdit("00090001")
        self._big_start.setValidator(QIntValidator(0, 99999999))
        self._big_start.setMaxLength(8)
        layout.addWidget(self._big_start, 0, 1)

        layout.addWidget(QLabel("打印数量:"), 0, 2)
        self._big_count = QSpinBox()
        self._big_count.setRange(1, 9999)
        self._big_count.setValue(16)
        layout.addWidget(self._big_count, 0, 3)

        return self._big_group

    def _build_small_code_group(self) -> QGroupBox:
        self._small_group = QGroupBox("小码参数")
        layout = QGridLayout(self._small_group)

        layout.addWidget(QLabel("X 起始:"), 0, 0)
        self._small_x = QSpinBox()
        self._small_x.setRange(0, 99999)
        self._small_x.setValue(100)
        layout.addWidget(self._small_x, 0, 1)

        layout.addWidget(QLabel("Y 起始:"), 0, 2)
        self._small_y = QSpinBox()
        self._small_y.setRange(0, 99999)
        self._small_y.setValue(200)
        layout.addWidget(self._small_y, 0, 3)

        layout.addWidget(QLabel("X 步长:"), 1, 0)
        self._small_x_step = QSpinBox()
        self._small_x_step.setRange(0, 99999)
        self._small_x_step.setValue(1)
        layout.addWidget(self._small_x_step, 1, 1)

        layout.addWidget(QLabel("Y 步长:"), 1, 2)
        self._small_y_step = QSpinBox()
        self._small_y_step.setRange(0, 99999)
        self._small_y_step.setValue(0)
        layout.addWidget(self._small_y_step, 1, 3)

        layout.addWidget(QLabel("打印数量:"), 2, 0)
        self._small_count = QSpinBox()
        self._small_count.setRange(1, 9999)
        self._small_count.setValue(16)
        layout.addWidget(self._small_count, 2, 1)

        return self._small_group

    def _build_generate_button(self) -> QPushButton:
        btn = QPushButton("② 生成码号列表")
        btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #0078D4;"
            "  color: white;"
            "  font-weight: bold;"
            "  padding: 8px;"
            "  border-radius: 4px;"
            "}"
            "QPushButton:hover { background-color: #106EBE; }"
            "QPushButton:pressed { background-color: #005A9E; }"
        )
        btn.clicked.connect(self._on_generate)
        return btn

    def _build_code_list_group(self) -> QGroupBox:
        group = QGroupBox("码号列表（可手动编辑、增删）")
        layout = QVBoxLayout(group)

        self._code_edit = QPlainTextEdit()
        self._code_edit.setFont(QFont("Consolas", 10))
        self._code_edit.setPlaceholderText(
            "点击「生成码号列表」或直接在此输入码号，每行一个"
        )
        layout.addWidget(self._code_edit)

        info_layout = QHBoxLayout()
        self._lbl_code_count = QLabel("码号: 0")
        self._lbl_label_count = QLabel("标签: 0 张")
        info_layout.addWidget(self._lbl_code_count)
        info_layout.addStretch()
        info_layout.addWidget(self._lbl_label_count)
        layout.addLayout(info_layout)

        self._code_edit.textChanged.connect(
            self._on_code_list_changed
        )
        return group

    def _build_options_group(self) -> QGroupBox:
        group = QGroupBox("打印选项")
        layout = QHBoxLayout(group)

        self._chk_flip_y = QCheckBox("翻转Y轴（适配出纸方向）")
        self._chk_center = QCheckBox("码居中于网格点")
        self._chk_center.setChecked(True)

        layout.addWidget(self._chk_flip_y)
        layout.addWidget(self._chk_center)
        return group

    def _build_printer_group(self) -> QGroupBox:
        group = QGroupBox("③ 选择打印机")
        layout = QHBoxLayout(group)

        self._combo_printer = QComboBox()
        self._combo_printer.setEditable(True)
        printers = get_available_printers()
        self._combo_printer.addItems(printers)
        layout.addWidget(self._combo_printer, stretch=1)

        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self._on_refresh_printers)
        layout.addWidget(btn_refresh)
        return group

    def _build_action_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        self._btn_test = QPushButton("测试打印（前4个码）")
        self._btn_test.setStyleSheet(
            "QPushButton {"
            "  background-color: #FF8C00;"
            "  color: white;"
            "  font-weight: bold;"
            "  padding: 10px 20px;"
            "  border-radius: 4px;"
            "}"
            "QPushButton:hover { background-color: #E07B00; }"
        )
        self._btn_test.clicked.connect(
            lambda: self._on_print(test_mode=True)
        )
        layout.addWidget(self._btn_test)

        self._btn_print = QPushButton("④ 直接打印")
        self._btn_print.setStyleSheet(
            "QPushButton {"
            "  background-color: #107C10;"
            "  color: white;"
            "  font-weight: bold;"
            "  padding: 10px 20px;"
            "  border-radius: 4px;"
            "}"
            "QPushButton:hover { background-color: #0E6B0E; }"
            "QPushButton:pressed { background-color: #0B5A0B; }"
        )
        self._btn_print.clicked.connect(
            lambda: self._on_print(test_mode=False)
        )
        layout.addWidget(self._btn_print)

        self._btn_save_zpl = QPushButton("保存ZPL文件")
        self._btn_save_zpl.setToolTip("将生成的ZPL指令保存到文件")
        self._btn_save_zpl.clicked.connect(self._on_save_zpl)
        layout.addWidget(self._btn_save_zpl)

        return layout

    # ── 事件处理 ──────────────────────────────────

    def _on_code_type_changed(self) -> None:
        is_big = (
            self._type_group.checkedId() == self._CODE_TYPE_BIG
        )
        self._big_group.setVisible(is_big)
        self._small_group.setVisible(not is_big)

    def _on_generate(self) -> None:
        if (
            self._type_group.checkedId() == self._CODE_TYPE_BIG
        ):
            text = self._big_start.text().strip()
            if not text:
                self.statusBar().showMessage("请输入起始编号")
                return
            start = int(text)
            count = self._big_count.value()
            codes = generate_big_codes(start, count)
        else:
            codes = generate_small_codes(
                x_start=self._small_x.value(),
                y_start=self._small_y.value(),
                x_step=self._small_x_step.value(),
                y_step=self._small_y_step.value(),
                count=self._small_count.value(),
            )

        self._code_edit.setPlainText("\n".join(codes))
        self.statusBar().showMessage(
            f"已生成 {len(codes)} 个码号"
        )

    def _on_code_list_changed(self) -> None:
        codes = self._get_codes_from_editor()
        n = len(codes)
        labels = math.ceil(n / CODES_PER_LABEL) if n else 0
        self._lbl_code_count.setText(f"码号: {n}")
        self._lbl_label_count.setText(f"标签: {labels} 张")

    def _on_refresh_printers(self) -> None:
        self._combo_printer.clear()
        self._combo_printer.addItems(get_available_printers())
        self.statusBar().showMessage("打印机列表已刷新")

    def _on_print(self, test_mode: bool = False) -> None:
        codes = self._get_codes_from_editor()
        if not codes:
            QMessageBox.warning(
                self, "提示", "码号列表为空，请先生成或输入码号。"
            )
            return

        if test_mode:
            codes = codes[:4]

        zpl_list = generate_zpl(
            codes,
            flip_y=self._chk_flip_y.isChecked(),
            center_offset=self._chk_center.isChecked(),
        )
        self._current_zpl_list = zpl_list

        printer = self._combo_printer.currentText().strip()
        if not printer:
            QMessageBox.warning(self, "提示", "请选择打印机。")
            return

        total = len(zpl_list)
        success = 0
        last_msg = ""

        for idx, zpl in enumerate(zpl_list, start=1):
            self.statusBar().showMessage(
                f"正在打印 {idx}/{total} ..."
            )
            QApplication.processEvents()
            last_msg = send_zpl(zpl, printer)
            if "错误" in last_msg or "出错" in last_msg:
                QMessageBox.critical(
                    self,
                    "打印错误",
                    f"第 {idx} 张标签打印失败：\n{last_msg}",
                )
                break
            success += 1

        mode_txt = "测试" if test_mode else "正式"
        self.statusBar().showMessage(
            f"{mode_txt}打印完成：{success}/{total} 张标签 — "
            f"{last_msg}"
        )

    def _on_save_zpl(self) -> None:
        codes = self._get_codes_from_editor()
        if not codes:
            QMessageBox.warning(
                self, "提示", "码号列表为空，请先生成或输入码号。"
            )
            return

        zpl_list = generate_zpl(
            codes,
            flip_y=self._chk_flip_y.isChecked(),
            center_offset=self._chk_center.isChecked(),
        )

        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            self,
            "保存 ZPL 文件",
            "dm_labels.zpl",
            "ZPL Files (*.zpl);;All Files (*)",
        )
        if not path:
            return

        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n\n".join(zpl_list))

        self.statusBar().showMessage(f"ZPL 已保存到 {path}")

    # ── 辅助方法 ──────────────────────────────────

    def _get_codes_from_editor(self) -> list[str]:
        text = self._code_edit.toPlainText()
        return [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]
