import re
from dataclasses import dataclass, field
from re import Pattern

from mdcx.models.types import CrawlerDebugInfo, CrawlerInput, CrawlerResult
from mdcx.utils.dataclass import update_valid


class XPath(str): ...


class CSSSelector(str): ...


class NotSupport: ...


NOT_SUPPORT = NotSupport()

type FieldValue[T = str] = T | None | NotSupport
type FieldRes[T = str] = FieldValue[T]

type SelectorType = XPath | CSSSelector | Pattern | str


def c(selector: str) -> CSSSelector:
    return CSSSelector(selector)


def x(selector: str) -> XPath:
    return XPath(selector)


def r(pattern: str) -> Pattern:
    return re.compile(pattern)


def is_valid[T](v: FieldValue[T]) -> bool:
    return bool(v) and not isinstance(v, NotSupport)


@dataclass
class CrawlerData:
    title: FieldValue = NOT_SUPPORT
    actors: FieldValue[list[str]] = NOT_SUPPORT
    all_actors: FieldValue[list[str]] = NOT_SUPPORT
    directors: FieldValue[list[str]] = NOT_SUPPORT
    extrafanart: FieldValue[list[str]] = NOT_SUPPORT
    originalplot: FieldValue = NOT_SUPPORT
    originaltitle: FieldValue = NOT_SUPPORT
    outline: FieldValue = NOT_SUPPORT
    poster: FieldValue = NOT_SUPPORT
    publisher: FieldValue = NOT_SUPPORT
    release: FieldValue = NOT_SUPPORT
    runtime: FieldValue = NOT_SUPPORT
    score: FieldValue = NOT_SUPPORT
    series: FieldValue = NOT_SUPPORT
    studio: FieldValue = NOT_SUPPORT
    tags: FieldValue[list[str]] = NOT_SUPPORT
    thumb: FieldValue = NOT_SUPPORT
    trailer: FieldValue = NOT_SUPPORT
    wanted: FieldValue = NOT_SUPPORT
    year: FieldValue = NOT_SUPPORT
    image_cut: FieldValue = NOT_SUPPORT
    image_download: FieldValue[bool] = NOT_SUPPORT
    number: FieldValue = NOT_SUPPORT
    mosaic: FieldValue = NOT_SUPPORT
    externalId: FieldValue = NOT_SUPPORT
    source: FieldValue = NOT_SUPPORT
    url: FieldValue = NOT_SUPPORT

    def to_result(self) -> "CrawlerResult":
        return update_valid(CrawlerResult.empty(), self, is_valid)


class CralwerException(Exception): ...


@dataclass
class Context:
    input: CrawlerInput  # crawler 的原始输入
    debug_info: "CrawlerDebugInfo" = field(default_factory=CrawlerDebugInfo)
    show_msgs: list[str] = field(default_factory=list)

    def show(self, message: str):
        """添加向用户展示的消息."""
        self.show_msgs.append(message)

    def debug(self, message: str):
        """添加调试消息."""
        self.debug_info.logs.append(message)
