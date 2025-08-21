import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator
from pydantic.fields import FieldInfo

from ..llm import LLMClient
from ..manual import ManualConfig
from ..server.config import SAFE_DIRS
from ..signals import signal
from ..utils import executor, get_random_headers
from ..web_async import AsyncWebClient
from .enums import (
    CDChar,
    CleanAction,
    DownloadableFile,
    EmbyAction,
    FieldRule,
    HDPicSource,
    KeepableFile,
    Language,
    MarkType,
    NfoInclude,
    NoEscape,
    NoneField,
    OutlineShow,
    ReadMode,
    SuffixSort,
    Switch,
    TagInclude,
    Translator,
    Website,
    WebsiteSet,
    WholeField,
)
from .ui_schema import Enum, ServerPathDirectory, extract_ui_schema_recursive


# Helper function to convert comma/pipe separated strings to lists
def str_to_list(v: str | list[Any] | None, separator: str = ",") -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(item) for item in v]
    if isinstance(v, str):
        # Filter out empty strings that result from trailing/leading separators
        return [item.strip() for item in v.strip(separator).split(separator) if item.strip()]
    return []


# Helper function to convert lists back to strings
def list_to_str(v: list[Any] | None, separator: str = ",") -> str:
    if not v:
        return ""
    # Ensure all items are strings before joining
    return separator + separator.join(map(str, v)) + separator


class TranslateConfig(BaseModel):
    translate_by: list[Translator] = Field(
        default_factory=lambda: [Translator.YOUDAO, Translator.GOOGLE, Translator.DEEPL, Translator.LLM],
        title="翻译服务",
    )
    deepl_key: str = Field(default="", title="Deepl密钥")
    llm_url: HttpUrl = Field(default=HttpUrl("https://api.llm.com/v1"), title="Llm网址")
    llm_model: str = Field(default="gpt-3.5-turbo", title="Llm模型")
    llm_key: str = Field(default="", title="Llm密钥")
    llm_prompt: str = Field(
        default="Please translate the following text to {lang}. Output only the translation without any explanation.\n{content}",
        title="Llm提示",
    )
    llm_max_req_sec: float = Field(default=1, title="Llm每秒最大请求数")
    llm_max_try: int = Field(default=5, title="Llm最大尝试次数")
    llm_temperature: float = Field(default=0.2, title="Llm温度")

    def model_post_init(self, context) -> None:
        if self.llm_max_req_sec <= 0:
            self.llm_max_req_sec = 1


class SiteConfig(BaseModel):
    use_browser: bool = Field(default=False, title="使用无头浏览器")
    custom_url: HttpUrl | None = Field(default=None, title="自定义网址")


