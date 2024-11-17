import os
import shutil

from models.base.file import copy_file, move_file, split_path
from models.config.config import config
from models.core.file import movie_lists
from models.core.utils import get_movie_path_setting
from models.signals import signal


def add_del_extras(mode):
    """
    添加/删除剧照
    """
    signal.show_log_text(f'Start {mode} extrafanart extras! \n')

    movie_path, success_folder, failed_folder, escape_folder_list, extrafanart_folder, softlink_path = get_movie_path_setting()
    signal.show_log_text(f' 🖥 Movie path: {movie_path} \n 🔎 Checking all videos, Please wait...')
    movie_type = config.media_type
    movie_list = movie_lists('', movie_type, movie_path)  # 获取所有需要刮削的影片列表

    extrafanart_folder_path_list = []
    for movie in movie_list:
        movie_file_folder_path = split_path(movie)[0]
        extrafanart_folder_path = os.path.join(movie_file_folder_path, 'extrafanart')
        if os.path.exists(extrafanart_folder_path):
            extrafanart_folder_path_list.append(movie_file_folder_path)
    extrafanart_folder_path_list = list(set(extrafanart_folder_path_list))
    extrafanart_folder_path_list.sort()
    total_count = len(extrafanart_folder_path_list)
    new_count = 0
    count = 0
    for each in extrafanart_folder_path_list:
        extrafanart_folder_path = os.path.join(each, 'extrafanart')
        extrafanart_copy_folder_path = os.path.join(each, 'behind the scenes')
        count += 1
        if mode == 'add':
            if not os.path.exists(extrafanart_copy_folder_path):
                shutil.copytree(extrafanart_folder_path, extrafanart_copy_folder_path)
                filelist = os.listdir(extrafanart_copy_folder_path)
                for file in filelist:
                    file_new_name = file.replace('jpg', 'mp4')
                    file_path = os.path.join(extrafanart_copy_folder_path, file)
                    file_new_path = os.path.join(extrafanart_copy_folder_path, file_new_name)
                    move_file(file_path, file_new_path)
                signal.show_log_text(f" {count} new extras: \n  {extrafanart_copy_folder_path}")
                new_count += 1
            else:
                signal.show_log_text(f" {count} old extras: \n  {extrafanart_copy_folder_path}")
        else:
            if os.path.exists(extrafanart_copy_folder_path):
                shutil.rmtree(extrafanart_copy_folder_path, ignore_errors=True)
                signal.show_log_text(f" {count} del extras: \n  {extrafanart_copy_folder_path}")
                new_count += 1

    signal.show_log_text(f'\nDone! \n Total: {total_count}  {mode} copy: {new_count} ')
    signal.show_log_text("================================================================================")


def add_del_theme_videos(mode):
    signal.show_log_text(f'Start {mode} theme videos! \n')

    movie_path, success_folder, failed_folder, escape_folder_list, extrafanart_folder, softlink_path = get_movie_path_setting()
    signal.show_log_text(f' 🖥 Movie path: {movie_path} \n 🔎 Checking all videos, Please wait...')
    movie_type = config.media_type
    movie_list = movie_lists('', movie_type, movie_path)  # 获取所有需要刮削的影片列表

    theme_videos_folder_path_dic = {}
    for movie in movie_list:
        movie_file_folder_path = split_path(movie)[0]
        movie_file_path_no_ext = os.path.splitext(movie)[0]
        trailer_file_path_with_filename = movie_file_path_no_ext + '-trailer.mp4'
        trailer_file_path_no_filename = os.path.join(movie_file_folder_path, 'trailers/trailer.mp4')
        if os.path.exists(trailer_file_path_with_filename):
            theme_videos_folder_path_dic[movie_file_folder_path] = trailer_file_path_with_filename
        elif os.path.exists(trailer_file_path_no_filename):
            theme_videos_folder_path_dic[movie_file_folder_path] = trailer_file_path_no_filename
    theme_videos_folder_path_list = sorted(theme_videos_folder_path_dic.keys())
    total_count = len(theme_videos_folder_path_list)
    new_count = 0
    count = 0
    for movie_file_folder_path in theme_videos_folder_path_list:
        trailer_file_path = theme_videos_folder_path_dic.get(movie_file_folder_path)
        theme_videos_folder_path = os.path.join(movie_file_folder_path, 'backdrops')
        theme_videos_file_path = os.path.join(movie_file_folder_path, 'backdrops/theme_video.mp4')
        count += 1
        if mode == 'add':
            if not os.path.exists(theme_videos_file_path):
                if not os.path.exists(theme_videos_folder_path):
                    os.mkdir(theme_videos_folder_path)
                copy_file(trailer_file_path, theme_videos_file_path)
                signal.show_log_text(" %s new theme video: \n  %s" % (count, theme_videos_file_path))
                new_count += 1
            else:
                signal.show_log_text(" %s old theme video: \n  %s" % (count, theme_videos_file_path))
        else:
            if os.path.exists(theme_videos_folder_path):
                shutil.rmtree(theme_videos_folder_path, ignore_errors=True)
                signal.show_log_text(" %s del theme video: \n  %s" % (count, theme_videos_folder_path))
                new_count += 1

    signal.show_log_text(f'\nDone! \n Total: {total_count}  {mode} copy: {new_count} ')
    signal.show_log_text("================================================================================")
