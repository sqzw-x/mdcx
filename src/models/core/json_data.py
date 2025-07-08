import threading
from typing import TypedDict


class LogBuffer:
    all_buffers = {}
    global_buffer = None

    @staticmethod
    def _global_buffer() -> "LogBuffer":
        if LogBuffer.global_buffer is None:
            LogBuffer.global_buffer = LogBuffer()
        return LogBuffer.global_buffer

    @staticmethod
    def _get_buffer(category: str) -> "LogBuffer":
        pid = threading.current_thread().ident
        if pid is None:
            return LogBuffer._global_buffer()
        if pid not in LogBuffer.all_buffers:
            LogBuffer.all_buffers[pid] = {}
        if category not in LogBuffer.all_buffers[pid]:
            LogBuffer.all_buffers[pid][category] = LogBuffer()
        return LogBuffer.all_buffers[pid][category]

    @staticmethod
    def clear_thread():
        pid = threading.current_thread().ident
        if pid is not None:
            LogBuffer.all_buffers.pop(pid, None)

    @staticmethod
    def log() -> "LogBuffer":
        return LogBuffer._get_buffer("log")

    @staticmethod
    def info() -> "LogBuffer":
        return LogBuffer._get_buffer("info")

    @staticmethod
    def error() -> "LogBuffer":
        return LogBuffer._get_buffer("error")

    @staticmethod
    def req() -> "LogBuffer":
        return LogBuffer._get_buffer("req")

    def __init__(self):
        self.buffer = []

    def write(self, message):
        self.buffer.append(message)

    def get(self):
        return "".join(self.buffer)

    def last(self):
        if len(self.buffer) == 0:
            return ""
        return self.buffer[-1]

    def clear(self):
        self.buffer.clear()


class MoveContext(TypedDict):
    dont_move_movie: bool
    del_file_path: bool
    file_path: str
    cd_part: str


class ImageContext(TypedDict):
    cd_part: str

    thumb_size: tuple[int, int]
    poster_big: bool
    image_cut: str
    # poster_marked: bool
    # thumb_marked: bool
    # fanart_marked: bool
    thumb_list: list[tuple[str, str]]
    poster_path: str
    thumb_path: str
    fanart_path: str
    thumb: str
    poster: str
    trailer: str
    extrafanart: list[str]
    thumb_from: str
    poster_from: str
    trailer_from: str


class ActorData(TypedDict):
    actor: str
    actor_amazon: list[str]
    actor_href: str
    all_actor: str
    actor_photo: str
    all_actor_photo: dict
    amazon_orginaltitle_actor: str


class MovieData(TypedDict):
    definition: str
    title: str
    outline: str
    failed_folder: str
    folder_name: str
    version: int
    image_download: bool
    outline_from: str
    thumb_from: str
    extrafanart_from: str
    trailer_from: str
    short_number: str
    appoint_number: str
    appoint_url: str
    website_name: str
    fields_info: str
    number: str
    letters: str
    has_sub: bool
    c_word: str
    destroyed: str
    leak: str
    wuma: str
    youma: str
    mosaic: str
    tag: str
    _4K: str
    source: str
    release: str
    year: str
    javdbid: str
    score: str
    originaltitle: str
    studio: str
    publisher: str
    runtime: str
    director: str
    website: str
    series: str
    trailer: str
    originaltitle_amazon: str
    originalplot: str
    wanted: str
    naming_media: str
    naming_file: str
    country: str


class InternalStateData(TypedDict):
    failed_folder: str
    version: int
    image_download: bool  # 爬虫返回
    nfo_can_translate: bool  # 内部状态
    # 内部状态, 控制是否加水印
    poster_marked: bool
    thumb_marked: bool
    fanart_marked: bool


class OutputData(TypedDict):
    title: str
    outline: str
    folder_name: str
    outline_from: str
    extrafanart_from: str
    trailer_from: str
    short_number: str
    appoint_number: str
    appoint_url: str
    website_name: str
    fields_info: str
    number: str
    letters: str
    has_sub: bool
    c_word: str
    cd_part: str
    destroyed: str
    leak: str
    wuma: str
    youma: str
    mosaic: str
    tag: str
    _4K: str
    source: str
    release: str
    year: str
    javdbid: str
    score: str
    originaltitle: str
    studio: str
    publisher: str
    runtime: str
    director: str
    website: str
    series: str
    trailer: str
    originaltitle_amazon: str
    originalplot: str
    wanted: str
    naming_media: str
    naming_file: str
    country: str


class JsonData(MoveContext, ActorData, MovieData, InternalStateData, OutputData, ImageContext):
    pass


def new_json_data() -> JsonData:
    return {
        "definition": "",
        "actor": "",
        "thumb_size": (0, 0),
        "poster_big": False,
        "image_cut": "",
        "poster_marked": True,
        "thumb_marked": True,
        "fanart_marked": True,
        "thumb_list": [],
        "poster_path": "",
        "thumb_path": "",
        "fanart_path": "",
        "thumb": "",
        "poster": "",
        "extrafanart": [],
        "actor_amazon": [],
        "actor_href": "",
        "all_actor": "",
        "actor_photo": "",
        "all_actor_photo": {},
        "amazon_orginaltitle_actor": "",
        "file_path": "",
        "del_file_path": False,
        "dont_move_movie": False,
        "nfo_can_translate": False,
        "title": "",
        "outline": "",
        "failed_folder": "",
        "folder_name": "",
        "version": 0,
        "image_download": False,
        "outline_from": "",
        "thumb_from": "",
        "poster_from": "",
        "extrafanart_from": "",
        "trailer_from": "",
        "short_number": "",
        "appoint_number": "",
        "appoint_url": "",
        "website_name": "",
        "fields_info": "",
        "number": "",
        "letters": "",
        "has_sub": False,
        "c_word": "",
        "cd_part": "",
        "destroyed": "",
        "leak": "",
        "wuma": "",
        "youma": "",
        "mosaic": "",
        "tag": "",
        "_4K": "",
        "source": "",
        "release": "",
        "year": "",
        "javdbid": "",
        "score": "0.0",
        "originaltitle": "",
        "studio": "",
        "publisher": "",
        "runtime": "",
        "director": "",
        "website": "",
        "series": "",
        "trailer": "",
        "originaltitle_amazon": "",
        "originalplot": "",
        "wanted": "",
        "naming_media": "",
        "naming_file": "",
        "country": "",
    }
