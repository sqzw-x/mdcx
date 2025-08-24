from dataclasses import dataclass
from pathlib import Path

from mdcx.config.enums import Website
from mdcx.config.manager import manager
from mdcx.config.models import CleanAction
from mdcx.manual import ManualConfig


@dataclass
class MoviePathSetting:
    """路径设置"""

    movie_path: Path  # 电影路径
    success_folder: Path  # 成功目录
    failed_folder: Path  # 失败目录
    ignore_dirs: list[Path]  # 排除目录列表
    extrafanart_folder: Path  # 剧照副本目录
    softlink_path: Path  # 软链接路径


def get_movie_path_setting(file_path: Path | None = None) -> MoviePathSetting:
    # 先把'\'转成'/'以便判断是路径还是目录
    movie_path = manager.config.media_path  # 用户设置的扫描媒体路径
    if movie_path == "":  # 未设置为空时，使用用户数据目录
        movie_path = manager.data_folder
    movie_path = Path(movie_path)
    end_folder_name = movie_path.name
    # 用户设置的软链接输出目录
    softlink_path = Path(manager.config.softlink_path.replace("end_folder_name", end_folder_name))
    # 用户设置的成功输出目录
    success_folder = Path(manager.config.success_output_folder.replace("end_folder_name", end_folder_name))
    # 用户设置的失败输出目录
    failed_folder = Path(manager.config.failed_output_folder.replace("end_folder_name", end_folder_name))
    # 用户设置的排除目录, 转换相对路径
    ignore_dirs = []
    for f in manager.config.folders:
        p = Path(f.replace("end_folder_name", end_folder_name))
        if not p.is_absolute():
            p = movie_path / p
        ignore_dirs.append(p)
    # 用户设置的剧照副本目录
    extrafanart_folder = Path(manager.config.extrafanart_folder)

    # 转换相对路径
    if not softlink_path.is_absolute():
        softlink_path = movie_path / softlink_path
    if not success_folder.is_absolute():
        success_folder = movie_path / success_folder
    if not failed_folder.is_absolute():
        failed_folder = movie_path / failed_folder

    if file_path:
        file_path = Path(file_path)
        temp_path = movie_path
        if manager.config.scrape_softlink_path:
            temp_path = softlink_path
        if "first_folder_name" in success_folder.as_posix() or "first_folder_name" in failed_folder.as_posix():
            first_folder_name = file_path.relative_to(temp_path).parts
            first_folder_name = first_folder_name[0] if first_folder_name else ""
            success_folder = Path(success_folder.as_posix().replace("first_folder_name", first_folder_name))
            failed_folder = Path(failed_folder.as_posix().replace("first_folder_name", first_folder_name))

    return MoviePathSetting(
        movie_path=movie_path,
        success_folder=success_folder,
        failed_folder=failed_folder,
        ignore_dirs=ignore_dirs,
        extrafanart_folder=extrafanart_folder,
        softlink_path=softlink_path,
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
