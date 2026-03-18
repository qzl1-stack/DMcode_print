"""打印后端：将 ZPL 指令以 RAW 模式发送到 Zebra 打印机.

Windows 使用 win32print，其他平台回退为文件保存（便于开发调试）。
"""

from __future__ import annotations

import os
import sys
from typing import Optional


def get_available_printers() -> list[str]:
    """获取系统中可用的打印机名称列表."""
    if sys.platform == "win32":
        try:
            import win32print  # type: ignore[import-untyped]

            flags = (
                win32print.PRINTER_ENUM_LOCAL
                | win32print.PRINTER_ENUM_CONNECTIONS
            )
            printers = win32print.EnumPrinters(flags, None, 2)
            return [p["pPrinterName"] for p in printers]
        except Exception:
            return []
    return ["[调试] 保存到文件 (非Windows系统)"]


def get_default_printer() -> Optional[str]:
    """获取系统默认打印机名称."""
    if sys.platform == "win32":
        try:
            import win32print  # type: ignore[import-untyped]

            return win32print.GetDefaultPrinter()
        except Exception:
            return None
    return None


def send_zpl(
    zpl: str,
    printer_name: str,
    save_dir: Optional[str] = None,
) -> str:
    """将 ZPL 指令发送到打印机.

    Args:
        zpl:          完整的 ZPL 指令字符串
        printer_name: 目标打印机名称
        save_dir:     (可选) 同时保存 .zpl 文件的目录

    Returns:
        操作结果描述（成功/失败信息）
    """
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, "last_print.zpl")
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(zpl)

    if sys.platform == "win32":
        return _send_via_win32(zpl, printer_name)

    filepath = save_dir or "."
    target = os.path.join(filepath, "last_print.zpl")
    if not save_dir:
        os.makedirs(".", exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(zpl)
    return f"[调试模式] ZPL 已保存到 {os.path.abspath(target)}"


def _send_via_win32(zpl: str, printer_name: str) -> str:
    """通过 win32print RAW 模式发送 ZPL."""
    try:
        import win32print  # type: ignore[import-untyped]
    except ImportError:
        return "错误：未安装 pywin32，请执行 pip install pywin32"

    try:
        hprinter = win32print.OpenPrinter(printer_name)
    except Exception as exc:
        return f"错误：无法打开打印机 '{printer_name}'：{exc}"

    try:
        doc_info = ("DM Label", None, "RAW")
        win32print.StartDocPrinter(hprinter, 1, doc_info)
        try:
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(
                hprinter, zpl.encode("utf-8")
            )
            win32print.EndPagePrinter(hprinter)
        finally:
            win32print.EndDocPrinter(hprinter)
    except Exception as exc:
        return f"打印出错：{exc}"
    finally:
        win32print.ClosePrinter(hprinter)

    return "打印成功"
