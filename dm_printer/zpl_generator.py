"""ZPL 指令生成器：将码值转换为 Zebra ZPL-II 打印流.

技术参数（与 BarTender 模板一致）：
- 符号类型：Data Matrix ECC200
- 模块尺寸：10 dots（≈1.25 mm @203 DPI）
- 标签尺寸：100×100 mm（≈800×800 dots @203 DPI）
- 排版网格：4×4（每张标签 16 个相同码）
- 虚线边框：85×85 mm, 居中
- XY 轴：贯穿中心, 两端箭头
"""

from __future__ import annotations

import math
import os
import tempfile

from PIL import Image

DPI = 203
LABEL_SIZE_MM = 100.0
MODULE_DOTS = 10
MATRIX_MODULES = 12
PRINT_OFFSET_X_MM = 4.0
PRINT_OFFSET_Y_MM = 0.0
BORDER_X_MM = 7.5
BORDER_Y_MM = 7.5
BORDER_W_MM = 85.0
BORDER_H_MM = 85.0
BORDER_LINE_DOTS = 1
BORDER_DASH_MM = 1.0
BORDER_GAP_MM = 1.0

AXIS_START_MM = 1.0
AXIS_END_MM = 99.0
AXIS_CENTER_MM = 50.0
AXIS_LINE_DOTS = 2

ARROW_LENGTH_MM = 4.0
ARROW_WIDTH_MM = 2.8
HOLLOW_ARROW_LINE_DOTS = 1

X_TEXT_MM = (97.0, 46.0)       # 右下锚点
Y_TEXT_MM = (47.0, 6.0)        # 右下锚点
CODE_TEXT_MM = (75.8, 6.0)     # 底部居中锚点
TEXT_HEIGHT_DOTS = 34          # 约 12pt @203DPI

POSITIONS_MM: list[tuple[float, float]] = [
    (20, 20), (40, 20), (60, 20), (80, 20),
    (20, 40), (40, 40), (60, 40), (80, 40),
    (20, 60), (40, 60), (60, 60), (80, 60),
    (20, 80), (40, 80), (60, 80), (80, 80),
]

CODES_PER_LABEL = len(POSITIONS_MM)


def mm_to_dots(mm: float) -> int:
    """毫米 → 打印点数，按整张标签点阵同比换算。"""
    return round(mm / LABEL_SIZE_MM * label_size_dots())


def label_size_dots() -> int:
    """返回整张标签的点阵边长。"""
    return math.ceil(LABEL_SIZE_MM * DPI / 25.4)


def _image_to_gfa(image: Image.Image) -> tuple[int, int, int, str]:
    """将黑白图片编码为 ZPL ^GFA 所需的十六进制数据."""
    mono = image.convert("L")
    width, height = mono.size
    bytes_per_row = (width + 7) // 8
    pixels = mono.load()
    raw = bytearray()

    for y in range(height):
        for byte_idx in range(bytes_per_row):
            value = 0
            for bit in range(8):
                x = byte_idx * 8 + bit
                if x >= width:
                    continue
                if pixels[x, y] < 128:
                    value |= 1 << (7 - bit)
            raw.append(value)

    total_bytes = len(raw)
    return total_bytes, total_bytes, bytes_per_row, raw.hex().upper()


def _add_hline(parts: list[str], x: int, y: int, w: int, t: int) -> None:
    if w <= 0:
        return
    parts.append(f"^FO{x},{y}^GB{w},{max(1, t)},{max(1, t)},B,0^FS")


def _add_vline(parts: list[str], x: int, y: int, h: int, t: int) -> None:
    if h <= 0:
        return
    parts.append(f"^FO{x},{y}^GB{max(1, t)},{h},{max(1, t)},B,0^FS")


def _add_dashed_hline(
    parts: list[str],
    x1: int,
    x2: int,
    y: int,
    dash: int,
    gap: int,
    t: int,
) -> None:
    cur = x1
    while cur <= x2:
        end = min(cur + dash - 1, x2)
        _add_hline(parts, cur, y, end - cur + 1, t)
        cur = end + 1 + gap


