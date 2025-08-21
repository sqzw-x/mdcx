import json
from dataclasses import fields
from datetime import timedelta

import pytest
from pydantic import HttpUrl

from mdcx.config.manager import ConfigV1
from mdcx.config.models import (
    COMPAT_RULES,
    Config,
    MarkType,
    ReadMode,
    Remove,
    TranslateConfig,
    Translator,
    Website,
)
from tests.random_generator import generate_random_pydantic_instance


def generate_random_config() -> Config:
    """生成具有随机字段值的 Config 实例"""
    r = generate_random_pydantic_instance(
        Config,
        no_default=True,
        allow_default=[
            "website_set",
            "headless_browser_sites",
        ],
    )
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
    """
    测试 Config 与 ConfigV1 之间的转换.

    Config 的语义是 ConfigV1 的超集, 因此只需保证转换过程中 ConfigV1 的信息不会丢失.
    """

    def test_to_legacy(self):
        """测试 to_legacy 返回的 dict 包含且仅包含 ConfigV1 中的所有字段, 且类型正确."""
        config = generate_random_config()
        res = config.to_legacy()
        res_names = set(res.keys())

        v1 = ConfigV1()
        v1_fields = fields(v1)
        v1_fields = {f.name: f for f in v1_fields}
        v1_names = set(v1_fields.keys())

        # 特殊处理 ConfigV1 中 *_website 字段
        assert res_names - {f"{w}_website" for w in Website} - v1_names == set(), (
            "to_legacy 返回值冗余字段 (与 ConfigV1 相比)"
        )
        # Config 中已标记移除的字段
        removed = {r.name for r in COMPAT_RULES if isinstance(r, Remove)}
        assert v1_names - removed - res_names == set(), "to_legacy 返回值缺少字段 (与 ConfigV1 相比)"

        for key in res:
            if key in {f"{w}_website" for w in Website}:
                continue
            assert type(res[key]) is v1_fields[key].type, (
                f"to_legacy 和 ConfigV1 的字段 {key} 类型不匹配: to_legacy={type(res[key])}, ConfigV1={type(getattr(v1, key))}"
            )

    @pytest.mark.parametrize("test_round", range(5))
    def test_convert(self, test_round):
        """测试转换不会造成 ConfigV1 上的字段丢失."""

        # 生成随机 ConfigV1. 这依赖于 generate_random_config 和 to_legacy 的正确性.
        random_config = generate_random_config()
        legacy_1 = random_config.to_legacy()
        v1 = ConfigV1()
        v1.__dict__.update(legacy_1)

        # 将 ConfigV1 转换回 Config, back_config 可能与 random_config 不同
        back_config = v1.to_pydantic_model()
        legacy_2 = back_config.to_legacy()
        assert json.dumps(legacy_1, indent=2) == json.dumps(legacy_2, indent=2), (
            "转换后的 ConfigV1 与原始 ConfigV1 不相等"
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
