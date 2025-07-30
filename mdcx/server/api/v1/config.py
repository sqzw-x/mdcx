from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from mdcx.config.manager import ConfigSchema, config, manager
from mdcx.config.models import Config
from mdcx.utils.dataclass import update_existing
from mdcx.utils.path import is_descendant

router = APIRouter(prefix="/config")


@router.get("/", response_model=Config)
async def get_config():
    """
    Returns the current configuration.
    """
    return Config.from_legacy(asdict(config))


@router.put("/")
async def update_config(new_config: Config):
    """
    Updates the current configuration with the provided values.
    """
    # config 被用作全局变量, 必须就地更新
    # 由于 ConfigSchema 没有嵌套字段, 因此可以直接更新 __dict__
    update_existing(config.__dict__, new_config.to_legacy())
    config.init()
    manager.save()
    return Config.from_legacy(asdict(config))


@router.delete("/")
async def delete_config(name: Annotated[str, Query(description="Configuration file name to delete without extension")]):
    """
    Deletes the specified configuration file.
    """
    if f"{name}.ini" == manager.file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete the currently active configuration file."
        )
    p = Path(manager.data_folder) / f"{name}.ini"
    if not is_descendant(p, manager.data_folder):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to the specified path is forbidden.")
    p.unlink(True)


@router.post("/reset")
async def reset_config():
    """
    Reset current configuration to default values.
    """
    manager.reset()
    manager.load()
    return Config.from_legacy(asdict(config))


@router.post("/create")
async def create_config(name: Annotated[str, Query(description="Configuration file name without extension")]):
    """
    Creates a new configuration file with the specified name.
    """
    p = Path(manager.data_folder) / f"{name}.ini"
    if not is_descendant(p, manager.data_folder):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to the specified path is forbidden.")
    if p.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Configuration file {name}.ini already exists."
        )
    p.write_text(ConfigSchema().format_ini(), encoding="UTF-8")


class ConfigSwitchResponse(BaseModel):
    config: Config
    errors: list[str] = Field(description="List of errors encountered when loading new configuration.")


@router.post("/switch", response_model=ConfigSwitchResponse)
async def switch_config(
    name: Annotated[str, Query(description="Configuration file name to switch to without extension")],
):
    """
    Switches to an exist configuration.
    """
    new_path = Path(manager.data_folder) / f"{name}.ini"
    if not is_descendant(new_path, manager.data_folder):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to the specified path is forbidden.")
    if not new_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Configuration file {name}.ini not found.")
    new_path = str(new_path.resolve())
    manager.path = new_path
    errors = manager.load()
    return ConfigSwitchResponse(config=Config.from_legacy(asdict(config)), errors=errors)


@router.get("/schema", response_model=dict)
async def get_config_schema():
    """
    Returns the JSON schema for the configuration.
    """
    return Config.model_json_schema()


@router.get("/default", response_model=Config)
async def get_default_config():
    """
    Returns the default configuration.
    """
    return Config.from_legacy(asdict(ConfigSchema()))
