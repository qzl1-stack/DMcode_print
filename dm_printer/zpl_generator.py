"""ZPL 指令生成器：将码号列表转换为 Zebra ZPL-II 打印流.

技术参数（与 BarTender .btw 模板 100% 一致）：
- 符号类型：Data Matrix ECC200 (12×12)
- 模块尺寸：10 dots（≈1.25 mm @203 DPI）
- 标签尺寸：100×100 mm（≈800×800 dots @203 DPI）
- 排版网格：4×4（每张标签最多 16 个码）
"""

from __future__ import annotations

import math

DPI = 203
LABEL_SIZE_MM = 100.0
MODULE_DOTS = 10
MATRIX_MODULES = 12  # 12×12 ECC200

POSITIONS_MM: list[tuple[float, float]] = [
    (20, 20), (40, 20), (60, 20), (80, 20),
    (20, 40), (40, 40), (60, 40), (80, 40),
    (20, 60), (40, 60), (60, 60), (80, 60),
    (20, 80), (40, 80), (60, 80), (80, 80),
]

CODES_PER_LABEL = len(POSITIONS_MM)  # 16


def mm_to_dots(mm: float) -> int:
    """毫米 → 打印点数 (向最近整数取整)."""
    return round(mm * DPI / 25.4)


def _build_label_zpl(
    codes: list[str],
    flip_y: bool = False,
    center_offset: bool = True,
) -> str:
    """为一张标签（最多 16 个码）生成完整 ZPL 指令."""
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

    for idx, code in enumerate(codes):
        if idx >= CODES_PER_LABEL:
            break
        mx, my = POSITIONS_MM[idx]
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
            f"^FD{code}^FS"
        )

    parts.append("^PQ1")
    parts.append("^XZ")
    return "\n".join(parts)


def generate_zpl(
    codes: list[str],
    flip_y: bool = False,
    center_offset: bool = True,
) -> list[str]:
    """将码号列表按 4×4 分批，返回每张标签的 ZPL 指令.

    Args:
        codes:         待打印的码号列表
        flip_y:        是否翻转 Y 轴（适配打印机出纸方向）
        center_offset: 是否将 ^FO 偏移半个符号尺寸使码居中于网格点
    Returns:
        ZPL 指令字符串列表，每个元素对应一张标签
    """
    if not codes:
        return []

    label_count = math.ceil(len(codes) / CODES_PER_LABEL)
    labels: list[str] = []

    for i in range(label_count):
        batch = codes[
            i * CODES_PER_LABEL : (i + 1) * CODES_PER_LABEL
        ]
        labels.append(
            _build_label_zpl(batch, flip_y, center_offset)
        )

    return labels
