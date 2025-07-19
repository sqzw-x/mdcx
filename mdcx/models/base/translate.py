import asyncio
import hashlib
import random
import time
from typing import Literal, Optional, Union, cast

from mdcx.config.manager import config
from mdcx.signals import signal


async def youdao_translate_async(title: str, outline: str):
    url = "https://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule"
    msg = f"{title}\n{outline}"
    lts = str(int(time.time() * 1000))
    salt = lts + str(random.randint(0, 10))
    sign = hashlib.md5(("fanyideskweb" + msg + salt + "Ygy_4c=r#e#4EX^NUGUc5").encode("utf-8")).hexdigest()

    data = {
        "i": msg,
        "from": "AUTO",
        "to": "zh-CHS",
        "smartresult": "dict",
        "client": "fanyideskweb",
        "salt": salt,
        "sign": sign,
        "lts": lts,
        "bv": "c6b8c998b2cbaa29bd94afc223bc106c",
        "doctype": "json",
        "version": "2.1",
        "keyfrom": "fanyi.web",
        "ue": "UTF-8",
        "typoResult": "true",
        "action": "FY_BY_CLICKBUTTION",
    }
    headers = {
        "Cookie": random.choice(
            [
                "OUTFOX_SEARCH_USER_ID=833904829@10.169.0.84",
                "OUTFOX_SEARCH_USER_ID=-10218418@11.136.67.24;",
                "OUTFOX_SEARCH_USER_ID=1989505748@10.108.160.19;",
                "OUTFOX_SEARCH_USER_ID=2072418438@218.82.240.196;",
                "OUTFOX_SEARCH_USER_ID=1768574849@220.181.76.83;",
                "OUTFOX_SEARCH_USER_ID=-2153895048@10.168.8.76;",
            ]
        ),
        "Referer": "https://fanyi.youdao.com/?keyfrom=dict2.top",
    }
    headers_o = config.headers
    headers.update(headers_o)
    res, error = await config.async_client.post_json(url, data=data, headers=headers)
    if res is None:
        return title, outline, f"请求失败！可能是被封了，可尝试更换代理！错误：{error}"
    else:
        res = cast(dict, res)
        translateResult = res.get("translateResult")
        if not translateResult:
            return title, outline, f"返回数据未找到翻译结果！返回内容：{res}"
        else:
            list_count = len(translateResult)
            if list_count:
                i = 0
                if title:
                    i = 1
                    title_result_list = translateResult[0]
                    title_list = [a.get("tgt") for a in title_result_list]
                    title_temp = "".join(title_list)
                    if title_temp:
                        title = title_temp
                if outline:
                    outline_temp = ""
                    for j in range(i, list_count):
                        outline_result_list = translateResult[j]
                        outline_list = [a.get("tgt") for a in outline_result_list]
                        outline_temp += "".join(outline_list) + "\n"
                    outline_temp = outline_temp.strip("\n")
                    if outline_temp:
                        outline = outline_temp
    return title, outline.strip("\n"), ""


async def _deepl_translate(text: str, source_lang: Union[Literal["JA"], Literal["EN"]] = "JA") -> Optional[str]:
    """调用 DeepL API 翻译文本"""
    if not text:
        return ""

    deepl_key = config.deepl_key
    if not deepl_key:
        return None

    # 确定 API URL, 免费版本的 key 包含 ":fx" 后缀，付费版本的 key 不包含 ":fx" 后缀
    deepl_url = "https://api-free.deepl.com" if ":fx" in deepl_key else "https://api.deepl.com"
    url = f"{deepl_url}/v2/translate"
    # 构造请求头
    headers = {"Content-Type": "application/json", "Authorization": f"DeepL-Auth-Key {deepl_key}"}
    # 构造请求体
    data = {"text": [text], "source_lang": source_lang, "target_lang": "ZH"}
    res, error = await config.async_client.post_json(url, json_data=data, headers=headers)
    if res is None:
        signal.add_log(f"DeepL API 请求失败: {error}")
        return None
    if "translations" in res and len(res["translations"]) > 0:
        return res["translations"][0]["text"]
    else:
        signal.add_log(f"DeepL API 返回数据异常: {res}")
        return None


async def deepl_translate_async(
    title: str,
    outline: str,
    ls: Union[Literal["JA"], Literal["EN"]] = "JA",
):
    """DeepL 翻译接口"""
    r1, r2 = await asyncio.gather(_deepl_translate(title, ls), _deepl_translate(outline, ls))
    if r1 is None or r2 is None:
        return "", "", "DeepL 翻译失败! 查看网络日志以获取更多信息"
    return r1, r2, None


async def _llm_translate(text: str, target_language: str = "简体中文") -> Optional[str]:
    """调用 LLM 翻译文本"""
    if not text:
        return ""
    return await config.llm_client.ask(
        model=config.llm_model,
        system_prompt="You are a professional translator.",
        user_prompt=config.llm_prompt.replace("{content}", text).replace("{lang}", target_language),
        temperature=config.llm_temperature,
        max_try=config.llm_max_try,
        log_fn=signal.add_log,
    )


async def llm_translate_async(title: str, outline: str, target_language: str = "简体中文"):
    r1, r2 = await asyncio.gather(_llm_translate(title, target_language), _llm_translate(outline, target_language))
    if r1 is None or r2 is None:
        return "", "", "LLM 翻译失败! 查看网络日志以获取更多信息"
    return r1, r2, None


async def _google_translate(msg: str) -> tuple[Optional[str], str]:
    if not msg:
        return "", ""
    msg_unquote = urllib.parse.unquote(msg)
    url = f"https://translate.google.com/translate_a/single?client=gtx&sl=auto&tl=zh-CN&dt=t&q={msg_unquote}"
    response, error = await config.async_client.get_json(url)
    if response is None:
        return None, error
    return "".join([sen[0] for sen in response[0]]), ""


async def google_translate_async(title: str, outline: str) -> tuple[str, str, Optional[str]]:
    (r1, e1), (r2, e2) = await asyncio.gather(_google_translate(title), _google_translate(outline))
    if r1 is None or r2 is None:
        return "", "", f"google 翻译失败! {e1} {e2}"
    return r1, r2, None
