import pytest


def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--overwite", action="store_true", help="覆盖现有的测试结果")
    parser.addoption("--name", nargs="+", help="指定解析器名称")


@pytest.fixture
def overwite(request: pytest.FixtureRequest) -> bool:
    """通过命令行参数 --overwite 以覆盖现有的测试结果"""
    print("overwite:", request.config.getoption("--overwite", default=False))
    return request.config.getoption("--overwite", default=False)


@pytest.fixture
def parser_names(request: pytest.FixtureRequest) -> list[str]:
    """通过命令行参数 --name 指定只在部分解析器上运行测试"""
    names = request.config.getoption("--name", default=[])
    return names
