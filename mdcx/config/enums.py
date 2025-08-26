from .ui_schema import Enum


class NoEscape(Enum):
    NO_SKIP_SMALL_FILE = "no_skip_small_file"
    FOLDER = "folder"
    SKIP_SUCCESS_FILE = "skip_success_file"
    RECORD_SUCCESS_FILE = "record_success_file"
    CHECK_SYMLINK = "check_symlink"
    SYMLINK_DEFINITION = "symlink_definition"

    @classmethod
    def names(cls):
        return [
            "不跳过小文件",
            "目录",
            "跳过成功文件",
            "记录成功文件",
            "检查符号链接",
            "符号链接定义",
        ]


class CleanAction(Enum):
    CLEAN_EXT = "clean_ext"
    CLEAN_NAME = "clean_name"
    CLEAN_CONTAINS = "clean_contains"
    CLEAN_SIZE = "clean_size"
    CLEAN_IGNORE_EXT = "clean_ignore_ext"
    CLEAN_IGNORE_CONTAINS = "clean_ignore_contains"
    I_KNOW = "i_know"
    I_AGREE = "i_agree"
    AUTO_CLEAN = "auto_clean"

    @classmethod
    def names(cls):
        return [
            "清理指定后缀文件",
            "清理指定文件名",
            "清理包含特定字符串的文件",
            "清理小于指定大小的文件",
            "忽略指定后缀",
            "忽略包含特定字符串的文件",
            "我知道",
            "我同意",
            "自动清理",
        ]


class OutlineShow(Enum):
    SHOW_FROM = "show_from"
    SHOW_ZH_JP = "show_zh_jp"
    SHOW_JP_ZH = "show_jp_zh"

    @classmethod
    def names(cls):
        return ["显示来源", "显示中日", "显示日中"]


class TagInclude(Enum):
    ACTOR = "actor"
    LETTERS = "letters"
    SERIES = "series"
    STUDIO = "studio"
    PUBLISHER = "publisher"
    CNWORD = "cnword"
    MOSAIC = "mosaic"
    DEFINITION = "definition"

    @classmethod
    def names(cls):
        return [
            "演员",
            "字母",
            "Series",
            "Studio",
            "Publisher",
            "Cnword",
            "Mosaic",
            "Definition",
        ]


class WholeField(Enum):
    OUTLINE = "outline"
    ACTOR = "actor"
    THUMB = "thumb"
    POSTER = "poster"
    EXTRAFANART = "extrafanart"
    TRAILER = "trailer"
    RELEASE = "release"
    RUNTIME = "runtime"
    SCORE = "score"
    TAG = "tag"
    DIRECTOR = "director"
    SERIES = "series"
    STUDIO = "studio"
    PUBLISHER = "publisher"

    @classmethod
    def names(cls):
        return [
            "简介",
            "演员",
            "缩略图",
            "海报",
            "附加剧照",
            "预告片",
            "发布日期",
            "时长",
            "评分",
            "标签",
            "导演",
            "系列",
            "工作室",
            "发行商",
        ]


class NoneField(Enum):
    OUTLINE = "outline"
    ACTOR = "actor"
    THUMB = "thumb"
    POSTER = "poster"
    EXTRAFANART = "extrafanart"
    TRAILER = "trailer"
    RELEASE = "release"
    RUNTIME = "runtime"
    SCORE = "score"
    TAG = "tag"
    DIRECTOR = "director"
    SERIES = "series"
    STUDIO = "studio"
    PUBLISHER = "publisher"
    WANTED = "wanted"

    @classmethod
    def names(cls):
        return [
            "简介",
            "演员",
            "缩略图",
            "海报",
            "附加剧照",
            "预告片",
            "发布日期",
            "时长",
            "评分",
            "标签",
            "导演",
            "系列",
            "工作室",
            "发行商",
            "想看",
        ]


class NfoInclude(Enum):
    SORTTITLE = "sorttitle"
    ORIGINALTITLE = "originaltitle"
    TITLE_CD = "title_cd"
    OUTLINE = "outline"
    PLOT_ = "plot_"
    ORIGINALPLOT = "originalplot"
    OUTLINE_NO_CDATA = "outline_no_cdata"
    RELEASE_ = "release_"
    RELEASEDATE = "releasedate"
    PREMIERED = "premiered"
    COUNTRY = "country"
    MPAA = "mpaa"
    CUSTOMRATING = "customrating"
    YEAR = "year"
    RUNTIME = "runtime"
    WANTED = "wanted"
    SCORE = "score"
    CRITICRATING = "criticrating"
    ACTOR = "actor"
    ACTOR_ALL = "actor_all"
    DIRECTOR = "director"
    SERIES = "series"
    TAG = "tag"
    GENRE = "genre"
    ACTOR_SET = "actor_set"
    SERIES_SET = "series_set"
    STUDIO = "studio"
    MAKER = "maker"
    PUBLISHER = "publisher"
    LABEL = "label"
    POSTER = "poster"
    COVER = "cover"
    TRAILER = "trailer"
    WEBSITE = "website"

    @classmethod
    def names(cls):
        return [
            "排序标题",
            "原始标题",
            "标题CD",
            "简介",
            "剧情",
            "原始剧情",
            "无CDATA简介",
            "发布",
            "发布日期",
            "首映",
            "国家",
            "MPAA",
            "自定义评分",
            "年份",
            "时长",
            "想看",
            "评分",
            "评论家评分",
            "演员",
            "所有演员",
            "导演",
            "系列",
            "标签",
            "类型",
            "演员集",
            "系列集",
            "工作室",
            "制造商",
            "发行商",
            "标签",
            "海报",
            "封面",
            "预告片",
            "网站",
        ]


