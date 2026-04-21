# DM 码打印工具 - 项目架构说明

## 1. 项目概述

DM 码打印工具是一个分层的 Python 桌面应用，采用经典的**分层架构**设计，将关注点分离到不同的模块中，便于维护、测试和扩展。

### 1.1 架构特点

- **分层设计**：严格分离 UI 层、业务逻辑层、通信层、硬件层
- **单一职责**：每个模块只负责一个明确的任务
- **低耦合**：模块之间通过明确的接口通信
- **易于测试**：业务逻辑独立于 UI，便于单元测试
- **易于扩展**：添加新功能或支持新硬件时改动最小

## 2. 整体架构

### 2.1 四层架构模型

```
┌─────────────────────────────────────────────────────┐
│              UI 表现层 (Presentation)               │
│  main.qml (QML) / main.py (应用入口)                 │
│  - 用户交互界面                                      │
│  - 按钮、输入框、预览显示                             │
└──────────────────┬──────────────────────────────────┘
                   │ 信号/槽机制
┌──────────────────▼──────────────────────────────────┐
│            业务逻辑层 (Business Logic)               │
│  Backend 后端类 / 各种生成器                          │
│  - 码号生成、标签渲染、ZPL 生成                       │
│  - 打印机选择、进度控制                              │
│  - 状态管理和错误处理                                │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐    ┌───────▼──────────┐
│ 硬件驱动层      │    │ 通信抽象层       │
│                │    │                  │
│ • Zebra 打印机 │    │ • IPC 通信       │
│   (win32print) │    │ • 进程通信       │
│                │    │                  │
└────────────────┘    └──────────────────┘
```

### 2.2 分层说明

| 分层 | 模块 | 职责 | 技术栈 |
|-----|------|------|--------|
| **UI 层** | main.qml / main.py | 用户界面、交互、事件处理 | QML / PySide6 |
| **业务逻辑层** | Backend 和各生成器 | 数据处理、算法、业务规则 | Python / Pillow / pylibdmtx |
| **硬件驱动层** | printer_backend.py | 硬件通信、打印机操作 | pywin32 / win32print |
| **通信层** | local_socket_client.py | 进程间通信、消息协议 | PySide6 QLocalSocket |

## 3. 详细模块划分

### 3.1 项目目录结构

```
dm_tool/
├── main.py                          ┌─ UI 层入口
├── main.qml                         ├─ QML 界面定义
│
├── dm_printer/                      ┌─ 业务逻辑包
│   ├── __init__.py                  │
│   ├── __main__.py                  ├─ 模块入口
│   │
│   ├── backend.py                   ├─ 核心业务逻辑（后端桥接）
│   ├── code_generator.py            ├─ 码号生成算法
│   ├── label_renderer.py            ├─ 标签渲染（4×4 矩阵）
│   ├── circle_label_renderer.py     ├─ 标签渲染（圆形）
│   ├── zpl_generator.py             ├─ ZPL 指令生成
│   │
│   ├── printer_backend.py           ├─ 硬件驱动层
│   └── local_socket_client.py       └─ 通信层
│
├── docs/                            ┌─ 文档
│   ├── env_setup.md                 ├─ 环境搭建
│   ├── dependencies.md              ├─ 依赖说明
│   ├── readme_overview.md           ├─ 软件简介
│   ├── architecture.md              └─ 架构说明
│
├── requirements.txt                 ┌─ 项目依赖
├── pyproject.toml                   └─ 项目配置
└── DMCodePrinter.spec               └─ PyInstaller 打包配置
```

### 3.2 核心模块详解

#### **UI 层**

**main.py** - 应用入口
```
职责：
  ✓ 初始化 PySide6 应用
  ✓ 加载 QML 文件
  ✓ 连接后端和 UI
  ✓ 启动 IPC 客户端

关键类：
  - QGuiApplication: Qt 应用程序
  - QQmlApplicationEngine: QML 引擎
  - Backend: 后端业务逻辑桥接（导出给 QML）
  - LocalSocketClient: IPC 通信客户端

典型代码流程：
  main() → QGuiApplication() → 加载 main.qml → 
  设置 Backend() → 启动 IPC 客户端 → 进入事件循环
```

**main.qml** - 用户界面
```
结构：
  ApplicationWindow
    ├── ColumnLayout (左面板)
    │   ├── 模板选择 (4×4 / 圆码)
    │   ├── 码值范围输入
    │   ├── 生成预览按钮
    │   ├── 打印机选择
    │   └── 打印/导出按钮
    │
    └── ColumnLayout (右面板)
        ├── 标签预览滚动区域
        └── 状态信息显示

UI 交互：
  用户输入 → 信号发射 → Backend 处理 → 属性变化 → UI 自动更新
```

---

#### **业务逻辑层**

