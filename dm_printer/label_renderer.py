"""标签预览渲染器 — 生成与 BarTender 打印模版完全一致的标签图像.

模版参数（100×100 mm 标签 @203 DPI）：
- 外围虚线边框: 85×85 mm, 0.5 pt, 虚线, 居中于 (50, 50) mm
- X 轴: 水平线, 点1(1,50)→点2(99,50), 1.0 pt
  正方向(右) 实心箭头, 负方向(左) 空心箭头, 大小 6
- Y 轴: 垂直线, 点1(50,99)→点2(50,1), 1.0 pt
  正方向(上) 实心箭头, 负方向(下) 空心箭头, 大小 6
- 码值文字: 右上角
- 16 个相同 DM 码: 4×4 网格, 12×12 模块
"""

from __future__ import annotations

import math
import os
import tempfile
from typing import Optional

from PIL import Image, ImageDraw, ImageFont
from pylibdmtx.pylibdmtx import encode as dm_encode
from dm_printer.zpl_generator import (
    DPI as PRINT_DPI,
    MODULE_DOTS,
    MATRIX_MODULES,
    POSITIONS_MM as PRINT_POSITIONS_MM,
    PRINT_OFFSET_X_MM,
)

LABEL_MM = 100.0
DPI = PRINT_DPI
DEFAULT_RENDER_SCALE = 4

# 虚线框：参考点为左上角 (x,y)，宽高 (w,h)
BORDER_X_MM = 7.5
BORDER_Y_MM = 7.5
BORDER_W_MM = 85.0
BORDER_H_MM = 85.0
BORDER_LINE_PT = 1.0

AXIS_START_MM = 1.0
AXIS_END_MM = 99.0
AXIS_CENTER_MM = 50.0

ARROW_LENGTH_MM = 4.0
ARROW_WIDTH_MM = 2.8
HOLLOW_ARROW_LINE_PT = 1.2
TEXT_SIZE_MULTIPLIER = 3

POSITIONS_MM: list[tuple[float, float]] = list(PRINT_POSITIONS_MM)

CODES_PER_LABEL = len(POSITIONS_MM)

DM_MODULES = MATRIX_MODULES
DM_MODULE_SIZE_MM = MODULE_DOTS * 25.4 / PRINT_DPI
DM_SYMBOL_SCALE = 1.3
DM_SYMBOL_MM = DM_MODULES * DM_MODULE_SIZE_MM * DM_SYMBOL_SCALE


def _label_px(render_scale: int) -> int:
    base_label_px = math.ceil(LABEL_MM / 25.4 * DPI)
    return base_label_px * render_scale


def _mm(mm: float, render_scale: int) -> int:
    return round(mm / LABEL_MM * _label_px(render_scale))


def _pt(pt: float, render_scale: int) -> int:
    return max(1, round(pt / 72.0 * DPI * render_scale))


def _print_safe_x_mm(mm: float, render_scale: int) -> float:
    """打印补偿时，避免右侧元素被位图边界裁剪。"""
    if render_scale == 1 and PRINT_OFFSET_X_MM > 0:
        overflow_mm = max(0.0, mm + PRINT_OFFSET_X_MM - LABEL_MM)
        return mm - overflow_mm
    return mm


def _load_font(size_px: int) -> ImageFont.FreeTypeFont:
    paths = [
        # Windows（优先 Arial）
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\Arial.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size_px)
    return ImageFont.load_default()


