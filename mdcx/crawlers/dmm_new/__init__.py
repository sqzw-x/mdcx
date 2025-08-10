import re
from typing import override

from parsel import Selector

from mdcx.config.models import Website

from ..base import (
    Context,
    CralwerException,
    CrawlerData,
    GenericBaseCrawler,
    register_crawler,
)
from .parsers import Category, Parser, Parser1, parse_category


@register_crawler
class DmmCrawler(GenericBaseCrawler):
    parser = Parser()
    parser1 = Parser1()

    @classmethod
    @override
    def site(cls) -> Website:
        return Website.DMM

    @classmethod
    @override
    def base_url_(cls) -> str:
        # DMM 不支持自定义 URL
        return ""

    @override
    def _get_cookies(self, ctx) -> dict[str, str] | None:
        return {"age_check_done": "1"}

    @override
    async def _generate_search_url(self, ctx) -> list[str] | None:
        number = ctx.input.number.lower()

        if x := re.findall(r"[A-Za-z]+-?(\d+)", number):
            digits = x[0]
            if len(digits) >= 5 and digits.startswith("00"):
                number = number.replace(digits, digits[2:])
            elif len(digits) == 4:
                number = number.replace("-", "0")  # https://github.com/sqzw-x/mdcx/issues/393

        # 搜索结果多，但snis-027没结果
        number_00 = number.replace("-", "00")
        # 搜索结果少
        number_no_00 = number.replace("-", "")

        return [
            f"https://www.dmm.co.jp/search/=/searchstr={number_00}/sort=ranking/",
            f"https://www.dmm.co.jp/search/=/searchstr={number_no_00}/sort=ranking/",
            f"https://www.dmm.com/search/=/searchstr={number_no_00}/sort=ranking/",  # 写真
        ]

    @override
    async def _parse_search_page(self, ctx, html, search_url) -> list[str] | None:
        if "404 Not Found" in html.css("span.d-txten::text").get(""):
            raise CralwerException("404! 页面地址错误！")

        url_list = html.css(".tmb>a[href]").getall()
        if not url_list:
            return None

        number_parts = re.search(r"(\d[a-z])+?-?(\d+)", ctx.input.number.lower())
        if not number_parts:
            ctx.show(f"无法从番号 {ctx.input.number} 提取前缀和数字")
            return None
        prefix = number_parts.group(1)
        digits = number_parts.group(2)
        n1 = f"{prefix}{digits:0>5}"
        n2 = f"{prefix}{digits}"

        matched: dict[Category, list[str]] = {}
        for u in url_list:
            if n1 in u or n2 in u:
                matched.setdefault(parse_category(u), []).append(u)

        matched.get("dvd", []).sort(reverse=True)  # why?

        # 网址排序：digital(数据完整) > dvd(无前缀数字，图片完整) > prime（有发行日期） > premium（无发行日期） > s1（无发行日期）
        res = []
        for c in ["tv", "digital", "dvd", "prime", "monthly", "other"]:
            if c in matched:
                res.extend(matched[c])

        return res

    @override
    async def _detail(self, ctx: Context, detail_urls: list[str]) -> CrawlerData | None:
        for detail_url in detail_urls:
            category = parse_category(detail_url)
            selector, error = await self._fetch_detail(ctx, detail_url)
            if selector is None:
                ctx.debug(f"详情页请求失败: {detail_url=} {error=}")
                continue
            ctx.debug(f"详情页请求成功: {detail_url=}")
            if category in ["digital", "dvd", "prime", "monthly"]:
                return await self.parser.parse(ctx, selector)
            elif category == "video":
                return await self.parser1.parse(ctx, selector)

    @override
    async def post_process(self, ctx, res):
        res.image_download = "VR" in res.title
        res.originaltitle = res.title
        res.originalplot = res.outline
        res.poster = res.thumb.replace("pl.jpg", "ps.jpg")
        if not res.publisher:
            res.publisher = res.studio
        if len(res.release) >= 4:
            res.year = res.release[:4]
        res.actor_photo = dict.fromkeys(res.actor.split(","), "")

    @override
    async def _parse_detail_page(self, ctx, html: Selector, detail_url: str) -> CrawlerData | None:
        raise NotImplementedError
