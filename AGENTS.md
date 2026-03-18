# AGENTS.md

## Cursor Cloud specific instructions

This is a minimal PySide6 QtQuick desktop GUI application ("Hello World" starter). There is no backend, no database, no tests, no CI/CD, and no linter configured.

### Project structure

- `main.py` — Python entry point (creates `QGuiApplication`, loads QML, runs event loop)
- `main.qml` — QML UI definition (640x480 window titled "Hello World")
- `requirements.txt` — Single dependency: `PySide6==6.8.2.1`
- `pyproject.toml` — Project metadata for PySide6 tooling

### Running the application

```bash
source /workspace/.venv/bin/activate
DISPLAY=:1 QT_QUICK_BACKEND=software python3 main.py
```

- **`QT_QUICK_BACKEND=software`** is required in this VM because hardware OpenGL acceleration is not available. Without it, QtQuick will fail to render.
- **`DISPLAY=:1`** uses the VM's desktop display. For headless/CI testing, use `DISPLAY=:99` with Xvfb (`Xvfb :99 -screen 0 1280x1024x24 &`).

### Notes

- No automated tests exist in this project (`.gitignore` even excludes `test_*.py`).
- No linter is configured. If needed, install and run `pylint` or `ruff` manually.
- The venv is at `/workspace/.venv`. Always activate it before running.
