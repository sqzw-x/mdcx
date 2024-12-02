def set_style(self):
    if self.dark_mode:
        self.set_dark_style()
        return

    # 控件美化 左侧栏样式
    self.Ui.widget_setting.setStyleSheet(f'''
        QWidget#widget_setting{{
            background: #F5F5F6;
            border-top-left-radius: {self.window_radius}px;
            border-bottom-left-radius: {self.window_radius}px;
        }}
        QPushButton#pushButton_main,#pushButton_log,#pushButton_tool,#pushButton_setting,#pushButton_net,#pushButton_about{{
            font-size: 14px;
            color: black;
            border-width: 9px;
            border-color: gray;
            border-radius: 10px;
            text-align : left;
            qproperty-iconSize: 20px 20px;
            padding-left: 20px;
        }}
        QLabel#label_show_version{{
            font-size: 13px;
            color: rgba(20, 20, 20, 250);
            border: 0px solid rgba(255, 255, 255, 80);
        }}
        ''')
    # 主界面
    self.Ui.page_main.setStyleSheet('''
        QLabel#label_number1,#label_actor1,#label_title1,#label_poster1,#label_number,#label_actor,#label_title,#label_poster1{
            font-size: 16px;
            font-weight: bold;
            background-color: rgba(246, 246, 246, 0);
            border: 0px solid rgba(0, 0, 0, 80);
        }
        QLabel#label_file_path{
            font-size: 16px;
            color: black;
            background-color: rgba(246, 246, 246, 0);
            font-weight: bold;
            border: 0px solid rgba(0, 0, 0, 80);
        }
        QLabel#label_poster_size{
            color: rgba(0, 0, 0, 200);
        }
        QLabel#label_poster,#label_thumb{
            border: 1px solid rgba(60, 60, 60, 100);
        }
        QGroupBox{
            background-color: rgba(246, 246, 246, 0);
        }
        ''')
    # 工具页
    self.Ui.page_tool.setStyleSheet('''
        * {
            font-size: 13px;
        }
        QScrollArea{
            background-color: rgba(246, 246, 246, 0);
            border-color: rgba(246, 246, 246, 0);
        }
        QWidget#scrollAreaWidgetContents_9{
            background-color: rgba(246, 246, 246, 0);
            border-color: rgba(246, 246, 246, 255);
        }

        QLabel{
            font-size:13px;
            border: 0px solid rgba(0, 0, 0, 80);
        }
        QLineEdit{
            font-size:13px;
            border:0px solid rgba(130, 30, 30, 20);
            border-radius: 15px;
        }
        QComboBox{
            font-size: 13px;
            color: black;
        }
        QGroupBox{
            background-color: rgba(245,245,246,220);
            border-radius: 10px;
        }
        ''')
    # 使用帮助页
    self.Ui.page_about.setStyleSheet('''
        * {
            font-size: 13px;
        }
        QTextBrowser{
            font-family: Consolas, 'PingFang SC', 'Microsoft YaHei UI', 'Noto Color Emoji', 'Segoe UI Emoji';
            font-size: 13px;
            border: 0px solid #BEBEBE;
            background-color: rgba(246,246,246,0);
            padding: 2px, 2px;
        }
        ''')
    # 设置页
    self.Ui.page_setting.setStyleSheet('''
        * {
            font-size:13px;
        }
        QScrollArea{
            background-color: rgba(246, 246, 246, 0);
            border-color: rgba(246, 246, 246, 255);
        }
        QTabWidget{
            background-color: rgba(246, 246, 246, 0);
            border-color: rgba(246, 246, 246, 255);
        }
        QTabWidget::tab-bar {
            alignment: center;
        }
        QTabBar::tab{
            color: black;
            border:1px solid #E8E8E8;
            min-height: 3ex;
            min-width: 6ex;
            padding: 2px;
            background-color:#FFFFFF;
            border-radius: 1px;
        }
        QTabBar::tab:selected{
            color: white;
            font-weight:bold;
            border-bottom: 2px solid #2080F7;
            background-color:#2080F7;
            border-radius: 1px;
        }
        QWidget#tab1,#scrollAreaWidgetContents,#tab2,#scrollAreaWidgetContents_2,#tab3,#scrollAreaWidgetContents_3,#tab4,#scrollAreaWidgetContents_4,#tab5,#scrollAreaWidgetContents_5,#tab,#tab_2,#tab_3,#tab_4,#tab_5,#tab_6,#tab_7,#scrollAreaWidgetContents_6,#scrollAreaWidgetContents_7,#scrollAreaWidgetContents_8,#scrollAreaWidgetContents_10,#scrollAreaWidgetContents_11,#scrollAreaWidgetContents_12,#scrollAreaWidgetContents_13{
            background-color: rgba(255, 255, 255, 255);
            border-color: rgba(246, 246, 246, 255);
        }
        QLabel{
            font-size:13px;
            border:0px solid rgba(0, 0, 0, 80);
        }
        QLabel#label_config{
            font-size:13px;
            border:0px solid rgba(230, 230, 230, 80);
            background: rgba(246, 246, 246, 220);
        }

        QLineEdit{
            font-size:13px;
            border:0px solid rgba(130, 30, 30, 20);
            border-radius: 15px;
        }
        QRadioButton{
            font-size:13px;
        }
        QComboBox{
            font-size:13px;
        }
        QCheckBox{
            font-size:13px;
        }
        QPlainTextEdit{
            font-size:13px;
        }
        QGroupBox{
            background-color: rgba(245,245,246,220);
            border-radius: 10px;
        }
        ''')
    # 整个页面
    self.Ui.centralwidget.setStyleSheet(f'''
        * {{
            font-family: Consolas, 'PingFang SC', 'Microsoft YaHei UI', 'Noto Color Emoji', 'Segoe UI Emoji';
            font-size:13px;
            color: black;
        }}
        QTreeWidget
        {{
            background-color: rgba(246, 246, 246, 0);
            font-size: 12px;
            border:0px solid rgb(120,120,120);
        }}
        QWidget#centralwidget{{
            background: #FFFFFF;
            border: {self.window_border}px solid rgba(20,20,20,50);
            border-radius: {self.window_radius}px;
       }}
        QTextBrowser#textBrowser_log_main,#textBrowser_net_main{{
            font-size:13px;
            border: 0px solid #BEBEBE;
            background-color: rgba(246,246,246,0);
            padding: 2px, 2px;
        }}
        QTextBrowser#textBrowser_log_main_2{{
            font-size:13px;
            border-radius: 0px;
            border-top: 1px solid #BEBEBE;
            background-color: rgba(238,245,245,60);
            padding: 2px, 2px;
        }}
        QTextBrowser#textBrowser_log_main_3{{
            font-size:13px;
            border-radius: 0px;
            border-right: 1px solid #EDEDED;
            background-color: rgba(239,255,252,240);
            padding: 2px, 2px;
        }}
        QTextBrowser#textBrowser_show_success_list,#textBrowser_show_tips{{
            font-size: 13px;
            background-color: rgba(240, 245, 240, 240);
            border: 1px solid #BEBEBE;
            padding: 2px;
        }}
        QWidget#widget_show_success,#widget_show_tips,#widget_nfo{{
            background-color: rgba(246,246,246,255);
            border: 1px solid rgba(20,20,20,50);
            border-radius: 10px;
       }}
        QWidget#scrollAreaWidgetContents_nfo{{
            background-color: rgba(240, 245, 240, 240);
            border: 0px solid rgba(0,0,0,150);
        }}
        QLineEdit{{
            font-size:14px;
            background:white;
            border-radius:10px;
            border: 1px solid rgba(20,20,20,200);
            padding: 2px;
        }}
        QTextEdit#textEdit_nfo_outline,#textEdit_nfo_originalplot,#textEdit_nfo_tag{{
            font-size:14px;
            background:white;
            border: 1px solid rgba(20,20,20,200);
            padding: 2px;
        }}
        QToolTip{{border: 1px solid;border-radius: 8px;border-color: gray;background:white;color:black;padding: 4px 8px;}}
        QPushButton#pushButton_right_menu,#pushButton_play,#pushButton_open_folder,#pushButton_open_nfo,#pushButton_show_hide_logs,#pushButton_save_failed_list,#pushButton_tree_clear{{
            background-color: rgba(181, 181, 181, 0);
            border-radius:10px;
            border: 0px solid rgba(0, 0, 0, 80);
        }}
        QPushButton:hover#pushButton_right_menu,:hover#pushButton_play,:hover#pushButton_open_folder,:hover#pushButton_open_nfo,:hover#pushButton_show_hide_logs,:hover#pushButton_save_failed_list,:hover#pushButton_tree_clear{{
            background-color: rgba(181, 181, 181, 120);
        }}
        QPushButton:pressed#pushButton_right_menu,:pressed#pushButton_play,:pressed#pushButton_open_folder,:pressed#pushButton_open_nfo,:pressed#pushButton_show_hide_logs,:pressed#pushButton_save_failed_list,:pressed#pushButton_tree_clear{{
            background-color: rgba(150, 150, 150, 120);
        }}
        QPushButton#pushButton_save_new_config,#pushButton_init_config,#pushButton_success_list_close,#pushButton_success_list_save,#pushButton_success_list_clear,#pushButton_show_tips_close,#pushButton_nfo_close,#pushButton_nfo_save,#pushButton_show_pic_actor,#pushButton_add_actor_pic,#pushButton_add_actor_info,#pushButton_add_actor_pic_kodi,#pushButton_del_actor_folder,#pushButton_move_mp4,#pushButton_select_file,#pushButton_select_local_library,#pushButton_select_netdisk_path,#pushButton_select_localdisk_path,#pushButton_creat_symlink,#pushButton_find_missing_number,#pushButton_select_thumb,#pushButton_start_single_file,#pushButton_select_file_clear_info,#pushButton_add_sub_for_all_video,#pushButton_view_failed_list,#pushButton_select_media_folder,#pushButton_select_media_folder_setting_page,#pushButton_select_softlink_folder,#pushButton_select_sucess_folder,#pushButton_select_failed_folder,#pushButton_view_success_file,#pushButton_select_subtitle_folder,#pushButton_select_actor_photo_folder,#pushButton_select_actor_info_db,#pushButton_select_config_folder,#pushButton_add_all_extrafanart_copy,#pushButton_del_all_extrafanart_copy,#pushButton_add_all_extras,#pushButton_del_all_extras,#pushButton_add_all_theme_videos,#pushButton_del_all_theme_videos,#pushButton_check_and_clean_files,#pushButton_search_by_number,#pushButton_search_by_url{{
            font-size:14px;
            background-color: rgba(220, 220,220, 255);
            border-color:black;
            border-width:8px;
            border-radius:20px;
            padding: 2px, 2px;
        }}
        QPushButton:hover#pushButton_show_pic_actor,:hover#pushButton_add_actor_pic,:hover#pushButton_add_actor_info,:hover#pushButton_add_actor_pic_kodi,:hover#pushButton_del_actor_folder,:hover#pushButton_add_sub_for_all_video,:hover#pushButton_view_failed_list,:hover#pushButton_select_media_folder,:hover#pushButton_select_media_folder_setting_page,:hover#pushButton_select_softlink_folder,:hover#pushButton_select_sucess_folder,:hover#pushButton_select_failed_folder,:hover#pushButton_view_success_file,:hover#pushButton_select_subtitle_folder,:hover#pushButton_select_actor_photo_folder,:hover#pushButton_select_actor_info_db,:hover#pushButton_select_config_folder,:hover#pushButton_add_all_extrafanart_copy,:hover#pushButton_del_all_extrafanart_copy,:hover#pushButton_add_all_extras,:hover#pushButton_del_all_extras,:hover#pushButton_add_all_theme_videos,:hover#pushButton_del_all_theme_videos,:hover#pushButton_check_and_clean_files,:hover#pushButton_search_by_number,:hover#pushButton_search_by_url{{
            color: white;
            background-color: rgba(76,110,255,240);
            font-weight:bold;
        }}
        QPushButton:pressed#pushButton_show_pic_actor,:pressed#pushButton_add_actor_pic,:pressed#pushButton_add_actor_info,:pressed#pushButton_add_actor_pic_kodi,:pressed#pushButton_del_actor_folder,:pressed#pushButton_add_sub_for_all_video,:pressed#pushButton_view_failed_list,:pressed#pushButton_select_media_folder,:pressed#pushButton_select_media_folder_setting_page,:pressed#pushButton_select_softlink_folder,:pressed#pushButton_select_sucess_folder,:pressed#pushButton_select_failed_folder,:pressed#pushButton_view_success_file,:pressed#pushButton_select_subtitle_folder,:pressed#pushButton_select_actor_photo_folder,:pressed#pushButton_select_actor_info_db,:pressed#pushButton_select_config_folder,:pressed#pushButton_add_all_extrafanart_copy,:pressed#pushButton_del_all_extrafanart_copy,:pressed#pushButton_add_all_extras,:pressed#pushButton_del_all_extras,:pressed#pushButton_add_all_theme_videos,:pressed#pushButton_del_all_theme_videos,:pressed#pushButton_check_and_clean_files,:pressed#pushButton_search_by_number,:pressed#pushButton_search_by_url{{
            background-color:#4C6EE0;
            border-color:black;
            border-width:14px;
            font-weight:bold;
        }}
        QPushButton#pushButton_save_config{{
            color: white;
            font-size:14px;
            background-color:#4C6EFF;
            border-radius:25px;
            padding: 2px, 2px;
        }}
        QPushButton:hover#pushButton_save_config,:hover#pushButton_save_new_config,:hover#pushButton_init_config,:hover#pushButton_success_list_close,:hover#pushButton_success_list_save,:hover#pushButton_success_list_clear,:hover#pushButton_show_tips_close,:hover#pushButton_nfo_close,:hover#pushButton_nfo_save,:hover#pushButton_scraper_failed_list{{
            color: white;
            background-color: rgba(76,110,255,240);
            font-weight:bold;
            }}
        QPushButton:pressed#pushButton_save_config,:pressed#pushButton_save_new_config,:pressed#pushButton_init_config,:pressed#pushButton_success_list_close,:pressed#pushButton_success_list_save,:pressed#pushButton_success_list_clear,:pressed#pushButton_show_tips_close,:pressed#pushButton_nfo_close,:pressed#pushButton_nfo_save,:pressed#pushButton_scraper_failed_list{{
            background-color:#4C6EE0;
            border-color:black;
            border-width:14px;
            font-weight:bold;
        }}
        QPushButton#pushButton_start_cap,#pushButton_start_cap2,#pushButton_check_net,#pushButton_scraper_failed_list{{
            color: white;
            font-size:14px;
            background-color:#4C6EFF;
            border-radius:20px;
            padding: 2px, 2px;
            font-weight:bold;
        }}
        QPushButton:hover#pushButton_start_cap,:hover#pushButton_start_cap2,:hover#pushButton_check_net,:hover#pushButton_move_mp4,:hover#pushButton_select_file,:hover#pushButton_select_local_library,:hover#pushButton_select_netdisk_path,:hover#pushButton_select_localdisk_path,:hover#pushButton_creat_symlink,:hover#pushButton_find_missing_number,:hover#pushButton_select_thumb,:hover#pushButton_start_single_file,:hover#pushButton_select_file_clear_info{{
            color: white;
            background-color: rgba(76,110,255,240);
            font-weight:bold;
            }}
        QPushButton:pressed#pushButton_start_cap,:pressed#pushButton_start_cap2,:pressed#pushButton_check_net,:pressed#pushButton_move_mp4,:pressed#pushButton_select_file,:pressed#pushButton_select_local_library,:pressed#pushButton_select_netdisk_path,:pressed#pushButton_select_localdisk_path,:pressed#pushButton_creat_symlink,:pressed#pushButton_find_missing_number,:pressed#pushButton_select_thumb,:pressed#pushButton_start_single_file,:press#pushButton_select_file_clear_info{{
            background-color:#4C6EE0;
            border-color:black;
            border-width:12px;
            font-weight:bold;
        }}
        QProgressBar::chunk{{
            background-color: #5777FF;
            width: 3px; /*区块宽度*/
            margin: 0px;
        }}
        ''')