def _draw_text_with_anchor(
    draw: ImageDraw.ImageDraw,
    pos: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    anchor: str,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x, y = pos

    if anchor == "right_bottom":
        x -= w
        y -= h
    elif anchor == "bottom_center":
        x -= w // 2
        y -= h
    elif anchor == "left_top":
        pass
    else:
        x -= w
        y -= h

    draw.text((x, y), text, fill=fill, font=font)


def _draw_dashed_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    dash_len: int,
    gap_len: int,
    width: int = 1,
    fill: str = "black",
) -> None:
    x0, y0 = start
    x1, y1 = end
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    while pos < length:
        seg_end = min(pos + dash_len, length)
        sx = int(x0 + ux * pos)
        sy = int(y0 + uy * pos)
        ex = int(x0 + ux * seg_end)
        ey = int(y0 + uy * seg_end)
        draw.line([(sx, sy), (ex, ey)], fill=fill, width=width)
        pos = seg_end + gap_len


def _draw_dashed_rect(
    draw: ImageDraw.ImageDraw,
    bbox: tuple[int, int, int, int],
    dash_len: int,
    gap_len: int,
    width: int,
    fill: str = "black",
) -> None:
    x0, y0, x1, y1 = bbox
    _draw_dashed_line(draw, (x0, y0), (x1, y0), dash_len, gap_len, width, fill)
    _draw_dashed_line(draw, (x1, y0), (x1, y1), dash_len, gap_len, width, fill)
    _draw_dashed_line(draw, (x1, y1), (x0, y1), dash_len, gap_len, width, fill)
    _draw_dashed_line(draw, (x0, y1), (x0, y0), dash_len, gap_len, width, fill)


def _arrow_points(
    tip: tuple[int, int],
    direction: tuple[float, float],
    render_scale: int,
) -> list[tuple[int, int]]:
    """计算箭头三角形的三个顶点."""
    tx, ty = tip
    dx, dy = direction
    length = math.hypot(dx, dy)
    if length == 0:
        return [(tx, ty)] * 3
    ux, uy = dx / length, dy / length
    px, py = -uy, ux

    arrow_len = _mm(ARROW_LENGTH_MM, render_scale)
    arrow_half_w = _mm(ARROW_WIDTH_MM, render_scale) / 2

    bx = tx - ux * arrow_len
    by = ty - uy * arrow_len

    return [
        (tx, ty),
        (int(bx + px * arrow_half_w), int(by + py * arrow_half_w)),
        (int(bx - px * arrow_half_w), int(by - py * arrow_half_w)),
    ]


def _draw_filled_arrow(
    draw: ImageDraw.ImageDraw,
    tip: tuple[int, int],
    direction: tuple[float, float],
    render_scale: int,
) -> None:
    """绘制实心箭头（正半轴方向）."""
    pts = _arrow_points(tip, direction, render_scale)
    draw.polygon(pts, fill="black")


def _draw_hollow_arrow(
    draw: ImageDraw.ImageDraw,
    tip: tuple[int, int],
    direction: tuple[float, float],
    render_scale: int,
    line_width: int = 0,
) -> None:
    """绘制空心箭头（负半轴方向）."""
    if line_width == 0:
        line_width = _pt(1.0, render_scale)
    pts = _arrow_points(tip, direction, render_scale)
    draw.polygon(pts, fill="white", outline="black", width=line_width)


def _render_dm(data: str, target_px: int) -> Image.Image:
    try:
        encoded = dm_encode(data.encode("utf-8"), size=f"{DM_MODULES}x{DM_MODULES}")
    except TypeError:
        encoded = dm_encode(data.encode("utf-8"))
    img = Image.frombytes(
        "RGB", (encoded.width, encoded.height), encoded.pixels
    )
    return img.resize((target_px, target_px), Image.NEAREST)


