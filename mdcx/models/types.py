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


# utils ============================================================
class ShowResultInput(TypedDict):
    title: str
    fields_info: str


class TemplateInput(TypedDict):
    """
    用于 render_name_template 根据用户模版生成文件名
    """

    destroyed: str
    leak: str
    wuma: str
    youma: str
    c_word: str
    title: str
    originaltitle: str
    studio: str
    publisher: str
    year: str
    outline: str
    runtime: str
    director: str
    actor: str
    release: str
    number: str
    series: str
    mosaic: str
    definition: str
    letters: str
    wanted: str
    all_actor: str
    score: str


class GetVideoSizeContext(TypedDict):
    definition: str
    _4K: str
    tag: str


class ShowData(TypedDict):
    """
    ref: ManualConfig.SHOW_KEY
    """

    number: str
    letters: str
    has_sub: bool
    cd_part: str
    mosaic: str
    title: str
    originaltitle: str
    actor: str
    all_actor: str
    outline: str
    originalplot: str
    tag: str
    release: str
    year: str
    runtime: str
    score: str
    wanted: str
    series: str
    director: str
    studio: str
    publisher: str
    trailer: str
    website: str
    javdbid: str


# file =================================================================
class GetFolderPathInput(TemplateInput):
    folder_name: str


class GetOutPutNameInput(TemplateInput):
    folder_name: str
    cd_part: str


class GenerateFileNameInput(TemplateInput):
    folder_name: str
    cd_part: str


class DealOldFilesInput(TypedDict):
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


class FileInfoResult(TypedDict):
    """
    Output of get_file_info
    """

    number: str
    letters: str
    cd_part: str
    has_sub: bool
    c_word: str
    destroyed: str
    leak: str
    wuma: str
    youma: str
    mosaic: str
    _4K: str
    file_path: str
    short_number: str
    appoint_number: str
    appoint_url: str
    website_name: str


@dataclass
class FileInfo:
    """
    新版本的文件信息数据类，整合了 get_file_info 函数的所有返回值
    """

    # FileInfoResult 的所有字段
    number: str
    letters: str
    cd_part: str
    has_sub: bool
    c_word: str
    destroyed: str
    leak: str
    wuma: str
    youma: str
    mosaic: str
    file_path: str
    short_number: str
    appoint_number: str
    appoint_url: str
    website_name: str

    # 原函数其他返回值
    folder_path: str
    file_name: str
    file_ex: str
    sub_list: list[str]
    file_show_name: str
    file_show_path: str


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
    number: str
    poster_path: str
    thumb_path: str
    fanart_path: str
    thumb_list: list[tuple[str, str]]
    thumb_from: str
    thumb_size: tuple[int, int]
    cd_part: str
    thumb_marked: bool
    letters: str
    thumb: str
    poster: str
    poster_from: str
    poster_big: bool
    trailer: str
    trailer_from: str


class PosterContext(CutThumbContext):
    number: str
    letters: str
    mosaic: str
    poster: str
    poster_from: str
    originaltitle_amazon: str
    poster_big: bool
    image_download: bool
    poster_path: str
    thumb_path: str
    fanart_path: str
    amazon_orginaltitle_actor: str
    actor_amazon: list[str]
    poster_size: tuple[int, int]
    cd_part: str
    thumb_marked: bool
    poster_marked: bool


class FanartContext(TypedDict):
    thumb_path: str
    fanart_path: str
    thumb_marked: bool
    fanart_marked: bool
    cd_part: str
    number: str


class AmazonContext(TypedDict):
    number: str
    poster: str
    poster_from: str
    amazon_orginaltitle_actor: str


# translate =================================================================
class TransTitleOutlineContext(TypedDict):
    title: str
    outline: str
    outline_from: str
    mosaic: str
    # read-only
    cd_part: str


class TranslateActorContext(TypedDict):
    mosaic: str
    number: str
    actor: str
    all_actor: str
    actor_href: str


class TranslateInfoContext(TypedDict):
    tag: str
    actor: str
    letters: str
    number: str
    has_sub: bool
    mosaic: str
    series: str
    studio: str
    publisher: str
    director: str


# nfo =================================================================
class WriteNfoInput(TypedDict):
    title: str
    originaltitle: str
    originaltitle_amazon: str
    number: str
    letters: str
    actor: str
    all_actor: str
    outline: str
    originalplot: str
    tag: str
    release: str
    year: str
    runtime: str
    score: str
    director: str
    series: str
    studio: str
    publisher: str
    website: str
    thumb: str
    poster: str
    trailer: str
    wanted: str
    poster_path: str
    thumb_path: str
    fanart_path: str
    cd_part: str  # CD分卷信息
    country: str  # 国家代码
    outline_from: str  # 剧情简介来源
    mosaic: str
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


