import json
from datetime import datetime
from pathlib import Path
from typing import Any, NotRequired, TypedDict

import pytest
from aiofiles import open as aio_open
from parsel import Selector

from mdcx.config.manager import asdict
from mdcx.crawlers.base import Context, CrawlerData, DetailPageParser, NotSupport
from mdcx.models.types import CrawlerInput, Language


class TestCase(TypedDict):
    last_updated: str
    url: str
    run_test: bool
    result_file: str
    description: str
    ctx: NotRequired[dict]  # used to build ctx


class ParserTestBase:
    """基础解析器测试类"""

    def __init__(self, parser_name: str, parser_class: type[DetailPageParser], overwrite: bool):
        self.parser_name = parser_name
        self.parser_class = parser_class
        self.overwrite = overwrite

    @property
    def test_data_dir(self) -> Path:
        """测试数据目录"""
        return Path(__file__).parent / "data" / self.parser_name

    @property
    def cases_json_path(self) -> Path:
        """files.json 文件路径"""
        return self.test_data_dir / "cases.json"

    async def run_all_tests(self) -> bool:
        """运行所有测试"""
        print(f"开始运行 {self.parser_name} 解析器测试...")

        html_files = self.scan_html_files()
        if not html_files:
            pytest.skip("未找到 HTML 测试文件")

        cases = self.load_cases()

        test_results = []

        for html_file in html_files:
            file_key = html_file.name
            if file_key not in cases:
                cases[file_key] = self.new_case(html_file)
            file_info = cases[file_key]

            # 检查是否需要运行测试
            if not file_info["run_test"]:
                print(f"跳过测试: {html_file.name}")
                continue

            # 运行测试
            result = await self.run_one_test(html_file, file_info)
            test_results.append(result)

        self.save_cases(cases)

        # 统计结果
        total_tests = len(test_results)
        passed_tests = sum(test_results)
        failed_tests = total_tests - passed_tests

        print(f"\n测试完成: 总计 {total_tests}, 通过 {passed_tests}, 失败 {failed_tests}")

        return failed_tests == 0

    async def run_one_test(self, html_file: Path, case_data: TestCase) -> bool:
        """运行单个 HTML 文件的回归测试"""
        result_file = self.test_data_dir / case_data["result_file"]

        # 解析 HTML 文件
        try:
            actual_result = await self.run_parser(html_file, case_data)
            actual_dict = self.serialize_result(actual_result)
        except Exception as e:
            print(f"解析 {html_file.name} 时出错: {e}")
            return False

        # 加载期望结果
        expected_dict = self.load_expected_result(result_file)

        # 如果没有期望结果或覆盖, 则保存实际结果
        if not expected_dict or self.overwrite:
            self.save_result(result_file, actual_dict)
            print(f"保存新结果: {html_file.name} -> {result_file.name}")
            return True

        # 比较结果
        differences = self.compare_results(actual_dict, expected_dict)

        if differences:
            print(f"回归测试失败: {self.test_data_dir / result_file.name}")
            for diff in differences:
                print(f"  - {diff}")
            return False
        else:
            print(f"回归测试通过: {self.test_data_dir / result_file.name}")
            return True

    async def run_parser(self, html_file: Path, case_data: TestCase):
        """解析 HTML 文件并返回结果"""
        async with aio_open(html_file, encoding="utf-8") as f:
            html_content = await f.read()

        selector = Selector(text=html_content)
        parser = self.parser_class()

        # 创建一个简单的上下文用于测试 # todo 从 case_data 创建
        ctx = Context(
            input=CrawlerInput(
                appoint_number="",
                appoint_url="",
                file_path="",
                mosaic="",
                number="",
                short_number="",
                language=Language.UNDEFINED,
                org_language=Language.UNDEFINED,
            )
        )

        return await parser.parse(ctx, selector)

    def load_cases(self) -> dict[str, TestCase]:
        files_json_path = self.cases_json_path
        if files_json_path.exists():
            return json.loads(files_json_path.read_text(encoding="utf-8"))
        else:
            files_json_path.parent.mkdir(parents=True, exist_ok=True)
        return {}

    def new_case(self, html_file: Path) -> TestCase:
        return {
            "last_updated": datetime.now().isoformat(),
            "url": "",
            "run_test": True,
            "result_file": html_file.with_suffix(".json").name,
            "description": "",
            "ctx": {},
        }

    def save_cases(self, data: dict[str, Any]) -> None:
        files_json_path = self.cases_json_path
        files_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(files_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def scan_html_files(self) -> list[Path]:
        """扫描测试数据目录中的所有 HTML 文件"""
        test_data_dir = self.test_data_dir
        if not test_data_dir.exists():
            test_data_dir.mkdir(parents=True, exist_ok=True)
            return []
        return list(test_data_dir.glob("*.html"))

    def load_expected_result(self, result_file: Path) -> dict[str, Any] | None:
        """加载期望的结果"""
        if not result_file.exists():
            return None
        return json.loads(result_file.read_text(encoding="utf-8"))

    def serialize_result(self, data: CrawlerData) -> dict[str, Any]:
        """将 CrawlerResult 序列化为字典"""
        result: dict[str, Any] = {"not_support": []}  # 标记解析器不支持的字段
        for key, value in asdict(data).items():
            if not isinstance(value, NotSupport):
                result[key] = value
            else:
                result["not_support"].append(key)
        return result

    def save_result(self, result_file: Path, result: dict[str, Any]) -> None:
        """保存结果到文件"""
        result_file.parent.mkdir(parents=True, exist_ok=True)
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    def compare_results(self, actual: dict[str, Any], expected: dict[str, Any]) -> list[str]:
        """比较实际结果和期望结果，返回差异列表"""
        differences = []

        # 检查 key 不匹配
        actual_keys = set(actual.keys())
        expected_keys = set(expected.keys())
        if actual_keys - expected_keys:
            differences.append(f"出现在实际结果中, 但不在期望结果中的字段: {actual_keys - expected_keys}")
        if expected_keys - actual_keys:
            differences.append(f"出现在期望结果中, 但不在实际结果中的字段: {expected_keys - actual_keys}")

        # 检查共同字段
        all_keys = actual_keys & expected_keys

        for key in all_keys:
            actual_value = actual.get(key)
            expected_value = expected.get(key)

            if actual_value != expected_value:
                differences.append(f"字段 '{key}': 期望 '{expected_value}', 实际 '{actual_value}'")

        return differences
