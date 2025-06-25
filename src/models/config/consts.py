import platform
import sys
from os.path import abspath, dirname, expanduser, join, realpath

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
IS_NUITKA = "__compiled__" in globals()  # nuitka 编译


"""
MAIN_PATH 是唯一硬编码的路径, 其定义如下:
- 绝对路径
- 从源代码运行时, 表示 main.py 所在目录
- 运行 pyinstaller/nuitka 打包的程序时, 在 macOS 上表示 `~/.mdcx`, 在 Windows 上表示 exe 所在目录

此路径的作用是, 该目录下有一个文件 (MDCx.config),
此文件中存储一个绝对路径, 指向当前启用的配置文件,
同时, 该配置文件所在的目录即为用户数据目录.

todo 已验证符合预期:
- [x] mac - pyinstaller
- [x] mac - src
- [ ] windows - pyinstaller
- [ ] windows - src
- [ ] docker?
"""
try:  # 从源代码运行时, 为 main.py 所在目录, 根据此文件路径确定, 若移动此文件需修改
    MAIN_PATH = realpath(__file__)
    i = 4
    if "__compiled__" in globals():  # nuitka 编译
        i = 3
    for _ in range(i):
        MAIN_PATH = dirname(MAIN_PATH)
except Exception:
    MAIN_PATH = abspath(sys.path[0])

# 运行 pyinstaller/nuitka 打包的程序时, 在 macOS 上为 `~/.mdcx`, 在 Windows 上为 exe 所在目录
if IS_PYINSTALLER:  # 是否Bundle Resource，是否打包成exe运行
    if IS_MAC:
        MAIN_PATH = join(expanduser("~"), ".mdcx")
    else:
        MAIN_PATH = abspath("")  # 打包后，路径是准的

MARK_FILE = join(MAIN_PATH, "MDCx.config")


def show_constants():
    """显示所有运行时常量"""
    constants = {
        "MAIN_PATH": MAIN_PATH,
        "IS_WINDOWS": IS_WINDOWS,
        "IS_MAC": IS_MAC,
        "IS_DOCKER": IS_DOCKER,
        "IS_NFC": IS_NFC,
        "IS_PYINSTALLER": IS_PYINSTALLER,
        "IS_NUITKA": IS_NUITKA,
    }
    print("Run time constants:")
    for key, value in constants.items():
        print(f"\t{key}: {value}")


show_constants()
