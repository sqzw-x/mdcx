from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class JsonData(TypedDict):
    _4K: str
    actor_amazon: list[str]
    actor_href: str
    actor_photo: dict
    actor: str
    all_actor_photo: dict
    all_actor: str
    amazon_orginaltitle_actor: str
    appoint_number: str
    appoint_url: str
    c_word: str
    cd_part: str
    country: str
    definition: str
    del_file_path: bool
    destroyed: str
    director: str
    dont_move_movie: bool
    extrafanart_from: str
    extrafanart: list[str]
    fanart_marked: bool
    fanart_path: str
    fields_info: str
    file_path: str
    folder_name: str
    has_sub: bool
    image_cut: str
    image_download: bool
    javdbid: str
    leak: str
    letters: str
    mosaic: str
    naming_file: str
    naming_media: str
    number: str
    originalplot: str
    originaltitle_amazon: str
    originaltitle: str
    outline_from: str
    outline: str
    poster_big: bool
    poster_from: str
    poster_marked: bool
    poster_path: str
    poster_size: tuple[int, int]
    poster: str
    publisher: str
    release: str
    runtime: str
    score: str
    series: str
    short_number: str
    source: str
    studio: str
    tag: str
    thumb_from: str
    thumb_list: list[tuple[str, str]]
    thumb_marked: bool
    thumb_path: str
    thumb_size: tuple[int, int]
    thumb: str
    title: str
    trailer_from: str
    trailer: str
    version: int
    wanted: str
    website_name: str
    website: str
    wuma: str
    year: str
    youma: str


def new_json_data() -> JsonData:
    return {
        "definition": "",
        "actor": "",
        "thumb_size": (0, 0),
        "poster_size": (0, 0),
        "poster_big": False,
        "image_cut": "",
        "poster_marked": True,
        "thumb_marked": True,
        "fanart_marked": True,
        "thumb_list": [],
        "poster_path": "",
        "thumb_path": "",
        "fanart_path": "",
        "thumb": "",
        "poster": "",
        "extrafanart": [],
        "actor_amazon": [],
        "actor_href": "",
        "all_actor": "",
        "actor_photo": {},
        "all_actor_photo": {},
        "amazon_orginaltitle_actor": "",
        "file_path": "",
        "del_file_path": False,
        "dont_move_movie": False,
        "title": "",
        "outline": "",
        "folder_name": "",
        "version": 0,
        "image_download": False,
        "outline_from": "",
        "thumb_from": "",
        "poster_from": "",
        "extrafanart_from": "",
        "trailer_from": "",
        "short_number": "",
        "appoint_number": "",
        "appoint_url": "",
        "website_name": "",
        "fields_info": "",
        "number": "",
        "letters": "",
        "has_sub": False,
        "c_word": "",
        "cd_part": "",
        "destroyed": "",
        "leak": "",
        "wuma": "",
        "youma": "",
        "mosaic": "",
        "tag": "",
        "_4K": "",
        "source": "",
        "release": "",
        "year": "",
        "javdbid": "",
        "score": "0.0",
        "originaltitle": "",
        "studio": "",
        "publisher": "",
        "runtime": "",
        "director": "",
        "website": "",
        "series": "",
        "trailer": "",
        "originaltitle_amazon": "",
        "originalplot": "",
        "wanted": "",
        "naming_media": "",
        "naming_file": "",
        "country": "",
    }


# ========================================================================
# 以下为 core 各模块各函数所需输入输出. 以 Input 结尾代表只读, Context 会被读写, Result 代表返回值
# ========================================================================


class BaseCrawlerResult(TypedDict):
    """
    爬虫结果的公共基础类型，包含 CrawlerResult 和 CrawlersResult 的共同字段
    (注释由 AI 生成, 仅供参考)
    """

    number: str  # 番号
    mosaic: str  # 马赛克类型（有码/无码）
    image_download: bool  # 是否需要下载图片
    # 以下字段会从多个来源 reduce 到一个最终结果
    actor: str  # 演员名称，逗号分隔
    director: str  # 导演
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
    tag: str  # 标签，逗号分隔
    thumb: str  # 缩略图URL
    title: str  # 标题
    trailer: str  # 预告片URL
    wanted: str
    year: str  # 发行年份


