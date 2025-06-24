import os
import os.path
import platform
import re
from configparser import ConfigParser, RawConfigParser
from dataclasses import dataclass, fields
from io import StringIO

from ..base.utils import get_mac_default_config_folder, get_random_headers, get_user_agent, singleton
from .manual import ManualConfig


@singleton
class ConfigManager(ManualConfig):
    mark_file_name = "MDCx.config"

    def __init__(self):
        self.file = ""
        self.folder = ""
        self._path = ""
        self.config = ConfigSchema()  # 此初始值作为默认配置
        self.youdaokey = "Ygy_4c=r#e#4EX^NUGUc5"

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str):
        self.folder, self.file = os.path.split(path)
        self._path = path

    @path.getter
    def path(self) -> str:
        return self._path

    def get_mark_file_path(self) -> str:
        """
        获取`记录了配置文件路径`的文件的路径。
        对于macOS，该文件位于`~/.mdcx/MDCx.config`。
        其他平台，该文件跟应用程序在同一目录下。
        """

        if platform.system() == "Darwin":
            return os.path.join(get_mac_default_config_folder(), self.mark_file_name)
        else:
            return self.mark_file_name

    def read_config(self):
        self._get_config_path()
        return self._read_file(self.path)

    def save_config(self):
        with open(self.get_mark_file_path(), "w", encoding="UTF-8") as f:
            f.write(self.path)
        with open(self.path, "w", encoding="UTF-8") as f:
            f.write(self.format_ini(self.config))

    def _read_file(self, path):
        reader = RawConfigParser()
        reader.read(path, encoding="UTF-8")
        field_types = {f.name: f.type for f in fields(ConfigSchema)}
        errors = []
        for section in reader.sections():
            for key, value in reader.items(section):
                if key not in field_types:
                    # 特例处理: 支持自定义网站配置
                    if key.endswith("_website") and key[:-8] in ManualConfig.SUPPORTED_WEBSITES and value:
                        setattr(self.config, key, value)
                        continue
                    errors.append(f"未知配置: {key} (位于 {section})")
                    continue
                expected_type = field_types[key]
                if expected_type is int:
                    try:
                        setattr(self.config, key, int(value))
                    except ValueError:
                        errors.append(f"类型无效: {key} 应为整数, 得到 {value} (位于 {section})")
                elif expected_type is float:
                    try:
                        setattr(self.config, key, float(value))
                    except ValueError:
                        errors.append(f"类型无效: {key} 应为浮点数, 得到 {value} (位于 {section})")
                elif expected_type is bool:
                    setattr(self.config, key, self.ini_value_to_bool(value))
                elif expected_type is str:
                    setattr(self.config, key, value)
                else:
                    errors.append(f"内部错误: {key} 具有未知类型 {expected_type} (位于 {section}), 请联系开发者")
        return "\n\t".join(errors)

    @staticmethod
    def ini_value_to_bool(value: str) -> bool:
        """将 ini 配置文件中的字符串值转换为布尔值"""
        if value.lower() in ["true", "1", "yes", "on"]:
            return True
        elif value.lower() in ["false", "0", "no", "off"]:
            return False
        else:
            return bool(value)

    @staticmethod
    def format_ini(cfg: "ConfigSchema"):
        buffer = StringIO()
        parser = ConfigParser()
        parser.add_section("mdcx")
        for field in fields(cfg):
            value = getattr(cfg, field.name)
            if isinstance(value, bool):
                value = "true" if value else "false"
            else:
                value = str(value)
            parser.set("mdcx", field.name, value)
        for website in ManualConfig.SUPPORTED_WEBSITES:
            if url := getattr(cfg, f"{website}_website", ""):
                parser.set("mdcx", f"{website}_website", url)
        parser.write(buffer)
        return buffer.getvalue()

    def init_config(self):
        """生成默认配置文件"""
        with open(self.path, "w", encoding="UTF-8") as f:
            f.write(self.format_ini(ConfigSchema()))

    def _get_config_path(self):
        mdcx_config = self.get_mark_file_path()  # 此文件用于记录当前配置文件的绝对路径, 从而实现多配置切换
        # 此文件必须存在, 且与 main.py 或打包的可执行文件在同一目录下.
        if not os.path.exists(mdcx_config):  # 不存在时, 创建
            if platform.system() == "Darwin":  # macOS下默认配置文件: ~/.mdcx/config.ini
                self.path = os.path.join(get_mac_default_config_folder(), "config.ini")
            else:
                self.path = os.path.realpath("config.ini")  # 默认配置文件: 同目录下的 config.ini
            # 设置默认配置文件路径, 若存在则可读取, 否则生成默认配置文件
            with open(mdcx_config, "w", encoding="UTF-8") as f:
                f.write(self.path)
            if not os.path.exists(self.path):
                self.init_config()
        else:
            with open(mdcx_config, encoding="UTF-8") as f:
                self.path = f.read()