# crawler =================================================================
class CallCrawlerInput(TypedDict):
    """调用单个 crawler 所需输入"""

    appoint_number: str
    appoint_url: str
    file_path: str
    number: str
    mosaic: str
    short_number: str


class CrawlTask(CallCrawlerInput):
    """刮削一个文件所需的信息"""

    has_sub: bool
    c_word: str
    leak: str
    wuma: str
    youma: str
    cd_part: str
    destroyed: str
    website_name: str  # 用于重新刮削时指定网站


class CrawlerResult(TypedDict):
    """
    单一网站爬虫返回的结果 (注释由 AI 生成, 仅供参考)
    """

    # 基本信息
    number: str  # 番号
    title: str  # 标题
    originaltitle: str  # 原始标题（日文）

    # 演员信息
    actor: str  # 演员名称，逗号分隔
    actor_photo: dict  # 演员照片信息

    # 内容描述
    outline: str  # 简介
    originalplot: str  # 原始简介（日文）

    # 元数据信息
    tag: str  # 标签，逗号分隔
    release: str  # 发行日期
    year: str  # 发行年份
    runtime: str  # 片长（分钟）
    score: str  # 评分
    series: str  # 系列
    director: str  # 导演
    studio: str  # 制作商
    publisher: str  # 发行商
    source: str  # 数据来源（爬虫名称）

    # 图片与视频
    thumb: str  # 缩略图URL
    poster: str  # 海报URL
    extrafanart: list[str]  # 额外剧照URL列表
    trailer: str  # 预告片URL

    # 控制参数
    image_download: bool  # 是否需要下载图片
    image_cut: str  # 图片裁剪方式
    mosaic: str  # 马赛克类型（有码/无码）

    # 其他信息
    website: str  # 网站地址
    wanted: str  # 期望信息


class CrawlersResult(TypedDict):
    """
    整合所有网站的爬虫结果 (注释由 AI 生成, 仅供参考)
    """

    # 基本信息
    number: str  # 番号
    short_number: str  # 素人番号的短形式（不带前缀数字）
    title: str  # 标题
    originaltitle: str  # 原始标题（日文）
    originaltitle_amazon: str  # 用于 Amazon 搜索的原始标题
    outline: str  # 简介
    originalplot: str  # 原始简介（日文）
    # 演员信息
    actor: str  # 演员名称，逗号分隔
    all_actor: str  # 所有来源的演员名称
    all_actor_photo: dict  # 演员照片信息
    actor_amazon: list[str]  # 用于 Amazon 搜索的演员名称
    amazon_orginaltitle_actor: str  # 用于 Amazon 搜索的原始标题中的演员
    # 元数据信息
    tag: str  # 标签，逗号分隔
    release: str  # 发行日期
    year: str  # 发行年份
    runtime: str  # 片长（分钟）
    score: str  # 评分
    series: str  # 系列
    director: str  # 导演
    studio: str  # 制作商
    publisher: str  # 发行商
    # 图片与视频
    thumb: str  # 缩略图URL
    thumb_list: list  # 所有来源的缩略图URL列表
    poster: str  # 海报URL
    extrafanart: list[str]  # 额外剧照URL列表
    trailer: str  # 预告片URL
    image_download: bool  # 是否需要下载图片
    # 马赛克类型
    mosaic: str
    letters: str  # 番号字母部分
    # 标志信息
    has_sub: bool  # 是否有字幕
    c_word: str  # 中文字幕标识
    leak: str  # 是否是无码流出
    wuma: str  # 是否是无码
    youma: str  # 是否是有码
    cd_part: str  # CD分集信息
    destroyed: str  # 是否是无码破解
    version: int  # 版本信息
    # 文件路径与指定信息
    file_path: str  # 文件路径
    appoint_number: str  # 指定番号
    appoint_url: str  # 指定URL
    # 其他信息
    javdbid: str  # JavDB ID
    fields_info: str  # 字段来源信息
    naming_media: str  # 媒体命名规则
    naming_file: str  # 文件命名规则
    folder_name: str  # 文件夹命名规则
    # 字段来源信息
    poster_from: str
    thumb_from: str
    extrafanart_from: str
    trailer_from: str
    outline_from: str
    website_name: str  # 使用的网站名称
