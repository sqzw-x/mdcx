import json
import os
import sys
import traceback

import zhconv
from PyQt5.QtGui import QFontDatabase
from lxml import etree

from models.base.file import copy_file
from models.base.path import get_main_path
from models.base.utils import singleton
from models.config.config import config
from models.signals import signal


@singleton
class Resources:
    def __init__(self):
        self._get_path()
        # region 获取资源路径
        self.sehua_title_path = self._resource_path('c_number/c_number.json')  # 内置色花数据的文件路径
        self.actor_map_backup_path = self._resource_path('mapping_table/mapping_actor.xml')  # 内置演员映射表的文件路径
        self.info_map_backup_path = self._resource_path('mapping_table/mapping_info.xml')  # 内置信息映射表的文件路径
        self.icon_ico = self._resource_path('Img/MDCx.ico')  # 任务栏图标
        self.right_menu = self._resource_path('Img/menu.svg')  # 主界面菜单按钮
        self.play_icon = self._resource_path('Img/play.svg')  # 主界面播放按钮
        self.open_folder_icon = self._resource_path('Img/folder.svg')  # 主界面打开文件夹按钮
        self.open_nfo_icon = self._resource_path('Img/nfo.svg')  # 主界面打开nfo按钮
        self.input_number_icon = self._resource_path('Img/number.svg')  # 主界面输入番号按钮
        self.input_website_icon = self._resource_path('Img/website.svg')  # 主界面输入网址按钮
        self.del_file_icon = self._resource_path('Img/delfile.svg')  # 主界面删除文件按钮
        self.del_folder_icon = self._resource_path('Img/delfolder.svg')  # 主界面删除文件夹按钮
        self.start_icon = self._resource_path('Img/start.svg')  # 主界面开始按钮
        self.stop_icon = self._resource_path('Img/stop.svg')  # 主界面开始按钮
        self.show_logs_icon = self._resource_path('Img/show.svg')  # 日志界面显示日志按钮
        self.hide_logs_icon = self._resource_path('Img/hide.svg')  # 日志界面隐藏日志按钮
        self.hide_boss_icon = self._resource_path('Img/hide_boss.svg')  # 隐藏界面按钮
        self.save_failed_list_icon = self._resource_path('Img/save.svg')  # 保存失败列表按钮
        self.clear_tree_icon = self._resource_path('Img/clear.svg')  # 主界面清空结果列表按钮
        self.home_icon = self._resource_path('Img/home.svg')
        self.log_icon = self._resource_path('Img/log.svg')
        self.tool_icon = self._resource_path('Img/tool.svg')
        self.setting_icon = self._resource_path('Img/setting.svg')
        self.net_icon = self._resource_path('Img/net.svg')
        self.help_icon = self._resource_path('Img/help.svg')
        self.mark_4k = self._resource_path('Img/4k.png')
        self.mark_8k = self._resource_path('Img/8k.png')
        self.mark_sub = self._resource_path('Img/sub.png')
        self.mark_youma = self._resource_path('Img/youma.png')
        self.mark_umr = self._resource_path('Img/umr.png')
        self.mark_leak = self._resource_path('Img/leak.png')
        self.mark_wuma = self._resource_path('Img/wuma.png')
        self.icon_4k_path = self.userdata_path('watermark/4k.png')
        self.icon_8k_path = self.userdata_path('watermark/8k.png')
        self.icon_sub_path = self.userdata_path('watermark/sub.png')
        self.icon_youma_path = self.userdata_path('watermark/youma.png')
        self.icon_umr_path = self.userdata_path('watermark/umr.png')
        self.icon_leak_path = self.userdata_path('watermark/leak.png')
        self.icon_wuma_path = self.userdata_path('watermark/wuma.png')
        # endregion

        self._check_userdata()
        self.actor_mapping_data = None  # 演员映射表数据
        self.info_mapping_data = None  # 信息映射表数据
        self.sehua_title_data = None  # 色花数据
        self._get_or_generate_local_data()
        self._get_mark_icon()
        zhconv.loaddict(self._resource_path('zhconv/zhcdict.json'))  # 加载繁简转换字典

    def get_actor_data(self, actor):
        # 初始化数据
        actor_data = {'zh_cn': actor, 'zh_tw': actor, 'jp': actor, 'keyword': [actor], 'href': '', 'has_name': False, }

        # 查询映射表
        xml_actor = self.actor_mapping_data
        if len(xml_actor):
            actor_name = ',%s,' % actor.upper()
            for each in config.full_half_char:
                actor_name = actor_name.replace(each[0], each[1])
            actor_ob = xml_actor.xpath(
                '//a[contains(translate(@keyword, "abcdefghijklmnopqrstuvwxyzａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ・", "ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ·"), $name)]',
                name=actor_name)
            if actor_ob:
                actor_ob = actor_ob[0]
                actor_data['zh_cn'] = actor_ob.get('zh_cn')
                actor_data['zh_tw'] = actor_ob.get('zh_tw')
                actor_data['jp'] = actor_ob.get('jp')
                actor_data['keyword'] = actor_ob.get('keyword').strip(',').split(',')
                actor_data['href'] = actor_ob.get('href')
                actor_data['has_name'] = True
        return actor_data

    def get_info_data(self, info):
        # 初始化数据
        info_data = {'zh_cn': info, 'zh_tw': info, 'jp': info, 'keyword': [info], 'has_name': False, }

        # 查询映射表
        xml_info = self.info_mapping_data
        if len(xml_info):
            info_name = ',%s,' % info.upper()
            for each in config.full_half_char:
                info_name = info_name.replace(each[0], each[1])
            info_ob = xml_info.xpath('//a[contains(translate(@keyword, '
                                     '"abcdefghijklmnopqrstuvwxyzａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ・", '
                                     '"ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ·"), $name)]', name=info_name)
            if info_ob:
                info_ob = info_ob[0]
                info_data['zh_cn'] = info_ob.get('zh_cn').replace('删除', '')
                info_data['zh_tw'] = info_ob.get('zh_tw').replace('删除', '')
                info_data['jp'] = info_ob.get('jp').replace('删除', '')
                info_data['keyword'] = info_ob.get('keyword').strip(',').split(',')
                info_data['has_name'] = True
        return info_data

    def _get_path(self):
        self._resources_base_path = os.path.join(get_main_path(), 'resources')
        if getattr(sys, 'frozen', False):  # 是否Bundle Resource，是否打包成exe运行
            try:
                self._resources_base_path = os.path.join(sys._MEIPASS, 'resources')
            except:
                signal.show_traceback_log(self._resources_base_path)
                signal.show_traceback_log(traceback.format_exc())
                print(self._resources_base_path, traceback.format_exc())
        self._userdata_base_path = os.path.join(config.folder, 'userdata')

    def _resource_path(self, relative_path):
        if os.path.exists(os.path.join(self._resources_base_path, relative_path)):
            pass
        else:
            signal.show_traceback_log(self._resources_base_path)
            signal.show_traceback_log(relative_path)
            signal.show_traceback_log(traceback.format_exc())
            print(self._resources_base_path, relative_path, traceback.format_exc())
        return os.path.join(self._resources_base_path, relative_path).replace('\\', '/')

    def userdata_path(self, relative_path):
        return os.path.join(self._userdata_base_path, relative_path).replace('\\', '/')

    def get_fonts(self):
        font_db = QFontDatabase()
        font_folder_path = self._resource_path('fonts')
        for f in os.listdir(font_folder_path):
            font_db.addApplicationFont(os.path.join(font_folder_path, f))  # 字体路径

    def _check_userdata(self):
        # 检查 userdata 文件夹是否存在
        if not os.path.exists(self._userdata_base_path):
            os.makedirs(self._userdata_base_path)

    def _get_or_generate_local_data(self):
        # 载入 c_numuber.json 数据
        with open(self.sehua_title_path, 'r', encoding='UTF-8') as data:
            self.sehua_title_data = json.load(data)

        # 载入 mapping_actor.xml mapping_info.xml 数据
        actor_map_local_path = self.userdata_path('mapping_actor.xml')
        info_map_local_path = self.userdata_path('mapping_info.xml')
        if not os.path.exists(actor_map_local_path):
            if not copy_file(self.actor_map_backup_path, actor_map_local_path):
                actor_map_local_path = self.actor_map_backup_path
        if not os.path.exists(info_map_local_path):
            if not copy_file(self.info_map_backup_path, info_map_local_path):
                info_map_local_path = self.info_map_backup_path
        try:
            parser = etree.HTMLParser(encoding="utf-8")
            with open(actor_map_local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.actor_mapping_data = etree.HTML(content.encode('utf-8'), parser=parser)
            with open(info_map_local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.info_mapping_data = etree.HTML(content.encode('utf-8'), parser=parser)
        except Exception as e:
            signal.show_log_text(f' {actor_map_local_path} 读取失败！请检查该文件是否存在问题！如需重置请删除该文件！错误信息：\n{str(e)}')
            signal.show_traceback_log(traceback.format_exc())
            signal.show_log_text(traceback.format_exc())
            self.actor_mapping_data = {}

    def _get_mark_icon(self):
        mark_folder = self.userdata_path('watermark')
        if not os.path.isdir(mark_folder):
            os.makedirs(mark_folder)
        if not os.path.isfile(self.icon_4k_path):
            copy_file(self.mark_4k, self.icon_4k_path)
        if not os.path.isfile(self.icon_8k_path):
            copy_file(self.mark_8k, self.icon_8k_path)
        if not os.path.isfile(self.icon_sub_path):
            copy_file(self.mark_sub, self.icon_sub_path)
        if not os.path.isfile(self.icon_youma_path):
            copy_file(self.mark_youma, self.icon_youma_path)
        if not os.path.isfile(self.icon_umr_path):
            copy_file(self.mark_umr, self.icon_umr_path)
        if not os.path.isfile(self.icon_leak_path):
            copy_file(self.mark_leak, self.icon_leak_path)
        if not os.path.isfile(self.icon_wuma_path):
            copy_file(self.mark_wuma, self.icon_wuma_path)


resources = Resources()