@dataclass
class ConfigSchema:
    version: int = 120240924

    # media
    media_path: str = r""
    softlink_path: str = r"softlink"
    success_output_folder: str = r"JAV_output"
    failed_output_folder: str = r"failed"
    extrafanart_folder: str = r"extrafanart_copy"
    media_type: str = r".mp4|.avi|.rmvb|.wmv|.mov|.mkv|.flv|.ts|.webm|.iso|.mpg"
    sub_type: str = r".smi|.srt|.idx|.sub|.sup|.psb|.ssa|.ass|.usf|.xss|.ssf|.rt|.lrc|.sbv|.vtt|.ttml"
    scrape_softlink_path: bool = False
    auto_link: bool = False

    # escape
    folders: str = r"JAV_output,examples"
    string: str = r"h_720,2048论坛@fun2048.com,1080p,720p,22-sht.me,-HD,bbs2048.org@,hhd800.com@,icao.me@,hhb_000,[456k.me],[ThZu.Cc]"
    file_size: float = 100.0
    no_escape: str = r"record_success_file,"

    # clean
    clean_ext: str = r".html|.url"
    clean_name: str = r"uur76.mp4|uur9 3.com.mp4"
    clean_contains: str = r"直 播 盒 子|最 新 情 報|最 新 位 址|注册免费送|房间火爆|美女荷官|妹妹直播|精彩直播"
    clean_size: float = 0.0
    clean_ignore_ext: str = r""
    clean_ignore_contains: str = r"skip|ignore"
    clean_enable: str = r"clean_ext,clean_name,clean_contains,clean_size,clean_ignore_ext,clean_ignore_contains,"

    # common
    thread_number: int = 10
    thread_time: int = 0
    javdb_time: int = 10
    main_mode: int = 1
    read_mode: str = r""
    update_mode: str = r"c"
    update_a_folder: str = r"actor"
    update_b_folder: str = r"number actor"
    update_d_folder: str = r"number actor"
    soft_link: int = 0
    success_file_move: bool = True
    failed_file_move: bool = True
    success_file_rename: bool = True
    del_empty_folder: bool = True
    show_poster: bool = True

    # file_download
    download_files: str = r",poster,thumb,fanart,nfo,ignore_wuma,ignore_fc2,ignore_guochan,"
    keep_files: str = r",extrafanart,trailer,theme_videos,"
    download_hd_pics: str = r"poster,thumb,amazon,official,google,"
    google_used: str = r"m.media-amazon.com,"
    google_exclude: str = r"fake,javfree,idoljp.com,qqimg.top,u9a9,picturedata,abpic,pbs.twimg.com,naiwarp"

    # website
    scrape_like: str = r"info"
    website_single: str = r"airav_cc"
    website_youma: str = (
        r"airav_cc,iqqtv,javbus,freejavbt,jav321,dmm,javlibrary,7mmtv,hdouban,javdb,avsex,lulubar,airav,xcity,avsox"
    )

    website_wuma: str = r"iqqtv,javbus,freejavbt,jav321,avsox,7mmtv,hdouban,javdb,airav"
    website_suren: str = r"mgstage,avsex,jav321,freejavbt,7mmtv,javbus,javdb"
    website_fc2: str = r"fc2,fc2club,fc2hub,freejavbt,7mmtv,hdouban,javdb,avsox,airav"
    website_oumei: str = r"theporndb,javdb,javbus,hdouban"
    website_guochan: str = r"madouqu,mdtv,hdouban,cnmdb,javday"
    whole_fields: str = r"outline,actor,thumb,release,tag,"
    none_fields: str = r"wanted,"
    website_set: str = r"official,"
    title_website: str = r"theporndb,mgstage,dmm,javbus,jav321,javlibrary"
    title_zh_website: str = r"airav_cc,iqqtv,avsex,lulubar"
    title_website_exclude: str = r""
    outline_website: str = r"theporndb,dmm,jav321"
    outline_zh_website: str = r"airav_cc,avsex,iqqtv,lulubar"
    outline_website_exclude: str = r"avsox,fc2club,javbus,javdb,javlibrary,freejavbt,hdouban"
    actor_website: str = r"theporndb,javbus,javlibrary,javdb"
    actor_website_exclude: str = r""
    thumb_website: str = r"theporndb,javbus"
    thumb_website_exclude: str = r"javdb"
    poster_website: str = r"theporndb,avsex,javbus"
    poster_website_exclude: str = r"airav,fc2club,fc2hub,iqqtv,7mmtv,javlibrary,lulubar"
    extrafanart_website: str = r"javbus,freejavbt"
    extrafanart_website_exclude: str = r"airav,airav_cc,avsex,avsox,iqqtv,javlibrary,lulubar"
    trailer_website: str = r"freejavbt,mgstage,dmm"
    trailer_website_exclude: str = r"7mmtv,lulubar"
    tag_website: str = r"javbus,freejavbt"
    tag_website_exclude: str = r""
    release_website: str = r"javbus,freejavbt,7mmtv"
    release_website_exclude: str = r"fc2club,fc2hub"
    runtime_website: str = r"javbus,freejavbt"
    runtime_website_exclude: str = r"airav,airav_cc,fc2,fc2club,fc2hub,lulubar"
    score_website: str = r"jav321,javlibrary,javdb"
    score_website_exclude: str = r"airav,airav_cc,avsex,avsox,7mmtv,fc2,fc2hub,iqqtv,javbus,xcity,lulubar"
    director_website: str = r"javbus,freejavbt"
    director_website_exclude: str = r"airav,airav_cc,avsex,avsox,fc2,fc2hub,iqqtv,jav321,mgstage,lulubar"
    series_website: str = r"javbus,freejavbt"
    series_website_exclude: str = r"airav,airav_cc,avsex,iqqtv,7mmtv,javlibrary,lulubar"
    studio_website: str = r"javbus,freejavbt"
    studio_website_exclude: str = r"avsex"
    publisher_website: str = r"javbus"
    publisher_website_exclude: str = r"airav,airav_cc,avsex,iqqtv,lulubar"
    wanted_website: str = r"javlibrary,javdb"
    translate_by: str = r"youdao,google,deepl,"
    deepl_key: str = r""
    title_language: str = r"zh_cn"
    title_sehua: bool = True
    title_yesjav: bool = False
    title_translate: bool = True
    title_sehua_zh: bool = True
    outline_language: str = r"zh_cn"
    outline_translate: bool = True
    outline_show: str = r""
    actor_language: str = r"zh_cn"
    actor_realname: bool = True
    actor_translate: bool = True
    tag_language: str = r"zh_cn"
    tag_translate: bool = True
    tag_include: str = r"actor,letters,series,studio,publisher,cnword,mosaic,definition,"
    director_language: str = r"zh_cn"
    director_translate: bool = True
    series_language: str = r"zh_cn"
    series_translate: bool = True
    studio_language: str = r"zh_cn"
    studio_translate: bool = True
    publisher_language: str = r"zh_cn"
    publisher_translate: bool = True
    nfo_include_new: str = r"sorttitle,originaltitle,title_cd,outline,plot_,originalplot,release_,releasedate,premiered,country,mpaa,customrating,year,runtime,wanted,score,criticrating,actor,director,series,tag,genre,series_set,studio,maker,publisher,label,poster,cover,trailer,website,"
    nfo_tagline: str = r"发行日期 release"
    nfo_tag_series: str = r"系列: series"
    nfo_tag_studio: str = r"片商: studio"
    nfo_tag_publisher: str = r"发行: publisher"

    # Name_Rule
    folder_name: str = r"actor/number actor"
    naming_file: str = r"number"
    naming_media: str = r"number title"
    prevent_char: str = r""
    fields_rule: str = r"del_actor,del_char,"
    suffix_sort: str = r"mosaic,cnword,definition"
    actor_no_name: str = r"未知演员"
    release_rule: str = r"YYYY-MM-DD"
    folder_name_max: int = 60
    file_name_max: int = 60
    actor_name_max: int = 3
    actor_name_more: str = r"等演员"
    umr_style: str = r"-破解"
    leak_style: str = r"-流出"
    wuma_style: str = r""
    youma_style: str = r""
    show_moword: str = r"file,"
    show_4k: str = r"folder,file,"
    cd_name: int = 0
    cd_char: str = r"letter,underline,"
    pic_simple_name: bool = False
    trailer_simple_name: bool = True
    hd_name: str = r"height"
    hd_get: str = r"video"

    # subtitle
    cnword_char: str = r"-C.,-C-,ch.,字幕"
    cnword_style: str = r"^-C^"
    folder_cnword: bool = True
    file_cnword: bool = True
    subtitle_folder: str = r""
    subtitle_add: bool = False
    subtitle_add_chs: bool = True
    subtitle_add_rescrape: bool = True

    # emby
    server_type: str = r"emby"
    emby_url: str = r"http://192.168.5.191:8096"
    api_key: str = r"ee9a2f2419704257b1dd60b975f2d64e"
    user_id: str = r""
    emby_on: str = r"actor_info_zh_cn,actor_info_miss,actor_photo_net,actor_photo_miss,"
    use_database: int = 0
    info_database_path: str = r""
    gfriends_github: str = r"https://github.com/gfriends/gfriends"
    actor_photo_folder: str = r""
    actor_photo_kodi_auto: bool = False

    # mark
    poster_mark: int = 1
    thumb_mark: int = 1
    fanart_mark: int = 0
    mark_size: int = 5
    mark_type: str = r"sub,umr,leak,uncensored,hd"
    mark_fixed: str = r"not_fixed"  # fixed, not_fixed, corner
    mark_pos: str = r"top_left"
    mark_pos_corner: str = r"top_left"
    mark_pos_sub: str = r"top_left"
    mark_pos_mosaic: str = r"top_right"
    mark_pos_hd: str = r"bottom_right"

    # proxy
    type: str = r"no"
    proxy: str = r"127.0.0.1:7890"
    timeout: int = 10
    retry: int = 3
    theporndb_api_token: str = r""

    # Cookies
    javdb: str = r""
    javbus: str = r""

    # other
    show_web_log: bool = False
    show_from_log: bool = True
    show_data_log: bool = True
    save_log: bool = True
    update_check: bool = True
    local_library: str = r""
    actors_name: str = r""
    netdisk_path: str = r""
    localdisk_path: str = r""
    window_title: str = r"hide"
    switch_on: str = r"rest_scrape,remain_task,show_dialog_stop_scrape,show_logs,ipv4_only,hide_none,"
    timed_interval: str = r"00:30:00"
    rest_count: int = 20
    rest_time: str = r"00:01:02"
    statement: int = 3

    def _update(self):
        """处理版本变更"""
        if self.version == ManualConfig.LOCAL_VERSION:
            return

    def init(self):
        self._update()
        # 获取proxies
        if self.type == "http":
            self.proxies = {
                "http": "http://" + self.proxy,
                "https": "http://" + self.proxy,
            }
        elif self.type == "socks5":
            self.proxies = {
                "http": "socks5h://" + self.proxy,
                "https": "socks5h://" + self.proxy,
            }
        else:
            self.proxies = None

        self.ipv4_only = "ipv4_only" in self.switch_on
        self.theporndb_no_hash = "theporndb_no_hash" in self.switch_on

        # 获取User-Agent
        self.headers = {
            "User-Agent": get_user_agent(),
        }

        self.random_headers = get_random_headers()

        # 去掉^符号！！！
        self.cnword_style = self.cnword_style.strip("^")

        # 获取 Google 下载关键词列表
        temp_list = re.split(r"[,，]", self.google_used)
        self.google_keyused = [each for each in temp_list if each.strip()]  # 去空
        # 获取 Google 过滤关键词列表
        temp_list = re.split(r"[,，]", self.google_exclude)
        self.google_keyword = [each for each in temp_list if each.strip()]  # 去空

        # 是否记录刮削成功列表
        self.record_success_file = "record_success_file" in self.no_escape

        # 是否清理文件以及清理列表
        can_clean = True if "i_know" in self.clean_enable and "i_agree" in self.clean_enable else False
        can_clean_auto = True if can_clean and "clean_auto" in self.clean_enable else False
        clean_ext_list = (
            re.split(r"[|｜，,]", self.clean_ext)
            if can_clean and self.clean_ext and "clean_ext" in self.clean_enable
            else []
        )
        clean_name_list = (
            re.split(r"[|｜，,]", self.clean_name)
            if can_clean and self.clean_name and "clean_name" in self.clean_enable
            else []
        )
        clean_contains_list = (
            re.split(r"[|｜，,]", self.clean_contains)
            if can_clean and self.clean_contains and "clean_contains" in self.clean_enable
            else []
        )
        clean_size_list = self.clean_size if can_clean and "clean_size" in self.clean_enable else 0.0
        clean_ignore_ext_list = (
            re.split(r"[|｜，,]", self.clean_ignore_ext)
            if can_clean and self.clean_ignore_ext and "clean_ignore_ext" in self.clean_enable
            else []
        )
        clean_ignore_contains_list = (
            re.split(r"[|｜，,]", self.clean_ignore_contains)
            if can_clean and self.clean_ignore_contains and "clean_ignore_contains" in self.clean_enable
            else []
        )
        self.can_clean = can_clean
        self.can_clean_auto = can_clean_auto
        self.clean_ext_list = clean_ext_list
        self.clean_name_list = clean_name_list
        self.clean_contains_list = clean_contains_list
        self.clean_size_list = clean_size_list
        self.clean_ignore_ext_list = clean_ignore_ext_list
        self.clean_ignore_contains_list = clean_ignore_contains_list

        # 获取排除字符列表
        temp_list = re.split("[,，]", self.string) + ManualConfig.REPL_LIST
        self.escape_string_list = []
        [self.escape_string_list.append(i) for i in temp_list if i.strip() and i not in self.escape_string_list]

        # 番号对应官网
        official_websites_dic = {}
        for key, value in ManualConfig.OFFICIAL.items():
            temp_list = value.upper().split("|")
            for each in temp_list:
                official_websites_dic[each] = key
        self.official_websites = official_websites_dic

        # 字段命名规则-后缀字段顺序
        all_str_list = ["mosaic", "cnword", "definition"]
        read_str_list = re.split(r"[,，]", self.suffix_sort)
        new_str_list1 = [i1 for i1 in read_str_list if i1 in all_str_list]  # 去除不在list中的字符
        new_str_list = []
        [new_str_list.append(i1) for i1 in new_str_list1 if i1 not in new_str_list]  # 去重
        [new_str_list.append(i1) for i1 in all_str_list if i1 not in new_str_list]  # 补全
        new_str = ",".join(new_str_list)
        self.suffix_sort = new_str


manager = ConfigManager()
config = manager.config


def get_new_str(a: str, wanted=False):
    all_website_list = ManualConfig.SUPPORTED_WEBSITES
    if wanted:
        all_website_list = ["javlibrary", "javdb"]
    read_web_list = re.split(r"[,，]", a)
    new_website_list1 = [i for i in read_web_list if i in all_website_list]  # 去除错误网站
    new_website_list = []
    # 此处配置包含优先级, 因此必须按顺序去重
    [new_website_list.append(i) for i in new_website_list1 if i not in new_website_list]  # 去重
    new_str = ",".join(new_website_list)
    return new_str
