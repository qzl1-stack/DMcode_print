# AGENTS.md

## Cursor Cloud specific instructions

This is a PyQt6 + QML desktop application — **DM码打印工具 v2.0** (Data Matrix code label printing tool). It renders label previews with 16 identical DM codes in a 4×4 grid on a 100×100mm template (dashed border, XY axes, code value in top-right), and generates ZPL-II instructions for Zebra printers.

### Project structure

- `main.py` — QML entry point (`QGuiApplication` + `QQmlApplicationEngine`)
- `main.qml` — QML UI (two-panel: controls + preview)
- `dm_printer/backend.py` — QObject bridge exposing business logic to QML
- `dm_printer/label_renderer.py` — Pillow + pylibdmtx label preview renderer
- `dm_printer/code_generator.py` — Batch code generation (auto-increment)
- `dm_printer/zpl_generator.py` — ZPL-II instruction generator (16 identical codes per label)
- `dm_printer/printer_backend.py` — Printer interface (win32print on Windows, file-save on Linux)
- `requirements.txt` — PyQt6, Pillow, pylibdmtx, setuptools

### Running the application

```bash
source /workspace/.venv/bin/activate
DISPLAY=:1 python3 main.py
```

### System dependencies

- `libdmtx0b` and `libdmtx-dev` — required by `pylibdmtx` for Data Matrix encoding
- Qt/XCB libraries — required by PyQt6 for GUI rendering

### Notes

- On non-Windows, printer dropdown shows `[调试] 保存到文件`, and print saves ZPL to `last_print.zpl`.
- Each label contains 16 **identical** DM codes. For batch printing, each label gets a different code value (auto-incremented).
- The venv is at `/workspace/.venv`. Always activate before running.
- No automated tests or linter configured in this project.