class Config(BaseModel):
    model_config = ConfigDict()
    # region: General Settings
    media_path: str = ServerPathDirectory("./media", title="媒体路径", initial_path=SAFE_DIRS[0].as_posix())
    softlink_path: str = ServerPathDirectory("softlink", title="软链接路径", ref_field="media_path")
    success_output_folder: str = ServerPathDirectory("JAV_output", title="成功输出目录", ref_field="media_path")
    failed_output_folder: str = ServerPathDirectory("failed", title="失败输出目录", ref_field="media_path")
    extrafanart_folder: str = ServerPathDirectory("extrafanart_copy", title="额外剧照目录")
    media_type: list[str] = Field(
        default_factory=lambda: [
            ".mp4",
            ".avi",
            ".rmvb",
            ".wmv",
            ".mov",
            ".mkv",
            ".flv",
            ".ts",
            ".webm",
            ".iso",
            ".mpg",
        ],
        title="媒体类型",
    )
    sub_type: list[str] = Field(
        default_factory=lambda: [
            ".smi",
            ".srt",
            ".idx",
            ".sub",
            ".sup",
            ".psb",
            ".ssa",
            ".ass",
            ".usf",
            ".xss",
            ".ssf",
            ".rt",
            ".lrc",
            ".sbv",
            ".vtt",
            ".ttml",
        ],
        title="字幕类型",
    )
    scrape_softlink_path: bool = Field(default=False, title="刮削软链接路径")
    auto_link: bool = Field(default=False, title="自动创建软链接")
    # endregion

    # region: Cleaning Settings
    folders: list[str] = Field(default_factory=lambda: ["JAV_output", "examples"], title="排除的目录")
    string: list[str] = Field(
        default_factory=lambda: [
            "h_720",
            "2048论坛@fun2048.com",
            "1080p",
            "720p",
            "22-sht.me",
            "-HD",
            "bbs2048.org@",
            "hhd800.com@",
            "icao.me@",
            "hhb_000",
            "[456k.me]",
            "[ThZu.Cc]",
        ],
        title="要从文件名中删除的字符串",
    )
    file_size: float = Field(default=100.0, title="要处理的最小文件大小（MB）")
    no_escape: list[NoEscape] = Field(
        default_factory=lambda: [NoEscape.RECORD_SUCCESS_FILE],
        title="不转义的字符串",
    )
    clean_ext: list[str] = Field(
        default_factory=lambda: [".html", ".url"],
        title="清理规则: 扩展名",
    )
    clean_name: list[str] = Field(
        default_factory=lambda: ["uur76.mp4", "uur93.com.mp4"],
        title="清理规则: 文件名(完全匹配)",
    )
    clean_contains: list[str] = Field(
        default_factory=lambda: [
            "直播盒子",
            "最新情报",
            "最新位址",
            "注册免费送",
            "房间火爆",
            "美女荷官",
            "妹妹直播",
            "精彩直播",
        ],
        title="清理规则: 文件名包含",
    )
    clean_size: float = Field(default=0.0, title="清理小于此大小的文件（KB）")
    clean_ignore_ext: list[str] = Field(
        default_factory=list,
        title="清理规则: 排除扩展名",
    )
    clean_ignore_contains: list[str] = Field(
        default_factory=lambda: ["skip", "ignore"],
        title="清理规则: 排除文件名包含",
    )
    clean_enable: list[CleanAction] = Field(
        default_factory=lambda: [
            CleanAction.CLEAN_EXT,
            CleanAction.CLEAN_NAME,
            CleanAction.CLEAN_CONTAINS,
            CleanAction.CLEAN_SIZE,
            CleanAction.CLEAN_IGNORE_EXT,
            CleanAction.CLEAN_IGNORE_CONTAINS,
        ],
        title="启用的清理规则",
    )
    # endregion

    # region: Scraping Settings
    thread_number: int = Field(default=10, title="线程数")
    thread_time: int = Field(default=0, title="线程时间")
    javdb_time: int = Field(default=10, title="Javdb时间")
    main_mode: int = Field(default=1, title="主模式")
    read_mode: list[ReadMode] = Field(default_factory=list, title="读取模式")
    update_mode: str = Field(default="c", title="更新模式")
    update_a_folder: str = Field(default="actor", title="更新A目录")
    update_b_folder: str = Field(default="number actor", title="更新B目录")
    update_c_filetemplate: str = Field(default="number", title="更新C文件模板")
    update_d_folder: str = Field(default="number actor", title="更新D目录")
    update_titletemplate: str = Field(default="number title", title="更新标题模板")
    soft_link: int = Field(default=0, title="软链接")
    success_file_move: bool = Field(default=True, title="成功后移动文件")
    failed_file_move: bool = Field(default=True, title="失败后移动文件")
    success_file_rename: bool = Field(default=True, title="成功后重命名文件")
    del_empty_folder: bool = Field(default=True, title="删除空目录")
    show_poster: bool = Field(default=True, title="显示海报")
    download_files: list[DownloadableFile] = Field(
        default_factory=lambda: [
            DownloadableFile.POSTER,
            DownloadableFile.THUMB,
            DownloadableFile.FANART,
            DownloadableFile.EXTRAFANART,
            DownloadableFile.TRAILER,
            DownloadableFile.NFO,
            DownloadableFile.EXTRAFANART_EXTRAS,
            DownloadableFile.EXTRAFANART_COPY,
            DownloadableFile.THEME_VIDEOS,
            DownloadableFile.IGNORE_PIC_FAIL,
            DownloadableFile.IGNORE_YOUMA,
            DownloadableFile.IGNORE_WUMA,
            DownloadableFile.IGNORE_FC2,
            DownloadableFile.IGNORE_GUOCHAN,
            DownloadableFile.IGNORE_SIZE,
        ],
        title="下载文件类型",
    )
    keep_files: list[KeepableFile] = Field(
        default_factory=lambda: [
            KeepableFile.POSTER,
            KeepableFile.THUMB,
            KeepableFile.FANART,
            KeepableFile.EXTRAFANART,
            KeepableFile.TRAILER,
            KeepableFile.NFO,
            KeepableFile.EXTRAFANART_COPY,
            KeepableFile.THEME_VIDEOS,
        ],
        title="保留文件类型",
    )
    download_hd_pics: list[HDPicSource] = Field(
        default_factory=lambda: [
            HDPicSource.POSTER,
            HDPicSource.THUMB,
            HDPicSource.AMAZON,
            HDPicSource.OFFICIAL,
            HDPicSource.GOOGLE,
            HDPicSource.GOO_ONLY,
        ],
        title="高清图片来源",
    )
    google_used: list[str] = Field(
        default_factory=lambda: ["m.media-amazon.com"],
        title="Google使用",
    )
    google_exclude: list[str] = Field(
        default_factory=lambda: [
            "fake",
            "javfree",
            "idoljp.com",
            "qqimg.top",
            "u9a9",
            "picturedata",
            "abpic",
            "pbs.twimg.com",
            "naiwarp",
        ],
        title="Google搜图排除的网址",
    )
    scrape_like: str = Field(default="info", title="刮削收藏")
    # endregion

    # region: Website Settings
    # todo 简化以下配置
    website_single: Website = Field(default=Website.AIRAV_CC, title="单个网站")  # todo 移除
    website_youma: list[Website] = Field(
        default_factory=lambda: [
            Website.AIRAV_CC,
            Website.IQQTV,
            Website.JAVBUS,
            Website.FREEJAVBT,
            Website.JAV321,
            Website.DMM,
            Website.JAVLIBRARY,
            Website.MMTV,
            Website.HDOUBAN,
            Website.JAVDB,
            Website.AVSEX,
            Website.LULUBAR,
            Website.AIRAV,
            Website.XCITY,
            Website.AVSOX,
        ],
        title="有码网站源",
    )
    website_wuma: list[Website] = Field(
        default_factory=lambda: [
            Website.IQQTV,
            Website.JAVBUS,
            Website.FREEJAVBT,
            Website.JAV321,
            Website.AVSOX,
            Website.MMTV,
            Website.HDOUBAN,
            Website.JAVDB,
            Website.AIRAV,
        ],
        title="无码网站源",
    )
    website_suren: list[Website] = Field(
        default_factory=lambda: [
            Website.MGSTAGE,
            Website.AVSEX,
            Website.JAV321,
            Website.FREEJAVBT,
            Website.MMTV,
            Website.JAVBUS,
            Website.JAVDB,
        ],
        title="素人网站源",
    )
    website_fc2: list[Website] = Field(
        default_factory=lambda: [
            Website.FC2,
            Website.FC2CLUB,
            Website.FC2HUB,
            Website.FREEJAVBT,
            Website.MMTV,
            Website.HDOUBAN,
            Website.JAVDB,
            Website.AVSOX,
            Website.AIRAV,
        ],
        title="FC2网站源",
    )
    website_oumei: list[Website] = Field(
        default_factory=lambda: [Website.THEPORNDB, Website.JAVDB, Website.JAVBUS, Website.HDOUBAN],
        title="欧美网站源",
    )
    website_guochan: list[Website] = Field(
        default_factory=lambda: [Website.MADOUQU, Website.MDTV, Website.HDOUBAN, Website.CNMDB, Website.JAVDAY],
        title="国产网站源",
    )
    whole_fields: list[WholeField] = Field(
        default_factory=lambda: [
            WholeField.OUTLINE,
            WholeField.ACTOR,
            WholeField.THUMB,
            WholeField.POSTER,
            WholeField.EXTRAFANART,
            WholeField.TRAILER,
            WholeField.RELEASE,
            WholeField.RUNTIME,
            WholeField.SCORE,
            WholeField.TAG,
            WholeField.DIRECTOR,
            WholeField.SERIES,
            WholeField.STUDIO,
            WholeField.PUBLISHER,
        ],
        title="完整字段",
    )
    none_fields: list[NoneField] = Field(
        default_factory=lambda: [
            NoneField.OUTLINE,
            NoneField.ACTOR,
            NoneField.THUMB,
            NoneField.POSTER,
            NoneField.EXTRAFANART,
            NoneField.TRAILER,
            NoneField.RELEASE,
            NoneField.RUNTIME,
            NoneField.SCORE,
            NoneField.TAG,
            NoneField.DIRECTOR,
            NoneField.SERIES,
            NoneField.STUDIO,
            NoneField.PUBLISHER,
            NoneField.WANTED,
        ],
        title="空字段",
    )
    website_set: list[WebsiteSet] = Field(
        default_factory=lambda: [WebsiteSet.OFFICIAL],
        title="网站设置",
    )
    title_website: list[Website] = Field(
        default_factory=lambda: [
            Website.THEPORNDB,
            Website.MGSTAGE,
            Website.DMM,
            Website.JAVBUS,
            Website.JAV321,
            Website.JAVLIBRARY,
        ],
        title="标题网站源",
    )
    title_zh_website: list[Website] = Field(
        default_factory=lambda: [Website.AIRAV_CC, Website.IQQTV, Website.AVSEX, Website.LULUBAR],
        title="中文标题网站源",
    )
    title_website_exclude: list[Website] = Field(
        default_factory=list,
        title="排除的标题网站源",
    )
    outline_website: list[Website] = Field(
        default_factory=lambda: [Website.THEPORNDB, Website.DMM, Website.JAV321],
        title="简介网站源",
    )
    outline_zh_website: list[Website] = Field(
        default_factory=lambda: [Website.AIRAV_CC, Website.AVSEX, Website.IQQTV, Website.LULUBAR],
        title="中文简介网站源",
    )
    outline_website_exclude: list[Website] = Field(
        default_factory=lambda: [
            Website.AVSOX,
            Website.FC2CLUB,
            Website.JAVBUS,
            Website.JAVDB,
            Website.JAVLIBRARY,
            Website.FREEJAVBT,
            Website.HDOUBAN,
        ],
        title="排除的简介网站源",
    )
    actor_website: list[Website] = Field(
        default_factory=lambda: [Website.THEPORNDB, Website.JAVBUS, Website.JAVLIBRARY, Website.JAVDB],
        title="演员网站源",
    )
    actor_website_exclude: list[Website] = Field(
        default_factory=list,
        title="排除的演员网站源",
    )
    thumb_website: list[Website] = Field(
        default_factory=lambda: [Website.THEPORNDB, Website.JAVBUS],
        title="缩略图网站源",
    )
    thumb_website_exclude: list[Website] = Field(
        default_factory=lambda: [Website.JAVDB],
        title="排除的缩略图网站源",
    )
    poster_website: list[Website] = Field(
        default_factory=lambda: [Website.THEPORNDB, Website.AVSEX, Website.JAVBUS],
        title="海报网站源",
    )
    poster_website_exclude: list[Website] = Field(
        default_factory=lambda: [
            Website.AIRAV,
            Website.FC2CLUB,
            Website.FC2HUB,
            Website.IQQTV,
            Website.MMTV,
            Website.JAVLIBRARY,
            Website.LULUBAR,
        ],
        title="排除的海报网站源",
    )
    extrafanart_website: list[Website] = Field(
        default_factory=lambda: [Website.JAVBUS, Website.FREEJAVBT],
        title="剧照网站源",
    )
    extrafanart_website_exclude: list[Website] = Field(
        default_factory=lambda: [
            Website.AIRAV,
            Website.AIRAV_CC,
            Website.AVSEX,
            Website.AVSOX,
            Website.IQQTV,
            Website.JAVLIBRARY,
            Website.LULUBAR,
        ],
        title="排除的剧照网站源",
    )
    trailer_website: list[Website] = Field(
        default_factory=lambda: [Website.FREEJAVBT, Website.MGSTAGE, Website.DMM],
        title="预告片网站源",
    )
    trailer_website_exclude: list[Website] = Field(
        default_factory=lambda: [Website.MMTV, Website.LULUBAR],
        title="排除的预告片网站源",
    )
    tag_website: list[Website] = Field(
        default_factory=lambda: [Website.JAVBUS, Website.FREEJAVBT],
        title="标签网站源",
    )
    tag_website_exclude: list[Website] = Field(
        default_factory=list,
        title="排除的标签网站源",
    )
    release_website: list[Website] = Field(
        default_factory=lambda: [Website.JAVBUS, Website.FREEJAVBT, Website.MMTV],
        title="发布日期网站源",
    )
    release_website_exclude: list[Website] = Field(
        default_factory=lambda: [Website.FC2CLUB, Website.FC2HUB],
        title="排除的发布日期网站源",
    )
    runtime_website: list[Website] = Field(
        default_factory=lambda: [Website.JAVBUS, Website.FREEJAVBT],
        title="时长网站源",
    )
    runtime_website_exclude: list[Website] = Field(
        default_factory=lambda: [
            Website.AIRAV,
            Website.AIRAV_CC,
            Website.FC2,
            Website.FC2CLUB,
            Website.FC2HUB,
            Website.LULUBAR,
        ],
        title="排除的时长网站源",
    )
    score_website: list[Website] = Field(
        default_factory=lambda: [Website.JAV321, Website.JAVLIBRARY, Website.JAVDB],
        title="评分网站源",
    )
    score_website_exclude: list[Website] = Field(
        default_factory=lambda: [
            Website.AIRAV,
            Website.AIRAV_CC,
            Website.AVSEX,
            Website.AVSOX,
            Website.MMTV,
            Website.FC2,
            Website.FC2HUB,
            Website.IQQTV,
            Website.JAVBUS,
            Website.XCITY,
            Website.LULUBAR,
        ],
        title="排除的评分网站源",
    )
    director_website: list[Website] = Field(
        default_factory=lambda: [Website.JAVBUS, Website.FREEJAVBT],
        title="导演网站源",
    )
    director_website_exclude: list[Website] = Field(
        default_factory=lambda: [
            Website.AIRAV,
            Website.AIRAV_CC,
            Website.AVSEX,
            Website.AVSOX,
            Website.FC2,
            Website.FC2HUB,
            Website.IQQTV,
            Website.JAV321,
            Website.MGSTAGE,
            Website.LULUBAR,
        ],
        title="排除的导演网站源",
    )
    series_website: list[Website] = Field(
        default_factory=lambda: [Website.JAVBUS, Website.FREEJAVBT],
        title="系列网站源",
    )
    series_website_exclude: list[Website] = Field(
        default_factory=lambda: [
            Website.AIRAV,
            Website.AIRAV_CC,
            Website.AVSEX,
            Website.IQQTV,
            Website.MMTV,
            Website.JAVLIBRARY,
            Website.LULUBAR,
        ],
        title="排除的系列网站源",
    )
    studio_website: list[Website] = Field(
        default_factory=lambda: [Website.JAVBUS, Website.FREEJAVBT],
        title="工作室网站源",
    )
    studio_website_exclude: list[Website] = Field(
        default_factory=lambda: [Website.AVSEX],
        title="排除的工作室网站源",
    )
    publisher_website: list[Website] = Field(
        default_factory=lambda: [Website.JAVBUS],
        title="发行商网站源",
    )
    publisher_website_exclude: list[Website] = Field(
        default_factory=lambda: [Website.AIRAV, Website.AIRAV_CC, Website.AVSEX, Website.IQQTV, Website.LULUBAR],
        title="排除的发行商网站源",
    )
    wanted_website: list[Website] = Field(
        default_factory=lambda: [Website.JAVLIBRARY, Website.JAVDB],
        title="想看网站源",
    )
    title_language: Language = Field(default=Language.ZH_CN, title="标题语言")
    title_sehua: bool = Field(default=True, title="使用色花标题")
    title_yesjav: bool = Field(default=False, title="使用 Yesjav 标题")
    title_translate: bool = Field(default=True, title="翻译标题")
    title_sehua_zh: bool = Field(default=True, title="使用色花中文标题")
    outline_language: Language = Field(default=Language.ZH_CN, title="简介语言")
    outline_translate: bool = Field(default=True, title="翻译简介")
    outline_format: list[OutlineShow] = Field(default_factory=list, title="简介格式")
    actor_language: Language = Field(default=Language.ZH_CN, title="演员语言")
    actor_realname: bool = Field(default=True, title="演员真名")
    actor_translate: bool = Field(default=True, title="翻译演员")
    tag_language: Language = Field(default=Language.ZH_CN, title="标签语言")
    tag_translate: bool = Field(default=True, title="翻译标签")
    director_language: Language = Field(default=Language.ZH_CN, title="导演语言")
    director_translate: bool = Field(default=True, title="翻译导演")
    series_language: Language = Field(default=Language.ZH_CN, title="系列语言")
    series_translate: bool = Field(default=True, title="翻译系列")
    studio_language: Language = Field(default=Language.ZH_CN, title="工作室语言")
    studio_translate: bool = Field(default=True, title="翻译工作室")
    publisher_language: Language = Field(default=Language.ZH_CN, title="发行商语言")
    publisher_translate: bool = Field(default=True, title="翻译发行商")

    site_configs: dict[Website, SiteConfig] = Field(default_factory=dict, title="网站配置")

    translate_config: TranslateConfig = Field(default_factory=TranslateConfig, title="翻译配置")

    # region: Naming and Formatting
    nfo_include_new: list[NfoInclude] = Field(
        default_factory=lambda: [
            NfoInclude.SORTTITLE,
            NfoInclude.ORIGINALTITLE,
            NfoInclude.TITLE_CD,
            NfoInclude.OUTLINE,
            NfoInclude.PLOT_,
            NfoInclude.ORIGINALPLOT,
            NfoInclude.OUTLINE_NO_CDATA,
            NfoInclude.RELEASE_,
            NfoInclude.RELEASEDATE,
            NfoInclude.PREMIERED,
            NfoInclude.COUNTRY,
            NfoInclude.MPAA,
            NfoInclude.CUSTOMRATING,
            NfoInclude.YEAR,
            NfoInclude.RUNTIME,
            NfoInclude.WANTED,
            NfoInclude.SCORE,
            NfoInclude.CRITICRATING,
            NfoInclude.ACTOR,
            NfoInclude.ACTOR_ALL,
            NfoInclude.DIRECTOR,
            NfoInclude.SERIES,
            NfoInclude.TAG,
            NfoInclude.GENRE,
            NfoInclude.ACTOR_SET,
            NfoInclude.SERIES_SET,
            NfoInclude.STUDIO,
            NfoInclude.MAKER,
            NfoInclude.PUBLISHER,
            NfoInclude.LABEL,
            NfoInclude.POSTER,
            NfoInclude.COVER,
            NfoInclude.TRAILER,
            NfoInclude.WEBSITE,
        ],
        title="NFO包含内容",
    )
    nfo_tagline: str = Field(default="发行日期 release", title="NFO标语")
    nfo_tag_include: list[TagInclude] = Field(
        default_factory=lambda: [
            TagInclude.ACTOR,
            TagInclude.LETTERS,
            TagInclude.SERIES,
            TagInclude.STUDIO,
            TagInclude.PUBLISHER,
            TagInclude.CNWORD,
            TagInclude.MOSAIC,
            TagInclude.DEFINITION,
        ],
        title="包含标签",
    )
    nfo_tag_series: str = Field(default="系列: series", title="NFO系列标签")
    nfo_tag_studio: str = Field(default="片商: studio", title="NFO工作室标签")
    nfo_tag_publisher: str = Field(default="发行: publisher", title="NFO发行商标签")
    nfo_tag_actor: str = Field(default="actor", title="NFO演员标签")
    nfo_tag_actor_contains: list[str] = Field(default_factory=list, title="NFO 演员名白名单")
    folder_name: str = Field(default="actor/number actor", title="目录名称")
    naming_file: str = Field(default="number", title="文件命名")
    naming_media: str = Field(default="number title", title="媒体命名")
    prevent_char: str = Field(default="", title="禁止字符")
    fields_rule: list[FieldRule] = Field(
        default_factory=lambda: [FieldRule.DEL_ACTOR, FieldRule.DEL_CHAR, FieldRule.FC2_SELLER, FieldRule.DEL_NUM],
        title="字段规则",
    )
    suffix_sort: list[SuffixSort] = Field(
        default_factory=lambda: [SuffixSort.MOWORD, SuffixSort.CNWORD, SuffixSort.DEFINITION],
        title="后缀排序",
    )
    actor_no_name: str = Field(default="未知演员", title="未知演员名称")
    release_rule: str = Field(default="YYYY-MM-DD", title="发布规则")
    folder_name_max: int = Field(default=60, title="目录名称最大长度")
    file_name_max: int = Field(default=60, title="文件名称最大长度")
    actor_name_max: int = Field(default=3, title="演员名称最大数量")
    actor_name_more: str = Field(default="等演员", title="更多演员名称")
    umr_style: str = Field(default="-破解", title="UMR样式")
    leak_style: str = Field(default="-流出", title="泄露样式")
    wuma_style: str = Field(default="", title="无码样式")
    youma_style: str = Field(default="", title="有码样式")
    cd_name: int = Field(default=0, title="CD名称")
    cd_char: list[CDChar] = Field(
        default_factory=lambda: [
            CDChar.LETTER,
            CDChar.ENDC,
            CDChar.DIGITAL,
            CDChar.MIDDLE_NUMBER,
            CDChar.UNDERLINE,
            CDChar.SPACE,
            CDChar.POINT,
        ],
        title="分集规则",
    )
    pic_simple_name: bool = Field(default=False, title="图片简化命名")
    trailer_simple_name: bool = Field(default=True, title="预告片简化命名")
    hd_name: str = Field(default="height", title="高清名称")
    hd_get: str = Field(default="video", title="获取高清")
    cnword_char: list[str] = Field(default_factory=lambda: ["-C.", "-C-", "ch.", "字幕"], title="中文字符")
    cnword_style: str = Field(default="-C", title="中文样式")
    folder_cnword: bool = Field(default=True, title="目录中文")
    file_cnword: bool = Field(default=True, title="文件中文")
    subtitle_folder: str = Field(default="", title="字幕目录")
    subtitle_add: bool = Field(default=False, title="添加字幕")
    subtitle_add_chs: bool = Field(default=True, title="添加中文字幕")
    subtitle_add_rescrape: bool = Field(default=True, title="重新刮削时添加字幕")
    # endregion

    # region: Server Settings
    server_type: str = Field(default="emby", title="服务器类型")
    emby_url: HttpUrl = Field(default=HttpUrl("http://127.0.0.1:8096"), title="Emby网址")
    api_key: str = Field(default="", title="API密钥")
    user_id: str = Field(default="", title="用户ID")
    emby_on: list[EmbyAction] = Field(
        default_factory=lambda: [
            EmbyAction.ACTOR_INFO_ZH_CN,
            EmbyAction.ACTOR_INFO_MISS,
            EmbyAction.ACTOR_PHOTO_NET,
            EmbyAction.ACTOR_PHOTO_MISS,
            EmbyAction.ACTOR_INFO_TRANSLATE,
            EmbyAction.ACTOR_INFO_PHOTO,
            EmbyAction.GRAPHIS_BACKDROP,
            EmbyAction.GRAPHIS_FACE,
            EmbyAction.GRAPHIS_NEW,
            EmbyAction.ACTOR_PHOTO_AUTO,
            EmbyAction.ACTOR_REPLACE,
        ],
        title="Emby功能开关",
    )
    use_database: bool = Field(default=False, title="使用数据库")
    info_database_path: str = Field(default="", title="信息数据库路径")
    gfriends_github: HttpUrl = Field(default=HttpUrl("https://github.com/gfriends/gfriends"), title="Gfriends Github")
    actor_photo_folder: str = Field(default="", title="演员照片目录")
    actor_photo_kodi_auto: bool = Field(default=False, title="演员照片Kodi自动")
    # endregion

    # region: Watermark Settings
    poster_mark: int = Field(default=1, title="海报水印")
    thumb_mark: int = Field(default=1, title="缩略图水印")
    fanart_mark: int = Field(default=0, title="Fanart水印")
    mark_size: int = Field(default=5, title="水印大小")
    mark_type: list[MarkType] = Field(
        default_factory=lambda: [
            MarkType.SUB,
            MarkType.YOUMA,
            MarkType.UMR,
            MarkType.LEAK,
            MarkType.UNCENSORED,
            MarkType.HD,
        ],
        title="水印类型",
    )
    mark_fixed: str = Field(default="not_fixed", title="固定水印")
    mark_pos: str = Field(default="top_left", title="水印位置")
    mark_pos_corner: str = Field(default="top_left", title="边角水印位置")
    mark_pos_sub: str = Field(default="top_left", title="字幕水印位置")
    mark_pos_mosaic: str = Field(default="top_right", title="马赛克水印位置")
    mark_pos_hd: str = Field(default="bottom_right", title="高清水印位置")
    # endregion

    # region: Network Settings
    use_proxy: bool = Field(default=False, title="代理类型")
    proxy: str = Field(default="127.0.0.1:7890", title="代理地址")
    timeout: int = Field(default=10, title="超时")
    retry: int = Field(default=3, title="重试")
    theporndb_api_token: str = Field(default="", title="Theporndb API令牌")
    javdb: str = Field(default="", title="Javdb")
    javbus: str = Field(default="", title="Javbus")
    # endregion

    # region: Log Settings
    show_web_log: bool = Field(default=False, title="显示网页日志")
    show_from_log: bool = Field(default=True, title="显示来源日志")
    show_data_log: bool = Field(default=True, title="显示数据日志")
    save_log: bool = Field(default=True, title="保存日志")
    # endregion

    # region: Misc Settings
    update_check: bool = Field(default=True, title="检查更新")
    local_library: str = Field(default="", title="本地库")
    actors_name: str = Field(default="", title="演员名称")
    netdisk_path: str = Field(default="", title="网盘路径")
    localdisk_path: str = Field(default="", title="本地磁盘路径")
    window_title: str = Field(default="hide", title="窗口标题")
    switch_on: list[Switch] = Field(
        default_factory=lambda: [
            Switch.AUTO_EXIT,
            Switch.REST_SCRAPE,
            Switch.TIMED_SCRAPE,
            Switch.REMAIN_TASK,
            Switch.SHOW_DIALOG_EXIT,
            Switch.SHOW_DIALOG_STOP_SCRAPE,
            Switch.SORT_DEL,
            Switch.IPV4_ONLY,
            Switch.QT_DIALOG,
            Switch.THEPORNDB_NO_HASH,
            Switch.HIDE_DOCK,
            Switch.PASSTHROUGH,
            Switch.HIDE_MENU,
            Switch.DARK_MODE,
            Switch.COPY_NETDISK_NFO,
            Switch.SHOW_LOGS,
            Switch.HIDE_NONE,
        ],
        title="功能开关",
    )
    timed_interval: timedelta = Field(default=timedelta(minutes=30), title="定时器间隔")
    rest_count: int = Field(default=20, title="休息计数")
    rest_time: timedelta = Field(default=timedelta(minutes=1, seconds=2), title="休息时间")
    statement: int = Field(default=3, title="声明")
    # endregion

    def get_site_config(self, site: Website) -> SiteConfig:
        return self.site_configs.get(site, SiteConfig())

    def get_site_url(self, site: Website, default: str = "") -> str:
        return str(self.get_site_config(site).custom_url or default)

    @model_validator(mode="before")
    def _update(cls, d: dict[str, Any]) -> dict[str, Any]:
        """
        处理字段变更.
        """
        if "proxy_type" in d:
            d["use_proxy"] = d["proxy_type"] != "no"
        if isinstance(r := d.get("nfo_tag_actor_contains"), str):
            d["nfo_tag_actor_contains"] = str_to_list(r, "|")
        if isinstance(r := d.get("use_database"), int):
            d["use_database"] = bool(r)
        return d

    @field_validator("timed_interval", "rest_time", mode="before")
    def convert_time_str_to_timedelta(cls, v):
        if isinstance(v, timedelta):
            return v
        if isinstance(v, str) and re.match(r"^\d{2}:\d{2}:\d{2}$", v):
            h, m, s = map(int, v.split(":"))
            return timedelta(hours=h, minutes=m, seconds=s)
        return v

    def to_legacy(self) -> dict[str, Any]:
        """
        将 Pydantic 模型转换为可用于构造 ConfigV1 的 dict.

        Returns:
            d: 与 ConfigV1 兼容的 dict.
        """
        d = self.model_dump(mode="python")

        # 处理 site_configs
        site_configs = d.pop("site_configs", {})
        for site, config in site_configs.items():
            d[f"{site}_website"] = config["custom_url"]

        def handle_fields(data: dict) -> dict[str, Any]:
            res = {}
            for key, value in data.items():
                # | 分隔的字符串列表. 如果在 Config 中重命名了这些字段需要修改此处
                if key in (
                    "media_type",
                    "sub_type",
                    "clean_ext",
                    "clean_name",
                    "clean_contains",
                    "clean_ignore_ext",
                    "clean_ignore_contains",
                    "nfo_tag_actor_contains",
                ):
                    res[key] = list_to_str(value, "|")
                # 逗号分隔的字符串列表
                elif isinstance(value, list):
                    str_list = [item.value if isinstance(item, Enum) else str(item) for item in value]
                    res[key] = list_to_str(str_list, ",")
                # Convert timedelta to HH:MM:SS string
                elif isinstance(value, timedelta):
                    total_seconds = int(value.total_seconds())
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    res[key] = f"{hours:02}:{minutes:02}:{seconds:02}"
                # Convert Enum to its value
                elif isinstance(value, Enum):
                    res[key] = value.value
                elif isinstance(value, dict):  # 展开嵌套模型
                    res.update(handle_fields(value))
                else:
                    if not isinstance(value, str | int | bool | float):
                        res[key] = str(value)
                    else:
                        res[key] = value
            return res

        schema_dict = handle_fields(d)
        # breakpoint()

        # 应用兼容规则
        for rule in COMPAT_RULES:
            if isinstance(rule, Rename):
                if rule.new_name in schema_dict:
                    schema_dict[rule.old_name] = (
                        rule.to_old(schema_dict[rule.new_name]) if rule.to_old else schema_dict[rule.new_name]
                    )
                    schema_dict.pop(rule.new_name, None)
            elif isinstance(rule, Remove):
                schema_dict.pop(rule.name, None)
            elif isinstance(rule, Add):
                schema_dict.pop(rule.name, None)

        return schema_dict

    @classmethod
    def from_legacy(cls, data: dict[str, Any]) -> "Config":
        """
        从 ConfigV1 创建 Config 实例.
        """
        # 应用兼容规则
        for rule in COMPAT_RULES:
            if isinstance(rule, Rename):
                if rule.old_name in data:
                    data[rule.new_name] = rule.to_new(data[rule.old_name]) if rule.to_new else data[rule.old_name]
                    data.pop(rule.old_name, None)
            elif isinstance(rule, Remove):
                data.pop(rule.name, None)
            elif isinstance(rule, Add):  # 新增字段会自动使用默认值初始化
                pass

        # 处理 site_configs
        site_configs = {}
        for key, value in data.items():
            # custom url
            if key.endswith("_website") and key[:-8] in Website:
                site_name = key.replace("_website", "")
                site_configs[Website(site_name)] = SiteConfig(custom_url=value)
        data["site_configs"] = site_configs

        # 格式转换
        def handle_dict(model_fields: dict[str, FieldInfo], data: dict[str, Any]) -> dict[str, Any]:
            for name, info in model_fields.items():
                assert info.annotation is not None, f"Field {name} has no annotation"
                # 处理嵌套
                if issubclass(info.annotation, BaseModel):
                    sub_dict = handle_dict(info.annotation.model_fields, data)
                    data[name] = sub_dict
                    continue
                if name not in data:
                    continue
                if "list" in str(info.annotation):
                    if name in (
                        "media_type",
                        "sub_type",
                        "clean_ext",
                        "clean_name",
                        "clean_contains",
                        "clean_ignore_ext",
                        "clean_ignore_contains",
                        "nfo_tag_actor_contains",
                    ):
                        data[name] = str_to_list(data[name], "|")
                    else:
                        data[name] = str_to_list(data[name], ",")
                if info.annotation is type(timedelta) and re.match(r"^\d{2}:\d{2}:\d{2}$", data[name]):
                    h, m, s = map(int, data[name].split(":"))
                    data[name] = timedelta(hours=h, minutes=m, seconds=s)
            return data

        data = handle_dict(cls.model_fields, data)
        return cls.model_validate(data)

    @classmethod
    @lru_cache
    def ui_schema(cls) -> dict[str, Any]:
        return extract_ui_schema_recursive(cls.json_schema())

    @classmethod
    @lru_cache
    def json_schema(cls) -> dict[str, Any]:
        return cls.model_json_schema()


