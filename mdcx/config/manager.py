import json
import os
import os.path
from pathlib import Path

from ..consts import MAIN_PATH, MARK_FILE
from .computed import Computed
from .models import Config
from .v1 import ConfigV1, load_v1


class ConfigManager:
    def __init__(self):
        if not MARK_FILE.is_file():  # 标记文件不存在
            self.path = MAIN_PATH / "config.json"  # 默认配置文件路径
        else:
            self._path = Path(self.read_mark_file())
            self.data_folder, self.file = self._path.parent, self._path.name
        if not os.path.exists(self._path):  # 配置文件不存在, 写入默认值
            if self._path.suffix == ".ini":
                self.path = self._path.with_suffix(".json")
            self.reset()
        self.load()

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, path: str | Path):
        p = Path(path)
        self.data_folder, self.file = p.parent, p.name
        self.write_mark_file(p)  # 更新标记文件路径
        self._path = p

    def load(self) -> list[str]:
        if self._path.suffix == ".ini":  # handle v1 config
            return self.handle_v1()
        try:
            d = json.loads(self._path.read_text(encoding="UTF-8"))
            errors = Config.update(d)
            self.config = Config.model_validate(d)
            self.computed = Computed(self.config)
            return errors
        except Exception as e:
            self.config = Config()
            self.computed = Computed(self.config)
            msg = f" 配置文件 {self._path} 验证失败. 错误信息: \n{str(e)}"
            return msg.splitlines()

    def handle_v1(self):
        v2path = self.path.with_suffix(".v2.json")
        v1path = self.path
        if os.path.exists(v2path):
            self.path = v2path
            return [f"[V1] {v1path} 是旧版配置文件, 对应的新版配置文件已存在, 改为加载新版配置: {v2path}"] + self.load()

        d, errors = load_v1(self.path)
        self.path = v2path
        errors = [
            f"[V1] {v1path} 是旧版配置文件, 将自动转换为新版配置并保存到 {v2path}",
            "[V1] 旧版配置文件不会被删除. 当保存配置时, 仅会写入新版配置文件, 后续会自动使用新版配置文件",
        ] + errors
        config_v1 = ConfigV1(**d)
        config_v1.init()
        self.config = config_v1.to_pydantic_model()
        self.computed = Computed(self.config)
        self.save()
        return errors

    def save(self):
        self._path.write_text(self.config.model_dump_json(indent=2), encoding="UTF-8")

    def reset(self):
        """写入默认配置"""
        self._path.write_text(Config().model_dump_json(indent=2), encoding="UTF-8")

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
        with open(MARK_FILE, encoding="UTF-8") as f:
            return f.read().strip()


manager = ConfigManager()


def get_new_str(a: str, wanted=False):
    return a
