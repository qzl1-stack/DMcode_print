# DM 码打印工具 - 依赖库与路径说明

## 1. 项目依赖概览

本项目是 Python 桌面应用，所有依赖都通过 `pip` 包管理器安装，存储在虚拟环境的 `Lib/site-packages` 目录下。

### 1.1 依赖安装位置

```
项目根目录/
├── .venv/                          # 虚拟环境
│   ├── Lib/
│   │   └── site-packages/          # 所有第三方库的安装位置
│   │       ├── PySide6/
│   │       ├── PIL/                # Pillow 库
│   │       ├── pylibdmtx/
│   │       ├── win32/              # pywin32 库
│   │       └── ...
│   └── Scripts/
│       ├── python.exe              # Python 解释器
│       ├── pip.exe                 # pip 工具
│       └── ...
├── requirements.txt                # 依赖声明文件
└── pyproject.toml                  # 项目配置文件
```

### 1.2 依赖安装命令

```powershell
# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 安装所有依赖
pip install setuptools
pip install -r requirements.txt
```

## 2. 外部依赖库清单

### 2.1 核心依赖表


| 库名称            | 版本      | 用途                         | 获取方式         | License  | 备注                 |
| -------------- | ------- | -------------------------- | ------------ | -------- | ------------------ |
| **PySide6**    | 6.8.2.1 | Qt 的 Python 绑定，提供 GUI 框架   | PyPI         | LGPL 3.0 | 核心 GUI 库，包含 QML 支持 |
| **Qt**         | 6.8.x   | 底层 C++ 库（由 PySide6 自动安装）   | 随 PySide6 安装 | LGPL 3.0 | 由 PySide6 自动下载和集成  |
| **Pillow**     | ≥10.0.0 | Python 图像库，用于生成标签预览图像      | PyPI         | HPND     | 处理 PNG、JPEG 等图像格式  |
| **pylibdmtx**  | ≥0.1.9  | DM 码编码库的 Python 绑定         | PyPI         | MIT      | 包装原生 libdmtx C 库   |
| **pywin32**    | ≥306    | Windows API 调用接口           | PyPI         | PSF      | 仅在 Windows 系统安装    |
| **setuptools** | ≥65.0   | Python 打包工具和 distutils 兼容层 | PyPI         | MIT      | Python 3.12+ 兼容性要求 |


### 2.2 依赖说明详表

#### PySide6 - Qt GUI 框架

```
名称: PySide6
版本: 6.8.2.1（固定版本）
官方网站: https://www.qt.io/qt-for-python
用途:
  - 提供桌面应用 GUI 框架
  - 支持 QML 声明式 UI
  - 包含信号/槽机制、属性绑定等
获取方式: pip install PySide6==6.8.2.1
License: LGPL 3.0
安装位置: .venv\Lib\site-packages\PySide6\
依赖关系: 自动安装 Qt 6.8.x C++ 库
系统要求: Windows 10/11 64-bit
```

**关键路径**：

- QML 引擎：`PySide6.QtQml.QQmlApplicationEngine`
- QML 加载：项目根目录的 `main.qml`
- 样式设置：`PySide6.QtQuickControls2.QQuickStyle`

---

#### Pillow - 图像处理库

```
名称: Pillow (PIL)
版本: ≥10.0.0（最低版本）
官方网站: https://python-pillow.org/
用途:
  - 生成 DM 码标签预览图像
  - 绘制标签框、坐标轴、文字
  - 支持 PNG、JPEG 等图像格式
获取方式: pip install Pillow
License: HPND（Historical Permission Notice and Disclaimer）
安装位置: .venv\Lib\site-packages\PIL\
依赖库: libjpeg, libpng, zlib（自动随 Pillow 安装）
系统要求: 无特殊要求
```

**关键模块**：

- `PIL.Image` - 图像对象
- `PIL.ImageDraw` - 绘制工具
- `PIL.ImageFont` - 字体处理

**项目使用**：

```python
# 位置: dm_printer/label_renderer.py, dm_printer/circle_label_renderer.py
from PIL import Image, ImageDraw, ImageFont

# 示例：绘制 DM 码标签
img = Image.new('RGB', (size_px, size_px), color='white')
draw = ImageDraw.Draw(img)
draw.rectangle([...], outline='black', width=2)
```

---

#### pylibdmtx - DM 码编码库

