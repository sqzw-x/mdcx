from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


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


def is_dataclass_instance(obj):
    return is_dataclass(obj) and not isinstance(obj, type)


T = TypeVar("T", bound="DataclassInstance")


def update(d1: "T", d2: "DataclassInstance | dict") -> T:
    """
    用一个 dataclass/dict 更新另一个 dataclass, 此函数不会修改原实例

    此函数不是类型安全的, 当 d2 中存在 d1 同名字段但类型不匹配时, 不会导致运行时错误, 可以在 d1 的 __post_init__ 方法中进行类型检查.

    Returns:
        返回一个新的实例, 其类型与 d1 相同.
    """
    assert is_dataclass_instance(d1), "update() should be called on dataclass instance"
    if not isinstance(d2, dict):
        d2 = asdict(d2)
    return type(d1)(**update_existing(asdict(d1), d2))
