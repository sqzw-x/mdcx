from mdcx.crawlers import dmm_new
from tests.crawlers.parser import ParserTestBase


class TestDmmParser(ParserTestBase):
    @property
    def parser_name(cls) -> str:
        return "dmm/mono"

    @property
    def parser_class(self):
        return dmm_new.Parser
