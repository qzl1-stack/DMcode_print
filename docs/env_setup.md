# 环境搭建说明

## 1. 项目简介

本项目是一个基于 `Python + PySide6 + QML` 的桌面应用，用于
DM 码标签打印。

项目主入口如下：

- `main.py`
- `main.qml`

当前项目依赖声明位于 `requirements.txt` 与 `pyproject.toml`。

## 2. 开发环境要求

建议在 Windows 环境下开发和运行。

推荐环境如下：

- 操作系统：`Windows 10` / `Windows 11`
- Python：`3.10` 及以上，推荐 `3.12.4`
- Qt for Python：`PySide6 6.8.2.1`
- Qt 版本：与 `PySide6 6.8.2.1` 对应的 `Qt 6.8.x`
- 包管理工具：`pip`
- 虚拟环境工具：`venv`
- 打包工具：`PyInstaller`

说明：

1. 项目运行依赖的是 `PySide6`，因此通常不需要单独手工编译 Qt。
2. 如果使用 `Qt Creator` 调试 Python 项目，建议选择
   `Python 3.12.4` 解释器，并为项目创建独立虚拟环境。

## 3. 安装 Python

### 3.1 Windows 系统安装 Python

#### 方式一：官方安装程序（推荐）

1. 访问官方 Python 下载页面：[https://www.python.org/downloads/](https://www.python.org/downloads/)

2. 下载 Python 3.12.4（或更高版本）的 Windows 安装程序

3. 运行下载的安装程序（.exe 文件）

4. **重要**：勾选以下选项：
   - ✓ `Add Python 3.12 to PATH`（这样可以直接在 PowerShell 中使用 `python` 命令）
   - ✓ `Install pip`（安装包管理工具）
   - ✓ `Install tcl/tk and IDLE`（可选，用于 Python 图形开发）

5. 点击 `Install Now` 进行安装

#### 方式二：使用 Conda / Miniconda

如果你已经安装了 Anaconda 或 Miniconda，可以创建指定版本的环境：

```powershell
conda create -n dm_tool python=3.12.4
conda activate dm_tool
```

### 3.2 验证 Python 和 pip 安装

打开 PowerShell 或命令提示符，执行以下命令验证安装：

```powershell
python --version
```

应该显示类似输出：
```
Python 3.12.4
```

验证 pip 版本：

```powershell
pip --version
```

应该显示类似输出：
```
pip 24.x.x from C:\Users\<用户名>\AppData\Local\Programs\Python\Python312\lib\site-packages\pip (python 3.12)
```

### 3.3 升级 pip

安装完 Python 后，建议先升级 pip 到最新版本：

```powershell
python -m pip install --upgrade pip
```

### 3.4 配置 pip（可选）

如果你需要加快 pip 下载速度，可以配置使用国内镜像源。

创建文件 `%APPDATA%\pip\pip.ini`（Windows 用户），或编辑：

```
C:\Users\<用户名>\AppData\Roaming\pip\pip.ini
```

添加以下内容（以阿里云镜像为例）：

```ini
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/
```

其他可用的镜像源：

- 清华大学：`https://pypi.tuna.tsinghua.edu.cn/simple`
- 腾讯云：`https://mirrors.cloud.tencent.com/pypi/simple`
- 官方（默认）：`https://pypi.org/simple/`

### 3.5 常见问题

**问题：提示 `python` 命令不存在**

解决方式：
1. 检查 Python 是否已添加到 PATH 环境变量
2. 重新运行 Python 安装程序，选择 `Repair` 或 `Modify`
3. 勾选 `Add Python to PATH` 并完成修复
4. 重启 PowerShell

**问题：pip 下载速度慢**

解决方式：配置 pip 镜像源（参考 3.4 节）

## 4. 获取项目代码

如果尚未获取项目代码，可先执行：

```powershell
git clone <your-repo-url>
cd D:\Desktop\DMcode_print
```

如果项目代码已经在本地，直接进入项目根目录即可：

```powershell
cd D:\Desktop\DMcode_print
```

## 5. 创建 venv 虚拟环境

推荐在项目根目录创建独立虚拟环境。

### 5.1 使用标准 `.venv`

```powershell
cd D:\Desktop\DMcode_print
python -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 限制脚本执行，可先执行：

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

然后再次激活：

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5.2 使用 Qt Creator 创建的虚拟环境

如果你使用 `Qt Creator` 打开本项目，Qt Creator 也可能自动为项目
创建虚拟环境，例如：

```powershell
D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv
```

该解释器可直接用于运行项目：

```powershell
& "D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe" main.py
```

如果你准备统一团队环境，仍然建议优先使用项目根目录下的 `.venv`。

## 6. 安装依赖

进入项目目录后，先升级 `pip`：

```powershell
python -m pip install --upgrade pip
```

然后安装 `setuptools`（用于 Python 3.12+ 兼容性）：

```powershell
pip install setuptools
```

接着安装项目依赖：

```powershell
pip install -r requirements.txt
```

当前核心依赖包括：

- `PySide6==6.8.2.1`
- `Pillow>=10.0.0`
- `pylibdmtx>=0.1.9`
- `pywin32>=306`（仅 Windows）
- `setuptools`（Python 3.12+ 兼容性要求）

如果你使用的是 Qt Creator 的解释器，也可以显式执行：

```powershell
& "D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe" -m pip install --upgrade pip
& "D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe" -m pip install -r requirements.txt
```

## 7. 检查环境是否安装成功

可以通过以下命令确认 Python 与 PySide6 版本：

```powershell
python --version
python -c "import PySide6; print(PySide6.__version__)"
```

如果使用 Qt Creator 虚拟环境：

```powershell
& "D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe" --version
& "D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe" -c "import PySide6; print(PySide6.__version__)"
```

## 8. 运行项目

### 8.1 使用默认 Python 运行

在激活虚拟环境后，执行：

```powershell
python main.py
```

### 8.2 使用指定解释器运行

根据当前项目的实际使用方式，可直接运行：

```powershell
& "D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe" main.py
```

### 8.3 使用模块方式运行

项目也支持模块方式启动：

```powershell
python -m dm_printer
```

## 9. 使用 pip 增加或更新依赖

新增依赖时，建议在当前虚拟环境中执行：

```powershell
pip install <package-name>
```

如果需要同步依赖清单，请手工更新 `requirements.txt`。

例如安装打包工具：

```powershell
pip install pyinstaller
```

## 10. 项目打包

项目根目录已经提供 `PyInstaller` 规格文件：

```text
DMCodePrinter.spec
```

因此推荐使用 `PyInstaller` 按现有规格进行打包。

### 10.1 安装打包依赖

```powershell
pip install pyinstaller
```

如果使用 Qt Creator 虚拟环境：

```powershell
& "D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe" -m pip install pyinstaller
```

### 10.2 执行打包

在项目根目录执行：

```powershell
pyinstaller --clean --noconfirm DMCodePrinter.spec
```

或者显式指定解释器：

```powershell
& "D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm DMCodePrinter.spec
```

### 10.3 打包输出目录

打包完成后，通常可在以下目录查看产物：

- `build\`
- `dist\DMCodePrinter\`

可执行文件通常位于：

```text
dist\DMCodePrinter\DMCodePrinter.exe
```

### 10.4 重新打包前清理

如果需要重新打包，建议先清理旧产物：

```powershell
Remove-Item -Recurse -Force .\build, .\dist
```

然后重新执行：

```powershell
pyinstaller --clean --noconfirm DMCodePrinter.spec
```

## 11. Qt Creator 使用建议

如果你使用 `Qt Creator` 开发本项目，建议按如下方式配置：

1. 打开项目根目录 `D:\Desktop\DMcode_print`
2. 选择 Python 项目解释器
3. 指向项目虚拟环境解释器，例如：
   `D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe`
4. 运行入口设置为 `main.py`
5. 工作目录设置为项目根目录

这样可以保证 `main.qml` 和 Python 模块都能按照当前目录正确加载。

## 12. 常见问题

### 11.1 `ModuleNotFoundError`

通常是依赖未安装或解释器选错导致。

处理方式：

```powershell
pip install -r requirements.txt
```

并确认实际运行的解释器与安装依赖的解释器是同一个。

### 11.2 QML 无法加载

请确认启动命令是在项目根目录执行，且 `main.qml` 文件存在。

推荐做法：

```powershell
cd D:\Desktop\DMcode_print
python main.py
```

### 11.3 `ModuleNotFoundError: No module named 'distutils'`

这是 Python 3.12+ 的兼容性问题。`distutils` 在 Python 3.12 中被完全移除，但 `pylibdmtx` 仍依赖它。

处理方式：

```powershell
pip install setuptools
```

然后重新安装依赖：

```powershell
pip install -r requirements.txt
```

### 11.4 `FileNotFoundError: Could not find module 'libdmtx-64.dll'`

**问题描述**

运行程序时提示找不到 `libdmtx-64.dll` 或其依赖项。

**根本原因**

`libdmtx-64.dll` 缺少 Microsoft Visual C++ 2013 运行时库的依赖。

**解决方案**

安装 Microsoft Visual C++ 2013 Redistributable（x64）：

1. 访问官方下载页面：[https://www.microsoft.com/en-us/download/details.aspx?id=40784](https://www.microsoft.com/en-us/download/details.aspx?id=40784)

2. 点击 `Download`，勾选 `vcredist_x64.exe`（64 位）并下载

3. 运行安装程序，按提示完成安装

4. 重启电脑（如果安装程序提示需要）

5. 重新运行 `python main.py`

### 11.5 打包后程序启动失败

请优先检查：

1. 是否使用了项目自带的 `DMCodePrinter.spec`
2. 是否已正确安装 `pylibdmtx` 和 `setuptools`
3. 是否已安装 Microsoft Visual C++ 2013 Redistributable
4. 是否在干净环境下重新执行过打包

## 13. 推荐的完整初始化流程

下面给出一个从零开始的最小可执行流程：

```powershell
cd D:\Desktop\DMcode_print
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install setuptools
pip install -r requirements.txt
python main.py
```

如果使用 Qt Creator 的虚拟环境，可执行：

```powershell
& "D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe" -m pip install --upgrade pip
& "D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe" -m pip install setuptools
& "D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe" -m pip install -r requirements.txt
& "D:\Desktop\DMcode_print\.qtcreator\Python_3_12_4venv\Scripts\python.exe" main.py
```
