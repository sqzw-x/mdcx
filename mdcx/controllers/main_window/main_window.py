import os
import re
import shutil
import threading
import time
import traceback
import webbrowser
from typing import TYPE_CHECKING, Literal, cast

from PyQt5.QtCore import QEvent, QPoint, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QCursor, QHoverEvent, QIcon, QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QShortcut,
    QSystemTrayIcon,
    QTreeWidgetItem,
)

from mdcx.config.extend import deal_url, get_movie_path_setting
from mdcx.config.manager import config, manager
from mdcx.config.resources import resources
from mdcx.consts import IS_WINDOWS, LOCAL_VERSION, MARK_FILE
from mdcx.controllers.cut_window import CutWindow
from mdcx.controllers.main_window.handlers import show_netstatus
from mdcx.controllers.main_window.init import Init_QSystemTrayIcon, Init_Singal, Init_Ui, init_QTreeWidget
from mdcx.controllers.main_window.load_config import load_config
from mdcx.controllers.main_window.save_config import save_config
from mdcx.controllers.main_window.style import set_dark_style, set_style
from mdcx.image import get_pixmap
from mdcx.manual import ManualConfig
from mdcx.models.base.file import (
    check_and_clean_files,
    get_success_list,
    movie_lists,
    newtdisk_creat_symlink,
    save_remain_list,
    save_success_list,
)
from mdcx.models.base.image import add_del_extrafanart_copy
from mdcx.models.base.video import add_del_extras, add_del_theme_videos
from mdcx.models.base.web import check_theporndb_api_token, check_version, get_avsox_domain, ping_host
from mdcx.models.base.web_sync import get_text_sync
from mdcx.models.core.nfo import write_nfo
from mdcx.models.core.scraper import again_search, get_remain_list, start_new_scrape
from mdcx.models.enums import FileMode
from mdcx.models.flags import Flags
from mdcx.models.log_buffer import LogBuffer
from mdcx.models.tools.actress_db import ActressDB
from mdcx.models.tools.emby_actor_image import update_emby_actor_photo
from mdcx.models.tools.emby_actor_info import creat_kodi_actors, show_emby_actor_list, update_emby_actor_info
from mdcx.models.tools.missing import check_missing_number
from mdcx.models.tools.subtitle import add_sub_for_all_video
from mdcx.models.types import CrawlersResult, FileInfo, OtherInfo, ShowData
from mdcx.signals import signal_qt
from mdcx.utils import _async_raise, add_html, convert_path, get_current_time, get_used_time, kill_a_thread, split_path
from mdcx.utils.file import delete_file_sync, open_file_thread
from mdcx.utils.path import get_path
from mdcx.views.MDCx import Ui_MDCx

if TYPE_CHECKING:
    from PyQt5.QtGui import QMouseEvent


