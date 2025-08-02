from fastapi import HTTPException, status

FORBIDDEN_PATH = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="服务器禁止访问指定的路径.")
