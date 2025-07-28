import os
from pathlib import Path

API_KEY_NAME = "X-API-KEY"
API_KEY = os.getenv("API_KEY")
assert API_KEY, "API_KEY must be set in the environment variables."

_SAFE_DIR = os.getenv("SAFE_DIR")
if _SAFE_DIR is None:
    print("SAFE_DIR environment variable is not set. Using default: ~")
    _SAFE_DIR = "~"
SAFE_DIR = Path(_SAFE_DIR).expanduser().resolve()
assert SAFE_DIR.is_dir(), "SAFE_DIR must be a valid directory path."