def render_label(
    code_value: str,
    output_path: Optional[str] = None,
    render_scale: int = DEFAULT_RENDER_SCALE,
) -> str:
    """渲染一张标签预览图.

    Args:
        code_value: DM 码内容（16 个码均为此值）
        output_path: 输出 PNG 路径；为 None 时使用临时文件
        render_scale: 渲染倍率；预览建议 4，打印建议 1

    Returns:
        生成图片的绝对路径
    """
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".png", prefix="dm_label_")
        os.close(fd)

    if render_scale < 1:
        raise ValueError("render_scale 必须大于等于 1")

    label_px = _label_px(render_scale)
    label = Image.new("RGB", (label_px, label_px), "white")
    draw = ImageDraw.Draw(label)

    # ── 虚线边框 ──
    border_x0 = _mm(BORDER_X_MM, render_scale)
    border_y0 = _mm(BORDER_Y_MM, render_scale)
    border_x1 = _mm(BORDER_X_MM + BORDER_W_MM, render_scale)
    border_y1 = _mm(BORDER_Y_MM + BORDER_H_MM, render_scale)

    dash = _mm(1.0, render_scale)
    gap = _mm(1.0, render_scale)
    border_w = _pt(BORDER_LINE_PT, render_scale)
    _draw_dashed_rect(
        draw,
        (border_x0, border_y0, border_x1, border_y1),
        dash, gap, border_w, "black",
    )

    # ── 坐标轴 ──
    axis_w = _pt(1.0, render_scale)
    cx = _mm(AXIS_CENTER_MM, render_scale)
    x_left = _mm(AXIS_START_MM, render_scale)
    x_right = _mm(_print_safe_x_mm(AXIS_END_MM, render_scale), render_scale)
    y_top = _mm(AXIS_START_MM, render_scale)
    y_bottom = _mm(AXIS_END_MM, render_scale)

    # X 轴: 水平线（线段缩进一个箭头长度，避免穿过箭头）
    arrow_len_px = _mm(ARROW_LENGTH_MM, render_scale)
    draw.line(
        [(x_left + arrow_len_px, cx), (x_right - arrow_len_px, cx)],
        fill="black",
        width=axis_w,
    )
    _draw_filled_arrow(draw, (x_right, cx), (1, 0), render_scale)
    _draw_hollow_arrow(
        draw,
        (x_left, cx),
        (-1, 0),
        render_scale,
        _pt(HOLLOW_ARROW_LINE_PT, render_scale),
    )

    # Y 轴: 垂直线（线段缩进一个箭头长度，避免穿过箭头）
    draw.line(
        [(cx, y_top + arrow_len_px), (cx, y_bottom - arrow_len_px)],
        fill="black",
        width=axis_w,
    )
    _draw_filled_arrow(draw, (cx, y_top), (0, -1), render_scale)
    _draw_hollow_arrow(
        draw,
        (cx, y_bottom),
        (0, 1),
        render_scale,
        _pt(HOLLOW_ARROW_LINE_PT, render_scale),
    )

    # ── 轴标签 ──
    font_axis = _load_font(12 * TEXT_SIZE_MULTIPLIER * render_scale)
    font_code = _load_font(12 * TEXT_SIZE_MULTIPLIER * render_scale)

    _draw_text_with_anchor(
        draw,
        (
            _mm(_print_safe_x_mm(97, render_scale), render_scale),
            _mm(46, render_scale),
        ),
        "X",
        font_axis,
        "black",
        "right_bottom",
    )
    _draw_text_with_anchor(
        draw,
        (_mm(47, render_scale), _mm(6, render_scale)),
        "Y",
        font_axis,
        "black",
        "right_bottom",
    )

    # ── 码值文字 ──
    _draw_text_with_anchor(
        draw,
        (_mm(75.8, render_scale), _mm(6, render_scale)),
        code_value,
        font_code,
        "black",
        "bottom_center",
    )

    # ── 16 个 DM 码 (12×12 模块) ──
    dm_size = _mm(DM_SYMBOL_MM, render_scale)
    half = dm_size // 2

    for mx, my in POSITIONS_MM:
        px_x = _mm(mx, render_scale)
        px_y = _mm(my, render_scale)
        dm_img = _render_dm(code_value, dm_size)
        label.paste(dm_img, (px_x - half, px_y - half))

    target_dpi = DPI * render_scale
    label.save(output_path, dpi=(target_dpi, target_dpi))
    return os.path.abspath(output_path)
