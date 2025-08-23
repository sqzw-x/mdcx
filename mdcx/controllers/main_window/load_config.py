import os
import platform
import traceback
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog

from mdcx.config.enums import (
    CDChar,
    CleanAction,
    DownloadableFile,
    EmbyAction,
    FieldRule,
    HDPicSource,
    KeepableFile,
    MarkType,
    NfoInclude,
    NoEscape,
    OutlineShow,
    ReadMode,
    Switch,
    TagInclude,
    Translator,
    Website,
)
from mdcx.config.extend import get_movie_path_setting
from mdcx.config.manager import manager
from mdcx.config.resources import resources
from mdcx.consts import IS_WINDOWS
from mdcx.controllers.main_window.bind_utils import set_checkboxes, set_radio_buttons
from mdcx.gen.field_enums import CrawlerResultFields
from mdcx.models.flags import Flags
from mdcx.signals import signal_qt
from mdcx.utils import convert_path
from mdcx.utils.file import delete_file_sync

if TYPE_CHECKING:
    from mdcx.controllers.main_window.main_window import MyMAinWindow


def load_config(self: "MyMAinWindow"):
    """
    读取配置文件并绑定到 UI 组件
    """
    field_mapping = {
        "title": CrawlerResultFields.TITLE,
        "originaltitle": CrawlerResultFields.ORIGINALTITLE,
        "outline": CrawlerResultFields.OUTLINE,
        "originalplot": CrawlerResultFields.ORIGINALPLOT,
        "actor": CrawlerResultFields.ACTORS,
        "all_actors": CrawlerResultFields.ALL_ACTORS,
        "tag": CrawlerResultFields.TAGS,
        "series": CrawlerResultFields.SERIES,
        "studio": CrawlerResultFields.STUDIO,
        "publisher": CrawlerResultFields.PUBLISHER,
        "director": CrawlerResultFields.DIRECTORS,
        "poster": CrawlerResultFields.POSTER,
        "thumb": CrawlerResultFields.THUMB,
        "extrafanart": CrawlerResultFields.EXTRAFANART,
        "score": CrawlerResultFields.SCORE,
        "release": CrawlerResultFields.RELEASE,
        "runtime": CrawlerResultFields.RUNTIME,
        "trailer": CrawlerResultFields.TRAILER,
        "wanted": CrawlerResultFields.WANTED,
    }

    errors = manager.load()
    if errors:
        signal_qt.show_log_text(
            f"⚠️ 读取配置文件出错:\n\t{'\n\t'.join(errors)}\n💡 这不会阻止程序运行, 无效配置将使用默认值\n"
        )
    config_folder = manager.data_folder
    config_file = manager.file
    config_path = manager.path

    # 检测配置目录权限
    mdcx_config = True
    if not os.access(config_folder, os.W_OK) or not os.access(config_folder, os.R_OK):
        mdcx_config = False

    if os.path.exists(config_path):
        # ======================================================================================获取配置文件夹中的配置文件列表
        all_config_files = manager.list_configs()
        all_config_files.sort()
        self.Ui.comboBox_change_config.clear()
        self.Ui.comboBox_change_config.addItems(all_config_files)
        if config_file in all_config_files:
            self.Ui.comboBox_change_config.setCurrentIndex(all_config_files.index(config_file))
        else:
            self.Ui.comboBox_change_config.setCurrentIndex(all_config_files.index("config.json"))

        # region media
        # 视频目录
        self.Ui.lineEdit_movie_path.setText(convert_path(manager.config.media_path))
        # 软链接目录
        self.Ui.lineEdit_movie_softlink_path.setText(convert_path(manager.config.softlink_path))
        # 成功目录
        self.Ui.lineEdit_success.setText(convert_path(manager.config.success_output_folder))
        # 失败目录
        self.Ui.lineEdit_fail.setText(convert_path(manager.config.failed_output_folder))
        # 剧照副本目录
        self.Ui.lineEdit_extrafanart_dir.setText(manager.config.extrafanart_folder)
        # 视频类型
        self.Ui.lineEdit_movie_type.setText("|".join(manager.config.media_type))
        # 字幕类型
        self.Ui.lineEdit_sub_type.setText("|".join(manager.config.sub_type).replace(".txt|", ""))
        # 不过滤文件、文件夹
        self.Ui.checkBox_scrape_softlink_path.setChecked(manager.config.scrape_softlink_path)
        # endregion

        # region escape
        # 排除目录
        self.Ui.lineEdit_escape_dir.setText(",".join(manager.config.folders))
        # 排除目录-工具页面
        self.Ui.lineEdit_escape_dir_move.setText(",".join(manager.config.folders))
        # 多余字符串
        escape_string = ",".join(manager.config.string)
        self.Ui.lineEdit_escape_string.setText(escape_string)
        # 小文件
        self.Ui.lineEdit_escape_size.setText(str(manager.config.file_size))
        # 不过滤文件、文件夹
        set_checkboxes(
            manager.config.no_escape,
            (self.Ui.checkBox_no_escape_file, NoEscape.NO_SKIP_SMALL_FILE),
            (self.Ui.checkBox_no_escape_dir, NoEscape.FOLDER),
            (self.Ui.checkBox_skip_success_file, NoEscape.SKIP_SUCCESS_FILE),
            (self.Ui.checkBox_record_success_file, NoEscape.RECORD_SUCCESS_FILE),
            (self.Ui.checkBox_check_symlink, NoEscape.CHECK_SYMLINK),
            (self.Ui.checkBox_check_symlink_definition, NoEscape.SYMLINK_DEFINITION),
        )
        # endregion

        # region clean
        # 清理扩展名等于
        self.Ui.lineEdit_clean_file_ext.setText("|".join(manager.config.clean_ext))
        # 清理文件名等于
        self.Ui.lineEdit_clean_file_name.setText("|".join(manager.config.clean_name))
        # 清理文件名包含
        self.Ui.lineEdit_clean_file_contains.setText("|".join(manager.config.clean_contains))
        # 清理文件大小
        self.Ui.lineEdit_clean_file_size.setText(str(manager.config.clean_size))
        # 不清理扩展名
        self.Ui.lineEdit_clean_excluded_file_ext.setText("|".join(manager.config.clean_ignore_ext))
        # 不清理文件名包含
        self.Ui.lineEdit_clean_excluded_file_contains.setText("|".join(manager.config.clean_ignore_contains))
        # region clean_enable
        set_checkboxes(
            manager.config.clean_enable,
            (self.Ui.checkBox_clean_file_ext, CleanAction.CLEAN_EXT),
            (self.Ui.checkBox_clean_file_name, CleanAction.CLEAN_NAME),
            (self.Ui.checkBox_clean_file_contains, CleanAction.CLEAN_CONTAINS),
            (self.Ui.checkBox_clean_file_size, CleanAction.CLEAN_SIZE),
            (self.Ui.checkBox_clean_excluded_file_ext, CleanAction.CLEAN_IGNORE_EXT),
            (self.Ui.checkBox_clean_excluded_file_contains, CleanAction.CLEAN_IGNORE_CONTAINS),
            (self.Ui.checkBox_i_understand_clean, CleanAction.I_KNOW),
            (self.Ui.checkBox_i_agree_clean, CleanAction.I_AGREE),
            (self.Ui.checkBox_auto_clean, CleanAction.AUTO_CLEAN),
        )
        # endregion
        # endregion

        # region website
        AllItems = [self.Ui.comboBox_website_all.itemText(i) for i in range(self.Ui.comboBox_website_all.count())]
        # 指定单个刮削网站
        self.Ui.comboBox_website_all.setCurrentIndex(AllItems.index(manager.config.website_single.value))
        # 有码番号刮削网站
        self.Ui.lineEdit_website_youma.setText(",".join([site.value for site in manager.config.website_youma]))
        # 无码番号刮削网站
        self.Ui.lineEdit_website_wuma.setText(",".join([site.value for site in manager.config.website_wuma]))
        # 素人番号刮削网站
        self.Ui.lineEdit_website_suren.setText(",".join([site.value for site in manager.config.website_suren]))
        # FC2番号刮削网站
        self.Ui.lineEdit_website_fc2.setText(",".join([site.value for site in manager.config.website_fc2]))
        # 欧美番号刮削网站
        temp_oumei = ",".join([site.value for site in manager.config.website_oumei])
        if "theporndb" not in temp_oumei:
            temp_oumei = "theporndb," + temp_oumei
        website_oumei = temp_oumei
        self.Ui.lineEdit_website_oumei.setText(website_oumei)
        # 国产番号刮削网站
        self.Ui.lineEdit_website_guochan.setText(",".join([site.value for site in manager.config.website_guochan]))

        # 刮削偏好
        scrape_like = manager.config.scrape_like
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

        # 标题字段配置
        title_field_config = manager.config.get_field_config(CrawlerResultFields.TITLE)
        title_website = ",".join(title_field_config.site_prority)
        self.Ui.lineEdit_title_website.setText(title_website)
        # 标题语言
        set_radio_buttons(
            title_field_config.language.value if title_field_config.language.value != "undefined" else "jp",
            (self.Ui.radioButton_title_zh_cn, "zh_cn"),
            (self.Ui.radioButton_title_zh_tw, "zh_tw"),
            default=self.Ui.radioButton_title_jp,
        )
        # originaltitle 字段配置
        sites = manager.config.get_field_config(CrawlerResultFields.ORIGINALTITLE).site_prority
        self.Ui.lineEdit_originaltitle_website.setText(",".join(sites))

        # 增强翻译-sehua
        self.Ui.checkBox_title_sehua.setChecked(manager.config.title_sehua)
        # 增强翻译-yesjav
        self.Ui.checkBox_title_yesjav.setChecked(manager.config.title_yesjav)
        # 标题增强翻译-使用翻译引擎
        self.Ui.checkBox_title_translate.setChecked(title_field_config.translate)
        # 增强翻译-优先sehua
        self.Ui.checkBox_title_sehua_2.setChecked(manager.config.title_sehua_zh)

        # 简介字段配置
        outline_field_config = manager.config.get_field_config(field_mapping["outline"])
        self.Ui.lineEdit_outline_website.setText(",".join(outline_field_config.site_prority))
        # originalplot 字段配置
        sites = manager.config.get_field_config(CrawlerResultFields.ORIGINALPLOT).site_prority
        self.Ui.lineEdit_originalplot_website.setText(",".join(sites))

        # 简介语言
        set_radio_buttons(
            outline_field_config.language.value if outline_field_config.language.value != "undefined" else "zh_cn",
            (self.Ui.radioButton_outline_zh_cn, "zh_cn"),
            (self.Ui.radioButton_outline_zh_tw, "zh_tw"),
            (self.Ui.radioButton_outline_jp, "jp"),
            default=self.Ui.radioButton_outline_zh_cn,
        )
        # 简介-使用翻译引擎
        self.Ui.checkBox_outline_translate.setChecked(outline_field_config.translate)
        # 简介-显示翻译来源、双语显示
        set_checkboxes(
            manager.config.outline_format,
            (self.Ui.checkBox_show_translate_from, OutlineShow.SHOW_FROM),
        )
        set_radio_buttons(
            "zh_jp"
            if OutlineShow.SHOW_ZH_JP in manager.config.outline_format
            else "jp_zh"
            if OutlineShow.SHOW_JP_ZH in manager.config.outline_format
            else "one",
            (self.Ui.radioButton_trans_show_zh_jp, "zh_jp"),
            (self.Ui.radioButton_trans_show_jp_zh, "jp_zh"),
            (self.Ui.radioButton_trans_show_one, "one"),
            default=self.Ui.radioButton_trans_show_one,
        )
        # 演员字段配置
        actor_field_config = manager.config.get_field_config(field_mapping["actor"])
        self.Ui.lineEdit_actors_website.setText(",".join([site.value for site in actor_field_config.site_prority]))
        # all_actors 字段配置
        self.Ui.lineEdit_all_actors_website.setText(
            ",".join(manager.config.get_field_config(CrawlerResultFields.ALL_ACTORS).site_prority)
        )
        # 演员映射表输出
        set_radio_buttons(
            actor_field_config.language.value if actor_field_config.language.value != "undefined" else "jp",
            (self.Ui.radioButton_actor_zh_cn, "zh_cn"),
            (self.Ui.radioButton_actor_zh_tw, "zh_tw"),
            (self.Ui.radioButton_actor_jp, "jp"),
            default=self.Ui.radioButton_actor_zh_cn,
        )
        # 演员-使用真实名字 (保留旧配置项)
        self.Ui.checkBox_actor_realname.setChecked(manager.config.actor_realname)
        # 演员-使用演员映射表
        self.Ui.checkBox_actor_translate.setChecked(actor_field_config.translate)

        # 标签字段配置
        tag_field_config = manager.config.get_field_config(field_mapping["tag"])
        self.Ui.lineEdit_tags_website.setText(",".join([site.value for site in tag_field_config.site_prority]))
        # 标签字段语言
        set_radio_buttons(
            tag_field_config.language.value if tag_field_config.language.value != "undefined" else "zh_cn",
            (self.Ui.radioButton_tag_zh_cn, "zh_cn"),
            (self.Ui.radioButton_tag_zh_tw, "zh_tw"),
            (self.Ui.radioButton_tag_jp, "jp"),
            default=self.Ui.radioButton_tag_zh_cn,
        )

        # 标签-使用信息映射表
        self.Ui.checkBox_tag_translate.setChecked(tag_field_config.translate)

        # 写入标签字段的信息
        # region tag_include
        set_checkboxes(
            manager.config.nfo_tag_include,
            (self.Ui.checkBox_tag_actor, TagInclude.ACTOR),
            (self.Ui.checkBox_tag_letters, TagInclude.LETTERS),
            (self.Ui.checkBox_tag_series, TagInclude.SERIES),
            (self.Ui.checkBox_tag_studio, TagInclude.STUDIO),
            (self.Ui.checkBox_tag_publisher, TagInclude.PUBLISHER),
            (self.Ui.checkBox_tag_cnword, TagInclude.CNWORD),
            (self.Ui.checkBox_tag_mosaic, TagInclude.MOSAIC),
            (self.Ui.checkBox_tag_definition, TagInclude.DEFINITION),
        )
        # endregion

        # 系列字段配置
        series_field_config = manager.config.get_field_config(field_mapping["series"])
        self.Ui.lineEdit_series_website.setText(",".join([site.value for site in series_field_config.site_prority]))

        # 系列字段语言
        set_radio_buttons(
            series_field_config.language.value if series_field_config.language.value != "undefined" else "zh_cn",
            (self.Ui.radioButton_series_zh_cn, "zh_cn"),
            (self.Ui.radioButton_series_zh_tw, "zh_tw"),
            (self.Ui.radioButton_series_jp, "jp"),
            default=self.Ui.radioButton_series_zh_cn,
        )
        # 系列-使用信息映射表
        self.Ui.checkBox_series_translate.setChecked(series_field_config.translate)

        # 工作室字段配置
        studio_field_config = manager.config.get_field_config(field_mapping["studio"])
        self.Ui.lineEdit_studio_website.setText(",".join([site.value for site in studio_field_config.site_prority]))

        # 片商字段语言
        set_radio_buttons(
            studio_field_config.language.value if studio_field_config.language.value != "undefined" else "zh_cn",
            (self.Ui.radioButton_studio_zh_cn, "zh_cn"),
            (self.Ui.radioButton_studio_zh_tw, "zh_tw"),
            (self.Ui.radioButton_studio_jp, "jp"),
            default=self.Ui.radioButton_studio_zh_cn,
        )
        # 片商-使用信息映射表
        self.Ui.checkBox_studio_translate.setChecked(studio_field_config.translate)

        # 想看字段配置
        wanted_field_config = manager.config.get_field_config(field_mapping["wanted"])
        self.Ui.lineEdit_wanted_website.setText(",".join([site.value for site in wanted_field_config.site_prority]))

        # 发行商字段配置
        publisher_field_config = manager.config.get_field_config(field_mapping["publisher"])
        self.Ui.lineEdit_publisher_website.setText(
            ",".join([site.value for site in publisher_field_config.site_prority])
        )

        # 发行字段语言
        set_radio_buttons(
            publisher_field_config.language.value if publisher_field_config.language.value != "undefined" else "zh_cn",
            (self.Ui.radioButton_publisher_zh_cn, "zh_cn"),
            (self.Ui.radioButton_publisher_zh_tw, "zh_tw"),
            (self.Ui.radioButton_publisher_jp, "jp"),
            default=self.Ui.radioButton_publisher_zh_cn,
        )
        # 发行-使用信息映射表
        self.Ui.checkBox_publisher_translate.setChecked(publisher_field_config.translate)

        # 导演字段配置
        director_field_config = manager.config.get_field_config(field_mapping["director"])
        self.Ui.lineEdit_directors_website.setText(
            ",".join([site.value for site in director_field_config.site_prority])
        )

        # 导演字段语言
        set_radio_buttons(
            director_field_config.language.value if director_field_config.language.value != "undefined" else "zh_cn",
            (self.Ui.radioButton_director_zh_cn, "zh_cn"),
            (self.Ui.radioButton_director_zh_tw, "zh_tw"),
            (self.Ui.radioButton_director_jp, "jp"),
            default=self.Ui.radioButton_director_zh_cn,
        )
        # 导演-使用信息映射表
        self.Ui.checkBox_director_translate.setChecked(director_field_config.translate)

        # 海报字段配置
        poster_field_config = manager.config.get_field_config(field_mapping["poster"])
        self.Ui.lineEdit_poster_website.setText(",".join([site.value for site in poster_field_config.site_prority]))

        # 缩略图字段配置
        thumb_field_config = manager.config.get_field_config(field_mapping["thumb"])
        self.Ui.lineEdit_thumb_website.setText(",".join([site.value for site in thumb_field_config.site_prority]))

        # 剧照字段配置
        extrafanart_field_config = manager.config.get_field_config(field_mapping["extrafanart"])
        self.Ui.lineEdit_extrafanart_website.setText(
            ",".join([site.value for site in extrafanart_field_config.site_prority])
        )

        # 评分字段配置
        score_field_config = manager.config.get_field_config(field_mapping["score"])
        self.Ui.lineEdit_score_website.setText(",".join([site.value for site in score_field_config.site_prority]))

        # 发行日期字段配置
        release_field_config = manager.config.get_field_config(field_mapping["release"])
        self.Ui.lineEdit_release_website.setText(",".join([site.value for site in release_field_config.site_prority]))

        # 时长字段配置
        runtime_field_config = manager.config.get_field_config(field_mapping["runtime"])
        self.Ui.lineEdit_runtime_website.setText(",".join([site.value for site in runtime_field_config.site_prority]))
        # 预告片字段配置
        trailer_field_config = manager.config.get_field_config(field_mapping["trailer"])
        self.Ui.lineEdit_trailer_website.setText(",".join([site.value for site in trailer_field_config.site_prority]))

        self.Ui.lineEdit_nfo_tagline.setText(manager.config.nfo_tagline)
        self.Ui.lineEdit_nfo_tag_series.setText(manager.config.nfo_tag_series)
        self.Ui.lineEdit_nfo_tag_studio.setText(manager.config.nfo_tag_studio)
        self.Ui.lineEdit_nfo_tag_publisher.setText(manager.config.nfo_tag_publisher)
        self.Ui.lineEdit_nfo_tag_actor.setText(manager.config.nfo_tag_actor)
        self.Ui.lineEdit_nfo_tag_actor_contains.setText("|".join(manager.config.nfo_tag_actor_contains))

        # 写入nfo的字段 - 新配置直接使用枚举列表，不需要版本兼容性检查
        nfo_include_new = manager.config.nfo_include_new

        set_checkboxes(
            nfo_include_new,
            (self.Ui.checkBox_nfo_sorttitle, NfoInclude.SORTTITLE),
            (self.Ui.checkBox_nfo_originaltitle, NfoInclude.ORIGINALTITLE),
            (self.Ui.checkBox_nfo_title_cd, NfoInclude.TITLE_CD),
            (self.Ui.checkBox_nfo_outline, NfoInclude.OUTLINE),
            (self.Ui.checkBox_nfo_plot, NfoInclude.PLOT_),
            (self.Ui.checkBox_nfo_originalplot, NfoInclude.ORIGINALPLOT),
            (self.Ui.checkBox_outline_cdata, NfoInclude.OUTLINE_NO_CDATA),
            (self.Ui.checkBox_nfo_release, NfoInclude.RELEASE_),
            (self.Ui.checkBox_nfo_relasedate, NfoInclude.RELEASEDATE),
            (self.Ui.checkBox_nfo_premiered, NfoInclude.PREMIERED),
            (self.Ui.checkBox_nfo_country, NfoInclude.COUNTRY),
            (self.Ui.checkBox_nfo_mpaa, NfoInclude.MPAA),
            (self.Ui.checkBox_nfo_customrating, NfoInclude.CUSTOMRATING),
            (self.Ui.checkBox_nfo_year, NfoInclude.YEAR),
            (self.Ui.checkBox_nfo_runtime, NfoInclude.RUNTIME),
            (self.Ui.checkBox_nfo_wanted, NfoInclude.WANTED),
            (self.Ui.checkBox_nfo_score, NfoInclude.SCORE),
            (self.Ui.checkBox_nfo_criticrating, NfoInclude.CRITICRATING),
            (self.Ui.checkBox_nfo_actor, NfoInclude.ACTOR),
            (self.Ui.checkBox_nfo_all_actor, NfoInclude.ACTOR_ALL),
            (self.Ui.checkBox_nfo_director, NfoInclude.DIRECTOR),
            (self.Ui.checkBox_nfo_series, NfoInclude.SERIES),
            (self.Ui.checkBox_nfo_tag, NfoInclude.TAG),
            (self.Ui.checkBox_nfo_genre, NfoInclude.GENRE),
            (self.Ui.checkBox_nfo_actor_set, NfoInclude.ACTOR_SET),
            (self.Ui.checkBox_nfo_set, NfoInclude.SERIES_SET),
            (self.Ui.checkBox_nfo_studio, NfoInclude.STUDIO),
            (self.Ui.checkBox_nfo_maker, NfoInclude.MAKER),
            (self.Ui.checkBox_nfo_publisher, NfoInclude.PUBLISHER),
            (self.Ui.checkBox_nfo_label, NfoInclude.LABEL),
            (self.Ui.checkBox_nfo_poster, NfoInclude.POSTER),
            (self.Ui.checkBox_nfo_cover, NfoInclude.COVER),
            (self.Ui.checkBox_nfo_trailer, NfoInclude.TRAILER),
            (self.Ui.checkBox_nfo_website, NfoInclude.WEBSITE),
        )
        # endregion

        # 翻译引擎
        set_checkboxes(
            manager.config.translate_config.translate_by,
            (self.Ui.checkBox_youdao, Translator.YOUDAO),
            (self.Ui.checkBox_google, Translator.GOOGLE),
            (self.Ui.checkBox_deepl, Translator.DEEPL),
            (self.Ui.checkBox_llm, Translator.LLM),
        )

        # deepl_key
        self.Ui.lineEdit_deepl_key.setText(manager.config.translate_config.deepl_key)

        # llm config
        self.Ui.lineEdit_llm_url.setText(str(manager.config.translate_config.llm_url))
        self.Ui.lineEdit_llm_key.setText(manager.config.translate_config.llm_key)
        self.Ui.lineEdit_llm_model.setText(manager.config.translate_config.llm_model)
        self.Ui.textEdit_llm_prompt.setText(manager.config.translate_config.llm_prompt)
        self.Ui.doubleSpinBox_llm_max_req_sec.setValue(manager.config.translate_config.llm_max_req_sec)
        self.Ui.spinBox_llm_max_try.setValue(manager.config.translate_config.llm_max_try)
        self.Ui.doubleSpinBox_llm_temperature.setValue(manager.config.translate_config.llm_temperature)
        # endregion

        # region common
        # 线程数量
        self.Ui.horizontalSlider_thread.setValue(manager.config.thread_number)
        self.Ui.lcdNumber_thread.display(manager.config.thread_number)
        # 线程延时
        self.Ui.horizontalSlider_thread_time.setValue(manager.config.thread_time)
        self.Ui.lcdNumber_thread_time.display(manager.config.thread_time)
        # javdb 延时
        self.Ui.horizontalSlider_javdb_time.setValue(manager.config.javdb_time)
        self.Ui.lcdNumber_javdb_time.display(manager.config.javdb_time)

        # 刮削模式
        main_mode = manager.config.main_mode
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
        # region read_mode
        set_checkboxes(
            manager.config.read_mode,
            (self.Ui.checkBox_read_has_nfo_update, ReadMode.HAS_NFO_UPDATE),
            (self.Ui.checkBox_read_download_file_again, ReadMode.READ_DOWNLOAD_AGAIN),
            (self.Ui.checkBox_read_update_nfo, ReadMode.READ_UPDATE_NFO),
            (self.Ui.checkBox_read_no_nfo_scrape, ReadMode.NO_NFO_SCRAPE),
        )
        # endregion

        # 更新模式
        self.Ui.checkBox_update_a.setChecked(False)
        update_mode = manager.config.update_mode

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
        self.Ui.lineEdit_update_a_folder.setText(manager.config.update_a_folder)
        # 更新模式 - b 目录
        self.Ui.lineEdit_update_b_folder.setText(manager.config.update_b_folder)
        # 更新模式 - d 目录
        self.Ui.lineEdit_update_d_folder.setText(manager.config.update_d_folder)
        # 更新模式 - c 文件名
        self.Ui.lineEdit_update_c_filetemplate.setText(manager.config.update_c_filetemplate)
        # 更新模式 - emby视频标题
        self.Ui.lineEdit_update_titletemplate.setText(manager.config.update_titletemplate)

        # 软链接
        set_radio_buttons(
            manager.config.soft_link,
            (self.Ui.radioButton_soft_on, 1),
            (self.Ui.radioButton_hard_on, 2),
            (self.Ui.radioButton_soft_off, 0),
            default=self.Ui.radioButton_soft_off,
        )
        # 成功后移动文件
        set_radio_buttons(
            manager.config.success_file_move,
            (self.Ui.radioButton_succ_move_on, True),
            (self.Ui.radioButton_succ_move_off, False),
            default=self.Ui.radioButton_succ_move_off,
        )
        # 失败后移动文件
        set_radio_buttons(
            manager.config.failed_file_move,
            (self.Ui.radioButton_fail_move_on, True),
            (self.Ui.radioButton_fail_move_off, False),
            default=self.Ui.radioButton_fail_move_off,
        )
        # 成功后重命名文件
        set_radio_buttons(
            manager.config.success_file_rename,
            (self.Ui.radioButton_succ_rename_on, True),
            (self.Ui.radioButton_succ_rename_off, False),
            default=self.Ui.radioButton_succ_rename_off,
        )
        # 结束后删除空文件夹
        set_radio_buttons(
            manager.config.del_empty_folder,
            (self.Ui.radioButton_del_empty_folder_on, True),
            (self.Ui.radioButton_del_empty_folder_off, False),
            default=self.Ui.radioButton_del_empty_folder_off,
        )

        # 显示封面
        self.Ui.checkBox_cover.setChecked(manager.config.show_poster)
        # endregion

        # region file_download
        # 下载文件
        set_checkboxes(
            manager.config.download_files,
            (self.Ui.checkBox_download_poster, DownloadableFile.POSTER),
            (self.Ui.checkBox_download_thumb, DownloadableFile.THUMB),
            (self.Ui.checkBox_download_fanart, DownloadableFile.FANART),
            (self.Ui.checkBox_download_extrafanart, DownloadableFile.EXTRAFANART),
            (self.Ui.checkBox_download_trailer, DownloadableFile.TRAILER),
            (self.Ui.checkBox_download_nfo, DownloadableFile.NFO),
            (self.Ui.checkBox_extras, DownloadableFile.EXTRAFANART_EXTRAS),
            (self.Ui.checkBox_download_extrafanart_copy, DownloadableFile.EXTRAFANART_COPY),
            (self.Ui.checkBox_theme_videos, DownloadableFile.THEME_VIDEOS),
            (self.Ui.checkBox_ignore_pic_fail, DownloadableFile.IGNORE_PIC_FAIL),
            (self.Ui.checkBox_ignore_youma, DownloadableFile.IGNORE_YOUMA),
            (self.Ui.checkBox_ignore_wuma, DownloadableFile.IGNORE_WUMA),
            (self.Ui.checkBox_ignore_fc2, DownloadableFile.IGNORE_FC2),
            (self.Ui.checkBox_ignore_guochan, DownloadableFile.IGNORE_GUOCHAN),
            (self.Ui.checkBox_ignore_size, DownloadableFile.IGNORE_SIZE),
        )
        # 保留文件
        set_checkboxes(
            manager.config.keep_files,
            (self.Ui.checkBox_old_poster, KeepableFile.POSTER),
            (self.Ui.checkBox_old_thumb, KeepableFile.THUMB),
            (self.Ui.checkBox_old_fanart, KeepableFile.FANART),
            (self.Ui.checkBox_old_extrafanart, KeepableFile.EXTRAFANART),
            (self.Ui.checkBox_old_trailer, KeepableFile.TRAILER),
            (self.Ui.checkBox_old_nfo, KeepableFile.NFO),
            (self.Ui.checkBox_old_extrafanart_copy, KeepableFile.EXTRAFANART_COPY),
            (self.Ui.checkBox_old_theme_videos, KeepableFile.THEME_VIDEOS),
        )

        # 下载高清图片 - 新配置直接使用枚举列表，不需要版本兼容性检查
        download_hd_pics = manager.config.download_hd_pics
        set_checkboxes(
            download_hd_pics,
            (self.Ui.checkBox_hd_poster, HDPicSource.POSTER),
            (self.Ui.checkBox_hd_thumb, HDPicSource.THUMB),
            (self.Ui.checkBox_amazon_big_pic, HDPicSource.AMAZON),
            (self.Ui.checkBox_official_big_pic, HDPicSource.OFFICIAL),
            (self.Ui.checkBox_google_big_pic, HDPicSource.GOOGLE),
        )
        set_radio_buttons(
            "only" if HDPicSource.GOO_ONLY in download_hd_pics else "first",
            (self.Ui.radioButton_google_only, "only"),
            (self.Ui.radioButton_google_first, "first"),
            default=self.Ui.radioButton_google_first,
        )
        # endregion

        # Google下载词
        self.Ui.lineEdit_google_used.setText(",".join(manager.config.google_used))
        # Google过滤词
        self.Ui.lineEdit_google_exclude.setText(",".join(manager.config.google_exclude))
        # endregion

        # region Name_Rule
        # 视频目录命名
        self.Ui.lineEdit_dir_name.setText(manager.config.folder_name)
        # 视频文件名命名（本地文件）
        self.Ui.lineEdit_local_name.setText(manager.config.naming_file)
        # emby视频标题（nfo文件）
        self.Ui.lineEdit_media_name.setText(manager.config.naming_media)
        # 防屏蔽字符
        self.Ui.lineEdit_prevent_char.setText(manager.config.prevent_char)

        # region fields_rule
        # 字段命名规则

        set_checkboxes(
            manager.config.fields_rule,
            # 去除标题后的演员名
            (self.Ui.checkBox_title_del_actor, FieldRule.DEL_ACTOR),
            # 演员去除括号
            (self.Ui.checkBox_actor_del_char, FieldRule.DEL_CHAR),
            # FC2 演员名
            (self.Ui.checkBox_actor_fc2_seller, FieldRule.FC2_SELLER),
            # 素人番号删除前缀数字
            (self.Ui.checkBox_number_del_num, FieldRule.DEL_NUM),
        )
        # endregion

        # 字段命名规则-未知演员
        self.Ui.lineEdit_actor_no_name.setText(manager.config.actor_no_name)
        # 字段命名规则-发行日期
        self.Ui.lineEdit_release_rule.setText(manager.config.release_rule)
        # 长度命名规则-目录
        folder_name_max = manager.config.folder_name_max
        if folder_name_max <= 0 or folder_name_max > 255:
            folder_name_max = 60
        self.Ui.lineEdit_folder_name_max.setText(str(folder_name_max))
        # 长度命名规则-文件名
        file_name_max = manager.config.file_name_max
        if file_name_max <= 0 or file_name_max > 255:
            file_name_max = 60
        self.Ui.lineEdit_file_name_max.setText(str(file_name_max))
        self.Ui.lineEdit_actor_name_max.setText(str(manager.config.actor_name_max))
        # 长度命名规则-演员名更多
        self.Ui.lineEdit_actor_name_more.setText(manager.config.actor_name_more)
        # 后缀排序
        self.Ui.lineEdit_suffix_sort.setText(",".join([s.value for s in manager.config.suffix_sort]))
        # 版本命名规则-无码破解版
        self.Ui.lineEdit_umr_style.setText(manager.config.umr_style)
        # 版本命名规则-无码流出版
        self.Ui.lineEdit_leak_style.setText(manager.config.leak_style)
        # 版本命名规则-无码版
        self.Ui.lineEdit_wuma_style.setText(manager.config.wuma_style)
        # 版本命名规则-有码版
        self.Ui.lineEdit_youma_style.setText(manager.config.youma_style)
        # show_moword 和 show_4k 已移除，功能已集成到命名模板中
        # 分集命名规则
        set_radio_buttons(
            manager.config.cd_name,
            (self.Ui.radioButton_cd_part_lower, 0),
            (self.Ui.radioButton_cd_part_upper, 1),
            default=self.Ui.radioButton_cd_part_digital,
        )

        cd_char = manager.config.cd_char
        # region cd_char
        # 版本兼容性检查已简化，新配置直接使用枚举列表

        set_checkboxes(
            cd_char,
            # 允许分集识别字母
            (self.Ui.checkBox_cd_part_a, CDChar.LETTER),
            # 允许分集识别字母（重复）
            (self.Ui.checkBox_cd_part_c, CDChar.LETTER),
            # 允许分集识别数字
            (self.Ui.checkBox_cd_part_01, CDChar.DIGITAL),
            (self.Ui.checkBox_cd_part_1_xxx, CDChar.MIDDLE_NUMBER),
            # 下划线分隔符
            (self.Ui.checkBox_cd_part_underline, CDChar.UNDERLINE),
            (self.Ui.checkBox_cd_part_space, CDChar.SPACE),
            (self.Ui.checkBox_cd_part_point, CDChar.POINT),
        )
        # 特殊处理 endc
        self.Ui.checkBox_cd_part_c.setChecked(CDChar.ENDC in cd_char)
        # endregion

        # 图片命名是否包含视频名
        set_radio_buttons(
            manager.config.pic_simple_name,
            (self.Ui.radioButton_pic_with_filename, False),
            default=self.Ui.radioButton_pic_no_filename,
        )
        # 预告片命名是否包含视频名
        set_radio_buttons(
            manager.config.trailer_simple_name,
            (self.Ui.radioButton_trailer_with_filename, False),
            default=self.Ui.radioButton_trailer_no_filename,
        )
        # 画质命名规则
        set_radio_buttons(
            manager.config.hd_name,
            (self.Ui.radioButton_definition_height, "height"),
            default=self.Ui.radioButton_definition_hd,
        )
        # 分辨率获取方式
        set_radio_buttons(
            manager.config.hd_get,
            (self.Ui.radioButton_videosize_video, "video"),
            (self.Ui.radioButton_videosize_path, "path"),
            default=self.Ui.radioButton_videosize_none,
        )
        # endregion

        # region 字幕
        # 中文字幕判断字符
        self.Ui.lineEdit_cnword_char.setText(",".join(manager.config.cnword_char))
        # 中文字幕字符样式
        self.Ui.lineEdit_cnword_style.setText(manager.config.cnword_style.strip("^"))
        # 显示中文字幕字符-视频目录名
        self.Ui.checkBox_foldername.setChecked(manager.config.folder_cnword)
        # 显示中文字幕字符-视频文件名
        self.Ui.checkBox_filename.setChecked(manager.config.file_cnword)
        # 外挂字幕文件目录
        self.Ui.lineEdit_sub_folder.setText(convert_path(manager.config.subtitle_folder))
        # 自动添加字幕
        set_radio_buttons(
            manager.config.subtitle_add,
            (self.Ui.radioButton_add_sub_on, True),
            default=self.Ui.radioButton_add_sub_off,
        )
        # 字幕文件名添加.chs后缀
        self.Ui.checkBox_sub_add_chs.setChecked(manager.config.subtitle_add_chs)
        # 重新刮削新添加字幕的视频
        self.Ui.checkBox_sub_rescrape.setChecked(manager.config.subtitle_add_rescrape)
        # endregion

        # region emby
        # 服务器类型
        set_radio_buttons(
            "emby" if "emby" in manager.config.server_type else "jellyfin",
            (self.Ui.radioButton_server_emby, "emby"),
            (self.Ui.radioButton_server_jellyfin, "jellyfin"),
            default=self.Ui.radioButton_server_emby,
        )
        # emby地址
        self.Ui.lineEdit_emby_url.setText(str(manager.config.emby_url))
        # emby密钥
        self.Ui.lineEdit_api_key.setText(manager.config.api_key)
        # emby用户ID
        self.Ui.lineEdit_user_id.setText(manager.config.user_id)

        emby_on = manager.config.emby_on
        # 演员信息语言设置
        if EmbyAction.ACTOR_INFO_ZH_CN in emby_on:
            lang = "zh_cn"
        elif EmbyAction.ACTOR_INFO_ZH_TW in emby_on:
            lang = "zh_tw"
        else:
            lang = "ja"

        set_radio_buttons(
            lang,
            (self.Ui.radioButton_actor_info_zh_cn, "zh_cn"),
            (self.Ui.radioButton_actor_info_zh_tw, "zh_tw"),
            (self.Ui.radioButton_actor_info_ja, "ja"),
            default=self.Ui.radioButton_actor_info_ja,
        )
        set_checkboxes(
            emby_on,
            (self.Ui.checkBox_actor_info_translate, EmbyAction.ACTOR_INFO_TRANSLATE),
            (self.Ui.checkBox_actor_info_photo, EmbyAction.ACTOR_INFO_PHOTO),
            (self.Ui.checkBox_actor_photo_ne_backdrop, EmbyAction.GRAPHIS_BACKDROP),
            (self.Ui.checkBox_actor_photo_ne_face, EmbyAction.GRAPHIS_FACE),
            (self.Ui.checkBox_actor_photo_ne_new, EmbyAction.GRAPHIS_NEW),
            (self.Ui.checkBox_actor_photo_auto, EmbyAction.ACTOR_PHOTO_AUTO),
            (self.Ui.checkBox_actor_pic_replace, EmbyAction.ACTOR_REPLACE),
        )
        # 演员信息刮削模式
        info_mode = "all" if EmbyAction.ACTOR_INFO_ALL in emby_on else "miss"
        set_radio_buttons(
            info_mode,
            (self.Ui.radioButton_actor_info_all, "all"),
            (self.Ui.radioButton_actor_info_miss, "miss"),
            default=self.Ui.radioButton_actor_info_miss,
        )
        # 演员照片来源
        photo_source = "local" if EmbyAction.ACTOR_PHOTO_LOCAL in emby_on else "net"
        set_radio_buttons(
            photo_source,
            (self.Ui.radioButton_actor_photo_local, "local"),
            (self.Ui.radioButton_actor_photo_net, "net"),
            default=self.Ui.radioButton_actor_photo_net,
        )
        # 演员照片刮削模式
        photo_mode = "all" if EmbyAction.ACTOR_PHOTO_ALL in emby_on else "miss"
        set_radio_buttons(
            photo_mode,
            (self.Ui.radioButton_actor_photo_all, "all"),
            (self.Ui.radioButton_actor_photo_miss, "miss"),
            default=self.Ui.radioButton_actor_photo_miss,
        )

        self.Ui.checkBox_actor_photo_kodi.setChecked(manager.config.actor_photo_kodi_auto)
        # 网络头像库 gfriends 项目地址
        self.Ui.lineEdit_net_actor_photo.setText(str(manager.config.gfriends_github))
        # 本地头像目录
        self.Ui.lineEdit_actor_photo_folder.setText(convert_path(manager.config.actor_photo_folder))
        # 演员数据库路径
        self.Ui.lineEdit_actor_db_path.setText(convert_path(manager.config.info_database_path))
        # 演员数据库
        self.Ui.checkBox_actor_db.setChecked(manager.config.use_database)
        # endregion

        # region mark
        # 水印设置
        # 封面图加水印
        self.Ui.checkBox_poster_mark.setChecked(manager.config.poster_mark != 0)
        # 缩略图加水印
        self.Ui.checkBox_thumb_mark.setChecked(manager.config.thumb_mark != 0)
        # 艺术图加水印
        self.Ui.checkBox_fanart_mark.setChecked(manager.config.fanart_mark != 0)
        # 水印大小
        self.Ui.horizontalSlider_mark_size.setValue(int(manager.config.mark_size))
        self.Ui.lcdNumber_mark_size.display(int(manager.config.mark_size))

        # 启用的水印类型
        set_checkboxes(
            manager.config.mark_type,
            (self.Ui.checkBox_sub, MarkType.SUB),
            (self.Ui.checkBox_censored, MarkType.YOUMA),
            (self.Ui.checkBox_umr, MarkType.UMR),
            (self.Ui.checkBox_leak, MarkType.LEAK),
            (self.Ui.checkBox_uncensored, MarkType.UNCENSORED),
            (self.Ui.checkBox_hd, MarkType.HD),
        )
        # 水印位置是否固定
        set_radio_buttons(
            manager.config.mark_fixed,
            (self.Ui.radioButton_not_fixed_position, "not_fixed"),
            (self.Ui.radioButton_fixed_corner, "corner"),
            (self.Ui.radioButton_fixed_position, "fixed"),
            default=self.Ui.radioButton_fixed_position,
        )
        # 首个水印位置
        set_radio_buttons(
            manager.config.mark_pos,
            (self.Ui.radioButton_top_left, "top_left"),
            (self.Ui.radioButton_top_right, "top_right"),
            (self.Ui.radioButton_bottom_left, "bottom_left"),
            (self.Ui.radioButton_bottom_right, "bottom_right"),
            default=self.Ui.radioButton_top_left,
        )
        # 固定一个位置
        set_radio_buttons(
            manager.config.mark_pos_corner,
            (self.Ui.radioButton_top_left_corner, "top_left"),
            (self.Ui.radioButton_top_right_corner, "top_right"),
            (self.Ui.radioButton_bottom_left_corner, "bottom_left"),
            (self.Ui.radioButton_bottom_right_corner, "bottom_right"),
            default=self.Ui.radioButton_top_left_corner,
        )
        # 高清水印位置
        set_radio_buttons(
            manager.config.mark_pos_hd,
            (self.Ui.radioButton_top_left_hd, "top_left"),
            (self.Ui.radioButton_top_right_hd, "top_right"),
            (self.Ui.radioButton_bottom_left_hd, "bottom_left"),
            (self.Ui.radioButton_bottom_right_hd, "bottom_right"),
            default=self.Ui.radioButton_bottom_right_hd,
        )
        # 字幕水印位置
        set_radio_buttons(
            manager.config.mark_pos_sub,
            (self.Ui.radioButton_top_left_sub, "top_left"),
            (self.Ui.radioButton_top_right_sub, "top_right"),
            (self.Ui.radioButton_bottom_left_sub, "bottom_left"),
            (self.Ui.radioButton_bottom_right_sub, "bottom_right"),
            default=self.Ui.radioButton_top_left_sub,
        )
        # 马赛克水印位置
        set_radio_buttons(
            manager.config.mark_pos_mosaic,
            (self.Ui.radioButton_top_left_mosaic, "top_left"),
            (self.Ui.radioButton_top_right_mosaic, "top_right"),
            (self.Ui.radioButton_bottom_left_mosaic, "bottom_left"),
            (self.Ui.radioButton_bottom_right_mosaic, "bottom_right"),
            default=self.Ui.radioButton_top_right_mosaic,
        )
        # endregion

        # region network
        # 代理类型
        proxy_type = "no" if not manager.config.use_proxy else "http"  # 简化代理类型判断
        set_radio_buttons(
            proxy_type,
            (self.Ui.radioButton_proxy_nouse, "no"),
            (self.Ui.radioButton_proxy_http, "http"),
            (self.Ui.radioButton_proxy_socks5, "socks5"),
            default=self.Ui.radioButton_proxy_nouse,
        )

        # 代理地址
        self.Ui.lineEdit_proxy.setText(manager.config.proxy)
        # 超时时间
        self.Ui.horizontalSlider_timeout.setValue(int(manager.config.timeout))
        self.Ui.lcdNumber_timeout.display(int(manager.config.timeout))
        # 重试次数
        self.Ui.horizontalSlider_retry.setValue(int(manager.config.retry))
        self.Ui.lcdNumber_retry.display(int(manager.config.retry))

        # site config
        site = self.Ui.comboBox_custom_website.currentText()
        if site in Website:
            self.Ui.lineEdit_site_custom_url.setText(manager.config.get_site_url(Website(site)))
            site_config = manager.config.get_site_config(Website(site))
            self.Ui.checkBox_site_use_browser.setChecked(site_config.use_browser)

        self.Ui.lineEdit_api_token_theporndb.setText(convert_path(manager.config.theporndb_api_token))
        # javdb cookie
        self.set_javdb_cookie.emit(manager.config.javdb)
        # javbus cookie
        self.set_javbus_cookie.emit(manager.config.javbus)
        # endregion

        # region other
        # 配置文件目录
        self.Ui.lineEdit_config_folder.setText(convert_path(manager.data_folder))
        # 间歇刮削文件数量
        rest_count = int(manager.config.rest_count)
        if rest_count == 0:
            rest_count = 1
        self.Ui.lineEdit_rest_count.setText(str(rest_count))

        # 间歇刮削间隔时间 - 转换 timedelta 为字符串格式
        rest_time = manager.config.rest_time
        rest_hours = rest_time.seconds // 3600
        rest_minutes = (rest_time.seconds % 3600) // 60
        rest_seconds = rest_time.seconds % 60
        rest_time_str = f"{rest_hours:02d}:{rest_minutes:02d}:{rest_seconds:02d}"
        self.Ui.lineEdit_rest_time.setText(rest_time_str)
        # 换算（秒）
        Flags.rest_time_convert = int(rest_time.total_seconds())

        # 循环任务间隔时间 - 转换 timedelta 为字符串格式
        timed_interval = manager.config.timed_interval
        timed_hours = timed_interval.seconds // 3600
        timed_minutes = (timed_interval.seconds % 3600) // 60
        timed_seconds = timed_interval.seconds % 60
        timed_interval_str = f"{timed_hours:02d}:{timed_minutes:02d}:{timed_seconds:02d}"
        self.Ui.lineEdit_timed_interval.setText(timed_interval_str)
        # 换算（毫秒）
        timed_interval_convert = timed_interval.total_seconds() * 1000
        self.timer_scrape.stop()

        # 显示字段刮削过程
        self.Ui.checkBox_show_web_log.setChecked(manager.config.show_web_log)
        # 显示字段来源信息
        self.Ui.checkBox_show_from_log.setChecked(manager.config.show_from_log)
        # 显示字段内容信息
        self.Ui.checkBox_show_data_log.setChecked(manager.config.show_data_log)
        # 保存日志
        set_radio_buttons(
            manager.config.save_log,
            (self.Ui.radioButton_log_off, False),
            default=self.Ui.radioButton_log_on,
        )
        # 检查更新
        set_radio_buttons(
            manager.config.update_check,
            (self.Ui.radioButton_update_off, False),
            default=self.Ui.radioButton_update_on,
        )

        # 本地资源库
        self.Ui.lineEdit_local_library_path.setText(convert_path(manager.config.local_library))
        # 演员名
        self.Ui.lineEdit_actors_name.setText(manager.config.actors_name)
        # 网盘目录
        self.Ui.lineEdit_netdisk_path.setText(convert_path(manager.config.netdisk_path))
        # 本地磁盘目录
        self.Ui.lineEdit_localdisk_path.setText(convert_path(manager.config.localdisk_path))
        # 窗口标题栏
        self.Ui.checkBox_hide_window_title.setChecked(manager.config.window_title == "hide")
        # endregion

        # region switch_on
        switch_on = manager.config.switch_on
        # 版本兼容性检查已简化，新配置直接使用枚举列表

        # 基础开关设置
        set_checkboxes(
            switch_on,
            (self.Ui.checkBox_auto_start, Switch.AUTO_START),
            (self.Ui.checkBox_auto_exit, Switch.AUTO_EXIT),
            (self.Ui.checkBox_rest_scrape, Switch.REST_SCRAPE),
            (self.Ui.checkBox_remain_task, Switch.REMAIN_TASK),
            (self.Ui.checkBox_show_dialog_exit, Switch.SHOW_DIALOG_EXIT),
            (self.Ui.checkBox_show_dialog_stop_scrape, Switch.SHOW_DIALOG_STOP_SCRAPE),
            (self.Ui.checkBox_dark_mode, Switch.DARK_MODE),
            (self.Ui.checkBox_copy_netdisk_nfo, Switch.COPY_NETDISK_NFO),
            (self.Ui.checkBox_net_ipv4_only, Switch.IPV4_ONLY),
            (self.Ui.checkBox_theporndb_hash, Switch.THEPORNDB_NO_HASH),
            (self.Ui.checkBox_sortmode_delpic, Switch.SORT_DEL),
        )

        # 定时刮削设置
        if Switch.TIMED_SCRAPE in switch_on:
            self.Ui.checkBox_timed_scrape.setChecked(True)
            self.timer_scrape.start(int(timed_interval_convert))
        else:
            self.Ui.checkBox_timed_scrape.setChecked(False)

        # 其他设置
        self.dark_mode = Switch.DARK_MODE in switch_on
        self.show_hide_logs(Switch.SHOW_LOGS in switch_on)

        # 隐藏窗口设置
        if Switch.HIDE_CLOSE in switch_on:
            hide_mode = "close"
        elif Switch.HIDE_MINI in switch_on:
            hide_mode = "mini"
        else:
            hide_mode = "none"

        set_radio_buttons(
            hide_mode,
            (self.Ui.radioButton_hide_close, "close"),
            (self.Ui.radioButton_hide_mini, "mini"),
            (self.Ui.radioButton_hide_none, "none"),
            default=self.Ui.radioButton_hide_none,
        )

        # Qt 对话框设置
        if Switch.QT_DIALOG in switch_on:
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
            if Switch.PASSTHROUGH in switch_on:
                self.Ui.checkBox_highdpi_passthrough.setChecked(True)
                if not os.path.isfile("highdpi_passthrough"):
                    open("highdpi_passthrough", "w").close()
            else:
                self.Ui.checkBox_highdpi_passthrough.setChecked(False)
                if os.path.isfile("highdpi_passthrough"):
                    delete_file_sync("highdpi_passthrough")
        else:
            self.Ui.checkBox_highdpi_passthrough.setEnabled(False)
            if Switch.HIDE_MENU in switch_on:
                self.Ui.checkBox_hide_menu_icon.setChecked(True)
                try:
                    if hasattr(self, "tray_icon"):
                        self.tray_icon.hide()
                except Exception:
                    signal_qt.show_traceback_log(traceback.format_exc())
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

        self.Ui.checkBox_create_link.setChecked(manager.config.auto_link)

        # ======================================================================================END
        # 根据是否同意改变清理按钮状态
        self.checkBox_i_agree_clean_clicked()
        try:
            scrape_like_text = Flags.scrape_like_text
            if manager.config.scrape_like == "single":
                scrape_like_text += f" · {manager.config.website_single.value}"
            if manager.config.soft_link == 1:
                scrape_like_text += " · 软连接开"
            elif manager.config.soft_link == 2:
                scrape_like_text += " · 硬连接开"
            signal_qt.show_log_text(
                f" 🛠 当前配置：{manager.path} 加载完成！\n "
                f"📂 程序目录：{manager.data_folder} \n "
                f"📂 刮削目录：{get_movie_path_setting().movie_path} \n "
                f"💠 刮削模式：{Flags.main_mode_text} · {scrape_like_text} \n "
                f"🖥️ 系统信息：{platform.platform()} \n "
                f"🐰 软件版本：{self.localversion} \n"
            )
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
        try:
            # 界面自动调整
            self._windows_auto_adjust()
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)  # type: ignore
        self.activateWindow()
        try:
            # 主界面右上角显示提示信息
            self.set_label_file_path.emit(f"🎈 当前刮削路径: \n {get_movie_path_setting().movie_path}")
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
    else:  # ini不存在，重新创建
        signal_qt.show_log_text(f"Create config file: {config_path} ")
        self.pushButton_init_config_clicked()
