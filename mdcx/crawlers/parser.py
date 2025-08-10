import re
from collections.abc import Awaitable, Callable

from parsel import Selector

from mdcx.models.types import CrawlerResult

from .base import Context


class XPath(str): ...


class CSSSelector(str): ...


class _NoField: ...


type FieldValue[T = str] = T | None | _NoField
type FieldRes[T = str] = tuple[XPath | CSSSelector, ...] | FieldValue[T]

type SelectorType = XPath | CSSSelector | str


def _get_selector(html: str | Selector) -> Selector:
    if isinstance(html, Selector):
        return html
    return Selector(text=html, type="html")


def extract_text(html: str | Selector, *selector: SelectorType) -> str:
    """
    从 HTML 中提取单个文本节点, 将依次尝试每个选择器直到找到匹配项.

    Args:
        html (str | Selector): HTML 内容或 parsel.Selector 对象.
        selector (tuple[SelectorType, ...]): 一组 XPath 或 CSS 选择器, 字符串视为 XPath 选择器.

    Returns:
        提取并清理后的文本, 未找到则返回空字符串.
    """
    sel = _get_selector(html)
    try:
        for s in selector:
            if isinstance(s, CSSSelector):
                f = sel.css
            else:
                f = sel.xpath
            result = f(s).get()
            if result:
                return clean_string(result)
        return ""
    except Exception:
        return ""


def extract_all_texts(html: str | Selector, *selector: SelectorType) -> list[str]:
    """
    提取所有匹配的文本节点, 将依次尝试每个选择器直到找到匹配项.

    Args:
        html (str | Selector): HTML 内容或 parsel.Selector 对象.
        selector (tuple[SelectorType, ...]): 一组 XPath 或 CSS 选择器, 字符串视为 XPath 选择器.

    Returns:
        list[str]: 所有匹配文本的列表, 每个文本都经过清理.
    """
    sel = _get_selector(html)
    try:
        for s in selector:
            if isinstance(s, CSSSelector):
                f = sel.css
            else:
                f = sel.xpath
            results = f(s).getall()
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

    对于返回类型为 FieldRes[T] 的方法, 可返回以下几种类型的值:
    1. T 类型的具体值: 直接用于构造 CrawlerResult.
    2. BaseSelector 子类实例 (XPath 或 CSSSelector): 表示一组选择器, 依次用于提取文本.
    3. None 或 T 类型的空值: 表示该字段在此页面上无法获取.
    4. self.NO_FIELD: 默认实现. 表示某字段在该网站上不存在.

    对于返回类型为 FieldValue[T] 的方法, T 较为复杂, 因此不支持情况 2 返回选择器.
    """

    NO_FIELD = _NoField()
    """表示某字段在该网站上不存在. 它和空值的区别在于, 该值不被视为获取失败."""

    async def title(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def actor(self, ctx: T, html: Selector) -> FieldRes[list[str]]:
        return self.NO_FIELD

    async def director(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def extrafanart(self, ctx: T, html: Selector) -> FieldRes[list[str]]:
        return self.NO_FIELD

    async def originalplot(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def originaltitle(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def outline(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def poster(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def publisher(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def release(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def runtime(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def score(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def series(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def studio(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def tag(self, ctx: T, html: Selector) -> FieldRes[list[str]]:
        return self.NO_FIELD

    async def thumb(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def trailer(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def wanted(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def year(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def actor_photo(self, ctx: T, html: Selector) -> FieldValue[dict]:
        return self.NO_FIELD

    async def image_cut(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def image_download(self, ctx: T, html: Selector) -> FieldValue[bool]:
        return self.NO_FIELD

    async def number(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def mosaic(self, ctx: T, html: Selector) -> FieldRes:
        return self.NO_FIELD

    async def parse(self, ctx: T, html: Selector) -> CrawlerResult:
        """
        调用所有字段的解析方法, 并构造 CrawlerResult.

        Args:
            html: 包含详情页 HTML 的 parsel Selector 对象.

        Returns:
            包含所有刮削数据的 CrawlerResult 对象.
        """
        return CrawlerResult(
            title=await self.str_field(ctx, self.title, html),
            actor=",".join(await self.str_list_field(ctx, self.actor, html)),
            director=await self.str_field(ctx, self.director, html),
            extrafanart=await self.str_list_field(ctx, self.extrafanart, html),
            originalplot=await self.str_field(ctx, self.originalplot, html),
            originaltitle=await self.str_field(ctx, self.originaltitle, html),
            outline=await self.str_field(ctx, self.outline, html),
            poster=await self.str_field(ctx, self.poster, html),
            publisher=await self.str_field(ctx, self.publisher, html),
            release=await self.str_field(ctx, self.release, html),
            runtime=await self.str_field(ctx, self.runtime, html),
            score=await self.str_field(ctx, self.score, html),
            series=await self.str_field(ctx, self.series, html),
            studio=await self.str_field(ctx, self.studio, html),
            tag=",".join(await self.str_list_field(ctx, self.tag, html)),
            thumb=await self.str_field(ctx, self.thumb, html),
            trailer=await self.str_field(ctx, self.trailer, html),
            wanted=await self.str_field(ctx, self.wanted, html),
            year=await self.str_field(ctx, self.year, html),
            actor_photo=unwrap_field_value(await self.actor_photo(ctx, html), {}),
            image_cut=await self.str_field(ctx, self.image_cut, html),
            image_download=unwrap_field_value(await self.image_download(ctx, html), False),
            number=await self.str_field(ctx, self.number, html),
            mosaic=await self.str_field(ctx, self.mosaic, html),
            javdbid="",
            source="",
            website="",
        )

    @classmethod
    async def str_field(cls, ctx: T, method: Callable[..., Awaitable[FieldRes[str]]], html: Selector) -> str:
        field_name = method.__name__
        method_res = await method(ctx, html)

        if method_res is None or method_res is cls.NO_FIELD or isinstance(method_res, _NoField):
            # todo 利用 nofield 信息
            ctx.debug(f"字段 '{field_name}' 在该网站不存在, 跳过.")
            return ""

        if isinstance(method_res, tuple | XPath | CSSSelector):
            # 执行选择器
            parsed_value = extract_text(html, *method_res)
        else:
            parsed_value = method_res

        return parsed_value

    @classmethod
    async def str_list_field(
        cls, ctx: T, method: Callable[..., Awaitable[FieldRes[list[str]]]], html: Selector
    ) -> list[str]:
        field_name = method.__name__
        method_res = await method(ctx, html)

        if method_res is None or method_res is cls.NO_FIELD or isinstance(method_res, _NoField):
            # todo 利用 nofield 信息
            ctx.debug(f"字段 '{field_name}' 在该网站不存在, 跳过.")
            return []

        if isinstance(method_res, tuple | XPath | CSSSelector):
            # 执行选择器
            parsed_value = extract_all_texts(html, *method_res)
        else:
            parsed_value = method_res

        return parsed_value


def unwrap_field_value[V = str](value: FieldValue[V], default: V) -> V:
    if value is None or isinstance(value, _NoField):
        return default
    return value
