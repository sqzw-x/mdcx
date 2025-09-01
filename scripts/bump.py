import re
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

app = typer.Typer(
    name="bump",
    help="MDCx 版本号管理工具",
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def get_project_root() -> Path:
    """获取项目根目录"""
    current = Path(__file__).resolve()
    # 从 scripts/bump.py 往上找到项目根目录
    while current.parent != current:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("无法找到项目根目录（包含 pyproject.toml 的目录）")


def get_consts_file() -> Path:
    """获取 consts.py 文件路径"""
    project_root = get_project_root()
    consts_file = project_root / "mdcx" / "consts.py"
    if not consts_file.exists():
        raise FileNotFoundError(f"找不到 consts.py 文件: {consts_file}")
    return consts_file


def get_current_version() -> int:
    """从 consts.py 中获取当前版本号"""
    consts_file = get_consts_file()
    content = consts_file.read_text(encoding="utf-8")

    # 匹配 LOCAL_VERSION = 数字
    match = re.search(r"LOCAL_VERSION\s*=\s*(\d+)", content)
    if not match:
        raise ValueError("在 consts.py 中找不到 LOCAL_VERSION")

    return int(match.group(1))


def update_version(new_version: int) -> None:
    """更新 consts.py 中的版本号"""
    consts_file = get_consts_file()
    content = consts_file.read_text(encoding="utf-8")

    # 替换版本号
    pattern = r"(LOCAL_VERSION\s*=\s*)\d+"
    replacement = rf"\g<1>{new_version}"
    new_content = re.sub(pattern, replacement, content)

    if new_content == content:
        raise ValueError("版本号替换失败，请检查 consts.py 文件格式")

    consts_file.write_text(new_content, encoding="utf-8")


@app.command()
def main(
    version: Annotated[int | None, typer.Option("--version", "-v", help="新版本号")] = None,
    increment: Annotated[int, typer.Option("--increment", "-i", help="版本号增量")] = 1,
    dry_run: Annotated[bool, typer.Option("--dry-run", "-n", help="预览模式")] = False,
    force: Annotated[bool, typer.Option("--force", "-f", help="强制执行")] = False,
) -> None:
    """
    更新 LOCAL_VERSION 版本号

    [bold green]示例:[/bold green]

    • [cyan]python bump.py[/cyan] - 版本号 +1
    • [cyan]python bump.py --version 220250902[/cyan] - 设置为指定版本号
    • [cyan]python bump.py --increment 10[/cyan] - 版本号 +10
    • [cyan]python bump.py --dry-run[/cyan] - 预览模式
    """
    try:
        # 获取当前版本号
        current_version = get_current_version()

        # 计算新版本号
        if version is not None:
            new_version = version
        else:
            new_version = current_version + increment

        # 显示版本信息
        console.print(
            Panel.fit(
                f"[bold]当前版本:[/bold] [yellow]{current_version}[/yellow]\n"
                f"[bold]新版本:[/bold] [green]{new_version}[/green]",
                title="[bold blue]版本信息[/bold blue]",
                border_style="blue",
            )
        )

        if new_version == current_version:
            console.print("[yellow]版本号没有变化，无需更新[/yellow]")
            return

        if dry_run:
            console.print("[cyan]预览模式：不会实际修改文件[/cyan]")
            return

        # 确认操作
        if not force:
            if not Confirm.ask(f"确认将版本号从 {current_version} 更新为 {new_version}？"):
                console.print("[yellow]操作已取消[/yellow]")
                return

        # 更新版本号
        update_version(new_version)

        console.print(
            Panel.fit(
                f"[bold green]✓[/bold green] 版本号已成功更新：[yellow]{current_version}[/yellow] → [green]{new_version}[/green]",
                title="[bold green]更新完成[/bold green]",
                border_style="green",
            )
        )

        # 显示文件路径
        consts_file = get_consts_file()
        console.print(f"[dim]已修改文件: {consts_file}[/dim]")

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]错误:[/bold red] {e}", title="[bold red]操作失败[/bold red]", border_style="red")
        )
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
