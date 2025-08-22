from typing import TYPE_CHECKING, Never

from .config.enums import Website
from .crawlers import get_crawler_compat

if TYPE_CHECKING:
    from .browser import BrowserProvider
    from .config.models import Config
    from .crawlers.base import GenericBaseCrawler
    from .crawlers.base.compat import LegacyCrawler
    from .web_async import AsyncWebClient


class CrawlerProvider:
    def __init__(self, config: "Config", client: "AsyncWebClient", browser_provider: "BrowserProvider"):
        self.instances: dict[Website, GenericBaseCrawler[Never] | LegacyCrawler] = {}
        self.config = config
        self.client = client
        self.browser_provider = browser_provider
        self.browser = None

    async def get(self, site: Website):
        if site not in self.instances:
            use_browser = self.config.get_site_config(site).use_browser
            if use_browser and self.browser is None:
                self.browser = await self.browser_provider.get_browser()
            crawler_cls = get_crawler_compat(site)
            self.instances[site] = crawler_cls(
                client=self.client,
                base_url=self.config.get_site_url(site),
                browser=self.browser,
            )
        return self.instances[site]
