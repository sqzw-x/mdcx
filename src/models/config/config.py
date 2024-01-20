import os
import os.path
import platform
import random
import re
import time
from configparser import RawConfigParser

from models.base.utils import singleton
from models.config.config_generated import GeneratedConfig
from models.config.config_manual import ManualConfig


@singleton
class MDCxConfig(GeneratedConfig, ManualConfig):

    mark_file_name = 'MDCx.config'

    def __init__(self):
        self.file = None
        self.folder = None
        self._path = None
        self._get_platform_info()
        self.read_config()
        self.youdaokey = 'Ygy_4c=r#e#4EX^NUGUc5'

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self.folder, self.file = os.path.split(path)
        self._path = path

    @path.getter
    def path(self):
        return self._path
    
    def get_mac_default_config_folder(self):
        """
        获取macOS下默认的配置文件夹路径

        ~/.mdcx

        :return: 配置文件夹路径
        """

        home = os.path.expanduser('~')
        folder_name = '.mdcx'
        config_folder = os.path.join(home, folder_name)
        if not os.path.exists(config_folder):
            os.makedirs(config_folder, exist_ok=True, mode=0o755)
        return config_folder

    def get_mark_file_path(self):
        """
        获取`记录了配置文件路径`的文件的路径。
        对于macOS，该文件位于`~/.mdcx/MDCx.config`。
        其他平台，该文件跟应用程序在同一目录下。
        """

        if platform.system() == 'Darwin':
            return os.path.join(self.get_mac_default_config_folder(), self.mark_file_name)
        else:
            return self.mark_file_name

    def read_config(self):
        self._get_config_path()
        reader = RawConfigParser()
        reader.read(self.path, encoding='UTF-8')
        for section in reader.sections():
            for key, value in reader.items(section):
                #  此处使用反射直接设置读取的配置, 缺少对键合法性的检测,
                #  有拼写错误的非法键会被直接读入, 不会报错, 不过不会被访问, 相应值会为默认值
                if key in self.INT_KEY:
                    setattr(self, key, int(value))
                elif key in self.FLOAT_KEY:
                    setattr(self, key, float(value))
                else:
                    setattr(self, key, value)
        self.update_config()

    def save_config(self):
        with open(self.get_mark_file_path(), 'w', encoding='UTF-8') as f:
            f.write(self.path)
        with open(self.path, "wt", encoding='UTF-8') as code:
            # 使用反射保存自定义网址设置
            custom_website_config = ''
            for website in ManualConfig.SUPPORTED_WEBSITES:
                if u := getattr(self, website + '_website', ''):
                    custom_website_config += f"{website}_website = {u}\n"
            print(f'''[modified_time]
modified_time = {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}
version = {self.version}

[media]
media_path = {self.media_path}
softlink_path = {self.softlink_path}
success_output_folder = {self.success_output_folder}
failed_output_folder = {self.failed_output_folder}
extrafanart_folder = {self.extrafanart_folder}
media_type = {self.media_type}
sub_type = {self.sub_type}
scrape_softlink_path = {self.scrape_softlink_path}

[escape]
folders = {self.folders}
string = {self.string}
file_size = {self.file_size}
no_escape = {self.no_escape}

[clean]
clean_ext = {self.clean_ext}
clean_name = {self.clean_name}
clean_contains = {self.clean_contains}
clean_size = {self.clean_size}
clean_ignore_ext = {self.clean_ignore_ext}
clean_ignore_contains = {self.clean_ignore_contains}
clean_enable = {self.clean_enable}

[common]
thread_number = {self.thread_number}
thread_time = {self.thread_time}
javdb_time = {self.javdb_time}
main_mode = {self.main_mode}
read_mode = {self.read_mode}
update_mode = {self.update_mode}
update_a_folder = {self.update_a_folder}
update_b_folder = {self.update_b_folder}
update_d_folder = {self.update_d_folder}
soft_link = {self.soft_link}
success_file_move = {self.success_file_move}
failed_file_move = {self.failed_file_move}
success_file_rename = {self.success_file_rename}
del_empty_folder = {self.del_empty_folder}
show_poster = {self.show_poster}

[file_download]
download_files = {self.download_files}
keep_files = {self.keep_files}
download_hd_pics = {self.download_hd_pics}
google_used = {self.google_used}
google_exclude = {self.google_exclude}

[website]
scrape_like = {self.scrape_like}
website_single = {self.website_single}
website_youma = {self.website_youma}
website_wuma = {self.website_wuma}
website_suren = {self.website_suren}
website_fc2 = {self.website_fc2}
website_oumei = {self.website_oumei}
website_guochan = {self.website_guochan}
whole_fields = {self.whole_fields}
none_fields = {self.none_fields}
website_set = {self.website_set}
title_website = {self.title_website}
title_zh_website = {self.title_zh_website}
title_website_exclude = {self.title_website_exclude}
outline_website = {self.outline_website}
outline_zh_website = {self.outline_zh_website}
outline_website_exclude = {self.outline_website_exclude}
actor_website = {self.actor_website}
actor_website_exclude = {self.actor_website_exclude}
thumb_website = {self.thumb_website}
thumb_website_exclude = {self.thumb_website_exclude}
poster_website = {self.poster_website}
poster_website_exclude = {self.poster_website_exclude}
extrafanart_website = {self.extrafanart_website}
extrafanart_website_exclude = {self.extrafanart_website_exclude}
trailer_website = {self.trailer_website}
trailer_website_exclude = {self.trailer_website_exclude}
tag_website = {self.tag_website}
tag_website_exclude = {self.tag_website_exclude}
release_website = {self.release_website}
release_website_exclude = {self.release_website_exclude}
runtime_website = {self.runtime_website}
runtime_website_exclude = {self.runtime_website_exclude}
score_website = {self.score_website}
score_website_exclude = {self.score_website_exclude}
director_website = {self.director_website}
director_website_exclude = {self.director_website_exclude}
series_website = {self.series_website}
series_website_exclude = {self.series_website_exclude}
studio_website = {self.studio_website}
studio_website_exclude = {self.studio_website_exclude}
publisher_website = {self.publisher_website}
publisher_website_exclude = {self.publisher_website_exclude}
wanted_website = {self.wanted_website}
translate_by = {self.translate_by}
deepl_key = {self.deepl_key}
title_language = {self.title_language}
title_sehua = {self.title_sehua}
title_yesjav = {self.title_yesjav}
title_translate = {self.title_translate}
title_sehua_zh = {self.title_sehua_zh}
outline_language = {self.outline_language}
outline_translate = {self.outline_translate}
outline_show = {self.outline_show}
actor_language = {self.actor_language}
actor_realname = {self.actor_realname}
actor_translate = {self.actor_translate}
tag_language = {self.tag_language}
tag_translate = {self.tag_translate}
tag_include = {self.tag_include}
director_language = {self.director_language}
director_translate = {self.director_translate}
series_language = {self.series_language}
series_translate = {self.series_translate}
studio_language = {self.studio_language}
studio_translate = {self.studio_translate}
publisher_language = {self.publisher_language}
publisher_translate = {self.publisher_translate}
nfo_include_new = {self.nfo_include_new}
nfo_tagline = {self.nfo_tagline}
nfo_tag_series = {self.nfo_tag_series}
nfo_tag_studio = {self.nfo_tag_studio}
nfo_tag_publisher = {self.nfo_tag_publisher}
# website: iqqtv, javbus, javdb, freejavbt, jav321, dmm, avsox, xcity, mgstage, fc2, fc2club, fc2hub, airav, javlibrary, mdtv

[Name_Rule]
folder_name = {self.folder_name}
naming_file = {self.naming_file}
naming_media = {self.naming_media}
prevent_char = {self.prevent_char}
fields_rule = {self.fields_rule}
suffix_sort = {self.suffix_sort}
actor_no_name = {self.actor_no_name}
release_rule = {self.release_rule}
folder_name_max = {self.folder_name_max}
file_name_max = {self.file_name_max}
actor_name_max = {self.actor_name_max}
actor_name_more = {self.actor_name_more}
umr_style = {self.umr_style}
leak_style = {self.leak_style}
wuma_style = {self.wuma_style}
youma_style = {self.youma_style}
show_moword = {self.show_moword}
show_4k = {self.show_4k}
cd_name = {self.cd_name}
cd_char = {self.cd_char}
pic_name = {self.pic_name}
trailer_name = {self.trailer_name}
hd_name = {self.hd_name}
hd_get = {self.hd_get}
# 命名字段有：title, originaltitle, actor, number, studio, publisher, year, mosaic, runtime, director, release, series, definition, cnword

[subtitle]
cnword_char = {self.cnword_char}
cnword_style = {self.cnword_style}
folder_cnword = {self.folder_cnword}
file_cnword = {self.file_cnword}
subtitle_folder = {self.subtitle_folder}
subtitle_add = {self.subtitle_add}
subtitle_add_chs = {self.subtitle_add_chs}
subtitle_add_rescrape = {self.subtitle_add_rescrape}

[emby]
server_type = {self.server_type}
emby_url = {self.emby_url}
api_key = {self.api_key}
user_id = {self.user_id}
emby_on = {self.emby_on}
use_database = {self.use_database}
info_database_path = {self.info_database_path}
gfriends_github = {self.gfriends_github}
actor_photo_folder = {self.actor_photo_folder}

[mark]
poster_mark = {self.poster_mark}
thumb_mark = {self.thumb_mark}
fanart_mark = {self.fanart_mark}
mark_size = {self.mark_size}
mark_type = {self.mark_type}
mark_fixed = {self.mark_fixed}
mark_pos = {self.mark_pos}
mark_pos_corner = {self.mark_pos_corner}
mark_pos_sub = {self.mark_pos_sub}
mark_pos_mosaic = {self.mark_pos_mosaic}
mark_pos_hd = {self.mark_pos_hd}
# mark_size: range 1-40
# mark_type: sub, youma, umr, leak, uncensored, hd
# mark_pos: top_left, top_right, bottom_left, bottom_right

[proxy]
type = {self.type}
proxy = {self.proxy}
timeout = {self.timeout}
retry = {self.retry}
{custom_website_config.strip()}
theporndb_api_token = {self.theporndb_api_token}
# type: no, http, socks5

[Cookies]
javdb = {self.javdb}
javbus = {self.javbus}
# cookies存在有效期，记得更新

[other]
show_web_log = {self.show_web_log}
show_from_log = {self.show_from_log}
show_data_log = {self.show_data_log}
save_log = {self.save_log}
update_check = {self.update_check}
local_library = {self.local_library}
actors_name = {self.actors_name}
netdisk_path = {self.netdisk_path}
localdisk_path = {self.localdisk_path}
window_title = {self.window_title}
switch_on = {self.switch_on}
timed_interval = {self.timed_interval}
rest_count = {self.rest_count}
rest_time = {self.rest_time}
statement = {self.statement}
''', file=code)

    def init_config(self):
        with open(self.path, "wt", encoding='UTF-8') as code:
            print(GeneratedConfig.CONFIG_STR, file=code)

    def update_config(self):
        # 获取proxies
        if self.type == 'http':
            self.proxies = {
                "http": "http://" + self.proxy,
                "https": "http://" + self.proxy,
            }
        elif self.type == 'socks5':
            self.proxies = {
                "http": "socks5h://" + self.proxy,
                "https": "socks5h://" + self.proxy,
            }
        else:
            self.proxies = None

        self.ipv4_only = 'ipv4_only' in self.switch_on
        self.theporndb_no_hash = 'theporndb_no_hash' in self.switch_on

        # 获取User-Agent
        temp_l = random.randint(110, 117)
        temp_m = random.randint(1, 5563)
        temp_n = random.randint(1, 180)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/%s.0.%s.%s Safari/537.36' % (
                temp_l, temp_m, temp_n),
        }

        # 获取javdb_cookie
        self.javdb_cookie = {'cookie': self.javdb} if self.javdb else None

        self.javbus_cookie = {'cookie': self.javbus} if self.javbus else None

        # 去掉^符号！！！
        self.cnword_style = self.cnword_style.strip('^')

        # 获取 Google 下载关键词列表
        temp_list = re.split(r'[,，]', self.google_used)
        self.google_keyused = [each for each in temp_list if each.strip()]  # 去空
        # 获取 Google 过滤关键词列表
        temp_list = re.split(r'[,，]', self.google_exclude)
        self.google_keyword = [each for each in temp_list if each.strip()]  # 去空

        # 是否记录刮削成功列表
        self.record_success_file = 'record_success_file' in self.no_escape

        # 是否清理文件以及清理列表
        can_clean = True if 'i_know' in self.clean_enable and 'i_agree' in self.clean_enable else False
        can_clean_auto = True if can_clean and 'clean_auto' in self.clean_enable else False
        clean_ext_list = re.split(r'[|｜，,]', self.clean_ext) \
            if can_clean and self.clean_ext and 'clean_ext' in self.clean_enable else []
        clean_name_list = re.split(r'[|｜，,]', self.clean_name) \
            if can_clean and self.clean_name and 'clean_name' in self.clean_enable else []
        clean_contains_list = re.split(r'[|｜，,]', self.clean_contains) \
            if can_clean and self.clean_contains and 'clean_contains' in self.clean_enable else []
        clean_size_list = self.clean_size if can_clean and 'clean_size' in self.clean_enable else ''
        clean_ignore_ext_list = re.split(r'[|｜，,]', self.clean_ignore_ext) \
            if can_clean and self.clean_ignore_ext and 'clean_ignore_ext' in self.clean_enable else []
        clean_ignore_contains_list = re.split(r'[|｜，,]', self.clean_ignore_contains) \
            if can_clean and self.clean_ignore_contains and 'clean_ignore_contains' in self.clean_enable else []
        self.can_clean = can_clean
        self.can_clean_auto = can_clean_auto
        self.clean_ext_list = clean_ext_list
        self.clean_name_list = clean_name_list
        self.clean_contains_list = clean_contains_list
        self.clean_size_list = clean_size_list
        self.clean_ignore_ext_list = clean_ignore_ext_list
        self.clean_ignore_contains_list = clean_ignore_contains_list

        # 获取排除字符列表
        temp_list = re.split('[,，]', self.string) + self.repl_list
        self.escape_string_list = []
        [self.escape_string_list.append(i) for i in temp_list if i.strip() and i not in self.escape_string_list]

        # 番号对应官网
        official_websites_dic = {}
        for key, value in self.official.items():
            temp_list = value.upper().split('|')
            for each in temp_list:
                official_websites_dic[each] = key
        self.official_websites = official_websites_dic

        # 字段命名规则-后缀字段顺序
        all_str_list = ['mosaic', 'cnword']
        read_str_list = re.split(r'[,，]', self.suffix_sort)
        new_str_list1 = [i1 for i1 in read_str_list if i1 in all_str_list]  # 去除不在list中的字符
        new_str_list = []
        [new_str_list.append(i1) for i1 in new_str_list1 if i1 not in new_str_list]  # 去重
        [new_str_list.append(i1) for i1 in all_str_list if i1 not in new_str_list]  # 补全
        new_str = ','.join(new_str_list)
        self.suffix_sort = new_str

    def _get_config_path(self):
        mdcx_config = self.get_mark_file_path()  # 此文件用于记录当前配置文件的绝对路径, 从而实现多配置切换
        # 此文件必须存在, 且与 main.py 或打包的可执行文件在同一目录下.
        if not os.path.exists(mdcx_config):  # 不存在时, 创建
            if platform.system() == 'Darwin':
                self.path = os.path.join(self.get_mac_default_config_folder(), 'config.ini')  # macOS下默认配置文件: ~/.mdcx/config.ini
            else:
                self.path = os.path.realpath('config.ini')  # 默认配置文件: 同目录下的 config.ini
            # 设置默认配置文件路径, 若存在则可读取, 否则生成默认配置文件
            with open(mdcx_config, 'w', encoding='UTF-8') as f:
                f.write(self.path)
            if not os.path.exists(self.path):
                self.init_config()
        else:
            with open(mdcx_config, 'r', encoding='UTF-8') as f:
                self.path = f.read()

    def _get_platform_info(self):
        self.is_windows = True
        self.is_mac = False
        self.is_nfc = True
        self.is_docker = False
        os_name = platform.system()
        if os_name != 'Windows':
            self.is_windows = False
        mac_ver = platform.mac_ver()[0]
        if os_name == 'Darwin' and mac_ver:
            self.is_mac = True
            ver_list = mac_ver.split('.')
            if float(ver_list[0] + '.' + ver_list[1]) < 10.12:
                self.is_nfc = False
        if os_name == 'Linux' or os_name == 'Java':
            self.is_docker = True


config: MDCxConfig = MDCxConfig()


def get_new_str(a: str, wanted=False):
    all_website_list = config.SUPPORTED_WEBSITES
    if wanted:
        all_website_list = ['javlibrary', 'javdb']
    read_web_list = re.split(r'[,，]', a)
    new_website_list1 = [i for i in read_web_list if i in all_website_list]  # 去除错误网站
    new_website_list = []
    # 此处配置包含优先级, 因此必须按顺序去重
    [new_website_list.append(i) for i in new_website_list1 if i not in new_website_list]  # 去重
    new_str = ','.join(new_website_list)
    return new_str
