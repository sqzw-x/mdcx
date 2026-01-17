from typing import override

from ..config.models import Website
from ..models.types import CrawlerResult
from .base import BaseCrawler, CralwerException, CrawlerData


class TheJavdbApiCrawler(BaseCrawler):
    @classmethod
    @override
    def site(cls) -> Website:
        return Website.THEJAVDB_API

    @classmethod
    @override
    def base_url_(cls) -> str:
        return "https://api.thejavdb.net"

    @override
    async def _generate_search_url(self, ctx) -> list[str]:
        return []

    @override
    async def _parse_search_page(self, ctx, html, search_url) -> list[str] | None:
        return None

    @override
    async def _parse_detail_page(self, ctx, html, detail_url) -> CrawlerData | None:
        return None

    @override
    async def _run(self, ctx) -> CrawlerResult:
        number = ctx.input.number.strip()
        url = f"{self.base_url}/v1/movies?q={number}"
        ctx.debug(f"API URL: {url}")

        json_data, error = await self.async_client.get_json(url)

        if not json_data:
            ctx.debug(f"API 请求失败: {error}")
            raise CralwerException(f"API Request Failed: {error}")

        data = self._parse_data(ctx, json_data)

        data.source = self.site().value
        result = data.to_result()

        return await self.post_process(ctx, result)

    def _parse_data(self, ctx, json_data: dict) -> CrawlerData:
        universal_id = json_data.get("universal_id")
        title = json_data.get("title")
        description = json_data.get("description")
        fullcover = json_data.get("fullcover_url")
        frontcover = json_data.get("frontcover_url")
        release_date = json_data.get("release_date")
        duration = json_data.get("duration")
        maker = json_data.get("maker")
        label = json_data.get("label")
        series = json_data.get("series")
        actresses = json_data.get("actresses")
        directors = json_data.get("directors")
        genres = json_data.get("genres")
        samples = json_data.get("samples")
        trailer = json_data.get("sample_movie_url")

        data = CrawlerData()
        data.number = universal_id
        data.title = title
        data.originaltitle = title
        data.outline = description
        data.originalplot = description
        data.poster = fullcover
        data.thumb = frontcover
        data.release = release_date

        if release_date and len(release_date) >= 4:
            data.year = release_date[:4]

        if duration is not None:
            data.runtime = str(duration)

        data.studio = maker
        data.publisher = label
        data.series = series
        data.tags = genres
        data.extrafanart = samples
        data.actors = actresses
        data.directors = directors
        data.trailer = trailer

        data.image_download = True

        # Mosaic check
        if title and any(k in title for k in ["無碼", "無修正", "Uncensored"]):
            data.mosaic = "无码"
        else:
            data.mosaic = "有码"

        return data
