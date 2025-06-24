import platform

os_name = platform.system()
mac_ver = platform.mac_ver()[0]
IS_WINDOWS = os_name == "Windows"
IS_MAC = os_name == "Darwin" and mac_ver
IS_DOCKER = os_name == "Linux" or os_name == "Java"

IS_NFC = True  # unicode NFC normalization
if IS_MAC:
    ver_list = mac_ver.split(".")
    if float(ver_list[0] + "." + ver_list[1]) < 10.12:
        IS_NFC = False
