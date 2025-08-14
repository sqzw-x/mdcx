"""
从 dataclass 生成 StrEnum
"""

from dataclasses import fields, is_dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


def generate_enum(dataclass_type: type["DataclassInstance"], enum_name: str | None = None) -> str:
    """
    生成 StrEnum 的代码字符串

    Args:
        dataclass_type: dataclass 类型
        enum_name: 生成的 enum 名称，如果为 None 则使用 dataclass 名称 + "Fields"

    Returns:
        StrEnum 类的代码字符串

    Raises:
        ValueError: 如果传入的不是 dataclass 类型

    Example:
        >>> @dataclass
        ... class User:
        ...     name: str
        ...     age: int
        >>>
        >>> code = generate_field_enum_code(User)
        >>> print(code)
        class UserFields(StrEnum):
            name = "name"
            age = "age"
    """
    if not is_dataclass(dataclass_type):
        raise ValueError(f"{dataclass_type} 不是 dataclass 类型")

    if enum_name is None:
        enum_name = f"{dataclass_type.__name__}Fields"

    # 获取所有字段名
    field_names = [field.name for field in fields(dataclass_type)]

    # 生成代码
    lines = [
        f"class {enum_name}(StrEnum):",
    ]

    if not field_names:
        lines.append("    pass")
    else:
        for field_name in field_names:
            enum_name = field_name.upper()
            if enum_name in dir(StrEnum):
                lines.append(f'    {enum_name}_ = "{field_name}"')
            else:
                lines.append(f'    {enum_name} = "{field_name}"')

    return "\n".join(lines)


def gen(dataclass_types: list[type["DataclassInstance"]], output_file: str | Path | None = None) -> str:
    """
    从多个 dataclass 生成对应的 StrEnum 代码

    Args:
        dataclass_types: dataclass 类型列表
        output_file: 如果提供，将生成的代码写入文件

    Returns:
        生成的完整代码字符串
    """
    code_lines = ["from enum import StrEnum", "", ""]

    for dataclass_type in dataclass_types:
        code_lines.append(generate_enum(dataclass_type))
        code_lines.extend(["", ""])

    # 生成完整代码
    full_code = "\n".join(code_lines)

    # 写入文件
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(full_code, encoding="utf-8")

    return full_code


def main():
    from mdcx.models.types import CrawlerResult

    output_file = "mdcx/gen/field_enums.py"
    gen([CrawlerResult], output_file)
    print(f"已生成代码到文件: {output_file}")


if __name__ == "__main__":
    main()
