import asyncio
import os
from typing import TYPE_CHECKING

from patchright.async_api import async_playwright

if TYPE_CHECKING:
    from patchright.async_api import Browser

    from .config.models import Config


class BrowserProvider:
    def __init__(self, config: "Config"):
        self.config = config
        self.playwright = None
        self.default_browser = None
        self.lock = asyncio.Lock()

    async def get_browser(self) -> "Browser":
        if self.default_browser is not None:
            return self.default_browser
        async with self.lock:
            if self.playwright is None:
                self.playwright = await async_playwright().start()
            if self.default_browser is None:
                self.default_browser = await self.playwright.chromium.launch(
                    channel="chrome",
                    headless=os.getenv("MDCX_SHOW_BROWSER") is None,
                )
        return self.default_browser

    async def close(self):
        if self.default_browser is not None:
            await self.default_browser.close()
        if self.playwright is not None:
            await self.playwright.stop()
        self.playwright = None
        self.default_browser = None
