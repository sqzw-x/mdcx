"""
用于刮削过程控制的标志位
此模块不应依赖任何项目代码
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from ..entity.enums import FileMode


@dataclass
class _Flags:
    translate_by_list: list[str] = field(default_factory=list)
    rest_time_convert: int = 0
    rest_time_convert_: int = 0
    appoint_url: str = ""
    total_kills: int = 0
    now_kill: int = 0
    success_save_time: float = 0.0
    pool: ThreadPoolExecutor = None
    next_start_time: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock)
    count_claw: int = 0  # 批量刮削次数
    can_save_remain: bool = False  # 保存剩余任务
    remain_list: list[str] = field(default_factory=list)
    new_again_dic: dict[str, tuple[str, str, str]] = field(default_factory=dict)
    again_dic: dict[str, tuple[str, str, str]] = field(default_factory=dict)  # 待重新刮削的字典
    start_time: float = 0.0
    file_mode: FileMode = FileMode.Default  # 默认刮削待刮削目录
    counting_order: int = 0  # 刮削顺序
    total_count: int = 0  # 总数
    rest_now_begin_count: int = 0  # 本轮刮削开始统计的线程序号（实际-1）
    rest_sleepping: bool = False  # 是否休眠中
    rest_next_begin_time: float = 0.0  # 下一轮开始时间
    scrape_starting: int = 0  # 已进入过刮削流程的数量
    scrape_started: int = 0  # 已进入过刮削流程并开始的数量
    scrape_done: int = 0  # 已完成刮削数量
    succ_count: int = 0  # 成功数量
    fail_count: int = 0  # 失败数量
    file_new_path_dic: dict[str, list[str]] = field(
        default_factory=dict
    )  # 所有文件最终输出路径的字典（如已存在，则视为重复文件，直接跳过）
    pic_catch_set: set[str] = field(
        default_factory=set
    )  # 当前文件的图片最终输出路径的字典（如已存在，则最终图片文件视为已处理过）
    file_done_dic: dict[str, dict[str, str]] = field(
        default_factory=dict
    )  # 当前番号的图片已下载完成的标识（如已存在，视为图片已下载完成）
    extrafanart_deal_set: set[str] = field(
        default_factory=set
    )  # 当前文件夹剧照已处理的标识（如已存在，视为剧照已处理过）
    extrafanart_copy_deal_set: set[str] = field(
        default_factory=set
    )  # 当前文件夹剧照副本已下载的标识（如已存在，视为剧照已处理过）
    trailer_deal_set: set[str] = field(default_factory=set)  # 当前文件trailer已处理的标识（如已存在，视为剧照已处理过）
    theme_videos_deal_set: set[str] = field(
        default_factory=set
    )  # 当前文件夹剧照已下载的标识（如已存在，视为剧照已处理过）
    nfo_deal_set: set[str] = field(default_factory=set)  # 当前文件nfo已处理的标识（如已存在，视为剧照已处理过）
    json_get_set: set[str] = field(default_factory=set)  # 去获取json的番号列表
    json_data_dic: dict[str, Any] = field(default_factory=dict)  # 获取成功的json
    img_path: str = ""
    deepl_result: dict[str, Any] = field(
        default_factory=dict
    )  # deep 翻译结果（当没有填写api时，使用第三方翻译模块，作用是实现超时自动退出，避免卡死）
    failed_list: list[list[str]] = field(default_factory=list)  # 失败文件和错误原因记录
    failed_file_list: list[str] = field(default_factory=list)  # 失败文件记录
    stop_flag: bool = False  # 线程停止标识
    single_file_path: str = ""  # 工具单文件刮削的文件路径
    website_name: str = ""
    scrape_start_time: float = 0.0
    success_list: set[str] = field(default_factory=set)
    threads_list: list[threading.Thread] = field(default_factory=list)  # 开启的线程列表
    stop_other: bool = True  # 非刮削线程停止标识
    local_number_flag: str = ""  # 启动后本地数据库是否扫描过
    actor_numbers_dic: dict[str, list[str]] = field(default_factory=dict)  # 每个演员所有番号的字典
    local_number_set: set[str] = field(default_factory=set)  # 本地所有番号的集合
    local_number_cnword_set: set[str] = field(default_factory=set)  # 本地所有有字幕的番号的集合
    current_proxy: str = ""
    log_txt: Any = None  # 日志文件对象
    scrape_like_text: str = ""
    main_mode_text: str = ""

    def reset(self) -> None:
        self.failed_list = []
        self.failed_file_list = []
        self.counting_order = 0
        self.total_count = 0
        self.rest_now_begin_count = 0
        self.rest_sleepping = False
        self.scrape_starting = 0
        self.scrape_started = 0
        self.scrape_done = 0
        self.succ_count = 0
        self.fail_count = 0
        self.file_new_path_dic = {}
        self.pic_catch_set = set()
        self.file_done_dic = {}
        self.extrafanart_deal_set = set()
        self.extrafanart_copy_deal_set = set()
        self.trailer_deal_set = set()
        self.theme_videos_deal_set = set()
        self.nfo_deal_set = set()
        self.json_get_set = set()
        self.json_data_dic = {}
        self.img_path = ""
        self.deepl_result = {}
        self.stop_flag = False


Flags = _Flags()
