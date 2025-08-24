from asyncio import create_task
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from mdcx.base.file import newtdisk_creat_symlink
from mdcx.config.extend import deal_url
from mdcx.config.manager import manager
from mdcx.config.models import SiteConfig, Website
from mdcx.core.scraper import start_new_scrape
from mdcx.models.enums import FileMode
from mdcx.models.flags import Flags
from mdcx.server.config import SAFE_DIRS
from mdcx.tools.emby_actor_image import update_emby_actor_photo
from mdcx.tools.emby_actor_info import show_emby_actor_list, update_emby_actor_info
from mdcx.tools.subtitle import add_sub_for_all_video

from .config import check_path_access

router = APIRouter(prefix="/legacy", tags=["Legacy"])


@router.post("/scrape", summary="开始刮削", operation_id="startScrape")
async def start_scrape():
    """使用当前配置运行刮削流程, 无需额外参数"""
    try:
        errors = manager.load()
        if errors:
            raise HTTPException(status_code=500, detail=f"Configuration errors: {', '.join(errors)}")
        start_new_scrape(FileMode.Default)
        return {"message": "Scraping started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ScrapeFileBody(BaseModel):
    path: str
    url: str


@router.post("/scrape/single", summary="单文件刮削", operation_id="scrapeSingleFile")
async def scrape_single(body: ScrapeFileBody):
    p = Path(body.path)
    check_path_access(p, *SAFE_DIRS)
    Flags.single_file_path = p
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


@router.post("/symlink", summary="创建软链接", operation_id="createSymlink")
async def create_symlink(body: CreateSoftlinksBody):
    check_path_access(body.source_dir, *SAFE_DIRS)
    check_path_access(body.dest_dir, *SAFE_DIRS)
    try:
        create_task(newtdisk_creat_symlink(body.copy_files, Path(body.source_dir), Path(body.dest_dir)))
        return {"message": "Softlink creation completed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subtitles", summary="检查并添加字幕", operation_id="addSubtitles")
async def add_subtitles():
    """检查媒体库字幕情况并自动添加 (依据本地字幕包)"""
    try:
        create_task(add_sub_for_all_video())
        return {"message": "Subtitle check and add task completed. Check logs for results."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actors", summary="查看媒体服务器演员名单", operation_id="getActors")
async def get_actors():
    """查看 emby/jellyfin 中符合条件的演员名单"""
    try:
        await show_emby_actor_list(0)
        return {"message": "Task to show actors completed. Check logs for results."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actors/complete", summary="补全演员信息", operation_id="completeActors")
async def complete_actors():
    """补全 emby/jellyfin 演员信息/头像"""
    try:
        create_task(update_emby_actor_info())
        create_task(update_emby_actor_photo())
        return {"message": "Actor info completion task completed. Check logs for results."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cookies", summary="Cookie 有效性检查", operation_id="checkCookies")
async def check_cookies():
    # This is a placeholder as the original logic is tied to UI.
    return {"message": "Not Implemented yet, original logic is tied to UI."}


class SetSiteUrlBody(BaseModel):
    site: Website
    url: HttpUrl


@router.post("/sites", summary="设置网站自定义网址", operation_id="setSiteUrl")
async def set_site_url(body: SetSiteUrlBody):
    """指定网站自定义网址设置"""
    try:
        manager.config.site_configs.setdefault(body.site, SiteConfig()).custom_url = body.url
        manager.save()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sites", summary="获取网站自定义网址", operation_id="getSiteUrls")
async def get_site_urls() -> dict[Website, HttpUrl]:
    """获取网站自定义网址设置."""
    try:
        return {s: c.custom_url for s, c in manager.config.site_configs.items() if c.custom_url is not None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
