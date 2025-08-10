import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from mdcx.config.manager import config
from mdcx.config.models import Website
from mdcx.consts import ManualConfig
from mdcx.crawlers.base import get_crawler
from mdcx.models.types import CrawlerInput
from mdcx.web_async import AsyncWebClient

app = typer.Typer(help="获取网站详情页")
console = Console()


def get_available_sites() -> list[str]:
    """获取所有可用的网站列表"""
    from mdcx.crawlers.base.base import crawler_registry

    return [site.value for site in crawler_registry.keys()]


@app.command()
def fetch(
    url: Annotated[str, typer.Argument(help="要抓取的详情页URL")],
    site: Annotated[str | None, typer.Option("--site", "-s", help="指定网站类型")] = None,
    output: Annotated[str | None, typer.Option("--output", "-o", help="输出文件路径")] = None,
    number: Annotated[str | None, typer.Option("--number", "-n", help="番号（用于生成文件名）")] = None,
    base_dir: Annotated[str, typer.Option("--base-dir", "-d", help="基础输出目录")] = "tests/crawlers/data",
    proxy: Annotated[str | None, typer.Option("--proxy", "-p", help="代理地址 (例如: http://127.0.0.1:7890)")] = None,
    timeout: Annotated[int, typer.Option("--timeout", "-t", help="请求超时时间（秒）")] = 10,
    retry: Annotated[int, typer.Option("--retry", "-r", help="重试次数")] = 3,
):
    """抓取指定URL的详情页内容"""

    # 验证URL
    if not url:
        console.print("[red]错误: 必须提供URL[/red]")
        raise typer.Exit(1)

    # 自动检测网站类型
    if not site:
        site = _detect_site_from_url(url)
        if site:
            console.print(f"[green]自动检测到网站类型: {site}[/green]")
        else:
            console.print("[yellow]无法自动检测网站类型，请手动指定[/yellow]")
            available_sites = get_available_sites()
            console.print("可用的网站:", ", ".join(available_sites))
            raise typer.Exit(1)

    # 验证网站类型
    try:
        website_enum = Website(site)
    except ValueError:
        console.print(f"[red]错误: 不支持的网站类型 '{site}'[/red]")
        console.print("支持的网站:", ", ".join(get_available_sites()))
        raise typer.Exit(1)

    # 运行异步抓取
    asyncio.run(
        _fetch_async(
            url=url,
            website=website_enum,
            output_path=output,
            number=number,
            base_dir=base_dir,
            proxy=proxy,
            timeout=timeout,
            retry=retry,
        )
    )


def _detect_site_from_url(url: str) -> str | None:
    """从URL自动检测网站类型"""
    url_lower = url.lower()

    for keyword, site in ManualConfig.WEB_DIC.items():
        if keyword.lower() in url_lower:
            return site
    return None


async def _fetch_async(
    url: str,
    website: Website,
    output_path: str | None,
    number: str | None,
    base_dir: str,
    proxy: str | None,
    timeout: int,
    retry: int,
):
    """异步抓取详情页内容"""

    # 配置网络客户端
    client_proxy = proxy or config.httpx_proxy
    client_timeout = timeout or config.timeout
    client_retry = retry or config.retry

    console.print(f"[cyan]正在抓取: {url}[/cyan]")
    console.print(f"[cyan]网站类型: {website.value}[/cyan]")
    if client_proxy:
        console.print(f"[cyan]代理: {client_proxy}[/cyan]")

    # 创建异步客户端
    async_client = AsyncWebClient(
        proxy=client_proxy,
        retry=client_retry,
        timeout=client_timeout,
        log_fn=lambda msg: console.print(f"[dim][AsyncWebClient] {msg}[/dim]"),
    )

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在抓取详情页...", total=None)

            # 获取爬虫类
            crawler_class = get_crawler(website)
            if crawler_class is None:
                console.print(f"[red]错误: 未找到 {website.value} 的爬虫[/red]")
                exit(1)

            # 创建爬虫实例
            crawler = crawler_class(client=async_client, base_url=config.get_website_base_url(website))

            # 创建输入
            crawler_input = CrawlerInput.empty()
            crawler_input.appoint_url = url

            # 创建上下文
            ctx = crawler.new_context(crawler_input)

            # 抓取详情页
            progress.update(task, description="正在请求详情页...")
            html, error = await crawler._fetch_detail(ctx, url)

            if html is None:
                console.print(f"[red]错误: 获取详情页失败 - {error}[/red]")
                return

            progress.update(task, description="请求成功，正在保存...")

            # 确定输出路径
            output_file = _determine_output_path(output_path, url, website.value, number, base_dir)

            # 创建输出目录
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 保存HTML内容
            output_file.write_text(html, encoding="utf-8")

            progress.remove_task(task)

        console.print("[green]✅ 抓取成功![/green]")
        console.print(f"[green]文件已保存到: {output_file}[/green]")
        console.print(f"[dim]文件大小: {len(html)} 字符[/dim]")

    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        raise typer.Exit(1)


def _determine_output_path(output_path: str | None, url: str, site: str, number: str | None, base_dir: str) -> Path:
    """确定输出文件路径"""
    if output_path:
        return Path(output_path)

    # 自动生成路径
    base_path = Path(base_dir)

    # 从URL提取可能的文件名
    if number:
        filename = f"{number}.html"
    else:
        # 尝试从URL提取标识符
        url_parts = url.strip("/").split("/")
        if url_parts:
            identifier = url_parts[-1]
            # 清理文件名
            identifier = identifier.replace("=", "_").replace("?", "_").replace("&", "_")
            filename = f"{identifier}.html"
        else:
            filename = "detail.html"

    return base_path / site / filename


@app.command()
def list():
    """列出所有支持的网站"""
    sites = get_available_sites()
    console.print("[bold blue]支持的网站列表:[/bold blue]")
    console.print()

    for i, site in enumerate(sites, 1):
        console.print(f"  {i:2d}. {site}")

    console.print(f"\n[dim]共 {len(sites)} 个网站[/dim]")


@app.command()
def show_config():
    """显示当前配置信息"""
    console.print("[bold blue]当前配置信息:[/bold blue]")
    console.print()
    console.print(f"代理: {config.httpx_proxy or '未设置'}")
    console.print(f"超时时间: {config.timeout} 秒")
    console.print(f"重试次数: {config.retry}")
    # config 对象没有 path 属性，从 manager 获取
    from mdcx.config.manager import manager

    console.print(f"配置文件路径: {getattr(manager, 'path', '未知')}")


if __name__ == "__main__":
    app()
