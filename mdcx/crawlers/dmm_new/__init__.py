import re
from collections import defaultdict
from typing import override

from parsel import Selector

from mdcx.config.models import Website
from mdcx.models.base.web import check_url
from mdcx.utils.dataclass import update_valid
from mdcx.utils.gather_group import GatherGroup

from ..base import BaseCrawler, Context, CralwerException, CrawlerData, DetailPageParser, is_valid
from .parsers import Category, DigitalParser, MonoParser, RentalParser, parse_category
from .tv import DmmTvResponse, FanzaResp, dmm_tv_com_payload, fanza_tv_payload


class DmmCrawler(BaseCrawler):
    mono = MonoParser()
    digital = DigitalParser()
    rental = RentalParser()

    @classmethod
    @override
    def site(cls) -> Website:
        return Website.DMM

    @classmethod
    @override
    def base_url_(cls) -> str:
        # DMM 不支持自定义 URL
        return ""

    @override
    def _get_cookies(self, ctx) -> dict[str, str] | None:
        return {"age_check_done": "1"}

    @override
    async def _generate_search_url(self, ctx) -> list[str] | None:
        number = ctx.input.number.lower()

        if x := re.findall(r"[A-Za-z]+-?(\d+)", number):
            digits = x[0]
            if len(digits) >= 5 and digits.startswith("00"):
                number = number.replace(digits, digits[2:])
            elif len(digits) == 4:
                number = number.replace("-", "0")  # https://github.com/sqzw-x/mdcx/issues/393

        # 搜索结果多，但snis-027没结果
        number_00 = number.replace("-", "00")
        # 搜索结果少
        number_no_00 = number.replace("-", "")

        return [
            f"https://www.dmm.co.jp/search/=/searchstr={number_00}/sort=ranking/",
            f"https://www.dmm.co.jp/search/=/searchstr={number_no_00}/sort=ranking/",
            f"https://www.dmm.com/search/=/searchstr={number_no_00}/sort=ranking/",  # 写真
        ]

    @override
    async def _parse_search_page(self, ctx, html, search_url) -> list[str] | None:
        if "404 Not Found" in html.css("span.d-txten::text").get(""):
            raise CralwerException("404! 页面地址错误！")

        # \"detailUrl\":\"https://www.dmm.co.jp/digital/videoa/-/detail/=/cid=ssni00103/?i3_ord=1\u0026i3_ref=search"
        url_list = set(html.re(r'detailUrl\\":\\"(.*?)\\"'))
        if not url_list:
            ctx.debug(f"没有找到搜索结果: {ctx.input.number} {search_url=}")
            return None

        number_parts: re.Match[str] | None = re.search(r"(\d*[a-z]+)?-?(\d+)", ctx.input.number.lower())
        if not number_parts:
            ctx.debug(f"无法从番号 {ctx.input.number} 提取前缀和数字")
            return None
        prefix = number_parts.group(1)
        digits = number_parts.group(2)
        n1 = f"{prefix}{digits:0>5}"
        n2 = f"{prefix}{digits}"

        res = []
        for u in url_list:
            # https://tv.dmm.co.jp/list/?content=mide00726&i3_ref=search&i3_ord=1
            # https://www.dmm.co.jp/digital/videoa/-/detail/=/cid=mide00726/?i3_ref=search&i3_ord=2
            # https://www.dmm.com/mono/dvd/-/detail/=/cid=n_709mmrak089sp/?i3_ref=search&i3_ord=1
            if re.search(rf"[^a-z]{n1}[^0-9]", u) or re.search(rf"[^a-z]{n2}[^0-9]", u):
                res.append(u.encode("utf-8").decode("unicode_escape"))

        return res

    @classmethod
    def _get_parser(cls, category: Category):
        match category:
            case Category.PRIME | Category.MONTHLY | Category.MONO:
                return cls.mono
            case Category.DIGITAL:
                return cls.digital
            case Category.RENTAL:
                return cls.rental

    @override
    async def _detail(self, ctx: Context, detail_urls: list[str]) -> CrawlerData | None:
        d = defaultdict(list)
        for url in detail_urls:
            category = parse_category(url)
            d[category].append(url)

        async with GatherGroup[CrawlerData]() as group:
            for url in d[Category.FANZA_TV]:
                group.add(self.fetch_fanza_tv(ctx, url))
            for url in d[Category.DMM_TV]:
                group.add(self.fetch_dmm_tv(ctx, url))

            for category in (
                Category.MONO,
                Category.RENTAL,
                Category.PRIME,
                Category.MONTHLY,
                # Category.DIGITAL,
            ):  # 优先级
                parser = self._get_parser(category)
                if parser is None:
                    continue
                for u in sorted(d[category]):
                    group.add(self.fetch_and_parse(ctx, u, parser))

        res = None
        for r in group.results[::-1]:
            if isinstance(r, Exception):  # 预计只会返回空值, 不会抛出异常
                ctx.debug(f"预料之外的异常: {r}")
                continue
            if res is None:
                res = r
            else:
                res = update_valid(res, r, is_valid)

        return res

    async def fetch_fanza_tv(self, ctx: Context, detail_url: str) -> CrawlerData:
        cid = re.search(r"content=([^&/]+)", detail_url)
        if not cid:
            ctx.debug(f"无法从 DMM TV URL 提取 cid: {detail_url}")
            return CrawlerData()
        cid = cid.group(1)

        response, error = await self.async_client.post_json(
            "https://api.tv.dmm.co.jp/graphql", json_data=fanza_tv_payload(cid)
        )
        if response is None:
            ctx.debug(f"Fanza TV API 请求失败: {cid=} {error=}")
            return CrawlerData()
        try:
            resp = FanzaResp.model_validate(response)
            data = resp.data.fanzaTvPlus.content
        except Exception as e:
            ctx.debug(f"Fanza TV API 响应解析失败: {e}")
            return CrawlerData()

        extrafanart = []
        for sample_pic in data.samplePictures:
            if sample_pic.imageLarge:
                extrafanart.append(sample_pic.imageLarge)

        # https://cc3001.dmm.co.jp/hlsvideo/freepv/s/ssi/ssis00497/playlist.m3u8
        trailer_url = data.sampleMovie.url.replace("hlsvideo", "litevideo")
        cid_match = re.search(r"/([^/]+)/playlist.m3u8", trailer_url)
        if cid_match:
            cid = cid_match.group(1)
            trailer = trailer_url.replace("playlist.m3u8", cid + "_sm_w.mp4")
        else:
            trailer = ""

        return CrawlerData(
            title=data.title,
            outline=data.description,
            release=data.startDeliveryAt,  # 2025-05-17T20:00:00Z
            tags=[genre.name for genre in data.genres],
            runtime=str(int(data.playInfo.duration / 60)),
            actors=[a.name for a in data.actresses],
            poster=data.packageImage,
            thumb=data.packageLargeImage,
            score=str(data.reviewSummary.averagePoint),
            series=data.series.name,
            directors=[d.name for d in data.directors],
            studio=data.maker.name,
            publisher=data.label.name,
            extrafanart=extrafanart,
            trailer=trailer,
            url=detail_url,
        )

    async def fetch_dmm_tv(self, ctx: Context, detail_url: str) -> CrawlerData:
        season_id = re.search(r"seasonId=(\d+)", detail_url)
        if not season_id:
            ctx.debug(f"无法从 DMM TV URL 提取 seasonId: {detail_url}")
            return CrawlerData()
        season_id = season_id.group(1)
        response, error = await self.async_client.post_json(
            "https://api.tv.dmm.com/graphql", json_data=dmm_tv_com_payload(season_id)
        )
        if response is None:
            ctx.debug(f"DMM TV API 请求失败: {season_id=} {error=}")
            return CrawlerData()
        try:
            resp = DmmTvResponse.model_validate(response)
            data = resp.data.video
        except Exception as e:
            ctx.debug(f"DMM TV API 响应解析失败: {e}")
            return CrawlerData()

        studio = ""
        if r := [item.staffName for item in data.staffs if item.roleName in ["制作プロダクション", "制作", "制作著作"]]:
            studio = r[0]

        return CrawlerData(
            title=data.titleName,
            outline=data.description,
            actors=[item.actorName for item in data.casts],
            poster=data.packageImage,
            thumb=data.keyVisualImage,
            tags=[item.name for item in data.genres],
            release=data.startPublicAt,  # 2025-05-17T20:00:00Z
            year=str(data.productionYear),
            score=str(data.reviewSummary.averagePoint),
            directors=[item.staffName for item in data.staffs if item.roleName == "監督"],
            studio=studio,
            publisher=studio,
            url=detail_url,
        )

    async def fetch_and_parse(self, ctx: Context, detail_url: str, parser: DetailPageParser) -> CrawlerData:
        html, error = await self._fetch_detail(ctx, detail_url)
        if html is None:
            ctx.debug(f"详情页请求失败: {error=}")
            return CrawlerData()
        ctx.debug(f"详情页请求成功: {detail_url=}")
        return await parser.parse(ctx, Selector(html), url=detail_url)

    @override
    async def post_process(self, ctx, res):
        if not res.number:
            res.number = ctx.input.number
        res.image_download = "VR" in res.title
        res.originaltitle = res.title
        res.originalplot = res.outline
        # check aws image
        if res.thumb and "pics.dmm.co.jp" in res.thumb:
            aws_url = res.thumb.replace("pics.dmm.co.jp", "awsimgsrc.dmm.co.jp/pics_dig").replace("/adult/", "/")
            if await check_url(aws_url):
                ctx.debug(f"use aws image: {aws_url}")
                res.thumb = aws_url
        res.poster = res.thumb.replace("pl.jpg", "ps.jpg")
        if not res.publisher:
            res.publisher = res.studio
        if len(res.release) >= 4:
            res.year = res.release[:4]
        res.externalId = res.url  # 由于 dmm 子类众多, 直接使用 url
        return res

    @override
    async def _parse_detail_page(self, ctx, html: Selector, detail_url: str) -> CrawlerData | None:
        raise NotImplementedError
