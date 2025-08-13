#!/usr/bin/env python3

import re
from typing import override

from parsel import Selector

from mdcx.config.models import Website
from mdcx.models.base.web import get_dmm_trailer
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
        title = extract_text(html, 'string(//h2[@class="title is-4"]/strong[@class="current-title"])')
        originaltitle = extract_text(html, 'string(//h2[@class="title is-4"]/span[@class="origin-title"])')

        # 根据语言偏好选择标题
        if originaltitle and ctx.input.org_language == "jp":
            title = originaltitle
        elif not originaltitle:
            originaltitle = title

        return self._clean_title(title, ctx.input.number)

    async def originaltitle(self, ctx, html: Selector) -> str:
        title = extract_text(html, 'string(//h2[@class="title is-4"]/strong[@class="current-title"])')
        originaltitle = extract_text(html, 'string(//h2[@class="title is-4"]/span[@class="origin-title"])')

        if not originaltitle:
            originaltitle = title

        return self._clean_title(originaltitle, ctx.input.number)

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
        result1 = extract_text(html, '//strong[contains(text(),"片商:")]/../span/a/text()')
        result2 = extract_text(html, '//strong[contains(text(),"Maker:")]/../span/a/text()')
        return self._clean_field_result(result1, result2)

    async def publisher(self, ctx, html: Selector) -> str:
        result1 = extract_text(html, '//strong[contains(text(),"發行:")]/../span/a/text()')
        result2 = extract_text(html, '//strong[contains(text(),"Publisher:")]/../span/a/text()')
        return self._clean_field_result(result1, result2)

    async def runtime(self, ctx, html: Selector) -> str:
        result1 = extract_text(html, '//strong[contains(text(),"時長")]/../span/text()')
        result2 = extract_text(html, '//strong[contains(text(),"Duration:")]/../span/text()')
        runtime = self._clean_field_result(result1, result2)
        return runtime.replace(" 分鍾", "").replace(" minute(s)", "")

    async def series(self, ctx, html: Selector) -> str:
        result1 = extract_text(html, '//strong[contains(text(),"系列:")]/../span/a/text()')
        result2 = extract_text(html, '//strong[contains(text(),"Series:")]/../span/a/text()')
        return self._clean_field_result(result1, result2)

    async def release(self, ctx, html: Selector) -> str:
        result1 = extract_text(html, '//strong[contains(text(),"日期:")]/../span/text()')
        result2 = extract_text(html, '//strong[contains(text(),"Released Date:")]/../span/text()')
        return self._clean_field_result(result1, result2)

    async def year(self, ctx, html: Selector) -> str:
        release_date = await self.release(ctx, html)
        try:
            result = re.search(r"\d{4}", release_date)
            return result.group() if result else release_date
        except Exception:
            return release_date

    async def tags(self, ctx, html: Selector) -> list[str]:
        result1 = extract_all_texts(html, '//strong[contains(text(),"類別:")]/../span/a/text()')
        result2 = extract_all_texts(html, '//strong[contains(text(),"Tags:")]/../span/a/text()')

        # 合并并清理标签
        all_tags = result1 + result2
        cleaned_tags = []
        for tag in all_tags:
            cleaned_tag = tag.replace("\\xa0", "").replace("'", "").replace(" ", "").strip()
            if cleaned_tag and cleaned_tag not in cleaned_tags:
                cleaned_tags.append(cleaned_tag)

        return cleaned_tags

    async def thumb(self, ctx, html: Selector) -> str:
        return extract_text(html, "//img[@class='video-cover']/@src")

    async def poster(self, ctx, html: Selector) -> str:
        cover_url = await self.thumb(ctx, html)
        return cover_url.replace("/covers/", "/thumbs/") if cover_url else ""

    async def extrafanart(self, ctx, html: Selector) -> list[str]:
        return extract_all_texts(html, "//div[@class='tile-images preview-images']/a[@class='tile-item']/@href")

    async def trailer(self, ctx, html: Selector) -> str:
        trailer_url_list = extract_all_texts(html, "//video[@id='preview-video']/source/@src")
        if trailer_url_list:
            return await get_dmm_trailer(trailer_url_list[0])
        return ""

    async def directors(self, ctx, html: Selector) -> list[str]:
        result1 = extract_text(html, '//strong[contains(text(),"導演:")]/../span/a/text()')
        result2 = extract_text(html, '//strong[contains(text(),"Director:")]/../span/a/text()')
        director = self._clean_field_result(result1, result2)
        return [director] if director else []

    async def score(self, ctx, html: Selector) -> str:
        result = extract_text(html, "//span[@class='score-stars']/../text()")
        try:
            score_match = re.search(r"(\d{1}\.\d+)(分|,)", result)
            return score_match.group(1) if score_match else ""
        except Exception:
            return ""

    async def mosaic(self, ctx, html: Selector) -> str:
        title = await self.title(ctx, html)
        return "无码" if any(keyword in title for keyword in ["無碼", "無修正", "Uncensored"]) else ""

    async def wanted(self, ctx, html: Selector) -> str:
        html_text = html.get()
        result = re.search(r"(\d+)(人想看| want to watch it)", html_text)
        return result.group(1) if result else ""

    async def actor_photo(self, ctx, html: Selector) -> dict:
        actors = await self.actors(ctx, html)
        return dict.fromkeys(actors, "")

    async def image_cut(self, ctx, html: Selector) -> str:
        return "right"

    async def image_download(self, ctx, html: Selector) -> bool:
        return False

    def _clean_title(self, title: str, number: str) -> str:
        if not title:
            return ""

        # 移除常见的无用字符和番号
        title = (
            title.replace("中文字幕", "")
            .replace("無碼", "")
            .replace("\\n", "")
            .replace("_", "-")
            .replace(number.upper(), "")
            .replace(number, "")
            .replace("--", "-")
            .strip()
        )

        # 移除标题中的分集标识
        title_replacements = ["第一集", "第二集", " - 上", " - 下", " 上集", " 下集", " -上", " -下"]
        for replacement in title_replacements:
            title = title.replace(replacement, "").strip()

        return title

    def _clean_field_result(self, result1: str, result2: str) -> str:
        combined = (result1 + result2).strip("+").replace("', '", "").replace('"', "")
        return combined


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
        # todo get and parse from config
        return

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
        # 检查各种错误情况
        html_text = html.get()

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
        return await self.parser.parse(ctx, html)

    @override
    async def post_process(self, ctx, res: CrawlerResult) -> CrawlerResult:
        # 设置网站 URL
        website_url = (
            res.website.replace(self.base_url, "https://javdb.com")
            if self.base_url != "https://javdb.com"
            else res.website
        )
        res.website = website_url.replace("?locale=zh", "")

        # 提取 javdbid
        if res.website and res.website.startswith("/v/"):
            javdbid = res.website.replace("/v/", "")
            res.javdbid = javdbid

        return res
