from dataclasses import asdict, dataclass, field
from typing import Any

from mdcx.models.types import CrawlerInput, CrawlerResult


class XPath(str): ...


class CSSSelector(str): ...


class _NoField: ...


type FieldValue[T = str] = T | None | _NoField
type FieldRes[T = str] = tuple[XPath | CSSSelector, ...] | FieldValue[T]

type SelectorType = XPath | CSSSelector | str


@dataclass
class CrawlerData:
    title: FieldValue
    actor: FieldValue[list[str]]
    all_actor: FieldValue[list[str]]
    director: FieldValue
    extrafanart: FieldValue[list[str]]
    originalplot: FieldValue
    originaltitle: FieldValue
    outline: FieldValue
    poster: FieldValue
    publisher: FieldValue
    release: FieldValue
    runtime: FieldValue
    score: FieldValue
    series: FieldValue
    studio: FieldValue
    tag: FieldValue[list[str]]
    thumb: FieldValue
    trailer: FieldValue
    wanted: FieldValue
    year: FieldValue
    actor_photo: FieldValue[dict]
    image_cut: FieldValue
    image_download: FieldValue[bool]
    number: FieldValue
    mosaic: FieldValue
    externalId: FieldValue
    source: FieldValue
    website: FieldValue

    def to_json(self) -> dict[str, Any]:
        """将 CrawlerData 转换为 JSON 兼容的字典, 忽略值为 _NoField 的字段."""
        result: dict[str, Any] = {}
        for key, value in asdict(self).items():
            if not isinstance(value, _NoField):
                result[key] = value
        return result

    def to_result(self) -> "CrawlerResult":
        default = CrawlerResult.empty()
        result: dict[str, Any] = {}
        for key, value in asdict(self).items():
            if isinstance(value, _NoField) or value is None:
                result[key] = getattr(default, key)
            else:
                result[key] = value
        return CrawlerResult(**result)

    @classmethod
    def empty(cls) -> "CrawlerData":
        """创建一个空的 CrawlerData 实例, 所有字段都为 _NoField."""
        return cls(
            title=_NoField(),
            actor=_NoField(),
            all_actor=_NoField(),
            director=_NoField(),
            extrafanart=_NoField(),
            originalplot=_NoField(),
            originaltitle=_NoField(),
            outline=_NoField(),
            poster=_NoField(),
            publisher=_NoField(),
            release=_NoField(),
            runtime=_NoField(),
            score=_NoField(),
            series=_NoField(),
            studio=_NoField(),
            tag=_NoField(),
            thumb=_NoField(),
            trailer=_NoField(),
            wanted=_NoField(),
            year=_NoField(),
            actor_photo=_NoField(),
            image_cut=_NoField(),
            image_download=_NoField(),
            number=_NoField(),
            mosaic=_NoField(),
            externalId=_NoField(),
            source=_NoField(),
            website=_NoField(),
        )


class CralwerException(Exception): ...


@dataclass
class Context:
    input: CrawlerInput  # crawler 的原始输入
    show_logs: list[str] = field(default_factory=list)
    debug_logs: list[str] = field(default_factory=list)

    def show(self, message: str):
        self.show_logs.append(message)

    def debug(self, message: str):
        self.debug_logs.append(message)
