from asyncio import create_task

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mdcx.config.extend import deal_url
from mdcx.config.manager import config, manager
from mdcx.config.models import Website
from mdcx.models.base.file import newtdisk_creat_symlink
from mdcx.models.core.scraper import start_new_scrape
from mdcx.models.enums import FileMode
from mdcx.models.flags import Flags
from mdcx.models.tools.emby_actor_image import update_emby_actor_photo
from mdcx.models.tools.emby_actor_info import show_emby_actor_list, update_emby_actor_info
from mdcx.models.tools.subtitle import add_sub_for_all_video
from mdcx.server.config import SAFE_DIRS

from .config import check_path_access

router = APIRouter(prefix="/legacy", tags=["Legacy"])


@router.post("/scrape", summary="开始刮削")
async def scrape():
    """使用当前配置运行刮削流程, 无需额外参数"""
    try:
        manager.load()
        start_new_scrape(FileMode.Default)
        return {"message": "Scraping started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ScrapeFileBody(BaseModel):
    path: str
    url: str


@router.post("/scrape_single", summary="单文件刮削")
async def scrape_single_file(body: ScrapeFileBody):
    Flags.single_file_path = body.path
    website, url = deal_url(body.url)
    if not website:
        raise HTTPException(status_code=400, detail="Unsupported URL")
    Flags.appoint_url = body.url
    Flags.website_name = website
    try:
        start_new_scrape(FileMode.Single)
        return {"message": "Single file scraping started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateSoftlinksBody(BaseModel):
    source_dir: str = Field(description="待软链接的源目录")
    dest_dir: str = Field(description="创建软链接的目标目录")
    copy_files: bool = Field(default=False, description="是否复制 nfo, 图片, 字幕等文件")


@router.post("/symlink", summary="创建软链接")
async def creat_symlink(body: CreateSoftlinksBody):
    check_path_access(body.source_dir, *SAFE_DIRS)
    check_path_access(body.dest_dir, *SAFE_DIRS)
    try:
        create_task(newtdisk_creat_symlink(body.copy_files, body.source_dir, body.dest_dir))
        return {"message": "Softlink creation completed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subtitles/check_and_add", summary="检查并添加字幕")
async def check_and_add_subtitles():
    """检查媒体库字幕情况并自动添加 (依据本地字幕包)"""
    try:
        create_task(add_sub_for_all_video())
        return {"message": "Subtitle check and add task completed. Check logs for results."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/media_server/actors", summary="查看媒体服务器演员名单")
async def get_media_server_actors():
    """查看 emby/jellyfin 中符合条件的演员名单"""
    try:
        await show_emby_actor_list(0)
        return {"message": "Task to show actors completed. Check logs for results."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/media_server/actors/complete_info", summary="补全演员信息")
async def complete_actor_info():
    """补全 emby/jellyfin 演员信息/头像"""
    try:
        create_task(update_emby_actor_info())
        create_task(update_emby_actor_photo())
        return {"message": "Actor info completion task completed. Check logs for results."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cookies/check", summary="Cookie 有效性检查")
async def check_cookies():
    # This is a placeholder as the original logic is tied to UI.
    return {"message": "Not Implemented yet, original logic is tied to UI."}


class SetSiteUrlBody(BaseModel):
    site: Website
    url: str


@router.post("/sites/set_url", summary="设置网站自定义网址")
async def set_site_url(body: SetSiteUrlBody):
    """指定网站自定义网址设置"""
    try:
        setattr(config, f"{body.site}_website", body.url)
        manager.save()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
