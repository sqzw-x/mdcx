from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from mdcx.config.manager import config, manager
from mdcx.config.models import Config
from mdcx.config.v1 import ConfigSchema
from mdcx.utils.dataclass import update_existing

from .utils import check_path_access

router = APIRouter(prefix="/config", tags=["配置管理"])


@router.get("/", response_model=Config, operation_id="getCurrentConfig", summary="获取当前配置")
async def get_config():
    manager.load()
    return Config.from_legacy(asdict(config))


@router.put("/", operation_id="updateConfig", summary="更新配置")
async def update_config(new_config: Config):
    # config 被用作全局变量, 必须就地更新
    # 由于 ConfigSchema 没有嵌套字段, 因此可以直接更新 __dict__
    update_existing(config.__dict__, new_config.to_legacy())
    config.init()
    manager.save()
    return Config.from_legacy(asdict(config))


@router.delete("/", operation_id="deleteConfig", summary="删除配置文件")
async def delete_config(name: Annotated[str, Query(description="待删除的配置文件名 (不含扩展名)")]):
    if f"{name}.ini" == manager.file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法删除当前激活的配置文件.")
    p = Path(manager.data_folder) / f"{name}.ini"
    check_path_access(p, manager.data_folder)
    p.unlink(True)


@router.post("/reset", operation_id="resetConfig", summary="重置配置")
async def reset_config():
    """将当前配置重置为默认值"""
    manager.reset()
    manager.load()
    return Config.from_legacy(asdict(config))


@router.post("/create", operation_id="createConfig", summary="创建配置文件")
async def create_config(name: Annotated[str, Query(description="配置文件名 (不含扩展名)")]):
    """创建指定名称的配置文件"""
    p = Path(manager.data_folder) / f"{name}.ini"
    check_path_access(p, manager.data_folder)
    if p.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"名称为 {name} 的配置文件已存在.")
    p.write_text(ConfigSchema().format_ini(), encoding="UTF-8")


class ConfigSwitchResponse(BaseModel):
    config: Config
    errors: list[str] = Field(description="加载配置时发生的错误信息列表")


@router.post("/switch", operation_id="switchConfig", summary="切换配置")
async def switch_config(
    name: Annotated[str, Query(description="待切换的配置文件名 (不含扩展名)")],
) -> ConfigSwitchResponse:
    """
    切换到现有的配置文件。
    """
    new_path = Path(manager.data_folder) / f"{name}.ini"
    check_path_access(new_path, manager.data_folder)
    if not new_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"配置文件 {name}.ini 不存在.")
    new_path = str(new_path.resolve())
    manager.path = new_path
    errors = manager.load()
    return ConfigSwitchResponse(config=Config.from_legacy(asdict(config)), errors=errors)


@router.get("/schema", response_model=dict, operation_id="getConfigSchema", summary="获取配置架构")
async def get_config_schema():
    """返回配置的JSON架构。"""
    return Config.json_schema()


@router.get("/ui_schema", response_model=dict, operation_id="getConfigUISchema", summary="获取UI架构")
async def get_ui_schema():
    """返回配置的UI架构。"""
    return Config.ui_schema()


@router.get("/default", operation_id="getDefaultConfig", summary="获取默认配置")
async def get_default_config() -> Config:
    """
    返回默认配置。
    """
    return Config.from_legacy(asdict(ConfigSchema()))
