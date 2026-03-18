"""码号生成器：支持大码（8位数字）和小码（XY坐标+A）两种格式."""

from __future__ import annotations


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

    Args:
        x_start: X 坐标起始值
        y_start: Y 坐标起始值
        x_step:  每个码 X 坐标增量
        y_step:  每个码 Y 坐标增量
        count:   生成数量
    """
    codes: list[str] = []
    for i in range(count):
        x = x_start + i * x_step
        y = y_start + i * y_step
        codes.append(f"XY{x:05d}{y:05d}A")
    return codes
