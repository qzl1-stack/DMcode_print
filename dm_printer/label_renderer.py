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

LABEL_MM = 100.0
DPI = 203
RENDER_SCALE = 4
LABEL_PX = int(LABEL_MM / 25.4 * DPI * RENDER_SCALE)

BORDER_SIZE_MM = 85.0
BORDER_CENTER_MM = 50.0
BORDER_HALF_MM = BORDER_SIZE_MM / 2.0

AXIS_START_MM = 1.0
AXIS_END_MM = 99.0
AXIS_CENTER_MM = 50.0

ARROW_LENGTH_MM = 4.0
ARROW_WIDTH_MM = 2.8

POSITIONS_MM: list[tuple[float, float]] = [
    (20, 20), (40, 20), (60, 20), (80, 20),
    (20, 40), (40, 40), (60, 40), (80, 40),
    (20, 60), (40, 60), (60, 60), (80, 60),
    (20, 80), (40, 80), (60, 80), (80, 80),
]

CODES_PER_LABEL = len(POSITIONS_MM)

DM_MODULES = 12
DM_MODULE_SIZE_MM = 1.25
DM_SYMBOL_MM = DM_MODULES * DM_MODULE_SIZE_MM


def _mm(mm: float) -> int:
    return round(mm / 25.4 * DPI * RENDER_SCALE)


def _pt(pt: float) -> int:
    return max(1, round(pt / 72.0 * DPI * RENDER_SCALE))


def _load_font(size_px: int) -> ImageFont.FreeTypeFont:
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size_px)
    return ImageFont.load_default()


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
) -> list[tuple[int, int]]:
    """计算箭头三角形的三个顶点."""
    tx, ty = tip
    dx, dy = direction
    length = math.hypot(dx, dy)
    if length == 0:
        return [(tx, ty)] * 3
    ux, uy = dx / length, dy / length
    px, py = -uy, ux

    arrow_len = _mm(ARROW_LENGTH_MM)
    arrow_half_w = _mm(ARROW_WIDTH_MM) / 2

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
) -> None:
    """绘制实心箭头（正半轴方向）."""
    pts = _arrow_points(tip, direction)
    draw.polygon(pts, fill="black")


def _draw_hollow_arrow(
    draw: ImageDraw.ImageDraw,
    tip: tuple[int, int],
    direction: tuple[float, float],
    line_width: int = 0,
) -> None:
    """绘制空心箭头（负半轴方向）."""
    if line_width == 0:
        line_width = _pt(1.0)
    pts = _arrow_points(tip, direction)
    draw.polygon(pts, fill="white", outline="black", width=line_width)


def _render_dm(data: str, target_px: int) -> Image.Image:
    encoded = dm_encode(data.encode("utf-8"))
    img = Image.frombytes(
        "RGB", (encoded.width, encoded.height), encoded.pixels
    )
    return img.resize((target_px, target_px), Image.NEAREST)


def render_label(
    code_value: str,
    output_path: Optional[str] = None,
) -> str:
    """渲染一张标签预览图.

    Args:
        code_value: DM 码内容（16 个码均为此值）
        output_path: 输出 PNG 路径；为 None 时使用临时文件

    Returns:
        生成图片的绝对路径
    """
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".png", prefix="dm_label_")
        os.close(fd)

    label = Image.new("RGB", (LABEL_PX, LABEL_PX), "white")
    draw = ImageDraw.Draw(label)

    # ── 虚线边框 85×85mm, 0.5pt, 虚线样式匹配 BarTender ──
    border_x0 = _mm(BORDER_CENTER_MM - BORDER_HALF_MM)
    border_y0 = _mm(BORDER_CENTER_MM - BORDER_HALF_MM)
    border_x1 = _mm(BORDER_CENTER_MM + BORDER_HALF_MM)
    border_y1 = _mm(BORDER_CENTER_MM + BORDER_HALF_MM)

    dash = _mm(5.5)
    gap = _mm(3.0)
    border_w = _pt(0.5)
    _draw_dashed_rect(
        draw,
        (border_x0, border_y0, border_x1, border_y1),
        dash, gap, border_w, "black",
    )

    # ── 坐标轴 ──
    axis_w = _pt(1.0)
    cx = _mm(AXIS_CENTER_MM)
    x_left = _mm(AXIS_START_MM)
    x_right = _mm(AXIS_END_MM)
    y_top = _mm(AXIS_START_MM)
    y_bottom = _mm(AXIS_END_MM)

    # X 轴: 水平线
    draw.line([(x_left, cx), (x_right, cx)], fill="black", width=axis_w)
    _draw_filled_arrow(draw, (x_right, cx), (1, 0))
    _draw_hollow_arrow(draw, (x_left, cx), (-1, 0), axis_w)

    # Y 轴: 垂直线 (正方向朝上)
    draw.line([(cx, y_top), (cx, y_bottom)], fill="black", width=axis_w)
    _draw_filled_arrow(draw, (cx, y_top), (0, -1))
    _draw_hollow_arrow(draw, (cx, y_bottom), (0, 1), axis_w)

    # ── 轴标签 ──
    font_axis = _load_font(int(12 * RENDER_SCALE))
    font_code = _load_font(int(10 * RENDER_SCALE))

    draw.text(
        (x_right - _mm(2), cx - _mm(7)),
        "X", fill="black", font=font_axis,
    )
    draw.text(
        (cx - _mm(5), y_top - _mm(2)),
        "Y", fill="black", font=font_axis,
    )

    # ── 码值文字 右上角 ──
    bbox_t = draw.textbbox((0, 0), code_value, font=font_code)
    tw = bbox_t[2] - bbox_t[0]
    draw.text(
        (border_x1 - tw, border_y0 - _mm(7)),
        code_value,
        fill="black",
        font=font_code,
    )

    # ── 16 个 DM 码 (12×12 模块) ──
    dm_size = _mm(DM_SYMBOL_MM)
    half = dm_size // 2

    for mx, my in POSITIONS_MM:
        px_x = _mm(mx)
        px_y = _mm(my)
        dm_img = _render_dm(code_value, dm_size)
        label.paste(dm_img, (px_x - half, px_y - half))

    label.save(output_path, dpi=(DPI, DPI))
    return os.path.abspath(output_path)
