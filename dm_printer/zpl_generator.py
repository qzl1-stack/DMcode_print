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
