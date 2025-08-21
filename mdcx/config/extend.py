import re
from pathlib import Path

from mdcx.config.enums import Website
from mdcx.config.manager import manager
from mdcx.config.models import CleanAction
from mdcx.manual import ManualConfig
from mdcx.utils import convert_path, nfd2c, split_path
from mdcx.utils.path import get_path


def get_movie_path_setting(file_path="") -> tuple[str, str, str, list[str], str, str]:
    # 先把'\'转成'/'以便判断是路径还是目录
    movie_path = manager.config.media_path.replace("\\", "/")  # 用户设置的扫描媒体路径
    if movie_path == "":  # 未设置为空时，使用用户数据目录
        movie_path = manager.data_folder
    movie_path = nfd2c(movie_path)
    end_folder_name = split_path(movie_path)[1]
    # 用户设置的软链接输出目录
    softlink_path = manager.config.softlink_path.replace("\\", "/").replace("end_folder_name", end_folder_name)
    # 用户设置的成功输出目录
    success_folder = manager.config.success_output_folder.replace("\\", "/").replace("end_folder_name", end_folder_name)
    # 用户设置的失败输出目录
    failed_folder = manager.config.failed_output_folder.replace("\\", "/").replace("end_folder_name", end_folder_name)
    # 用户设置的排除目录
    escape_folder_list = [
        f.replace("\\", "/").replace("end_folder_name", end_folder_name) for f in manager.config.folders
    ]
    # 用户设置的剧照副本目录
    extrafanart_folder = manager.config.extrafanart_folder.replace("\\", "/")

    # 获取路径
    softlink_path = convert_path(get_path(movie_path, softlink_path))
    success_folder = convert_path(get_path(movie_path, success_folder))
    failed_folder = convert_path(get_path(movie_path, failed_folder))
    softlink_path = nfd2c(softlink_path)
    success_folder = nfd2c(success_folder)
    failed_folder = nfd2c(failed_folder)
    extrafanart_folder = nfd2c(extrafanart_folder)

    # 获取排除目录完整路径（尾巴添加/）
    escape_folder_new_list = []
    for es in escape_folder_list:  # 排除目录可以多个，以，,分割
        es = es.strip(" ")
        if es:
            es = get_path(movie_path, es).replace("\\", "/")
            if es[-1] != "/":  # 路径尾部添加“/”，方便后面move_list查找时匹配路径
                es += "/"
            es = nfd2c(es)
            escape_folder_new_list.append(es)

    if file_path:
        temp_path = movie_path
        if manager.config.scrape_softlink_path:
            temp_path = softlink_path
        if "first_folder_name" in success_folder or "first_folder_name" in failed_folder:
            first_folder_name = re.findall(r"^/?([^/]+)/", file_path[len(temp_path) :].replace("\\", "/"))
            first_folder_name = first_folder_name[0] if first_folder_name else ""
            success_folder = success_folder.replace("first_folder_name", first_folder_name)
            failed_folder = failed_folder.replace("first_folder_name", first_folder_name)

    return (
        convert_path(movie_path),
        success_folder,
        failed_folder,
        escape_folder_new_list,
        extrafanart_folder,
        softlink_path,
    )


def need_clean(file_path: Path, file_name: str, file_ext: str) -> bool:
    # 判断文件是否需清理
    if not manager.computed.can_clean:
        return False

    # 不清理的扩展名
    if CleanAction.CLEAN_IGNORE_EXT in manager.config.clean_enable and file_ext in manager.config.clean_ignore_ext:
        return False

    # 不清理的文件名包含
    if CleanAction.CLEAN_IGNORE_CONTAINS in manager.config.clean_enable:
        for each in manager.config.clean_ignore_contains:
            if each in file_name:
                return False

    # 清理的扩展名
    if CleanAction.CLEAN_EXT in manager.config.clean_enable and file_ext in manager.config.clean_ext:
        return True

    # 清理的文件名等于
    if CleanAction.CLEAN_NAME in manager.config.clean_enable and file_name in manager.config.clean_name:
        return True

    # 清理的文件名包含
    if CleanAction.CLEAN_CONTAINS in manager.config.clean_enable:
        for each in manager.config.clean_contains:
            if each in file_name:
                return True

    # 清理的文件大小<=(KB)
    if CleanAction.CLEAN_SIZE in manager.config.clean_enable:
        try:  # 路径太长时，此处会报错 FileNotFoundError: [WinError 3] 系统找不到指定的路径。
            return file_path.stat().st_size <= manager.config.clean_size * 1024
        except Exception:
            pass
    return False


def deal_url(url: str) -> tuple[str | None, str]:
    if "://" not in url:
        url = "https://" + url
    url = url.strip()
    for key, site in ManualConfig.WEB_DIC.items():
        if key.lower() in url.lower():
            return site.value, url

    # 自定义的网址
    for site in Website:
        if (r := manager.config.site_configs.get(site)) and r.custom_url:
            if str(r.custom_url) in url:
                return site.value, url

    return None, url
