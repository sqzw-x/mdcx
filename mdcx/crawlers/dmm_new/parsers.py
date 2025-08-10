import re
from typing import Literal, override

from parsel import Selector
from pydantic import BaseModel

from ..base import (
    Context,
    CrawlerData,
    DetailPageParser,
    XPath,
    extract_all_texts,
    extract_text,
)

Category = Literal["tv", "digital", "dvd", "prime", "monthly", "other", "video"]


def parse_category(url: str) -> Category:
    """
    根据 DMM URL 判断其子类.
    """
    if "tv.dmm.co.jp" in url:
        return "tv"
    elif "/digital/" in url:
        # digital tag 可能有流媒体相关, 如 独占配信
        return "digital"
    elif "/dvd/" in url:
        # dvd 可能有多个结果, 蓝光是单独结果, 封面不同, tag 包含 Blu-ray 字样
        return "dvd"
    elif "/prime/" in url:
        return "prime"
    elif "/monthly/" in url:
        return "monthly"
    elif "video.dmm.co.jp" in url:
        return "video"
    else:
        # todo 其他类别
        return "other"


class Parser(DetailPageParser):
    """
    适用类别: monthly, digital, dvd # todo 测试具体适用哪些类别
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


class AggregateRating(BaseModel):
    ratingValue: float | None = None


class Actor(BaseModel):
    name: str | None = None
    alternateName: str | None = None


class VideoObject(BaseModel):
    name: str | None = None
    description: str | None = None
    contentUrl: str | None = None
    thumbnailUrl: str | None = None
    uploadDate: str | None = None
    actor: list[Actor] | None = None
    genre: list[str] | None = None


class Brand(BaseModel):
    name: str | None = None


class DmmJsonSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    image: list[str] | None = None
    sku: str | None = None
    brand: Brand | None = None
    subjectOf: VideoObject | None = None
    aggregateRating: AggregateRating | None = None


class Parser1(DetailPageParser):
    """
    适用于 video.dmm.co.jp 的详情页解析器
    """

    @override
    async def parse(self, ctx: Context, html: Selector) -> CrawlerData:
        d = await super().parse(ctx, html)
        json_data = extract_text(html, '//script[@type="application/ld+json"]/text()')
        try:
            json_data = DmmJsonSchema.model_validate_json(json_data)
            if json_data.name:
                d.title = json_data.name
            if json_data.description:
                d.outline = json_data.description
            if json_data.image:  # todo 此处的图片包含了封面, 半封面, 预览
                d.thumb = json_data.image[0]
            if json_data.brand and json_data.brand.name:
                d.studio = json_data.brand.name
            if video := json_data.subjectOf:
                if video.genre:
                    d.tag = video.genre
                if video.contentUrl:
                    d.trailer = video.contentUrl
                if video.uploadDate:
                    d.release = re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\1-\2-\3", video.uploadDate)
                if video.actor:
                    d.actor = [a.name for a in video.actor if a.name]
            if json_data.aggregateRating:
                rating = json_data.aggregateRating.ratingValue
                if rating is not None:
                    d.score = str(rating)
        except Exception as e:
            ctx.debug(f"解析 JSON-LD 失败: {e}")
            pass

        return d

    @override
    async def title(self, ctx, html) -> str:
        return extract_text(
            html,
            '//h1[contains(@class, "text-lg")]/span/text()',
            '//h1[@id="title"]/text()',
            '//h1[@class="item fn bold"]/text()',
        )

    @override
    async def release(self, ctx, html) -> str | None:
        release = extract_text(
            html,
            "//th[contains(text(),'配信開始日')]/following-sibling::td/span/text()",
            "//th[contains(text(),'商品発売日')]/following-sibling::td/span/text()",
            "//td[contains(text(),'発売日')]/following-sibling::td/text()",
            "//th[contains(text(),'発売日')]/following-sibling::td/text()",
            "//td[contains(text(),'配信開始日')]/following-sibling::td/text()",
            "//th[contains(text(),'配信開始日')]/following-sibling::td/text()",
        )
        if release:
            release = release.replace("/", "-")
            if match := re.search(r"(\d{4}-\d{1,2}-\d{1,2})", release):
                return match.group(1)

    @override
    async def runtime(self, ctx, html) -> str | None:
        runtime = extract_text(
            html,
            "//th[contains(text(),'収録時間')]/following-sibling::td/span/text()",
            "//td[contains(text(),'収録時間')]/following-sibling::td/text()",
            "//th[contains(text(),'収録時間')]/following-sibling::td/text()",
        )
        if match := re.search(r"\d+", runtime):
            return match.group()

    @override
    async def studio(self, ctx, html) -> str | None:
        return extract_text(
            html,
            "//th[contains(text(),'メーカー')]/following-sibling::td/span/a/text()",
            "//td[contains(text(),'メーカー')]/following-sibling::td/a/text()",
        )

    @override
    async def publisher(self, ctx, html) -> str | None:
        return extract_text(
            html,
            "//th[contains(text(),'レーベル')]/following-sibling::td/span/a/text()",
            "//td[contains(text(),'レーベル')]/following-sibling::td/a/text()",
        )

    @override
    async def series(self, ctx, html) -> str | None:
        return extract_text(
            html,
            "//th[contains(text(),'シリーズ')]/following-sibling::td/span/a/text()",
            "//td[contains(text(),'シリーズ')]/following-sibling::td/a/text()",
            "//th[contains(text(),'シリーズ')]/following-sibling::td/a/text()",
        )

    @override
    async def director(self, ctx, html) -> str | None:
        return extract_text(
            html,
            "//th[contains(text(),'監督')]/following-sibling::td/span/a/text()",
            "//td[contains(text(),'監督')]/following-sibling::td/a/text()",
            "//th[contains(text(),'監督')]/following-sibling::td/a/text()",
        )

    @override
    async def actor(self, ctx, html) -> list[str]:
        return extract_all_texts(
            html,
            "//th[contains(text(),'出演者')]/following-sibling::td/span/div/a/text()",
            "//span[@id='performer']/a/text()",
            "//td[@id='fn-visibleActor']/div/a/text()",
            "//td[contains(text(),'出演者')]/following-sibling::td/a/text()",
        )

    @override
    async def tag(self, ctx, html) -> list[str]:
        return extract_all_texts(
            html,
            "//th[contains(text(),'ジャンル')]/following-sibling::td/span/div/a/text()",
            "//td[contains(text(),'ジャンル')]/following-sibling::td/a/text()",
            "//div[@class='info__item']/table/tbody/tr/th[contains(text(),'ジャンル')]/following-sibling::td/a/text()",
        )

    @override
    async def thumb(self, ctx, html) -> str | None:
        url = extract_text(html, '//meta[@property="og:image"]/@content')
        if url:
            aws_url = url.replace("pics.dmm.co.jp", "awsimgsrc.dmm.co.jp/pics_dig")
            return aws_url.replace("ps.jpg", "pl.jpg")

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
