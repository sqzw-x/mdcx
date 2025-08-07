import random
import string
from datetime import timedelta
from enum import Enum
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel, HttpUrl
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined


def generate_random_pydantic_instance(
    model_class: type[BaseModel],
    no_default: bool = True,
    allow_default: list[str] | None = None,
) -> BaseModel:
    """
    为给定的 Pydantic 模型生成一个随机实例

    Args:
        model_class: Pydantic 模型类
        no_default: 若为 True 则确保生成的值与默认值不同
        allow_default: no_default 为 True 时也允许使用默认值的字段列表

    Returns:
        包含随机字段值的模型实例
    """
    # 获取默认实例用于比较

    # 生成随机数据
    random_data = {}

    for field_name, field_info in model_class.model_fields.items():
        field_type = field_info.annotation

        # 跳过没有类型注解的字段
        if field_type is None:
            continue

        # 生成随机值
        random_value = generate_random_value_for_type(field_type, field_info)

        if not no_default:
            random_data[field_name] = random_value
            continue

        # 获取默认值
        default_value = None
        if field_info.default is not PydanticUndefined:
            default_value = field_info.default
        elif field_info.default_factory is not None:
            try:
                default_value = field_info.default_factory()  # type: ignore
            except Exception as e:
                raise ValueError(
                    f"Field '{field_name}' has a default factory that requires parameters, which is not supported."
                ) from e

        # 确保与默认值不同
        if default_value:
            attempts = 0
            max_attempts = 10

            # 尝试生成与默认值不同的值
            while random_value == default_value and attempts < max_attempts:
                if field_type is not None:
                    random_value = generate_random_value_for_type(field_type, field_info)
                attempts += 1
            if attempts == max_attempts and field_name not in (allow_default or []):
                raise ValueError(f"无法为字段 '{field_name}' 生成与默认值不同的随机值")

        random_data[field_name] = random_value

    # 创建实例
    instance = model_class(**random_data)

    return instance


def generate_random_value_for_type(field_type: type, field_info: FieldInfo | None = None) -> Any:
    """
    根据类型生成随机值

    Args:
        field_type: 字段类型
        field_info: 字段信息（可选）

    Returns:
        适合该类型的随机值
    """
    # 处理 Union 类型（如 Optional）
    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin is Union:
        # 如果是 Optional (Union[T, None])，选择非 None 的类型
        non_none_types = [arg for arg in args if arg is not type(None)]
        if non_none_types:
            field_type = non_none_types[0]
        else:
            return None

    # 处理 list 类型
    if origin is list:
        if args:
            item_type = args[0]
            # 如果是枚举列表
            if isinstance(item_type, type) and issubclass(item_type, Enum):
                return generate_random_list_from_enum(item_type, 1, 5)
            else:
                # 生成随机数量的列表项
                size = random.randint(1, 5)
                return [generate_random_value_for_type(item_type) for _ in range(size)]
        else:
            return []

    # 基本类型
    if field_type is str:
        # 检查字段名来推断更合适的随机值类型
        if field_info and hasattr(field_info, "alias") and field_info.alias:
            field_name = field_info.alias.lower()
        else:
            field_name = ""

        if "path" in field_name or "folder" in field_name or "directory" in field_name:
            return generate_random_path()
        elif "url" in field_name or "api" in field_name:
            return f"https://{generate_random_string(8)}.com"
        elif "key" in field_name or "token" in field_name:
            return generate_random_string(32)
        elif "id" in field_name:
            return generate_random_string(16)
        else:
            return generate_random_string()

    elif field_type is int:
        return random.randint(1, 100)

    elif field_type is float:
        return random.uniform(0.0, 100.0)

    elif field_type is bool:
        return (
            not field_info.default
            if field_info and field_info.default is not PydanticUndefined
            else random.choice([True, False])
        )

    elif field_type is timedelta:
        return generate_random_timedelta()

    elif field_type is HttpUrl:
        return generate_random_url()

    # 枚举类型
    elif isinstance(field_type, type) and issubclass(field_type, Enum):
        return random.choice(list(field_type))

    # Pydantic 模型
    elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
        return generate_random_pydantic_instance(field_type)

    else:
        raise ValueError(f"Unsupported field type: {field_type}")


def generate_random_string(length: int = 10) -> str:
    """生成随机字符串"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_path() -> str:
    """生成随机路径"""
    return f"/random/path/{generate_random_string()}"


def generate_random_url() -> HttpUrl:
    """生成随机 HTTP URL"""
    domain = generate_random_string(8)
    return HttpUrl(f"https://{domain}.com")


def generate_random_timedelta() -> timedelta:
    """生成随机时间间隔"""
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    seconds = random.randint(0, 59)
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


def generate_random_list_from_enum(enum_class: type[Enum], min_items: int = 1, max_items: int = 5) -> list:
    """从枚举类生成随机列表"""
    all_items = list(enum_class)
    num_items = random.randint(min_items, min(max_items, len(all_items)))
    return random.sample(all_items, num_items)
