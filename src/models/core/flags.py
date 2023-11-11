"""
用于刮削过程控制的标志位
此模块不应依赖任何项目代码
"""
from models.entity.enums import FileMode


class Flags:
    translate_by_list = []
    rest_time_convert = None
    rest_time_convert_ = None
    appoint_url = None
    total_kills = 0
    now_kill = 0
    success_save_time = None
    pool = None
    next_start_time = None
    lock = None
    count_claw = 0  # 批量刮削次数
    can_save_remain = False  # 保存剩余任务
    remain_list = []
    new_again_dic = {}
    again_dic = {}  # 待重新刮削的字典
    start_time = None
    file_mode = FileMode.Default  # 默认刮削待刮削目录
    counting_order = 0  # 刮削顺序
    total_count = 0  # 总数
    rest_now_begin_count = 0  # 本轮刮削开始统计的线程序号（实际-1）
    rest_sleepping = False  # 是否休眠中
    scrape_starting = 0  # 已进入过刮削流程的数量
    scrape_started = 0  # 已进入过刮削流程并开始的数量
    scrape_done = 0  # 已完成刮削数量
    succ_count = 0  # 成功数量
    fail_count = 0  # 失败数量
    file_new_path_dic = {}  # 所有文件最终输出路径的字典（如已存在，则视为重复文件，直接跳过）
    pic_catch_set = set()  # 当前文件的图片最终输出路径的字典（如已存在，则最终图片文件视为已处理过）
    file_done_dic = {}  # 当前番号的图片已下载完成的标识（如已存在，视为图片已下载完成）
    extrafanart_deal_set = set()  # 当前文件夹剧照已处理的标识（如已存在，视为剧照已处理过）
    extrafanart_copy_deal_set = set()  # 当前文件夹剧照副本已下载的标识（如已存在，视为剧照已处理过）
    trailer_deal_set = set()  # 当前文件trailer已处理的标识（如已存在，视为剧照已处理过）
    theme_videos_deal_set = set()  # 当前文件夹剧照已下载的标识（如已存在，视为剧照已处理过）
    nfo_deal_set = set()  # 当前文件nfo已处理的标识（如已存在，视为剧照已处理过）
    json_get_set = set()  # 去获取json的番号列表
    json_data_dic = {}  # 获取成功的json
    img_path = ''
    deepl_result = {}  # deep 翻译结果（当没有填写api时，使用第三方翻译模块，作用是实现超时自动退出，避免卡死）
    failed_list = []  # 失败文件和错误原因记录
    failed_file_list = []  # 失败文件记录
    stop_flag = False  # 线程停止标识
    single_file_path = ''  # 工具单文件刮削的文件路径
    website_name = ''
    scrape_start_time = None
    success_list = set()
    threads_list = []  # 开启的线程列表
    stop_other = True  # 非刮削线程停止标识
    local_number_flag = ''  # 启动后本地数据库是否扫描过
    actor_numbers_dic = {}  # 每个演员所有番号的字典
    local_number_set = set()  # 本地所有番号的集合
    local_number_cnword_set = set()  # 本地所有有字幕的番号的集合
    current_proxy = None  # 代理信息
    log_txt = None  # 日志文件对象
    scrape_like_text = None
    main_mode_text = None
