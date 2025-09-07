import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()
app = typer.Typer(help="生成 changelog", context_settings={"help_option_names": ["-h", "--help"]})


def run_git_command(command: list[str]) -> str:
    """运行git命令并返回输出"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        console.print(f"[red]执行git命令失败: {' '.join(command)}[/red]")
        console.print(f"[red]错误信息: {e.stderr}[/red]")
        raise typer.Exit(1)


def get_latest_tag(pattern: str) -> str | None:
    """获取匹配模式的最新tag"""
    command = ["git", "tag", "-l", pattern, "--sort=-v:refname"]
    output = run_git_command(command)

    if not output:
        return None

    # 返回第一行（最新的tag）
    return output.split("\n")[0]


def get_commit_log(from_tag: str) -> str:
    """获取从指定tag到HEAD的提交日志"""
    command = ["git", "log", "--pretty=format:%h %s", f"{from_tag}..HEAD"]
    return run_git_command(command)


def generate_changelog(commit_log: str, output_file: Path) -> None:
    """生成changelog内容并写入文件"""
    changelog_content = f"""## 新增
*

## 修复
*

<details>
<summary>Full Changelog</summary>

{commit_log}

</details>"""

    try:
        output_file.write_text(changelog_content, encoding="utf-8")
        console.print(f"[green]✓ Changelog已生成到: {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]写入文件失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def main(
    pattern: Annotated[str, typer.Option("--pattern", "-p", help="Git tag匹配模式")] = "220*",
    output: Annotated[str, typer.Option("--output", "-o", help="输出文件路径")] = "changelog.md",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="显示详细信息")] = False,
) -> None:
    """
    生成changelog文件

    从最新的匹配tag到HEAD的提交记录生成changelog
    """

    # 将字符串路径转换为Path对象
    output_path = Path(output)

    if verbose:
        console.print(
            Panel(
                f"[cyan]Tag模式:[/cyan] {pattern}\n[cyan]输出文件:[/cyan] {output_path}",
                title="配置信息",
                border_style="blue",
            )
        )

    # 获取最新的匹配tag
    console.print(f"[yellow]正在查找匹配模式 '{pattern}' 的最新tag...[/yellow]")
    latest_tag = get_latest_tag(pattern)

    if not latest_tag:
        console.print(f"[red]未找到匹配模式 '{pattern}' 的tag[/red]")
        raise typer.Exit(1)

    console.print(f"[green]找到最新tag: {latest_tag}[/green]")

    # 获取提交日志
    console.print(f"[yellow]正在获取从 {latest_tag} 到 HEAD 的提交记录...[/yellow]")
    commit_log = get_commit_log(latest_tag)

    if verbose and commit_log:
        console.print("\n[cyan]提交记录预览:[/cyan]")
        # 显示前5条记录作为预览
        preview_lines = commit_log.split("\n")[:5]
        for line in preview_lines:
            console.print(f"  {line}")
        if len(commit_log.split("\n")) > 5:
            console.print(f"  ... 还有 {len(commit_log.split('\n')) - 5} 条记录")
        console.print()

    # 生成changelog
    console.print(f"[yellow]正在生成changelog到 {output_path}...[/yellow]")
    generate_changelog(commit_log, output_path)

    # 显示成功信息
    success_text = Text("🎉 Changelog生成完成!", style="bold green")
    console.print(Panel(success_text, border_style="green"))


if __name__ == "__main__":
    app()