**backend.py** - 后端桥接（核心类）
```
类：Backend (QObject)

属性（Property）：
  - codeStart: 起始码值
  - codeEnd: 结束码值
  - template: 打印模板 ("4x4" / "circle")
  - previewImageUrls: 预览图像 URL 列表
  - printerList: 可用打印机列表
  - status: 状态信息

方法（Slot）：
  - generatePreview(): 生成标签预览
  - printLabels(printer_name): 打印标签
  - saveZpl(printer_name, save_path): 导出 ZPL
  - refreshPrinters(): 刷新打印机列表
  - setExternalStatus(msg): 接收外部状态

信号（Signal）：
  - codeStartChanged
  - codeEndChanged
  - previewImageUrlsChanged
  - statusChanged
  - printerListChanged
  - templateChanged

核心流程：
  1. 接收 UI 输入（码值范围、模板选择）
  2. 验证输入参数
  3. 调用各生成器模块
  4. 生成预览或发送打印
  5. 更新 UI 状态
```

**code_generator.py** - 码号生成
```
函数：
  - generate_range_codes(start, end) -> list[str]
    生成范围内的所有码值
    例如: start="1", end="10" → ["1","2",...,"10"]
  
  - generate_batch_codes(start_code, count) -> list[str]
    生成批量码值
    例如: start="100", count=3 → ["100","101","102"]
  
  - generate_big_codes(start, count) -> list[str]
    生成大码（8位补零）
    例如: start=90001, count=2 → ["00090001","00090002"]
  
  - generate_small_codes(x_start, y_start, ...) -> list[str]
    生成小码（XY 坐标格式）
    例如: x=100, y=200 → ["XY0010000200A"]

规则：
  ✓ 输入为字符串，自动识别格式
  ✓ 自动处理数值转换和范围检查
  ✓ 返回字符串列表便于 UI 显示和后续处理
```

**label_renderer.py** - 标签渲染（4×4 矩阵）
```
函数：
  - render_label(code: str, output_path: str) -> None
    渲染单个标签为 PNG 图像
    
参数说明：
  - code: 要编码的码值（字符串）
  - output_path: 输出 PNG 文件的完整路径

处理流程：
  1. 使用 pylibdmtx.encode() 编码 DM 码
  2. 创建 100×100mm 空白标签画布（Pillow Image）
  3. 绘制虚线边框（85×85 mm）
  4. 绘制坐标轴（中心十字）
  5. 绘制 4×4 网格（每格一个 DM 码）
  6. 绘制码值文字标签
  7. 保存为 PNG

模板参数：
  - 标签尺寸: 100×100 mm
  - DPI: 203 (Zebra 标准)
  - DM 码模块: 12×12
  - 排版: 4×4 网格 (16 个码/标签)

常量：
  CODES_PER_LABEL = 16  # 每张标签的码数
```

**circle_label_renderer.py** - 标签渲染（圆形）
```
职责：
  与 label_renderer.py 类似，但采用圆形排列

函数：
  - render_circle_label(code: str, output_path: str) -> None

排版：
  - 圆形布局，6 个码/标签
  - DM 码围绕中心排列

常量：
  CODES_PER_LABEL = 6  # 每张标签的码数
```

**zpl_generator.py** - ZPL 指令生成
```
函数：
  - generate_zpl(code: str) -> list[str]
    生成 4×4 矩阵的 ZPL 指令
    返回值是字符串列表（每个 ZPL 是一条完整指令）
  
  - generate_circle_zpl(code: str) -> list[str]
    生成圆形的 ZPL 指令
    返回值是字符串列表

ZPL 指令组成：
  1. 标记初始化: ^XA
  2. 标签尺寸: ^LL...^PW...
  3. 图形数据: ^GFA...（编码后的 DM 码位图）
  4. 文字: ^FD...^FS
  5. 标记结束: ^XZ

核心流程：
  1. 使用 Pillow 渲染标签为图像
  2. 使用 _image_to_gfa() 将图像编码为 ZPL GFA 格式
  3. 组装完整的 ZPL 指令字符串
  4. 返回格式化的 ZPL 指令

参数表：
  DPI = 203              # Zebra 打印机标准 DPI
  LABEL_SIZE_MM = 100    # 标签尺寸 100×100 mm
  MODULE_DOTS = 10       # 每个模块的点数
  MATRIX_MODULES = 12    # DM 码大小 12×12 模块
```

---

#### **硬件驱动层**

**printer_backend.py** - 打印机驱动
```
函数：
  - get_available_printers() -> list[str]
    获取系统中所有可用的 Zebra 打印机
    
    Windows: 使用 win32print 枚举打印机
    其他: 返回模拟打印机列表（调试用）
  
  - get_default_printer() -> Optional[str]
    获取系统默认打印机
  
  - send_zpl(zpl: str, printer_name: str, save_dir: Optional[str]) -> str
    将 ZPL 指令发送到打印机或保存为文件
    
    参数：
      - zpl: 完整的 ZPL 指令字符串
      - printer_name: 目标打印机名称
      - save_dir: (可选) 同时保存 .zpl 文件的目录
    
    返回值：
      - 成功: "打印成功"
      - 失败: 错误描述字符串

实现细节：
  - Windows 下使用 win32print.OpenPrinter() 打开打印机
  - 使用 RAW 模式发送 ZPL 指令
  - 自动处理编码、错误异常
  - 非 Windows 系统回退为文件保存

过滤规则：
  识别 Zebra 打印机的条件：
    ✓ 驱动名含 "Zebra"
    ✓ 驱动名含 "ZDesigner"
    ✓ 驱动名含 ZPL 且含机型前缀 (ZD/ZT/GK/GX/ZQ/ZM)
```