class Computed:
    def __init__(self, config: Config):
        self.can_clean = CleanAction.I_KNOW in config.clean_enable and CleanAction.I_AGREE in config.clean_enable

        if any(schema in config.proxy for schema in ["http://", "https://", "socks5://", "socks5h://"]):
            self.proxy = config.proxy.strip()
        else:
            self.proxy = "http://" + config.proxy.strip()

        self.random_headers = get_random_headers()

        proxy = config.proxy if config.use_proxy else None
        self.llm_client = LLMClient(
            api_key=config.translate_config.llm_key,
            base_url=config.translate_config.llm_url.unicode_string(),
            proxy=proxy,
            timeout=httpx.Timeout(config.timeout, read=None),  # 只设置连接超时, 不限制 llm 生成时间
            rate=(max(config.translate_config.llm_max_req_sec, 1), max(1, 1 / config.translate_config.llm_max_req_sec)),
        )

        self.async_client = AsyncWebClient(
            loop=executor._loop,
            proxy=proxy,
            retry=config.retry,
            timeout=config.timeout,
            log_fn=signal.add_log,
        )

        official_websites_dic = {}
        for key, value in ManualConfig.OFFICIAL.items():
            temp_list = value.upper().split("|")
            for each in temp_list:
                official_websites_dic[each] = key
        self.official_websites = official_websites_dic

        self.escape_string_list = list(dict.fromkeys(k for k in config.string + ManualConfig.REPL_LIST if k.strip()))

        # 生成 Google 关键词列表 迁移自 ConfigV1.init
        temp_list = re.split(r"[,，]", ",".join(config.google_used))
        self.google_keyused = [each for each in temp_list if each.strip()]  # 去空
        temp_list = re.split(r"[,，]", ",".join(config.google_exclude))
        self.google_keyword = [each for each in temp_list if each.strip()]  # 去空