```
名称: pylibdmtx
版本: ≥0.1.9（最低版本）
官方网站: https://github.com/NaturalHistoryMuseum/pylibdmtx
用途:
  - 编码字符串为 DM 码（Data Matrix）二维码
  - 生成 DM 码矩阵数据供 Pillow 绘制
  - 支持各种编码格式和大小
获取方式: pip install pylibdmtx
License: MIT
安装位置: .venv\Lib\site-packages\pylibdmtx\
依赖库: libdmtx-64.dll（原生 C DLL，随 pylibdmtx 安装）
系统要求: 
  - Windows 64-bit
  - Microsoft Visual C++ 2013 Redistributable (x64) 必须
  - 参考环境搭建文档第 12.4 节
```

**关键模块**：

- `pylibdmtx.pylibdmtx.encode` - DM 码编码函数

**原生 DLL 路径**：

```
.venv\Lib\site-packages\pylibdmtx\libdmtx-64.dll
```

**项目使用**：

```python
# 位置: dm_printer/label_renderer.py
from pylibdmtx.pylibdmtx import encode as dm_encode

# 编码 DM 码
encoded = dm_encode(code_value.encode('utf-8'))
# 返回: Encoded(width, height, matrix_data)
```

**常见问题处理**：

- 若提示找不到 `libdmtx-64.dll`，需要安装 Visual C++ 2013 Redistributable
- 详见环境搭建文档第 12.4 节

---

#### pywin32 - Windows API

```
名称: pywin32
版本: ≥306（最低版本）
官方网站: https://github.com/pywin32/pywin32
用途:
  - 调用 Windows API 进行系统操作
  - 与打印机驱动通信
  - 进程间通信 (IPC)
获取方式: pip install pywin32
License: PSF（Python Software Foundation）
安装位置: .venv\Lib\site-packages\win32\
系统要求: Windows 系统（不支持 Linux/Mac）
平台特定: 仅在 requirements.txt 中指定 sys_platform == "win32"
```

**项目使用**：

```python
# 位置: dm_printer/local_socket_client.py
# 使用 Windows IPC 进行进程间通信
# 用于单例程序控制和状态通知
```

---

#### setuptools - Python 打包工具

```
名称: setuptools
版本: ≥65.0（推荐）
官方网站: https://setuptools.pypa.io/
用途:
  - 为 Python 3.12+ 提供 distutils 兼容层
  - 解决 pylibdmtx 依赖 distutils 的问题
  - 项目打包和分发
获取方式: pip install setuptools
License: MIT
安装位置: .venv\Lib\site-packages\setuptools\
系统要求: Python 3.10+
特殊注意:
  - Python 3.12 中 distutils 被完全移除
  - setuptools 提供兼容性包装
  - 必须在安装 requirements.txt 前安装
```

**项目使用**：

```powershell
# 正确的安装顺序
pip install setuptools              # 先装这个
pip install -r requirements.txt     # 再装其他依赖
```

---

### 2.3 依赖版本锁定说明

**为何 PySide6 固定版本？**

```
PySide6==6.8.2.1 (固定)
```

- PySide6 与 Qt 版本必须精确匹配
- 不同版本之间 API 可能不兼容
- QML 文件格式在版本间可能差异
- 打包时需要特定版本的 Qt 库集成

**为何其他库使用浮动版本？**

```
Pillow>=10.0.0    (≥ 表示向后兼容)
pylibdmtx>=0.1.9  (≥ 表示向后兼容)
pywin32>=306      (≥ 表示向后兼容)
```

- 这些库维护良好的向后兼容性
- 允许自动安装安全补丁和新版本
- 减少依赖版本冲突的风险

## 3. 依赖项目结构和导入路径

### 3.1 项目代码中的导入

```python
# main.py - 主入口
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

# dm_printer/backend.py - 后端业务逻辑
from dm_printer.label_renderer import render_label, CODES_PER_LABEL
from dm_printer.code_generator import generate_range_codes
from dm_printer.zpl_generator import generate_zpl
from dm_printer.printer_backend import get_available_printers, send_zpl

# dm_printer/label_renderer.py - 标签生成
from PIL import Image, ImageDraw, ImageFont
from pylibdmtx.pylibdmtx import encode as dm_encode

# dm_printer/local_socket_client.py - IPC 通信
from win32file import CreateFile, ReadFile, WriteFile  # pywin32
```

### 3.2 第三方库的内部结构示例

**PySide6 目录结构**：

```
PySide6/
├── __init__.py
├── QtCore.pyd          # C++ 扩展模块
├── QtGui.pyd
├── QtQml.pyd
├── QtQuickControls2.pyd
├── bin/                # 可执行文件和 DLL
│   ├── Qt6Core.dll
│   ├── Qt6Gui.dll
│   ├── Qt6Qml.dll
│   └── ...
└── ...
```

