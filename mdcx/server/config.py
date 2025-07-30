import os
from pathlib import Path

API_KEY_HEADER = "X-API-KEY"
API_KEY = os.getenv("MDCX_API_KEY")
assert API_KEY, "MDCX_API_KEY must be set in the environment variables."

_SAFE_DIR = os.getenv("MDCX_SAFE_DIR")
if _SAFE_DIR is None:
    print("MDCX_SAFE_DIR environment variable is not set. Using default: ~")
    _SAFE_DIR = "~"
SAFE_DIR = Path(_SAFE_DIR).expanduser().resolve()
assert SAFE_DIR.is_dir(), "MDCX_SAFE_DIR must be a valid directory path."

WS_PROTOCOL = "v1.mdcx"
