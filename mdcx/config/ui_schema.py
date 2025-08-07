from enum import Enum as PyEnum
from functools import partial, update_wrapper
from typing import Any, Literal, overload

from pydantic import Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema as cs


def extract_ui_schema_recursive(json_schema: dict[str, Any]) -> dict[str, Any]:
    """
    从 JSON Schema 中递归提取 UI Schema. 此 UI Schema 可直接用于 react-jsonschema-form 渲染表单.

    约定: JSON Schema 中的 uiSchema 字段被直接用作该字段的 UI Schema 值

    已知 UI Schema 和 JSON Schema 结构的差异:
    - JSON Schema 中 object 的字段包含在 properties 中, 而 UI Schema 中 object 字段直接嵌套

    Args:
        json_schema: 输入的 JSON Schema 字典

    Returns:
        提取的 UI Schema 字典。如果没有 UI 相关的配置，返回空字典。

    Examples:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "name": {
        ...             "type": "string",
        ...             "uiSchema": {"ui:widget": "text"}
        ...         }
        ...     }
        ... }
        >>> extract_ui_schema_recursive(schema)
        {"name": {"ui:widget": "text"}}
    """
    result = {}

    # 如果当前层级有 uiSchema 字段，直接使用
    if "uiSchema" in json_schema:
        result.update(json_schema["uiSchema"])

    # 处理 object 类型的 properties
    # JSON Schema: properties 包含字段定义
    # UI Schema: 字段直接嵌套
    if json_schema.get("type") == "object" and "properties" in json_schema:
        for field_name, field_schema in json_schema["properties"].items():
            if isinstance(field_schema, dict):
                field_ui_schema = extract_ui_schema_recursive(field_schema)
                if field_ui_schema:  # 只有非空时才添加
                    result[field_name] = field_ui_schema

    # 处理 array 类型的 items
    # 数组的 UI Schema 通过 "items" 键传递给数组元素
    elif json_schema.get("type") == "array" and "items" in json_schema:
        items_schema = json_schema["items"]
        if isinstance(items_schema, dict):
            items_ui_schema = extract_ui_schema_recursive(items_schema)
            if items_ui_schema:
                result["items"] = items_ui_schema

    return result


class Enum(PyEnum):
    @classmethod
    def names(cls):
        """
        向用户显示的枚举名称, 子类需重写. 必须与枚举定义顺序一致.

        Returns:
            list of enum names shown in the UI.
        """
        return [member.name for member in cls]

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: cs.CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        """
        为枚举添加自定义 JSON schema 字段.

        自定义字段:
        - showNames 定义显示名称
        """
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        # 此时 json_schema 已包含标准字段 title, enum, type
        json_schema["showNames"] = cls.names()
        return json_schema


@overload
def _ServerPath(
    default: str,
    *,
    title: str | None = None,
    path_type: Literal["file", "directory", "mixed"],
    multiple: Literal[False],
    initial_path: str = ".",
    ref_field: str | None = None,
    description: str | None = None,
) -> str: ...
@overload
def _ServerPath(
    default: list[str],
    *,
    title: str | None = None,
    path_type: Literal["file", "directory", "mixed"],
    multiple: Literal[True],
    initial_path: str = ".",
    ref_field: str | None = None,
    description: str | None = None,
) -> list[str]: ...
def _ServerPath(
    default,
    *,
    title: str | None = None,
    path_type: Literal["file", "directory", "mixed"],
    multiple: bool,
    initial_path: str = ".",
    ref_field: str | None = None,
    description: str | None = None,
) -> Any:
    """
    创建一个字段, 表示一个或多个服务器上的路径. 同时为此字段添加自定义 UI schema.

    Args:
        path_type: 路径类型，可选值: "file", "directory", "mixed"
        multiple: 是否支持多选
        initial_path: 初始路径
        ref_field: 引用另一字段作为相对路径的基准
        default: 默认值
        description: 字段描述
        **kwargs: 传递给 Field 的其他参数

    Returns:
        配置了自定义 UI schema 的 Field
    """
    if default is None:
        default = [] if multiple else "."
    # 构建自定义属性
    custom_props = {"multiple": multiple, "type": path_type, "initialPath": initial_path, "refField": ref_field}
    # 构建 JSON schema extra
    json_schema_extra: dict[str, Any] = {"uiSchema": {"customProps": custom_props, "ui:field": "serverPath"}}
    return Field(title=title, default=default, description=description, json_schema_extra=json_schema_extra)


ServerPathFile = update_wrapper(partial(_ServerPath, path_type="file", multiple=False), _ServerPath)
ServerPathFileMultiple = update_wrapper(partial(_ServerPath, path_type="file", multiple=True), _ServerPath)
ServerPathDirectory = update_wrapper(partial(_ServerPath, path_type="directory", multiple=False), _ServerPath)
ServerPathDirectoryMultiple = update_wrapper(partial(_ServerPath, path_type="directory", multiple=True), _ServerPath)
ServerPathMixedField = update_wrapper(partial(_ServerPath, path_type="mixed", multiple=True), _ServerPath)
