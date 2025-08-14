#!/usr/bin/env python3

import re
from typing import override

from parsel import Selector

from mdcx.config.manager import config
from mdcx.config.models import Website
from mdcx.models.types import CrawlerResult

from .base import (
    BaseCrawler,
    CralwerException,
    CrawlerData,
    DetailPageParser,
    extract_all_texts,
    extract_text,
)


class Parser(DetailPageParser):
    async def number(self, ctx, html: Selector) -> str:
        result = extract_text(html, '//a[@class="button is-white copy-to-clipboard"]/@data-clipboard-text')
        return result or ctx.input.number

    async def title(self, ctx, html: Selector) -> str:
        return extract_text(html, 'string(//h2[@class="title is-4"]/strong[@class="current-title"])')

    async def originaltitle(self, ctx, html: Selector) -> str:
        return extract_text(html, 'string(//h2[@class="title is-4"]/span[@class="origin-title"])')

    async def actors(self, ctx, html: Selector) -> list[str]:
        # parsel css 不支持 :has() 中的多个选择器, 这是一个已知问题: https://github.com/scrapy/cssselect/issues/138
        return (
            html.css("span:has(strong.female)")
            .xpath("//strong[contains(@class, 'female')]/preceding-sibling::a/text()")
            .getall()
        )

    async def all_actors(self, ctx, html: Selector) -> list[str]:
        return (html.css("span:has(strong.female)") or html.css("span:has(strong.male)")).xpath("a/text()").getall()

    async def studio(self, ctx, html: Selector) -> str:
        return extract_text(
            html,
            '//strong[contains(text(),"片商:")]/../span/a/text()',
            '//strong[contains(text(),"Maker:")]/../span/a/text()',
        )

    async def publisher(self, ctx, html: Selector) -> str:
        return extract_text(
            html,
            '//strong[contains(text(),"發行:")]/../span/a/text()',
            '//strong[contains(text(),"Publisher:")]/../span/a/text()',
        )

    async def runtime(self, ctx, html: Selector) -> str:
        result = extract_text(
            html,
            '//strong[contains(text(),"時長")]/../span/text()',
            '//strong[contains(text(),"Duration:")]/../span/text()',
        )
        return result.replace(" 分鍾", "").replace(" minute(s)", "")

    async def series(self, ctx, html: Selector) -> str:
        return extract_text(
            html,
            '//strong[contains(text(),"系列:")]/../span/a/text()',
            '//strong[contains(text(),"Series:")]/../span/a/text()',
        )

    async def release(self, ctx, html: Selector) -> str:
        return extract_text(
            html,
            '//strong[contains(text(),"日期:")]/../span/text()',
            '//strong[contains(text(),"Released Date:")]/../span/text()',
        )

    async def year(self, ctx, html: Selector) -> str:
        release_date = await self.release(ctx, html)
        try:
            result = re.search(r"\d{4}", release_date)
            return result.group() if result else release_date
        except Exception:
            return release_date

    async def tags(self, ctx, html: Selector) -> list[str]:
        tags = extract_all_texts(
            html,
            '//strong[contains(text(),"類別:")]/../span/a/text()',
            '//strong[contains(text(),"Tags:")]/../span/a/text()',
        )
        tags = [tag.replace("\\xa0", "").replace("'", "").replace(" ", "").strip() for tag in tags if tag.strip()]
        return list(dict.fromkeys(tags))

    async def thumb(self, ctx, html: Selector) -> str:
        return extract_text(html, "//img[@class='video-cover']/@src")

    async def extrafanart(self, ctx, html: Selector) -> list[str]:
        return extract_all_texts(html, "//div[@class='tile-images preview-images']/a[@class='tile-item']/@href")

    async def trailer(self, ctx, html: Selector) -> str:
        return extract_text(html, "//video[@id='preview-video']/source/@src")

    async def directors(self, ctx, html: Selector) -> list[str]:
        return extract_all_texts(
            html,
            '//strong[contains(text(),"導演:")]/../span/a/text()',
            '//strong[contains(text(),"Director:")]/../span/a/text()',
        )

    async def score(self, ctx, html: Selector) -> str:
        result = extract_text(html, "//span[@class='score-stars']/../text()")
        try:
            score_match = re.search(r"(\d{1}\.\d+)(分|,)", result)
            return score_match.group(1) if score_match else ""
        except Exception:
            return ""

    async def wanted(self, ctx, html: Selector) -> str:
        html_text = html.get()
        result = re.search(r"(\d+)(人想看| want to watch it)", html_text)
        return result.group(1) if result else ""

    async def image_cut(self, ctx, html: Selector) -> str:
        return "right"

    async def image_download(self, ctx, html: Selector) -> bool:
        return False