def _add_dashed_vline(
    parts: list[str],
    x: int,
    y1: int,
    y2: int,
    dash: int,
    gap: int,
    t: int,
) -> None:
    cur = y1
    while cur <= y2:
        end = min(cur + dash - 1, y2)
        _add_vline(parts, x, cur, end - cur + 1, t)
        cur = end + 1 + gap


def _add_filled_arrow(
    parts: list[str],
    tip_x: int,
    tip_y: int,
    direction: str,
    arrow_len: int,
    arrow_half_w: int,
) -> None:
    # 用多条 1-dot 线段填充三角形箭头
    if direction in ("right", "left"):
        for dy in range(-arrow_half_w, arrow_half_w + 1):
            span = int((1.0 - abs(dy) / max(1, arrow_half_w)) * arrow_len)
            if span <= 0:
                continue
            if direction == "right":
                _add_hline(parts, tip_x - span + 1, tip_y + dy, span, 1)
            else:
                _add_hline(parts, tip_x, tip_y + dy, span, 1)
    else:
        for dx in range(-arrow_half_w, arrow_half_w + 1):
            span = int((1.0 - abs(dx) / max(1, arrow_half_w)) * arrow_len)
            if span <= 0:
                continue
            if direction == "up":
                _add_vline(parts, tip_x + dx, tip_y - span + 1, span, 1)
            else:
                _add_vline(parts, tip_x + dx, tip_y, span, 1)


def _add_hollow_arrow(
    parts: list[str],
    tip_x: int,
    tip_y: int,
    direction: str,
    arrow_len: int,
    arrow_half_w: int,
    t: int,
) -> None:
    # 空心箭头：使用确定方向的三条边，避免镜像/反向
    if direction == "right":
        base_x = tip_x - arrow_len
        _add_hline(parts, base_x, tip_y - arrow_half_w, arrow_len, t)
        parts.append(
            f"^FO{base_x},{tip_y - arrow_half_w}"
            f"^GD{arrow_len},{arrow_half_w + 1},{max(1, t)},B,R^FS"
        )
        parts.append(
            f"^FO{base_x},{tip_y}"
            f"^GD{arrow_len},{arrow_half_w + 1},{max(1, t)},B,N^FS"
        )
    elif direction == "left":
        base_x = tip_x + arrow_len
        _add_hline(parts, tip_x, tip_y - arrow_half_w, arrow_len, t)
        parts.append(
            f"^FO{tip_x},{tip_y - arrow_half_w}"
            f"^GD{arrow_len},{arrow_half_w + 1},{max(1, t)},B,N^FS"
        )
        parts.append(
            f"^FO{tip_x},{tip_y}"
            f"^GD{arrow_len},{arrow_half_w + 1},{max(1, t)},B,R^FS"
        )
    elif direction == "up":
        base_y = tip_y + arrow_len
        _add_vline(parts, tip_x - arrow_half_w, tip_y, arrow_len, t)
        parts.append(
            f"^FO{tip_x - arrow_half_w},{tip_y}"
            f"^GD{arrow_half_w + 1},{arrow_len},{max(1, t)},B,R^FS"
        )
        parts.append(
            f"^FO{tip_x},{tip_y}"
            f"^GD{arrow_half_w + 1},{arrow_len},{max(1, t)},B,N^FS"
        )
    else:  # down
        base_y = tip_y - arrow_len
        _add_vline(parts, tip_x - arrow_half_w, base_y, arrow_len, t)
        parts.append(
            f"^FO{tip_x - arrow_half_w},{base_y}"
            f"^GD{arrow_half_w + 1},{arrow_len},{max(1, t)},B,N^FS"
        )
        parts.append(
            f"^FO{tip_x},{base_y}"
            f"^GD{arrow_half_w + 1},{arrow_len},{max(1, t)},B,R^FS"
        )


