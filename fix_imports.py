#!/usr/bin/env python3
"""
修复项目中的导入语句，将同级和上一级的导入改为相对导入
"""

import re
from pathlib import Path


def fix_imports_in_file(file_path: Path, project_root: Path):
    """修复单个文件中的导入语句"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"无法读取文件 {file_path}: {e}")
        return False

    # 计算当前文件相对于项目根目录的路径
    rel_path = file_path.relative_to(project_root)
    current_dir_parts = rel_path.parent.parts

    # 获取当前目录层级
    depth = len(current_dir_parts)

    original_content = content
    lines = content.split("\n")
    modified = False

    for i, line in enumerate(lines):
        # 匹配 from mdcx.xxx import yyy 格式的导入
        match = re.match(r"^(\s*)from\s+mdcx\.([a-zA-Z0-9_.]+)\s+import\s+(.+)$", line)
        if not match:
            continue

        indent, module_path, import_items = match.groups()
        module_parts = module_path.split(".")

        # 判断是否需要修改为相对导入
        new_import = None

        if depth == 1:  # 在 mdcx/ 下的文件
            # 同级导入使用 .
            if len(module_parts) == 1:
                new_import = f"{indent}from .{module_parts[0]} import {import_items}"
            # 子目录导入使用 .
            elif module_parts[0] in current_dir_parts or len(module_parts) > 1:
                new_import = f"{indent}from .{'.'.join(module_parts)} import {import_items}"

        elif depth == 2:  # 在 mdcx/subdir/ 下的文件
            current_subdir = current_dir_parts[1]

            if len(module_parts) == 1:
                # 导入顶级模块，使用 ..
                new_import = f"{indent}from ..{module_parts[0]} import {import_items}"
            elif module_parts[0] == current_subdir:
                # 同级导入，使用 .
                if len(module_parts) == 1:
                    new_import = f"{indent}from . import {import_items}"
                else:
                    new_import = f"{indent}from .{'.'.join(module_parts[1:])} import {import_items}"
            else:
                # 其他子目录或顶级，使用 ..
                new_import = f"{indent}from ..{'.'.join(module_parts)} import {import_items}"

        elif depth == 3:  # 在 mdcx/subdir/subsubdir/ 下的文件
            current_subdir = current_dir_parts[1]
            current_subsubdir = current_dir_parts[2]

            if len(module_parts) >= 2 and module_parts[0] == current_subdir and module_parts[1] == current_subsubdir:
                # 同级导入
                if len(module_parts) == 2:
                    new_import = f"{indent}from . import {import_items}"
                else:
                    new_import = f"{indent}from .{'.'.join(module_parts[2:])} import {import_items}"
            elif len(module_parts) >= 1 and module_parts[0] == current_subdir:
                # 上一级导入
                if len(module_parts) == 1:
                    new_import = f"{indent}from .. import {import_items}"
                else:
                    new_import = f"{indent}from ..{'.'.join(module_parts[1:])} import {import_items}"
            else:
                # 保持绝对导入（太远的路径）
                continue

        # 应用修改
        if new_import and new_import != line:
            lines[i] = new_import
            modified = True
            print(f"  {file_path.name}: {line.strip()} -> {new_import.strip()}")

    if modified:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True
        except Exception as e:
            print(f"无法写入文件 {file_path}: {e}")
            return False

    return False


def main():
    project_root = Path(__file__).parent
    mdcx_dir = project_root / "mdcx"

    if not mdcx_dir.exists():
        print("未找到 mdcx 目录")
        return

    # 查找所有 Python 文件
    python_files = list(mdcx_dir.rglob("*.py"))

    print(f"找到 {len(python_files)} 个 Python 文件")

    modified_count = 0
    for file_path in python_files:
        # 跳过 __pycache__ 目录
        if "__pycache__" in str(file_path):
            continue

        print(f"处理: {file_path.relative_to(project_root)}")
        if fix_imports_in_file(file_path, project_root):
            modified_count += 1

    print(f"修改了 {modified_count} 个文件")


if __name__ == "__main__":
    main()