class Translator(Enum):
    YOUDAO = "youdao"
    GOOGLE = "google"
    DEEPL = "deepl"
    LLM = "llm"

    @classmethod
    def names(cls):
        return ["有道", "谷歌", "Deepl", "LLM"]


class ReadMode(Enum):
    HAS_NFO_UPDATE = "has_nfo_update"
    NO_NFO_SCRAPE = "no_nfo_scrape"
    READ_DOWNLOAD_AGAIN = "read_download_again"
    READ_UPDATE_NFO = "read_update_nfo"

    @classmethod
    def names(cls):
        return ["有NFO时更新", "无NFO时刮削", "重新下载", "更新NFO"]


class DownloadableFile(Enum):
    POSTER = "poster"
    THUMB = "thumb"
    FANART = "fanart"
    EXTRAFANART = "extrafanart"
    TRAILER = "trailer"
    NFO = "nfo"
    EXTRAFANART_EXTRAS = "extrafanart_extras"
    EXTRAFANART_COPY = "extrafanart_copy"
    THEME_VIDEOS = "theme_videos"
    IGNORE_PIC_FAIL = "ignore_pic_fail"
    IGNORE_YOUMA = "ignore_youma"
    IGNORE_WUMA = "ignore_wuma"
    IGNORE_FC2 = "ignore_fc2"
    IGNORE_GUOCHAN = "ignore_guochan"
    IGNORE_SIZE = "ignore_size"

    @classmethod
    def names(cls):
        return [
            "海报",
            "缩略图",
            "剧照",
            "额外剧照",
            "预告片",
            "Nfo",
            "额外剧照扩展",
            "额外剧照复制",
            "主题视频",
            "忽略图片失败",
            "忽略有码",
            "忽略无码",
            "忽略FC2",
            "忽略国产",
            "忽略大小",
        ]


class KeepableFile(Enum):
    POSTER = "poster"
    THUMB = "thumb"
    FANART = "fanart"
    EXTRAFANART = "extrafanart"
    TRAILER = "trailer"
    NFO = "nfo"
    EXTRAFANART_COPY = "extrafanart_copy"
    THEME_VIDEOS = "theme_videos"

    @classmethod
    def names(cls):
        return [
            "海报",
            "缩略图",
            "剧照",
            "额外剧照",
            "预告片",
            "nfo",
            "复制额外剧照",
            "主题视频",
        ]


class HDPicSource(Enum):
    POSTER = "poster"
    THUMB = "thumb"
    AMAZON = "amazon"
    OFFICIAL = "official"
    GOOGLE = "google"
    GOO_ONLY = "goo_only"

    @classmethod
    def names(cls):
        return ["poster", "thumb", "Amazon", "官网", "Google", "仅 Google"]


class FieldRule(Enum):
    DEL_ACTOR = "del_actor"
    DEL_CHAR = "del_char"
    FC2_SELLER = "fc2_seller"
    DEL_NUM = "del_num"

    @classmethod
    def names(cls):
        return ["移除标题后的演员名", "移除演员名中的括号", "使用 FC2 卖家作为演员名", "移除番号前缀数字"]


class ShowLocation(Enum):
    FOLDER = "folder"
    FILE = "file"

    @classmethod
    def names(cls):
        return ["目录", "文件"]


class CDChar(Enum):
    LETTER = "letter"
    ENDC = "endc"
    DIGITAL = "digital"
    MIDDLE_NUMBER = "middle_number"
    UNDERLINE = "underline"
    SPACE = "space"
    POINT = "point"

    @classmethod
    def names(cls):
        return [
            "除C以外的字母",
            "C结尾也视为分集而非字幕",
            "末尾两位数字",
            "不在结尾的数字",
            "分集分隔符: 下划线",
            "分集分隔符: 空格",
            "分集分隔符: 英文句号",
        ]


