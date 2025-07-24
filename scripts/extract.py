#!/usr/bin/env python3
r"""
文件行提取工具 - CLI 版本
从输入文件中提取符合指定标准的行并输出到目标文件

使用示例:
    python extract.py input.txt output.txt --pattern "*.jpg"
    python extract.py input.txt output.txt --regex "^\d+\."
    python extract.py input.txt output.txt --contains "error"
    python extract.py input.txt output.txt --min-length 10 --max-length 100
"""

import argparse
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path


class LineExtractor:
    """行提取器类"""

    def __init__(self):
        self.filters: list[Callable[[str], bool]] = []

    def add_pattern_filter(self, pattern: str):
        """添加通配符模式过滤器"""
        import fnmatch

        def pattern_filter(line: str) -> bool:
            return fnmatch.fnmatch(line.strip(), pattern)

        self.filters.append(pattern_filter)

    def add_regex_filter(self, regex_pattern: str):
        """添加正则表达式过滤器"""
        compiled_regex = re.compile(regex_pattern)

        def regex_filter(line: str) -> bool:
            return bool(compiled_regex.search(line.strip()))

        self.filters.append(regex_filter)

    def add_contains_filter(self, text: str, case_sensitive: bool = True):
        """添加包含文本过滤器"""
        if not case_sensitive:
            text = text.lower()

        def contains_filter(line: str) -> bool:
            search_line = line.strip() if case_sensitive else line.strip().lower()
            return text in search_line

        self.filters.append(contains_filter)

    def add_length_filter(self, min_length=None, max_length=None):
        """添加行长度过滤器"""

        def length_filter(line: str) -> bool:
            line_length = len(line.strip())
            if min_length is not None and line_length < min_length:
                return False
            if max_length is not None and line_length > max_length:
                return False
            return True

        self.filters.append(length_filter)

    def add_starts_with_filter(self, prefix: str, case_sensitive: bool = True):
        """添加以指定前缀开头的过滤器"""
        if not case_sensitive:
            prefix = prefix.lower()

        def starts_with_filter(line: str) -> bool:
            search_line = line.strip() if case_sensitive else line.strip().lower()
            return search_line.startswith(prefix)

        self.filters.append(starts_with_filter)

    def add_ends_with_filter(self, suffix: str, case_sensitive: bool = True):
        """添加以指定后缀结尾的过滤器"""
        if not case_sensitive:
            suffix = suffix.lower()

        def ends_with_filter(line: str) -> bool:
            search_line = line.strip() if case_sensitive else line.strip().lower()
            return search_line.endswith(suffix)

        self.filters.append(ends_with_filter)

    def add_empty_filter(self, exclude_empty: bool = True):
        """添加空行过滤器"""

        def empty_filter(line: str) -> bool:
            is_empty = len(line.strip()) == 0
            return not is_empty if exclude_empty else is_empty

        self.filters.append(empty_filter)

    def matches_line(self, line: str) -> bool:
        """检查行是否匹配所有过滤器"""
        if not self.filters:
            return True  # 如果没有过滤器，则匹配所有行

        return all(filter_func(line) for filter_func in self.filters)

    def extract_lines(self, input_file: str, output_file: str, encoding: str = "utf-8") -> dict:
        """从输入文件提取匹配的行到输出文件"""
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"输入文件不存在: {input_file}")

        # 确保输出目录存在
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        matched_lines = []
        total_lines = 0

        try:
            with open(input_file, encoding=encoding) as infile:
                for line_num, line in enumerate(infile, 1):
                    total_lines += 1
                    if self.matches_line(line):
                        matched_lines.append(line)

            with open(output_file, "w", encoding=encoding) as outfile:
                outfile.writelines(matched_lines)

            return {"total_lines": total_lines, "matched_lines": len(matched_lines), "output_file": output_file}

        except UnicodeDecodeError as e:
            raise ValueError(f"文件编码错误，请尝试其他编码格式: {e}")


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="从文件中提取符合指定标准的行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
使用示例:
  %(prog)s input.txt output.txt --pattern "*.jpg"
  %(prog)s input.txt output.txt --regex "^\d+\."
  %(prog)s input.txt output.txt --contains "error" --case-insensitive
  %(prog)s input.txt output.txt --min-length 10 --max-length 100
  %(prog)s input.txt output.txt --starts-with "http" --exclude-empty
        """,
    )

    # 必需参数
    parser.add_argument("input_file", help="输入文件路径")
    parser.add_argument("output_file", help="输出文件路径")

    # 过滤选项
    parser.add_argument("--pattern", help="通配符模式匹配 (例如: *.jpg, test*)")
    parser.add_argument("--regex", help="正则表达式模式匹配")
    parser.add_argument("--contains", help="包含指定文本的行")
    parser.add_argument("--starts-with", help="以指定文本开头的行")
    parser.add_argument("--ends-with", help="以指定文本结尾的行")

    # 长度过滤
    parser.add_argument("--min-length", type=int, help="最小行长度")
    parser.add_argument("--max-length", type=int, help="最大行长度")

    # 布尔选项
    parser.add_argument(
        "--case-insensitive", action="store_true", help="忽略大小写 (适用于 contains, starts-with, ends-with)"
    )
    parser.add_argument("--exclude-empty", action="store_true", help="排除空行")
    parser.add_argument("--only-empty", action="store_true", help="只保留空行")

    # 其他选项
    parser.add_argument("--encoding", default="utf-8", help="文件编码格式 (默认: utf-8)")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细输出")

    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    # 验证参数
    if args.only_empty and args.exclude_empty:
        print("错误: --only-empty 和 --exclude-empty 选项不能同时使用", file=sys.stderr)
        sys.exit(1)

    # 创建提取器
    extractor = LineExtractor()

    # 添加过滤器
    if args.pattern:
        extractor.add_pattern_filter(args.pattern)
        if args.verbose:
            print(f"添加通配符过滤器: {args.pattern}")

    if args.regex:
        try:
            extractor.add_regex_filter(args.regex)
            if args.verbose:
                print(f"添加正则表达式过滤器: {args.regex}")
        except re.error as e:
            print(f"错误: 无效的正则表达式 '{args.regex}': {e}", file=sys.stderr)
            sys.exit(1)

    if args.contains:
        extractor.add_contains_filter(args.contains, not args.case_insensitive)
        if args.verbose:
            case_info = "（忽略大小写）" if args.case_insensitive else "（区分大小写）"
            print(f"添加包含文本过滤器: {args.contains} {case_info}")

    if args.starts_with:
        extractor.add_starts_with_filter(args.starts_with, not args.case_insensitive)
        if args.verbose:
            case_info = "（忽略大小写）" if args.case_insensitive else "（区分大小写）"
            print(f"添加开头文本过滤器: {args.starts_with} {case_info}")

    if args.ends_with:
        extractor.add_ends_with_filter(args.ends_with, not args.case_insensitive)
        if args.verbose:
            case_info = "（忽略大小写）" if args.case_insensitive else "（区分大小写）"
            print(f"添加结尾文本过滤器: {args.ends_with} {case_info}")

    if args.min_length is not None or args.max_length is not None:
        extractor.add_length_filter(args.min_length, args.max_length)
        if args.verbose:
            length_info = []
            if args.min_length is not None:
                length_info.append(f"最小长度: {args.min_length}")
            if args.max_length is not None:
                length_info.append(f"最大长度: {args.max_length}")
            print(f"添加长度过滤器: {', '.join(length_info)}")

    if args.exclude_empty:
        extractor.add_empty_filter(exclude_empty=True)
        if args.verbose:
            print("添加空行过滤器: 排除空行")
    elif args.only_empty:
        extractor.add_empty_filter(exclude_empty=False)
        if args.verbose:
            print("添加空行过滤器: 只保留空行")

    # 执行提取
    try:
        if args.verbose:
            print(f"\n开始处理文件: {args.input_file}")

        result = extractor.extract_lines(args.input_file, args.output_file, args.encoding)

        print("处理完成!")
        print(f"总行数: {result['total_lines']}")
        print(f"匹配行数: {result['matched_lines']}")
        print(f"匹配率: {result['matched_lines'] / result['total_lines'] * 100:.1f}%")
        print(f"输出文件: {result['output_file']}")

    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
