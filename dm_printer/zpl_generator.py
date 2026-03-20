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

DPI = 203
LABEL_SIZE_MM = 100.0
MODULE_DOTS = 10
MATRIX_MODULES = 12
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
    """毫米 → 打印点数 (向最近整数取整)."""
    return round(mm * DPI / 25.4)


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
    # 空心箭头：两条边线 + 底边
    if direction in ("right", "left"):
        if direction == "right":
            base_x = tip_x - arrow_len
        else:
            base_x = tip_x + arrow_len
        _add_hline(parts, base_x, tip_y - arrow_half_w, abs(tip_x - base_x) + 1, t)
        parts.append(
            f"^FO{min(base_x, tip_x)},{tip_y - arrow_half_w}"
            f"^GD{abs(tip_x - base_x) + 1},{arrow_half_w + 1},{max(1, t)},B,R^FS"
        )
        parts.append(
            f"^FO{min(base_x, tip_x)},{tip_y}"
            f"^GD{abs(tip_x - base_x) + 1},{arrow_half_w + 1},{max(1, t)},B,N^FS"
        )
    else:
        if direction == "up":
            base_y = tip_y + arrow_len
        else:
            base_y = tip_y - arrow_len
        _add_vline(parts, tip_x - arrow_half_w, min(base_y, tip_y), abs(base_y - tip_y) + 1, t)
        parts.append(
            f"^FO{tip_x - arrow_half_w},{min(base_y, tip_y)}"
            f"^GD{arrow_half_w + 1},{abs(base_y - tip_y) + 1},{max(1, t)},B,N^FS"
        )
        parts.append(
            f"^FO{tip_x},{min(base_y, tip_y)}"
            f"^GD{arrow_half_w + 1},{abs(base_y - tip_y) + 1},{max(1, t)},B,R^FS"
        )


def _build_label_zpl(
    code_value: str,
    flip_y: bool = False,
    center_offset: bool = True,
) -> str:
    """为一张标签生成完整 ZPL 指令.

    标签上 16 个 DM 码全部为 code_value。
    """
    label_dots = mm_to_dots(LABEL_SIZE_MM)
    symbol_dots = MATRIX_MODULES * MODULE_DOTS
    half = symbol_dots // 2

    parts: list[str] = [
        "^XA",
        "^CI28",
        f"^PW{label_dots}",
        f"^LL{label_dots}",
        "^LH0,0",
    ]

    # ---- 模板元素（边框 / 坐标轴 / 文字）----
    border_x0 = mm_to_dots(BORDER_X_MM)
    border_y0 = mm_to_dots(BORDER_Y_MM)
    border_x1 = mm_to_dots(BORDER_X_MM + BORDER_W_MM)
    border_y1 = mm_to_dots(BORDER_Y_MM + BORDER_H_MM)
    dash = max(1, mm_to_dots(BORDER_DASH_MM))
    gap = max(1, mm_to_dots(BORDER_GAP_MM))

    _add_dashed_hline(parts, border_x0, border_x1, border_y0, dash, gap, BORDER_LINE_DOTS)
    _add_dashed_hline(parts, border_x0, border_x1, border_y1, dash, gap, BORDER_LINE_DOTS)
    _add_dashed_vline(parts, border_x0, border_y0, border_y1, dash, gap, BORDER_LINE_DOTS)
    _add_dashed_vline(parts, border_x1, border_y0, border_y1, dash, gap, BORDER_LINE_DOTS)

    cx = mm_to_dots(AXIS_CENTER_MM)
    x_left = mm_to_dots(AXIS_START_MM)
    x_right = mm_to_dots(AXIS_END_MM)
    y_top = mm_to_dots(AXIS_START_MM)
    y_bottom = mm_to_dots(AXIS_END_MM)

    arrow_len = max(1, mm_to_dots(ARROW_LENGTH_MM))
    arrow_half_w = max(1, mm_to_dots(ARROW_WIDTH_MM) // 2)

    # 轴线（缩进箭头长度，避免穿过箭头）
    _add_hline(
        parts,
        x_left + arrow_len,
        cx,
        max(1, x_right - x_left - 2 * arrow_len),
        AXIS_LINE_DOTS,
    )
    _add_vline(
        parts,
        cx,
        y_top + arrow_len,
        max(1, y_bottom - y_top - 2 * arrow_len),
        AXIS_LINE_DOTS,
    )

    # 箭头：+X / +Y 实心，-X / -Y 空心
    _add_filled_arrow(parts, x_right, cx, "right", arrow_len, arrow_half_w)
    _add_hollow_arrow(
        parts,
        x_left,
        cx,
        "left",
        arrow_len,
        arrow_half_w,
        HOLLOW_ARROW_LINE_DOTS,
    )
    _add_filled_arrow(parts, cx, y_top, "up", arrow_len, arrow_half_w)
    _add_hollow_arrow(
        parts,
        cx,
        y_bottom,
        "down",
        arrow_len,
        arrow_half_w,
        HOLLOW_ARROW_LINE_DOTS,
    )

    # 文字（锚点近似）
    x_text_x = mm_to_dots(X_TEXT_MM[0]) - TEXT_HEIGHT_DOTS
    x_text_y = mm_to_dots(X_TEXT_MM[1]) - TEXT_HEIGHT_DOTS
    y_text_x = mm_to_dots(Y_TEXT_MM[0]) - TEXT_HEIGHT_DOTS
    y_text_y = mm_to_dots(Y_TEXT_MM[1]) - TEXT_HEIGHT_DOTS
    code_anchor_x = mm_to_dots(CODE_TEXT_MM[0])
    code_anchor_y = mm_to_dots(CODE_TEXT_MM[1])

    parts.append(f"^FO{x_text_x},{x_text_y}^A0N,{TEXT_HEIGHT_DOTS},{TEXT_HEIGHT_DOTS}^FDX^FS")
    parts.append(f"^FO{y_text_x},{y_text_y}^A0N,{TEXT_HEIGHT_DOTS},{TEXT_HEIGHT_DOTS}^FDY^FS")
    # 底部居中：用 ^FB 做单行居中
    parts.append(
        f"^FO{code_anchor_x - 120},{max(0, code_anchor_y - TEXT_HEIGHT_DOTS)}"
        f"^A0N,{TEXT_HEIGHT_DOTS},{int(TEXT_HEIGHT_DOTS * 0.75)}"
        "^FB240,1,0,C,0"
        f"^FD{code_value}^FS"
    )

    for mx, my in POSITIONS_MM:
        dx = mm_to_dots(mx)
        dy = mm_to_dots(my)

        if flip_y:
            dy = label_dots - dy

        if center_offset:
            dx -= half
            dy -= half

        parts.append(
            f"^FO{dx},{dy}"
            f"^BXN,{MODULE_DOTS},200"
            f"^FD{code_value}^FS"
        )

    parts.append("^PQ1")
    parts.append("^XZ")
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
