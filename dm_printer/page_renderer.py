"""完整打印页面预览渲染器 — 生成模拟打印效果的完整页面图像.

支持：
- 单页标签预览（A4 页面）
- 完整批次预览
- 支持翻转 Y 轴
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional

from PIL import Image

from dm_printer.label_renderer import render_label


def render_page_preview(
    codes: list[str],
    output_path: Optional[str] = None,
    codes_per_label: int = 16,
    flip_y: bool = False,
) -> str:
    """生成完整页面预览图.

    Args:
        codes: DM 码列表
        output_path: 输出 PNG 路径；为 None 时使用临时文件
        codes_per_label: 每张标签的码数（通常为 16）
        flip_y: 是否翻转 Y 轴

    Returns:
        生成图片的绝对路径
    """
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".png", prefix="dm_page_")
        os.close(fd)

    # A4 尺寸：210×297 mm @203 DPI
    a4_width_mm = 210.0
    a4_height_mm = 297.0
    dpi = 203
    scale = 4

    label_mm = 100.0
    labels_per_row = int(a4_width_mm / label_mm)
    labels_per_col = int(a4_height_mm / label_mm)
    max_labels_per_page = labels_per_row * labels_per_col

    # 计算页数
    total_labels = (len(codes) + codes_per_label - 1) // codes_per_label
    total_pages = (total_labels + max_labels_per_page - 1) // max_labels_per_page

    a4_width_px = int(a4_width_mm / 25.4 * dpi * scale)
    a4_height_px = int(a4_height_mm / 25.4 * dpi * scale)

    # 只生成第一页预览
    page = Image.new("RGB", (a4_width_px, a4_height_px), "white")

    label_px = int(label_mm / 25.4 * dpi * scale)
    label_idx = 0

    for row in range(labels_per_col):
        for col in range(labels_per_row):
            if label_idx >= len(codes):
                break

            code = codes[label_idx]
            label_img_path = render_label(code)
            label_img = Image.open(label_img_path)

            # 粘贴标签
            x = col * label_px
            y = row * label_px
            page.paste(label_img, (x, y))

            label_idx += 1

        if label_idx >= len(codes):
            break

    page.save(output_path, dpi=(dpi, dpi))
    return os.path.abspath(output_path)


def render_all_pages_preview(
    codes: list[str],
    output_dir: Optional[str] = None,
    codes_per_label: int = 16,
    flip_y: bool = False,
) -> list[str]:
    """生成所有页面预览图.

    Args:
        codes: DM 码列表
        output_dir: 输出目录；为 None 时使用临时目录
        codes_per_label: 每张标签的码数
        flip_y: 是否翻转 Y 轴

    Returns:
        生成图片的路径列表
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="dm_pages_")

    os.makedirs(output_dir, exist_ok=True)

    paths = []
    page_idx = 1
    codes_idx = 0

    while codes_idx < len(codes):
        # 每页最多 2 行 × 2 列 = 4 张标签
        page_codes = codes[codes_idx:codes_idx + 64]  # 4 张标签 × 16 码/张
        output_path = os.path.join(output_dir, f"page_{page_idx:03d}.png")
        path = render_page_preview(page_codes, output_path, codes_per_label, flip_y)
        paths.append(path)

        codes_idx += len(page_codes)
        page_idx += 1

    return paths