@dataclass
class CompatRule:
    # 添加必要注释
    notes: list = field(kw_only=True, default_factory=list)


@dataclass
class Rename[TRaw = str, TNew = TRaw](CompatRule):
    old_name: str
    new_name: str
    to_new: Callable[[TRaw], TNew] | None = None
    to_old: Callable[[TNew], TRaw] | None = None


@dataclass
class Remove(CompatRule):
    name: str


@dataclass
class Add(CompatRule):
    name: str


# 描述 Config 相比于 ConfigV1 的变更并添加相应的兼容规则
COMPAT_RULES: list[CompatRule] = [
    Remove("version"),
    Remove("unknown_fields"),
    Rename[str, bool](
        "type",
        "use_proxy",
        to_new=lambda x: x != "no",
        to_old=lambda x: "no" if not x else "yes",
        notes=["ConfigV1.type", Config().use_proxy, "与关键词冲突"],
    ),
    Rename("outline_show", "outline_format", notes=["ConfigV1.outline_show", Config().outline_format, "澄清语义"]),
    Rename("tag_include", "nfo_tag_include", notes=["ConfigV1.tag_include", Config().nfo_tag_include, "澄清语义"]),
    Remove("show_4k", notes=["ConfigV1.show_4k", "功能与命名模板冲突"]),
    Remove("show_moword", notes=["ConfigV1.show_moword", "功能与命名模板冲突"]),
    Add("site_configs", notes=[Config().site_configs]),
]
if TYPE_CHECKING:
    from .v1 import ConfigV1

    # 方便快速查看 ConfigV1 的字段
    _ = [
        ConfigV1.type,
        ConfigV1.outline_show,
        ConfigV1.tag_include,
        ConfigV1.show_4k,
        ConfigV1.show_moword,
    ]
