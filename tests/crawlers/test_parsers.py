import pytest

from mdcx.crawlers import dmm_new
from tests.crawlers.parser import ParserTestBase


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name, parser_class",
    [
        ("dmm/mono", dmm_new.Parser),
        ("dmm/video", dmm_new.Parser1),
    ],
)
async def test_parsers(name, parser_class, overwite, parser_names):
    if parser_names and name not in parser_names:
        pytest.skip(f"跳过解析器: {name}")
    t = ParserTestBase(name, parser_class, overwite)
    result = await t.run_all_tests()
    assert result, "所有测试应该通过"