class EmbyAction(Enum):
    # todo 这些枚举对应 Emby 操作及配置的组合, 需简化
    ACTOR_INFO_ZH_CN = "actor_info_zh_cn"
    ACTOR_INFO_ZH_TW = "actor_info_zh_tw"
    ACTOR_INFO_JA = "actor_info_ja"
    ACTOR_INFO_ALL = "actor_info_all"
    ACTOR_INFO_MISS = "actor_info_miss"
    ACTOR_PHOTO_NET = "actor_photo_net"
    ACTOR_PHOTO_LOCAL = "actor_photo_local"
    ACTOR_PHOTO_ALL = "actor_photo_all"
    ACTOR_PHOTO_MISS = "actor_photo_miss"
    ACTOR_INFO_TRANSLATE = "actor_info_translate"
    ACTOR_INFO_PHOTO = "actor_info_photo"
    GRAPHIS_BACKDROP = "graphis_backdrop"
    GRAPHIS_FACE = "graphis_face"
    GRAPHIS_NEW = "graphis_new"
    ACTOR_PHOTO_AUTO = "actor_photo_auto"
    ACTOR_REPLACE = "actor_replace"

    @classmethod
    def names(cls):
        return [
            "获取简体中文演员信息",
            "获取繁体中文演员信息",
            "Actor Info Ja",
            "Actor Info All",
            "Actor Info Miss",
            "Actor Photo Net",
            "Actor Photo Local",
            "Actor Photo All",
            "Actor Photo Miss",
            "Actor Info Translate",
            "Actor Info Photo",
            "Graphis Backdrop",
            "Graphis Face",
            "Graphis New",
            "Actor Photo Auto",
            "Actor Replace",
        ]


class MarkType(Enum):
    SUB = "sub"
    YOUMA = "youma"
    UMR = "umr"
    LEAK = "leak"
    UNCENSORED = "uncensored"
    HD = "hd"

    @classmethod
    def names(cls):
        return ["字幕", "有码", "破解", "流出", "无码", "高清"]


class Switch(Enum):
    # todo 许多配置项不适用 web 应用
    AUTO_START = "auto_start"
    AUTO_EXIT = "auto_exit"
    REST_SCRAPE = "rest_scrape"
    TIMED_SCRAPE = "timed_scrape"
    REMAIN_TASK = "remain_task"
    SHOW_DIALOG_EXIT = "show_dialog_exit"
    SHOW_DIALOG_STOP_SCRAPE = "show_dialog_stop_scrape"
    SORT_DEL = "sort_del"
    QT_DIALOG = "qt_dialog"
    THEPORNDB_NO_HASH = "theporndb_no_hash"
    HIDE_DOCK = "hide_dock"
    PASSTHROUGH = "passthrough"
    HIDE_MENU = "hide_menu"
    DARK_MODE = "dark_mode"
    COPY_NETDISK_NFO = "copy_netdisk_nfo"
    SHOW_LOGS = "show_logs"
    HIDE_CLOSE = "hide_close"
    HIDE_MINI = "hide_mini"
    HIDE_NONE = "hide_none"
    # deperated
    IPV4_ONLY = "ipv4_only"

    @classmethod
    def names(cls):
        return [
            "自动开始",
            "自动退出",
            "Rest Scrape",
            "Timed Scrape",
            "Remain Task",
            "Show Dialog Exit",
            "Show Dialog Stop Scrape",
            "Sort Del",
            "Qt Dialog",
            "Theporndb No Hash",
            "Hide Dock",
            "Passthrough",
            "Hide Menu",
            "Dark Mode",
            "Copy Netdisk Nfo",
            "Show Logs",
            "Hide Close",
            "Hide Mini",
            "Hide None",
        ]


class SuffixSort(Enum):
    MOWORD = "moword"
    CNWORD = "cnword"
    DEFINITION = "definition"

    @classmethod
    def names(cls):
        return ["马赛克", "中文字幕", "清晰度"]


class Website(Enum):
    AIRAV = "airav"
    AIRAV_CC = "airav_cc"
    AVSEX = "avsex"
    AVSOX = "avsox"
    CABLEAV = "cableav"
    CNMDB = "cnmdb"
    DMM = "dmm"
    FALENO = "faleno"
    FANTASTICA = "fantastica"
    FC2 = "fc2"
    FC2CLUB = "fc2club"
    FC2HUB = "fc2hub"
    FC2PPVDB = "fc2ppvdb"
    FREEJAVBT = "freejavbt"
    GETCHU = "getchu"
    GIGA = "giga"
    HDOUBAN = "hdouban"
    HSCANGKU = "hscangku"
    IQQTV = "iqqtv"
    JAV321 = "jav321"
    JAVBUS = "javbus"
    JAVDAY = "javday"
    JAVDB = "javdb"
    JAVLIBRARY = "javlibrary"
    KIN8 = "kin8"
    LOVE6 = "love6"
    LULUBAR = "lulubar"
    MADOUQU = "madouqu"
    MDTV = "mdtv"
    MGSTAGE = "mgstage"
    MMTV = "7mmtv"
    MYWIFE = "mywife"
    PRESTIGE = "prestige"
    THEPORNDB = "theporndb"
    XCITY = "xcity"

    DAHLIA = "dahlia"
    GETCHU_DMM = "getchu_dmm"
    OFFICIAL = "official"


class Language(Enum):
    UNDEFINED = "undefined"
    UNKNOWN = "unknown"
    ZH_CN = "zh_cn"
    ZH_TW = "zh_tw"
    JP = "jp"
    EN = "en"
