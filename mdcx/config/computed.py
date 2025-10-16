import re

import httpx

from ..llm import LLMClient, OllamaClient
from ..manual import ManualConfig
from ..signals import signal
from ..utils import executor, get_random_headers
from ..web_async import AsyncWebClient
from .enums import CleanAction
from .models import Config


class Computed:
    def __init__(self, config: Config):
        self.can_clean = CleanAction.I_KNOW in config.clean_enable and CleanAction.I_AGREE in config.clean_enable

        self.random_headers = get_random_headers()

        proxy = config.proxy if config.use_proxy else None
        self.llm_client = LLMClient(
            api_key=config.translate_config.llm_key,
            base_url=config.translate_config.llm_url.unicode_string(),
            proxy=proxy,
            timeout=httpx.Timeout(config.timeout, read=config.translate_config.llm_read_timeout),
            rate=(max(config.translate_config.llm_max_req_sec, 1), max(1, 1 / config.translate_config.llm_max_req_sec)),
        )

        # 初始化 Ollama 客户端
        self.ollama_client = OllamaClient(
            base_url=config.translate_config.ollama_url.unicode_string(),
            timeout=httpx.Timeout(config.timeout, read=config.translate_config.ollama_read_timeout),
            rate=(max(config.translate_config.ollama_max_req_sec, 0.1), max(1, 1 / config.translate_config.ollama_max_req_sec)),
        )

        self.async_client = AsyncWebClient(
            loop=executor._loop,
            proxy=proxy,
            retry=config.retry,
            timeout=config.timeout,
            log_fn=signal.add_log,
        )

        official_websites_dic = {}
        for key, value in ManualConfig.OFFICIAL.items():
            temp_list = value.upper().split("|")
            for each in temp_list:
                official_websites_dic[each] = key
        self.official_websites = official_websites_dic

        self.escape_string_list = list(dict.fromkeys(k for k in config.string + ManualConfig.REPL_LIST if k.strip()))

        # 生成 Google 关键词列表 迁移自 ConfigV1.init
        temp_list = re.split(r"[,，]", ",".join(config.google_used))
        self.google_keyused = [each for each in temp_list if each.strip()]  # 去空
        temp_list = re.split(r"[,，]", ",".join(config.google_exclude))
        self.google_keyword = [each for each in temp_list if each.strip()]  # 去空
