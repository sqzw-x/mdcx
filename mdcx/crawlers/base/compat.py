import time
import traceback
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from mdcx.config.models import Website
from mdcx.models.types import CrawlerInput, CrawlerResponse, CrawlerResult
from mdcx.utils.dataclass import update

from .types import Context, CralwerException

v1_cralwers = {}


def register_v1_crawler(site: Website, fn: Callable):
    v1_cralwers[site] = LegacyCrawler(fn=fn, site=site)


def get_v1_crawler(site: Website) -> "LegacyCrawler":
    if site not in v1_cralwers:
        raise CralwerException(f"v1 crawler for {site} not found")
    return v1_cralwers[site]


@dataclass
class LegacyCrawler:
    fn: Callable[..., Awaitable[dict[str, dict[str, dict]]]]
    site: Website

    def __call__(self, client, base_url):
        return self

    async def run(self, input: CrawlerInput) -> CrawlerResponse:
        """与 `GenericBaseCrawler.run` 兼容的包装器."""
        start_time = time.time()
        ctx = Context(input=input)
        ctx.debug(f"{input=}")

        try:
            data = await self._run(ctx)
            ctx.debug_info.execution_time = time.time() - start_time
            return CrawlerResponse(data=data, debug_info=ctx.debug_info)
        except Exception:
            ctx.debug(traceback.format_exc())
            return CrawlerResponse(debug_info=ctx.debug_info)

    async def _run(self, ctx: Context) -> CrawlerResult:
        r = await self.fn(
            **{
                "number": ctx.input.number,
                "appoint_url": ctx.input.appoint_url,
                "language": ctx.input.language,
                "file_path": ctx.input.file_path,
                "appoint_number": ctx.input.appoint_number,
                "mosaic": ctx.input.mosaic,
                "short_number": ctx.input.short_number,
                "org_language": ctx.input.org_language,
            }
        )
        if not r:
            raise CralwerException(f"v1 crawler failed: {self.site}")
        res = list(r.values())[0]
        # 只有 iqqtv_new 和 javlibrary_new 会返回多种语言的数据, 其他所有来源只可能
        # 1. 返回单一语言的数据, 即 {site: {language: data}}
        # 2. 返回多语言 dict, 但实际上内部数据相同, 即 {site: {zh_cn: data, zh_tw: data, jp: data}}
        # 因此此处只取第一个 data, 对大多数网站都无影响.
        # 唯一受影响的是当需要 iqqtv_new 或 javlibrary_new 的多个语言的数据时, 需要多次请求
        res = list(res.values())[0]

        return update(CrawlerResult.empty(), res)