class CrawlerResult(BaseCrawlerResult):
    """
    单一网站爬虫返回的结果
    """

    actor_photo: dict  # 演员照片信息
    # todo 在 v1 里此字段似乎并未被使用, 唯一需要的位置是 cut_thumb_to_poster, 而其值是在调用方 poster_download 中推断出来的
    image_cut: str  # 图片裁剪方式
    source: str  # 数据来源（爬虫名称）
    website: str  # 网站地址


class CrawlersResult(BaseCrawlerResult):
    """
    整合所有网站的爬虫结果
    """

    # 以下用于后续下载资源
    actor_amazon: list[str]  # 用于 Amazon 搜索的演员名称
    all_actor_photo: dict  # 演员照片信息
    all_actor: str  # 所有来源的演员名称
    amazon_orginaltitle_actor: str  # 用于 Amazon 搜索的原始标题中的演员
    thumb_list: list  # 所有来源的缩略图URL列表
    originaltitle_amazon: str  # 用于 Amazon 搜索的原始标题
    # 用于写入 nfo 的特殊字段
    javdbid: str  # JavDB ID

    # 以下直接复制 config, 无意义
    # folder_name: str  # 文件夹命名规则
    # naming_file: str  # 文件命名规则
    # naming_media: str  # 媒体命名规则

    # 用于 log
    fields_info: str  # 字段来源信息

    # 字段来源
    extrafanart_from: str
    outline_from: str
    poster_from: str
    thumb_from: str
    trailer_from: str
    version: int  # 版本信息, 可能没用

    # in FileInfo
    # 除 letters 不确定外, 其它字段是只读的, 所以后续流程可以直接从 FileInfo 获取
    letters: str  # 番号字母部分, 理论上 get_file_info 函数会返回这个字段

    # short_number: str  # 素人番号的短形式（不带前缀数字）, 参与刮削决策
    # # in CallCrawlerInput
    # c_word: str  # 中文字幕标识
    # cd_part: str  # CD分集信息
    # destroyed: str  # 是否是无码破解
    # has_sub: bool  # 是否有字幕
    # leak: str  # 是否是无码流出
    # website_name: str
    # wuma: str  # 是否是无码
    # youma: str  # 是否是有码
    # # in CallCrawlerInput
    # appoint_number: str  # 指定番号
    # appoint_url: str  # 指定URL
    # file_path: str  # 文件路径


