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


class BaseCrawlerResult(TypedDict):
    """
    爬虫结果的公共基础类型，包含 CrawlerResult 和 CrawlersResult 的共同字段
    (注释由 AI 生成, 仅供参考)
    """

    actor: str  # 演员名称，逗号分隔
    director: str  # 导演
    extrafanart: list[str]  # 额外剧照URL列表
    image_download: bool  # 是否需要下载图片
    mosaic: str  # 马赛克类型（有码/无码）
    number: str  # 番号
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
    year: str  # 发行年份


class CrawlerResult(BaseCrawlerResult):
    """
    单一网站爬虫返回的结果
    """

    actor_photo: dict  # 演员照片信息
    image_cut: str  # 图片裁剪方式
    source: str  # 数据来源（爬虫名称）
    wanted: str  # 期望信息
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


# utils ============================================================
class TemplateInput(BaseCrawlerResult):
    """
    用于 render_name_template 根据用户模版生成文件名
    """

    all_actor: str
    c_word: str
    definition: str
    destroyed: str
    leak: str
    letters: str
    wanted: str
    wuma: str
    youma: str


class GetVideoSizeContext(TypedDict):
    definition: str
    _4K: str
    tag: str


class ShowData(BaseCrawlerResult):
    """
    ref: ManualConfig.SHOW_KEY
    """

    # actor: str
    all_actor: str
    cd_part: str
    # director: str
    has_sub: bool
    javdbid: str
    letters: str
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
    wanted: str
    website: str
    # year: str


# file =================================================================
class GetFolderPathContext(TemplateInput):
    folder_name: str


class GetOutPutNameContext(GetFolderPathContext):
    cd_part: str


class DealOldFilesContext(TypedDict):
    number: str
    poster_marked: bool
    thumb_marked: bool
    fanart_marked: bool
    poster_path: str
    thumb_path: str
    fanart_path: str


class MoveMovieContext(TypedDict):
    dont_move_movie: bool
    del_file_path: bool
    file_path: str
    cd_part: str


class CreateFolderContext(TypedDict):
    dont_move_movie: bool
    del_file_path: bool
    title: str
    thumb_path: str
    poster_path: str


@dataclass
class AssetsInfo: ...


# image ============================================================
class AddMarkInput(TypedDict):
    has_sub: bool
    mosaic: str
    definition: str
    poster_path: str
    thumb_path: str
    fanart_path: str


class CutThumbContext(TypedDict):
    image_cut: str
    poster_from: str


# web ============================================================
class ExtraFanartInput(TypedDict):
    extrafanart: list[str]
    extrafanart_from: str


class TrailerInput(TypedDict):
    number: str
    trailer: str
    trailer_from: str


class ThumbContext(TypedDict):
    poster_path: str
    thumb_path: str
    fanart_path: str
    thumb_list: list[tuple[str, str]]
    thumb_from: str
    thumb_size: tuple[int, int]
    cd_part: str
    thumb_marked: bool
    letters: str
    poster_from: str
    poster_big: bool
    trailer_from: str
    # in BaseCrawlerResult
    number: str
    thumb: str
    poster: str
    trailer: str


class PosterContext(CutThumbContext):
    actor_amazon: list[str]
    amazon_orginaltitle_actor: str
    cd_part: str
    fanart_path: str
    image_download: bool
    letters: str
    originaltitle_amazon: str
    poster_big: bool
    poster_path: str
    poster_size: tuple[int, int]
    thumb_marked: bool
    thumb_path: str
    poster_marked: bool
    # in BaseCrawlerResult
    mosaic: str
    number: str
    poster: str


class FanartContext(TypedDict):
    thumb_path: str
    fanart_path: str
    thumb_marked: bool
    fanart_marked: bool
    cd_part: str
    number: str


class AmazonContext(TypedDict):
    poster_from: str
    amazon_orginaltitle_actor: str
    # in BaseCrawlerResult
    number: str
    poster: str


# translate =================================================================
class TransTitleOutlineContext(TypedDict):
    outline_from: str
    cd_part: str  # read-only
    # in BaseCrawlerResult
    title: str
    outline: str
    mosaic: str


class TranslateActorContext(TypedDict):
    all_actor: str
    actor_href: str
    # in BaseCrawlerResult
    mosaic: str
    number: str
    actor: str


class TranslateInfoContext(TypedDict):
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
class WriteNfoInput(BaseCrawlerResult):
    all_actor: str
    cd_part: str  # CD分卷信息
    country: str  # 国家代码
    fanart_path: str
    letters: str
    originaltitle_amazon: str
    outline_from: str  # 剧情简介来源
    poster_path: str
    thumb_path: str
    wanted: str
    website: str
    # for render_name_template
    destroyed: str
    leak: str
    wuma: str
    youma: str
    c_word: str
    definition: str


class ReadNfoResult(WriteNfoInput):
    source: str
    poster_from: str
    thumb_from: str
    extrafanart_from: str
    trailer_from: str
    tag_only: str
    thumb_list: list[tuple[str, str]]
    actor_amazon: list[str]
