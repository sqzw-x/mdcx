import os
import platform
import re
import traceback

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog

from models.base.file import delete_file
from models.base.path import get_main_path
from models.base.utils import convert_path
from models.config.config import config, get_new_str
from models.config.resources import resources
from models.core.flags import Flags
from models.core.utils import get_movie_path_setting
from models.core.web import check_proxyChange
from models.signals import signal


def load_config(self):
    config.read_config()
    config_folder = config.folder
    config_file = config.file
    config_path = config.path

    # 检测配置目录权限
    mdcx_config = True
    if not os.access(config_folder, os.W_OK) or not os.access(config_folder, os.R_OK):
        mdcx_config = False

    if os.path.exists(config_path):
        # ======================================================================================获取配置文件夹中的配置文件列表
        all_files = os.listdir(config_folder)
        all_config_files = [i for i in all_files if '.ini' in i]
        all_config_files.sort()
        self.Ui.comboBox_change_config.clear()
        self.Ui.comboBox_change_config.addItems(all_config_files)
        if config_file in all_config_files:
            self.Ui.comboBox_change_config.setCurrentIndex(all_config_files.index(config_file))
        else:
            self.Ui.comboBox_change_config.setCurrentIndex(all_config_files.index('config.ini'))

        # region modified_time
        # config.modified_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        try:  # 修改时间
            read_version = config.version
        except:
            read_version = 20220101
        # endregion

        # region media
        self.Ui.lineEdit_movie_path.setText(convert_path(config.media_path))  # 视频目录
        self.Ui.lineEdit_movie_softlink_path.setText(convert_path(config.softlink_path))  # 软链接目录
        self.Ui.lineEdit_success.setText(convert_path(config.success_output_folder))  # 成功目录
        self.Ui.lineEdit_fail.setText(convert_path(config.failed_output_folder))  # 失败目录
        self.Ui.lineEdit_extrafanart_dir.setText(str(config.extrafanart_folder))  # 剧照副本目录
        self.Ui.lineEdit_movie_type.setText(str(config.media_type))  # 视频类型
        self.Ui.lineEdit_sub_type.setText(str(config.sub_type).replace('.txt|', ''))  # 字幕类型
        scrape_softlink_path = config.scrape_softlink_path  # 不过滤文件、文件夹
        if scrape_softlink_path:
            self.Ui.checkBox_scrape_softlink_path.setChecked(True)
        else:
            self.Ui.checkBox_scrape_softlink_path.setChecked(False)
        # endregion

        # region escape
        self.Ui.lineEdit_escape_dir.setText(str(config.folders))  # 排除目录
        self.Ui.lineEdit_escape_dir_move.setText(str(config.folders))  # 排除目录-工具页面
        escape_string = str(config.string)  # 多余字符串
        if read_version < 20230326:
            escape_string = 'h_720,' + escape_string
        self.Ui.lineEdit_escape_string.setText(escape_string)
        self.Ui.lineEdit_escape_size.setText(str(float(config.file_size)))  # 小文件
        no_escape = config.no_escape  # 不过滤文件、文件夹
        self.Ui.checkBox_no_escape_file.setChecked('no_skip_small_file' in no_escape)
        self.Ui.checkBox_no_escape_dir.setChecked('folder' in no_escape)
        self.Ui.checkBox_skip_success_file.setChecked('skip_success_file' in no_escape)
        self.Ui.checkBox_record_success_file.setChecked('record_success_file' in no_escape)
        self.Ui.checkBox_check_symlink.setChecked('check_symlink' in no_escape)
        self.Ui.checkBox_check_symlink_definition.setChecked('symlink_definition' in no_escape)
        # endregion

        # region clean
        self.Ui.lineEdit_clean_file_ext.setText(str(config.clean_ext))  # 清理扩展名等于
        self.Ui.lineEdit_clean_file_name.setText(str(config.clean_name))  # 清理文件名等于
        self.Ui.lineEdit_clean_file_contains.setText(str(config.clean_contains))  # 清理文件名包含
        self.Ui.lineEdit_clean_file_size.setText(str(float(config.clean_size)))  # 清理文件大小
        self.Ui.lineEdit_clean_excluded_file_ext.setText(str(config.clean_ignore_ext))  # 不清理扩展名
        self.Ui.lineEdit_clean_excluded_file_contains.setText(str(config.clean_ignore_contains))  # 不清理文件名包含
        clean_enable = config.clean_enable
        # region clean_enable
        self.Ui.checkBox_clean_file_ext.setChecked('clean_ext' in clean_enable)
        self.Ui.checkBox_clean_file_name.setChecked('clean_name' in clean_enable)
        self.Ui.checkBox_clean_file_contains.setChecked('clean_contains' in clean_enable)
        self.Ui.checkBox_clean_file_size.setChecked('clean_size' in clean_enable)
        self.Ui.checkBox_clean_excluded_file_ext.setChecked('clean_ignore_ext' in clean_enable)
        self.Ui.checkBox_clean_excluded_file_contains.setChecked('clean_ignore_contains' in clean_enable)
        self.Ui.checkBox_i_understand_clean.setChecked('i_know' in clean_enable)
        self.Ui.checkBox_i_agree_clean.setChecked('i_agree' in clean_enable)
        self.Ui.checkBox_auto_clean.setChecked('auto_clean' in clean_enable)
        # endregion
        # endregion

        # region website
        AllItems = [self.Ui.comboBox_website_all.itemText(i) for i in range(self.Ui.comboBox_website_all.count())]
        website_single = config.website_single  # 指定单个刮削网站
        self.Ui.comboBox_website_all.setCurrentIndex(AllItems.index(website_single))
        temp_youma = str(config.website_youma)  # 有码番号刮削网站
        website_youma = get_new_str(temp_youma)
        self.Ui.lineEdit_website_youma.setText(str(website_youma))
        website_wuma = get_new_str(str(config.website_wuma))  # 无码番号刮削网站
        self.Ui.lineEdit_website_wuma.setText(str(website_wuma))
        website_suren = get_new_str(str(config.website_suren))  # 素人番号刮削网站
        self.Ui.lineEdit_website_suren.setText(str(website_suren))
        website_fc2 = get_new_str(str(config.website_fc2))  # FC2番号刮削网站
        self.Ui.lineEdit_website_fc2.setText(str(website_fc2))
        temp_oumei = str(config.website_oumei)  # 欧美番号刮削网站
        if 'theporndb' not in temp_oumei:
            temp_oumei = 'theporndb,' + temp_oumei
        website_oumei = get_new_str(temp_oumei)
        self.Ui.lineEdit_website_oumei.setText(str(website_oumei))
        website_guochan = get_new_str(str(config.website_guochan))  # 国产番号刮削网站
        self.Ui.lineEdit_website_guochan.setText(str(website_guochan))

        # 刮削偏好
        if 'speed' in config.scrape_like:
            self.Ui.radioButton_scrape_speed.setChecked(True)
            Flags.scrape_like_text = '速度优先'
        elif 'single' in config.scrape_like:
            self.Ui.radioButton_scrape_single.setChecked(True)
            Flags.scrape_like_text = '指定网站'
        else:
            self.Ui.radioButton_scrape_info.setChecked(True)
            Flags.scrape_like_text = '字段优先'

        website_set = str(config.website_set)
        self.Ui.checkBox_use_official_data.setChecked('official,' in website_set)

        title_website = get_new_str(str(config.title_website))  # 标题字段网站优先级
        if read_version < 20230405:
            title_website = 'theporndb,mgstage,' + title_website
        self.Ui.lineEdit_title_website.setText(str(title_website))
        title_zh_website = get_new_str(str(config.title_zh_website))  # 中文标题字段网站优先级
        self.Ui.lineEdit_title_zh_website.setText(str(title_zh_website))

        title_website_exclude = get_new_str(str(config.title_website_exclude))  # 标题字段排除网站
        self.Ui.lineEdit_title_website_exclude.setText(str(title_website_exclude))

        title_language = config.title_language  # 标题语言
        if title_language == 'zh_cn':
            self.Ui.radioButton_title_zh_cn.setChecked(True)
        elif title_language == 'zh_tw':
            self.Ui.radioButton_title_zh_tw.setChecked(True)
        else:
            self.Ui.radioButton_title_jp.setChecked(True)

        title_sehua = config.title_sehua  # 增强翻译-sehua
        if title_sehua == 'on':
            self.Ui.checkBox_title_sehua.setChecked(True)
        else:
            self.Ui.checkBox_title_sehua.setChecked(False)

        title_yesjav = config.title_yesjav  # 增强翻译-yesjav
        if title_yesjav == 'on':
            self.Ui.checkBox_title_yesjav.setChecked(True)
        else:
            self.Ui.checkBox_title_yesjav.setChecked(False)

        title_translate = config.title_translate  # 标题增强翻译-使用翻译引擎
        if title_translate == 'on':
            self.Ui.checkBox_title_translate.setChecked(True)
        else:
            self.Ui.checkBox_title_translate.setChecked(False)

        title_sehua_zh = config.title_sehua_zh  # 增强翻译-优先sehua
        if title_sehua_zh == 'on':
            self.Ui.checkBox_title_sehua_2.setChecked(True)
        else:
            self.Ui.checkBox_title_sehua_2.setChecked(False)

        outline_website = get_new_str(str(config.outline_website))  # 简介字段网站优先级
        self.Ui.lineEdit_outline_website.setText(str(outline_website))
        outline_zh_website = get_new_str(str(config.outline_zh_website))  # 中文简介字段网站优先级
        self.Ui.lineEdit_outline_zh_website.setText(str(outline_zh_website))

        outline_website_exclude = get_new_str(str(config.outline_website_exclude))  # 简介字段排除网站
        self.Ui.lineEdit_outline_website_exclude.setText(str(outline_website_exclude))

        outline_language = config.outline_language  # 简介语言
        if outline_language == 'zh_cn':
            self.Ui.radioButton_outline_zh_cn.setChecked(True)
        elif outline_language == 'zh_tw':
            self.Ui.radioButton_outline_zh_tw.setChecked(True)
        elif outline_language == 'jp':
            self.Ui.radioButton_outline_jp.setChecked(True)
        else:
            self.Ui.radioButton_outline_zh_cn.setChecked(True)

        outline_translate = config.outline_translate  # 简介-使用翻译引擎
        if outline_translate == 'on':
            self.Ui.checkBox_outline_translate.setChecked(True)
        else:
            self.Ui.checkBox_outline_translate.setChecked(False)
        outline_show = config.outline_show  # 简介-显示翻译来源、双语显示
        self.Ui.checkBox_show_translate_from.setChecked('show_from' in outline_show)
        if 'show_zh_jp' in outline_show:
            self.Ui.radioButton_trans_show_zh_jp.setChecked(True)
        elif 'show_jp_zh' in outline_show:
            self.Ui.radioButton_trans_show_jp_zh.setChecked(True)
        else:
            self.Ui.radioButton_trans_show_one.setChecked(True)

        actor_website = get_new_str(str(config.actor_website))  # 演员字段网站优先级
        self.Ui.lineEdit_actor_website.setText(str(actor_website))

        actor_website_exclude = get_new_str(str(config.actor_website_exclude))  # 演员字段排除网站
        self.Ui.lineEdit_actor_website_exclude.setText(str(actor_website_exclude))

        actor_language = config.actor_language  # 演员映射表输出
        if actor_language == 'zh_cn':
            self.Ui.radioButton_actor_zh_cn.setChecked(True)
        elif actor_language == 'zh_tw':
            self.Ui.radioButton_actor_zh_tw.setChecked(True)
        elif actor_language == 'jp':
            self.Ui.radioButton_actor_jp.setChecked(True)
        else:
            self.Ui.radioButton_actor_zh_cn.setChecked(True)

        actor_realname = config.actor_realname  # 演员-使用真实名字
        if actor_realname == 'on':
            self.Ui.checkBox_actor_realname.setChecked(True)
        else:
            self.Ui.checkBox_actor_realname.setChecked(False)

        actor_translate = config.actor_translate  # 演员-使用演员映射表
        if actor_translate == 'on':
            self.Ui.checkBox_actor_translate.setChecked(True)
        else:
            self.Ui.checkBox_actor_translate.setChecked(False)

        tag_website = get_new_str(str(config.tag_website))  # 标签字段网站优先级
        self.Ui.lineEdit_tag_website.setText(str(tag_website))

        tag_website_exclude = get_new_str(str(config.tag_website_exclude))  # 标签字段排除网站
        self.Ui.lineEdit_tag_website_exclude.setText(str(tag_website_exclude))

        tag_language = config.tag_language  # 标签字段语言
        if tag_language == 'zh_cn':
            self.Ui.radioButton_tag_zh_cn.setChecked(True)
        elif tag_language == 'zh_tw':
            self.Ui.radioButton_tag_zh_tw.setChecked(True)
        elif tag_language == 'jp':
            self.Ui.radioButton_tag_jp.setChecked(True)
        else:
            self.Ui.radioButton_tag_zh_cn.setChecked(True)

        tag_translate = config.tag_translate  # 标签-使用信息映射表
        if tag_translate == 'on':
            self.Ui.checkBox_tag_translate.setChecked(True)
        else:
            self.Ui.checkBox_tag_translate.setChecked(False)

        tag_include = config.tag_include  # 写入标签字段的信息
        # region tag_include
        self.Ui.checkBox_tag_actor.setChecked('actor' in tag_include)
        self.Ui.checkBox_tag_letters.setChecked('letters' in tag_include)
        self.Ui.checkBox_tag_series.setChecked('series' in tag_include)
        self.Ui.checkBox_tag_studio.setChecked('studio' in tag_include)
        self.Ui.checkBox_tag_publisher.setChecked('publisher' in tag_include)
        self.Ui.checkBox_tag_cnword.setChecked('cnword' in tag_include)
        self.Ui.checkBox_tag_mosaic.setChecked('mosaic' in tag_include)
        self.Ui.checkBox_tag_definition.setChecked('definition' in tag_include)
        # endregion

        series_website = get_new_str(str(config.series_website))  # 系列字段网站优先级
        self.Ui.lineEdit_series_website.setText(str(series_website))

        series_website_exclude = get_new_str(str(config.series_website_exclude))  # 系列字段排除网站
        self.Ui.lineEdit_series_website_exclude.setText(str(series_website_exclude))

        series_language = config.series_language  # 系列字段语言
        if series_language == 'zh_cn':
            self.Ui.radioButton_series_zh_cn.setChecked(True)
        elif series_language == 'zh_tw':
            self.Ui.radioButton_series_zh_tw.setChecked(True)
        elif series_language == 'jp':
            self.Ui.radioButton_series_jp.setChecked(True)
        else:
            self.Ui.radioButton_series_zh_cn.setChecked(True)

        series_translate = config.series_translate  # 系列-使用信息映射表
        if series_translate == 'on':
            self.Ui.checkBox_series_translate.setChecked(True)
        else:
            self.Ui.checkBox_series_translate.setChecked(False)

        studio_website = get_new_str(str(config.studio_website))  # 片商字段网站优先级
        self.Ui.lineEdit_studio_website.setText(str(studio_website))

        studio_website_exclude = get_new_str(str(config.studio_website_exclude))  # 片商字段排除网站
        self.Ui.lineEdit_studio_website_exclude.setText(str(studio_website_exclude))

        studio_language = config.studio_language  # 片商字段语言
        if studio_language == 'zh_cn':
            self.Ui.radioButton_studio_zh_cn.setChecked(True)
        elif studio_language == 'zh_tw':
            self.Ui.radioButton_studio_zh_tw.setChecked(True)
        elif studio_language == 'jp':
            self.Ui.radioButton_studio_jp.setChecked(True)
        else:
            self.Ui.radioButton_studio_zh_cn.setChecked(True)

        studio_translate = config.studio_translate  # 片商-使用信息映射表
        if studio_translate == 'on':
            self.Ui.checkBox_studio_translate.setChecked(True)
        else:
            self.Ui.checkBox_studio_translate.setChecked(False)

        wanted_website = get_new_str(str(config.wanted_website), wanted=True)  # 想看人数
        self.Ui.lineEdit_wanted_website.setText(str(wanted_website))

        publisher_website = get_new_str(str(config.publisher_website))  # 发行字段网站优先级
        self.Ui.lineEdit_publisher_website.setText(str(publisher_website))

        publisher_website_exclude = get_new_str(str(config.publisher_website_exclude))  # 发行字段排除网站
        self.Ui.lineEdit_publisher_website_exclude.setText(str(publisher_website_exclude))

        publisher_language = config.publisher_language  # 发行字段语言
        if publisher_language == 'zh_cn':
            self.Ui.radioButton_publisher_zh_cn.setChecked(True)
        elif publisher_language == 'zh_tw':
            self.Ui.radioButton_publisher_zh_tw.setChecked(True)
        elif publisher_language == 'jp':
            self.Ui.radioButton_publisher_jp.setChecked(True)
        else:
            self.Ui.radioButton_publisher_zh_cn.setChecked(True)

        publisher_translate = config.publisher_translate  # 发行-使用信息映射表
        if publisher_translate == 'on':
            self.Ui.checkBox_publisher_translate.setChecked(True)
        else:
            self.Ui.checkBox_publisher_translate.setChecked(False)

        director_website = get_new_str(str(config.director_website))  # 导演字段网站优先级
        self.Ui.lineEdit_director_website.setText(str(director_website))

        director_website_exclude = get_new_str(str(config.director_website_exclude))  # 导演字段排除网站
        self.Ui.lineEdit_director_website_exclude.setText(str(director_website_exclude))

        director_language = config.director_language  # 导演字段语言
        if director_language == 'zh_cn':
            self.Ui.radioButton_director_zh_cn.setChecked(True)
        elif director_language == 'zh_tw':
            self.Ui.radioButton_director_zh_tw.setChecked(True)
        elif director_language == 'jp':
            self.Ui.radioButton_director_jp.setChecked(True)
        else:
            self.Ui.radioButton_director_zh_cn.setChecked(True)

        director_translate = config.director_translate  # 导演-使用信息映射表
        if director_translate == 'on':
            self.Ui.checkBox_director_translate.setChecked(True)
        else:
            self.Ui.checkBox_director_translate.setChecked(False)

        poster_website = get_new_str(str(config.poster_website))  # 封面字段网站优先级
        self.Ui.lineEdit_poster_website.setText(str(poster_website))

        poster_website_exclude = get_new_str(str(config.poster_website_exclude))  # 封面字段排除网站
        self.Ui.lineEdit_poster_website_exclude.setText(str(poster_website_exclude))

        thumb_website = get_new_str(str(config.thumb_website))  # 背景字段网站优先级
        self.Ui.lineEdit_thumb_website.setText(str(thumb_website))

        thumb_website_exclude = get_new_str(str(config.thumb_website_exclude))  # 背景字段排除网站
        self.Ui.lineEdit_thumb_website_exclude.setText(str(thumb_website_exclude))

        extrafanart_website = get_new_str(str(config.extrafanart_website))  # 剧照字段网站优先级
        self.Ui.lineEdit_extrafanart_website.setText(str(extrafanart_website))

        extrafanart_website_exclude = get_new_str(str(config.extrafanart_website_exclude))  # 剧照字段排除网站
        self.Ui.lineEdit_extrafanart_website_exclude.setText(str(extrafanart_website_exclude))

        score_website = get_new_str(str(config.score_website))  # 评分字段网站优先级
        self.Ui.lineEdit_score_website.setText(str(score_website))

        score_website_exclude = get_new_str(str(config.score_website_exclude))  # 评分字段排除网站
        self.Ui.lineEdit_score_website_exclude.setText(str(score_website_exclude))

        release_website = get_new_str(str(config.release_website))  # 发行日期字段网站优先级
        self.Ui.lineEdit_release_website.setText(str(release_website))

        release_website_exclude = get_new_str(str(config.release_website_exclude))  # 发行日期字段排除网站
        self.Ui.lineEdit_release_website_exclude.setText(str(release_website_exclude))

        runtime_website = get_new_str(str(config.runtime_website))  # 时长字段网站优先级
        self.Ui.lineEdit_runtime_website.setText(str(runtime_website))

        runtime_website_exclude = get_new_str(str(config.runtime_website_exclude))  # 时长字段排除网站
        self.Ui.lineEdit_runtime_website_exclude.setText(str(runtime_website_exclude))

        trailer_website = get_new_str(str(config.trailer_website))  # 预告片字段网站优先级
        self.Ui.lineEdit_trailer_website.setText(str(trailer_website))

        trailer_website_exclude = get_new_str(str(config.trailer_website_exclude))  # 预告片字段排除网站
        self.Ui.lineEdit_trailer_website_exclude.setText(str(trailer_website_exclude))

        whole_fields = config.whole_fields  # 刮削设置
        none_fields = config.none_fields
        # region whole_fields
        if 'outline' in whole_fields:
            self.Ui.radioButton_outline_more.setChecked(True)
        elif 'outline' in none_fields:
            self.Ui.radioButton_outline_none.setChecked(True)
        else:
            self.Ui.radioButton_outline_listed.setChecked(True)

        if 'actor' in whole_fields:
            self.Ui.radioButton_actor_more.setChecked(True)
        elif 'actor' in none_fields:
            self.Ui.radioButton_actor_none.setChecked(True)
        else:
            self.Ui.radioButton_actor_listed.setChecked(True)

        if 'thumb' in whole_fields:
            self.Ui.radioButton_thumb_more.setChecked(True)
        elif 'thumb' in none_fields:
            self.Ui.radioButton_thumb_none.setChecked(True)
        else:
            self.Ui.radioButton_thumb_listed.setChecked(True)

        if 'poster' in whole_fields:
            self.Ui.radioButton_poster_more.setChecked(True)
        elif 'poster' in none_fields:
            self.Ui.radioButton_poster_none.setChecked(True)
        else:
            self.Ui.radioButton_poster_listed.setChecked(True)

        if 'extrafanart' in whole_fields:
            self.Ui.radioButton_extrafanart_more.setChecked(True)
        elif 'extrafanart' in none_fields:
            self.Ui.radioButton_extrafanart_none.setChecked(True)
        else:
            self.Ui.radioButton_extrafanart_listed.setChecked(True)

        if 'trailer' in whole_fields:
            self.Ui.radioButton_trailer_more.setChecked(True)
        elif 'trailer' in none_fields:
            self.Ui.radioButton_trailer_none.setChecked(True)
        else:
            self.Ui.radioButton_trailer_listed.setChecked(True)

        if 'tag' in whole_fields:
            self.Ui.radioButton_tag_more.setChecked(True)
        elif 'tag' in none_fields:
            self.Ui.radioButton_tag_none.setChecked(True)
        else:
            self.Ui.radioButton_tag_listed.setChecked(True)

        if 'release' in whole_fields:
            self.Ui.radioButton_release_more.setChecked(True)
        elif 'release' in none_fields:
            self.Ui.radioButton_release_none.setChecked(True)
        else:
            self.Ui.radioButton_release_listed.setChecked(True)

        if 'runtime' in whole_fields:
            self.Ui.radioButton_runtime_more.setChecked(True)
        elif 'runtime' in none_fields:
            self.Ui.radioButton_runtime_none.setChecked(True)
        else:
            self.Ui.radioButton_runtime_listed.setChecked(True)

        if 'score' in whole_fields:
            self.Ui.radioButton_score_more.setChecked(True)
        elif 'score' in none_fields:
            self.Ui.radioButton_score_none.setChecked(True)
        else:
            self.Ui.radioButton_score_listed.setChecked(True)

        if 'director' in whole_fields:
            self.Ui.radioButton_director_more.setChecked(True)
        elif 'director' in none_fields:
            self.Ui.radioButton_director_none.setChecked(True)
        else:
            self.Ui.radioButton_director_listed.setChecked(True)

        if 'series' in whole_fields:
            self.Ui.radioButton_series_more.setChecked(True)
        elif 'series' in none_fields:
            self.Ui.radioButton_series_none.setChecked(True)
        else:
            self.Ui.radioButton_series_listed.setChecked(True)

        if 'studio' in whole_fields:
            self.Ui.radioButton_studio_more.setChecked(True)
        elif 'studio' in none_fields:
            self.Ui.radioButton_studio_none.setChecked(True)
        else:
            self.Ui.radioButton_studio_listed.setChecked(True)

        if 'publisher' in whole_fields:
            self.Ui.radioButton_publisher_more.setChecked(True)
        elif 'publisher' in none_fields:
            self.Ui.radioButton_publisher_none.setChecked(True)
        else:
            self.Ui.radioButton_publisher_listed.setChecked(True)

        if 'wanted' in none_fields:
            self.Ui.radioButton_wanted_none.setChecked(True)
        else:
            self.Ui.radioButton_wanted_listed.setChecked(True)
        # endregion

        nfo_tagline = str(config.nfo_tagline)  # tagline
        self.Ui.lineEdit_nfo_tagline.setText(str(nfo_tagline))

        nfo_tag_series = str(config.nfo_tag_series)  # nfo_tag_series
        self.Ui.lineEdit_nfo_tag_series.setText(str(nfo_tag_series))
        nfo_tag_studio = str(config.nfo_tag_studio)  # nfo_tag_studio
        self.Ui.lineEdit_nfo_tag_studio.setText(str(nfo_tag_studio))
        nfo_tag_publisher = str(config.nfo_tag_publisher)  # nfo_tag_publisher
        self.Ui.lineEdit_nfo_tag_publisher.setText(str(nfo_tag_publisher))

        nfo_include_new = config.nfo_include_new  # 写入nfo的字段
        # region nfo_include_new
        if read_version < 20230302:
            nfo_include_new = nfo_include_new.replace(',set,', ',series_set,')
            nfo_include_new += 'sorttitle,originaltitle,outline,plot_,originalplot,website,'
            if 'release' in nfo_include_new:
                nfo_include_new += 'release_, releasedate,premiered,'
            if 'mpaa,' in nfo_include_new:
                nfo_include_new += 'country,customrating,'
            if 'studio,' in nfo_include_new:
                nfo_include_new += 'maker,'
            if 'publisher,' in nfo_include_new:
                nfo_include_new += 'label,'

        self.Ui.checkBox_nfo_sorttitle.setChecked('sorttitle,' in nfo_include_new)
        self.Ui.checkBox_nfo_originaltitle.setChecked('originaltitle,' in nfo_include_new)
        self.Ui.checkBox_nfo_title_cd.setChecked('title_cd,' in nfo_include_new)
        self.Ui.checkBox_nfo_outline.setChecked('outline,' in nfo_include_new)
        self.Ui.checkBox_nfo_plot.setChecked('plot_,' in nfo_include_new)
        self.Ui.checkBox_nfo_originalplot.setChecked('originalplot,' in nfo_include_new)
        self.Ui.checkBox_outline_cdata.setChecked('outline_no_cdata,' in nfo_include_new)
        self.Ui.checkBox_nfo_release.setChecked('release_,' in nfo_include_new)
        self.Ui.checkBox_nfo_relasedate.setChecked('releasedate,' in nfo_include_new)
        self.Ui.checkBox_nfo_premiered.setChecked('premiered,' in nfo_include_new)

        self.Ui.checkBox_nfo_country.setChecked('country,' in nfo_include_new)
        self.Ui.checkBox_nfo_mpaa.setChecked('mpaa,' in nfo_include_new)
        self.Ui.checkBox_nfo_customrating.setChecked('customrating,' in nfo_include_new)
        self.Ui.checkBox_nfo_year.setChecked('year,' in nfo_include_new)
        self.Ui.checkBox_nfo_runtime.setChecked('runtime,' in nfo_include_new)
        self.Ui.checkBox_nfo_wanted.setChecked('wanted,' in nfo_include_new)
        self.Ui.checkBox_nfo_score.setChecked('score,' in nfo_include_new)
        self.Ui.checkBox_nfo_criticrating.setChecked('criticrating,' in nfo_include_new)
        self.Ui.checkBox_nfo_actor.setChecked('actor,' in nfo_include_new)
        self.Ui.checkBox_nfo_all_actor.setChecked('actor_all,' in nfo_include_new)
        self.Ui.checkBox_nfo_director.setChecked('director,' in nfo_include_new)
        self.Ui.checkBox_nfo_series.setChecked('series,' in nfo_include_new)
        self.Ui.checkBox_nfo_tag.setChecked('tag,' in nfo_include_new)
        self.Ui.checkBox_nfo_genre.setChecked('genre,' in nfo_include_new)
        self.Ui.checkBox_nfo_actor_set.setChecked('actor_set,' in nfo_include_new)
        self.Ui.checkBox_nfo_set.setChecked('series_set,' in nfo_include_new)
        self.Ui.checkBox_nfo_studio.setChecked('studio,' in nfo_include_new)
        self.Ui.checkBox_nfo_maker.setChecked('maker,' in nfo_include_new)
        self.Ui.checkBox_nfo_publisher.setChecked('publisher,' in nfo_include_new)
        self.Ui.checkBox_nfo_label.setChecked('label,' in nfo_include_new)
        self.Ui.checkBox_nfo_poster.setChecked('poster,' in nfo_include_new)
        self.Ui.checkBox_nfo_cover.setChecked('cover,' in nfo_include_new)
        self.Ui.checkBox_nfo_trailer.setChecked('trailer,' in nfo_include_new)
        self.Ui.checkBox_nfo_website.setChecked('website,' in nfo_include_new)
        # endregion

        translate_by = config.translate_by  # 翻译引擎
        if 'youdao' in translate_by:
            self.Ui.checkBox_youdao.setChecked(True)
        if 'google' in translate_by:
            self.Ui.checkBox_google.setChecked(True)
        if 'deepl' in translate_by:
            self.Ui.checkBox_deepl.setChecked(True)
        Flags.translate_by_list = translate_by.strip(',').split(',') if translate_by.strip(',') else []

        self.Ui.lineEdit_deepl_key.setText(str(config.deepl_key))  # deepl_key
        # endregion

        # region common
        thread_number = int(config.thread_number)  # 线程数量
        self.Ui.horizontalSlider_thread.setValue(thread_number)
        self.Ui.lcdNumber_thread.display(thread_number)

        thread_time = int(config.thread_time)  # 线程延时
        self.Ui.horizontalSlider_thread_time.setValue(thread_time)
        self.Ui.lcdNumber_thread_time.display(thread_time)

        javdb_time = int(config.javdb_time)  # javdb 延时
        self.Ui.horizontalSlider_javdb_time.setValue(javdb_time)
        self.Ui.lcdNumber_javdb_time.display(javdb_time)

        main_mode = int(config.main_mode)  # 刮削模式
        if main_mode == 1:
            self.Ui.radioButton_mode_common.setChecked(True)
            Flags.main_mode_text = '正常模式'
        elif main_mode == 2:
            self.Ui.radioButton_mode_sort.setChecked(True)
            Flags.main_mode_text = '整理模式'
        elif main_mode == 3:
            self.Ui.radioButton_mode_update.setChecked(True)
            Flags.main_mode_text = '更新模式'
        elif main_mode == 4:
            self.Ui.radioButton_mode_read.setChecked(True)
            Flags.main_mode_text = '读取模式'
        else:
            self.Ui.radioButton_mode_common.setChecked(True)
            Flags.main_mode_text = '正常模式'

        read_mode = config.read_mode  # 有nfo，是否执行更新模式
        # region read_mode
        self.Ui.checkBox_read_has_nfo_update.setChecked('has_nfo_update' in read_mode)
        self.Ui.checkBox_read_download_file_again.setChecked('read_download_again' in read_mode)
        self.Ui.checkBox_read_translate_again.setChecked('read_translate_again' in read_mode)
        self.Ui.checkBox_read_no_nfo_scrape.setChecked('no_nfo_scrape' in read_mode)
        # endregion

        self.Ui.checkBox_update_a.setChecked(False)  # 更新模式
        update_mode = config.update_mode
        if update_mode == 'c':
            self.Ui.radioButton_update_c.setChecked(True)
        elif update_mode == 'bc':
            self.Ui.radioButton_update_b_c.setChecked(True)
        elif update_mode == 'abc':
            self.Ui.radioButton_update_b_c.setChecked(True)
            self.Ui.checkBox_update_a.setChecked(True)
        elif update_mode == 'd':
            self.Ui.radioButton_update_d_c.setChecked(True)
        else:
            self.Ui.radioButton_update_c.setChecked(True)

        self.Ui.lineEdit_update_a_folder.setText(str(config.update_a_folder))  # 更新模式 - a 目录
        self.Ui.lineEdit_update_b_folder.setText(str(config.update_b_folder))  # 更新模式 - b 目录
        self.Ui.lineEdit_update_d_folder.setText(str(config.update_d_folder))  # 更新模式 - d 目录

        soft_link = int(config.soft_link)  # 软链接
        if soft_link == 1:
            self.Ui.radioButton_soft_on.setChecked(True)
        elif soft_link == 2:
            self.Ui.radioButton_hard_on.setChecked(True)
        else:
            self.Ui.radioButton_soft_off.setChecked(True)

        success_file_move = int(config.success_file_move)  # 成功后移动文件
        if success_file_move == 0:
            self.Ui.radioButton_succ_move_off.setChecked(True)
        else:
            self.Ui.radioButton_succ_move_on.setChecked(True)

        failed_file_move = int(config.failed_file_move)  # 失败后移动文件
        if failed_file_move == 0:
            self.Ui.radioButton_fail_move_off.setChecked(True)
        else:
            self.Ui.radioButton_fail_move_on.setChecked(True)

        success_file_rename = int(config.success_file_rename)  # 成功后重命名文件
        if success_file_rename == 0:
            self.Ui.radioButton_succ_rename_off.setChecked(True)
        else:
            self.Ui.radioButton_succ_rename_on.setChecked(True)

        del_empty_folder = int(config.del_empty_folder)  # 结束后删除空文件夹
        if del_empty_folder == 0:
            self.Ui.radioButton_del_empty_folder_off.setChecked(True)
        else:
            self.Ui.radioButton_del_empty_folder_on.setChecked(True)

        show_poster = int(config.show_poster)  # 显示封面
        if show_poster == 0:
            self.Ui.checkBox_cover.setChecked(False)
        else:
            self.Ui.checkBox_cover.setChecked(True)
        # endregion

        # region file_download
        download_files = config.download_files  # 下载文件
        # region download_files
        self.Ui.checkBox_download_poster.setChecked('poster' in download_files)
        self.Ui.checkBox_download_thumb.setChecked('thumb' in download_files)
        self.Ui.checkBox_download_fanart.setChecked(',fanart' in download_files)
        self.Ui.checkBox_download_extrafanart.setChecked('extrafanart,' in download_files)
        self.Ui.checkBox_download_trailer.setChecked('trailer,' in download_files)
        self.Ui.checkBox_download_nfo.setChecked('nfo' in download_files)
        self.Ui.checkBox_extras.setChecked('extrafanart_extras' in download_files)
        self.Ui.checkBox_download_extrafanart_copy.setChecked('extrafanart_copy' in download_files)
        self.Ui.checkBox_theme_videos.setChecked('theme_videos' in download_files)
        self.Ui.checkBox_ignore_pic_fail.setChecked('ignore_pic_fail' in download_files)
        self.Ui.checkBox_ignore_youma.setChecked('ignore_youma' in download_files)
        self.Ui.checkBox_ignore_wuma.setChecked('ignore_wuma' in download_files)
        self.Ui.checkBox_ignore_fc2.setChecked('ignore_fc2' in download_files)
        self.Ui.checkBox_ignore_guochan.setChecked('ignore_guochan' in download_files)
        self.Ui.checkBox_ignore_size.setChecked('ignore_size' in download_files)
        # endregion

        keep_files = config.keep_files  # 保留文件
        # region keep_files
        self.Ui.checkBox_old_poster.setChecked('poster' in keep_files)
        self.Ui.checkBox_old_thumb.setChecked('thumb' in keep_files)
        self.Ui.checkBox_old_fanart.setChecked(',fanart' in keep_files)
        self.Ui.checkBox_old_extrafanart.setChecked('extrafanart,' in keep_files)
        self.Ui.checkBox_old_trailer.setChecked('trailer' in keep_files)
        self.Ui.checkBox_old_nfo.setChecked('nfo' in keep_files)
        self.Ui.checkBox_old_extrafanart_copy.setChecked('extrafanart_copy' in keep_files)
        self.Ui.checkBox_old_theme_videos.setChecked('theme_videos' in keep_files)
        # endregion

        download_hd_pics = config.download_hd_pics  # 下载高清图片
        # region download_hd_pics
        if read_version < 20230310:
            download_hd_pics += 'amazon,official,'
        self.Ui.checkBox_hd_poster.setChecked('poster' in download_hd_pics)
        self.Ui.checkBox_hd_thumb.setChecked('thumb' in download_hd_pics)
        self.Ui.checkBox_amazon_big_pic.setChecked('amazon' in download_hd_pics)
        self.Ui.checkBox_official_big_pic.setChecked('official' in download_hd_pics)
        self.Ui.checkBox_google_big_pic.setChecked('google' in download_hd_pics)
        if 'goo_only' in download_hd_pics:
            self.Ui.radioButton_google_only.setChecked(True)
        else:
            self.Ui.radioButton_google_first.setChecked(True)
        # endregion

        self.Ui.lineEdit_google_used.setText(str(config.google_used))  # Google下载词
        google_exclude = str(config.google_exclude)  # Google过滤词
        self.Ui.lineEdit_google_exclude.setText(google_exclude)
        # endregion

        # region Name_Rule
        self.Ui.lineEdit_dir_name.setText(str(config.folder_name))  # 视频目录命名
        self.Ui.lineEdit_local_name.setText(str(config.naming_file))  # 视频文件名命名（本地文件）
        self.Ui.lineEdit_media_name.setText(str(config.naming_media))  # emby视频标题（nfo文件）
        self.Ui.lineEdit_prevent_char.setText(str(config.prevent_char))  # 防屏蔽字符

        fields_rule = config.fields_rule  # 字段命名规则
        # region fields_rule
        if read_version < 20230317:
            fields_rule += 'del_char,'
        if 'del_actor' in fields_rule:  # 去除标题后的演员名
            self.Ui.checkBox_title_del_actor.setChecked(True)
        else:
            self.Ui.checkBox_title_del_actor.setChecked(False)
        if 'del_char' in fields_rule:  # 演员去除括号
            self.Ui.checkBox_actor_del_char.setChecked(True)
        else:
            self.Ui.checkBox_actor_del_char.setChecked(False)
        if 'fc2_seller' in fields_rule:  # FC2 演员名
            self.Ui.checkBox_actor_fc2_seller.setChecked(True)
        else:
            self.Ui.checkBox_actor_fc2_seller.setChecked(False)
        if 'del_num' in fields_rule:  # 素人番号删除前缀数字
            self.Ui.checkBox_number_del_num.setChecked(True)
        else:
            self.Ui.checkBox_number_del_num.setChecked(False)
        # endregion

        self.Ui.lineEdit_actor_no_name.setText(str(config.actor_no_name))  # 字段命名规则-未知演员
        self.Ui.lineEdit_release_rule.setText(str(config.release_rule))  # 字段命名规则-发行日期
        folder_name_max = config.folder_name_max  # 长度命名规则-目录
        if folder_name_max <= 0 or folder_name_max > 255:
            folder_name_max = 60
        self.Ui.lineEdit_folder_name_max.setText(str(folder_name_max))
        file_name_max = config.file_name_max  # 长度命名规则-文件名
        if file_name_max <= 0 or file_name_max > 255:
            file_name_max = 60
        self.Ui.lineEdit_file_name_max.setText(str(file_name_max))
        self.Ui.lineEdit_actor_name_max.setText(str(config.actor_name_max))
        self.Ui.lineEdit_actor_name_more.setText(str(config.actor_name_more))  # 长度命名规则-演员名更多
        self.Ui.lineEdit_suffix_sort.setText(str(config.suffix_sort))
        self.Ui.lineEdit_umr_style.setText(str(config.umr_style))  # 版本命名规则-无码破解版
        self.Ui.lineEdit_leak_style.setText(str(config.leak_style))  # 版本命名规则-无码流出版
        self.Ui.lineEdit_wuma_style.setText(str(config.wuma_style))  # 版本命名规则-无码版
        self.Ui.lineEdit_youma_style.setText(str(config.youma_style))  # 版本命名规则-有码版
        show_moword = config.show_moword
        if 'folder' in show_moword:  # 显示版本命名字符-视频目录名
            self.Ui.checkBox_foldername_mosaic.setChecked(True)
        else:
            self.Ui.checkBox_foldername_mosaic.setChecked(False)
        if 'file' in show_moword:  # 显示版本命名字符-视频文件名
            self.Ui.checkBox_filename_mosaic.setChecked(True)
        else:
            self.Ui.checkBox_filename_mosaic.setChecked(False)
        show_4k = config.show_4k
        if 'folder' in show_4k:  # 显示4k
            self.Ui.checkBox_foldername_4k.setChecked(True)
        else:
            self.Ui.checkBox_foldername_4k.setChecked(False)
        if 'file' in show_4k:  # 显示4k
            self.Ui.checkBox_filename_4k.setChecked(True)
        else:
            self.Ui.checkBox_filename_4k.setChecked(False)

        cd_name = int(config.cd_name)  # 分集命名规则
        if cd_name == 0:
            self.Ui.radioButton_cd_part_lower.setChecked(True)
        elif cd_name == 1:
            self.Ui.radioButton_cd_part_upper.setChecked(True)
        else:
            self.Ui.radioButton_cd_part_digital.setChecked(True)

        cd_char = config.cd_char
        # region cd_char
        if read_version < 20230321:
            cd_char += ',underline,'
        self.Ui.checkBox_cd_part_a.setChecked('letter' in cd_char)  # 允许分集识别字母
        self.Ui.checkBox_cd_part_c.setChecked('letter' in cd_char)
        self.Ui.checkBox_cd_part_c.setChecked('endc' in cd_char)
        self.Ui.checkBox_cd_part_01.setChecked('digital' in cd_char)  # 允许分集识别数字
        self.Ui.checkBox_cd_part_1_xxx.setChecked('middle_number' in cd_char)
        self.Ui.checkBox_cd_part_underline.setChecked('underline' in cd_char)  # 下划线分隔符
        self.Ui.checkBox_cd_part_space.setChecked('space' in cd_char)
        self.Ui.checkBox_cd_part_point.setChecked('point' in cd_char)
        # endregion

        pic_name = int(config.pic_name)  # 图片命名规则
        if pic_name == 0:
            self.Ui.radioButton_pic_with_filename.setChecked(True)
        else:
            self.Ui.radioButton_pic_no_filename.setChecked(True)

        trailer_name = int(config.trailer_name)  # 预告片命名规则
        if trailer_name == 0:
            self.Ui.radioButton_trailer_with_filename.setChecked(True)
        else:
            self.Ui.radioButton_trailer_no_filename.setChecked(True)
        hd_name = config.hd_name  # 画质命名规则
        if hd_name == 'height':
            self.Ui.radioButton_definition_height.setChecked(True)
        else:
            self.Ui.radioButton_definition_hd.setChecked(True)
        hd_get = config.hd_get  # 分辨率获取方式
        if hd_get == 'video':
            self.Ui.radioButton_videosize_video.setChecked(True)
        elif hd_get == 'path':
            self.Ui.radioButton_videosize_path.setChecked(True)
        else:
            self.Ui.radioButton_videosize_none.setChecked(True)
        # endregion

        # region 字幕
        self.Ui.lineEdit_cnword_char.setText(str(config.cnword_char))  # 中文字幕判断字符
        self.Ui.lineEdit_cnword_style.setText(str(config.cnword_style).strip('^'))  # 中文字幕字符样式
        self.Ui.checkBox_foldername.setChecked(config.folder_cnword != 'off')  # 显示中文字幕字符-视频目录名
        self.Ui.checkBox_filename.setChecked(config.file_cnword != 'off')  # 显示中文字幕字符-视频文件名
        self.Ui.lineEdit_sub_folder.setText(convert_path(config.subtitle_folder))  # 外挂字幕文件目录
        if str(config.subtitle_add) == 'on':  # 自动添加字幕
            self.Ui.radioButton_add_sub_on.setChecked(True)
        else:
            self.Ui.radioButton_add_sub_off.setChecked(True)
        self.Ui.checkBox_sub_add_chs.setChecked(config.subtitle_add_chs == 'on')  # 字幕文件名添加.chs后缀
        self.Ui.checkBox_sub_rescrape.setChecked(config.subtitle_add_rescrape == 'on')  # 重新刮削新添加字幕的视频
        # endregion

        # region emby
        try:
            server_type = config.server_type  # 服务器类型
            if 'emby' in server_type:
                self.Ui.radioButton_server_emby.setChecked(True)
            else:
                self.Ui.radioButton_server_jellyfin.setChecked(True)
        except:
            self.Ui.radioButton_server_emby.setChecked(True)
        self.Ui.lineEdit_emby_url.setText(str(config.emby_url))  # emby地址
        self.Ui.lineEdit_api_key.setText(str(config.api_key))  # emby密钥
        self.Ui.lineEdit_user_id.setText(str(config.user_id))  # emby用户ID

        emby_on = config.emby_on
        # region emby_on
        if 'actor_info_zh_cn' in emby_on:
            self.Ui.radioButton_actor_info_zh_cn.setChecked(True)
        elif 'actor_info_zh_tw' in emby_on:
            self.Ui.radioButton_actor_info_zh_tw.setChecked(True)
        else:
            self.Ui.radioButton_actor_info_ja.setChecked(True)
        self.Ui.checkBox_actor_info_translate.setChecked('actor_info_translate' in emby_on)
        if 'actor_info_all' in emby_on:
            self.Ui.radioButton_actor_info_all.setChecked(True)
        else:
            self.Ui.radioButton_actor_info_miss.setChecked(True)
        self.Ui.checkBox_actor_info_photo.setChecked('actor_info_photo' in emby_on)
        if 'actor_photo_local' in emby_on:
            self.Ui.radioButton_actor_photo_local.setChecked(True)
        else:
            self.Ui.radioButton_actor_photo_net.setChecked(True)
        self.Ui.checkBox_actor_photo_ne_backdrop.setChecked('graphis_backdrop' in emby_on)
        self.Ui.checkBox_actor_photo_ne_face.setChecked('graphis_face' in emby_on)
        self.Ui.checkBox_actor_photo_ne_new.setChecked('graphis_new' in emby_on)
        if 'actor_photo_all' in emby_on:
            self.Ui.radioButton_actor_photo_all.setChecked(True)
        else:
            self.Ui.radioButton_actor_photo_miss.setChecked(True)
        self.Ui.checkBox_actor_photo_auto.setChecked('actor_photo_auto' in emby_on)
        self.Ui.checkBox_actor_pic_replace.setChecked('actor_replace' in emby_on)
        # endregion

        self.Ui.checkBox_actor_photo_kodi.setChecked(config.actor_photo_kodi_auto)
        self.Ui.lineEdit_net_actor_photo.setText(config.gfriends_github)  # 网络头像库 gfriends 项目地址
        self.Ui.lineEdit_actor_photo_folder.setText(convert_path(config.actor_photo_folder))  # 本地头像目录
        self.Ui.lineEdit_actor_db_path.setText(convert_path(config.info_database_path))  # 演员数据库路径
        self.Ui.checkBox_actor_db.setChecked(config.use_database == 1)  # 演员数据库
        # endregion

        # region mark
        poster_mark = int(config.poster_mark)  # 封面图加水印
        if poster_mark == 0:
            self.Ui.checkBox_poster_mark.setChecked(False)
        else:
            self.Ui.checkBox_poster_mark.setChecked(True)

        thumb_mark = int(config.thumb_mark)  # 缩略图加水印
        if thumb_mark == 0:
            self.Ui.checkBox_thumb_mark.setChecked(False)
        else:
            self.Ui.checkBox_thumb_mark.setChecked(True)

        fanart_mark = int(config.fanart_mark)  # 艺术图加水印
        if fanart_mark == 0:
            self.Ui.checkBox_fanart_mark.setChecked(False)
        else:
            self.Ui.checkBox_fanart_mark.setChecked(True)

        mark_size = int(config.mark_size)  # 水印大小
        self.Ui.horizontalSlider_mark_size.setValue(mark_size)
        self.Ui.lcdNumber_mark_size.display(mark_size)

        mark_type = config.mark_type  # 水印类型
        # region mark_type
        self.Ui.checkBox_sub.setChecked('sub' in mark_type)
        self.Ui.checkBox_censored.setChecked('youma' in mark_type)
        self.Ui.checkBox_umr.setChecked('umr' in mark_type)
        self.Ui.checkBox_leak.setChecked('leak' in mark_type)
        self.Ui.checkBox_uncensored.setChecked('uncensored' in mark_type)
        self.Ui.checkBox_hd.setChecked('hd' in mark_type)
        # endregion

        mark_fixed = config.mark_fixed  # 水印位置是否固定
        if mark_fixed == 'off':
            self.Ui.radioButton_not_fixed_position.setChecked(True)
        elif mark_fixed == 'corner':
            self.Ui.radioButton_fixed_corner.setChecked(True)
        else:
            self.Ui.radioButton_fixed_position.setChecked(True)

        mark_pos = config.mark_pos  # 首个水印位置
        if mark_pos == 'top_left':
            self.Ui.radioButton_top_left.setChecked(True)
        elif mark_pos == 'top_right':
            self.Ui.radioButton_top_right.setChecked(True)
        elif mark_pos == 'bottom_left':
            self.Ui.radioButton_bottom_left.setChecked(True)
        elif mark_pos == 'bottom_right':
            self.Ui.radioButton_bottom_right.setChecked(True)
        else:
            self.Ui.radioButton_top_left.setChecked(True)

        mark_pos_corner = config.mark_pos_corner  # 固定一个位置
        if mark_pos_corner == 'top_left':
            self.Ui.radioButton_top_left_corner.setChecked(True)
        elif mark_pos_corner == 'top_right':
            self.Ui.radioButton_top_right_corner.setChecked(True)
        elif mark_pos_corner == 'bottom_left':
            self.Ui.radioButton_bottom_left_corner.setChecked(True)
        elif mark_pos_corner == 'bottom_right':
            self.Ui.radioButton_bottom_right_corner.setChecked(True)
        else:
            self.Ui.radioButton_top_left_corner.setChecked(True)

        mark_pos_hd = config.mark_pos_hd  # hd水印位置
        if mark_pos_hd == 'top_left':
            self.Ui.radioButton_top_left_hd.setChecked(True)
        elif mark_pos_hd == 'top_right':
            self.Ui.radioButton_top_right_hd.setChecked(True)
        elif mark_pos_hd == 'bottom_left':
            self.Ui.radioButton_bottom_left_hd.setChecked(True)
        elif mark_pos_hd == 'bottom_right':
            self.Ui.radioButton_bottom_right_hd.setChecked(True)
        else:
            self.Ui.radioButton_bottom_right_hd.setChecked(True)

        mark_pos_sub = config.mark_pos_sub  # 字幕水印位置
        if mark_pos_sub == 'top_left':
            self.Ui.radioButton_top_left_sub.setChecked(True)
        elif mark_pos_sub == 'top_right':
            self.Ui.radioButton_top_right_sub.setChecked(True)
        elif mark_pos_sub == 'bottom_left':
            self.Ui.radioButton_bottom_left_sub.setChecked(True)
        elif mark_pos_sub == 'bottom_right':
            self.Ui.radioButton_bottom_right_sub.setChecked(True)
        else:
            self.Ui.radioButton_top_left_sub.setChecked(True)

        mark_pos_mosaic = config.mark_pos_mosaic  # 马赛克水印位置
        if mark_pos_mosaic == 'top_left':
            self.Ui.radioButton_top_left_mosaic.setChecked(True)
        elif mark_pos_mosaic == 'top_right':
            self.Ui.radioButton_top_right_mosaic.setChecked(True)
        elif mark_pos_mosaic == 'bottom_left':
            self.Ui.radioButton_bottom_left_mosaic.setChecked(True)
        elif mark_pos_mosaic == 'bottom_right':
            self.Ui.radioButton_bottom_right_mosaic.setChecked(True)
        else:
            self.Ui.radioButton_top_right_mosaic.setChecked(True)
        # endregion

        # region network
        proxy_type = config.type  # 代理类型
        if proxy_type == 'no':
            self.Ui.radioButton_proxy_nouse.setChecked(True)
        elif proxy_type == 'http':
            self.Ui.radioButton_proxy_http.setChecked(True)
        elif proxy_type == 'socks5':
            self.Ui.radioButton_proxy_socks5.setChecked(True)
        else:
            self.Ui.radioButton_proxy_nouse.setChecked(True)

        self.Ui.lineEdit_proxy.setText(str(config.proxy))  # 代理地址

        timeout = int(config.timeout)  # 超时时间
        self.Ui.horizontalSlider_timeout.setValue(timeout)
        self.Ui.lcdNumber_timeout.display(timeout)

        retry_count = int(config.retry)  # 重试次数
        self.Ui.horizontalSlider_retry.setValue(retry_count)
        self.Ui.lcdNumber_retry.display(retry_count)

        custom_website_name = self.Ui.comboBox_custom_website.currentText()
        self.Ui.lineEdit_custom_website.setText(getattr(config, f"{custom_website_name}_website", ""))  # 自定义网站

        self.Ui.lineEdit_api_token_theporndb.setText(convert_path(config.theporndb_api_token))  # api token
        self.set_javdb_cookie.emit(config.javdb)  # javdb cookie
        self.set_javbus_cookie.emit(config.javbus)  # javbus cookie
        # endregion

        # region other
        self.Ui.lineEdit_config_folder.setText(convert_path(config.folder))  # 配置文件目录
        rest_count = int(config.rest_count)  # 间歇刮削文件数量
        if rest_count == 0:
            rest_count = 1
        self.Ui.lineEdit_rest_count.setText(str(rest_count))

        rest_time = config.rest_time  # 间歇刮削间隔时间
        self.Ui.lineEdit_rest_time.setText(str(rest_time))
        h, m, s = re.findall(r'^(\d+):(\d+):(\d+)$', rest_time)[0]  # 换算（秒）
        Flags.rest_time_convert = int(h) * 3600 + int(m) * 60 + int(s)

        timed_interval = config.timed_interval  # 循环任务间隔时间
        self.Ui.lineEdit_timed_interval.setText(timed_interval)
        h, m, s = re.findall(r'^(\d+):(\d+):(\d+)$', timed_interval)[0]  # 换算（毫秒）
        timed_interval_convert = (int(h) * 3600 + int(m) * 60 + int(s)) * 1000
        self.timer_scrape.stop()
        self.statement = int(config.statement)  # 间歇刮削间隔时间

        self.Ui.checkBox_show_web_log.setChecked(config.show_web_log == 'on')  # 显示字段刮削过程
        self.Ui.checkBox_show_from_log.setChecked(config.show_from_log == 'on')  # 显示字段来源信息
        self.Ui.checkBox_show_data_log.setChecked(config.show_data_log == 'on')  # 显示字段内容信息
        if config.save_log == 'off':  # 保存日志
            self.Ui.radioButton_log_off.setChecked(True)
        else:
            self.Ui.radioButton_log_on.setChecked(True)
        if config.update_check == 'off':  # 检查更新
            self.Ui.radioButton_update_off.setChecked(True)
        else:
            self.Ui.radioButton_update_on.setChecked(True)

        self.Ui.lineEdit_local_library_path.setText(convert_path(config.local_library))  # 本地资源库
        self.Ui.lineEdit_actors_name.setText(str(config.actors_name))  # 演员名
        self.Ui.lineEdit_netdisk_path.setText(convert_path(config.netdisk_path))  # 网盘目录
        self.Ui.lineEdit_localdisk_path.setText(convert_path(config.localdisk_path))  # 本地磁盘目录
        self.Ui.checkBox_hide_window_title.setChecked(config.window_title == 'hide')  # 窗口标题栏
        # endregion

        # region switch_on
        switch_on = config.switch_on
        if read_version < 20230404:
            switch_on += 'ipv4_only,'
        self.Ui.checkBox_auto_start.setChecked('auto_start' in switch_on)
        self.Ui.checkBox_auto_exit.setChecked('auto_exit' in switch_on)
        self.Ui.checkBox_rest_scrape.setChecked('rest_scrape' in switch_on)

        if 'timed_scrape' in switch_on:
            self.Ui.checkBox_timed_scrape.setChecked(True)
            self.timer_scrape.start(timed_interval_convert)
        else:
            self.Ui.checkBox_timed_scrape.setChecked(False)
        self.Ui.checkBox_remain_task.setChecked('remain_task' in switch_on)
        self.Ui.checkBox_show_dialog_exit.setChecked('show_dialog_exit' in switch_on)
        self.Ui.checkBox_show_dialog_stop_scrape.setChecked('show_dialog_stop_scrape' in switch_on)
        self.Ui.checkBox_dark_mode.setChecked('dark_mode' in switch_on)
        self.dark_mode = 'dark_mode' in switch_on
        self.Ui.checkBox_copy_netdisk_nfo.setChecked('copy_netdisk_nfo' in switch_on)
        self.show_hide_logs('show_logs' in switch_on)
        self.Ui.checkBox_net_ipv4_only.setChecked('ipv4_only' in switch_on)
        if 'qt_dialog' in switch_on:
            self.Ui.checkBox_dialog_qt.setChecked(True)
            self.options = QFileDialog.DontUseNativeDialog
        else:
            self.Ui.checkBox_dialog_qt.setChecked(False)
            self.options = QFileDialog.Options()
        self.Ui.checkBox_theporndb_hash.setChecked('theporndb_no_hash' in switch_on)
        self.Ui.checkBox_sortmode_delpic.setChecked('sort_del' in switch_on)
        if 'hide_close' in switch_on:
            self.Ui.radioButton_hide_close.setChecked(True)
        elif 'hide_mini' in switch_on:
            self.Ui.radioButton_hide_mini.setChecked(True)
        else:
            self.Ui.radioButton_hide_none.setChecked(True)
        if config.is_windows:
            self.Ui.checkBox_hide_dock_icon.setEnabled(False)
            self.Ui.checkBox_hide_menu_icon.setEnabled(False)
            try:
                self.tray_icon.show()
            except:
                self.Init_QSystemTrayIcon()
                if not mdcx_config:
                    self.tray_icon.showMessage(f"MDCx {self.localversion}", u'配置写入失败！所在目录没有读写权限！', QIcon(resources.icon_ico), 3000)
            if 'passthrough' in switch_on:
                self.Ui.checkBox_highdpi_passthrough.setChecked(True)
                if not os.path.isfile('highdpi_passthrough'):
                    open('highdpi_passthrough', 'w').close()
            else:
                self.Ui.checkBox_highdpi_passthrough.setChecked(False)
                if os.path.isfile('highdpi_passthrough'):
                    delete_file('highdpi_passthrough')
        else:
            self.Ui.checkBox_highdpi_passthrough.setEnabled(False)
            if 'hide_menu' in switch_on:
                self.Ui.checkBox_hide_menu_icon.setChecked(True)
                try:
                    if hasattr(self, 'tray_icon'):
                        self.tray_icon.hide()
                except:
                    signal.show_traceback_log(traceback.format_exc())
            else:
                self.Ui.checkBox_hide_menu_icon.setChecked(False)
                try:
                    self.tray_icon.show()
                except:
                    self.Init_QSystemTrayIcon()
                    if not mdcx_config:
                        self.tray_icon.showMessage(f"MDCx {self.localversion}", u'配置写入失败！所在目录没有读写权限！', QIcon(resources.icon_ico), 3000)

            # TODO macOS上运行pyinstaller打包的程序，这个处理方式有问题
            try:
                hide_dock_flag_file = 'resources/Img/1'
                # 在macOS上测试（普通用户），发现`hide_dock_flag_file`路径有几种情况（以下用xxx代替该相对路径）：
                # 1.如果通过Finder进入/Applications/MDCx.app/Contents/MacOS/，然后运行MDCx，路径是/Users/username/xxx
                # 2.如果通过终端进入/Applications/MDCx.app/Contents/MacOS/，然后运行MDCx，路径是/Applications/MDCx.app/Contents/MacOS/xxx
                # 3.正常运行MDCx，路径是/xxx，也就是在根目录下
                # 1和2都有权限写入文件，但不能持久化（升级后会丢失），3是没有写入权限。
                # 暂时的处理：屏蔽异常，避免程序崩溃
                # 考虑的处理：不使用标记文件，只使用config
                # 相关文件：main.py
                if 'hide_dock' in switch_on:
                    self.Ui.checkBox_hide_dock_icon.setChecked(True)
                    if not os.path.isfile(hide_dock_flag_file):
                        open(hide_dock_flag_file, 'w').close()
                else:
                    self.Ui.checkBox_hide_dock_icon.setChecked(False)
                    if os.path.isfile(hide_dock_flag_file):
                        delete_file(hide_dock_flag_file)
            except Exception as e:
                signal.show_traceback_log(f'hide_dock_flag_file: {os.path.realpath(hide_dock_flag_file)}')
                signal.show_traceback_log(traceback.format_exc())
        # endregion

        self.Ui.checkBox_create_link.setChecked(config.auto_link)

        # ======================================================================================END
        self.checkBox_i_agree_clean_clicked()  # 根据是否同意改变清理按钮状态
        try:
            scrape_like_text = Flags.scrape_like_text
            if config.scrape_like == 'single':
                scrape_like_text += f" · {config.website_single}"
            if config.soft_link == 1:
                scrape_like_text += " · 软连接开"
            elif config.soft_link == 2:
                scrape_like_text += " · 硬连接开"
            signal.show_log_text(f' 🛠 当前配置：{config.path} 加载完成！\n '
                                 f'📂 程序目录：{get_main_path()} \n '
                                 f'📂 刮削目录：{get_movie_path_setting()[0]} \n '
                                 f'💠 刮削模式：{Flags.main_mode_text} · {scrape_like_text} \n '
                                 f'🖥️ 系统信息：{platform.platform()} \n '
                                 f'🐰 软件版本：{self.localversion} \n')
        except:
            signal.show_traceback_log(traceback.format_exc())
        try:
            check_proxyChange()  # 更新代理信息
            self._windows_auto_adjust()  # 界面自动调整
        except:
            signal.show_traceback_log(traceback.format_exc())
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()
        try:
            self.set_label_file_path.emit('🎈 当前刮削路径: \n %s' % get_movie_path_setting()[0])  # 主界面右上角显示提示信息
        except:
            signal.show_traceback_log(traceback.format_exc())
    else:  # ini不存在，重新创建
        signal.show_log_text('Create config file: %s ' % config_path)
        self.pushButton_init_config_clicked()
