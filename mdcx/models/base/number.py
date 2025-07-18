import os
import re
import unicodedata

from mdcx.config.manager import config
from mdcx.config.manual import ManualConfig


def is_uncensored(number: str) -> bool:
    if re.match(r"n\d{4}", number) or re.search(r"[^.]+\.\d{2}\.\d{2}\.\d{2}", number):
        return True

    # 无码车牌BT,CT,EMP,CCDV,CWP,CWPBD,DSAM,DRC,DRG,GACHI,heydouga,JAV,LAF,LAFBD,HEYZO,KTG,KP,KG,LLDV,MCDV,MKD,MKBD,MMDV,NIP,PB,PT,QE,RED,RHJ,S2M,SKY,SKYHD,SMD,SSDV,SSKP,TRG,TS,xxx-av,YKB
    key_start_word = [
        "BT-",
        "CT-",
        "EMP-",
        "CCDV-",
        "CWP-",
        "CWPBD-",
        "DSAM-",
        "DRC-",
        "DRG-",
        "GACHI-",
        "heydouga",
        "JAV-",
        "LAF-",
        "LAFBD-",
        "HEYZO-",
        "KTG-",
        "KP-",
        "KG-",
        "LLDV-",
        "MCDV-",
        "MKD-",
        "MKBD-",
        "MMDV-",
        "NIP-",
        "PB-",
        "PT-",
        "QE-",
        "RED-",
        "RHJ-",
        "S2M-",
        "SKY-",
        "SKYHD-",
        "SMD-",
        "SSDV-",
        "SSKP-",
        "TRG-",
        "TS-",
        "xxx-av-",
        "YKB-",
        "bird",
        "bouga",
    ]
    for each in key_start_word:
        if number.upper().startswith(each.upper()):
            return True
    else:
        return False


def is_suren(number: str) -> bool:
    if re.search(r"\d{3,}[A-Z]+-\d{2}", number.upper()) or "SIRO" in number.upper():
        return True
    for key in ManualConfig.SUREN_DIC.keys():
        if number.upper().startswith(key):
            return True
    return False


def get_number_letters(number: str) -> str:
    number_upper = number.upper()
    if r := re.search(r"([A-Za-z0-9-.]{3,})[-_. ]\d{2}\.\d{2}\.\d{2}", number):
        return r[1]
    if number_upper.startswith("FC2"):
        return "FC2"
    if number_upper.startswith("MYWIFE"):
        return "MYWIFE"
    if number_upper.startswith("KIN8"):
        return "KIN8"
    if number_upper.startswith("S2M"):
        return "S2M"
    if number_upper.startswith("T28"):
        return "T28"
    if number_upper.startswith("TH101"):
        return "TH101"
    if number_upper.startswith("XXX-AV"):
        return "XXX-AV"
    if r := re.search(r"(MKY-[A-Z]+)-\d{3,}", number_upper):
        return r[1]
    if re.search(r"(CW3D2D?BD)", number_upper):
        return "CW3D2D"
    if re.search(r"MCB3D[BD]*-\d{2,}", number_upper):
        return "MCB3D"
    if re.findall(r"(H4610|C0930|H0930)-[A-Z]+\d{4,}", number_upper):
        return re.findall(r"(H4610|C0930|H0930)-[A-Z]+\d{4,}", number_upper)[0]
    result = re.search(r"(\d*[A-Za-z]+)\d*", number)
    return result[1] if result else "未知车牌"


def get_number_first_letter(number: str) -> str:
    result = number.upper()[0]
    return result if result.encode("utf-8").isalnum() else "#"


def long_name(short_name: str) -> str:
    long_name = ManualConfig.OUMEI_NAME.get(short_name.lower())
    return long_name.lower().replace("-", "").replace(".", "") if long_name else short_name.lower()