def set_dark_style(self):
    # 控件美化 左侧栏样式 暗黑模式
    self.Ui.widget_setting.setStyleSheet(f'''
        QWidget#widget_setting{{
            background: #1F272F;
            border-top-left-radius: {self.window_radius}px;
            border-bottom-left-radius: {self.window_radius}px;
        }}
        QPushButton#pushButton_main,#pushButton_log,#pushButton_tool,#pushButton_setting,#pushButton_net,#pushButton_about{{
            font-size: 14px;
            color: white;
            border-width: 9px;
            border-color: gray;
            border-radius: 10px;
            text-align : left;
            qproperty-iconSize: 20px 20px;
            padding-left: 20px;
        }}
        QLabel#label_show_version{{
            font-size: 13px;
            color: rgba(210, 210, 210, 250);
            border: 0px solid rgba(255, 255, 255, 80);
        }}
        ''')
    # 主界面
    self.Ui.page_main.setStyleSheet('''
        QLabel#label_number1,#label_actor1,#label_title1,#label_poster1,#label_number,#label_actor,#label_title,#label_poster1{
            font-size: 16px;
            font-weight: bold;
            background-color: rgba(246, 246, 246, 0);
            border: 0px solid rgba(0, 0, 0, 80);
        }
        QLabel#label_file_path{
            font-size: 16px;
            color: white;
            background-color: rgba(246, 246, 246, 0);
            font-weight: bold;
            border: 0px solid rgba(0, 0, 0, 80);
        }
        QLabel#label_poster_size{
            color: rgba(255, 255, 255, 200);
        }
        QLabel#label_poster,#label_thumb{
            border: 1px solid rgba(255, 255, 255, 200);
        }
        QGroupBox{
            background-color: rgba(246, 246, 246, 0);
        }
        ''')
    # 工具页
    self.Ui.page_tool.setStyleSheet('''
        * {
            font-size: 13px;
        }
        QScrollArea{
            background-color: rgba(246, 246, 246, 0);
            border-color: rgba(246, 246, 246, 0);
        }
        QWidget#scrollAreaWidgetContents_9{
            background-color: rgba(246, 246, 246, 0);
            border-color: rgba(246, 246, 246, 255);
        }

        QLabel{
            font-size:13px;
            border: 0px solid rgba(0, 0, 0, 80);
        }

        QGroupBox{
            background-color: rgba(180, 180, 180, 20);
            border-radius: 10px;
        }
        ''')
    # 使用帮助页
    self.Ui.page_about.setStyleSheet('''
        * {
            font-size: 13px;
        }
        QTextBrowser{
            font-family: Consolas, 'PingFang SC', 'Microsoft YaHei UI', 'Noto Color Emoji', 'Segoe UI Emoji';
            font-size: 13px;
            border: 0px solid #BEBEBE;
            background-color: rgba(246,246,246,0);
            padding: 2px, 2px;
        }
        ''')
    # 设置页
    self.Ui.page_setting.setStyleSheet('''
        * {
            font-size:13px;
        }
        QScrollArea{
            background-color: rgba(246, 246, 246, 0);
            border-color: rgba(246, 246, 246, 0);
        }
        QTabWidget{
            background-color: rgba(246, 246, 246, 0);
            border-color: rgba(246, 246, 246, 0);
        }
        QTabWidget::tab-bar {
            alignment: center;
        }
        QTabBar::tab{
            border:1px solid #1F272F;
            min-height: 3ex;
            min-width: 6ex;
            padding: 2px;
            background-color:#242D37;
            border-radius: 2px;
        }
        QTabBar::tab:selected{
            font-weight:bold;
            border-bottom: 2px solid #2080F7;
            background-color:#2080F7;
            border-radius: 1px;
        }
        QWidget#tab1,#scrollAreaWidgetContents,#tab2,#scrollAreaWidgetContents_2,#tab3,#scrollAreaWidgetContents_3,#tab4,#scrollAreaWidgetContents_4,#tab5,#scrollAreaWidgetContents_5,#tab,#tab_2,#tab_3,#tab_4,#tab_5,#tab_6,#tab_7,#scrollAreaWidgetContents_6,#scrollAreaWidgetContents_7,#scrollAreaWidgetContents_8,#scrollAreaWidgetContents_10,#scrollAreaWidgetContents_11,#scrollAreaWidgetContents_12,#scrollAreaWidgetContents_13{
            background-color: #18222D;
            border-color: rgba(246, 246, 246, 0);
        }
        QLabel{
            font-size:13px;
            border:0px solid rgba(0, 0, 0, 80);
        }
        QLabel#label_config{
            font-size:13px;
            border:0px solid rgba(0, 0, 0, 80);
            background: rgba(31,39,47,230);
        }
        QLineEdit{
            font-size:13px;
            border:0px solid rgba(130, 30, 30, 20);
            border-radius: 15px;
        }
        QRadioButton{
            font-size:13px;
        }
        QCheckBox{
            font-size:13px;
        }
        QPlainTextEdit{
            font-size:13px;
            background:#18222D;
            border-radius: 4px;
        }
        QGroupBox{
            background-color: rgba(180, 180, 180, 20);
            border-radius: 10px;
        }
        QPushButton#pushButton_scrape_note,#pushButton_field_tips_website,#pushButton_field_tips_nfo,#pushButton_check_javdb_cookie{
            color: black;
        }
        ''')
    # 整个页面
    self.Ui.centralwidget.setStyleSheet(f'''
        * {{
            font-family: Consolas, 'PingFang SC', 'Microsoft YaHei UI', 'Noto Color Emoji', 'Segoe UI Emoji';
            font-size:13px;
            color: white;
        }}
        QTreeWidget
        {{
            background-color: rgba(246, 246, 246, 0);
            font-size: 12px;
            border:0px solid rgb(120,120,120);
        }}
        QWidget#centralwidget{{
            background: #18222D;
            border: {self.window_border}px solid rgba(20,20,20,50);
            border-radius: {self.window_radius}px;
       }}
        QTextBrowser#textBrowser_log_main,#textBrowser_net_main{{
            font-size:13px;
            border: 0px solid #BEBEBE;
            background-color: rgba(246,246,246,0);
            padding: 2px, 2px;
        }}
        QTextBrowser#textBrowser_log_main_2{{
            font-size:13px;
            border-radius: 0px;
            border-top: 1px solid #BEBEBE;
            background-color: #18222D;
            padding: 2px, 2px;
        }}
        QTextBrowser#textBrowser_log_main_3{{
            font-size:13px;
            border-radius: 0px;
            border-right: 1px solid #20303F;
            background-color: #1F272F;
            padding: 2px, 2px;
        }}
        QTextBrowser#textBrowser_show_success_list,#textBrowser_show_tips{{
            font-size: 13px;
            border: 1px solid #BEBEBE;
            background-color: #18222D;
            padding: 2px;
        }}
        QWidget#widget_show_success,#widget_show_tips,#widget_nfo{{
            background-color: #1F272F;
            border: 1px solid rgba(240,240,240,150);
            border-radius: 10px;
       }}
        QWidget#scrollAreaWidgetContents_nfo{{
            background-color: #18222D;
            border: 0px solid rgba(0,0,0,150);
        }}
        QLineEdit{{
            font-size:13px;
            background:#18222D;
            border-radius:20px;
            border: 1px solid rgba(240,240,240,200);
            padding: 2px;
        }}
        QTextEdit#textEdit_nfo_outline,#textEdit_nfo_originalplot,#textEdit_nfo_tag{{
            font-size:13px;
            background:#18222D;
            border: 1px solid rgba(240,240,240,200);
            padding: 2px;
        }}
        QToolTip{{border: 1px solid;border-radius: 8px;border-color: gray;background:white;color:black;padding: 4px 8px;}}
        QPushButton#pushButton_right_menu,#pushButton_play,#pushButton_open_folder,#pushButton_open_nfo,#pushButton_show_hide_logs,#pushButton_save_failed_list,#pushButton_tree_clear{{
            background-color: rgba(181, 181, 181, 0);
            border-radius:10px;
            border: 0px solid rgba(0, 0, 0, 80);
        }}
        QPushButton:hover#pushButton_right_menu,:hover#pushButton_play,:hover#pushButton_open_folder,:hover#pushButton_open_nfo,:hover#pushButton_show_hide_logs,:hover#pushButton_save_failed_list,:hover#pushButton_tree_clear{{
            background-color: rgba(181, 181, 181, 120);
        }}
        QPushButton:pressed#pushButton_right_menu,:pressed#pushButton_play,:pressed#pushButton_open_folder,:pressed#pushButton_open_nfo,:pressed#pushButton_show_hide_logs,:pressed#pushButton_save_failed_list,:pressed#pushButton_tree_clear{{
            background-color: rgba(150, 150, 150, 120);
        }}
        QPushButton#pushButton_save_new_config,#pushButton_init_config,#pushButton_success_list_close,#pushButton_success_list_save,#pushButton_success_list_clear,#pushButton_show_tips_close,#pushButton_nfo_close,#pushButton_nfo_save,#pushButton_show_pic_actor,#pushButton_add_actor_pic,#pushButton_add_actor_info,#pushButton_add_actor_pic_kodi,#pushButton_del_actor_folder,#pushButton_move_mp4,#pushButton_select_file,#pushButton_select_local_library,#pushButton_select_netdisk_path,#pushButton_select_localdisk_path,#pushButton_creat_symlink,#pushButton_find_missing_number,#pushButton_select_thumb,#pushButton_start_single_file,#pushButton_select_file_clear_info,#pushButton_add_sub_for_all_video,#pushButton_view_failed_list,#pushButton_select_media_folder,#pushButton_select_media_folder_setting_page,#pushButton_select_softlink_folder,#pushButton_select_sucess_folder,#pushButton_select_failed_folder,#pushButton_view_success_file,#pushButton_select_subtitle_folder,#pushButton_select_actor_photo_folder,#pushButton_select_actor_info_db,#pushButton_select_config_folder,#pushButton_add_all_extrafanart_copy,#pushButton_del_all_extrafanart_copy,#pushButton_add_all_extras,#pushButton_del_all_extras,#pushButton_add_all_theme_videos,#pushButton_del_all_theme_videos,#pushButton_check_and_clean_files,#pushButton_search_by_number,#pushButton_search_by_url{{
            font-size:14px;
            background-color: rgba(220, 220,220, 50);
            border-color:black;
            border-width:8px;
            border-radius:20px;
            padding: 2px, 2px;
        }}
        QPushButton:hover#pushButton_show_pic_actor,:hover#pushButton_add_actor_pic,:hover#pushButton_add_actor_info,:hover#pushButton_add_actor_pic_kodi,:hover#pushButton_del_actor_folder,:hover#pushButton_add_sub_for_all_video,:hover#pushButton_view_failed_list,:hover#pushButton_scraper_failed_list,:hover#pushButton_select_media_folder,:hover#pushButton_select_media_folder_setting_page,:hover#pushButton_select_softlink_folder,:hover#pushButton_select_sucess_folder,:hover#pushButton_select_failed_folder,:hover#pushButton_view_success_file,:hover#pushButton_select_subtitle_folder,:hover#pushButton_select_actor_photo_folder,:hover#pushButton_select_actor_info_db,:hover#pushButton_select_config_folder,:hover#pushButton_add_all_extrafanart_copy,:hover#pushButton_del_all_extrafanart_copy,:hover#pushButton_add_all_extras,:hover#pushButton_del_all_extras,:hover#pushButton_add_all_theme_videos,:hover#pushButton_del_all_theme_videos,:hover#pushButton_check_and_clean_files,:hover#pushButton_search_by_number,:hover#pushButton_search_by_url{{
            color: white;
            background-color: rgba(76,110,255,240);
            font-weight:bold;
        }}
        QPushButton:pressed#pushButton_show_pic_actor,:pressed#pushButton_add_actor_pic,:pressed#pushButton_add_actor_info,:pressed#pushButton_add_actor_pic_kodi,:pressed#pushButton_del_actor_folder,:pressed#pushButton_add_sub_for_all_video,:pressed#pushButton_view_failed_list,:pressed#pushButton_scraper_failed_list,:pressed#pushButton_select_media_folder,:pressed#pushButton_select_media_folder_setting_page,:pressed#pushButton_select_softlink_folder,:pressed#pushButton_select_sucess_folder,:pressed#pushButton_select_failed_folder,:pressed#pushButton_view_success_file,:pressed#pushButton_select_subtitle_folder,:pressed#pushButton_select_actor_photo_folder,:pressed#pushButton_select_actor_info_db,:pressed#pushButton_select_config_folder,:pressed#pushButton_add_all_extrafanart_copy,:pressed#pushButton_del_all_extrafanart_copy,:pressed#pushButton_add_all_extras,:pressed#pushButton_del_all_extras,:pressed#pushButton_add_all_theme_videos,:pressed#pushButton_del_all_theme_videos,:pressed#pushButton_check_and_clean_files,:pressed#pushButton_search_by_number,:pressed#pushButton_search_by_url{{
            background-color:#4C6EE0;
            border-color:black;
            border-width:14px;
            font-weight:bold;
        }}
        QPushButton#pushButton_save_config{{
            color: white;
            font-size:14px;
            background-color:#4C6EFF;
            border-radius:25px;
            padding: 2px, 2px;
        }}
        QPushButton:hover#pushButton_save_config,:hover#pushButton_save_new_config,:hover#pushButton_init_config,:hover#pushButton_success_list_close,:hover#pushButton_success_list_save,:hover#pushButton_success_list_clear,:hover#pushButton_show_tips_close,:hover#pushButton_nfo_close,:hover#pushButton_nfo_save{{
            color: white;
            background-color: rgba(76,110,255,240);
            font-weight:bold;
        }}
        QPushButton:pressed#pushButton_save_config,:pressed#pushButton_save_new_config,:pressed#pushButton_init_config,:pressed#pushButton_success_list_close,:pressed#pushButton_success_list_save,:pressed#pushButton_success_list_clear,pressed#pushButton_show_tips_close,:pressed#pushButton_nfo_close,:pressed#pushButton_nfo_save{{
            background-color:#4C6EE0;
            border-color:black;
            border-width:14px;
            font-weight:bold;
        }}
        QPushButton#pushButton_start_cap,#pushButton_start_cap2,#pushButton_check_net,#pushButton_scraper_failed_list{{
            color: white;
            font-size:14px;
            background-color:#4C6EFF;
            border-radius:20px;
            padding: 2px, 2px;
            font-weight:bold;
        }}
        QPushButton:hover#pushButton_start_cap,:hover#pushButton_start_cap2,:hover#pushButton_check_net,:hover#pushButton_move_mp4,:hover#pushButton_select_file,:hover#pushButton_select_local_library,:hover#pushButton_select_netdisk_path,:hover#pushButton_select_localdisk_path,:hover#pushButton_creat_symlink,:hover#pushButton_find_missing_number,:hover#pushButton_select_thumb,:hover#pushButton_start_single_file,:hover#pushButton_select_file_clear_info{{
            color: white;
            background-color: rgba(76,110,255,240);
            font-weight:bold;
            }}
        QPushButton:pressed#pushButton_start_cap,:pressed#pushButton_start_cap2,:pressed#pushButton_check_net,:pressed#pushButton_move_mp4,:pressed#pushButton_select_file,:pressed#pushButton_select_local_library,:pressed#pushButton_select_netdisk_path,:pressed#pushButton_select_localdisk_path,:pressed#pushButton_creat_symlink,:pressed#pushButton_find_missing_number,:pressed#pushButton_select_thumb,:pressed#pushButton_start_single_file,:press#pushButton_select_file_clear_info{{
            background-color:#4C6EE0;
            border-color:black;
            border-width:12px;
            font-weight:bold;
        }}
        QComboBox{{
            font-size:13px;
            color: white;
            background:#18222D;
            border-radius: 15px;
        }}
        QComboBox::drop-down:!editable {{
            subcontrol-position: right;
            margin: 10px;
            height: 10px;
            width: 10px;
            border-radius: 5px;
            background: lightgreen;
        }}
        QComboBox::drop-down:!editable:on {{
            background: lightgreen;
        }}

        QComboBox QAbstractItemView {{
            color:white;
            background: #1F272F;
            selection-color:white;
            selection-background-color: #18222D;
        }}
        QScrollBar:vertical{{
            border-radius:2px;
            background:#242D37;
            padding-top:16px;
            padding-bottom:16px
        }}
        QScrollBar::handle:vertical{{
            border-radius:2px;
            background:#484F57;
        }}
        QScrollBar::add-page:vertical{{
            background:#242D37;
        }}
        QScrollBar::sub-page:vertical{{
            border-radius:2px;
            background:#242D37;
        }}
        QProgressBar::chunk{{
            background-color: #5777FF;
            width: 3px; /*区块宽度*/
            margin: 0px;
        }}
        ''')
