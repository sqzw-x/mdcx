import os
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...config import SAFE_DIR

router = APIRouter(prefix="/files")


class FileItem(BaseModel):
    """Represents a file or directory item."""

    name: str = Field(..., description="The name of the file or directory.")
    path: str = Field(..., description="The full absolute path of the item.")
    type: Literal["file", "directory"] = Field(..., description="The type of the item.")
    size: int | None = Field(None, description="The size of the file in bytes. Omitted for directories.")
    last_modified: str | None = Field(None, description="The last modification date and time in ISO 8601 format.")


class FileListResponse(BaseModel):
    """The response structure for the file list endpoint."""

    data: list[FileItem]


@router.get("/list", response_model=FileListResponse)
async def list_files(path: Annotated[str, Query(description="The absolute path of the directory to browse.")]):
    """
    Retrieves the list of items (files and directories) within a specified directory.
    """
    p = Path(path)
    try:
        if p.is_absolute():
            target_path = p.resolve(strict=True)
        else:
            target_path = (Path.cwd() / p).resolve(strict=True)
    except OSError:
        raise HTTPException(status_code=400, detail="Resolve path failed. Invalid path provided.")

    # Ensure the path is within the SAFE_DIR
    if not target_path.as_posix().startswith(SAFE_DIR.as_posix()):
        raise HTTPException(
            status_code=403,
            detail="Access to the specified path is forbidden.",
        )

    if not target_path.is_dir():
        target_path = target_path.parent

    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    try:
        items = []
        for entry in os.scandir(target_path):
            entry_path = Path(entry.path)
            item_type = "directory" if entry.is_dir() else "file"
            item = FileItem(name=entry.name, path=str(entry_path), type=item_type, size=None, last_modified=None)
            # Get optional file metadata
            try:
                stat_result = entry.stat()
                mtime = datetime.fromtimestamp(stat_result.st_mtime)
                item.last_modified = mtime.isoformat()
                if item_type == "file":
                    item.size = stat_result.st_size
            except (OSError, FileNotFoundError):
                # Could not retrieve stats, skip these fields
                pass
            items.append(item)

        # Sort items: directories first, then files, both alphabetically
        items.sort(key=lambda x: (x.type != "directory", x.name.lower()))
        return {"data": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
