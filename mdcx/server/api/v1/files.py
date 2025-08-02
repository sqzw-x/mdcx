import os
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from mdcx.utils.path import is_descendant

from ...config import SAFE_DIRS
from .exceptions import FORBIDDEN_PATH

router = APIRouter(prefix="/files", tags=["文件管理"])


class FileItem(BaseModel):
    """Represents a file or directory item."""

    name: str = Field(..., description="The name of the file or directory.")
    path: str = Field(..., description="The absolute path of the file or directory.")
    type: Literal["file", "directory"] = Field(..., description="The type of the item. 'file' or 'directory'.")
    size: int | None = Field(default=None, description="The size of the file in bytes. Omitted for directories.")
    last_modified: datetime | None = None


class FileListResponse(BaseModel):
    """The response structure for the file list endpoint."""

    items: list[FileItem] = Field(
        ..., description="指定路径下的文件和目录列表. 先目录后文件, 均按名称排序且不区分大小写."
    )
    total: int = Field(..., description="路径下的文件和目录总数. 若大于 len(data) 说明 data 因文件过多被截断.")


@router.get("/list", operation_id="listFiles", summary="列出文件和目录")
async def list_files(
    path: Annotated[str, Query(description="服务器路径. 相对路径将基于 SAFE_DIRS 中的首个路径解析.")],
) -> FileListResponse:
    """
    列出指定路径下的文件和目录. 仅允许访问 `SAFE_DIRS` 目录下的内容, `SAFE_DIRS` 可通过服务器环境变量 `MDCX_SAFE_DIRS` 设置. 指向 `SAFE_DIRS` 外目录的软链接本身可见, 但无法访问其内容.
    """
    p = Path(path)
    try:
        if p.is_absolute():
            target_path = p.resolve(strict=True)
        else:
            target_path = (SAFE_DIRS[0] / p).resolve(strict=True)
    except OSError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="路径解析失败, 可能不存在或无访问权限")

    # Ensure the path is within the SAFE_DIRS
    if all(not is_descendant(target_path, safe_dir) for safe_dir in SAFE_DIRS):
        raise FORBIDDEN_PATH

    # 由于我们保证了 target_path 在 SAFE_DIRS 中, 而后者必然为目录, 因此 target_path 非目录时可以安全的访问 target_path.parent
    if not target_path.is_dir():
        target_path = target_path.parent

    if not target_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"指定路径 {path} 不存在.")

    try:
        items = []
        for entry in os.scandir(target_path):
            entry_path = Path(entry.path)
            item_type = "directory" if entry.is_dir() else "file"
            item = FileItem(name=entry.name, path=str(entry_path.as_posix()), type=item_type)
            # Get optional file metadata
            try:
                stat_result = entry.stat()
                mtime = datetime.fromtimestamp(stat_result.st_mtime)
                item.last_modified = mtime
                if item_type == "file":
                    item.size = stat_result.st_size
            except (OSError, FileNotFoundError):
                # Could not retrieve stats, skip these fields
                pass
            items.append(item)

        # Sort items: directories first, then files, both alphabetically
        items.sort(key=lambda x: (x.type != "directory", x.name.lower()))
        total = len(items)
        return FileListResponse(items=items[:1000], total=total)  # 限制最多返回 1k 项

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}"
        )
