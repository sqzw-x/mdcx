import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from parsel import Selector

from mdcx.config.models import Website
from mdcx.models.types import CrawlerInput, CrawlerResponse, CrawlerResult
from mdcx.web_async import AsyncWebClient

if TYPE_CHECKING:
    from mdcx.config.manager import ConfigSchema

    from .parser import DetailPageParser


class CralwerException(Exception): ...


@dataclass
class Context:
    input: CrawlerInput  # crawler 的原始输入
    show_logs: list[str] = field(default_factory=list)
    debug_logs: list[str] = field(default_factory=list)

    def show(self, message: str):
        self.show_logs.append(message)

    def debug(self, message: str):
        self.debug_logs.append(message)


class GenericBaseCrawler[T: Context = Context](ABC):
    """
    爬虫基类. 所有具体爬虫均应继承此类并实现其抽象方法.

    Crawler 本身应该是无状态的, 所有与单次爬取相关的数据均应存储在 `Context` 中, 可在所有方法中通过 `ctx` 参数访问.

    `Context` 是默认类型, 必要时可实现子类并通过泛型参数 T 指定.

    由于爬取逻辑因网站而异, 在最极端情况下可以重写 `_run` 方法以完全自定义爬取流程.
    """

    def __init__(self, config: "ConfigSchema"):
        self.async_client: AsyncWebClient = config.async_client
        self.base_url: str = getattr(config, f"{self.site}_website", self.base_url_())

    @classmethod
    @abstractmethod
    def site(cls) -> Website:
        """此爬虫对应的网站枚举值."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def base_url_(cls) -> str:
        """支持自定义 URL 的爬虫在不提供自定义值时的默认值. 可以通过 self.base_url 访问实际值."""
        raise NotImplementedError

    @abstractmethod
    def new_context(self, input: CrawlerInput) -> T:
        raise NotImplementedError

    async def run(self, input: CrawlerInput) -> CrawlerResponse:
        start_time = time.time()
        ctx = self.new_context(input)
        ctx.debug(f"{input=}")
        ctx.show(f"-> {self.site}")

        try:
            res = await self._run(ctx)
            res.execution_time = time.time() - start_time
            return res
        except Exception as e:
            ctx.show(str(e))
            ctx.debug(traceback.format_exc())
            return CrawlerResponse(
                success=False,
                logs=ctx.show_logs,
                execution_time=time.time() - start_time,
                error=e,
            )
        finally:
            ctx.show(f"({round(time.time() - start_time, 2)}s)")

    async def _run(self, ctx: T):
        if not ctx.input.appoint_url:
            search_urls = await self._generate_search_url(ctx)
            if not search_urls:
                raise CralwerException("生成搜索页 URL 失败")
            if isinstance(search_urls, str):
                search_urls = [search_urls]
            ctx.debug(f"搜索页 URL: {search_urls}")

            detail_urls = await self._search(ctx, search_urls)
        else:
            detail_urls = [ctx.input.appoint_url]
            ctx.debug(f"使用指定详情页 URL: {ctx.input.appoint_url}")

        data = await self._detail(ctx, detail_urls)
        data.source = self.site().value  # todo use Enum directly
        await self.post_process(ctx, data)

        return CrawlerResponse(
            success=True,
            data=data,
            detail_urls=detail_urls,
        )

    async def _search(self, ctx: T, search_urls: list[str]) -> list[str]:
        for search_url in search_urls:
            selector, error = await self._fetch_search(ctx, search_url)
            if selector is None:
                ctx.debug(f"搜索页请求失败: {search_url=} {error=}")
                continue
            detail_urls = await self._parse_search_page(ctx, selector, search_url)
            if detail_urls:
                ctx.debug(f"详情页 URL: {detail_urls}")
                return detail_urls if isinstance(detail_urls, list) else [detail_urls]
        else:
            raise CralwerException("获取详情页 URL 失败")

    async def _detail(self, ctx: T, detail_urls: list[str]) -> CrawlerResult:
        for detail_url in detail_urls:
            selector, error = await self._fetch_detail(ctx, detail_url)
            if selector is None:
                ctx.debug(f"详情页请求失败: {detail_url=} {error=}")
                continue

            parser = self._get_detail_parser(ctx, detail_url)
            scraped_data = await parser.parse(ctx, selector)
            if scraped_data:
                scraped_data.website = detail_url
                return scraped_data
        else:
            raise CralwerException("获取详情页数据失败")

    @abstractmethod
    async def _generate_search_url(self, ctx: T) -> list[str] | str | None:
        """
        生成搜索 URL.
        """
        raise NotImplementedError

    @abstractmethod
    async def _parse_search_page(self, ctx: T, html: Selector, search_url: str) -> list[str] | str | None:
        """
        解析搜索结果页, 获取详情页 URL.

        Args:
            html (Selector): 包含搜索结果页 HTML 的 parsel Selector 对象.
            search_url (str): 搜索页 URL.

        Returns:
            detail_urls: 一个或多个详情页的 URL, 如果找不到则返回 None.
        """
        raise NotImplementedError

    @abstractmethod
    def _get_detail_parser(self, ctx: T, detail_url: str) -> "DetailPageParser[T]":
        """
        获取详情页解析器.
        """
        raise NotImplementedError

    async def post_process(self, ctx: T, res: CrawlerResult):
        """
        爬取并解析完成后对结果进行后处理.

        Args:
            res (CrawlerResult): 爬取结果对象.
        """
        return

    async def _fetch_search(self, ctx: T, url: str) -> tuple[Selector | None, str]:
        """
        获取搜索页的 HTML 内容并解析为 parsel Selector 对象. 此方法不应抛出异常.

        Args:
            url (str): 搜索页的 URL.

        Returns:
            解析后的 Selector 对象和错误信息.
        """
        html_text, error = await self.async_client.get_text(
            url, headers=self._get_headers(ctx), cookies=self._get_cookies(ctx)
        )
        if html_text is None:
            return None, f"搜索页请求失败: {error}"
        return Selector(text=html_text), ""

    async def _fetch_detail(self, ctx: T, url: str) -> tuple[Selector | None, str]:
        """
        获取详情页的 HTML 内容并解析为 parsel Selector 对象. 此方法不应抛出异常.

        Args:
            url (str): 详情页的 URL.

        Returns:
            解析后的 Selector 对象和错误信息.
        """
        html_text, error = await self.async_client.get_text(
            url, headers=self._get_headers(ctx), cookies=self._get_cookies(ctx)
        )
        if html_text is None:
            return None, f"详情页请求失败: {error}"
        return Selector(text=html_text), ""

    def _get_cookies(self, ctx: T) -> dict[str, str] | None:
        return None

    def _get_headers(self, ctx: T) -> dict[str, str] | None:
        return None


class BaseCrawler(GenericBaseCrawler[Context]):
    def new_context(self, input: CrawlerInput) -> Context:
        return Context(input=input)


crawler_registry: dict[Website, type[GenericBaseCrawler]] = {}


def register_crawler(crawler_cls: type[GenericBaseCrawler]):
    crawler_registry[crawler_cls.site()] = crawler_cls
    return crawler_cls


def get_crawler(site: Website) -> type[GenericBaseCrawler] | None:
    return crawler_registry.get(site)
