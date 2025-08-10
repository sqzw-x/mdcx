import re
from typing import override

from parsel import Selector

from mdcx.config.models import Website

from ..base import (
    BaseCrawler,
    Context,
    CralwerException,
    CrawlerData,
)
from .parsers import Category, Parser, Parser1, RentalParser, parse_category


class DmmCrawler(BaseCrawler):
    parser = Parser()
    parser1 = Parser1()
    rental_parser = RentalParser()

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

        res = []
        for u in url_list:
            if n1 in u or n2 in u:
                res.append(u)

        return res

    @classmethod
    def _get_parser(cls, category: Category):
        match category:
            case "digital" | "dvd" | "prime" | "monthly" | "mono":
                return cls.parser
            case "video":
                return cls.parser1
            case "rental":
                return cls.rental_parser
            case _:
                return cls.parser

    @override
    async def _detail(self, ctx: Context, detail_urls: list[str]) -> CrawlerData | None:
        d: dict[Category, list[str]] = {}
        for url in detail_urls:
            category = parse_category(url)
            if category not in d:
                ctx.debug(f"未知类别: {category} {url=}")
                continue
            d.setdefault(category, []).append(url)
        for category in ("mono", "tv", "video", "digital", "dvd", "prime", "monthly", "other"):  # 优先级
            urls = d.get(category, [])
            parser = self._get_parser(category)
            for u in urls:
                html, error = await self._fetch_detail(ctx, u)
                if html is None:
                    ctx.debug(f"详情页请求失败: {u=} {error=}")
                    continue
                ctx.debug(f"详情页请求成功: {u=}")
                return await parser.parse(ctx, Selector(html))

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
