from functools import cached_property
from pathlib import Path

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MDCX_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    host: str = Field(default="localhost")
    port: int = Field(default=8000)

    api_key_: str | None = Field(default=None, init_var=True)
    api_key: str = ""
    safe_dirs: str | None = Field(default=None, description="逗号分隔的路径列表, 指定哪些目录可以被访问.")

    dev: bool = Field(default=False)

    @field_validator("dev", mode="before")
    @classmethod
    def validate_dev(cls, v):
        """将环境变量转换为布尔值"""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v) if v is not None else False

    @model_validator(mode="after")
    def validate_config(self):
        """验证整体配置"""
        # 开发模式下设置默认值
        if self.dev:
            if self.host not in ("localhost", "127.0.0.1") and not self.host.startswith("192.168"):
                raise ValueError(
                    f"不允许在开发模式下监听非本地地址 {self.host}:{self.port}"
                    # todo 考虑任何情况下都不允许监听非本地地址, 必须使用 reverse proxy
                )
            if not self.api_key_:
                self.api_key_ = "test"
            if not self.safe_dirs:
                self.safe_dirs = "~"

        # 验证必需配置
        if not self.api_key_:
            raise ValueError("必须设置环境变量 MDCX_API_KEY")
        if not self.safe_dirs:
            raise ValueError("必须设置环境变量 MDCX_SAFE_DIRS")
        self.api_key = self.api_key_
        return self

    @cached_property
    def safe_dirs_list(self) -> list[Path]:
        """获取解析后的安全目录列表"""
        if not self.safe_dirs:
            raise ValueError("必须设置环境变量 MDCX_SAFE_DIRS")
        dirs = [Path(p).expanduser().resolve() for p in self.safe_dirs.split(",")]
        if len(dirs) == 0:
            raise ValueError("环境变量 MDCX_SAFE_DIRS 必须包含至少一个路径")
        invalid_dirs = [str(p) for p in dirs if not p.is_dir()]
        if invalid_dirs:
            raise ValueError(f"以下路径不是有效的目录: {', '.join(invalid_dirs)}")
        return dirs


try:
    settings = Config()
    HOST = settings.host
    PORT = settings.port
    IS_DEV = settings.dev
    API_KEY_HEADER = "X-API-KEY"
    API_KEY = settings.api_key
    SAFE_DIRS = settings.safe_dirs_list
    WS_PROTOCOL = "v1.mdcx"
except ValidationError as e:
    print(f"服务器配置验证失败: {e}")
    exit(1)