class MyMAinWindow(QMainWindow):
    # region 信号量
    main_logs_show = pyqtSignal(str)  # 显示刮削日志信号
    main_logs_clear = pyqtSignal(str)  # 清空刮削日志信号
    req_logs_clear = pyqtSignal(str)  # 清空请求日志信号
    main_req_logs_show = pyqtSignal(str)  # 显示刮削后台日志信号
    net_logs_show = pyqtSignal(str)  # 显示网络检测日志信号
    set_javdb_cookie = pyqtSignal(str)  # 加载javdb cookie文本内容到设置页面
    set_javbus_cookie = pyqtSignal(str)  # 加载javbus cookie文本内容到设置页面
    set_javbus_status = pyqtSignal(str)  # javbus 检查状态更新
    set_label_file_path = pyqtSignal(str)  # 主界面更新路径信息显示
    set_pic_pixmap = pyqtSignal(list, list)  # 主界面显示封面、缩略图
    set_pic_text = pyqtSignal(str)  # 主界面显示封面信息
    change_to_mainpage = pyqtSignal(str)  # 切换到主界面
    label_result = pyqtSignal(str)
    pushButton_start_cap = pyqtSignal(str)
    pushButton_start_cap2 = pyqtSignal(str)
    pushButton_start_single_file = pyqtSignal(str)
    pushButton_add_sub_for_all_video = pyqtSignal(str)
    pushButton_show_pic_actor = pyqtSignal(str)
    pushButton_add_actor_info = pyqtSignal(str)
    pushButton_add_actor_pic = pyqtSignal(str)
    pushButton_add_actor_pic_kodi = pyqtSignal(str)
    pushButton_del_actor_folder = pyqtSignal(str)
    pushButton_check_and_clean_files = pyqtSignal(str)
    pushButton_move_mp4 = pyqtSignal(str)
    pushButton_find_missing_number = pyqtSignal(str)
    label_show_version = pyqtSignal(str)

    # endregion

    def __init__(self, parent=None):
        super().__init__(parent)

        # region 初始化需要的变量
        self.localversion = LOCAL_VERSION  # 当前版本号
        self.new_version = "\n🔍 点击检查最新版本"  # 有版本更新时在左下角显示的新版本信息
        self.show_data: ShowData | None = None  # 当前树状图选中文件的数据
        self.img_path = ""  # 当前树状图选中文件的图片地址
        self.m_drag = False  # 允许鼠标拖动的标识
        self.m_DragPosition: QPoint  # 鼠标拖动位置
        self.logs_counts = 0  # 日志次数（每1w次清屏）
        self.req_logs_counts = 0  # 日志次数（每1w次清屏）
        self.file_main_open_path = ""  # 主界面打开的文件路径
        self.json_array: dict[str, ShowData] = {}  # 主界面右侧结果树状数据

        self.window_radius = 0  # 窗口四角弧度，为0时表示显示窗口标题栏
        self.window_border = 0  # 窗口描边，为0时表示显示窗口标题栏
        self.dark_mode = False  # 暗黑模式标识
        self.check_mac = True  # 检测配置目录
        # self.window_marjin = 0 窗口外边距，为0时不往里缩
        self.show_flag = True  # 是否加载刷新样式

        self.timer = QTimer()  # 初始化一个定时器，用于显示日志
        self.timer.timeout.connect(self.show_detail_log)
        self.timer.start(100)  # 设置间隔100毫秒
        self.timer_scrape = QTimer()  # 初始化一个定时器，用于间隔刮削
        self.timer_scrape.timeout.connect(self.auto_scrape)
        self.timer_update = QTimer()  # 初始化一个定时器，用于检查更新
        self.timer_update.timeout.connect(check_version)
        self.timer_update.start(43200000)  # 设置检查间隔12小时
        self.timer_remain_task = QTimer()  # 初始化一个定时器，用于显示保存剩余任务
        self.timer_remain_task.timeout.connect(save_remain_list)
        self.timer_remain_task.start(1500)  # 设置间隔1.5秒
        self.atuo_scrape_count = 0  # 循环刮削次数
        # endregion

        # region 其它属性声明
        self.threads_list: list[threading.Thread] = []  # 启动的线程列表
        self.start_click_time = 0
        self.start_click_pos: QPoint
        self.window_marjin = None
        self.now_show_name = None
        self.show_name = None
        self.t_net = None
        self.options: QFileDialog.Options | QFileDialog.Option
        self.tray_icon: QSystemTrayIcon
        self.item_succ: QTreeWidgetItem
        self.item_fail: QTreeWidgetItem
        # endregion

        # region 初始化 UI
        resources.get_fonts()
        self.Ui = Ui_MDCx()  # 实例化 Ui
        self.Ui.setupUi(self)  # 初始化 Ui
        self.cutwindow = CutWindow(self)
        self.Init_Singal()  # 信号连接
        self.Init_Ui()  # 设置Ui初始状态
        self.load_config()  # 加载配置
        get_success_list()  # 获取历史成功刮削列表
        # endregion

        # region 启动显示信息和后台检查更新
        self.show_scrape_info()  # 主界面左下角显示一些配置信息
        self.show_net_info("\n🏠 代理设置在:【设置】 - 【网络】 - 【代理设置】。\n")  # 检查网络界面显示提示信息
        show_netstatus()  # 检查网络界面显示当前网络代理信息
        self.show_net_info(
            "\n💡 说明：\n "
            "任意代理：javbus、jav321、javlibrary、mywife、giga、freejavbt、"
            "mdtv、madouqu、7mmtv、faleno、dahlia、prestige、theporndb、cnmdb、fantastica、kin8\n "
            "非日本代理：javdb、airav-cc、avsex（日本代理会报错）\n "
            "日本代理：seesaawiki、mgstage\n "
            "无需代理：avsex、hdouban、iqqtv、airav-wiki、love6、lulubar、fc2、fc2club、fc2hub\n\n"
            "▶️ 点击右上角 【开始检测】按钮以测试网络连通性。"
        )  # 检查网络界面显示提示信息
        signal_qt.add_log("🍯 你可以点击左下角的图标来 显示 / 隐藏 请求信息面板！")
        self.show_version()  # 日志页面显示版本信息
        self.creat_right_menu()  # 加载右键菜单
        self.pushButton_main_clicked()  # 切换到主界面
        self.auto_start()  # 自动开始刮削
        # endregion

    # region Init
    def Init_Ui(self): ...

    def Init_Singal(self): ...

    def Init_QSystemTrayIcon(self): ...

    def init_QTreeWidget(self): ...

    def load_config(self): ...

    def creat_right_menu(self):
        self.menu_start = QAction(QIcon(resources.start_icon), "  开始刮削\tS", self)
        self.menu_stop = QAction(QIcon(resources.stop_icon), "  停止刮削\tS", self)
        self.menu_number = QAction(QIcon(resources.input_number_icon), "  重新刮削\tN", self)
        self.menu_website = QAction(QIcon(resources.input_website_icon), "  输入网址重新刮削\tU", self)
        self.menu_del_file = QAction(QIcon(resources.del_file_icon), "  删除文件\tD", self)
        self.menu_del_folder = QAction(QIcon(resources.del_folder_icon), "  删除文件和文件夹\tA", self)
        self.menu_folder = QAction(QIcon(resources.open_folder_icon), "  打开文件夹\tF", self)
        self.menu_nfo = QAction(QIcon(resources.open_nfo_icon), "  编辑 NFO\tE", self)
        self.menu_play = QAction(QIcon(resources.play_icon), "  播放\tP", self)
        self.menu_hide = QAction(QIcon(resources.hide_boss_icon), "  隐藏\tQ", self)

        self.menu_start.triggered.connect(self.pushButton_start_scrape_clicked)
        self.menu_stop.triggered.connect(self.pushButton_start_scrape_clicked)
        self.menu_number.triggered.connect(self.search_by_number_clicked)
        self.menu_website.triggered.connect(self.search_by_url_clicked)
        self.menu_del_file.triggered.connect(self.main_del_file_click)
        self.menu_del_folder.triggered.connect(self.main_del_folder_click)
        self.menu_folder.triggered.connect(self.main_open_folder_click)
        self.menu_nfo.triggered.connect(self.main_open_nfo_click)
        self.menu_play.triggered.connect(self.main_play_click)
        self.menu_hide.triggered.connect(self.hide)

        QShortcut(QKeySequence(self.tr("N")), self, self.search_by_number_clicked)
        QShortcut(QKeySequence(self.tr("U")), self, self.search_by_url_clicked)
        QShortcut(QKeySequence(self.tr("D")), self, self.main_del_file_click)
        QShortcut(QKeySequence(self.tr("A")), self, self.main_del_folder_click)
        QShortcut(QKeySequence(self.tr("F")), self, self.main_open_folder_click)
        QShortcut(QKeySequence(self.tr("E")), self, self.main_open_nfo_click)
        QShortcut(QKeySequence(self.tr("P")), self, self.main_play_click)
        QShortcut(QKeySequence(self.tr("S")), self, self.pushButton_start_scrape_clicked)
        QShortcut(QKeySequence(self.tr("Q")), self, self.hide)
        # QShortcut(QKeySequence(self.tr("Esc")), self, self.hide)
        QShortcut(QKeySequence(self.tr("Ctrl+M")), self, self.pushButton_min_clicked2)
        QShortcut(QKeySequence(self.tr("Ctrl+W")), self, self.ready_to_exit)

        self.Ui.page_main.setContextMenuPolicy(Qt.CustomContextMenu)
        self.Ui.page_main.customContextMenuRequested.connect(self._menu)

    def _menu(self, pos=None):
        if not pos:
            pos = self.Ui.pushButton_right_menu.pos() + QPoint(40, 10)
            # pos = QCursor().pos()
        menu = QMenu()
        if self.file_main_open_path:
            file_name = split_path(self.file_main_open_path)[1]
            menu.addAction(QAction(file_name, self))
            menu.addSeparator()
        else:
            menu.addAction(QAction("请刮削后使用！", self))
            menu.addSeparator()
            if self.Ui.pushButton_start_cap.text() != "开始":
                menu.addAction(self.menu_stop)
            else:
                menu.addAction(self.menu_start)
        menu.addAction(self.menu_number)
        menu.addAction(self.menu_website)
        menu.addSeparator()
        menu.addAction(self.menu_del_file)
        menu.addAction(self.menu_del_folder)
        menu.addSeparator()
        menu.addAction(self.menu_folder)
        menu.addAction(self.menu_nfo)
        menu.addAction(self.menu_play)
        menu.addAction(self.menu_hide)
        menu.exec_(self.Ui.page_main.mapToGlobal(pos))
        # menu.move(pos)
        # menu.show()

    # endregion

    # region 窗口操作
    def tray_icon_click(self, e):
        if int(e) == 3 and IS_WINDOWS:
            if self.isVisible():
                self.hide()
            else:
                self.activateWindow()
                self.raise_()
                self.show()

    def tray_icon_show(self):
        if int(self.windowState()) == 1:  # 最小化时恢复
            self.showNormal()
        self.recover_windowflags()  # 恢复焦点
        self.activateWindow()
        self.raise_()
        self.show()

    def change_mainpage(self, t):
        self.pushButton_main_clicked()

    def eventFilter(self, a0, a1):
        # print(event.type())

        if a1.type() == 3:  # 松开鼠标，检查是否在前台
            self.recover_windowflags()
        if a1.type() == 121 and not self.isVisible():
            self.show()
        if a0.objectName() == "label_poster" or a0.objectName() == "label_thumb":
            if a1.type() == QEvent.Type.MouseButtonPress:
                a1 = cast("QMouseEvent", a1)
                if a1.button() == Qt.MouseButton.LeftButton:
                    self.start_click_time = time.time()
                    self.start_click_pos = a1.globalPos()
            elif a1.type() == QEvent.Type.MouseButtonRelease:
                a1 = cast("QMouseEvent", a1)
                if a1.button() == Qt.MouseButton.LeftButton:
                    if not bool(a1.globalPos() - self.start_click_pos) or (time.time() - self.start_click_time < 0.05):
                        self._pic_main_clicked()
        if a0 is self.Ui.textBrowser_log_main.viewport() or a0 is self.Ui.textBrowser_log_main_2.viewport():
            if not self.Ui.textBrowser_log_main_3.isHidden() and a1.type() == QEvent.Type.MouseButtonPress:
                self.Ui.textBrowser_log_main_3.hide()
                self.Ui.pushButton_scraper_failed_list.hide()
                self.Ui.pushButton_save_failed_list.hide()
        return super().eventFilter(a0, a1)

    def showEvent(self, a0):
        self.resize(1030, 700)  # 调整窗口大小

    # 当隐藏边框时，最小化后，点击任务栏时，需要监听事件，在恢复窗口时隐藏边框
    def changeEvent(self, a0):
        # self.show_traceback_log(QEvent.WindowStateChange)
        # WindowState （WindowNoState=0 正常窗口; WindowMinimized= 1 最小化;
        # WindowMaximized= 2 最大化; WindowFullScreen= 3 全屏;WindowActive= 8 可编辑。）
        # windows平台无问题，仅mac平台python版有问题
        if (
            not IS_WINDOWS
            and self.window_radius
            and a0.type() == QEvent.Type.WindowStateChange
            and not int(self.windowState())
        ):
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)  # 隐藏边框
            self.show()

        # activeAppName = AppKit.NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName'] # 活动窗口的标题

    def closeEvent(self, a0):
        self.ready_to_exit()
        if a0:
            a0.ignore()

    # 显示与隐藏窗口标题栏
    def _windows_auto_adjust(self):
        if config.window_title == "hide":  # 隐藏标题栏
            if self.window_radius == 0:
                self.show_flag = True
            self.window_radius = 5
            if IS_WINDOWS:
                self.window_border = 1
            else:
                self.window_border = 0
            self.setWindowFlag(Qt.FramelessWindowHint, True)  # 隐藏标题栏
            self.Ui.pushButton_close.setVisible(True)
            self.Ui.pushButton_min.setVisible(True)
            self.Ui.widget_buttons.move(0, 50)

        else:  # 显示标题栏
            if self.window_radius == 5:
                self.show_flag = True
            self.window_radius = 0
            self.window_border = 0
            self.window_marjin = 0
            self.setWindowFlag(Qt.FramelessWindowHint, False)  # 显示标题栏
            self.Ui.pushButton_close.setVisible(False)
            self.Ui.pushButton_min.setVisible(False)
            self.Ui.widget_buttons.move(0, 20)

        if bool(self.dark_mode != self.Ui.checkBox_dark_mode.isChecked()):
            self.show_flag = True
            self.dark_mode = self.Ui.checkBox_dark_mode.isChecked()

        if self.show_flag:
            self.show_flag = False
            self.set_style()  # 样式美化

            # self.setWindowState(Qt.WindowNoState)                               # 恢复正常窗口
            self.show()
            self._change_page()

    def _change_page(self):
        page = int(self.Ui.stackedWidget.currentIndex())
        if page == 0:
            self.pushButton_main_clicked()
        elif page == 1:
            self.pushButton_show_log_clicked()
        elif page == 2:
            self.pushButton_show_net_clicked()
        elif page == 3:
            self.pushButton_tool_clicked()
        elif page == 4:
            self.pushButton_setting_clicked()
        elif page == 5:
            self.pushButton_about_clicked()

    def set_style(self): ...

    def set_dark_style(self): ...

    # region 拖动窗口
    # 按下鼠标
    def mousePressEvent(self, a0):
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.m_drag = True
            self.m_DragPosition = a0.globalPos() - self.pos()
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))  # 按下左键改变鼠标指针样式为手掌

    # 松开鼠标
    def mouseReleaseEvent(self, a0):
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.m_drag = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  # 释放左键改变鼠标指针样式为箭头

    # 拖动鼠标
    def mouseMoveEvent(self, a0):
        if a0 and self.m_drag:
            self.move(a0.globalPos() - self.m_DragPosition)
            a0.accept()

    # endregion

    # region 关闭
    # 关闭按钮点击事件响应函数
    def pushButton_close_clicked(self):
        if "hide_close" in config.switch_on:
            self.hide()
        else:
            self.ready_to_exit()

    def ready_to_exit(self):
        if "show_dialog_exit" in config.switch_on:
            if not self.isVisible():
                self.show()
            if int(self.windowState()) == 1:
                self.showNormal()

            # print(self.window().isActiveWindow()) # 是否为活动窗口
            self.raise_()
            box = QMessageBox(QMessageBox.Warning, "退出", "确定要退出吗？")
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.button(QMessageBox.Yes).setText("退出 MDCx")
            box.button(QMessageBox.No).setText("取消")
            box.setDefaultButton(QMessageBox.No)
            reply = box.exec()
            if reply != QMessageBox.Yes:
                self.raise_()
                self.show()
                return
        self.exit_app()

    # 关闭窗口
    def exit_app(self):
        show_poster = config.show_poster
        switch_on = config.switch_on
        need_save_config = False

        if bool(self.Ui.checkBox_cover.isChecked()) != bool(show_poster):
            config.show_poster = self.Ui.checkBox_cover.isChecked()
            need_save_config = True
        if self.Ui.textBrowser_log_main_2.isHidden() == bool("show_logs" in switch_on):
            if self.Ui.textBrowser_log_main_2.isHidden():
                config.switch_on = switch_on.replace("show_logs,", "")
            else:
                config.switch_on = switch_on + "show_logs,"
            need_save_config = True
        if need_save_config:
            try:
                manager.save()
            except Exception:
                signal_qt.show_traceback_log(traceback.format_exc())
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
        signal_qt.show_traceback_log("\n\n\n\n************ 程序正常退出！************\n")
        os._exit(0)

    # endregion

    # 最小化窗口
    def pushButton_min_clicked(self):
        if "hide_mini" in config.switch_on:
            self.hide()
            return
        # mac 平台 python 版本 最小化有问题，此处就是为了兼容它，需要先设置为显示窗口标题栏才能最小化
        if not IS_WINDOWS:
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, False)  # 不隐藏边框

        # self.setWindowState(Qt.WindowMinimized)
        # self.show_traceback_log(self.isMinimized())
        self.showMinimized()

    def pushButton_min_clicked2(self):
        if not IS_WINDOWS:
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, False)  # 不隐藏边框
            # self.show()  # 加上后可以显示缩小动画
        self.showMinimized()

    # 重置左侧按钮样式
    def set_left_button_style(self):
        try:
            if self.dark_mode:
                self.Ui.left_backgroud_widget.setStyleSheet(
                    f"background: #1F272F;border-right: 1px solid #20303F;border-top-left-radius: {self.window_radius}px;border-bottom-left-radius: {self.window_radius}px;"
                )
                self.Ui.pushButton_main.setStyleSheet(
                    "QPushButton:hover#pushButton_main{color: white;background-color: rgba(160,160,165,40);}"
                )
                self.Ui.pushButton_log.setStyleSheet(
                    "QPushButton:hover#pushButton_log{color: white;background-color: rgba(160,160,165,40);}"
                )
                self.Ui.pushButton_net.setStyleSheet(
                    "QPushButton:hover#pushButton_net{color: white;background-color: rgba(160,160,165,40);}"
                )
                self.Ui.pushButton_tool.setStyleSheet(
                    "QPushButton:hover#pushButton_tool{color: white;background-color: rgba(160,160,165,40);}"
                )
                self.Ui.pushButton_setting.setStyleSheet(
                    "QPushButton:hover#pushButton_setting{color: white;background-color: rgba(160,160,165,40);}"
                )
                self.Ui.pushButton_about.setStyleSheet(
                    "QPushButton:hover#pushButton_about{color: white;background-color: rgba(160,160,165,40);}"
                )
            else:
                self.Ui.pushButton_main.setStyleSheet(
                    "QPushButton:hover#pushButton_main{color: black;background-color: rgba(160,160,165,40);}"
                )
                self.Ui.pushButton_log.setStyleSheet(
                    "QPushButton:hover#pushButton_log{color: black;background-color: rgba(160,160,165,40);}"
                )
                self.Ui.pushButton_net.setStyleSheet(
                    "QPushButton:hover#pushButton_net{color: black;background-color: rgba(160,160,165,40);}"
                )
                self.Ui.pushButton_tool.setStyleSheet(
                    "QPushButton:hover#pushButton_tool{color: black;background-color: rgba(160,160,165,40);}"
                )
                self.Ui.pushButton_setting.setStyleSheet(
                    "QPushButton:hover#pushButton_setting{color: black;background-color: rgba(160,160,165,40);}"
                )
                self.Ui.pushButton_about.setStyleSheet(
                    "QPushButton:hover#pushButton_about{color: black;background-color: rgba(160,160,165,40);}"
                )
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())

    # endregion

    # region 显示版本号
    def show_version(self):
        try:
            t = threading.Thread(target=self._show_version_thread)
            t.start()  # 启动线程,即让线程开始执行
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
            signal_qt.show_log_text(traceback.format_exc())

    def _show_version_thread(self):
        version_info = f"基于 MDC-GUI 修改 当前版本: {self.localversion}"
        download_link = ""
        latest_version = check_version()
        if latest_version:
            if int(self.localversion) < int(latest_version):
                self.new_version = f"\n🍉 有新版本了！（{latest_version}）"
                signal_qt.show_scrape_info()
                self.Ui.label_show_version.setCursor(Qt.OpenHandCursor)  # 设置鼠标形状为十字形
                version_info = f'基于 MDC-GUI 修改 · 当前版本: {self.localversion} （ <font color="red" >最新版本是: {latest_version}，请及时更新！🚀 </font>）'
                download_link = ' ⬇️ <a href="https://github.com/sqzw-x/mdcx/releases">下载新版本</a>'
            else:
                version_info = f'基于 MDC-GUI 修改 · 当前版本: {self.localversion} （ <font color="green">你使用的是最新版本！🎉 </font>）'

        feedback = ' 💌 问题反馈: <a href="https://github.com/sqzw-x/mdcx/issues/new">GitHub Issues</a>'

        # 显示版本信息和反馈入口
        signal_qt.show_log_text(version_info)
        if feedback or download_link:
            self.main_logs_show.emit(f"{feedback}{download_link}")
        signal_qt.show_log_text("================================================================================")
        self.pushButton_check_javdb_cookie_clicked()  # 检测javdb cookie
        self.pushButton_check_javbus_cookie_clicked()  # 检测javbus cookie
        if config.use_database:
            ActressDB.init_db()
        try:
            t = threading.Thread(target=check_theporndb_api_token)
            t.start()  # 启动线程,即让线程开始执行
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
            signal_qt.show_log_text(traceback.format_exc())

    # endregion

    # region 各种点击跳转浏览器
    def label_version_clicked(self, ev):
        try:
            if "🔍" in self.new_version:
                webbrowser.open("https://github.com/sqzw-x/mdcx/releases/tag/daily_release")
            else:
                webbrowser.open("https://github.com/sqzw-x/mdcx/releases")
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())

    # endregion

    # region 左侧切换页面
    # 点左侧的主界面按钮
    def pushButton_main_clicked(self):
        self.Ui.left_backgroud_widget.setStyleSheet(
            f"background: #F5F5F6;border-right: 1px solid #EDEDED;border-top-left-radius: {self.window_radius}px;border-bottom-left-radius: {self.window_radius}px;"
        )
        self.Ui.stackedWidget.setCurrentIndex(0)
        self.set_left_button_style()
        self.Ui.pushButton_main.setStyleSheet("font-weight: bold; background-color: rgba(160,160,165,60);")

    # 点左侧的日志按钮
    def pushButton_show_log_clicked(self):
        self.Ui.left_backgroud_widget.setStyleSheet(
            f"background: #EFFFFC;border-right: 1px solid #EDEDED;border-top-left-radius: {self.window_radius}px;border-bottom-left-radius: {self.window_radius}px;"
        )
        self.Ui.stackedWidget.setCurrentIndex(1)
        self.set_left_button_style()
        self.Ui.pushButton_log.setStyleSheet(
            "font-weight: bold; background-color: rgba(160,160,165,60);"
        )  # self.Ui.textBrowser_log_main.verticalScrollBar().setValue(  #     self.Ui.textBrowser_log_main.verticalScrollBar().maximum())  # self.Ui.textBrowser_log_main_2.verticalScrollBar().setValue(  #     self.Ui.textBrowser_log_main_2.verticalScrollBar().maximum())

    # 点左侧的工具按钮
    def pushButton_tool_clicked(self):
        self.Ui.left_backgroud_widget.setStyleSheet(
            f"background: #FFEFF6;border-right: 1px solid #EDEDED;border-top-left-radius: {self.window_radius}px;border-bottom-left-radius: {self.window_radius}px;"
        )
        self.Ui.stackedWidget.setCurrentIndex(3)
        self.set_left_button_style()
        self.Ui.pushButton_tool.setStyleSheet("font-weight: bold; background-color: rgba(160,160,165,60);")

    # 点左侧的设置按钮
    def pushButton_setting_clicked(self):
        self.Ui.left_backgroud_widget.setStyleSheet(
            f"background: #84CE9A;border-right: 1px solid #EDEDED;border-top-left-radius: {self.window_radius}px;border-bottom-left-radius: {self.window_radius}px;"
        )
        self.Ui.stackedWidget.setCurrentIndex(4)
        self.set_left_button_style()
        try:
            if self.dark_mode:
                self.Ui.pushButton_setting.setStyleSheet("font-weight: bold; background-color: rgba(160,160,165,60);")
            else:
                self.Ui.pushButton_setting.setStyleSheet("font-weight: bold; background-color: rgba(160,160,165,100);")
            self._check_mac_config_folder()
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())

    # 点击左侧【检测网络】按钮，切换到检测网络页面
    def pushButton_show_net_clicked(self):
        self.Ui.left_backgroud_widget.setStyleSheet(
            f"background: #E1F2FF;border-right: 1px solid #EDEDED;border-top-left-radius: {self.window_radius}px;border-bottom-left-radius: {self.window_radius}px;"
        )
        self.Ui.stackedWidget.setCurrentIndex(2)
        self.set_left_button_style()
        self.Ui.pushButton_net.setStyleSheet("font-weight: bold; background-color: rgba(160,160,165,60);")

    # 点左侧的关于按钮
    def pushButton_about_clicked(self):
        self.Ui.left_backgroud_widget.setStyleSheet(
            f"background: #FFEFEF;border-right: 1px solid #EDEDED;border-top-left-radius: {self.window_radius}px;border-bottom-left-radius: {self.window_radius}px;"
        )
        self.Ui.stackedWidget.setCurrentIndex(5)
        self.set_left_button_style()
        self.Ui.pushButton_about.setStyleSheet("font-weight: bold; background-color: rgba(160,160,165,60);")

    # endregion

    # region 主界面
    # 开始刮削按钮
    def pushButton_start_scrape_clicked(self):
        if self.Ui.pushButton_start_cap.text() == "开始":
            if not get_remain_list():
                start_new_scrape(FileMode.Default)
        elif self.Ui.pushButton_start_cap.text() == "■ 停止":
            self.pushButton_stop_scrape_clicked()

    # 停止确认弹窗
    def pushButton_stop_scrape_clicked(self):
        if "show_dialog_stop_scrape" in config.switch_on:
            box = QMessageBox(QMessageBox.Warning, "停止刮削", "确定要停止刮削吗？")
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.button(QMessageBox.Yes).setText("停止刮削")
            box.button(QMessageBox.No).setText("取消")
            box.setDefaultButton(QMessageBox.No)
            reply = box.exec()
            if reply != QMessageBox.Yes:
                return
        if self.Ui.pushButton_start_cap.text() == "■ 停止":
            config.executor.run(save_success_list())
            Flags.rest_time_convert_ = Flags.rest_time_convert
            Flags.rest_time_convert = 0
            self.Ui.pushButton_start_cap.setText(" ■ 停止中 ")
            self.Ui.pushButton_start_cap2.setText(" ■ 停止中 ")
            signal_qt.show_scrape_info("⛔️ 刮削停止中...")
            config.executor.cancel_async()  # 取消异步任务
            t = threading.Thread(target=self._kill_threads)  # 关闭线程池
            t.start()

    # 显示停止信息
    def _show_stop_info(self):
        signal_qt.reset_buttons_status.emit()
        try:
            Flags.rest_time_convert = Flags.rest_time_convert_
            if Flags.stop_other:
                signal_qt.show_scrape_info("⛔️ 已手动停止！")
                signal_qt.show_log_text(
                    "⛔️ 已手动停止！\n================================================================================"
                )
                self.set_label_file_path.emit("⛔️ 已手动停止！")
                return
            signal_qt.exec_set_processbar.emit(0)
            end_time = time.time()
            used_time = str(round((end_time - Flags.start_time), 2))
            if Flags.scrape_done:
                average_time = str(round((end_time - Flags.start_time) / Flags.scrape_done, 2))
            else:
                average_time = used_time
            signal_qt.show_scrape_info("⛔️ 刮削已手动停止！")
            self.set_label_file_path.emit(
                f"⛔️ 刮削已手动停止！\n   已刮削 {Flags.scrape_done} 个视频, 还剩余 {Flags.total_count - Flags.scrape_done} 个! 刮削用时 {used_time} 秒"
            )
            signal_qt.show_log_text(
                f"\n ⛔️ 刮削已手动停止！\n 😊 已刮削 {Flags.scrape_done} 个视频, 还剩余 {Flags.total_count - Flags.scrape_done} 个! 刮削用时 {used_time} 秒, 停止用时 {self.stop_used_time} 秒"
            )
            signal_qt.show_log_text("================================================================================")
            signal_qt.show_log_text(
                " ⏰ Start time".ljust(13) + ": " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(Flags.start_time))
            )
            signal_qt.show_log_text(
                " 🏁 End time".ljust(13) + ": " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
            )
            signal_qt.show_log_text(f"{' ⏱ Used time'.ljust(13)}: {used_time}S")
            signal_qt.show_log_text(f"{' 🍕 Per time'.ljust(13)}: {average_time}S")
            signal_qt.show_log_text("================================================================================")
            Flags.again_dic.clear()
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
            signal_qt.show_log_text(traceback.format_exc())
        print(threading.enumerate())

    def show_stop_info_thread(
        self,
    ):
        t = threading.Thread(target=self._show_stop_info)
        t.start()

    # 关闭线程池和扫描线程
    def _kill_threads(self):
        Flags.total_kills = len(self.threads_list)
        Flags.now_kill = 0
        start_time = time.time()
        self.set_label_file_path.emit(f"⛔️ 正在停止刮削...\n   正在停止已在运行的任务线程（1/{Flags.total_kills}）...")
        signal_qt.show_log_text(
            f"\n ⛔️ {get_current_time()} 已停止添加新的刮削任务，正在停止已在运行的任务线程（{Flags.total_kills}）..."
        )
        signal_qt.show_traceback_log(f"⛔️ 正在停止正在运行的任务线程 ({Flags.total_kills}) ...")
        i = 0
        for each in self.threads_list:
            i += 1
            signal_qt.show_traceback_log(f"正在停止线程: {i}/{Flags.total_kills} {each.name} ...")
        signal_qt.show_traceback_log(
            "线程正在停止中，请稍后...\n 🍯 停止时间与线程数量及线程正在执行的任务有关，比如正在执行网络请求、文件下载等IO操作时，需要等待其释放资源。。。\n"
        )
        signal_qt.stop = True
        for each in self.threads_list:  # 线程池的线程
            kill_a_thread(each)
            while each.is_alive():
                pass

        signal_qt.stop = False
        self.stop_used_time = get_used_time(start_time)
        signal_qt.show_log_text(f" 🕷 {get_current_time()} 已停止线程：{Flags.total_kills}/{Flags.total_kills}")
        signal_qt.show_traceback_log(f"所有线程已停止！！！({self.stop_used_time}s)\n ⛔️ 刮削已手动停止！\n")
        signal_qt.show_log_text(f" ⛔️ {get_current_time()} 所有线程已停止！({self.stop_used_time}s)")
        thread_remain_list = []
        [thread_remain_list.append(i.getName()) for i in threading.enumerate()]  # 剩余线程名字列表
        thread_remain = ", ".join(thread_remain_list)
        print(f"✅ 剩余线程 ({len(thread_remain_list)}): {thread_remain}")
        self.show_stop_info_thread()

    # 进度条
    def set_processbar(self, value):
        self.Ui.progressBar_scrape.setProperty("value", value)

    # region 刮削结果显示
    def _addTreeChild(self, result, filename):
        node = QTreeWidgetItem()
        node.setText(0, filename)
        if result == "succ":
            self.item_succ.addChild(node)
        else:
            self.item_fail.addChild(node)
        # self.Ui.treeWidget_number.verticalScrollBar().setValue(self.Ui.treeWidget_number.verticalScrollBar().maximum())
        # self.Ui.treeWidget_number.setCurrentItem(node)
        # self.Ui.treeWidget_number.scrollToItem(node)

    def show_list_name(self, status: Literal["succ", "fail"], show_data: ShowData, real_number=""):
        # 添加树状节点
        self._addTreeChild(status, show_data.show_name)

        if not show_data.data.title:
            show_data.data.title = LogBuffer.error().get()
            show_data.data.number = real_number
        self.show_name = show_data.show_name
        self.set_main_info(show_data)
        self.json_array[show_data.show_name] = show_data

    def set_main_info(self, show_data: "ShowData | None"):
        if show_data is not None:
            self.show_data = show_data
            file_info = show_data.file_info
            data = show_data.data
            other = show_data.other
            self.show_name = show_data.show_name
        else:
            file_info = FileInfo.empty()
            data = CrawlersResult.empty()
            other = OtherInfo.empty()
            self.show_name = None
        try:
            number = data.number
            self.Ui.label_number.setToolTip(number)
            if len(number) > 11:
                number = number[:10] + "……"
            self.Ui.label_number.setText(number)
            actor = str(data.actor)
            if data.all_actor and "actor_all," in config.nfo_include_new:
                actor = str(data.all_actor)
            self.Ui.label_actor.setToolTip(actor)
            if number and not actor:
                actor = config.actor_no_name
            if len(actor) > 10:
                actor = actor[:9] + "……"
            self.Ui.label_actor.setText(actor)
            self.file_main_open_path = file_info.file_path  # 文件路径

            title = data.title.split("\n")[0].strip(" :")
            self.Ui.label_title.setToolTip(title)
            if len(title) > 27:
                title = title[:25] + "……"
            self.Ui.label_title.setText(title)
            outline = str(data.outline)
            self.Ui.label_outline.setToolTip(outline)
            if len(outline) > 38:
                outline = outline[:36] + "……"
            self.Ui.label_outline.setText(outline)
            tag = str(data.tag).strip(" [',']").replace("'", "")
            self.Ui.label_tag.setToolTip(tag)
            if len(tag) > 76:
                tag = tag[:75] + "……"
            self.Ui.label_tag.setText(tag)
            self.Ui.label_release.setText(str(data.release))
            self.Ui.label_release.setToolTip(str(data.release))
            if data.runtime:
                self.Ui.label_runtime.setText(str(data.runtime) + " 分钟")
                self.Ui.label_runtime.setToolTip(str(data.runtime) + " 分钟")
            else:
                self.Ui.label_runtime.setText("")
            self.Ui.label_director.setText(str(data.director))
            self.Ui.label_director.setToolTip(str(data.director))
            series = str(data.series)
            self.Ui.label_series.setToolTip(series)
            if len(series) > 32:
                series = series[:31] + "……"
            self.Ui.label_series.setText(series)
            self.Ui.label_studio.setText(data.studio)
            self.Ui.label_studio.setToolTip(data.studio)
            self.Ui.label_publish.setText(data.publisher)
            self.Ui.label_publish.setToolTip(data.publisher)
            self.Ui.label_poster.setToolTip("点击裁剪图片")
            self.Ui.label_thumb.setToolTip("点击裁剪图片")
            # 生成img_path，用来裁剪使用
            img_path = other.fanart_path if os.path.isfile(other.fanart_path) else other.thumb_path
            self.img_path = img_path
            if self.Ui.checkBox_cover.isChecked():  # 主界面显示封面和缩略图
                poster_path = other.poster_path
                thumb_path = other.thumb_path
                fanart_path = other.fanart_path
                if not os.path.exists(thumb_path) and os.path.exists(fanart_path):
                    thumb_path = fanart_path

                poster_from = data.poster_from
                cover_from = data.thumb_from

                config.executor.submit(self._set_pixmap(poster_path, thumb_path, poster_from, cover_from))
        except Exception:
            if not signal_qt.stop:
                signal_qt.show_traceback_log(traceback.format_exc())

    async def _set_pixmap(
        self,
        poster_path="",
        thumb_path="",
        poster_from="",
        cover_from="",
    ):
        poster_pix = [False, "", "暂无封面图", 156, 220]
        thumb_pix = [False, "", "暂无缩略图", 328, 220]
        if os.path.exists(poster_path):
            poster_pix = await get_pixmap(poster_path, poster=True, pic_from=poster_from)
        if os.path.exists(thumb_path):
            thumb_pix = await get_pixmap(thumb_path, poster=False, pic_from=cover_from)

        # self.Ui.label_poster_size.setText(poster_pix[2] + '  ' + thumb_pix[2])
        poster_text = poster_pix[2] if poster_pix[2] != "暂无封面图" else ""
        thumb_text = thumb_pix[2] if thumb_pix[2] != "暂无缩略图" else ""
        self.set_pic_text.emit((poster_text + " " + thumb_text).strip())
        self.set_pic_pixmap.emit(poster_pix, thumb_pix)

    def resize_label_and_setpixmap(self, poster_pix, thumb_pix):
        self.Ui.label_poster.resize(poster_pix[3], poster_pix[4])
        self.Ui.label_thumb.resize(thumb_pix[3], thumb_pix[4])

        if poster_pix[0]:
            self.Ui.label_poster.setPixmap(poster_pix[1])
        else:
            self.Ui.label_poster.setText(poster_pix[2])

        if thumb_pix[0]:
            self.Ui.label_thumb.setPixmap(thumb_pix[1])
        else:
            self.Ui.label_thumb.setText(thumb_pix[2])

    # endregion

    # 主界面-点击树状条目
    def treeWidget_number_clicked(self, qmodeLindex):
        item = self.Ui.treeWidget_number.currentItem()
        if item and item.text(0) != "成功" and item.text(0) != "失败":
            try:
                index_json = str(item.text(0))
                self.set_main_info(self.json_array[str(index_json)])
                if not self.Ui.widget_nfo.isHidden():
                    self._show_nfo_info()
            except Exception:
                signal_qt.show_traceback_log(item.text(0) + ": No info!")

    def _check_main_file_path(self):
        if not self.file_main_open_path:
            QMessageBox.about(self, "没有目标文件", "请刮削后再使用！！")
            signal_qt.show_scrape_info(f"💡 请刮削后使用！{get_current_time()}")
            return False
        return True

    def main_play_click(self):
        """
        主界面点播放
        """
        # 发送hover事件，清除hover状态（因为弹窗后，失去焦点，状态不会变化）
        self.Ui.pushButton_play.setAttribute(Qt.WidgetAttribute.WA_UnderMouse, False)
        event = QHoverEvent(QEvent.Type.HoverLeave, QPoint(40, 40), QPoint(0, 0))
        QApplication.sendEvent(self.Ui.pushButton_play, event)
        if self._check_main_file_path():
            # file_path = convert_path(self.file_main_open_path)
            # mac需要改为无焦点状态，不然弹窗失去焦点后，再切换回来会有找不到焦点的问题（windows无此问题）
            # if not self.is_windows:
            #     self.setWindowFlags(self.windowFlags() | Qt.WindowDoesNotAcceptFocus)
            #     self.show()
            # 启动线程打开文件
            t = threading.Thread(target=open_file_thread, args=(self.file_main_open_path, False))
            t.start()

    def main_open_folder_click(self):
        """
        主界面点打开文件夹
        """
        self.Ui.pushButton_open_folder.setAttribute(Qt.WidgetAttribute.WA_UnderMouse, False)
        event = QHoverEvent(QEvent.Type.HoverLeave, QPoint(40, 40), QPoint(0, 0))
        QApplication.sendEvent(self.Ui.pushButton_open_folder, event)
        if self._check_main_file_path():
            # file_path = convert_path(self.file_main_open_path)
            # mac需要改为无焦点状态，不然弹窗失去焦点后，再切换回来会有找不到焦点的问题（windows无此问题）
            # if not self.is_windows:
            #     self.setWindowFlags(self.windowFlags() | Qt.WindowDoesNotAcceptFocus)
            #     self.show()
            # 启动线程打开文件
            t = threading.Thread(target=open_file_thread, args=(self.file_main_open_path, True))
            t.start()

    def main_open_nfo_click(self):
        """
        主界面点打开nfo
        """
        self.Ui.pushButton_open_nfo.setAttribute(Qt.WidgetAttribute.WA_UnderMouse, False)
        event = QHoverEvent(QEvent.Type.HoverLeave, QPoint(40, 40), QPoint(0, 0))
        QApplication.sendEvent(self.Ui.pushButton_open_nfo, event)
        if self._check_main_file_path():
            self.Ui.widget_nfo.show()
            self._show_nfo_info()

    def main_open_right_menu(self):
        """
        主界面点打开右键菜单
        """
        # 发送hover事件，清除hover状态（因为弹窗后，失去焦点，状态不会变化）
        self.Ui.pushButton_right_menu.setAttribute(Qt.WA_UnderMouse, False)
        event = QHoverEvent(QEvent.Type.HoverLeave, QPoint(40, 40), QPoint(0, 0))
        QApplication.sendEvent(self.Ui.pushButton_right_menu, event)
        self._menu()

    def search_by_number_clicked(self):
        """
        主界面点输入番号
        """
        if self._check_main_file_path():
            file_path = self.file_main_open_path
            main_file_name = split_path(file_path)[1]
            default_text = os.path.splitext(main_file_name)[0].upper()
            text, ok = QInputDialog.getText(
                self, "输入番号重新刮削", f"文件名: {main_file_name}\n请输入番号:", text=default_text
            )
            if ok and text:
                Flags.again_dic[file_path] = (text, "", "")
                signal_qt.show_scrape_info(f"💡 已添加刮削！{get_current_time()}")
                if self.Ui.pushButton_start_cap.text() == "开始":
                    again_search()

    def search_by_url_clicked(self):
        """
        主界面点输入网址
        """
        if self._check_main_file_path():
            file_path = self.file_main_open_path
            main_file_name = split_path(file_path)[1]
            text, ok = QInputDialog.getText(
                self,
                "输入网址重新刮削",
                f"文件名: {main_file_name}\n支持网站:airav_cc、airav、avsex、avsox、dmm、getchu、fc2"
                f"、fc2club、fc2hub、iqqtv、jav321、javbus、javdb、freejavbt、javlibrary、mdtv"
                f"、madouqu、mgstage、7mmtv、xcity、mywife、giga、faleno、dahlia、fantastica"
                f"、prestige、hdouban、lulubar、love6、cnmdb、theporndb、kin8\n请输入番号对应的网址（不是网站首页地址！！！是番号页面地址！！！）:",
            )
            if ok and text:
                website, url = deal_url(text)
                if website:
                    Flags.again_dic[file_path] = ("", url, website)
                    signal_qt.show_scrape_info(f"💡 已添加刮削！{get_current_time()}")
                    if self.Ui.pushButton_start_cap.text() == "开始":
                        again_search()
                else:
                    signal_qt.show_scrape_info(f"💡 不支持的网站！{get_current_time()}")

    def main_del_file_click(self):
        """
        主界面点删除文件
        """
        if self._check_main_file_path():
            file_path = self.file_main_open_path
            box = QMessageBox(QMessageBox.Warning, "删除文件", f"将要删除文件: \n{file_path}\n\n 你确定要删除吗？")
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.button(QMessageBox.Yes).setText("删除文件")
            box.button(QMessageBox.No).setText("取消")
            box.setDefaultButton(QMessageBox.No)
            reply = box.exec()
            if reply != QMessageBox.Yes:
                return
            delete_file_sync(file_path)
            signal_qt.show_scrape_info(f"💡 已删除文件！{get_current_time()}")

    def main_del_folder_click(self):
        """
        主界面点删除文件夹
        """
        if self._check_main_file_path():
            folder_path = split_path(self.file_main_open_path)[0]
            box = QMessageBox(QMessageBox.Warning, "删除文件", f"将要删除文件夹: \n{folder_path}\n\n 你确定要删除吗？")
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.button(QMessageBox.Yes).setText("删除文件和文件夹")
            box.button(QMessageBox.No).setText("取消")
            box.setDefaultButton(QMessageBox.No)
            reply = box.exec()
            if reply != QMessageBox.Yes:
                return
            shutil.rmtree(folder_path, ignore_errors=True)
            self.show_scrape_info(f"💡 已删除文件夹！{get_current_time()}")

    def _pic_main_clicked(self):
        """
        主界面点图片
        """
        file_info = None if self.show_data is None else self.show_data.file_info
        self.cutwindow.showimage(self.img_path, file_info)
        self.cutwindow.show()

    # 主界面-开关封面显示
    def checkBox_cover_clicked(self):
        if not self.Ui.checkBox_cover.isChecked():
            self.Ui.label_poster.setText("封面图")
            self.Ui.label_thumb.setText("缩略图")
            self.Ui.label_poster.resize(156, 220)
            self.Ui.label_thumb.resize(328, 220)
            self.Ui.label_poster_size.setText("")
            self.Ui.label_thumb_size.setText("")
        else:
            self.set_main_info(self.show_data)

    # region 主界面编辑nfo
    def _show_nfo_info(self):
        try:
            if not self.show_name:
                return
            show_data = self.json_array[self.show_name]
            json_data = show_data.data
            file_info = show_data.file_info
            self.now_show_name = show_data.show_name
            actor = json_data.actor
            if json_data.all_actor and "actor_all," in config.nfo_include_new:
                actor = json_data.all_actor
            self.Ui.label_nfo.setText(file_info.file_path)
            self.Ui.lineEdit_nfo_number.setText(json_data.number)
            self.Ui.lineEdit_nfo_actor.setText(actor)
            self.Ui.lineEdit_nfo_year.setText(json_data.year)
            self.Ui.lineEdit_nfo_title.setText(json_data.title)
            self.Ui.lineEdit_nfo_originaltitle.setText(json_data.originaltitle)
            self.Ui.textEdit_nfo_outline.setPlainText(json_data.outline)
            self.Ui.textEdit_nfo_originalplot.setPlainText(json_data.originalplot)
            self.Ui.textEdit_nfo_tag.setPlainText(json_data.tag)
            self.Ui.lineEdit_nfo_release.setText(json_data.release)
            self.Ui.lineEdit_nfo_runtime.setText(json_data.runtime)
            self.Ui.lineEdit_nfo_score.setText(json_data.score)
            self.Ui.lineEdit_nfo_wanted.setText(json_data.wanted)
            self.Ui.lineEdit_nfo_director.setText(json_data.director)
            self.Ui.lineEdit_nfo_series.setText(json_data.series)
            self.Ui.lineEdit_nfo_studio.setText(json_data.studio)
            self.Ui.lineEdit_nfo_publisher.setText(json_data.publisher)
            self.Ui.lineEdit_nfo_poster.setText(json_data.poster)
            self.Ui.lineEdit_nfo_cover.setText(json_data.thumb)
            self.Ui.lineEdit_nfo_trailer.setText(json_data.trailer)
            all_items = [self.Ui.comboBox_nfo.itemText(i) for i in range(self.Ui.comboBox_nfo.count())]
            self.Ui.comboBox_nfo.setCurrentIndex(all_items.index(json_data.country))
        except Exception:
            if not signal_qt.stop:
                signal_qt.show_traceback_log(traceback.format_exc())

    def save_nfo_info(self):
        try:
            if self.now_show_name is None:
                return
            show_data = self.json_array[self.now_show_name]
            json_data = show_data.data
            file_info = show_data.file_info
            file_path = file_info.file_path
            nfo_path = os.path.splitext(file_path)[0] + ".nfo"
            nfo_folder = split_path(file_path)[0]
            json_data.number = self.Ui.lineEdit_nfo_number.text()
            if "actor_all," in config.nfo_include_new:
                json_data.all_actor = self.Ui.lineEdit_nfo_actor.text()
            json_data.actor = self.Ui.lineEdit_nfo_actor.text()
            json_data.year = self.Ui.lineEdit_nfo_year.text()
            json_data.title = self.Ui.lineEdit_nfo_title.text()
            json_data.originaltitle = self.Ui.lineEdit_nfo_originaltitle.text()
            json_data.outline = self.Ui.textEdit_nfo_outline.toPlainText()
            json_data.originalplot = self.Ui.textEdit_nfo_originalplot.toPlainText()
            json_data.tag = self.Ui.textEdit_nfo_tag.toPlainText()
            json_data.release = self.Ui.lineEdit_nfo_release.text()
            json_data.runtime = self.Ui.lineEdit_nfo_runtime.text()
            json_data.score = self.Ui.lineEdit_nfo_score.text()
            json_data.wanted = self.Ui.lineEdit_nfo_wanted.text()
            json_data.director = self.Ui.lineEdit_nfo_director.text()
            json_data.series = self.Ui.lineEdit_nfo_series.text()
            json_data.studio = self.Ui.lineEdit_nfo_studio.text()
            json_data.publisher = self.Ui.lineEdit_nfo_publisher.text()
            json_data.poster = self.Ui.lineEdit_nfo_poster.text()
            json_data.thumb = self.Ui.lineEdit_nfo_cover.text()
            json_data.trailer = self.Ui.lineEdit_nfo_trailer.text()
            if config.executor.run(write_nfo(file_info, json_data, nfo_path, nfo_folder, file_path, update=True)):
                self.Ui.label_save_tips.setText(f"已保存! {get_current_time()}")
                self.set_main_info(show_data)
            else:
                self.Ui.label_save_tips.setText(f"保存失败! {get_current_time()}")
        except Exception:
            if not signal_qt.stop:
                signal_qt.show_traceback_log(traceback.format_exc())

    # endregion

    # 主界面左下角显示信息
    def show_scrape_info(self, before_info=""):
        try:
            if Flags.file_mode == FileMode.Single:
                scrape_info = f"💡 单文件刮削\n💠 {Flags.main_mode_text} · {self.Ui.comboBox_website_all.currentText()}"
            else:
                scrape_info = f"💠 {Flags.main_mode_text} · {Flags.scrape_like_text}"
                if config.scrape_like == "single":
                    scrape_info = f"💡 {config.website_single} 刮削\n" + scrape_info
            if config.soft_link == 1:
                scrape_info = "🍯 软链接 · 开\n" + scrape_info
            elif config.soft_link == 2:
                scrape_info = "🍯 硬链接 · 开\n" + scrape_info
            after_info = f"\n{scrape_info}\n🛠 {manager.file}\n🐰 MDCx {self.localversion}"
            self.label_show_version.emit(before_info + after_info + self.new_version)
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())

    # region 获取/保存成功刮削列表
    def pushButton_success_list_save_clicked(self):
        box = QMessageBox(QMessageBox.Warning, "保存成功列表", "确定要将当前列表保存为已刮削成功文件列表吗？")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.button(QMessageBox.Yes).setText("保存")
        box.button(QMessageBox.No).setText("取消")
        box.setDefaultButton(QMessageBox.No)
        reply = box.exec()
        if reply == QMessageBox.Yes:
            with open(resources.userdata_path("success.txt"), "w", encoding="utf-8", errors="ignore") as f:
                f.write(self.Ui.textBrowser_show_success_list.toPlainText().replace("暂无成功刮削的文件", "").strip())
            get_success_list()
            self.Ui.widget_show_success.hide()

    def pushButton_success_list_clear_clicked(self):
        box = QMessageBox(QMessageBox.Warning, "清空成功列表", "确定要清空当前已刮削成功文件列表吗？")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.button(QMessageBox.Yes).setText("清空")
        box.button(QMessageBox.No).setText("取消")
        box.setDefaultButton(QMessageBox.No)
        reply = box.exec()
        if reply == QMessageBox.Yes:
            Flags.success_list.clear()
            config.executor.run(save_success_list())
            self.Ui.widget_show_success.hide()

    def pushButton_view_success_file_clicked(self):
        self.Ui.widget_show_success.show()
        info = "暂无成功刮削的文件"
        if len(Flags.success_list):
            temp = list(Flags.success_list)
            temp.sort()
            info = "\n".join(temp)
        self.Ui.textBrowser_show_success_list.setText(info)

    # endregion
    # endregion

    # region 日志页
    # 日志页点展开折叠日志
    def pushButton_show_hide_logs_clicked(self):
        if self.Ui.textBrowser_log_main_2.isHidden():
            self.show_hide_logs(True)
        else:
            self.show_hide_logs(False)

    # 日志页点展开折叠日志
    def show_hide_logs(self, show):
        if show:
            self.Ui.pushButton_show_hide_logs.setIcon(QIcon(resources.hide_logs_icon))
            self.Ui.textBrowser_log_main_2.show()
            self.Ui.textBrowser_log_main.resize(790, 418)
            self.Ui.textBrowser_log_main.verticalScrollBar().setValue(
                self.Ui.textBrowser_log_main.verticalScrollBar().maximum()
            )
            self.Ui.textBrowser_log_main_2.verticalScrollBar().setValue(
                self.Ui.textBrowser_log_main_2.verticalScrollBar().maximum()
            )

            # self.Ui.textBrowser_log_main_2.moveCursor(self.Ui.textBrowser_log_main_2.textCursor().End)

        else:
            self.Ui.pushButton_show_hide_logs.setIcon(QIcon(resources.show_logs_icon))
            self.Ui.textBrowser_log_main_2.hide()
            self.Ui.textBrowser_log_main.resize(790, 689)
            self.Ui.textBrowser_log_main.verticalScrollBar().setValue(
                self.Ui.textBrowser_log_main.verticalScrollBar().maximum()
            )

    # 日志页点展开折叠失败列表
    def pushButton_show_hide_failed_list_clicked(self):
        if self.Ui.textBrowser_log_main_3.isHidden():
            self.show_hide_failed_list(True)
        else:
            self.show_hide_failed_list(False)

    # 日志页点展开折叠失败列表
    def show_hide_failed_list(self, show):
        if show:
            self.Ui.textBrowser_log_main_3.show()
            self.Ui.pushButton_scraper_failed_list.show()
            self.Ui.pushButton_save_failed_list.show()
            self.Ui.textBrowser_log_main_3.verticalScrollBar().setValue(
                self.Ui.textBrowser_log_main_3.verticalScrollBar().maximum()
            )

        else:
            self.Ui.pushButton_save_failed_list.hide()
            self.Ui.textBrowser_log_main_3.hide()
            self.Ui.pushButton_scraper_failed_list.hide()

    # 日志页点一键刮削失败列表
    def pushButton_scraper_failed_list_clicked(self):
        if len(Flags.failed_file_list) and self.Ui.pushButton_start_cap.text() == "开始":
            start_new_scrape(FileMode.Default, movie_list=Flags.failed_file_list)
            self.show_hide_failed_list(False)

    # 日志页点另存失败列表
    def pushButton_save_failed_list_clicked(self):
        if len(Flags.failed_file_list) or True:
            log_name = "failed_" + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + ".txt"
            log_name = convert_path(os.path.join(get_movie_path_setting()[0], log_name))
            filename, filetype = QFileDialog.getSaveFileName(
                None, "保存失败文件列表", log_name, "Text Files (*.txt)", options=self.options
            )
            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.Ui.textBrowser_log_main_3.toPlainText().strip())

    # 显示详细日志
    def show_detail_log(self):
        text = signal_qt.get_log()
        if text:
            self.main_req_logs_show.emit(add_html(text))
            if self.req_logs_counts < 10000:
                self.req_logs_counts += 1
            else:
                self.req_logs_counts = 0
                self.req_logs_clear.emit("")
                self.main_req_logs_show.emit(add_html(" 🗑️ 日志过多，已清屏！"))

    # 日志页面显示内容
    def show_log_text(self, text):
        if not text:
            return
        text = str(text)
        if config.save_log:  # 保存日志
            try:
                Flags.log_txt.write((text + "\n").encode("utf-8"))
            except Exception:
                log_folder = os.path.join(manager.data_folder, "Log")
                if not os.path.exists(log_folder):
                    os.makedirs(log_folder)
                log_name = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + ".txt"
                log_name = convert_path(os.path.join(log_folder, log_name))

                Flags.log_txt = open(log_name, "wb", buffering=0)
                signal_qt.show_log_text("Create log file: " + log_name + "\n")
                signal_qt.show_log_text(text)
                return
        try:
            self.main_logs_show.emit(add_html(text))
            if self.logs_counts < 10000:
                self.logs_counts += 1
            else:
                self.logs_counts = 0
                self.main_logs_clear.emit("")
                self.main_logs_show.emit(add_html(" 🗑️ 日志过多，已清屏！"))
                # self.show_traceback_log(self.Ui.textBrowser_log_main.document().lineCount())

        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
            self.Ui.textBrowser_log_main.append(traceback.format_exc())

    # endregion

    # region 工具页
    # 工具页面点查看本地番号
    def label_local_number_clicked(self, ev):
        if self.Ui.pushButton_find_missing_number.isEnabled():
            self.pushButton_show_log_clicked()  # 点击按钮后跳转到日志页面
            if self.Ui.lineEdit_actors_name.text() != config.actors_name:  # 保存配置
                self.pushButton_save_config_clicked()
            config.executor.submit(check_missing_number(False))

    # 工具页面本地资源库点选择目录
    def pushButton_select_local_library_clicked(self):
        media_folder_path = self._get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_local_library_path.setText(convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # 工具页面网盘目录点选择目录
    def pushButton_select_netdisk_path_clicked(self):
        media_folder_path = self._get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_netdisk_path.setText(convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # 工具页面本地目录点选择目录
    def pushButton_select_localdisk_path_clicked(self):
        media_folder_path = self._get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_localdisk_path.setText(convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # 工具/设置页面点选择目录
    def pushButton_select_media_folder_clicked(self):
        media_folder_path = self._get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_movie_path.setText(convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # 工具-软链接助手
    def pushButton_creat_symlink_clicked(self):
        """
        工具点一键创建软链接
        """
        self.pushButton_show_log_clicked()  # 点击按钮后跳转到日志页面

        if bool("copy_netdisk_nfo" in config.switch_on) != bool(self.Ui.checkBox_copy_netdisk_nfo.isChecked()):
            self.pushButton_save_config_clicked()

        try:
            config.executor.submit(newtdisk_creat_symlink(self.Ui.checkBox_copy_netdisk_nfo.isChecked()))
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
            signal_qt.show_log_text(traceback.format_exc())

    # 工具-检查番号
    def pushButton_find_missing_number_clicked(self):
        """
        工具点检查缺失番号
        """
        self.pushButton_show_log_clicked()  # 点击按钮后跳转到日志页面

        # 如果本地资源库或演员与配置内容不同，则自动保存
        if (
            self.Ui.lineEdit_actors_name.text() != config.actors_name
            or self.Ui.lineEdit_local_library_path.text() != config.local_library
        ):
            self.pushButton_save_config_clicked()
        config.executor.submit(check_missing_number(True))

    # 工具-单文件刮削
    def pushButton_select_file_clicked(self):
        media_path = self.Ui.lineEdit_movie_path.text()  # 获取待刮削目录作为打开目录
        if not media_path:
            media_path = manager.data_folder
        file_path, filetype = QFileDialog.getOpenFileName(
            None,
            "选取视频文件",
            media_path,
            "Movie Files(*.mp4 "
            "*.avi *.rmvb *.wmv "
            "*.mov *.mkv *.flv *.ts "
            "*.webm *.MP4 *.AVI "
            "*.RMVB *.WMV *.MOV "
            "*.MKV *.FLV *.TS "
            "*.WEBM);;All Files(*)",
            options=self.options,
        )
        if file_path:
            self.Ui.lineEdit_single_file_path.setText(convert_path(file_path))

    def pushButton_start_single_file_clicked(self):  # 点刮削
        Flags.single_file_path = self.Ui.lineEdit_single_file_path.text().strip()
        if not Flags.single_file_path:
            signal_qt.show_scrape_info("💡 请选择文件！")
            return

        if not os.path.isfile(Flags.single_file_path):
            signal_qt.show_scrape_info("💡 文件不存在！")  # 主界面左下角显示信息
            return

        if not self.Ui.lineEdit_appoint_url.text():
            signal_qt.show_scrape_info("💡 请填写番号网址！")  # 主界面左下角显示信息
            return

        self.pushButton_show_log_clicked()  # 点击刮削按钮后跳转到日志页面
        Flags.appoint_url = self.Ui.lineEdit_appoint_url.text().strip()
        # 单文件刮削从用户输入的网址中识别网址名，复用现成的逻辑=>主页面输入网址刮削
        website, url = deal_url(Flags.appoint_url)
        if website:
            Flags.website_name = website
        else:
            signal_qt.show_scrape_info(f"💡 不支持的网站！{get_current_time()}")
            return
        start_new_scrape(FileMode.Single)

    def pushButton_select_file_clear_info_clicked(self):  # 点清空信息
        self.Ui.lineEdit_single_file_path.setText("")
        self.Ui.lineEdit_appoint_url.setText("")

        # self.Ui.lineEdit_movie_number.setText('')

    # 工具-裁剪封面图
    def pushButton_select_thumb_clicked(self):
        path = self.Ui.lineEdit_movie_path.text()
        if not path:
            path = manager.data_folder
        file_path, fileType = QFileDialog.getOpenFileName(
            None, "选取缩略图", path, "Picture Files(*.jpg *.png);;All Files(*)", options=self.options
        )
        if file_path != "":
            self.cutwindow.showimage(file_path)
            self.cutwindow.show()

    # 工具-视频移动
    def pushButton_move_mp4_clicked(self):
        box = QMessageBox(QMessageBox.Warning, "移动视频和字幕", "确定要移动视频和字幕吗？")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.button(QMessageBox.Yes).setText("移动")
        box.button(QMessageBox.No).setText("取消")
        box.setDefaultButton(QMessageBox.No)
        reply = box.exec()
        if reply == QMessageBox.Yes:
            self.pushButton_show_log_clicked()  # 点击开始移动按钮后跳转到日志页面
            try:
                t = threading.Thread(target=self._move_file_thread)
                self.threads_list.append(t)
                t.start()  # 启动线程,即让线程开始执行
            except Exception:
                signal_qt.show_traceback_log(traceback.format_exc())
                signal_qt.show_log_text(traceback.format_exc())

    def _move_file_thread(self):
        signal_qt.change_buttons_status.emit()
        movie_type = self.Ui.lineEdit_movie_type.text().lower()
        sub_type = self.Ui.lineEdit_sub_type.text().lower().replace("|.txt", "")
        all_type = movie_type.strip("|") + "|" + sub_type.strip("|")
        movie_path = config.media_path.replace("\\", "/")  # 用户设置的扫描媒体路径
        if movie_path == "":  # 未设置为空时，使用主程序目录
            movie_path = manager.data_folder
        escape_dir = self.Ui.lineEdit_escape_dir_move.text().replace("\\", "/")
        escape_dir = escape_dir + ",Movie_moved"
        escape_folder_list = escape_dir.split(",")
        escape_folder_new_list = []
        for es in escape_folder_list:  # 排除目录可以多个，以，,分割
            es = es.strip(" ")
            if es:
                es = get_path(movie_path, es).replace("\\", "/")
                if es[-1] != "/":  # 路径尾部添加“/”，方便后面move_list查找时匹配路径
                    es += "/"
                escape_folder_new_list.append(es)
        movie_list = config.executor.run(movie_lists(escape_folder_new_list, all_type, movie_path))
        if not movie_list:
            signal_qt.show_log_text("No movie found!")
            signal_qt.show_log_text("================================================================================")
            signal_qt.reset_buttons_status.emit()
            return
        des_path = os.path.join(movie_path, "Movie_moved")
        if not os.path.exists(des_path):
            signal_qt.show_log_text("Created folder: Movie_moved")
            os.makedirs(des_path)
        signal_qt.show_log_text("Start move movies...")
        skip_list = []
        for file_path in movie_list:
            file_name = split_path(file_path)[1]
            file_ext = os.path.splitext(file_name)[1]
            try:
                # move_file(file_path, des_path)
                shutil.move(file_path, des_path)
                if file_ext in movie_type:
                    signal_qt.show_log_text("   Move movie: " + file_name + " to Movie_moved Success!")
                else:
                    signal_qt.show_log_text("   Move sub: " + file_name + " to Movie_moved Success!")
            except Exception as e:
                skip_list.append([file_name, file_path, str(e)])
        if skip_list:
            signal_qt.show_log_text(f"\n{len(skip_list)} file(s) did not move!")
            i = 0
            for info in skip_list:
                i += 1
                signal_qt.show_log_text(f"[{i}] {info[0]}\n file path: {info[1]}\n {info[2]}\n")
        signal_qt.show_log_text("Move movies finished!")
        signal_qt.show_log_text("================================================================================")
        signal_qt.reset_buttons_status.emit()

    # endregion

    # region 设置页
    # region 选择目录
    # 设置-目录-软链接目录-点选择目录
    def pushButton_select_softlink_folder_clicked(self):
        media_folder_path = self._get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_movie_softlink_path.setText(convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # 设置-目录-成功输出目录-点选择目录
    def pushButton_select_sucess_folder_clicked(self):
        media_folder_path = self._get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_success.setText(convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # 设置-目录-失败输出目录-点选择目录
    def pushButton_select_failed_folder_clicked(self):
        media_folder_path = self._get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_fail.setText(convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # 设置-字幕-字幕文件目录-点选择目录
    def pushButton_select_subtitle_folder_clicked(self):
        media_folder_path = self._get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_sub_folder.setText(convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # 设置-头像-头像文件目录-点选择目录
    def pushButton_select_actor_photo_folder_clicked(self):
        media_folder_path = self._get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_actor_photo_folder.setText(convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # 设置-其他-配置文件目录-点选择目录
    def pushButton_select_config_folder_clicked(self):
        media_folder_path = convert_path(self._get_select_folder_path())
        if media_folder_path and media_folder_path != manager.data_folder:
            config_path = os.path.join(media_folder_path, "config.json")
            manager.path = media_folder_path
            if os.path.isfile(config_path):
                temp_dark = self.dark_mode
                temp_window_radius = self.window_radius
                self.load_config()
                if temp_dark != self.dark_mode and temp_window_radius == self.window_radius:
                    self.show_flag = True
                    self._windows_auto_adjust()
            else:
                self.Ui.lineEdit_config_folder.setText(media_folder_path)
                self.pushButton_save_config_clicked()
            signal_qt.show_scrape_info(f"💡 目录已切换！{get_current_time()}")

    # endregion

    # 设置-演员-补全信息-演员信息数据库-选择文件按钮
    def pushButton_select_actor_info_db_clicked(self):
        database_path, _ = QFileDialog.getOpenFileName(
            None, "选择数据库文件", manager.data_folder, options=self.options
        )
        if database_path:
            self.Ui.lineEdit_actor_db_path.setText(convert_path(database_path))
            self.pushButton_save_config_clicked()

    # region 设置-问号
    def pushButton_tips_normal_mode_clicked(self):
        self._show_tips(self.Ui.pushButton_tips_normal_mode.toolTip())

    def pushButton_tips_sort_mode_clicked(self):
        self._show_tips(self.Ui.pushButton_tips_sort_mode.toolTip())

    def pushButton_tips_update_mode_clicked(self):
        self._show_tips(self.Ui.pushButton_tips_update_mode.toolTip())

    def pushButton_tips_read_mode_clicked(self):
        self._show_tips(self.Ui.pushButton_tips_read_mode.toolTip())

    def pushButton_tips_soft_clicked(self):
        self._show_tips(self.Ui.pushButton_tips_soft.toolTip())

    def pushButton_tips_hard_clicked(self):
        self._show_tips(self.Ui.pushButton_tips_hard.toolTip())

    # 设置-显示说明信息
    def _show_tips(self, msg):
        self.Ui.textBrowser_show_tips.setText(msg)
        self.Ui.widget_show_tips.show()

    # 设置-刮削网站和字段中的详细说明弹窗
    def pushButton_scrape_note_clicked(self):
        self._show_tips("""<html><head/><body><p><span style=" font-weight:700;">1、以下类型番号，请指定刮削网站，可以提供成功率，节省刮削用时</span></p><p>· 欧美：theporndb </p><p>· 国产：mdtv、madouqu、hdouban、cnmdb、love6</p><p>· 里番：getchu_dmm </p><p>· Mywife：mywife </p><p>· GIGA：giga </p><p>· Kin8：Kin8 </p><p><span style=" font-weight:700;">2、下不了预告片和剧照，请选择「字段优先」</span></p>\
            <p>· 速度优先：字段来自一个网站 </p><p>· 字段优先：分字段刮削，不同字段来自不同网站</p><p>字段优先的信息会比速度优先好很多！建议默认使用「字段优先」</p><p>当文件数量较多，线程数量10+以上，两者耗时差不太多 </p><p><span style=" font-weight:700;">3、匹配到同名的另一个番号信息或者错误番号</span></p><p>请使用单文件刮削。路径：工具 - 单文件刮削 </p><p><span style=" font-weight:700;">4、频繁请求被封 IP 了</span></p><p>建议更换节点，启用「间歇刮削」： 设置 - 其他 - 间歇刮削</p></body></html>""")

    # 设置-刮削网站和字段中的详细说明弹窗
    def pushButton_field_tips_website_clicked(self):
        self._show_tips("""<html><head/><body><p><span style=" font-weight:700;">字段说明</span></p><p>举个🌰，比如刮削一个有码番号的简介字段时，假定： </p><p>1，有码番号设置的网站为（1，2，3，4，5，6，7） </p><p>2，简介字段设置的网站为（9，5，2，7） </p><p>3，简介字段的排除网站为（3，6） （比如3和6的网站没有简介，这时没必要去请求，因此可以加入到排除网站）</p><p><br/></p><p><span style=" font-weight:700;">程序将通过以下方法生成请求网站的顺序表：</span></p><p>1，取简介字段网站和有码番号网站的交集：（5，2，7） （此顺序以简介字段设置的网站顺序为准） </p><p>\
            2，取有码番号剩余的网站，补充在后面，结果为（5，2，7，1，3，4，6） （此顺序以有码番号设置的网站顺序为准。补充的原因是当设置的字段网站未请求到时，可以继续使用有码网站查询，如不想查询可加到排除网站或去掉尽量补全字段的勾选） </p><p>3，去除排除的网站，生成简介的网站请求顺序为（5，2，7，1，4） </p><p>程序将按此顺序进行刮削，即优先请求5，当5获取成功后，就不再继续请求。当5没有获取成功，继续按顺序请求2，依次类推……刮削其他番号和字段同理。</p></body></html>""")

    # 设置-刮削网站和字段中的详细说明弹窗
    def pushButton_field_tips_nfo_clicked(self):
        msg = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n\
<movie>\n\
    <plot><![CDATA[剧情简介]]></plot>\n\
    <outline><![CDATA[剧情简介]]></outline>\n\
    <originalplot><![CDATA[原始剧情简介]]></originalplot>\n\
    <tagline>发行日期 XXXX-XX-XX</tagline> \n\
    <premiered>发行日期</premiered>\n\
    <releasedate>发行日期</releasedate>\n\
    <release>发行日期</release>\n\
    <num>番号</num>\n\
    <title>标题</title>\n\
    <originaltitle>原始标题</originaltitle>\n\
    <sorttitle>类标题 </sorttitle>\n\
    <mpaa>家长分级</mpaa>\n\
    <customrating>自定义分级</customrating>\n\
    <actor>\n\
        <name>名字</name>\n\
        <type>类型：演员</type>\n\
    </actor>\n\
    <director>导演</director>\n\
    <rating>评分</rating>\n\
    <criticrating>影评人评分</criticrating>\n\
    <votes>想看人数</votes>\n\
    <year>年份</year>\n\
    <runtime>时长</runtime>\n\
    <series>系列</series>\n\
    <set>\n\
        <name>合集</name>\n\
    </set>\n\
    <studio>片商/制作商</studio> \n\
    <maker>片商/制作商</maker>\n\
    <publisher>厂牌/发行商</publisher>\n\
    <label>厂牌/发行商</label>\n\
    <tag>标签</tag>\n\
    <genre>风格</genre>\n\
    <cover>背景图地址</cover>\n\
    <poster>封面图地址</poster>\n\
    <trailer>预告片地址</trailer>\n\
    <website>刮削网址</website>\n\
</movie>\n\
        """
        self._show_tips(msg)

    # endregion

    # 设置-刮削目录 点击检查待刮削目录并清理文件
    def pushButton_check_and_clean_files_clicked(self):
        if not config.can_clean:
            self.pushButton_save_config_clicked()
        self.pushButton_show_log_clicked()
        try:
            config.executor.submit(check_and_clean_files())
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
            signal_qt.show_log_text(traceback.format_exc())

    # 设置-字幕 为所有视频中的无字幕视频添加字幕
    def pushButton_add_sub_for_all_video_clicked(self):
        self.pushButton_show_log_clicked()  # 点按钮后跳转到日志页面
        try:
            config.executor.submit(add_sub_for_all_video())
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
            signal_qt.show_log_text(traceback.format_exc())

    # region 设置-下载
    # 为所有视频中的创建/删除剧照附加内容
    def pushButton_add_all_extras_clicked(self):
        self.pushButton_show_log_clicked()  # 点按钮后跳转到日志页面
        try:
            config.executor.submit(add_del_extras("add"))
        except Exception:
            signal_qt.show_log_text(traceback.format_exc())

    def pushButton_del_all_extras_clicked(self):
        self.pushButton_show_log_clicked()  # 点按钮后跳转到日志页面
        try:
            config.executor.submit(add_del_extras("del"))
        except Exception:
            signal_qt.show_log_text(traceback.format_exc())

    # 为所有视频中的创建/删除剧照副本
    def pushButton_add_all_extrafanart_copy_clicked(self):
        self.pushButton_show_log_clicked()  # 点按钮后跳转到日志页面
        self.pushButton_save_config_clicked()
        try:
            config.executor.submit(add_del_extrafanart_copy("add"))
        except Exception:
            signal_qt.show_log_text(traceback.format_exc())

    def pushButton_del_all_extrafanart_copy_clicked(self):
        self.pushButton_show_log_clicked()  # 点按钮后跳转到日志页面
        self.pushButton_save_config_clicked()
        try:
            config.executor.submit(add_del_extrafanart_copy("del"))
        except Exception:
            signal_qt.show_log_text(traceback.format_exc())

    # 为所有视频中的创建/删除主题视频
    def pushButton_add_all_theme_videos_clicked(self):
        self.pushButton_show_log_clicked()  # 点按钮后跳转到日志页面
        try:
            config.executor.submit(add_del_theme_videos("add"))
        except Exception:
            signal_qt.show_log_text(traceback.format_exc())

    def pushButton_del_all_theme_videos_clicked(self):
        self.pushButton_show_log_clicked()  # 点按钮后跳转到日志页面
        try:
            config.executor.submit(add_del_theme_videos("del"))
        except Exception:
            signal_qt.show_log_text(traceback.format_exc())

    # endregion

    # region 设置-演员
    # 设置-演员 补全演员信息
    def pushButton_add_actor_info_clicked(self):
        self.pushButton_save_config_clicked()
        self.pushButton_show_log_clicked()  # 点按钮后跳转到日志页面
        try:
            config.executor.submit(update_emby_actor_info())
        except Exception:
            signal_qt.show_log_text(traceback.format_exc())

    # 设置-演员 补全演员头像按钮
    def pushButton_add_actor_pic_clicked(self):
        self.pushButton_save_config_clicked()
        self.pushButton_show_log_clicked()  # 点按钮后跳转到日志页面
        try:
            config.executor.submit(update_emby_actor_photo())
        except Exception:
            signal_qt.show_log_text(traceback.format_exc())

    # 设置-演员 补全演员头像按钮 kodi
    def pushButton_add_actor_pic_kodi_clicked(self):
        self.pushButton_save_config_clicked()
        self.pushButton_show_log_clicked()  # 点按钮后跳转到日志页面
        try:
            config.executor.submit(creat_kodi_actors(True))
        except Exception:
            signal_qt.show_log_text(traceback.format_exc())

    # 设置-演员 清除演员头像按钮 kodi
    def pushButton_del_actor_folder_clicked(self):
        self.pushButton_show_log_clicked()  # 点按钮后跳转到日志页面
        try:
            config.executor.submit(creat_kodi_actors(False))
        except Exception:
            signal_qt.show_log_text(traceback.format_exc())

    # 设置-演员 查看演员列表按钮
    def pushButton_show_pic_actor_clicked(self):
        self.pushButton_show_log_clicked()  # 点按钮后跳转到日志页面
        try:
            config.executor.submit(show_emby_actor_list(self.Ui.comboBox_pic_actor.currentIndex()))
        except Exception:
            signal_qt.show_log_text(traceback.format_exc())

    # endregion

    # 设置-线程数量
    def lcdNumber_thread_change(self):
        thread_number = self.Ui.horizontalSlider_thread.value()
        self.Ui.lcdNumber_thread.display(thread_number)

    # 设置-javdb延时
    def lcdNumber_javdb_time_change(self):
        javdb_time = self.Ui.horizontalSlider_javdb_time.value()
        self.Ui.lcdNumber_javdb_time.display(javdb_time)

    # 设置-其他网站延时
    def lcdNumber_thread_time_change(self):
        thread_time = self.Ui.horizontalSlider_thread_time.value()
        self.Ui.lcdNumber_thread_time.display(thread_time)

    # 设置-超时时间
    def lcdNumber_timeout_change(self):
        timeout = self.Ui.horizontalSlider_timeout.value()
        self.Ui.lcdNumber_timeout.display(timeout)

    # 设置-重试次数
    def lcdNumber_retry_change(self):
        retry = self.Ui.horizontalSlider_retry.value()
        self.Ui.lcdNumber_retry.display(retry)

    # 设置-水印大小
    def lcdNumber_mark_size_change(self):
        mark_size = self.Ui.horizontalSlider_mark_size.value()
        self.Ui.lcdNumber_mark_size.display(mark_size)

    # 设置-网络-网址设置-下拉框切换
    def switch_custom_website_change(self, new_website_name):
        self.Ui.lineEdit_custom_website.setText(getattr(config, f"{new_website_name}_website", ""))

    # 切换配置
    def config_file_change(self, new_config_file):
        if new_config_file != manager.file:
            new_config_path = os.path.join(manager.data_folder, new_config_file)
            signal_qt.show_log_text(
                f"\n================================================================================\n切换配置：{new_config_path}"
            )
            with open(MARK_FILE, "w", encoding="UTF-8") as f:
                f.write(new_config_path)
            temp_dark = self.dark_mode
            temp_window_radius = self.window_radius
            self.load_config()
            if temp_dark != self.dark_mode and temp_window_radius == self.window_radius:
                self.show_flag = True
                self._windows_auto_adjust()
            signal_qt.show_scrape_info(f"💡 配置已切换！{get_current_time()}")

    # 重置配置
    def pushButton_init_config_clicked(self):
        self.Ui.pushButton_init_config.setEnabled(False)
        manager.reset()
        temp_dark = self.dark_mode
        temp_window_radius = self.window_radius
        self.load_config()
        if temp_dark and temp_window_radius:
            self.show_flag = True
            self._windows_auto_adjust()
        self.Ui.pushButton_init_config.setEnabled(True)
        signal_qt.show_scrape_info(f"💡 配置已重置！{get_current_time()}")

    # 设置-命名-分集-字母
    def checkBox_cd_part_a_clicked(self):
        if self.Ui.checkBox_cd_part_a.isChecked():
            self.Ui.checkBox_cd_part_c.setEnabled(True)
        else:
            self.Ui.checkBox_cd_part_c.setEnabled(False)

    # 设置-刮削目录-同意清理(我已知晓/我已同意)
    def checkBox_i_agree_clean_clicked(self):
        if self.Ui.checkBox_i_understand_clean.isChecked() and self.Ui.checkBox_i_agree_clean.isChecked():
            self.Ui.pushButton_check_and_clean_files.setEnabled(True)
            self.Ui.checkBox_auto_clean.setEnabled(True)
        else:
            self.Ui.pushButton_check_and_clean_files.setEnabled(False)
            self.Ui.checkBox_auto_clean.setEnabled(False)

    # 读取设置页的设置, 保存config.ini，然后重新加载
    def _check_mac_config_folder(self):
        if self.check_mac and not IS_WINDOWS and ".app/Contents/Resources" in manager.data_folder:
            self.check_mac = False
            box = QMessageBox(
                QMessageBox.Warning,
                "选择配置文件目录",
                f"检测到当前配置文件目录为：\n {manager.data_folder}\n\n由于 MacOS 平台在每次更新 APP 版本时会覆盖该目录的配置，因此请选择其他的配置目录！\n这样下次更新 APP 时，选择相同的配置目录即可读取你之前的配置！！！",
            )
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.button(QMessageBox.Yes).setText("选择目录")
            box.button(QMessageBox.No).setText("取消")
            box.setDefaultButton(QMessageBox.Yes)
            reply = box.exec()
            if reply == QMessageBox.Yes:
                self.pushButton_select_config_folder_clicked()

    # 设置-保存
    def pushButton_save_config_clicked(self):
        self.save_config()
        # self.load_config()
        signal_qt.show_scrape_info(f"💡 配置已保存！{get_current_time()}")

    # 设置-另存为
    def pushButton_save_new_config_clicked(self):
        new_config_name, ok = QInputDialog.getText(self, "另存为新配置", "请输入新配置的文件名")
        if ok and new_config_name:
            new_config_name = new_config_name.replace("/", "").replace("\\", "")
            new_config_name = re.sub(r'[\\:*?"<>|\r\n]+', "", new_config_name)
            if os.path.splitext(new_config_name)[1] != ".ini":
                new_config_name += ".ini"
            if new_config_name != manager.file:
                manager.file = new_config_name
                self.pushButton_save_config_clicked()

    def save_config(self): ...

    # endregion

    # region 检测网络
    def network_check(self):
        start_time = time.time()
        try:
            # 显示代理信息
            signal_qt.show_net_info("\n⛑ 开始检测网络....")
            show_netstatus()
            # 检测网络连通性
            signal_qt.show_net_info(" 开始检测网络连通性...")

            net_info = {
                "github": ["https://raw.githubusercontent.com", ""],
                "airav_cc": ["https://airav.io", ""],
                "iqqtv": ["https://iqq5.xyz", ""],
                "avsex": ["https://paycalling.com", ""],
                "freejavbt": ["https://freejavbt.com", ""],
                "javbus": ["https://www.javbus.com", ""],
                "javdb": ["https://javdb.com", ""],
                "jav321": ["https://www.jav321.com", ""],
                "javlibrary": ["https://www.javlibrary.com", ""],
                "dmm": ["https://www.dmm.co.jp", ""],
                "mgstage": ["https://www.mgstage.com", ""],
                "getchu": ["http://www.getchu.com", ""],
                "theporndb": ["https://api.theporndb.net", ""],
                "avsox": [config.executor.run(get_avsox_domain()), ""],
                "xcity": ["https://xcity.jp", ""],
                "7mmtv": ["https://7mmtv.sx", ""],
                "mdtv": ["https://www.mdpjzip.xyz", ""],
                "madouqu": ["https://madouqu.com", ""],
                "cnmdb": ["https://cnmdb.net", ""],
                "hscangku": ["https://hscangku.net", ""],
                "cableav": ["https://cableav.tv", ""],
                "lulubar": ["https://lulubar.co", ""],
                "love6": ["https://love6.tv", ""],
                "yesjav": ["http://www.yesjav101.com", ""],
                "fc2": ["https://adult.contents.fc2.com", ""],
                "fc2club": ["https://fc2club.top", ""],
                "fc2hub": ["https://javten.com", ""],
                "airav": ["https://www.airav.wiki", ""],
                "av-wiki": ["https://av-wiki.net", ""],
                "seesaawiki": ["https://seesaawiki.jp", ""],
                "mywife": ["https://mywife.cc", ""],
                "giga": ["https://www.giga-web.jp", ""],
                "kin8": ["https://www.kin8tengoku.com", ""],
                "fantastica": ["http://fantastica-vr.com", ""],
                "faleno": ["https://faleno.jp", ""],
                "dahlia": ["https://dahlia-av.jp", ""],
                "prestige": ["https://www.prestige-av.com", ""],
                "s1s1s1": ["https://s1s1s1.com", ""],
                "moodyz": ["https://moodyz.com", ""],
                "madonna": ["https://www.madonna-av.com", ""],
                "wanz-factory": ["https://www.wanz-factory.com", ""],
                "ideapocket": ["https://ideapocket.com", ""],
                "kirakira": ["https://kirakira-av.com", ""],
                "ebody": ["https://www.av-e-body.com", ""],
                "bi-av": ["https://bi-av.com", ""],
                "premium": ["https://premium-beauty.com", ""],
                "miman": ["https://miman.jp", ""],
                "tameikegoro": ["https://tameikegoro.jp", ""],
                "fitch": ["https://fitch-av.com", ""],
                "kawaiikawaii": ["https://kawaiikawaii.jp", ""],
                "befreebe": ["https://befreebe.com", ""],
                "muku": ["https://muku.tv", ""],
                "attackers": ["https://attackers.net", ""],
                "mko-labo": ["https://mko-labo.net", ""],
                "dasdas": ["https://dasdas.jp", ""],
                "mvg": ["https://mvg.jp", ""],
                "opera": ["https://av-opera.jp", ""],
                "oppai": ["https://oppai-av.com", ""],
                "v-av": ["https://v-av.com", ""],
                "to-satsu": ["https://to-satsu.com", ""],
                "bibian": ["https://bibian-av.com", ""],
                "honnaka": ["https://honnaka.jp", ""],
                "rookie": ["https://rookie-av.jp", ""],
                "nanpa": ["https://nanpa-japan.jp", ""],
                "hajimekikaku": ["https://hajimekikaku.com", ""],
                "hhh-av": ["https://hhh-av.com", ""],
            }

            for website in ManualConfig.SUPPORTED_WEBSITES:
                if hasattr(config, f"{website}_website"):
                    signal_qt.show_net_info(f"   ⚠️{website} 使用自定义网址：{getattr(config, f'{website}_website')}")
                    net_info[website][0] = getattr(config, f"{website}_website")

            net_info["javdb"][0] += "/v/D16Q5?locale=zh"
            net_info["seesaawiki"][0] += "/av_neme/d/%C9%F1%A5%EF%A5%A4%A5%D5"
            net_info["airav_cc"][0] += "/playon.aspx?hid=44733"
            net_info["javlibrary"][0] += "/cn/?v=javme2j2tu"
            net_info["kin8"][0] += "/moviepages/3681/index.html"

            for name, each in net_info.items():
                host_address = each[0].replace("https://", "").replace("http://", "").split("/")[0]
                if name == "javdb":
                    res_javdb = self._check_javdb_cookie()
                    each[1] = res_javdb.replace("✅ 连接正常", f"✅ 连接正常{ping_host(host_address)}")
                elif name == "javbus":
                    res_javbus = self._check_javbus_cookie()
                    each[1] = res_javbus.replace("✅ 连接正常", f"✅ 连接正常{ping_host(host_address)}")
                elif name == "theporndb":
                    res_theporndb = check_theporndb_api_token()
                    each[1] = res_theporndb.replace("✅ 连接正常", f"✅ 连接正常{ping_host(host_address)}")
                elif name == "javlibrary":
                    use_proxy = True
                    if hasattr(config, "javlibrary_website"):
                        use_proxy = False
                    html_info, error = get_text_sync(each[0], use_proxy=use_proxy)
                    if html_info is None:
                        each[1] = "❌ 连接失败 请检查网络或代理设置！ " + error
                    elif "Cloudflare" in html_info:
                        each[1] = "❌ 连接失败 (被 Cloudflare 5 秒盾拦截！)"
                    else:
                        each[1] = f"✅ 连接正常{ping_host(host_address)}"
                elif name in ["avsex", "freejavbt", "airav_cc", "airav", "madouqu", "7mmtv"]:
                    html_info, error = get_text_sync(each[0])
                    if html_info is None:
                        each[1] = "❌ 连接失败 请检查网络或代理设置！ " + error
                    elif "Cloudflare" in html_info:
                        each[1] = "❌ 连接失败 (被 Cloudflare 5 秒盾拦截！)"
                    else:
                        each[1] = f"✅ 连接正常{ping_host(host_address)}"
                else:
                    try:
                        html_content, error = get_text_sync(each[0])
                        if html_content is None:
                            each[1] = "❌ 连接失败 请检查网络或代理设置！ " + str(error)
                        else:
                            if name == "dmm":
                                if re.findall("このページはお住まいの地域からご利用になれません", html_content):
                                    each[1] = "❌ 连接失败 地域限制, 请使用日本节点访问！"
                                else:
                                    each[1] = f"✅ 连接正常{ping_host(host_address)}"
                            elif name == "mgstage":
                                if not html_content.strip():
                                    each[1] = "❌ 连接失败 地域限制, 请使用日本节点访问！"
                                else:
                                    each[1] = f"✅ 连接正常{ping_host(host_address)}"
                            else:
                                each[1] = f"✅ 连接正常{ping_host(host_address)}"
                    except Exception as e:
                        each[1] = "测试连接时出现异常！信息:" + str(e)
                        signal_qt.show_traceback_log(traceback.format_exc())
                        signal_qt.show_net_info(traceback.format_exc())
                signal_qt.show_net_info("   " + name.ljust(12) + each[1])
            signal_qt.show_net_info(f"\n🎉 网络检测已完成！用时 {get_used_time(start_time)} 秒！")
            signal_qt.show_net_info(
                "================================================================================\n"
            )
        except Exception as e:
            if signal_qt.stop:
                signal_qt.show_net_info("\n⛔️ 当前有刮削任务正在停止中，请等待刮削停止后再进行检测！")
                signal_qt.show_net_info(
                    "================================================================================\n"
                )
            else:
                signal_qt.show_net_info("\n⛔️ 网络检测出现异常！")
                signal_qt.show_net_info(
                    "================================================================================\n"
                )
                signal_qt.show_traceback_log(str(e))
                signal_qt.show_traceback_log(traceback.format_exc())
        self.Ui.pushButton_check_net.setEnabled(True)
        self.Ui.pushButton_check_net.setText("开始检测")
        self.Ui.pushButton_check_net.setStyleSheet(
            "QPushButton#pushButton_check_net{background-color:#4C6EFF}QPushButton:hover#pushButton_check_net{background-color: rgba(76,110,255,240)}QPushButton:pressed#pushButton_check_net{#4C6EE0}"
        )

    # 网络检查
    def pushButton_check_net_clicked(self):
        if self.Ui.pushButton_check_net.text() == "开始检测":
            self.Ui.pushButton_check_net.setText("停止检测")
            self.Ui.pushButton_check_net.setStyleSheet(
                "QPushButton#pushButton_check_net{color: white;background-color: rgba(230, 36, 0, 250);}QPushButton:hover#pushButton_check_net{color: white;background-color: rgba(247, 36, 0, 250);}QPushButton:pressed#pushButton_check_net{color: white;background-color: rgba(180, 0, 0, 250);}"
            )
            try:
                self.t_net = threading.Thread(target=self.network_check)
                self.t_net.start()  # 启动线程,即让线程开始执行
            except Exception:
                signal_qt.show_traceback_log(traceback.format_exc())
                signal_qt.show_net_info(traceback.format_exc())
        elif self.Ui.pushButton_check_net.text() == "停止检测":
            self.Ui.pushButton_check_net.setText(" 停止检测 ")
            self.Ui.pushButton_check_net.setText(" 停止检测 ")
            t = threading.Thread(target=kill_a_thread, args=(self.t_net,))
            t.start()
            signal_qt.show_net_info("\n⛔️ 网络检测已手动停止！")
            signal_qt.show_net_info(
                "================================================================================\n"
            )
            self.Ui.pushButton_check_net.setStyleSheet(
                "QPushButton#pushButton_check_net{color: white;background-color:#4C6EFF;}QPushButton:hover#pushButton_check_net{color: white;background-color: rgba(76,110,255,240)}QPushButton:pressed#pushButton_check_net{color: white;background-color:#4C6EE0}"
            )
            self.Ui.pushButton_check_net.setText("开始检测")
        else:
            try:
                if self.t_net is not None:
                    _async_raise(self.t_net.ident, SystemExit)
            except Exception as e:
                signal_qt.show_traceback_log(str(e))
                signal_qt.show_traceback_log(traceback.format_exc())

    # 检测网络界面日志显示
    def show_net_info(self, text):
        try:
            self.net_logs_show.emit(add_html(text))
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
            self.Ui.textBrowser_net_main.append(traceback.format_exc())

    # 检查javdb cookie
    def pushButton_check_javdb_cookie_clicked(self):
        input_cookie = self.Ui.plainTextEdit_cookie_javdb.toPlainText()
        if not input_cookie:
            self.Ui.label_javdb_cookie_result.setText("❌ 未填写 Cookie，影响 FC2 刮削！")
            self.show_log_text(" ❌ JavDb 未填写 Cookie，影响 FC2 刮削！可在「设置」-「网络」添加！")
            return
        self.Ui.label_javdb_cookie_result.setText("⏳ 正在检测中...")
        try:
            t = threading.Thread(target=self._check_javdb_cookie)
            t.start()  # 启动线程,即让线程开始执行
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
            signal_qt.show_log_text(traceback.format_exc())

    def _check_javdb_cookie(self):
        tips = "❌ 未填写 Cookie，影响 FC2 刮削！"
        input_cookie = self.Ui.plainTextEdit_cookie_javdb.toPlainText()
        if not input_cookie:
            self.Ui.label_javdb_cookie_result.setText(tips)
            return tips
        # self.Ui.pushButton_check_javdb_cookie.setEnabled(False)
        tips = "✅ 连接正常！"
        header = {"cookie": input_cookie}
        cookies = config.javdb
        javdb_url = getattr(config, "javdb_website", "https://javdb.com") + "/v/D16Q5?locale=zh"
        try:
            response, error = get_text_sync(javdb_url, headers=header)
            if response is None:
                if "Cookie" in error:
                    if cookies != input_cookie:
                        tips = "❌ Cookie 已过期！"
                    else:
                        tips = "❌ Cookie 已过期！已清理！(不清理无法访问)"
                        self.set_javdb_cookie.emit("")
                        self.pushButton_save_config_clicked()
                else:
                    tips = f"❌ 连接失败！请检查网络或代理设置！ {response}"
            else:
                if "The owner of this website has banned your access based on your browser's behaving" in response:
                    ip_adress = re.findall(r"(\d+\.\d+\.\d+\.\d+)", response)
                    ip_adress = ip_adress[0] + " " if ip_adress else ""
                    tips = f"❌ 你的 IP {ip_adress}被 JavDb 封了！"
                elif "Due to copyright restrictions" in response or "Access denied" in response:
                    tips = "❌ 当前 IP 被禁止访问！请使用非日本节点！"
                elif "ray-id" in response:
                    tips = "❌ 访问被 CloudFlare 拦截！"
                elif "/logout" in response:  # 已登录，有登出按钮
                    vip_info = "未开通 VIP"
                    tips = f"✅ 连接正常！（{vip_info}）"
                    if input_cookie:
                        if "icon-diamond" in response or "/v/D16Q5" in response:  # 有钻石图标或者跳到详情页表示已开通
                            vip_info = "已开通 VIP"
                        if cookies != input_cookie:  # 保存cookie
                            tips = f"✅ 连接正常！（{vip_info}）Cookie 已保存！"
                            self.pushButton_save_config_clicked()
                        else:
                            tips = f"✅ 连接正常！（{vip_info}）"

                else:
                    if cookies != input_cookie:
                        tips = "❌ Cookie 无效！请重新填写！"
                    else:
                        tips = "❌ Cookie 无效！已清理！"
                        self.set_javdb_cookie.emit("")
                        self.pushButton_save_config_clicked()
        except Exception as e:
            tips = f"❌ 连接失败！请检查网络或代理设置！ {e}"
            signal_qt.show_traceback_log(tips)
        if input_cookie:
            self.Ui.label_javdb_cookie_result.setText(tips)
            # self.Ui.pushButton_check_javdb_cookie.setEnabled(True)
        self.show_log_text(tips.replace("❌", " ❌ JavDb").replace("✅", " ✅ JavDb"))
        return tips

    # javbus cookie
    def pushButton_check_javbus_cookie_clicked(self):
        try:
            t = threading.Thread(target=self._check_javbus_cookie)
            t.start()  # 启动线程,即让线程开始执行
        except Exception:
            signal_qt.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    def _check_javbus_cookie(self):
        self.set_javbus_status.emit("⏳ 正在检测中...")

        # self.Ui.pushButton_check_javbus_cookie.setEnabled(False)
        tips = "✅ 连接正常！"
        input_cookie = self.Ui.plainTextEdit_cookie_javbus.toPlainText()
        new_cookie = {"cookie": input_cookie}
        cookies = config.javbus
        headers_o = config.headers
        headers = {
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6",
        }
        headers.update(headers_o)
        javbus_url = getattr(config, "javbus_website", "https://javbus.com") + "/FSDSS-660"

        try:
            response, error = get_text_sync(javbus_url, headers=headers, cookies=new_cookie)

            if response is None:
                tips = f"❌ 连接失败！请检查网络或代理设置！ {error}"
            elif "lostpasswd" in response:
                if input_cookie:
                    tips = "❌ Cookie 无效！"
                else:
                    tips = "❌ 当前节点需要 Cookie 才能刮削！请填写 Cookie 或更换节点！"
            elif cookies != input_cookie:
                self.pushButton_save_config_clicked()
                tips = "✅ 连接正常！Cookie 已保存！  "

        except Exception as e:
            tips = f"❌ 连接失败！请检查网络或代理设置！ {e}"

        self.show_log_text(tips.replace("❌", " ❌ JavBus").replace("✅", " ✅ JavBus"))
        self.set_javbus_status.emit(tips)
        # self.Ui.pushButton_check_javbus_cookie.setEnabled(True)
        return tips

    # endregion

    # region 其它
    # 点选择目录弹窗
    def _get_select_folder_path(self):
        media_path = self.Ui.lineEdit_movie_path.text()  # 获取待刮削目录作为打开目录
        if not media_path:
            media_path = manager.data_folder
        media_folder_path = QFileDialog.getExistingDirectory(None, "选择目录", media_path, options=self.options)
        return convert_path(media_folder_path)

    # 改回接受焦点状态
    def recover_windowflags(self):
        return

    def change_buttons_status(self):
        Flags.stop_other = True
        self.Ui.pushButton_start_cap.setText("■ 停止")
        self.Ui.pushButton_start_cap2.setText("■ 停止")
        self.Ui.pushButton_select_media_folder.setVisible(False)
        self.Ui.pushButton_start_single_file.setEnabled(False)
        self.Ui.pushButton_start_single_file.setText("正在刮削中...")
        self.Ui.pushButton_add_sub_for_all_video.setEnabled(False)
        self.Ui.pushButton_add_sub_for_all_video.setText("正在刮削中...")
        self.Ui.pushButton_show_pic_actor.setEnabled(False)
        self.Ui.pushButton_show_pic_actor.setText("刮削中...")
        self.Ui.pushButton_add_actor_info.setEnabled(False)
        self.Ui.pushButton_add_actor_info.setText("正在刮削中...")
        self.Ui.pushButton_add_actor_pic.setEnabled(False)
        self.Ui.pushButton_add_actor_pic.setText("正在刮削中...")
        self.Ui.pushButton_add_actor_pic_kodi.setEnabled(False)
        self.Ui.pushButton_add_actor_pic_kodi.setText("正在刮削中...")
        self.Ui.pushButton_del_actor_folder.setEnabled(False)
        self.Ui.pushButton_del_actor_folder.setText("正在刮削中...")
        # self.Ui.pushButton_check_and_clean_files.setEnabled(False)
        self.Ui.pushButton_check_and_clean_files.setText("正在刮削中...")
        self.Ui.pushButton_move_mp4.setEnabled(False)
        self.Ui.pushButton_move_mp4.setText("正在刮削中...")
        self.Ui.pushButton_find_missing_number.setEnabled(False)
        self.Ui.pushButton_find_missing_number.setText("正在刮削中...")
        self.Ui.pushButton_start_cap.setStyleSheet(
            "QPushButton#pushButton_start_cap{color: white;background-color: rgba(230, 66, 30, 255);}QPushButton:hover#pushButton_start_cap{color: white;background-color: rgba(247, 36, 0, 250);}QPushButton:pressed#pushButton_start_cap{color: white;background-color: rgba(180, 0, 0, 250);}"
        )
        self.Ui.pushButton_start_cap2.setStyleSheet(
            "QPushButton#pushButton_start_cap2{color: white;background-color: rgba(230, 66, 30, 255);}QPushButton:hover#pushButton_start_cap2{color: white;background-color: rgba(247, 36, 0, 250);}QPushButton:pressed#pushButton_start_cap2{color: white;background-color: rgba(180, 0, 0, 250);}"
        )

    def reset_buttons_status(self):
        self.Ui.pushButton_start_cap.setEnabled(True)
        self.Ui.pushButton_start_cap2.setEnabled(True)
        self.pushButton_start_cap.emit("开始")
        self.pushButton_start_cap2.emit("开始")
        self.Ui.pushButton_select_media_folder.setVisible(True)
        self.Ui.pushButton_start_single_file.setEnabled(True)
        self.pushButton_start_single_file.emit("刮削")
        self.Ui.pushButton_add_sub_for_all_video.setEnabled(True)
        self.pushButton_add_sub_for_all_video.emit("点击检查所有视频的字幕情况并为无字幕视频添加字幕")

        self.Ui.pushButton_show_pic_actor.setEnabled(True)
        self.pushButton_show_pic_actor.emit("查看")
        self.Ui.pushButton_add_actor_info.setEnabled(True)
        self.pushButton_add_actor_info.emit("开始补全")
        self.Ui.pushButton_add_actor_pic.setEnabled(True)
        self.pushButton_add_actor_pic.emit("开始补全")
        self.Ui.pushButton_add_actor_pic_kodi.setEnabled(True)
        self.pushButton_add_actor_pic_kodi.emit("开始补全")
        self.Ui.pushButton_del_actor_folder.setEnabled(True)
        self.pushButton_del_actor_folder.emit("清除所有.actors文件夹")
        self.Ui.pushButton_check_and_clean_files.setEnabled(True)
        self.pushButton_check_and_clean_files.emit("点击检查待刮削目录并清理文件")
        self.Ui.pushButton_move_mp4.setEnabled(True)
        self.pushButton_move_mp4.emit("开始移动")
        self.Ui.pushButton_find_missing_number.setEnabled(True)
        self.pushButton_find_missing_number.emit("检查缺失番号")

        self.Ui.pushButton_start_cap.setStyleSheet(
            "QPushButton#pushButton_start_cap{color: white;background-color:#4C6EFF;}QPushButton:hover#pushButton_start_cap{color: white;background-color: rgba(76,110,255,240)}QPushButton:pressed#pushButton_start_cap{color: white;background-color:#4C6EE0}"
        )
        self.Ui.pushButton_start_cap2.setStyleSheet(
            "QPushButton#pushButton_start_cap2{color: white;background-color:#4C6EFF;}QPushButton:hover#pushButton_start_cap2{color: white;background-color: rgba(76,110,255,240)}QPushButton:pressed#pushButton_start_cap2{color: white;background-color:#4C6EE0}"
        )
        Flags.file_mode = FileMode.Default
        self.threads_list = []
        if len(Flags.failed_list):
            self.Ui.pushButton_scraper_failed_list.setText(f"一键重新刮削当前 {len(Flags.failed_list)} 个失败文件")
        else:
            self.Ui.pushButton_scraper_failed_list.setText("当有失败任务时，点击可以一键刮削当前失败列表")

    # endregion

    # region 自动刮削
    def auto_scrape(self):
        if "timed_scrape" in config.switch_on and self.Ui.pushButton_start_cap.text() == "开始":
            time.sleep(0.1)
            timed_interval = config.timed_interval
            self.atuo_scrape_count += 1
            signal_qt.show_log_text(
                f"\n\n 🍔 已启用「循环刮削」！间隔时间：{timed_interval}！即将开始第 {self.atuo_scrape_count} 次循环刮削！"
            )
            if Flags.scrape_start_time:
                signal_qt.show_log_text(
                    " ⏰ 上次刮削时间: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(Flags.scrape_start_time))
                )
            start_new_scrape(FileMode.Default)

    def auto_start(self):
        if "auto_start" in config.switch_on:
            signal_qt.show_log_text("\n\n 🍔 已启用「软件启动后自动刮削」！即将开始自动刮削！")
            self.pushButton_start_scrape_clicked()

    # endregion


# region 外部方法定义
MyMAinWindow.load_config = load_config
MyMAinWindow.save_config = save_config
MyMAinWindow.Init_QSystemTrayIcon = Init_QSystemTrayIcon
MyMAinWindow.Init_Ui = Init_Ui
MyMAinWindow.Init_Singal = Init_Singal
MyMAinWindow.init_QTreeWidget = init_QTreeWidget
MyMAinWindow.set_style = set_style
MyMAinWindow.set_dark_style = set_dark_style
# endregion
