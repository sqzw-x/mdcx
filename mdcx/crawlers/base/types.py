from dataclasses import asdict, dataclass, field
from typing import Any

from mdcx.models.types import CrawlerInput, CrawlerResult


class XPath(str): ...


class CSSSelector(str): ...


class _NoField: ...


NO_FIELD = _NoField()

type FieldValue[T = str] = T | None | _NoField
type FieldRes[T = str] = tuple[XPath | CSSSelector, ...] | FieldValue[T]

type SelectorType = XPath | CSSSelector | str


@dataclass
class CrawlerData:
    title: FieldValue = NO_FIELD
    actors: FieldValue[list[str]] = NO_FIELD
    all_actors: FieldValue[list[str]] = NO_FIELD
    directors: FieldValue[list[str]] = NO_FIELD
    extrafanart: FieldValue[list[str]] = NO_FIELD
    originalplot: FieldValue = NO_FIELD
    originaltitle: FieldValue = NO_FIELD
    outline: FieldValue = NO_FIELD
    poster: FieldValue = NO_FIELD
    publisher: FieldValue = NO_FIELD
    release: FieldValue = NO_FIELD
    runtime: FieldValue = NO_FIELD
    score: FieldValue = NO_FIELD
    series: FieldValue = NO_FIELD
    studio: FieldValue = NO_FIELD
    tags: FieldValue[list[str]] = NO_FIELD
    thumb: FieldValue = NO_FIELD
    trailer: FieldValue = NO_FIELD
    wanted: FieldValue = NO_FIELD
    year: FieldValue = NO_FIELD
    actor_photo: FieldValue[dict] = NO_FIELD
    image_cut: FieldValue = NO_FIELD
    image_download: FieldValue[bool] = NO_FIELD
    number: FieldValue = NO_FIELD
    mosaic: FieldValue = NO_FIELD
    externalId: FieldValue = NO_FIELD
    source: FieldValue = NO_FIELD
    website: FieldValue = NO_FIELD

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
                if key in ("actor", "all_actor", "extrafanart", "tag"):
                    result[key] = ",".join(value) if isinstance(value, list) else value
        return CrawlerResult(**result)


class CralwerException(Exception): ...


@dataclass
class Context:
    input: CrawlerInput  # crawler 的原始输入
    show_logs: list[str] = field(default_factory=list)
    debug_logs: list[str] = field(default_factory=list)

    def show(self, message: str):
        """添加向用户展示的消息."""
        self.show_logs.append(message)

    def debug(self, message: str):
        """添加调试消息."""
        self.debug_logs.append(message)
