import pytest

from mdcx.config.models import Website


def pytest_addoption(parser: pytest.Parser):
    """添加自定义命令行参数"""
    g1 = parser.getgroup("parsers", "parser test options")
    g1.addoption("--overwrite", action="store_true", help="覆盖现有的测试结果")
    g1.addoption("--parser-name", nargs="+", help="指定解析器名称")
    g2 = parser.getgroup("crawler", "crawler test options")
    g2.addoption("--network", action="store_true", help="允许网络请求")
    g2.addoption("--site", nargs="+", help="指定网站")


@pytest.fixture
def overwrite(request: pytest.FixtureRequest) -> bool:
    """通过命令行参数 --overwrite 以覆盖现有的测试结果"""
    return request.config.getoption("--overwrite", default=False)


@pytest.fixture
def parser_names(request: pytest.FixtureRequest) -> list[str]:
    """通过命令行参数 --parser-name 指定只在部分解析器上运行测试"""
    names = request.config.getoption("--parser-name", default=[])
    return names


@pytest.fixture
def network(request: pytest.FixtureRequest) -> bool:
    """通过命令行参数 --network 允许网络请求"""
    return request.config.getoption("--network", default=False)


@pytest.fixture
def sites(request: pytest.FixtureRequest) -> list[Website]:
    """通过命令行参数 --site 指定网站"""
    sites = request.config.getoption("--site", default=[])
    sites = sites if isinstance(sites, list) else [sites] if sites else []
    for site in sites:
        if site.upper() not in Website.__members__:
            raise ValueError(f"Invalid site: {site}. Available sites: {[s.name for s in Website]}")
    return [Website[site.upper()] for site in sites]
