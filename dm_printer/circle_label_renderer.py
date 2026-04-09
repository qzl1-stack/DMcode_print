"""圆码模版渲染器 — 80×60mm 标签，中心圆环 + 单个 DM 码.

模版参数：
- 标签尺寸：80×60 mm
- 圆心：(40, 30) mm（标签中心）
- 圆环外径：45 mm（半径 22.5 mm）
- 圆环线宽：12 pt
- DM 码边长：22.5 mm，居中
- DM 码模块数：14×14
- 十字准线：中心十字，长 5 mm
- 码值文字：右下角
"""

from __future__ import annotations

import math
import os
import tempfile
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageOps
from pylibdmtx.pylibdmtx import encode as dm_encode
from dm_printer.zpl_generator import DPI as PRINT_DPI

LABEL_W_MM = 80.0
LABEL_H_MM = 60.0
DEFAULT_RENDER_SCALE = 4

CENTER_X_MM = 40.0
CENTER_Y_MM = 30.0

CIRCLE_DIAMETER_MM = 45.0
CIRCLE_RADIUS_MM = CIRCLE_DIAMETER_MM / 2.0
RING_WIDTH_PT = 12.0

DM_SIDE_MM = 22.5
DM_SYMBOL_SIZE = 14

CROSSHAIR_LINE_PT = 1.0
CROSSHAIR_SEGMENT_LEN_MM = 5.0

# 四条指向中心的线段起点（mm）
CROSSHAIR_TOP_START = (40.0, -1.0)
CROSSHAIR_BOTTOM_START = (40.0, 62.3)
CROSSHAIR_LEFT_START = (1.1, 30.0)
CROSSHAIR_RIGHT_START = (79.2, 30.0)

CODES_PER_LABEL = 1

DPI = PRINT_DPI


def _label_w_px(render_scale: int) -> int:
    return math.ceil(LABEL_W_MM / 25.4 * DPI) * render_scale


def _label_h_px(render_scale: int) -> int:
    return math.ceil(LABEL_H_MM / 25.4 * DPI) * render_scale


def _mm_x(mm: float, render_scale: int) -> int:
    return round(mm / LABEL_W_MM * _label_w_px(render_scale))


def _mm_y(mm: float, render_scale: int) -> int:
    return round(mm / LABEL_H_MM * _label_h_px(render_scale))


def _mm_abs(mm: float, render_scale: int) -> int:
    """用于与方向无关的尺寸（如半径、边长）.
    
    使用标签宽度作为基准（更合理）。
    """
    base_px = _label_w_px(render_scale)
    return round(mm / LABEL_W_MM * base_px)


def _pt(pt: float, render_scale: int) -> int:
    return max(1, round(pt / 72.0 * DPI * render_scale))


def _load_font(size_px: int) -> ImageFont.FreeTypeFont:
    paths = [
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


def _render_dm(data: str, target_px: int) -> Image.Image:
    """生成固定 14×14 模块的 Data Matrix 码."""
    symbol_size = f"{DM_SYMBOL_SIZE}x{DM_SYMBOL_SIZE}"
    encoded = dm_encode(data.encode("utf-8"), size=symbol_size)

    img = Image.frombytes(
        "RGB", (encoded.width, encoded.height), encoded.pixels
    )

    # pylibdmtx 输出通常包含 quiet zone（白边），先裁掉再按目标边长缩放，
    # 避免视觉上"未铺满 22.5mm 正方形"。
    mono = img.convert("L")
    bbox = ImageOps.invert(mono).getbbox()
    if bbox is not None:
        img = img.crop(bbox)

    return img.resize((target_px, target_px), Image.Resampling.NEAREST)


def render_circle_label(
    code_value: str,
    output_path: Optional[str] = None,
    render_scale: int = DEFAULT_RENDER_SCALE,
) -> str:
    """渲染一张圆码标签预览图.

    Args:
        code_value:    DM 码内容
        output_path:   输出 PNG 路径；为 None 时使用临时文件
        render_scale:  渲染倍率；预览建议 4，打印建议 1

    Returns:
        生成图片的绝对路径
    """
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".png", prefix="dm_circle_")
        os.close(fd)

    if render_scale < 1:
        raise ValueError("render_scale 必须大于等于 1")

    w_px = _label_w_px(render_scale)
    h_px = _label_h_px(render_scale)
    label = Image.new("RGB", (w_px, h_px), "white")
    draw = ImageDraw.Draw(label)

    cx = _mm_x(CENTER_X_MM, render_scale)
    cy = _mm_y(CENTER_Y_MM, render_scale)

    # ── 圆环 ──
    ring_w = _pt(RING_WIDTH_PT, render_scale)
    r_px = _mm_abs(CIRCLE_RADIUS_MM, render_scale)

    draw.ellipse(
        [cx - r_px, cy - r_px, cx + r_px, cy + r_px],
        fill=None,
        outline="black",
        width=ring_w,
    )

    # ── 中央 DM 码 ──
    dm_px = _mm_abs(DM_SIDE_MM, render_scale)
    half_dm = dm_px // 2
    dm_img = _render_dm(code_value, dm_px)
    label.paste(dm_img, (cx - half_dm, cy - half_dm))

    # ── 四条指向中心的准线（在 DM 码之上）──
    crosshair_w = _pt(CROSSHAIR_LINE_PT, render_scale)
    seg_len_x = _mm_x(CROSSHAIR_SEGMENT_LEN_MM, render_scale)
    seg_len_y = _mm_y(CROSSHAIR_SEGMENT_LEN_MM, render_scale)

    # 上方线：从 (40, -1) 向下 12mm，到 (40, 11)
    x1 = _mm_x(CROSSHAIR_TOP_START[0], render_scale)
    y1 = _mm_y(CROSSHAIR_TOP_START[1], render_scale)
    draw.line([(x1, y1), (x1, y1 + seg_len_y)], fill="black", width=crosshair_w)

    # 下方线：从 (40, 62.3) 向上 12mm，到 (40, 50.3)
    x2 = _mm_x(CROSSHAIR_BOTTOM_START[0], render_scale)
    y2 = _mm_y(CROSSHAIR_BOTTOM_START[1], render_scale)
    draw.line([(x2, y2), (x2, y2 - seg_len_y)], fill="black", width=crosshair_w)

    # 左方线：从 (1.1, 30) 向右 12mm，到 (13.1, 30)
    x3 = _mm_x(CROSSHAIR_LEFT_START[0], render_scale)
    y3 = _mm_y(CROSSHAIR_LEFT_START[1], render_scale)
    draw.line([(x3, y3), (x3 + seg_len_x, y3)], fill="black", width=crosshair_w)

    # 右方线：从 (79.2, 30) 向左 12mm，到 (67.2, 30)
    x4 = _mm_x(CROSSHAIR_RIGHT_START[0], render_scale)
    y4 = _mm_y(CROSSHAIR_RIGHT_START[1], render_scale)
    draw.line([(x4, y4), (x4 - seg_len_x, y4)], fill="black", width=crosshair_w)

    # ── 码值文字（右下角）──
    font = _load_font(48 * render_scale)
    bbox = draw.textbbox((0, 0), code_value, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    margin = _mm_abs(2.0, render_scale)
    draw.text(
        (w_px - tw - margin, h_px - th - margin),
        code_value,
        fill="black",
        font=font,
    )

    target_dpi = DPI * render_scale
    label.save(output_path, dpi=(target_dpi, target_dpi))
    return os.path.abspath(output_path)
