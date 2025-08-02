from pathlib import Path

from fastapi import HTTPException, status

from mdcx.utils.path import is_descendant


def check_path_access(path: str | Path, *allowed: str | Path) -> None:
    """检查指定路径是否在允许的目录中, 不在时返回 403 错误."""
    if not any(is_descendant(path, p) for p in allowed):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="服务器禁止访问指定的路径.")
