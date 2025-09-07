import re
from typing import TypedDict, Unpack

from parsel import Selector

from .types import NOT_SUPPORT, Context, CrawlerData, CSSSelector, FieldRes, FieldValue, SelectorType


def extract_text(html: Selector, *selector: SelectorType) -> str:
    """
    从 HTML 中提取单个文本节点, 将依次尝试每个选择器直到找到匹配项.

    Args:
        html (Selector): parsel.Selector 对象, 表示一个 HTML document.
        selector (tuple[SelectorType, ...]): 一组 XPath, CSS 选择器或正则表达式, 字符串视为 XPath 选择器.

    Returns:
        提取并清理后的文本, 未找到则返回空字符串.
    """
    try:
        for s in selector:
            if isinstance(s, re.Pattern):
                result = html.re(s)
                result = result[0] if result else ""
            elif isinstance(s, CSSSelector):
                result = html.css(s).get()
            else:
                result = html.xpath(s).get()
            if result:
                return clean_string(result)
        return ""
    except Exception:
        return ""


def extract_all_texts(html: Selector, *selector: SelectorType) -> list[str]:
    """
    从 HTML 中提取所有匹配的文本节点, 将依次尝试每个选择器直到找到匹配项.

    Args:
        html (Selector): parsel.Selector 对象, 表示一个 HTML document.
        selector (tuple[SelectorType, ...]): 一组 XPath, CSS 选择器或正则表达式, 字符串视为 XPath 选择器.

    Returns:
        list[str]: 所有匹配文本的列表, 每个文本都经过清理.
    """
    try:
        for s in selector:
            if isinstance(s, re.Pattern):
                results = html.re(s)
            elif isinstance(s, CSSSelector):
                results = html.css(s).getall()
            else:
                results = html.xpath(s).getall()
            if results:
                return [clean_string(r) for r in results if clean_string(r)]
        return []
    except Exception:
        return []


def clean_string(text: str | None) -> str:
    """
    通过删除首尾空格和常见的 HTML 实体来清理字符串.

    Args:
        text (str | None): 输入字符串.

    Returns:
        str: 清理后的字符串.
    """
    if not text:
        return ""
    return text.strip().replace("\n", "").replace("\r", "").replace("&nbsp;", " ")


def re_findall(pattern: str, text: str, flags: int = 0) -> list[tuple[str, ...]]:
    """
    re.findall 的类型安全的封装.

    re.findall 在不含/只含一个捕获组时返回 list[str], 在包含多个捕获组时返回 list[tuple[str, ...]].
    此函数将返回类型统一为第二种. 尽管如此, 仍需注意:
    1. 不要直接用正则表达式处理 HTML, 而是首先使用 xpath 或 css 选择器.
    2. 尽量不要使用 re.findall, 很可能 re.search 就足够.
    """
    r = re.findall(pattern, text, flags)
    if r and isinstance(r[0], str):
        return [(m,) for m in r]
    return r


class DetailPageParser[T: Context = Context]:
    """
    详情页解析器的基类. 子类应重写所需字段的对应方法.

    可返回以下几种类型的值:
    1. T 类型的具体值: 直接用于构造 CrawlerResult.
    2. None 或 T 类型的空值: 表示该字段在此页面上无法获取.
    3. self.NOT_SUPPORT: 默认实现. 表示某字段在该网站上不存在.

    2 和 3 在最终结果中都会转为空值. 唯一区别在于, None 或空值被视为获取失败, 而 NOT_SUPPORT 则不会.
    """

    NOT_SUPPORT = NOT_SUPPORT
    """表示某字段在该网站上不存在. 它和空值的区别在于, 该值不被视为获取失败."""

    async def title(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def actors(self, ctx: T, html: Selector) -> FieldRes[list[str]]:
        return self.NOT_SUPPORT

    async def all_actors(self, ctx: T, html: Selector) -> FieldRes[list[str]]:
        return self.NOT_SUPPORT

    async def directors(self, ctx: T, html: Selector) -> FieldRes[list[str]]:
        return self.NOT_SUPPORT

    async def extrafanart(self, ctx: T, html: Selector) -> FieldRes[list[str]]:
        return self.NOT_SUPPORT

    async def originalplot(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def originaltitle(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def outline(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def poster(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def publisher(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def release(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def runtime(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def score(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def series(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def studio(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def tags(self, ctx: T, html: Selector) -> FieldRes[list[str]]:
        return self.NOT_SUPPORT

    async def thumb(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def trailer(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def wanted(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def year(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def image_cut(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def image_download(self, ctx: T, html: Selector) -> FieldValue[bool]:
        return self.NOT_SUPPORT

    async def number(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    async def mosaic(self, ctx: T, html: Selector) -> FieldRes:
        return self.NOT_SUPPORT

    class OtherFields(TypedDict, total=False):
        external_id: str
        source: str

    async def parse(self, ctx: T, html: Selector, **kwargs: Unpack[OtherFields]) -> CrawlerData:
        """
        调用所有字段的解析方法, 并构造 CrawlerResult.

        Args:
            html: 包含详情页 HTML 的 parsel Selector 对象.

        Returns:
            包含所有刮削数据的 CrawlerResult 对象.
        """
        return CrawlerData(
            title=await self.title(ctx, html),
            actors=await self.actors(ctx, html),
            all_actors=await self.all_actors(ctx, html),
            directors=await self.directors(ctx, html),
            extrafanart=await self.extrafanart(ctx, html),
            originalplot=await self.originalplot(ctx, html),
            originaltitle=await self.originaltitle(ctx, html),
            outline=await self.outline(ctx, html),
            poster=await self.poster(ctx, html),
            publisher=await self.publisher(ctx, html),
            release=await self.release(ctx, html),
            runtime=await self.runtime(ctx, html),
            score=await self.score(ctx, html),
            series=await self.series(ctx, html),
            studio=await self.studio(ctx, html),
            tags=await self.tags(ctx, html),
            thumb=await self.thumb(ctx, html),
            trailer=await self.trailer(ctx, html),
            wanted=await self.wanted(ctx, html),
            year=await self.year(ctx, html),
            image_cut=await self.image_cut(ctx, html),
            image_download=await self.image_download(ctx, html),
            number=await self.number(ctx, html),
            mosaic=await self.mosaic(ctx, html),
            external_id=kwargs.get("external_id", ""),
            source=kwargs.get("source", ""),
        )