@dataclass
class FileInfo:
    """
    新版本的文件信息数据类，整合了 get_file_info 函数的所有返回值
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

    def crawler_input(self) -> "CallCrawlerInput":
        """
        将 FileInfo 转换为 CallCrawlerInput 类型
        """
        return CallCrawlerInput(
            appoint_number=self.appoint_number,
            appoint_url=self.appoint_url,
            file_path=self.file_path,
            number=self.number,
            mosaic=self.mosaic,
            short_number=self.short_number,
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


# crawler =================================================================
@dataclass
class CallCrawlerInput:
    """调用单个 crawler 所需输入"""

    appoint_number: str
    appoint_url: str
    file_path: str
    mosaic: str
    number: str
    short_number: str


@dataclass
class CrawlTask(CallCrawlerInput):
    """刮削一个文件所需的信息."""

    c_word: str
    cd_part: str
    destroyed: str
    has_sub: bool
    leak: str
    website_name: str  # 用于重新刮削时指定网站
    wuma: str
    youma: str


@dataclass
class BaseCrawlerResultDataClass:
    """
    爬虫结果的公共基础类型，包含 CrawlerResult 和 CrawlersResult 的共同字段
    (注释由 AI 生成, 仅供参考)
    """

    number: str  # 番号
    mosaic: str  # 马赛克类型（有码/无码）
    image_download: bool  # 是否需要下载图片
    # 以下字段会从多个来源 reduce 到一个最终结果
    actor: str  # 演员名称，逗号分隔
    director: str  # 导演
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
    tag: str  # 标签，逗号分隔
    thumb: str  # 缩略图URL
    title: str  # 标题
    trailer: str  # 预告片URL
    wanted: str
    year: str  # 发行年份

    # 用于写入 nfo 的特殊字段
    javdbid: str  # JavDB ID

    @classmethod
    def empty(cls) -> "BaseCrawlerResultDataClass":
        """
        返回一个空的 BaseCrawlerResultDataClass 实例
        """
        return cls(
            number="",
            mosaic="",
            image_download=False,
            actor="",
            director="",
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
            tag="",
            thumb="",
            title="",
            trailer="",
            wanted="",
            year="",
            javdbid="",
        )


@dataclass
class CrawlerResultDataclass(BaseCrawlerResultDataClass):
    """
    单一网站爬虫返回的结果
    """

    actor_photo: dict  # 演员照片信息
    image_cut: str  # 图片裁剪方式
    source: str  # 数据来源（爬虫名称）
    website: str  # 网站地址

    @classmethod
    def empty(cls) -> "CrawlerResultDataclass":
        """
        返回一个空的 CrawlerResultDataclass 实例
        """
        return cls(
            **BaseCrawlerResultDataClass.empty().__dict__,
            actor_photo={},
            image_cut="",
            source="",
            website="",
        )


@dataclass
class CrawlersResultDataClass(BaseCrawlerResultDataClass):
    """
    整合所有网站的爬虫结果
    """

    # 以下用于后续下载资源
    actor_amazon: list[str]  # 用于 Amazon 搜索的演员名称
    all_actor_photo: dict  # 演员照片信息
    all_actor: str  # 所有来源的演员名称
    amazon_orginaltitle_actor: str  # 用于 Amazon 搜索的原始标题中的演员
    thumb_list: list[tuple[str, str]]  # 所有来源的缩略图URL列表
    originaltitle_amazon: str  # 用于 Amazon 搜索的原始标题

    # 用于 log
    fields_info: str  # 字段来源信息

    # 字段来源
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
    def empty(cls) -> "CrawlersResultDataClass":
        """
        返回一个空的 CrawlersResultDataClass 实例
        """
        return cls(
            **BaseCrawlerResultDataClass.empty().__dict__,
            actor_amazon=[],
            all_actor_photo={},
            all_actor="",
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
class ShowDataDataclass:
    """
    用于主界面显示的数据类
    """

    file_info: FileInfo
    data: CrawlersResultDataClass | None
    other: OtherInfo | None
    show_name: str = ""  # 显示名称, 用于主界面显示

    @classmethod
    def empty(cls) -> "ShowDataDataclass":
        """
        返回一个空的 ShowDataDataclass 实例
        """
        return cls(
            file_info=FileInfo.empty(),
            data=CrawlersResultDataClass.empty(),
            other=OtherInfo.empty(),
            show_name="",
        )


@dataclass
class ScrapeResult:
    file_info: FileInfo
    data: CrawlersResultDataClass
    other: OtherInfo


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


# utils ============================================================


class TemplateInput(BaseCrawlerResult):
    """
    用于 render_name_template 根据用户模版生成文件名

    covered by: FileInfo + CrawlersResult
    """

    # in FileInfo
    c_word: str
    destroyed: str
    leak: str
    letters: str
    wuma: str
    youma: str
    definition: str
    # in CrawlersResult
    all_actor: str


class GetVideoSizeContext(TypedDict):
    definition: str  # 在此处新建, 考虑移动到 FileInfo
    _4K: str  # 在此处新建, 等于 -definition, 仅用于显示, 考虑移除
    # in BaseCrawlerResult
    tag: str  # 根据用户配置, 可能将分辨率添加到 tag


class ShowData(BaseCrawlerResult):
    """
    ref: ManualConfig.SHOW_KEY
    """

    # in CrawlersResult
    all_actor: str
    javdbid: str

    # in FileInfo
    cd_part: str
    has_sub: bool
    letters: str

    # website: str # remove

    # in BaseCrawlerResult
    # actor: str
    # director: str
    # mosaic: str
    # number: str
    # originalplot: str
    # originaltitle: str
    # outline: str
    # publisher: str
    # release: str
    # runtime: str
    # score: str
    # series: str
    # studio: str
    # tag: str
    # title: str
    # trailer: str
    # wanted: str
    # year: str


# file =================================================================
class GetOutPutNameContext(TemplateInput):
    # in FileInfo
    cd_part: str  # read-only


class DealOldFilesContext(TypedDict):
    poster_marked: bool
    thumb_marked: bool
    fanart_marked: bool
    poster_path: str
    thumb_path: str
    fanart_path: str
    # in BaseCrawlerResult
    number: str


class MoveMovieContext(TypedDict):
    dont_move_movie: bool
    del_file_path: bool
    # in FileInfo
    file_path: str
    cd_part: str


class CreateFolderContext(TypedDict):
    dont_move_movie: bool
    del_file_path: bool
    thumb_path: str
    poster_path: str
    # in BaseCrawlerResult
    title: str


# image ============================================================
class AddMarkInput(TypedDict):
    fanart_marked: bool
    poster_marked: bool
    thumb_marked: bool
    poster_path: str
    thumb_path: str
    fanart_path: str
    # in FileInfo
    definition: str
    has_sub: bool
    # in BaseCrawlerResult
    mosaic: str


class CutThumbContext(TypedDict):
    # in CrawlerResult
    image_cut: str
    # in CrawlersResult
    poster_from: str


# web ============================================================
class ExtraFanartInput(TypedDict):
    # in CrawlersResult
    extrafanart_from: str
    # in BaseCrawlerResult
    extrafanart: list[str]


class TrailerInput(TypedDict):
    # in CrawlersResult
    trailer_from: str
    # in BaseCrawlerResult
    number: str
    trailer: str


class ThumbContext(TypedDict):
    fanart_path: str
    poster_big: bool
    poster_path: str
    thumb_marked: bool
    thumb_path: str
    thumb_size: tuple[int, int]
    # in CrawlersResult
    thumb_list: list[tuple[str, str]]
    thumb_from: str
    poster_from: str
    trailer_from: str
    letters: str
    # in FileInfo
    cd_part: str
    # in BaseCrawlerResult
    number: str
    thumb: str
    poster: str
    trailer: str


class PosterContext(CutThumbContext):
    fanart_path: str
    poster_path: str
    poster_size: tuple[int, int]
    thumb_marked: bool
    thumb_path: str
    poster_marked: bool
    poster_big: bool
    # in CrawlersResult
    actor_amazon: list[str]
    amazon_orginaltitle_actor: str
    originaltitle_amazon: str
    letters: str
    # in FileInfo
    cd_part: str
    # in BaseCrawlerResult
    image_download: bool
    mosaic: str
    number: str
    poster: str


class FanartContext(TypedDict):
    thumb_path: str
    fanart_path: str
    thumb_marked: bool
    fanart_marked: bool
    # in FileInfo
    cd_part: str
    # in BaseCrawlerResult
    number: str


class AmazonContext(TypedDict):
    # in CrawlersResult
    poster_from: str
    amazon_orginaltitle_actor: str
    # in BaseCrawlerResult
    number: str
    poster: str


# translate =================================================================
class TransTitleOutlineContext(TypedDict):
    # in CrawlersResult
    outline_from: str
    # in BaseCrawlerResult
    title: str
    outline: str
    mosaic: str
    # in FileInfo
    cd_part: str  # read-only


class TranslateActorContext(TypedDict):
    actor_href: str  # 此字段在此创建, 是从映射表读取所得, 仅用于主界面显示, 考虑移除
    # in CrawlersResult
    all_actor: str
    # in BaseCrawlerResult
    mosaic: str
    number: str
    actor: str


class TranslateInfoContext(TypedDict):
    # in FileInfo
    has_sub: bool
    letters: str
    # in BaseCrawlerResult
    actor: str
    director: str
    mosaic: str
    number: str
    publisher: str
    series: str
    studio: str
    tag: str


# nfo =================================================================
# convert to: CrawlersResult + FileInfo + *_path
class WriteNfoInput(BaseCrawlerResult):
    fanart_path: str
    poster_path: str
    thumb_path: str

    # in CrawlersResult
    all_actor: str
    originaltitle_amazon: str
    outline_from: str  # 剧情简介来源

    # 在 v1 中国产网站会返回 CN, 其它网站无结果
    # 考虑到此时 mosaic==国产, 此字段可推导得出, 因此移除
    # country: str

    # todo 此字段是某 crawler 实际请求的 url
    # 在 v1 中, 会取标题的第一个来源的值
    # 鉴于此值并不是 emby 所需的, 考虑移除
    # website: str

    # in FileInfo
    letters: str
    cd_part: str  # CD分卷信息
    # for render_name_template
    # c_word: str
    # definition: str
    # destroyed: str
    # leak: str
    # wuma: str
    # youma: str


class ReadNfoResult(WriteNfoInput):
    source: str  # 只用于显示, 理论上多来源刮削时此字段无效, 考虑移除
    tag_only: str  # 仅在此出现
    # in CrawlersResult
    thumb_list: list[tuple[str, str]]
    poster_from: str
    thumb_from: str
    extrafanart_from: str
    trailer_from: str
    actor_amazon: list[str]
