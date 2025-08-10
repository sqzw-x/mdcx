import re
from typing import override

from mdcx.config.models import Website
from mdcx.crawlers.base import Context
from mdcx.models.types import CrawlerResult

from .base import BaseCrawler, CralwerException, register_crawler
from .parser import DetailPageParser, XPath, extract_all_texts, extract_text


class Parser(DetailPageParser):
    """
    适用类别: monthly, digital, dvd, prime, tv.dmm.co.jp # todo 测试具体适用哪些类别
    """

    @override
    async def title(self, ctx, html) -> str:
        title = extract_text(html, '//h1[@id="title"]/text()', '//h1[@class="item fn bold"]/text()')
        return title

    @override
    async def release(self, ctx, html) -> str | None:
        release = extract_text(
            html,
            "//td[contains(text(),'発売日')]/following-sibling::td/text()",
            "//th[contains(text(),'発売日')]/following-sibling::td/text()",
            "//td[contains(text(),'配信開始日')]/following-sibling::td/text()",
            "//th[contains(text(),'配信開始日')]/following-sibling::td/text()",
        )
        release = release.replace("/", "-")
        if match := re.search(r"(\d{4}-\d{1,2}-\d{1,2})", release):
            return match.group(1)

    @override
    async def runtime(self, ctx, html) -> str | None:
        runtime = extract_text(
            html,
            "//td[contains(text(),'収録時間')]/following-sibling::td/text()",
            "//th[contains(text(),'収録時間')]/following-sibling::td/text()",
        )
        if match := re.search(r"\d+", runtime):
            return match.group()

    @override
    async def studio(self, ctx, html) -> XPath:
        return XPath("//td[contains(text(),'メーカー')]/following-sibling::td/a/text()")

    @override
    async def publisher(self, ctx, html) -> str | None:
        return extract_text(html, "//td[contains(text(),'レーベル')]/following-sibling::td/a/text()")

    @override
    async def series(self, ctx, html):
        return (
            XPath("//td[contains(text(),'シリーズ')]/following-sibling::td/a/text()"),
            XPath("//th[contains(text(),'シリーズ')]/following-sibling::td/a/text()"),
        )

    @override
    async def director(self, ctx, html):
        return (
            XPath("//td[contains(text(),'監督')]/following-sibling::td/a/text()"),
            XPath("//th[contains(text(),'監督')]/following-sibling::td/a/text()"),
        )

    @override
    async def actor(self, ctx, html) -> list[str]:
        return extract_all_texts(
            html,
            "//span[@id='performer']/a/text()",
            "//td[@id='fn-visibleActor']/div/a/text()",
            "//td[contains(text(),'出演者')]/following-sibling::td/a/text()",
        )

    @override
    async def tag(self, ctx, html) -> list[str]:
        return extract_all_texts(
            html,
            "//td[contains(text(),'ジャンル')]/following-sibling::td/a/text()",
            "//div[@class='info__item']/table/tbody/tr/th[contains(text(),'ジャンル')]/following-sibling::td/a/text()",
        )

    @override
    async def thumb(self, ctx, html) -> str | None:
        url = extract_text(html, '//meta[@property="og:image"]/@content')
        aws_url = url.replace("pics.dmm.co.jp", "awsimgsrc.dmm.co.jp/pics_dig")
        return aws_url.replace("ps.jpg", "pl.jpg")
        # return url.replace("ps.jpg", "pl.jpg")

    @override
    async def extrafanart(self, ctx, html) -> list[str]:
        extrafanart = extract_all_texts(
            html, "//div[@id='sample-image-block']/a/@href", "//a[@name='sample-image']/img/@data-lazy"
        )
        return [re.sub(r"-(\d+)\.jpg", r"jp-\1.jpg", i) for i in extrafanart]

    @override
    async def outline(self, ctx, html) -> str:
        outline = extract_text(
            html,
            "normalize-space(string(//div[@class='wp-smplex']/preceding-sibling::div[contains(@class, 'mg-b20')][1]))",
        )
        return outline.replace("「コンビニ受取」対象商品です。詳しくはこちらをご覧ください。", "")

    @override
    async def score(self, ctx, html) -> str:
        score = extract_text(html, "//p[contains(@class,'d-review__average')]/strong/text()")
        return score.replace("点", "")

    @override
    async def image_cut(self, ctx, html):
        return "right"

    @override
    async def mosaic(self, ctx, html):
        if extract_text(html, '//li[@class="on"]/a/text()') == "アニメ":
            return "里番"
        return "有码"


@register_crawler
class DmmCrawler(BaseCrawler):
    detail_parser = Parser()

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

        url_list = html.css("p.tmb a::attr(href)").getall()
        if not url_list:
            return None

        number_temp = ctx.input.number.lower().replace("-", "")
        number1 = number_temp.replace("000", "")
        number_pre = re.compile(f"(?<=[=0-9]){number_temp[:3]}")
        number_end = re.compile(f"{number_temp[-3:]}(?=(-[0-9])|([a-z]*)?[/&])")
        number_mid = re.compile(f"[^a-z]{number1}[^0-9]")
        temp_list = []

        for each in url_list:
            if (number_pre.search(each) and number_end.search(each)) or number_mid.search(each):
                temp_list.append(each)

        if not temp_list:  # 通过标题搜索
            title_list = html.css("p.txt a::text").getall()
            if title_list and url_list:
                full_title = ctx.input.number
                for i in range(len(url_list)):
                    temp_title = title_list[i].replace("...", "").strip()
                    if temp_title in full_title:
                        temp_list.append(url_list[i])

        # 网址排序：digital(数据完整) > dvd(无前缀数字，图片完整) > prime（有发行日期） > premium（无发行日期） > s1（无发行日期）
        tv_list = []
        digital_list = []
        dvd_list = []
        prime_list = []
        monthly_list = []
        other_list = []
        for i in temp_list:
            if "tv.dmm.co.jp" in i:
                tv_list.append(i)
            elif "/digital/" in i:
                digital_list.append(i)
            elif "/dvd/" in i:
                dvd_list.append(i)
            elif "/prime/" in i:
                prime_list.append(i)
            elif "/monthly/" in i:
                monthly_list.append(i)
            else:
                other_list.append(i)
        dvd_list.sort(reverse=True)

        new_url_list = tv_list + digital_list + dvd_list + prime_list + monthly_list + other_list
        if not new_url_list:
            return None

        return new_url_list

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
    def _get_detail_parser(self, ctx, detail_url: str) -> DetailPageParser:
        return self.detail_parser

    @override
    async def _detail(self, ctx: Context, detail_urls: list[str]) -> CrawlerResult:
        return await super()._detail(ctx, detail_urls)
