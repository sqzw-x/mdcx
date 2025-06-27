#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML 映射表过滤脚本
过滤掉无信息的行，即：
1. zh_cn、zh_tw、jp三个字段内容完全相同
2. keyword中只包含一个关键词（即只有逗号分隔的一个词）且也相同
"""

import argparse
import os
import xml.etree.ElementTree as ET
from typing import Optional, Tuple


def count_keywords(keyword_string: str) -> int:
    """
    计算keyword字符串中包含的关键词数量
    keyword格式：,word1,word2,word3,
    """
    if not keyword_string:
        return 0

    # 移除首尾的逗号，然后按逗号分割
    keywords = keyword_string.strip(",").split(",")
    # 过滤空字符串
    keywords = [k.strip() for k in keywords if k.strip()]
    return len(keywords)


def is_redundant_entry(element) -> bool:
    """
    判断是否为无信息的条目
    条件：
    1. zh_cn、zh_tw、jp三个字段内容完全相同
    2. keyword中只包含一个关键词
    """
    zh_cn = element.get("zh_cn", "").strip()
    zh_tw = element.get("zh_tw", "").strip()
    jp = element.get("jp", "").strip()
    keyword = element.get("keyword", "").strip()

    # 检查三个语言字段是否完全相同
    if not (zh_cn == zh_tw == jp):
        return False

    # 检查keyword是否只有一个关键词
    keyword_count = count_keywords(keyword)
    if keyword_count != 1:
        return False

    # 进一步检查：keyword中的唯一关键词是否与zh_cn相同
    if keyword_count == 1:
        clean_keyword = keyword.strip(",").strip()
        if clean_keyword == zh_cn:
            return True

    return False


def filter_xml_file(input_file: str, output_file: Optional[str] = None, backup: bool = True) -> Tuple[int, int]:
    """
    过滤XML文件中的无信息条目

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径，如果为None则覆盖原文件
        backup: 是否创建备份文件

    Returns:
        (total_count, filtered_count): 总条目数和被过滤的条目数
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"输入文件不存在: {input_file}")

    # 创建备份
    if backup:
        backup_file = input_file + ".backup"
        print(f"创建备份文件: {backup_file}")
        with open(input_file, "r", encoding="utf-8") as src, open(backup_file, "w", encoding="utf-8") as dst:
            dst.write(src.read())

    # 解析XML文件
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"XML解析错误: {e}")

    # 统计信息
    total_count = 0
    filtered_count = 0
    redundant_entries = []

    # 找出所有演员条目
    for actor_elem in root.findall("a"):
        total_count += 1
        if is_redundant_entry(actor_elem):
            filtered_count += 1
            redundant_entries.append(actor_elem)

            # 打印被过滤的条目信息
            zh_cn = actor_elem.get("zh_cn", "")
            keyword = actor_elem.get("keyword", "")
            print(f"过滤: {zh_cn} (keyword: {keyword})")

    # 移除无信息的条目
    for elem in redundant_entries:
        root.remove(elem)

    # 确定输出文件
    if output_file is None:
        output_file = input_file

    # 保存过滤后的XML
    tree.write(output_file, encoding="utf-8", xml_declaration=True)

    # 格式化输出，保持原始格式
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 简单的格式化：在每个<a>标签前添加缩进
    content = content.replace("<a ", "  <a ")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    return total_count, filtered_count


def main():
    parser = argparse.ArgumentParser(description="过滤 XML 映射表文件中的无信息条目")
    parser.add_argument("input_file", help="输入的 XML 文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径（默认覆盖原文件）")
    parser.add_argument("--no-backup", action="store_true", help="不创建备份文件")
    parser.add_argument("--dry-run", action="store_true", help="只显示会被过滤的条目，不实际修改文件")

    args = parser.parse_args()

    try:
        if args.dry_run:
            # 干运行模式：只分析不修改
            print("=== 干运行模式：分析无信息条目 ===")
            tree = ET.parse(args.input_file)
            root = tree.getroot()

            total_count = 0
            filtered_count = 0

            for actor_elem in root.findall("a"):
                total_count += 1
                if is_redundant_entry(actor_elem):
                    filtered_count += 1
                    zh_cn = actor_elem.get("zh_cn", "")
                    keyword = actor_elem.get("keyword", "")
                    href = actor_elem.get("href", "")
                    print(f"将被过滤: {zh_cn} (keyword: {keyword} href: {href})")

            print("\n分析结果：")
            print(f"总条目数: {total_count}")
            print(f"无信息条目数: {filtered_count}")
            print(f"过滤率: {filtered_count / total_count * 100:.2f}%")

        else:
            # 实际过滤
            print("=== 开始过滤XML文件 ===")
            total_count, filtered_count = filter_xml_file(args.input_file, args.output, backup=not args.no_backup)

            print("\n过滤完成：")
            print(f"总条目数: {total_count}")
            print(f"过滤的无信息条目数: {filtered_count}")
            print(f"剩余条目数: {total_count - filtered_count}")
            print(f"过滤率: {filtered_count / total_count * 100:.2f}%")

            output_file = args.output or args.input_file
            print(f"结果保存到: {output_file}")

    except Exception as e:
        print(f"错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
