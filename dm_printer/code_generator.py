"""码号生成器：支持大码（8位数字）和小码（XY坐标+A）两种格式.

核心规则：
- 一张标签上的 16 个 DM 码值 **完全相同**。
- 批量打印时，每张标签的码值递增。
"""

from __future__ import annotations

import re


def generate_big_codes(start: int, count: int) -> list[str]:
    """生成大码列表.

    大码格式：8位纯数字，自动递增。
    例如 start=90001, count=3 → ["00090001","00090002","00090003"]
    """
    return [f"{start + i:08d}" for i in range(count)]


def generate_small_codes(
    x_start: int,
    y_start: int,
    x_step: int,
    y_step: int,
    count: int,
) -> list[str]:
    """生成小码列表.

    小码格式：XY + 5位X坐标 + 5位Y坐标 + A
    例如 x=100, y=200 → "XY0010000200A"
    """
    codes: list[str] = []
    for i in range(count):
        x = x_start + i * x_step
        y = y_start + i * y_step
        codes.append(f"XY{x:05d}{y:05d}A")
    return codes


def generate_batch_codes(start_code: str, count: int) -> list[str]:
    """从起始码值生成批量码号列表.

    每个码号对应一张标签（标签内 16 个码均为同一值）。
    自动识别码类型并递增。

    Args:
        start_code: 起始码值字符串
        count:      标签数量

    Returns:
        码值列表，长度等于 count
    """
    if count <= 0:
        return []
    if count == 1:
        return [start_code]

    m = re.match(r"^(\D*)(\d+)(\D*)$", start_code)
    if m:
        prefix, num_str, suffix = m.groups()
        width = len(num_str)
        start_num = int(num_str)
        return [
            f"{prefix}{start_num + i:0{width}d}{suffix}"
            for i in range(count)
        ]

    return [start_code] * count
