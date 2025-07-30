from enum import Enum as PyEnum

from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema as cs


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
