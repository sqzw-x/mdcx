import re
from dataclasses import dataclass, field
from typing import Literal

from mdcx.config.models import Language


@dataclass
class FileInfo:
    """
    读取媒体文件获得的基础信息
    """

    number: str
    mosaic: str

    appoint_number: str
    appoint_url: str
    c_word: str
    cd_part: str
    destroyed: str
    file_ex: str
    file_name: str
    file_path: str
    file_show_name: str
    file_show_path: str
    folder_path: str
    has_sub: bool
    leak: str
    letters: str
    short_number: str
    sub_list: list[str]
    website_name: str  # 仅用于重新刮削
    wuma: str
    youma: str

    definition: str
    codec: str

    def crawler_input(self) -> "CrawlerInput":
        """
        将 FileInfo 转换为 CallCrawlerInput 类型
        """
        return CrawlerInput(
            appoint_number=self.appoint_number,
            appoint_url=self.appoint_url,
            file_path=self.file_path,
            number=self.number,
            mosaic=self.mosaic,
            short_number=self.short_number,
            language=Language.UNDEFINED,
            org_language=Language.UNDEFINED,
        )

    def crawl_task(self) -> "CrawlTask":
        """
        将 FileInfo 转换为 CrawlTask 类型
        """
        return CrawlTask(
            appoint_number=self.appoint_number,
            appoint_url=self.appoint_url,
            file_path=self.file_path,
            number=self.number,
            mosaic=self.mosaic,
            short_number=self.short_number,
            has_sub=self.has_sub,
            c_word=self.c_word,
            leak=self.leak,
            wuma=self.wuma,
            youma=self.youma,
            cd_part=self.cd_part,
            destroyed=self.destroyed,
            website_name=self.website_name,
            language=Language.UNDEFINED,
            org_language=Language.UNDEFINED,
        )

    @classmethod
    def empty(cls) -> "FileInfo":
        """
        返回一个空的 FileInfo 实例
        """
        return cls(
            number="",
            mosaic="",
            appoint_number="",
            appoint_url="",
            c_word="",
            cd_part="",
            destroyed="",
            file_ex="",
            file_name="",
            file_path="",
            file_show_name="",
            file_show_path="",
            folder_path="",
            has_sub=False,
            leak="",
            letters="",
            short_number="",
            sub_list=[],
            website_name="",
            wuma="",
            youma="",
            definition="",
            codec="",
        )


@dataclass
class CrawlerInput:
    """调用单个 crawler 所需输入"""

    appoint_number: str
    appoint_url: str
    file_path: str
    mosaic: str
    number: str
    short_number: str

    # 向后兼容
    language: Language
    org_language: Language

    @classmethod
    def empty(cls) -> "CrawlerInput":
        return FileInfo.empty().crawler_input()


@dataclass
class CrawlTask(CrawlerInput):
    """刮削一个文件所需的信息"""

    c_word: str
    cd_part: str
    destroyed: str
    has_sub: bool
    leak: str
    website_name: str  # 用于重新刮削时指定网站
    wuma: str
    youma: str

    @classmethod
    def empty(cls) -> "CrawlTask":
        return FileInfo.empty().crawl_task()


@dataclass
class BaseCrawlerResult:
    """
    爬虫结果的公共基础类型, 包含 CrawlerResult 和 CrawlersResult 的共同字段
    (注释由 AI 生成, 仅供参考)
    """

    number: str  # 番号
    mosaic: str  # 马赛克类型（有码/无码）
    image_download: bool  # 是否需要下载图片
    # 以下字段会从多个来源 reduce 到一个最终结果
    actors: list[str]
    # actor: str  # 演员名称，逗号分隔
    all_actors: list[str]
    # all_actor: str  # 包含男演员的所有演员名称
    directors: list[str]
    # director: str  # 导演
    extrafanart: list[str]  # 额外剧照URL列表
    originalplot: str  # 原始简介（日文）
    originaltitle: str  # 原始标题（日文）
    outline: str  # 简介
    poster: str  # 海报URL
    publisher: str  # 发行商
    release: str  # 发行日期
    runtime: str  # 片长（分钟）
    score: str  # 评分
    series: str  # 系列
    studio: str  # 制作商
    tags: list[str]
    # tag: str  # 标签，逗号分隔
    thumb: str  # 缩略图URL # todo 需修改为 list[str] 支持多个候选地址
    title: str  # 标题
    trailer: str  # 预告片URL
    wanted: str
    year: str  # 发行年份 # todo 移除. 总是可以从 release 推断

    # 用于写入 nfo 的特殊字段
    javdbid: str  # JavDB ID

    @property
    def country(self) -> Literal["CN", "JP", "US"]:
        """
        根据 mosaic 字段返回国家代码
        """
        country = "JP"
        if self.mosaic in ["国产", "國產"]:
            country = "CN"
        elif re.findall(r"\.\d{2}\.\d{2}\.\d{2}", self.number):
            country = "US"
        return country

    @property
    def tag(self) -> str:
        """
        向后兼容. 返回标签字段, 如果 tags 不为空则使用 tags, 否则使用 tag
        """
        return ",".join(self.tags)

    @tag.setter
    def tag(self, value: str):
        """
        向后兼容. 设置标签字段, 将逗号分隔的字符串转换为列表
        """
        self.tags = value.split(",") if value else []

    @property
    def actor(self) -> str:
        """
        向后兼容. 返回演员字段, 如果 actors 不为空则使用 actors, 否则使用 actor
        """
        return ",".join(self.actors)

    @actor.setter
    def actor(self, value: str):
        """
        向后兼容. 设置演员字段, 将逗号分隔的字符串转换为列表
        """
        self.actors = value.split(",") if value else []

    @property
    def all_actor(self) -> str:
        """
        向后兼容. 返回所有演员字段, 如果 all_actors 不为空则使用 all_actors, 否则使用 all_actor
        """
        return ",".join(self.all_actors)

    @all_actor.setter
    def all_actor(self, value: str):
        """
        向后兼容. 设置所有演员字段, 将逗号分隔的字符串转换为列表
        """
        self.all_actors = value.split(",") if value else []

    @property
    def director(self) -> str:
        """
        向后兼容. 返回导演字段, 如果 directors 不为空则使用 directors, 否则使用 director
        """
        return ",".join(self.directors)

    @director.setter
    def director(self, value: str):
        """
        向后兼容. 设置导演字段, 将逗号分隔的字符串转换为列表
        """
        self.directors = value.split(",") if value else []

    @classmethod
    def empty(cls) -> "BaseCrawlerResult":
        """
        返回一个空的 BaseCrawlerResultDataClass 实例
        """
        return cls(
            number="",
            mosaic="",
            image_download=False,
            actors=[],
            all_actors=[],
            directors=[],
            extrafanart=[],
            originalplot="",
            originaltitle="",
            outline="",
            poster="",
            publisher="",
            release="",
            runtime="",
            score="0.0",
            series="",
            studio="",
            tags=[],
            thumb="",
            title="",
            trailer="",
            wanted="",
            year="",
            javdbid="",
        )