**Pillow 目录结构**：

```
PIL/
├── __init__.py
├── Image.py            # 图像处理模块
├── ImageDraw.py        # 绘制工具
├── ImageFont.py        # 字体处理
├── _imaging.pyd        # C 扩展
└── ...
```

**pylibdmtx 目录结构**：

```
pylibdmtx/
├── __init__.py
├── pylibdmtx.py        # 主模块
├── wrapper.py          # C 库包装
├── libdmtx-64.dll      # 原生 DLL（关键文件）
└── dmtx_library.py     # DLL 加载器
```

## 4. 依赖管理最佳实践

### 4.1 更新依赖

```powershell
# 升级单个库
pip install --upgrade Pillow

# 升级所有库（谨慎操作）
pip install --upgrade -r requirements.txt

# 查看可升级的包
pip list --outdated
```

### 4.2 冻结当前环境

生成确切版本的依赖列表：

```powershell
pip freeze > requirements_frozen.txt
```

输出示例：

```
PySide6==6.8.2.1
Pillow==10.2.0
pylibdmtx==0.1.10
pywin32==306
setuptools==68.0.0
```

### 4.3 卸载依赖

```powershell
# 卸载单个库
pip uninstall Pillow

# 卸载所有依赖
pip uninstall -r requirements.txt -y
```

## 5. 故障排除

### 常见问题与解决方案


| 问题                                               | 症状             | 解决方案                                        |
| ------------------------------------------------ | -------------- | ------------------------------------------- |
| `ModuleNotFoundError: No module named 'PySide6'` | 导入 PySide6 失败  | 激活虚拟环境，运行 `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'PIL'`     | Pillow 未安装     | 运行 `pip install Pillow`                     |
| `FileNotFoundError: libdmtx-64.dll`              | pylibdmtx 加载失败 | 安装 Visual C++ 2013 Redistributable，参考环境搭建文档 |
| `ModuleNotFoundError: distutils`                 | 仅 Python 3.12  | 运行 `pip install setuptools`                 |
| `Module not found in site-packages`              | 虚拟环境不匹配        | 确保使用正确的虚拟环境解释器                              |


### 验证依赖安装

```powershell
# 激活虚拟环境后执行
python -c "import PySide6; print('PySide6:', PySide6.__version__)"
python -c "import PIL; print('Pillow:', PIL.__version__)"
python -c "import pylibdmtx; print('pylibdmtx 已安装')"
python -c "import win32file; print('pywin32 已安装')" # Windows only
```

## 6. 依赖版本历史

### 6.1 当前版本（v2.0）


| 库          | 版本      | 更新日期    | 备注             |
| ---------- | ------- | ------- | -------------- |
| PySide6    | 6.8.2.1 | 2024-Q4 | 最新稳定版          |
| Pillow     | 10.2.0+ | 滚动更新    | 支持 Python 3.12 |
| pylibdmtx  | 0.1.9+  | 滚动更新    | Windows DLL 支持 |
| pywin32    | 306+    | 滚动更新    | IPC 支持         |
| setuptools | 68.0+   | 滚动更新    | distutils 兼容性  |


### 6.2 版本升级考虑

升级依赖前应考虑：

- ✓ 测试 QML 兼容性（PySide6 升级时）
- ✓ 验证图像生成效果（Pillow 升级时）
- ✓ 确保 DM 码编码正确（pylibdmtx 升级时）
- ✓ 通过完整的打印流程测试

## 7. 外部资源链接


| 资源               | 链接                                                                                                     |
| ---------------- | ------------------------------------------------------------------------------------------------------ |
| PySide6 官方文档     | [https://doc.qt.io/qtforpython/](https://doc.qt.io/qtforpython/)                                       |
| Pillow 文档        | [https://pillow.readthedocs.io/](https://pillow.readthedocs.io/)                                       |
| pylibdmtx GitHub | [https://github.com/NaturalHistoryMuseum/pylibdmtx](https://github.com/NaturalHistoryMuseum/pylibdmtx) |
| pywin32 文档       | [https://github.com/pywin32/pywin32](https://github.com/pywin32/pywin32)                               |
| PyPI 官方源         | [https://pypi.org/](https://pypi.org/)                                                                 |


---

**最后更新**：2026 年 4 月  
**相关文档**：[环境搭建说明](./env_setup.md) | [软件简介](./readme_overview.md)