class JavdbCrawler(BaseCrawler):
    parser = Parser()

    @classmethod
    @override
    def site(cls) -> Website:
        return Website.JAVDB

    @classmethod
    @override
    def base_url_(cls) -> str:
        return "https://javdb.com"

    @override
    def _get_headers(self, ctx) -> dict[str, str] | None:
        if config.javdb:
            return {"cookie": config.javdb}

    @override
    async def _generate_search_url(self, ctx) -> list[str]:
        number = ctx.input.number.strip()

        # 处理日期格式的番号
        if "." in number:
            old_date = re.findall(r"\D+(\d{2}\.\d{2}\.\d{2})$", number)
            if old_date:
                old_date = old_date[0]
                new_date = "20" + old_date
                number = number.replace(old_date, new_date)

        search_url = f"{self.base_url}/search?q={number}&locale=zh"
        ctx.debug(f"搜索地址: {search_url}")
        return [search_url]

    @override
    async def _parse_search_page(self, ctx, html: Selector, search_url: str) -> list[str] | None:
        html_text = html._text or ""
        if "The owner of this website has banned your access based on your browser's behaving" in html_text:
            raise CralwerException(f"由于请求过多，javdb网站暂时禁止了你当前IP的访问！！点击 {search_url} 查看详情！")
        if "Due to copyright restrictions" in html_text:
            raise CralwerException(
                f"由于版权限制，javdb网站禁止了日本IP的访问！！请更换日本以外代理！点击 {search_url} 查看详情！"
            )
        if "ray-id" in html_text:
            raise CralwerException("搜索结果: 被 Cloudflare 5 秒盾拦截！请尝试更换cookie！")

        # 获取搜索结果
        res_list = html.xpath("//a[@class='box']")
        if not res_list:
            return None

        info_list = []
        for each in res_list:
            href = extract_text(each, "@href")
            title = extract_text(each, "div[@class='video-title']/strong/text()")
            meta = extract_text(each, "div[@class='meta']/text()")

            if href:
                info_list.append([href, title, meta])

        # 精确匹配
        number = ctx.input.number
        for href, title, meta in info_list:
            if number.upper() in title.upper():
                return [href]

        # 模糊匹配
        clean_number = number.upper().replace(".", "").replace("-", "").replace(" ", "")
        for href, title, meta in info_list:
            clean_content = (title + meta).upper().replace("-", "").replace(".", "").replace(" ", "")
            if clean_number in clean_content:
                return [href]

        return None

    @override
    async def _parse_detail_page(self, ctx, html: Selector, detail_url: str) -> CrawlerData | None:
        return await self.parser.parse(ctx, html, url=detail_url)

    @override
    async def post_process(self, ctx, res: CrawlerResult) -> CrawlerResult:
        if not res.originaltitle:
            res.originaltitle = res.title
        res.poster = res.thumb.replace("/covers/", "/thumbs/")
        # 提取 javdbid
        if res.url and (r := re.search(r"/v/([a-zA-Z0-9])+", res.url)):
            javdbid = r.group(1)
            res.javdbid = javdbid
            res.externalId = javdbid
        res.mosaic = "无码" if any(keyword in res.title for keyword in ["無碼", "無修正", "Uncensored"]) else "有码"

        return res
