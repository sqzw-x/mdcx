import asyncio
import re
from collections.abc import Callable

from aiolimiter import AsyncLimiter
from httpx import AsyncClient, Timeout
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam


class LLMClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,  # https://api.openai.com/v1
        proxy: str | None = None,
        timeout: Timeout,
        rate: tuple[float, float],
    ):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=AsyncClient(proxy=proxy, verify=False, timeout=timeout, follow_redirects=True),
            timeout=timeout,
        )
        self.limiter = AsyncLimiter(*rate)

    async def ask(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.8,
        max_try: int,
        log_fn: Callable[[str], None] = lambda _: None,
        extra_body: object | None = None,
    ) -> str | None:
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        wait = 1
        async with self.limiter:
            for _ in range(max_try):
                try:
                    chat = await self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        extra_body=extra_body,
                    )
                    break
                except Exception as e:
                    log_fn(f"⚠️ LLM API 请求失败: {e}, {wait}s 后重试")
                    await asyncio.sleep(wait)
                    wait *= 2
            else:
                log_fn("❌ LLM API 请求失败, 已达最大重试次数\n")
                return None
        # reasoning_content = getattr(chat.choices[0].message, "reasoning_content", None)
        text = chat.choices[0].message.content
        # 移除 cot
        if text:
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        return text
