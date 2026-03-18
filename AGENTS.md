# AGENTS.md

## Cursor Cloud specific instructions

This is a PyQt6 desktop application — **DM码打印工具 v1.0** (Data Matrix code label printing tool). It generates DM codes (big codes: 8-digit sequential, small codes: XY-coordinate based) and sends ZPL-II instructions to Zebra printers. On non-Windows, the printer backend falls back to saving `.zpl` files (debug mode).

### Project structure

- `main.py` — Entry point (`QApplication` + `MainWindow`)
- `dm_printer/main_window.py` — Main window UI (PyQt6 Widgets)
- `dm_printer/code_generator.py` — Code generation logic (big/small codes)
- `dm_printer/zpl_generator.py` — ZPL-II instruction generation for Zebra printers
- `dm_printer/printer_backend.py` — Printer interface (win32print on Windows, file-save fallback on Linux)
- `requirements.txt` — `PyQt6>=6.6.0` (+ `pywin32` on Windows only)

### Running the application

```bash
source /workspace/.venv/bin/activate
DISPLAY=:1 python3 main.py
```

- On headless Linux, use Xvfb: `Xvfb :99 -screen 0 1280x1024x24 &` then `DISPLAY=:99 python3 main.py`.
- No `QT_QUICK_BACKEND=software` needed — this app uses QtWidgets (not QtQuick).
- On non-Windows, the printer selector shows `[调试] 保存到文件 (非Windows系统)` and print actions save ZPL to `last_print.zpl` instead of sending to a printer.

### Notes

- No automated tests exist in this project.
- No linter is configured. Use `ruff` or `pylint` manually if needed.
- The venv is at `/workspace/.venv`. Always activate before running.
- `pywin32` dependency is Windows-only and skipped on Linux automatically.
