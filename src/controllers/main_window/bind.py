from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QLineEdit

    from models.config.manager import ConfigSchema
    from views.MDCx import Ui_MDCx


class ConfigBinder:
    def __init__(self, ui: "Ui_MDCx", config: "ConfigSchema"):
        self.text_relations: list[tuple["QLineEdit", str]] = [
            (ui.lineEdit_extrafanart_dir, config.extrafanart_folder),  # 剧照副本目录
            (ui.lineEdit_movie_type, config.media_type),  # 视频类型
            (ui.lineEdit_escape_dir, config.folders),  # 排除目录
            (ui.lineEdit_escape_dir_move, config.folders),  # 排除目录 - 工具页面
            (ui.lineEdit_clean_file_ext, config.clean_ext),  # 清理扩展名等于
            (ui.lineEdit_clean_file_name, config.clean_name),  # 清理文件名等于
            (ui.lineEdit_clean_file_contains, config.clean_contains),  # 清理文件名包含
            (ui.lineEdit_clean_excluded_file_ext, config.clean_ignore_ext),  # 不清理扩展名
            (ui.lineEdit_clean_excluded_file_contains, config.clean_ignore_contains),  # 不清理文件名包含
            (ui.lineEdit_deepl_key, config.deepl_key),  # deepl_key
            (ui.lineEdit_llm_url, config.llm_url),
            (ui.lineEdit_llm_key, config.llm_key),
            (ui.lineEdit_llm_model, config.llm_model),
            (ui.textEdit_llm_prompt, config.llm_prompt),
            (ui.lineEdit_update_a_folder, config.update_a_folder),  # 更新模式  -  a 目录
            (ui.lineEdit_update_b_folder, config.update_b_folder),  # 更新模式  -  b 目录
            (ui.lineEdit_update_d_folder, config.update_d_folder),  # 更新模式  -  d 目录
            (ui.lineEdit_google_used, config.google_used),  # Google下载词
            (ui.lineEdit_google_exclude, config.google_exclude),  # Google排除词
            (ui.lineEdit_dir_name, config.folder_name),  # 视频目录命名
            (ui.lineEdit_local_name, config.naming_file),  # 视频文件名命名（本地文件）
            (ui.lineEdit_media_name, config.naming_media),  # emby视频标题（nfo文件）
            (ui.lineEdit_prevent_char, config.prevent_char),  # 防屏蔽字符
            (ui.lineEdit_actor_no_name, config.actor_no_name),  # 字段命名规则 - 未知演员
            (ui.lineEdit_release_rule, config.release_rule),  # 字段命名规则 - 发行日期
            (ui.lineEdit_actor_name_more, config.actor_name_more),  # 长度命名规则 - 演员名更多
            (ui.lineEdit_suffix_sort, config.suffix_sort),
            (ui.lineEdit_umr_style, config.umr_style),  # 版本命名规则 - 无码破解版
            (ui.lineEdit_leak_style, config.leak_style),  # 版本命名规则 - 无码流出版
            (ui.lineEdit_wuma_style, config.wuma_style),  # 版本命名规则 - 无码版
            (ui.lineEdit_youma_style, config.youma_style),  # 版本命名规则 - 有码版
            (ui.lineEdit_cnword_char, config.cnword_char),  # 中文字幕判断字符
            (ui.lineEdit_emby_url, config.emby_url),  # emby地址
            (ui.lineEdit_api_key, config.api_key),  # emby密钥
            (ui.lineEdit_user_id, config.user_id),  # emby用户ID
            (ui.lineEdit_net_actor_photo, config.gfriends_github),  # 网络头像库 gfriends 项目地址
            (ui.lineEdit_proxy, config.proxy),  # 代理地址
            (ui.lineEdit_actors_name, config.actors_name),  # 演员名
            (ui.lineEdit_nfo_tag_publisher, config.nfo_tag_publisher),  # NFO标签 - 发行商
            (ui.lineEdit_nfo_tag_series, config.nfo_tag_series),  # NFO标签 - 系列
            (ui.lineEdit_nfo_tag_studio, config.nfo_tag_studio),  # NFO标签 - 工作室
            (ui.lineEdit_nfo_tagline, config.nfo_tagline),  # NFO标语
            (ui.lineEdit_rest_time, config.rest_time),  # 休息时间
            (ui.lineEdit_timed_interval, config.timed_interval),  # 定时间隔
        ]
        self.text_with_fn: list[tuple["QLineEdit", Any, Callable[[Any], str]]] = [
            # 需要转换为字符串的数值类型
            (ui.lineEdit_actor_name_max, config.actor_name_max, str),
            (ui.lineEdit_clean_file_size, config.clean_size, str),
            (ui.lineEdit_escape_size, config.file_size, str),
            # 需要特殊处理的字符串
            (ui.lineEdit_sub_type, config.sub_type, lambda x: x.replace(".txt|", "")),
        ]

    def set_ui(self):
        for component, value in self.text_relations:
            component.setText(value)

        for component, value, converter_fn in self.text_with_fn:
            component.setText(converter_fn(value))
