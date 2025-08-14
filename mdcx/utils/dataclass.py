from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


def is_dataclass_instance(obj):
    return is_dataclass(obj) and not isinstance(obj, type)


T = TypeVar("T", bound="DataclassInstance")


def update(d1: "T", d2: "DataclassInstance | dict") -> T:
    """
    用一个 dataclass/dict 更新另一个 dataclass, 此函数返回一个新实例.

    Returns:
        返回一个新的实例, 其类型与 d1 相同.
    """
    assert is_dataclass_instance(d1), "update() should be called on dataclass instance"
    if not isinstance(d2, dict):
        d2 = asdict(d2)
    return type(d1)(**update_existing(asdict(d1), d2))


def update_valid(d1: "T", d2: "DataclassInstance | dict", validator: Callable[..., bool] = bool) -> T:
    """
    用一个 dataclass/dict 中的有效值更新另一个 dataclass, 此函数返回一个新实例.

    Args:
        d1: 要更新的 dataclass 实例
        d2: 包含新值的 dataclass 实例或字典
        validator: 判断有效值的函数, 接受新值, 返回 bool 表示是否有效. 默认使用 bool 转换.
    """
    assert is_dataclass_instance(d1), "update_valid() should be called on dataclass instance"
    if not isinstance(d2, dict):
        d2 = asdict(d2)
    return type(d1)(**update_existing_valid(asdict(d1), d2, validator))


def update_existing(d1: dict, d2: dict) -> dict:
    """
    类似 dict.update, 但不会向 d1 添加新 key.
    """
    res = d1
    other = d2
    if len(d1) > len(d2):
        d1, d2 = d2, d1  # 确保 d1 是较小的字典
    for key in d1:
        if key in d2:
            res[key] = other[key]
    return res


def update_existing_valid(d1: dict, d2: dict, validator: Callable[..., bool] = bool) -> dict:
    """
    类似 update_existing, 但只使用 d2 中有效的字段.

    Args:
        d1: 要更新的字典
        d2: 包含新值的字典
        validator: 判断有效值的函数, 接受新值, 返回 bool 表示是否有效. 默认使用 bool 转换.
    """
    res = d1
    other = d2
    if len(d1) > len(d2):
        d1, d2 = d2, d1
    for key in d1:
        if key in d2 and validator(r := other[key]):
            res[key] = r
    return res