---

#### **通信层**

**local_socket_client.py** - IPC 通信
```
类：LocalSocketClient (QObject)

职责：
  - 与主 IPC 服务器通信
  - 发送 HELLO 消息（进程注册）
  - 定期发送 HEARTBEAT（心跳）
  - 接收和处理 COMMAND（外部命令）

信号：
  - status_message(str): 状态消息信号（连接 Backend 的状态栏）
  - graceful_shutdown_requested: 请求优雅关闭

消息协议：
  - HELLO_TYPE (0): 首次连接，发送进程信息
  - HEARTBEAT_TYPE (2): 心跳信号
  - HEARTBEAT_ACK_TYPE (3): 心跳应答
  - COMMAND_TYPE (5): 接收外部命令

核心机制：
  1. 创建 QLocalSocket 连接
  2. 定期发送心跳信号
  3. 监听进程间消息
  4. 接收外部命令（如关闭、状态查询等）
  5. 通过信号触发相应的 Backend 操作

配置：
  IPC_SERVER_NAME = "master_ipc_server"     # 服务器名称
  RECONNECT_INTERVAL_MS = 5000              # 重连间隔 5 秒
  HEARTBEAT_INTERVAL_MS = 10000             # 心跳间隔 10 秒
```

## 4. 模块依赖关系

### 4.1 依赖关系图

```
main.py (入口)
    │
    ├─→ PySide6 (GUI 框架)
    │   └─→ main.qml (UI 定义)
    │
    └─→ Backend (业务逻辑核心)
        │
        ├─→ code_generator (码号生成)
        │
        ├─→ label_renderer (标签渲染)
        │   │
        │   ├─→ PIL/Pillow (图像处理)
        │   └─→ pylibdmtx (DM 码编码)
        │
        ├─→ circle_label_renderer (圆形标签)
        │   │
        │   ├─→ PIL/Pillow
        │   └─→ pylibdmtx
        │
        ├─→ zpl_generator (ZPL 生成)
        │   └─→ PIL/Pillow
        │
        ├─→ printer_backend (硬件驱动)
        │   └─→ pywin32 (Windows API)
        │
        └─→ LocalSocketClient (IPC 通信)
            └─→ PySide6.QtNetwork (网络模块)
```

### 4.2 数据流向

#### 打印预览流程

```
用户输入码值范围
  │
  ▼
Backend.generatePreview()
  │
  ├─→ code_generator.generate_range_codes()
  │   返回: ["1", "2", ..., "10"]
  │
  ├─→ 遍历码值列表（最多 10 个）
  │   │
  │   ├─→ label_renderer.render_label() 或
  │   │   circle_label_renderer.render_circle_label()
  │   │   返回: PNG 文件路径
  │   │
  │   └─→ 收集所有 PNG 路径
  │
  ├─→ Backend.previewImageUrls = [url1, url2, ...]
  │   发射: previewImageUrlsChanged 信号
  │
  └─→ QML 接收信号，自动更新预览显示
      显示: 预览缩略图网格
```

#### 打印流程

```
用户选择打印机并点击"打印"
  │
  ▼
Backend.printLabels(printer_name)
  │
  ├─→ code_generator.generate_range_codes()
  │   返回码值列表
  │
  ├─→ 遍历每个码值
  │   │
  │   ├─→ zpl_generator.generate_zpl()
  │   │   返回: ZPL 指令字符串列表
  │   │
  │   └─→ 对每条 ZPL 指令
  │       │
  │       ├─→ printer_backend.send_zpl(zpl, printer_name)
  │       │   返回: "打印成功" 或错误信息
  │       │
  │       └─→ Backend._set_status() 更新状态
  │           发射: statusChanged 信号
  │
  └─→ QML 接收信号，显示打印进度
      显示: "正在打印 5/100"
```

#### ZPL 导出流程

```
用户选择导出位置并点击"导出 ZPL"
  │
  ▼
Backend.saveZpl(printer_name, save_path)
  │
  ├─→ code_generator.generate_range_codes()
  │   返回码值列表
  │
  ├─→ 遍历每个码值
  │   │
  │   └─→ zpl_generator.generate_zpl()
  │       收集所有 ZPL 指令
  │
  ├─→ 将所有 ZPL 指令写入文件 (以 \n\n 分隔)
  │
  └─→ Backend._set_status()
      发射: statusChanged 信号
      显示: "ZPL 已保存到 C:\...\dm_labels.zpl"
```

---

**文档更新日期**：2026 年 4 月  
**相关文档**：[环境搭建](./env_setup.md) | [依赖说明](./dependencies.md) | [软件简介](./readme_overview.md)