def _build_label_zpl(
    code_value: str,
    flip_y: bool = False,
    center_offset: bool = True,
) -> str:
    """为一张标签生成完整 ZPL 指令."""
    del flip_y

    from dm_printer.label_renderer import render_label

    label_dots = label_size_dots()
    fd, image_path = tempfile.mkstemp(suffix=".png", prefix="dm_label_print_")
    os.close(fd)

    try:
        # 打印时直接按打印机点阵渲染，避免预览图缩放导致中心漂移。
        render_label(code_value, image_path, render_scale=1)
        with Image.open(image_path) as image:
            image_width, image_height = image.size
            origin_x = 0
            origin_y = 0
            if center_offset:
                origin_x = max(0, (label_dots - image_width) // 2)
                origin_y = max(0, (label_dots - image_height) // 2)
            origin_x += mm_to_dots(PRINT_OFFSET_X_MM)
            origin_y += mm_to_dots(PRINT_OFFSET_Y_MM)
            total, used, bytes_per_row, hex_data = _image_to_gfa(image)
    finally:
        try:
            os.remove(image_path)
        except OSError:
            pass

    parts = [
        "^XA",
        "^CI28",
        "^MMT",
        "^MTT",
        "^MNY",
        "^FWN",
        "^PON",
        "^LT0",
        "^LS0",
        f"^PW{label_dots}",
        f"^LL{label_dots}",
        "^LH0,0",
        "^XB",
        f"^FO{origin_x},{origin_y}"
        f"^GFA,{total},{used},{bytes_per_row},{hex_data}^FS",
        "^PQ1,0,1,N",
        "^XZ",
    ]
    return "\n".join(parts)


def generate_zpl(
    code_value: str,
    flip_y: bool = False,
    center_offset: bool = True,
) -> list[str]:
    """为单个码值生成 ZPL（一张标签 = 16 个相同码）.

    Args:
        code_value:    DM 码内容
        flip_y:        是否翻转 Y 轴
        center_offset: 是否偏移使码居中

    Returns:
        包含一条 ZPL 指令的列表
    """
    if not code_value:
        return []
    return [_build_label_zpl(code_value, flip_y, center_offset)]


# ── 圆码模版 (80×60 mm) ──

CIRCLE_LABEL_W_MM = 80.0
CIRCLE_LABEL_H_MM = 60.0
CIRCLE_PRINT_OFFSET_X_MM = 0.0
CIRCLE_PRINT_OFFSET_Y_MM = 0.0


def _circle_label_w_dots() -> int:
    return math.ceil(CIRCLE_LABEL_W_MM * DPI / 25.4)


def _circle_label_h_dots() -> int:
    return math.ceil(CIRCLE_LABEL_H_MM * DPI / 25.4)


def _build_circle_label_zpl(code_value: str) -> str:
    """为一张圆码标签生成完整 ZPL 指令."""
    from dm_printer.circle_label_renderer import render_circle_label

    w_dots = _circle_label_w_dots()
    h_dots = _circle_label_h_dots()
    fd, image_path = tempfile.mkstemp(
        suffix=".png", prefix="dm_circle_print_"
    )
    os.close(fd)

    try:
        render_circle_label(code_value, image_path, render_scale=1)
        with Image.open(image_path) as image:
            total, used, bytes_per_row, hex_data = _image_to_gfa(image)
    finally:
        try:
            os.remove(image_path)
        except OSError:
            pass

    offset_x = round(CIRCLE_PRINT_OFFSET_X_MM / CIRCLE_LABEL_W_MM * w_dots)
    offset_y = round(CIRCLE_PRINT_OFFSET_Y_MM / CIRCLE_LABEL_H_MM * h_dots)

    parts = [
        "^XA",
        "^CI28",
        "^MMT",
        "^MTT",
        "^MNY",
        "^FWN",
        "^PON",
        "^LT0",
        "^LS0",
        f"^PW{w_dots}",
        f"^LL{h_dots}",
        "^LH0,0",
        f"^FO{offset_x},{offset_y}"
        f"^GFA,{total},{used},{bytes_per_row},{hex_data}^FS",
        "^PQ1,0,1,N",
        "^XZ",
    ]
    return "\n".join(parts)


def generate_circle_zpl(code_value: str) -> list[str]:
    """为单个码值生成圆码模版 ZPL（一张标签 = 1 个码）.

    Args:
        code_value: DM 码内容

    Returns:
        包含一条 ZPL 指令的列表
    """
    if not code_value:
        return []
    return [_build_circle_label_zpl(code_value)]
