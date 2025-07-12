import os

from ..base.file import copy_file, move_file, split_path
from ..config.manager import config
from ..entity.enums import FileMode
from ..signals import signal
from .file import get_file_info, movie_lists
from .scraper import start_new_scrape
from .utils import get_movie_path_setting


def add_sub_for_all_video():
    signal.change_buttons_status.emit()
    sub_add = True
    signal.show_log_text("开始检查无字幕视频并为其添加字幕！\n")
    if config.subtitle_folder == "" or not os.path.exists(config.subtitle_folder):
        sub_add = False
        signal.show_log_text("字幕文件夹不存在！\n只能检查无字幕视频，无法添加字幕！")
        signal.show_log_text("================================================================================")

    movie_path, success_folder, failed_folder, escape_folder_list, extrafanart_folder, softlink_path = (
        get_movie_path_setting()
    )
    signal.show_log_text(f" 🖥 Movie path: {movie_path} \n 🔎 正在检查所有视频，请稍候...")
    if config.subtitle_add_chs:
        signal.show_log_text(" 如果字幕文件名不以 .chs 结尾，则会自动添加！\n")
    else:
        signal.show_log_text(" 如果字幕文件名以 .chs 结尾，将被自动删除！\n")
    movie_type = config.media_type
    movie_list = movie_lists([], movie_type, movie_path)  # 获取所有需要刮削的影片列表
    sub_type_list = config.sub_type.split("|")  # 本地字幕文件后缀

    add_count = 0
    no_sub_count = 0
    new_sub_movie_list = []
    for movie in movie_list:
        file_info = get_file_info(movie, copy_sub=False)
        json_data, number, folder_old_path, file_name, file_ex, sub_list, file_show_name, file_show_path = file_info
        has_sub = json_data["has_sub"]  # 视频中文字幕标识
        if not has_sub:
            no_sub_count += 1
            signal.show_log_text(f" No sub:'{movie}' ")
            cd_part = json_data["cd_part"]
            if sub_add:
                add_succ = False
                for sub_type in sub_type_list:
                    sub_path = os.path.join(config.subtitle_folder, (number + cd_part + sub_type))
                    sub_file_name = file_name + sub_type
                    if config.subtitle_add_chs:
                        sub_file_name = file_name + ".chs" + sub_type
                    sub_new_path = os.path.join(folder_old_path, sub_file_name)

                    if os.path.exists(sub_path):
                        copy_file(sub_path, sub_new_path)
                        signal.show_log_text(f" 🍀 字幕文件 '{sub_file_name}' 成功复制! ")
                        new_sub_movie_list.append(movie)
                        add_succ = True
                if add_succ:
                    add_count += 1
        elif sub_list:
            for sub_type in sub_list:
                sub_old_path = os.path.join(folder_old_path, (file_name + sub_type))
                sub_new_path = os.path.join(folder_old_path, (file_name + ".chs" + sub_type))
                if config.subtitle_add_chs:
                    if ".chs" not in sub_old_path and not os.path.exists(sub_new_path):
                        move_file(sub_old_path, sub_new_path)
                        signal.show_log_text(
                            f" 🍀 字幕文件: '{file_name + sub_type}' 已被重命名为: '{file_name + '.chs' + sub_type}' "
                        )
                else:
                    sub_old_path_no_chs = sub_old_path.replace(".chs", "")
                    if ".chs" in sub_old_path and not os.path.exists(sub_old_path_no_chs):
                        move_file(sub_old_path, sub_old_path_no_chs)
                        signal.show_log_text(
                            f" 🍀 字幕文件: '{file_name + sub_type}' 已被重命名为: '{split_path(sub_old_path_no_chs)[1]}' "
                        )

                cnword_style = config.cnword_style
                if cnword_style and cnword_style not in sub_new_path:
                    folder_cnword = config.folder_cnword
                    file_cnword = config.file_cnword
                    folder_name = config.folder_name
                    naming_file = config.naming_file
                    naming_media = config.naming_media
                    if folder_cnword or file_cnword or "cnword" in folder_name or "cnword" in naming_file or "cnword" in naming_media:
                        new_sub_movie_list.append(movie)

    signal.show_log_text(f"\nDone! \n成功添加字幕影片数量: {add_count} \n仍无字幕影片数量: {no_sub_count - add_count} ")
    signal.show_log_text("================================================================================")
    # 重新刮削新添加字幕的影片
    list2 = list(set(new_sub_movie_list))  # 去重
    list3 = [each for each in list2 if each.strip()]  # 去空
    list3.sort(key=new_sub_movie_list.index)  # 排序（保持原顺序）
    if list3 and config.subtitle_add_rescrape:
        signal.show_log_text("开始对新添加字幕的视频重新刮削...")
        start_new_scrape(FileMode.Default, movie_list=list3)
    signal.reset_buttons_status.emit()
