import os
import platform
import re
import traceback
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog

from mdcx.config.extend import get_movie_path_setting
from mdcx.config.manager import config, get_new_str, manager
from mdcx.config.resources import resources
from mdcx.consts import IS_WINDOWS
from mdcx.controllers.main_window.bind_utils import set_checkboxes, set_radio_buttons
from mdcx.models.flags import Flags
from mdcx.signals import signal
from mdcx.utils import convert_path
from mdcx.utils.file import delete_file_sync

if TYPE_CHECKING:
    from mdcx.controllers.main_window.main_window import MyMAinWindow


def load_config(self: "MyMAinWindow"):
    """
    读取配置文件并绑定到 UI 组件
    """
    errors = manager.read_config()
    if errors:
        signal.show_log_text(f"⚠️ 读取配置文件出错:\n\t{errors}\n💡 这不会阻止程序运行, 无效配置将使用默认值\n")
    config.init()
    config_folder = manager.data_folder
    config_file = manager.file
    config_path = manager.path

    # 检测配置目录权限
    mdcx_config = True
    if not os.access(config_folder, os.W_OK) or not os.access(config_folder, os.R_OK):
        mdcx_config = False

    if os.path.exists(config_path):
        # ======================================================================================获取配置文件夹中的配置文件列表
        all_files = os.listdir(config_folder)
        all_config_files = [i for i in all_files if ".ini" in i]
        all_config_files.sort()
        self.Ui.comboBox_change_config.clear()
        self.Ui.comboBox_change_config.addItems(all_config_files)
        if config_file in all_config_files:
            self.Ui.comboBox_change_config.setCurrentIndex(all_config_files.index(config_file))
        else:
            self.Ui.comboBox_change_config.setCurrentIndex(all_config_files.index("config.ini"))

        read_version = config.version
        # region media
        # 视频目录
        self.Ui.lineEdit_movie_path.setText(convert_path(config.media_path))
        # 软链接目录
        self.Ui.lineEdit_movie_softlink_path.setText(convert_path(config.softlink_path))
        # 成功目录
        self.Ui.lineEdit_success.setText(convert_path(config.success_output_folder))
        # 失败目录
        self.Ui.lineEdit_fail.setText(convert_path(config.failed_output_folder))
        # 剧照副本目录
        self.Ui.lineEdit_extrafanart_dir.setText(config.extrafanart_folder)
        # 视频类型
        self.Ui.lineEdit_movie_type.setText(config.media_type)
        # 字幕类型
        self.Ui.lineEdit_sub_type.setText(config.sub_type.replace(".txt|", ""))
        # 不过滤文件、文件夹
        self.Ui.checkBox_scrape_softlink_path.setChecked(config.scrape_softlink_path)
        # endregion

        # region escape
        # 排除目录
        self.Ui.lineEdit_escape_dir.setText(config.folders)
        # 排除目录-工具页面
        self.Ui.lineEdit_escape_dir_move.setText(config.folders)
        # 多余字符串
        escape_string = config.string
        if read_version < 20230326:
            escape_string = "h_720," + escape_string
        self.Ui.lineEdit_escape_string.setText(escape_string)
        # 小文件
        self.Ui.lineEdit_escape_size.setText(str(config.file_size))
        # 不过滤文件、文件夹
        set_checkboxes(
            config.no_escape,
            (self.Ui.checkBox_no_escape_file, "no_skip_small_file"),
            (self.Ui.checkBox_no_escape_dir, "folder"),
            (self.Ui.checkBox_skip_success_file, "skip_success_file"),
            (self.Ui.checkBox_record_success_file, "record_success_file"),
            (self.Ui.checkBox_check_symlink, "check_symlink"),
            (self.Ui.checkBox_check_symlink_definition, "symlink_definition"),
        )
        # endregion

        # region clean
        # 清理扩展名等于
        self.Ui.lineEdit_clean_file_ext.setText(config.clean_ext)
        # 清理文件名等于
        self.Ui.lineEdit_clean_file_name.setText(config.clean_name)
        # 清理文件名包含
        self.Ui.lineEdit_clean_file_contains.setText(config.clean_contains)
        # 清理文件大小
        self.Ui.lineEdit_clean_file_size.setText(str(config.clean_size))
        # 不清理扩展名
        self.Ui.lineEdit_clean_excluded_file_ext.setText(config.clean_ignore_ext)
        # 不清理文件名包含
        self.Ui.lineEdit_clean_excluded_file_contains.setText(config.clean_ignore_contains)
        # region clean_enable
        set_checkboxes(
            config.clean_enable,
            (self.Ui.checkBox_clean_file_ext, "clean_ext"),
            (self.Ui.checkBox_clean_file_name, "clean_name"),
            (self.Ui.checkBox_clean_file_contains, "clean_contains"),
            (self.Ui.checkBox_clean_file_size, "clean_size"),
            (self.Ui.checkBox_clean_excluded_file_ext, "clean_ignore_ext"),
            (self.Ui.checkBox_clean_excluded_file_contains, "clean_ignore_contains"),
            (self.Ui.checkBox_i_understand_clean, "i_know"),
            (self.Ui.checkBox_i_agree_clean, "i_agree"),
            (self.Ui.checkBox_auto_clean, "auto_clean"),
        )
        # endregion
        # endregion

        # region website
        AllItems = [self.Ui.comboBox_website_all.itemText(i) for i in range(self.Ui.comboBox_website_all.count())]
        # 指定单个刮削网站
        self.Ui.comboBox_website_all.setCurrentIndex(AllItems.index(config.website_single))
        # 有码番号刮削网站
        self.Ui.lineEdit_website_youma.setText(get_new_str(config.website_youma))
        # 无码番号刮削网站
        self.Ui.lineEdit_website_wuma.setText(get_new_str((config.website_wuma)))
        # 素人番号刮削网站
        self.Ui.lineEdit_website_suren.setText(get_new_str((config.website_suren)))
        # FC2番号刮削网站
        self.Ui.lineEdit_website_fc2.setText(get_new_str(config.website_fc2))
        # 欧美番号刮削网站
        temp_oumei = str(config.website_oumei)
        if "theporndb" not in temp_oumei:
            temp_oumei = "theporndb," + temp_oumei
        website_oumei = get_new_str(temp_oumei)
        self.Ui.lineEdit_website_oumei.setText(website_oumei)
        # 国产番号刮削网站
        self.Ui.lineEdit_website_guochan.setText(get_new_str(config.website_guochan))

        # 刮削偏好
        scrape_like = config.scrape_like
        if "speed" in scrape_like:
            Flags.scrape_like_text = "速度优先"
        elif "single" in scrape_like:
            Flags.scrape_like_text = "指定网站"
        else:
            Flags.scrape_like_text = "字段优先"

        set_radio_buttons(
            "speed" if "speed" in scrape_like else "single" if "single" in scrape_like else "info",
            (self.Ui.radioButton_scrape_speed, "speed"),
            (self.Ui.radioButton_scrape_single, "single"),
            (self.Ui.radioButton_scrape_info, "info"),
            default=self.Ui.radioButton_scrape_info,
        )

        website_set = config.website_set
        self.Ui.checkBox_use_official_data.setChecked("official," in website_set)

        # 标题字段网站优先级
        title_website = get_new_str(config.title_website)
        if read_version < 20230405:
            title_website = "theporndb,mgstage," + title_website
        self.Ui.lineEdit_title_website.setText(title_website)
        # 中文标题字段网站优先级
        self.Ui.lineEdit_title_zh_website.setText(get_new_str(config.title_zh_website))
        # 标题字段排除网站
        self.Ui.lineEdit_title_website_exclude.setText(get_new_str(config.title_website_exclude))
        # 标题语言
        set_radio_buttons(
            config.title_language,
            (self.Ui.radioButton_title_zh_cn, "zh_cn"),
            (self.Ui.radioButton_title_zh_tw, "zh_tw"),
            default=self.Ui.radioButton_title_jp,
        )

        # 增强翻译-sehua
        self.Ui.checkBox_title_sehua.setChecked(config.title_sehua)
        # 增强翻译-yesjav
        self.Ui.checkBox_title_yesjav.setChecked(config.title_yesjav)
        # 标题增强翻译-使用翻译引擎
        self.Ui.checkBox_title_translate.setChecked(config.title_translate)
        # 增强翻译-优先sehua
        self.Ui.checkBox_title_sehua_2.setChecked(config.title_sehua_zh)

        # 简介字段网站优先级
        self.Ui.lineEdit_outline_website.setText(get_new_str(config.outline_website))
        # 中文简介字段网站优先级
        self.Ui.lineEdit_outline_zh_website.setText(get_new_str(config.outline_zh_website))
        # 简介字段排除网站
        self.Ui.lineEdit_outline_website_exclude.setText(get_new_str(config.outline_website_exclude))
        # 简介语言
        set_radio_buttons(
            config.outline_language,
            (self.Ui.radioButton_outline_zh_cn, "zh_cn"),
            (self.Ui.radioButton_outline_zh_tw, "zh_tw"),
            (self.Ui.radioButton_outline_jp, "jp"),
            default=self.Ui.radioButton_outline_zh_cn,
        )
        # 简介-使用翻译引擎
        self.Ui.checkBox_outline_translate.setChecked(config.outline_translate)
        # 简介-显示翻译来源、双语显示
        outline_show = config.outline_show
        self.Ui.checkBox_show_translate_from.setChecked("show_from" in outline_show)
        set_radio_buttons(
            "zh_jp" if "show_zh_jp" in outline_show else "jp_zh" if "show_jp_zh" in outline_show else "one",
            (self.Ui.radioButton_trans_show_zh_jp, "zh_jp"),
            (self.Ui.radioButton_trans_show_jp_zh, "jp_zh"),
            (self.Ui.radioButton_trans_show_one, "one"),
            default=self.Ui.radioButton_trans_show_one,
        )
        # 演员字段网站优先级
        self.Ui.lineEdit_actor_website.setText(get_new_str(config.actor_website))
        # 演员字段排除网站
        self.Ui.lineEdit_actor_website_exclude.setText(get_new_str(config.actor_website_exclude))
        # 演员映射表输出
        set_radio_buttons(
            config.actor_language,
            (self.Ui.radioButton_actor_zh_cn, "zh_cn"),
            (self.Ui.radioButton_actor_zh_tw, "zh_tw"),
            (self.Ui.radioButton_actor_jp, "jp"),
            default=self.Ui.radioButton_actor_zh_cn,
        )
        # 演员-使用真实名字
        self.Ui.checkBox_actor_realname.setChecked(config.actor_realname)
        # 演员-使用演员映射表
        self.Ui.checkBox_actor_translate.setChecked(config.actor_translate)
        # 标签字段网站优先级
        self.Ui.lineEdit_tag_website.setText(get_new_str(config.tag_website))
        # 标签字段排除网站
        self.Ui.lineEdit_tag_website_exclude.setText(get_new_str(config.tag_website_exclude))
        # 标签字段语言
        set_radio_buttons(
            config.tag_language,
            (self.Ui.radioButton_tag_zh_cn, "zh_cn"),
            (self.Ui.radioButton_tag_zh_tw, "zh_tw"),
            (self.Ui.radioButton_tag_jp, "jp"),
            default=self.Ui.radioButton_tag_zh_cn,
        )

        # 标签-使用信息映射表
        self.Ui.checkBox_tag_translate.setChecked(config.tag_translate)

        # 写入标签字段的信息
        tag_include = config.tag_include
        # region tag_include
        set_checkboxes(
            tag_include,
            (self.Ui.checkBox_tag_actor, "actor"),
            (self.Ui.checkBox_tag_letters, "letters"),
            (self.Ui.checkBox_tag_series, "series"),
            (self.Ui.checkBox_tag_studio, "studio"),
            (self.Ui.checkBox_tag_publisher, "publisher"),
            (self.Ui.checkBox_tag_cnword, "cnword"),
            (self.Ui.checkBox_tag_mosaic, "mosaic"),
            (self.Ui.checkBox_tag_definition, "definition"),
        )
        # endregion

        # 系列字段网站优先级
        self.Ui.lineEdit_series_website.setText(get_new_str(config.series_website))
        # 系列字段排除网站
        self.Ui.lineEdit_series_website_exclude.setText(get_new_str(config.series_website_exclude))
        # 系列字段语言
        set_radio_buttons(
            config.series_language,
            (self.Ui.radioButton_series_zh_cn, "zh_cn"),
            (self.Ui.radioButton_series_zh_tw, "zh_tw"),
            (self.Ui.radioButton_series_jp, "jp"),
            default=self.Ui.radioButton_series_zh_cn,
        )
        # 系列-使用信息映射表
        self.Ui.checkBox_series_translate.setChecked(config.series_translate)
        # 片商字段网站优先级
        self.Ui.lineEdit_studio_website.setText(get_new_str(config.studio_website))
        # 片商字段排除网站
        self.Ui.lineEdit_studio_website_exclude.setText(get_new_str(config.studio_website_exclude))
        # 片商字段语言
        set_radio_buttons(
            config.studio_language,
            (self.Ui.radioButton_studio_zh_cn, "zh_cn"),
            (self.Ui.radioButton_studio_zh_tw, "zh_tw"),
            (self.Ui.radioButton_studio_jp, "jp"),
            default=self.Ui.radioButton_studio_zh_cn,
        )
        # 片商-使用信息映射表
        self.Ui.checkBox_studio_translate.setChecked(config.studio_translate)
        # 想看人数
        self.Ui.lineEdit_wanted_website.setText(get_new_str(config.wanted_website, wanted=True))
        # 发行字段网站优先级
        self.Ui.lineEdit_publisher_website.setText(get_new_str(config.publisher_website))
        # 发行字段排除网站
        self.Ui.lineEdit_publisher_website_exclude.setText(get_new_str(config.publisher_website_exclude))
        # 发行字段语言
        set_radio_buttons(
            config.publisher_language,
            (self.Ui.radioButton_publisher_zh_cn, "zh_cn"),
            (self.Ui.radioButton_publisher_zh_tw, "zh_tw"),
            (self.Ui.radioButton_publisher_jp, "jp"),
            default=self.Ui.radioButton_publisher_zh_cn,
        )
        # 发行-使用信息映射表
        self.Ui.checkBox_publisher_translate.setChecked(config.publisher_translate)
        # 导演字段网站优先级
        self.Ui.lineEdit_director_website.setText(get_new_str(config.director_website))
        # 导演字段排除网站
        self.Ui.lineEdit_director_website_exclude.setText(get_new_str(config.director_website_exclude))
        # 导演字段语言
        set_radio_buttons(
            config.director_language,
            (self.Ui.radioButton_director_zh_cn, "zh_cn"),
            (self.Ui.radioButton_director_zh_tw, "zh_tw"),
            (self.Ui.radioButton_director_jp, "jp"),
            default=self.Ui.radioButton_director_zh_cn,
        )
        # 导演-使用信息映射表
        self.Ui.checkBox_director_translate.setChecked(config.director_translate)
        # 封面字段网站优先级
        self.Ui.lineEdit_poster_website.setText(get_new_str(config.poster_website))
        # 封面字段排除网站
        self.Ui.lineEdit_poster_website_exclude.setText(get_new_str(config.poster_website_exclude))
        # 背景字段网站优先级
        self.Ui.lineEdit_thumb_website.setText(get_new_str(config.thumb_website))
        # 背景字段排除网站
        self.Ui.lineEdit_thumb_website_exclude.setText(get_new_str(config.thumb_website_exclude))
        # 剧照字段网站优先级
        self.Ui.lineEdit_extrafanart_website.setText(get_new_str(config.extrafanart_website))
        # 剧照字段排除网站
        self.Ui.lineEdit_extrafanart_website_exclude.setText(get_new_str(config.extrafanart_website_exclude))
        # 评分字段网站优先级
        self.Ui.lineEdit_score_website.setText(get_new_str(config.score_website))
        # 评分字段排除网站
        self.Ui.lineEdit_score_website_exclude.setText(get_new_str(config.score_website_exclude))
        # 发行日期字段网站优先级
        self.Ui.lineEdit_release_website.setText(get_new_str(config.release_website))
        # 发行日期字段排除网站
        self.Ui.lineEdit_release_website_exclude.setText(get_new_str(config.release_website_exclude))
        # 时长字段网站优先级
        self.Ui.lineEdit_runtime_website.setText(get_new_str(config.runtime_website))
        # 时长字段排除网站
        self.Ui.lineEdit_runtime_website_exclude.setText(get_new_str(config.runtime_website_exclude))
        # 预告片字段网站优先级
        self.Ui.lineEdit_trailer_website.setText(get_new_str(config.trailer_website))
        # 预告片字段排除网站
        self.Ui.lineEdit_trailer_website_exclude.setText(get_new_str(config.trailer_website_exclude))
        # 刮削设置
        whole_fields = config.whole_fields
        none_fields = config.none_fields

        def set_field_radio_buttons(field_name, more_radio, none_radio, listed_radio):
            """设置字段的三个单选按钮状态"""
            if field_name in whole_fields:
                more_radio.setChecked(True)
            elif field_name in none_fields:
                none_radio.setChecked(True)
            else:
                listed_radio.setChecked(True)

        # region whole_fields
        set_field_radio_buttons(
            "outline",
            self.Ui.radioButton_outline_more,
            self.Ui.radioButton_outline_none,
            self.Ui.radioButton_outline_listed,
        )
        set_field_radio_buttons(
            "actor", self.Ui.radioButton_actor_more, self.Ui.radioButton_actor_none, self.Ui.radioButton_actor_listed
        )
        set_field_radio_buttons(
            "thumb", self.Ui.radioButton_thumb_more, self.Ui.radioButton_thumb_none, self.Ui.radioButton_thumb_listed
        )
        set_field_radio_buttons(
            "poster",
            self.Ui.radioButton_poster_more,
            self.Ui.radioButton_poster_none,
            self.Ui.radioButton_poster_listed,
        )
        set_field_radio_buttons(
            "extrafanart",
            self.Ui.radioButton_extrafanart_more,
            self.Ui.radioButton_extrafanart_none,
            self.Ui.radioButton_extrafanart_listed,
        )
        set_field_radio_buttons(
            "trailer",
            self.Ui.radioButton_trailer_more,
            self.Ui.radioButton_trailer_none,
            self.Ui.radioButton_trailer_listed,
        )
        set_field_radio_buttons(
            "tag", self.Ui.radioButton_tag_more, self.Ui.radioButton_tag_none, self.Ui.radioButton_tag_listed
        )
        set_field_radio_buttons(
            "release",
            self.Ui.radioButton_release_more,
            self.Ui.radioButton_release_none,
            self.Ui.radioButton_release_listed,
        )
        set_field_radio_buttons(
            "runtime",
            self.Ui.radioButton_runtime_more,
            self.Ui.radioButton_runtime_none,
            self.Ui.radioButton_runtime_listed,
        )
        set_field_radio_buttons(
            "score", self.Ui.radioButton_score_more, self.Ui.radioButton_score_none, self.Ui.radioButton_score_listed
        )
        set_field_radio_buttons(
            "director",
            self.Ui.radioButton_director_more,
            self.Ui.radioButton_director_none,
            self.Ui.radioButton_director_listed,
        )
        set_field_radio_buttons(
            "series",
            self.Ui.radioButton_series_more,
            self.Ui.radioButton_series_none,
            self.Ui.radioButton_series_listed,
        )
        set_field_radio_buttons(
            "studio",
            self.Ui.radioButton_studio_more,
            self.Ui.radioButton_studio_none,
            self.Ui.radioButton_studio_listed,
        )
        set_field_radio_buttons(
            "publisher",
            self.Ui.radioButton_publisher_more,
            self.Ui.radioButton_publisher_none,
            self.Ui.radioButton_publisher_listed,
        )

        if "wanted" in none_fields:
            self.Ui.radioButton_wanted_none.setChecked(True)
        else:
            self.Ui.radioButton_wanted_listed.setChecked(True)
        # endregion

        self.Ui.lineEdit_nfo_tagline.setText(config.nfo_tagline)
        self.Ui.lineEdit_nfo_tag_series.setText(config.nfo_tag_series)
        self.Ui.lineEdit_nfo_tag_studio.setText(config.nfo_tag_studio)
        self.Ui.lineEdit_nfo_tag_publisher.setText(config.nfo_tag_publisher)
        self.Ui.lineEdit_nfo_tag_actor.setText(config.nfo_tag_actor)
        self.Ui.lineEdit_nfo_tag_actor_contains.setText(config.nfo_tag_actor_contains)

        # 写入nfo的字段
        nfo_include_new = config.nfo_include_new
        # region nfo_include_new
        if read_version < 20230302:
            nfo_include_new = nfo_include_new.replace(",set,", ",series_set,")
            nfo_include_new += "sorttitle,originaltitle,outline,plot_,originalplot,website,"
            if "release" in nfo_include_new:
                nfo_include_new += "release_, releasedate,premiered,"
            if "mpaa," in nfo_include_new:
                nfo_include_new += "country,customrating,"
            if "studio," in nfo_include_new:
                nfo_include_new += "maker,"
            if "publisher," in nfo_include_new:
                nfo_include_new += "label,"

        set_checkboxes(
            nfo_include_new,
            (self.Ui.checkBox_nfo_sorttitle, "sorttitle,"),
            (self.Ui.checkBox_nfo_originaltitle, "originaltitle,"),
            (self.Ui.checkBox_nfo_title_cd, "title_cd,"),
            (self.Ui.checkBox_nfo_outline, "outline,"),
            (self.Ui.checkBox_nfo_plot, "plot_,"),
            (self.Ui.checkBox_nfo_originalplot, "originalplot,"),
            (self.Ui.checkBox_outline_cdata, "outline_no_cdata,"),
            (self.Ui.checkBox_nfo_release, "release_,"),
            (self.Ui.checkBox_nfo_relasedate, "releasedate,"),
            (self.Ui.checkBox_nfo_premiered, "premiered,"),
            (self.Ui.checkBox_nfo_country, "country,"),
            (self.Ui.checkBox_nfo_mpaa, "mpaa,"),
            (self.Ui.checkBox_nfo_customrating, "customrating,"),
            (self.Ui.checkBox_nfo_year, "year,"),
            (self.Ui.checkBox_nfo_runtime, "runtime,"),
            (self.Ui.checkBox_nfo_wanted, "wanted,"),
            (self.Ui.checkBox_nfo_score, "score,"),
            (self.Ui.checkBox_nfo_criticrating, "criticrating,"),
            (self.Ui.checkBox_nfo_actor, "actor,"),
            (self.Ui.checkBox_nfo_all_actor, "actor_all,"),
            (self.Ui.checkBox_nfo_director, "director,"),
            (self.Ui.checkBox_nfo_series, "series,"),
            (self.Ui.checkBox_nfo_tag, "tag,"),
            (self.Ui.checkBox_nfo_genre, "genre,"),
            (self.Ui.checkBox_nfo_actor_set, "actor_set,"),
            (self.Ui.checkBox_nfo_set, "series_set,"),
            (self.Ui.checkBox_nfo_studio, "studio,"),
            (self.Ui.checkBox_nfo_maker, "maker,"),
            (self.Ui.checkBox_nfo_publisher, "publisher,"),
            (self.Ui.checkBox_nfo_label, "label,"),
            (self.Ui.checkBox_nfo_poster, "poster,"),
            (self.Ui.checkBox_nfo_cover, "cover,"),
            (self.Ui.checkBox_nfo_trailer, "trailer,"),
            (self.Ui.checkBox_nfo_website, "website,"),
        )
        # endregion

        # 翻译引擎
        translate_by = config.translate_by
        set_checkboxes(
            translate_by,
            (self.Ui.checkBox_youdao, "youdao"),
            (self.Ui.checkBox_google, "google"),
            (self.Ui.checkBox_deepl, "deepl"),
            (self.Ui.checkBox_llm, "llm"),
        )
        Flags.translate_by_list = translate_by.strip(",").split(",") if translate_by.strip(",") else []

        # deepl_key
        self.Ui.lineEdit_deepl_key.setText(config.deepl_key)

        # llm config
        self.Ui.lineEdit_llm_url.setText(config.llm_url)
        self.Ui.lineEdit_llm_key.setText(config.llm_key)
        self.Ui.lineEdit_llm_model.setText(config.llm_model)
        self.Ui.textEdit_llm_prompt.setText(config.llm_prompt)
        self.Ui.doubleSpinBox_llm_max_req_sec.setValue(config.llm_max_req_sec)
        self.Ui.spinBox_llm_max_try.setValue(config.llm_max_try)
        self.Ui.doubleSpinBox_llm_temperature.setValue(config.llm_temperature)
        # endregion

        # region common
        # 线程数量
        self.Ui.horizontalSlider_thread.setValue(config.thread_number)
        self.Ui.lcdNumber_thread.display(config.thread_number)
        # 线程延时
        self.Ui.horizontalSlider_thread_time.setValue(config.thread_time)
        self.Ui.lcdNumber_thread_time.display(config.thread_time)
        # javdb 延时
        self.Ui.horizontalSlider_javdb_time.setValue(config.javdb_time)
        self.Ui.lcdNumber_javdb_time.display(config.javdb_time)

        # 刮削模式
        main_mode = config.main_mode
        mode_mapping = {
            1: ("common", "正常模式"),
            2: ("sort", "整理模式"),
            3: ("update", "更新模式"),
            4: ("read", "读取模式"),
        }
        mode_key, mode_text = mode_mapping.get(main_mode, ("common", "正常模式"))
        Flags.main_mode_text = mode_text
        set_radio_buttons(
            mode_key,
            (self.Ui.radioButton_mode_common, "common"),
            (self.Ui.radioButton_mode_sort, "sort"),
            (self.Ui.radioButton_mode_update, "update"),
            (self.Ui.radioButton_mode_read, "read"),
            default=self.Ui.radioButton_mode_common,
        )

        # 有nfo，是否执行更新模式
        read_mode = config.read_mode
        # region read_mode
        set_checkboxes(
            read_mode,
            (self.Ui.checkBox_read_has_nfo_update, "has_nfo_update"),
            (self.Ui.checkBox_read_download_file_again, "read_download_again"),
            (self.Ui.checkBox_read_update_nfo, "read_update_nfo"),
            (self.Ui.checkBox_read_no_nfo_scrape, "no_nfo_scrape"),
        )
        # endregion

        # 更新模式
        self.Ui.checkBox_update_a.setChecked(False)
        update_mode = config.update_mode

        # 处理 abc 模式的特殊情况
        if update_mode == "abc":
            self.Ui.radioButton_update_b_c.setChecked(True)
            self.Ui.checkBox_update_a.setChecked(True)
        else:
            set_radio_buttons(
                update_mode,
                (self.Ui.radioButton_update_c, "c"),
                (self.Ui.radioButton_update_b_c, "bc"),
                (self.Ui.radioButton_update_d_c, "d"),
                default=self.Ui.radioButton_update_c,
            )

        # 更新模式 - a 目录
        self.Ui.lineEdit_update_a_folder.setText(config.update_a_folder)
        # 更新模式 - b 目录
        self.Ui.lineEdit_update_b_folder.setText(config.update_b_folder)
        # 更新模式 - d 目录
        self.Ui.lineEdit_update_d_folder.setText(config.update_d_folder)
        # 更新模式 - c 文件名
        self.Ui.lineEdit_update_c_filetemplate.setText(config.update_c_filetemplate)
        # 更新模式 - emby视频标题
        self.Ui.lineEdit_update_titletemplate.setText(config.update_titletemplate)

        # 软链接
        set_radio_buttons(
            config.soft_link,
            (self.Ui.radioButton_soft_on, 1),
            (self.Ui.radioButton_hard_on, 2),
            (self.Ui.radioButton_soft_off, 0),
            default=self.Ui.radioButton_soft_off,
        )
        # 成功后移动文件
        set_radio_buttons(
            config.success_file_move,
            (self.Ui.radioButton_succ_move_on, True),
            (self.Ui.radioButton_succ_move_off, False),
            default=self.Ui.radioButton_succ_move_off,
        )
        # 失败后移动文件
        set_radio_buttons(
            config.failed_file_move,
            (self.Ui.radioButton_fail_move_on, True),
            (self.Ui.radioButton_fail_move_off, False),
            default=self.Ui.radioButton_fail_move_off,
        )
        # 成功后重命名文件
        set_radio_buttons(
            config.success_file_rename,
            (self.Ui.radioButton_succ_rename_on, True),
            (self.Ui.radioButton_succ_rename_off, False),
            default=self.Ui.radioButton_succ_rename_off,
        )
        # 结束后删除空文件夹
        set_radio_buttons(
            config.del_empty_folder,
            (self.Ui.radioButton_del_empty_folder_on, True),
            (self.Ui.radioButton_del_empty_folder_off, False),
            default=self.Ui.radioButton_del_empty_folder_off,
        )

        # 显示封面
        self.Ui.checkBox_cover.setChecked(config.show_poster)
        # endregion

        # region file_download
        # 下载文件
        set_checkboxes(
            config.download_files,
            (self.Ui.checkBox_download_poster, "poster"),
            (self.Ui.checkBox_download_thumb, "thumb"),
            (self.Ui.checkBox_download_fanart, ",fanart"),
            (self.Ui.checkBox_download_extrafanart, "extrafanart,"),
            (self.Ui.checkBox_download_trailer, "trailer,"),
            (self.Ui.checkBox_download_nfo, "nfo"),
            (self.Ui.checkBox_extras, "extrafanart_extras"),
            (self.Ui.checkBox_download_extrafanart_copy, "extrafanart_copy"),
            (self.Ui.checkBox_theme_videos, "theme_videos"),
            (self.Ui.checkBox_ignore_pic_fail, "ignore_pic_fail"),
            (self.Ui.checkBox_ignore_youma, "ignore_youma"),
            (self.Ui.checkBox_ignore_wuma, "ignore_wuma"),
            (self.Ui.checkBox_ignore_fc2, "ignore_fc2"),
            (self.Ui.checkBox_ignore_guochan, "ignore_guochan"),
            (self.Ui.checkBox_ignore_size, "ignore_size"),
        )
        # 保留文件
        set_checkboxes(
            config.keep_files,
            (self.Ui.checkBox_old_poster, "poster"),
            (self.Ui.checkBox_old_thumb, "thumb"),
            (self.Ui.checkBox_old_fanart, ",fanart"),
            (self.Ui.checkBox_old_extrafanart, "extrafanart,"),
            (self.Ui.checkBox_old_trailer, "trailer"),
            (self.Ui.checkBox_old_nfo, "nfo"),
            (self.Ui.checkBox_old_extrafanart_copy, "extrafanart_copy"),
            (self.Ui.checkBox_old_theme_videos, "theme_videos"),
        )

        # 下载高清图片
        download_hd_pics = config.download_hd_pics
        # region download_hd_pics
        if read_version < 20230310:
            download_hd_pics += "amazon,official,"
        set_checkboxes(
            download_hd_pics,
            (self.Ui.checkBox_hd_poster, "poster"),
            (self.Ui.checkBox_hd_thumb, "thumb"),
            (self.Ui.checkBox_amazon_big_pic, "amazon"),
            (self.Ui.checkBox_official_big_pic, "official"),
            (self.Ui.checkBox_google_big_pic, "google"),
        )
        set_radio_buttons(
            "only" if "goo_only" in download_hd_pics else "first",
            (self.Ui.radioButton_google_only, "only"),
            (self.Ui.radioButton_google_first, "first"),
            default=self.Ui.radioButton_google_first,
        )
        # endregion

        # Google下载词
        self.Ui.lineEdit_google_used.setText(config.google_used)
        # Google过滤词
        self.Ui.lineEdit_google_exclude.setText(config.google_exclude)
        # endregion

        # region Name_Rule
        # 视频目录命名
        self.Ui.lineEdit_dir_name.setText(config.folder_name)
        # 视频文件名命名（本地文件）
        self.Ui.lineEdit_local_name.setText(config.naming_file)
        # emby视频标题（nfo文件）
        self.Ui.lineEdit_media_name.setText(config.naming_media)
        # 防屏蔽字符
        self.Ui.lineEdit_prevent_char.setText(config.prevent_char)

        # region fields_rule
        # 字段命名规则
        fields_rule = config.fields_rule
        if read_version < 20230317:
            fields_rule += "del_char,"

        set_checkboxes(
            fields_rule,
            # 去除标题后的演员名
            (self.Ui.checkBox_title_del_actor, "del_actor"),
            # 演员去除括号
            (self.Ui.checkBox_actor_del_char, "del_char"),
            # FC2 演员名
            (self.Ui.checkBox_actor_fc2_seller, "fc2_seller"),
            # 素人番号删除前缀数字
            (self.Ui.checkBox_number_del_num, "del_num"),
        )
        # endregion

        # 字段命名规则-未知演员
        self.Ui.lineEdit_actor_no_name.setText(config.actor_no_name)
        # 字段命名规则-发行日期
        self.Ui.lineEdit_release_rule.setText(config.release_rule)
        # 长度命名规则-目录
        folder_name_max = config.folder_name_max
        if folder_name_max <= 0 or folder_name_max > 255:
            folder_name_max = 60
        self.Ui.lineEdit_folder_name_max.setText(str(folder_name_max))
        # 长度命名规则-文件名
        file_name_max = config.file_name_max
        if file_name_max <= 0 or file_name_max > 255:
            file_name_max = 60
        self.Ui.lineEdit_file_name_max.setText(str(file_name_max))
        self.Ui.lineEdit_actor_name_max.setText(str(config.actor_name_max))
        # 长度命名规则-演员名更多
        self.Ui.lineEdit_actor_name_more.setText(config.actor_name_more)
        self.Ui.lineEdit_suffix_sort.setText(config.suffix_sort)
        # 版本命名规则-无码破解版
        self.Ui.lineEdit_umr_style.setText(config.umr_style)
        # 版本命名规则-无码流出版
        self.Ui.lineEdit_leak_style.setText(config.leak_style)
        # 版本命名规则-无码版
        self.Ui.lineEdit_wuma_style.setText(config.wuma_style)
        # 版本命名规则-有码版
        self.Ui.lineEdit_youma_style.setText(config.youma_style)
        set_checkboxes(
            config.show_moword,
            # 显示版本命名字符-视频目录名
            (self.Ui.checkBox_foldername_mosaic, "folder"),
            # 显示版本命名字符-视频文件名
            (self.Ui.checkBox_filename_mosaic, "file"),
        )
        set_checkboxes(
            config.show_4k,
            # 显示4k-视频目录名
            (self.Ui.checkBox_foldername_4k, "folder"),
            # 显示4k-视频文件名
            (self.Ui.checkBox_filename_4k, "file"),
        )
        # 分集命名规则
        set_radio_buttons(
            config.cd_name,
            (self.Ui.radioButton_cd_part_lower, 0),
            (self.Ui.radioButton_cd_part_upper, 1),
            default=self.Ui.radioButton_cd_part_digital,
        )

        cd_char = config.cd_char
        # region cd_char
        if read_version < 20230321:
            cd_char += ",underline,"

        set_checkboxes(
            cd_char,
            # 允许分集识别字母
            (self.Ui.checkBox_cd_part_a, "letter"),
            # 允许分集识别字母（重复）
            (self.Ui.checkBox_cd_part_c, "letter"),
            # 允许分集识别数字
            (self.Ui.checkBox_cd_part_01, "digital"),
            (self.Ui.checkBox_cd_part_1_xxx, "middle_number"),
            # 下划线分隔符
            (self.Ui.checkBox_cd_part_underline, "underline"),
            (self.Ui.checkBox_cd_part_space, "space"),
            (self.Ui.checkBox_cd_part_point, "point"),
        )
        # 特殊处理 endc
        self.Ui.checkBox_cd_part_c.setChecked("endc" in cd_char)
        # endregion

        # 图片命名是否包含视频名
        set_radio_buttons(
            config.pic_simple_name,
            (self.Ui.radioButton_pic_with_filename, False),
            default=self.Ui.radioButton_pic_no_filename,
        )
        # 预告片命名是否包含视频名
        set_radio_buttons(
            config.trailer_simple_name,
            (self.Ui.radioButton_trailer_with_filename, False),
            default=self.Ui.radioButton_trailer_no_filename,
        )
        # 画质命名规则
        set_radio_buttons(
            config.hd_name,
            (self.Ui.radioButton_definition_height, "height"),
            default=self.Ui.radioButton_definition_hd,
        )
        # 分辨率获取方式
        set_radio_buttons(
            config.hd_get,
            (self.Ui.radioButton_videosize_video, "video"),
            (self.Ui.radioButton_videosize_path, "path"),
            default=self.Ui.radioButton_videosize_none,
        )
        # endregion

        # region 字幕
        # 中文字幕判断字符
        self.Ui.lineEdit_cnword_char.setText(config.cnword_char)
        # 中文字幕字符样式
        self.Ui.lineEdit_cnword_style.setText(config.cnword_style.strip("^"))
        # 显示中文字幕字符-视频目录名
        self.Ui.checkBox_foldername.setChecked(config.folder_cnword)
        # 显示中文字幕字符-视频文件名
        self.Ui.checkBox_filename.setChecked(config.file_cnword)
        # 外挂字幕文件目录
        self.Ui.lineEdit_sub_folder.setText(convert_path(config.subtitle_folder))
        # 自动添加字幕
        set_radio_buttons(
            config.subtitle_add,
            (self.Ui.radioButton_add_sub_on, True),
            default=self.Ui.radioButton_add_sub_off,
        )
        # 字幕文件名添加.chs后缀
        self.Ui.checkBox_sub_add_chs.setChecked(config.subtitle_add_chs)
        # 重新刮削新添加字幕的视频
        self.Ui.checkBox_sub_rescrape.setChecked(config.subtitle_add_rescrape)
        # endregion

        # region emby
        # 服务器类型
        set_radio_buttons(
            "emby" if "emby" in config.server_type else "jellyfin",
            (self.Ui.radioButton_server_emby, "emby"),
            (self.Ui.radioButton_server_jellyfin, "jellyfin"),
            default=self.Ui.radioButton_server_emby,
        )
        # emby地址
        self.Ui.lineEdit_emby_url.setText(config.emby_url)
        # emby密钥
        self.Ui.lineEdit_api_key.setText(config.api_key)
        # emby用户ID
        self.Ui.lineEdit_user_id.setText(config.user_id)

        emby_on = config.emby_on
        set_radio_buttons(
            "zh_cn" if "actor_info_zh_cn" in emby_on else "zh_tw" if "actor_info_zh_tw" in emby_on else "ja",
            (self.Ui.radioButton_actor_info_zh_cn, "zh_cn"),
            (self.Ui.radioButton_actor_info_zh_tw, "zh_tw"),
            (self.Ui.radioButton_actor_info_ja, "ja"),
            default=self.Ui.radioButton_actor_info_ja,
        )
        set_checkboxes(
            emby_on,
            (self.Ui.checkBox_actor_info_translate, "actor_info_translate"),
            (self.Ui.checkBox_actor_info_photo, "actor_info_photo"),
            (self.Ui.checkBox_actor_photo_ne_backdrop, "graphis_backdrop"),
            (self.Ui.checkBox_actor_photo_ne_face, "graphis_face"),
            (self.Ui.checkBox_actor_photo_ne_new, "graphis_new"),
            (self.Ui.checkBox_actor_photo_auto, "actor_photo_auto"),
            (self.Ui.checkBox_actor_pic_replace, "actor_replace"),
        )
        set_radio_buttons(
            "all" if "actor_info_all" in emby_on else "miss",
            (self.Ui.radioButton_actor_info_all, "all"),
            (self.Ui.radioButton_actor_info_miss, "miss"),
            default=self.Ui.radioButton_actor_info_miss,
        )
        set_radio_buttons(
            "local" if "actor_photo_local" in emby_on else "net",
            (self.Ui.radioButton_actor_photo_local, "local"),
            (self.Ui.radioButton_actor_photo_net, "net"),
            default=self.Ui.radioButton_actor_photo_net,
        )
        set_radio_buttons(
            "all" if "actor_photo_all" in emby_on else "miss",
            (self.Ui.radioButton_actor_photo_all, "all"),
            (self.Ui.radioButton_actor_photo_miss, "miss"),
            default=self.Ui.radioButton_actor_photo_miss,
        )

        self.Ui.checkBox_actor_photo_kodi.setChecked(config.actor_photo_kodi_auto)
        # 网络头像库 gfriends 项目地址
        self.Ui.lineEdit_net_actor_photo.setText(config.gfriends_github)
        # 本地头像目录
        self.Ui.lineEdit_actor_photo_folder.setText(convert_path(config.actor_photo_folder))
        # 演员数据库路径
        self.Ui.lineEdit_actor_db_path.setText(convert_path(config.info_database_path))
        # 演员数据库
        self.Ui.checkBox_actor_db.setChecked(config.use_database == 1)
        # endregion

        # region mark
        # 水印设置
        # 封面图加水印
        self.Ui.checkBox_poster_mark.setChecked(config.poster_mark != 0)
        # 缩略图加水印
        self.Ui.checkBox_thumb_mark.setChecked(config.thumb_mark != 0)
        # 艺术图加水印
        self.Ui.checkBox_fanart_mark.setChecked(config.fanart_mark != 0)
        # 水印大小
        self.Ui.horizontalSlider_mark_size.setValue(int(config.mark_size))
        self.Ui.lcdNumber_mark_size.display(int(config.mark_size))

        # 启用的水印类型
        set_checkboxes(
            config.mark_type,
            (self.Ui.checkBox_sub, "sub"),
            (self.Ui.checkBox_censored, "youma"),
            (self.Ui.checkBox_umr, "umr"),
            (self.Ui.checkBox_leak, "leak"),
            (self.Ui.checkBox_uncensored, "uncensored"),
            (self.Ui.checkBox_hd, "hd"),
        )
        # 水印位置是否固定
        set_radio_buttons(
            config.mark_fixed,
            (self.Ui.radioButton_not_fixed_position, "not_fixed"),
            (self.Ui.radioButton_fixed_corner, "corner"),
            (self.Ui.radioButton_fixed_position, "fixed"),
            default=self.Ui.radioButton_fixed_position,
        )
        # 首个水印位置
        set_radio_buttons(
            config.mark_pos,
            (self.Ui.radioButton_top_left, "top_left"),
            (self.Ui.radioButton_top_right, "top_right"),
            (self.Ui.radioButton_bottom_left, "bottom_left"),
            (self.Ui.radioButton_bottom_right, "bottom_right"),
            default=self.Ui.radioButton_top_left,
        )
        # 固定一个位置
        set_radio_buttons(
            config.mark_pos_corner,
            (self.Ui.radioButton_top_left_corner, "top_left"),
            (self.Ui.radioButton_top_right_corner, "top_right"),
            (self.Ui.radioButton_bottom_left_corner, "bottom_left"),
            (self.Ui.radioButton_bottom_right_corner, "bottom_right"),
            default=self.Ui.radioButton_top_left_corner,
        )
        # 高清水印位置
        set_radio_buttons(
            config.mark_pos_hd,
            (self.Ui.radioButton_top_left_hd, "top_left"),
            (self.Ui.radioButton_top_right_hd, "top_right"),
            (self.Ui.radioButton_bottom_left_hd, "bottom_left"),
            (self.Ui.radioButton_bottom_right_hd, "bottom_right"),
            default=self.Ui.radioButton_bottom_right_hd,
        )
        # 字幕水印位置
        set_radio_buttons(
            config.mark_pos_sub,
            (self.Ui.radioButton_top_left_sub, "top_left"),
            (self.Ui.radioButton_top_right_sub, "top_right"),
            (self.Ui.radioButton_bottom_left_sub, "bottom_left"),
            (self.Ui.radioButton_bottom_right_sub, "bottom_right"),
            default=self.Ui.radioButton_top_left_sub,
        )
        # 马赛克水印位置
        set_radio_buttons(
            config.mark_pos_mosaic,
            (self.Ui.radioButton_top_left_mosaic, "top_left"),
            (self.Ui.radioButton_top_right_mosaic, "top_right"),
            (self.Ui.radioButton_bottom_left_mosaic, "bottom_left"),
            (self.Ui.radioButton_bottom_right_mosaic, "bottom_right"),
            default=self.Ui.radioButton_top_right_mosaic,
        )
        # endregion

        # region network
        # 代理类型
        set_radio_buttons(
            config.type,
            (self.Ui.radioButton_proxy_nouse, "no"),
            (self.Ui.radioButton_proxy_http, "http"),
            (self.Ui.radioButton_proxy_socks5, "socks5"),
            default=self.Ui.radioButton_proxy_nouse,
        )

        # 代理地址
        self.Ui.lineEdit_proxy.setText(config.proxy)
        # 超时时间
        self.Ui.horizontalSlider_timeout.setValue(int(config.timeout))
        self.Ui.lcdNumber_timeout.display(int(config.timeout))
        # 重试次数
        self.Ui.horizontalSlider_retry.setValue(int(config.retry))
        self.Ui.lcdNumber_retry.display(int(config.retry))

        custom_website_name = self.Ui.comboBox_custom_website.currentText()
        # 自定义网站
        self.Ui.lineEdit_custom_website.setText(getattr(config, f"{custom_website_name}_website", ""))

        self.Ui.lineEdit_api_token_theporndb.setText(convert_path(config.theporndb_api_token))
        # javdb cookie
        self.set_javdb_cookie.emit(config.javdb)
        # javbus cookie
        self.set_javbus_cookie.emit(config.javbus)
        # endregion

        # region other
        # 配置文件目录
        self.Ui.lineEdit_config_folder.setText(convert_path(manager.data_folder))
        # 间歇刮削文件数量
        rest_count = int(config.rest_count)
        if rest_count == 0:
            rest_count = 1
        self.Ui.lineEdit_rest_count.setText(str(rest_count))

        # 间歇刮削间隔时间
        self.Ui.lineEdit_rest_time.setText(config.rest_time)
        # 换算（秒）
        h, m, s = re.findall(r"^(\d+):(\d+):(\d+)$", config.rest_time)[0]
        Flags.rest_time_convert = int(h) * 3600 + int(m) * 60 + int(s)

        # 循环任务间隔时间
        self.Ui.lineEdit_timed_interval.setText(config.timed_interval)
        # 换算（毫秒）
        h, m, s = re.findall(r"^(\d+):(\d+):(\d+)$", config.timed_interval)[0]
        timed_interval_convert = (int(h) * 3600 + int(m) * 60 + int(s)) * 1000
        self.timer_scrape.stop()

        # 显示字段刮削过程
        self.Ui.checkBox_show_web_log.setChecked(config.show_web_log)
        # 显示字段来源信息
        self.Ui.checkBox_show_from_log.setChecked(config.show_from_log)
        # 显示字段内容信息
        self.Ui.checkBox_show_data_log.setChecked(config.show_data_log)
        # 保存日志
        set_radio_buttons(
            config.save_log,
            (self.Ui.radioButton_log_off, False),
            default=self.Ui.radioButton_log_on,
        )
        # 检查更新
        set_radio_buttons(
            config.update_check,
            (self.Ui.radioButton_update_off, False),
            default=self.Ui.radioButton_update_on,
        )

        # 本地资源库
        self.Ui.lineEdit_local_library_path.setText(convert_path(config.local_library))
        # 演员名
        self.Ui.lineEdit_actors_name.setText(config.actors_name)
        # 网盘目录
        self.Ui.lineEdit_netdisk_path.setText(convert_path(config.netdisk_path))
        # 本地磁盘目录
        self.Ui.lineEdit_localdisk_path.setText(convert_path(config.localdisk_path))
        # 窗口标题栏
        self.Ui.checkBox_hide_window_title.setChecked(config.window_title == "hide")
        # endregion

        # region switch_on
        switch_on = config.switch_on
        if read_version < 20230404:
            switch_on += "ipv4_only,"

        # 基础开关设置
        set_checkboxes(
            switch_on,
            (self.Ui.checkBox_auto_start, "auto_start"),
            (self.Ui.checkBox_auto_exit, "auto_exit"),
            (self.Ui.checkBox_rest_scrape, "rest_scrape"),
            (self.Ui.checkBox_remain_task, "remain_task"),
            (self.Ui.checkBox_show_dialog_exit, "show_dialog_exit"),
            (self.Ui.checkBox_show_dialog_stop_scrape, "show_dialog_stop_scrape"),
            (self.Ui.checkBox_dark_mode, "dark_mode"),
            (self.Ui.checkBox_copy_netdisk_nfo, "copy_netdisk_nfo"),
            (self.Ui.checkBox_net_ipv4_only, "ipv4_only"),
            (self.Ui.checkBox_theporndb_hash, "theporndb_no_hash"),
            (self.Ui.checkBox_sortmode_delpic, "sort_del"),
        )

        # 定时刮削设置
        if "timed_scrape" in switch_on:
            self.Ui.checkBox_timed_scrape.setChecked(True)
            self.timer_scrape.start(timed_interval_convert)
        else:
            self.Ui.checkBox_timed_scrape.setChecked(False)

        # 其他设置
        self.dark_mode = "dark_mode" in switch_on
        self.show_hide_logs("show_logs" in switch_on)

        # 隐藏窗口设置
        set_radio_buttons(
            "close" if "hide_close" in switch_on else "mini" if "hide_mini" in switch_on else "none",
            (self.Ui.radioButton_hide_close, "close"),
            (self.Ui.radioButton_hide_mini, "mini"),
            (self.Ui.radioButton_hide_none, "none"),
            default=self.Ui.radioButton_hide_none,
        )

        # Qt 对话框设置
        if "qt_dialog" in switch_on:
            self.Ui.checkBox_dialog_qt.setChecked(True)
            self.options = QFileDialog.DontUseNativeDialog
        else:
            self.Ui.checkBox_dialog_qt.setChecked(False)
            self.options = QFileDialog.Options()
        if IS_WINDOWS:
            self.Ui.checkBox_hide_dock_icon.setEnabled(False)
            self.Ui.checkBox_hide_menu_icon.setEnabled(False)
            try:
                self.tray_icon.show()
            except Exception:
                self.Init_QSystemTrayIcon()
                if not mdcx_config:
                    self.tray_icon.showMessage(
                        f"MDCx {self.localversion}",
                        "配置写入失败！所在目录没有读写权限！",
                        QIcon(resources.icon_ico),
                        3000,
                    )
            if "passthrough" in switch_on:
                self.Ui.checkBox_highdpi_passthrough.setChecked(True)
                if not os.path.isfile("highdpi_passthrough"):
                    open("highdpi_passthrough", "w").close()
            else:
                self.Ui.checkBox_highdpi_passthrough.setChecked(False)
                if os.path.isfile("highdpi_passthrough"):
                    delete_file_sync("highdpi_passthrough")
        else:
            self.Ui.checkBox_highdpi_passthrough.setEnabled(False)
            if "hide_menu" in switch_on:
                self.Ui.checkBox_hide_menu_icon.setChecked(True)
                try:
                    if hasattr(self, "tray_icon"):
                        self.tray_icon.hide()
                except Exception:
                    signal.show_traceback_log(traceback.format_exc())
            else:
                self.Ui.checkBox_hide_menu_icon.setChecked(False)
                try:
                    self.tray_icon.show()
                except Exception:
                    self.Init_QSystemTrayIcon()
                    if not mdcx_config:
                        self.tray_icon.showMessage(
                            f"MDCx {self.localversion}",
                            "配置写入失败！所在目录没有读写权限！",
                            QIcon(resources.icon_ico),
                            3000,
                        )
        # endregion

        self.Ui.checkBox_create_link.setChecked(config.auto_link)

        # ======================================================================================END
        # 根据是否同意改变清理按钮状态
        self.checkBox_i_agree_clean_clicked()
        try:
            scrape_like_text = Flags.scrape_like_text
            if config.scrape_like == "single":
                scrape_like_text += f" · {config.website_single}"
            if config.soft_link == 1:
                scrape_like_text += " · 软连接开"
            elif config.soft_link == 2:
                scrape_like_text += " · 硬连接开"
            signal.show_log_text(
                f" 🛠 当前配置：{manager.path} 加载完成！\n "
                f"📂 程序目录：{manager.data_folder} \n "
                f"📂 刮削目录：{get_movie_path_setting()[0]} \n "
                f"💠 刮削模式：{Flags.main_mode_text} · {scrape_like_text} \n "
                f"🖥️ 系统信息：{platform.platform()} \n "
                f"🐰 软件版本：{self.localversion} \n"
            )
        except Exception:
            signal.show_traceback_log(traceback.format_exc())
        try:
            # 界面自动调整
            self._windows_auto_adjust()
        except Exception:
            signal.show_traceback_log(traceback.format_exc())
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)  # type: ignore
        self.activateWindow()
        try:
            # 主界面右上角显示提示信息
            self.set_label_file_path.emit(f"🎈 当前刮削路径: \n {get_movie_path_setting()[0]}")
        except Exception:
            signal.show_traceback_log(traceback.format_exc())
    else:  # ini不存在，重新创建
        signal.show_log_text(f"Create config file: {config_path} ")
        self.pushButton_init_config_clicked()