@dataclass
class CrawlerResult(BaseCrawlerResult):
    """
    单一网站爬虫返回的结果
    """

    image_cut: str  # 图片裁剪方式
    source: str  # 数据来源（爬虫名称）
    website: str  # 网站地址

    @classmethod
    def empty(cls) -> "CrawlerResult":
        """
        返回一个空的 CrawlerResultDataclass 实例
        """
        return cls(
            **BaseCrawlerResult.empty().__dict__,
            image_cut="",
            source="",
            website="",
        )


@dataclass
class CrawlerDebugInfo:
    execution_time: float = 0.0
    error: Exception | None = None
    search_urls: list[str] | None = None
    detail_urls: list[str] | None = None
    logs: list[str] = field(default_factory=list)


@dataclass
class CrawlerResponse:
    """
    封装单个爬虫的完整执行信息
    """

    debug_info: CrawlerDebugInfo
    data: CrawlerResult | None = None


@dataclass
class CrawlersResult(BaseCrawlerResult):
    """
    整合所有网站的爬虫结果
    """

    # 以下用于后续下载资源
    actor_amazon: list[str]  # 用于 Amazon 搜索的演员名称
    amazon_orginaltitle_actor: str  # 用于 Amazon 搜索的原始标题中的演员
    thumb_list: list[tuple[str, str]]  # 所有来源的缩略图URL列表
    originaltitle_amazon: str  # 用于 Amazon 搜索的原始标题

    # 用于 log
    fields_info: str  # 字段来源信息

    # 字段来源 # todo 用一个与 BaseCrawlerResult 字段一一对应的字典表示
    extrafanart_from: str
    outline_from: str
    poster_from: str
    thumb_from: str
    trailer_from: str
    version: int  # 版本信息, 可能没用

    # in FileInfo
    # 除 letters 不确定外, 其它字段是只读的, 所以后续流程可以直接从 FileInfo 获取
    letters: str  # 番号字母部分, 理论上 get_file_info 函数会返回这个字段

    @classmethod
    def empty(cls) -> "CrawlersResult":
        """
        返回一个空的 CrawlersResultDataClass 实例
        """
        return cls(
            **BaseCrawlerResult.empty().__dict__,
            actor_amazon=[],
            amazon_orginaltitle_actor="",
            thumb_list=[],
            originaltitle_amazon="",
            fields_info="",
            extrafanart_from="",
            outline_from="",
            poster_from="",
            thumb_from="",
            trailer_from="",
            version=0,
            letters="",
        )


@dataclass
class OtherInfo:
    # 由 creat_folder 写入, move_movie 使用
    del_file_path: bool
    dont_move_movie: bool
    # 用于控制 add_mark 是否添加水印, 有多个写入来源
    fanart_marked: bool
    poster_marked: bool
    thumb_marked: bool
    # 其它图片获取过程所需字段
    fanart_path: str
    poster_path: str
    thumb_path: str
    poster_big: bool
    poster_size: tuple[int, int]
    thumb_size: tuple[int, int]

    @classmethod
    def empty(cls) -> "OtherInfo":
        """
        返回一个空的 OtherInfo 实例
        """
        return cls(
            del_file_path=False,
            dont_move_movie=False,
            fanart_marked=True,
            poster_marked=True,
            thumb_marked=True,
            fanart_path="",
            poster_path="",
            thumb_path="",
            poster_big=False,
            poster_size=(0, 0),
            thumb_size=(0, 0),
        )


@dataclass
class ScrapeResult:
    file_info: FileInfo
    data: CrawlersResult
    other: OtherInfo


@dataclass
class ShowData(ScrapeResult):
    """
    用于主界面显示
    """

    show_name: str

    @classmethod
    def empty(cls) -> "ShowData":
        """
        返回一个空的 ShowDataDataclass 实例
        """
        return cls(
            file_info=FileInfo.empty(),
            data=CrawlersResult.empty(),
            other=OtherInfo.empty(),
            show_name="",
        )
