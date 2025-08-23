from mdcx.config.enums import Website
from mdcx.config.models import Config
from mdcx.config.v1 import ConfigV1
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


def test_from_legacy():
    """测试从旧版配置转换为新版配置"""
    config_v1 = ConfigV1()
    config_v1.wuma_style = "test_value"
    config_v1.javdb_website = "https://test.com"  # type: ignore

    config = Config.from_legacy(config_v1.__dict__.copy())

    assert Website.JAVDB in config.site_configs
    assert config.get_site_url(Website.JAVDB) == "https://test.com"
    assert config.wuma_style == "test_value"