def remove_escape_string(filename: str, replace_char: str = "") -> str:
    filename = filename.upper()
    for string in config.escape_string_list:
        if string:
            filename = filename.replace(string.upper(), replace_char)
    short_strings = [
        "4K",
        "4KS",
        "8K",
        "HD",
        "LR",
        "VR",
        "DVD",
        "FULL",
        "HEVC",
        "H264",
        "H265",
        "X264",
        "X265",
        "AAC",
        "XXX",
        "PRT",
    ]
    for each in short_strings:
        filename = re.sub(rf"[-_ .\[]{each.upper()}[-_ .\]]", "-", filename)
    return filename.replace("--", "-").strip("-_ .")


def get_file_number(filepath: str) -> str:
    real_name = os.path.splitext(os.path.split(filepath)[1])[0].strip() + "."

    # 去除多余字符
    file_name = remove_escape_string(real_name) + "."

    # 替换cd_part、EP、-C
    filename = (
        file_name.replace("-C.", ".")
        .replace(".PART", "-CD")
        .replace("-PART", "-CD")
        .replace(" EP.", ".EP")
        .replace("-CD-", "")
    )

    # 去除分集
    filename = re.sub(r"[-_ .]CD\d{1,2}", "", filename)  # xxx-CD1.mp4
    filename = re.sub(r"[-_ .][A-Z0-9]\.$", "", filename)  # xxx_1.mp4, xxx.1.mp4, xxx.A.mp4, xxx A.mp4
    filename = filename.replace(" ", "-").strip("-_. ")
    oumei_filename = filename

    # 去除时间
    filename = re.sub(r"\d{4}[-_.]\d{1,2}[-_.]\d{1,2}", "", filename)  # 去除文件名中时间
    filename = re.sub(r"[-\[]\d{2}[-_.]\d{2}[-_.]\d{2}]?", "", filename)  # 去除文件名中时间

    # 转换番号
    filename = (
        filename.replace("FC2-PPV", "FC2-").replace("FC2PPV", "FC2-").replace("--", "-").replace("GACHIPPV", "GACHI")
    )

    # 提取番号
    if "MYWIFE" in filename and re.search(r"NO\.\d*", filename):  # 提取 mywife No.1111
        temp_num = re.findall(r"NO\.(\d*)", filename)[0]
        return f"Mywife No.{temp_num}"

    elif r := re.search(r"CW3D2D?BD-?\d{2,}", filename):  # 提取番号 CW3D2DBD-11
        file_number = r.group()
        return file_number

    elif r := re.search(r"MMR-?[A-Z]{2,}-?\d+[A-Z]*", filename):  # 提取番号 mmr-ak089sp
        file_number = r.group()
        return file_number.replace("MMR-", "MMR")

    elif (
        r := re.search(r"([^A-Z]|^)(MD[A-Z-]*\d{4,}(-\d)?)", file_name)
    ) and "MDVR" not in file_name:  # 提取番号 md-0165-1
        file_number = r.group(2)
        return file_number

    elif re.findall(
        r"([A-Z0-9_]{2,})[-.]2?0?(\d{2}[-.]\d{2}[-.]\d{2})", oumei_filename
    ):  # 提取欧美番号 sexart.11.11.11
        result = re.findall(r"([A-Z0-9-]{2,})[-_.]2?0?(\d{2}[-.]\d{2}[-.]\d{2})", oumei_filename)
        return (long_name(result[0][0].strip("-")) + "." + result[0][1].replace("-", ".")).capitalize()

    elif r := re.search(r"XXX-AV-\d{4,}", filename):  # 提取xxx-av-11111
        file_number = r.group()

    elif r := re.search(r"MKY-[A-Z]+-\d{3,}", filename):  # MKY-A-11111
        file_number = r.group()

    elif "FC2" in filename:
        filename = filename.replace("PPV", "").replace("_", "-").replace("--", "-")
        if r := re.search(r"FC2-\d{5,}", filename):  # 提取类似fc2-111111番号
            file_number = r.group()
        elif r := re.search(r"FC2\d{5,}", filename):
            file_number = r.group().replace("FC2", "FC2-")
        else:
            file_number = filename

    elif "HEYZO" in filename:
        filename = filename.replace("_", "-").replace("--", "-")
        if r := re.search(r"HEYZO-\d{3,}", filename):  # HEYZO-1111番号
            file_number = r.group()
        elif r := re.search(r"HEYZO\d{3,}", filename):
            file_number = r.group().replace("HEYZO", "HEYZO-")
        else:
            file_number = filename

    elif r := re.search(
        r"(H4610|C0930|H0930)-[A-Z]+\d{4,}", filename
    ):  # 提取H4610-ki111111 c0930-ki221218 h0930-ori1665
        file_number = r.group()

    elif r := re.search(r"KIN8(TENGOKU)?-?\d{3,}", filename):  # 提取S2MBD-002 或S2MBD-006
        file_number = r.group().replace("TENGOKU", "-").replace("--", "-")

    elif r := re.search(r"S2M[BD]*-\d{3,}", filename):  # 提取S2MBD-002 或S2MBD-006
        file_number = r.group()

    elif r := re.search(r"MCB3D[BD]*-\d{2,}", filename):  # MCB3DBD-33
        file_number = r.group()

    elif r := re.search(r"T28-?\d{3,}", filename):  # 提取T28-223
        file_number = r.group().replace("T2800", "T28-")

    elif r := re.search(r"TH101-\d{3,}-\d{5,}", filename):  # 提取th101-140-112594
        file_number = r.group().lower()

    elif r := re.search(r"([A-Z]{2,})00(\d{3})", filename):  # 提取ssni00644为ssni-644
        file_number = r[1] + "-" + r[2]

    elif r := re.search(r"\d{2,}[A-Z]{2,}-\d{2,}[A-Z]?", filename):  # 提取类似259luxu-1456番号
        file_number = r.group()

    elif r := re.search(r"[A-Z]{2,}-\d{2,}[Z]?", filename):  # 提取类似mkbd-120番号
        file_number = r.group()
        for key, value in ManualConfig.SUREN_DIC.items():
            if key in file_number:
                file_number = value + file_number
                break

    elif r := re.search(r"[A-Z]+-[A-Z]\d+", filename):  # 提取类似mkbd-s120番号
        file_number = r.group()

    elif r := re.search(r"\d{2,}[-_]\d{2,}", filename):  # 提取类似 111111-000 111111_000 番号
        file_number = r.group()

    elif r := re.search(r"\d{3,}-[A-Z]{3,}", filename):  # 提取类似 111111-MMMM 番号
        file_number = r.group()

    elif r := re.search(r"([^A-Z]|^)(N\d{4})(\D|$)", filename):  # 提取n1111
        file_number = r.group(2).lower()

    elif r := re.search(r"H_\d{3,}([A-Z]{2,})(\d{2,})", filename):  # 提取类似h_173mega05番号
        a, b = r.groups()
        file_number = a + "-" + b

    elif r := re.findall(r"([A-Z]{3,}).*?(\d{2,})", filename):  # 3个及以上字母，2个及以上数字
        temp = r[0]
        file_number = temp[0] + "-" + temp[1]

    elif r := re.findall(r"([A-Z]{2,}).*?(\d{3,})", filename):  # 2个及以上字母，3个及以上数字
        temp = r[0]
        file_number = temp[0] + "-" + temp[1]

    else:
        temp_name = re.sub(r"[【(（\[].+?[]）)】]", "", file_name).strip("@. ")  # 去除[]
        temp_name = unicodedata.normalize("NFC", temp_name)  # Mac 把会拆成两个字符，即 NFD，而网页请求使用的是 NFC
        try:
            temp_name = temp_name.encode("cp932").decode("shift_jis")  # 转换为常见日文，比如～ 转换成 〜
        except Exception:
            pass
        file_number = temp_name

    if file_number.startswith("FC-"):
        file_number = file_number.replace("FC-", "FC2-")
    return file_number.strip("-_. ")


def deal_actor_more(actor: str) -> str:
    actor_name_max = int(config.actor_name_max)
    actor_name_more = config.actor_name_more
    actor_list = actor.split(",")
    if len(actor_list) > actor_name_max:  # 演员多于设置值时
        actor = ""
        for i in range(actor_name_max):
            actor = actor + actor_list[i] + ","
        actor = actor.strip(",") + actor_name_more
    return actor
