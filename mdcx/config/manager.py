import os
import os.path
import re
from pathlib import Path
from warnings import deprecated

from mdcx.consts import MAIN_PATH, MARK_FILE
from mdcx.manual import ManualConfig

from .models import Config
from .v1 import ConfigSchema, load_v1


class ConfigManager:
    def __init__(self):
        self._get_config_path()
        self.config = Config()
        self._config_v1 = ConfigSchema(**self.config.to_legacy())
        self._config_v1.init()

    @property
    def path(self) -> str:
        return str(self._path)

    @path.setter
    def path(self, path: str | Path):
        p = Path(path)
        self.data_folder, self.file = os.path.split(p)
        self.write_mark_file(p)  # 更新标记文件路径
        self._path = p

    @property
    @deprecated("v1 config is deprecated, use config instead")
    def config_v1(self) -> ConfigSchema:
        return self._config_v1

    def load(self) -> list[str]:
        if self.file.endswith(".ini"):  # handle v1 config
            return self.handle_v1()
        try:
            self.config = Config.model_validate_json(self._path.read_text(encoding="UTF-8"))
            self._config_v1 = ConfigSchema(**self.config.to_legacy())
            return []
        except Exception as e:
            return str(e).splitlines()

    def handle_v1(self):
        v2path = self.path.removesuffix(".ini") + ".v2.json"
        v1path = self.path
        if os.path.exists(v2path):
            self.path = v2path
            return [f"{v1path} 是旧版配置文件, 对应的新版配置文件已存在, 改为加载新版配置: {v2path}"] + self.load()

        d, errors = load_v1(self.path)
        self.path = v2path
        errors = [
            f"{self.path} 是旧版配置文件, 将自动转换为新版配置并保存到 {v2path}",
            "旧版配置文件不会被删除. 当保存配置时, 仅会写入新版配置文件, 后续会自动使用新版配置文件",
        ] + errors
        self._config_v1 = ConfigSchema(**d)
        self._config_v1.init()
        self.config = self._config_v1.to_pydantic_model()
        self.save()
        return errors

    def save(self):
        self._path.write_text(self.config.model_dump_json(indent=2), encoding="UTF-8")

    def reset(self):
        """写入默认配置"""
        self._path.write_text(Config().model_dump_json(indent=2), encoding="UTF-8")

    def _get_config_path(self):
        if not os.path.exists(MARK_FILE):  # 标记文件不存在
            self.path = os.path.join(MAIN_PATH, "config.json")  # 默认配置文件路径
        else:
            self._path = Path(self.read_mark_file())
            self.data_folder, self.file = os.path.split(self._path)
        if not os.path.exists(self._path):  # 配置文件不存在, 写入默认值
            self.reset()

    def list_configs(self) -> list[str]:
        """列出配置文件夹中的所有配置文件名."""
        if not self._path.parent.exists():
            return []
        return [f.name for f in self._path.parent.iterdir() if f.suffix in (".json", ".ini")]

    @staticmethod
    def write_mark_file(path: str | Path):
        """写入 MARK_FILE"""
        if not os.path.exists(MARK_FILE):  # 标记文件不存在
            # 确保 MARK_FILE 所在目录存在
            mark_dir = os.path.dirname(MARK_FILE)
            if mark_dir:
                os.makedirs(mark_dir, exist_ok=True)
        with open(MARK_FILE, "w", encoding="UTF-8") as f:
            f.write(str(path))

    @staticmethod
    def read_mark_file() -> str:
        """读取 MARK_FILE"""
        if not os.path.exists(MARK_FILE):
            raise FileNotFoundError(f"标记文件 {MARK_FILE} 不存在, 请先运行配置初始化.")
        with open(MARK_FILE, encoding="UTF-8") as f:
            return f.read().strip()


manager = ConfigManager()


def get_new_str(a: str, wanted=False):
    all_website_list = ManualConfig.SUPPORTED_WEBSITES
    if wanted:
        all_website_list = ["javlibrary", "javdb"]
    read_web_list = re.split(r"[,，]", a)
    new_website_list1 = [i for i in read_web_list if i in all_website_list]  # 去除错误网站
    new_website_list = []
    # 此处配置包含优先级, 因此必须按顺序去重
    [new_website_list.append(i) for i in new_website_list1 if i not in new_website_list]  # 去重
    new_str = ",".join(new_website_list)
    return new_str
