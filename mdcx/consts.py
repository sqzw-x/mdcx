import platform
import sys
from pathlib import Path

LOCAL_VERSION = 220250826

os_name = platform.system()
mac_ver = platform.mac_ver()[0]
IS_WINDOWS = os_name == "Windows"
IS_MAC = os_name == "Darwin"
IS_DOCKER = os_name == "Linux" or os_name == "Java"

IS_NFC = True  # unicode NFC normalization
if IS_MAC and mac_ver:
    # 旧版本 mac 使用 NFD
    ver_list = mac_ver.split(".")
    if float(ver_list[0] + "." + ver_list[1]) < 10.12:
        IS_NFC = False

IS_PYINSTALLER = hasattr(sys, "frozen")


"""
MAIN_PATH 是唯一硬编码的路径, 其定义如下:
- 绝对路径
- 从源代码运行时, 表示 main.py 所在目录
- 运行 pyinstaller 打包的程序时
    - 在 macOS 上表示 `~/.mdcx`
    - 在 Windows 上表示工作目录, 当直接双击运行 exe 时即为 exe 所在目录

此路径的作用是, 该目录下有一个文件 (MDCx.config),
此文件中存储一个绝对路径, 指向当前启用的配置文件,
同时, 该配置文件所在的目录即为用户数据目录.
"""
try:  # 从源代码运行时, 为 main.py 所在目录, 根据此文件路径确定, 若移动此文件需修改 i
    MAIN_PATH = Path(__file__).resolve()
    i = 2
    for _ in range(i):
        MAIN_PATH = MAIN_PATH.parent
except Exception:
    MAIN_PATH = Path(sys.path[0]).resolve()

if IS_PYINSTALLER:
    if IS_MAC:
        MAIN_PATH = Path("~").expanduser() / ".mdcx"
    else:
        MAIN_PATH = Path("").resolve()

MARK_FILE = MAIN_PATH / "MDCx.config"
