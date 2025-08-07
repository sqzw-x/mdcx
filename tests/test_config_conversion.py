from dataclasses import fields
from datetime import timedelta

import pytest
from pydantic import HttpUrl

from mdcx.config.manager import ConfigSchema
from mdcx.config.models import (
    Config,
    MarkType,
    ReadMode,
    TranslateConfig,
    Translator,
    Website,
)
from mdcx.utils.dataclass import update
from tests.random_generator import generate_random_pydantic_instance


def generate_random_config() -> Config:
    """生成具有随机字段值的 Config 实例"""
    r = generate_random_pydantic_instance(Config, no_default=True, allow_default=["website_set"])
    d = r.model_dump(mode="json")

    errors = []

    def dict_fields_all_different(d1: dict, d2: dict) -> bool:
        """
        递归检查两个字典是否所有字段都不相同.

        Returns:
            bool: 如果所有字段都不相同返回 True，否则返回 False
        """
        for key in d1:
            if key not in d2:  # 非共同字段, 视为不同
                continue

            value1 = d1[key]
            value2 = d2[key]

            # 如果值相同,返回 False
            if value1 == value2:
                errors.append(f"字段 '{key}' 的值相同: {value1}")
                return False

            # 如果都是字典,递归检查
            if isinstance(value1, dict) and isinstance(value2, dict):
                if not dict_fields_all_different(value1, value2):
                    return False

        return True

    # 检查任何字段都与默认值不相同
    # default = Config().model_dump(mode="json")
    # assert dict_fields_all_different(d, default), "生成的随机配置中存在与默认值相同的字段: " + ", ".join(errors)

    return Config.model_validate(d)


class TestConfigConversion:
    """测试 Config 与 ConfigSchema 之间的转换"""

    @pytest.mark.parametrize("test_round", range(5))
    def test_to_legacy_and_from_legacy_equivalence(self, test_round):
        """测试 to_legacy 和 from_legacy 的等价性"""
        # 生成随机 Config 实例
        original_config = generate_random_config()

        # 调用 to_legacy 转换为 dict
        legacy_dict = original_config.to_legacy()

        # 创建 ConfigSchema 实例并使用 update 方法更新
        config_schema = ConfigSchema()
        updated_config_schema = update(config_schema, legacy_dict)

        converted_config = updated_config_schema.to_pydantic_model()

        # 验证两个 Config 实例深度相等
        assert converted_config.model_dump_json(indent=2) == original_config.model_dump_json(indent=2), (
            "转换后的 Config 与原始 Config 不相等"
        )

    @pytest.mark.parametrize("test_round", range(5))
    def test_to_legacy_and_from_legacy_multiple_rounds(self, test_round):
        """测试多轮转换的稳定性"""
        # 生成随机 Config 实例
        original_config = generate_random_config()
        current_config = original_config

        # 进行多轮转换
        for i in range(3):
            # to_legacy -> from_legacy
            legacy_dict = current_config.to_legacy()
            config_schema = ConfigSchema()
            updated_config_schema = update(config_schema, legacy_dict)
            current_config = updated_config_schema.to_pydantic_model()
            # 每轮都应该与原始配置相等
            assert current_config.model_dump_json(indent=2) == original_config.model_dump_json(indent=2), (
                f"第 {i + 1} 轮转换后配置不一致"
            )

    def test_to_legacy_dict_compatibility(self):
        """测试 to_legacy 返回的 dict 与 ConfigSchema 字段兼容"""
        config = generate_random_config()
        legacy_dict = config.to_legacy()

        # 创建 ConfigSchema 实例
        config_schema = ConfigSchema()
        schema_fields = fields(config_schema)

        # 检查 legacy_dict 中的所有键都能被 ConfigSchema 接受
        for key in legacy_dict:
            schema_field = next((f for f in schema_fields if f.name == key), None)
            assert schema_field is not None, f"to_legacy 返回的 dict 中包含 ConfigSchema 中不存在的字段: {key}"
            assert type(legacy_dict[key]) is schema_field.type, (
                f"to_legacy 中的字段 {key} 类型不匹配: {type(legacy_dict[key])} != {type(getattr(config_schema, key))}"
            )

    def test_empty_lists_handling(self):
        """测试空列表的处理"""
        config = Config(
            folders=[],
            string=[],
            no_escape=[],
            clean_ext=[],
            media_type=[],
            sub_type=[],
            translate_config=TranslateConfig(),
        )

        legacy_dict = config.to_legacy()
        converted_config = Config.from_legacy(legacy_dict)

        assert converted_config.model_dump_json(indent=2) == config.model_dump_json(indent=2)

    def test_timedelta_conversion(self):
        """测试时间间隔的转换"""
        config = Config(
            timed_interval=timedelta(hours=2, minutes=30, seconds=45),
            rest_time=timedelta(minutes=5, seconds=10),
            translate_config=TranslateConfig(),
        )

        legacy_dict = config.to_legacy()

        # 检查时间格式
        assert legacy_dict["timed_interval"] == "02:30:45"
        assert legacy_dict["rest_time"] == "00:05:10"

        converted_config = Config.from_legacy(legacy_dict)
        assert converted_config.model_dump_json(indent=2) == config.model_dump_json(indent=2)

    def test_nested_model_conversion(self):
        """测试嵌套模型的转换"""
        translate_config = TranslateConfig(
            translate_by=[Translator.YOUDAO, Translator.GOOGLE],
            deepl_key="test_key",
            llm_url=HttpUrl("https://api.test.com/v1"),
            llm_model="test-model",
            llm_temperature=0.5,
        )

        config = Config(translate_config=translate_config)
        legacy_dict = config.to_legacy()

        # 检查嵌套模型字段被展开
        assert "translate_by" in legacy_dict
        assert "deepl_key" in legacy_dict
        assert "llm_url" in legacy_dict
        assert "translate_config" not in legacy_dict  # 嵌套模型本身不应该在结果中

        converted_config = Config.from_legacy(legacy_dict)
        assert converted_config.model_dump_json(indent=2) == config.model_dump_json(indent=2)

    def test_url_conversion(self):
        """测试 URL 的转换"""
        config = Config(
            emby_url=HttpUrl("https://emby.example.com:8096"),
            gfriends_github=HttpUrl("https://github.com/test/repo"),
            translate_config=TranslateConfig(),
        )

        legacy_dict = config.to_legacy()

        # URL 应该被转换为字符串
        assert isinstance(legacy_dict["emby_url"], str)
        assert isinstance(legacy_dict["gfriends_github"], str)

        converted_config = Config.from_legacy(legacy_dict)
        assert converted_config.model_dump_json(indent=2) == config.model_dump_json(indent=2)

    def test_enum_conversion(self):
        """测试枚举值的转换"""
        config = Config(
            website_single=Website.JAVBUS,
            read_mode=[ReadMode.HAS_NFO_UPDATE, ReadMode.NO_NFO_SCRAPE],
            mark_type=[MarkType.SUB, MarkType.HD],
        )

        legacy_dict = config.to_legacy()

        # 枚举应该被转换为值字符串
        assert legacy_dict["website_single"] == "javbus"
        assert "has_nfo_update" in str(legacy_dict["read_mode"])
        assert "sub" in str(legacy_dict["mark_type"])

        converted_config = Config.from_legacy(legacy_dict)
        assert converted_config.model_dump_json(indent=2) == config.model_dump_json(indent=2)
