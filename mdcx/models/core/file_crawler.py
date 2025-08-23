import asyncio
import os
import re
from itertools import chain
from typing import TYPE_CHECKING

from patchright.async_api import Error as PatchrightError

from mdcx.config.models import Language, Website
from mdcx.gen.field_enums import CrawlerResultFields
from mdcx.manual import ManualConfig
from mdcx.models.enums import FileMode
from mdcx.models.flags import Flags
from mdcx.models.types import CrawlerInput, CrawlerResponse, CrawlerResult, CrawlersResult, CrawlTask
from mdcx.number import is_uncensored
from mdcx.utils.dataclass import update

if TYPE_CHECKING:
    from mdcx.config.models import Config
    from mdcx.crawler import CrawlerProviderProtocol


MULTI_LANGUAGE_WEBSITES = [  # 支持多语言, language 参数有意义
    Website.AIRAV_CC,
    Website.AIRAV,
    Website.IQQTV,
    Website.JAVLIBRARY,
]


def sprint_source(website: Website, language: Language) -> str:
    if language == Language.UNDEFINED:
        return f"{website.value}"
    return f"{website.value} ({language.value})"


def _deal_res(res: CrawlersResult) -> CrawlersResult:
    # 标签
    tag = re.sub(r",\d+[kKpP],", ",", res.tag)
    tag_rep_word = [",HD高画质", ",HD高畫質", ",高画质", ",高畫質"]
    for each in tag_rep_word:
        if tag.endswith(each):
            tag = tag.replace(each, "")
        tag = tag.replace(each + ",", ",")
    res.tag = tag

    # 发行日期
    release = res.release
    if release:
        release = release.replace("/", "-").strip(". ")
        if len(release) < 10:
            release_list = re.findall(r"(\d{4})-(\d{1,2})-(\d{1,2})", release)
            if release_list:
                r_year, r_month, r_day = release_list[0]
                r_month = "0" + r_month if len(r_month) == 1 else r_month
                r_day = "0" + r_day if len(r_day) == 1 else r_day
                release = r_year + "-" + r_month + "-" + r_day
    res.release = release

    # 评分
    if res.score:
        res.score = f"{float(res.score):.1f}"

    # publisher
    if not res.publisher:
        res.publisher = res.studio

    # 字符转义，避免显示问题
    key_word = [
        "title",
        "originaltitle",
        "number",
        "outline",
        "originalplot",
        "series",
        "studio",
        "publisher",
    ]
    rep_word = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&apos;": "'",
        "&quot;": '"',
        "&lsquo;": "「",
        "&rsquo;": "」",
        "&hellip;": "…",
        "<br/>": "",
        "・": "·",
        """: "「",
        """: "」",
        "...": "…",
        "\xa0": "",
        "\u3000": "",
        "\u2800": "",
    }
    for each in key_word:
        for key, value in rep_word.items():
            # res[each] = res[each].replace(key, value)
            setattr(res, each, getattr(res, each).replace(key, value))

    return res


class FileScraper:
    def __init__(self, config: "Config", crawler_provider: "CrawlerProviderProtocol"):
        self.config = config
        self.crawler_provider = crawler_provider

    async def _call_crawler(
        self, task_input: CrawlerInput, website: Website, timeout: float | None = 30
    ) -> CrawlerResponse:
        """
        调用指定网站的爬虫函数

        Args:
            task_input (CrawlerInput): 包含爬虫所需的输入数据
            website (str): 网站名称
            timeout (float | None): 请求超时时间，默认为30秒

        Raises:
            asyncio.TimeoutError: 如果请求超时
            Exception: 爬虫函数抛出的异常
        """
        short_number = task_input.short_number

        # 259LUXU-1111， mgstage 和 avsex 之外使用 LUXU-1111（素人番号时，short_number有值，不带前缀数字；反之，short_number为空)
        if short_number and website != "mgstage" and website != "avsex":
            task_input.number = short_number

        c = await self.crawler_provider.get(website)

        # 对爬虫函数调用添加超时限制, 超时异常由调用者处理
        if os.getenv("DEBUG"):
            timeout = None
        r = await asyncio.wait_for(c.run(task_input), timeout=timeout)
        return r

    async def _call_crawlers(self, task_input: CrawlerInput, type_sites: set[Website]) -> CrawlersResult:
        """
        获取一组网站的数据：按照设置的网站组，请求各字段数据，并返回最终的数据
        采用按需请求策略：仅请求必要的网站，失败时才请求下一优先级网站
        """
        all_res: dict[tuple[Website, Language], CrawlerResult] = {}
        failed: set[tuple[Website, Language]] = set()  # 记录失败的网站
        reduced = CrawlersResult.empty()
        req_info: list[str] = []  # 请求信息列表

        # 按字段分别处理，每个字段按优先级尝试获取
        for field in ManualConfig.REDUCED_FIELDS:
            # 获取该字段的优先级列表
            f_config = self.config.get_field_config(field)
            f_sites = [s for s in f_config.site_prority if s in type_sites]
            f_lang = f_config.language

            reduced.field_log += (
                f"\n\n    📌 {field} \n    ====================================\n"
                f"    🌐 优先级设置: {' -> '.join(s.value for s in f_sites)}"
            )

            # 按优先级依次尝试获取字段值
            for site in f_sites:
                # 检查是否已经请求过该网站
                key = (site, f_lang)

                # 如果网站不支持多语言, 则使用 UNDEFINED
                if site not in MULTI_LANGUAGE_WEBSITES:
                    key = (site, Language.UNDEFINED)

                # 如果已有该网站数据，直接使用
                if key in all_res:
                    site_data = all_res[key]
                elif key in failed:
                    # 不再请求已失败的网站
                    reduced.field_log += f"\n    🔴 {site:<15} (已失败, 跳过)"
                    continue
                else:
                    # 如果网站数据尚未请求，则进行请求
                    try:
                        task_input.language = f_lang
                        task_input.org_language = f_lang
                        # 多语言网站, 指定一个默认语言
                        if site in MULTI_LANGUAGE_WEBSITES and key[1] == Language.UNDEFINED:
                            task_input.language = Language.JP
                            task_input.org_language = Language.JP
                        web_data = await self._call_crawler(task_input, site)
                        req_info.append(f"{sprint_source(*key)} ({web_data.debug_info.execution_time:.2f}s)")
                        if web_data.data is None:
                            if e := web_data.debug_info.error:
                                raise e
                            raise ValueError(f"{site} 返回了空数据")
                        site_data = web_data.data
                        # 处理并保存结果
                        all_res[key] = web_data.data
                        # 多语言网站, 如果 undefined 尚不存在, 也使用当前语言数据
                        if site in MULTI_LANGUAGE_WEBSITES and (site, Language.UNDEFINED) not in all_res:
                            all_res[(site, Language.UNDEFINED)] = web_data.data
                    except Exception as e:
                        if isinstance(e, PatchrightError):
                            if "BrowserType.launch: Executable doesn't exist" in e.message:
                                e = "找不到 Chrome 浏览器, 请安装或关闭对应网站的 use_browser 选项"
                        reduced.field_log += f"\n    🔴 {site:<15} (失败: {str(e)})"
                        failed.add(key)
                        continue

                # 检查字段数据
                if not getattr(site_data, field.value, None):
                    reduced.field_log += f"\n    🔴 {site:<15} (未找到)"
                    continue

                # 添加来源信息
                reduced.field_sources[field] = site.value

                if field == CrawlerResultFields.POSTER:
                    reduced.image_download = site_data.image_download
                elif field == CrawlerResultFields.ORIGINALTITLE and site_data.actor:
                    reduced.amazon_orginaltitle_actor = site_data.actor.split(",")[0]

                # 保存数据
                setattr(reduced, field.value, getattr(site_data, field.value))
                reduced.field_log += f"\n    🟢 {site}\n     ↳{getattr(reduced, field.value)}"
                # 找到有效数据，跳出循环继续处理下一个字段
                break
            else:  # 所有来源都无此字段
                reduced.field_log += "\n    🔴 所有来源均无数据"

        # 需尽力收集的字段
        for data in all_res.values():
            # 记录所有来源的 thumb url 以便后续下载
            if data.thumb:
                reduced.thumb_list.append((data.source, data.thumb))
            # 记录所有来源的 actor 用于 Amazon 搜图
            if data.actor:
                reduced.actor_amazon.extend(data.actors)
        # 去重
        reduced.thumb_list = list(dict.fromkeys(reduced.thumb_list))  # 保序
        reduced.actor_amazon = list(set(reduced.actor_amazon))

        # 处理 year
        if reduced.year and (r := re.search(r"\d{4}", reduced.release)):
            reduced.year = r.group()

        # 处理 javdbid
        if r := all_res.get((Website.JAVDB, Language.UNDEFINED)):
            reduced.javdbid = r.javdbid

        # 使用 actors 字段补全 all_actors, 理想情况下前者应该是后者的子集
        # 对 actors 的所有后处理都需要同样地应用到 all_actors
        reduced.all_actors = list(dict.fromkeys(chain(reduced.all_actors, reduced.actors)))

        reduced.site_log = f"\n 🌐 [website] {'-> '.join(req_info)}"

        return reduced

    async def _call_specific_crawler(self, task_input: CrawlerInput, website: Website) -> CrawlersResult:
        file_number = task_input.number
        short_number = task_input.short_number

        title_language = self.config.get_field_config(CrawlerResultFields.TITLE).language
        org_language = title_language

        if website not in ["airav_cc", "iqqtv", "airav", "avsex", "javlibrary", "mdtv", "madouqu", "lulubar"]:
            title_language = Language.JP

        elif website == "mdtv":
            title_language = Language.ZH_CN

        task_input.language = title_language
        task_input.org_language = org_language
        web_data = await self._call_crawler(task_input, website)
        web_data_json = web_data.data
        if web_data_json is None:
            return CrawlersResult.empty()

        res = update(CrawlersResult.empty(), web_data_json)
        if not res.title:
            return res
        if res.thumb:
            res.thumb_list = [(website, res.thumb)]

        # 加入来源信息
        res.field_sources = dict.fromkeys(CrawlerResultFields, website.value)

        res.site_log = (
            f"\n 🌐 [website] {sprint_source(website, title_language)} ({web_data.debug_info.execution_time:.2f}s)"
        )

        if short_number:
            res.number = file_number

        res.actor_amazon = web_data_json.actors
        res.all_actors = list(dict.fromkeys(chain(res.all_actors, web_data_json.actors)))

        return res

    async def _crawl(self, task_input: CrawlTask, website: Website | None) -> CrawlersResult:  # 从JSON返回元数据
        appoint_number = task_input.appoint_number
        destroyed = task_input.destroyed
        file_number = task_input.number
        file_path = task_input.file_path
        leak = task_input.leak
        mosaic = task_input.mosaic
        short_number = task_input.short_number
        wuma = task_input.wuma
        youma = task_input.youma

        # ================================================网站规则添加开始================================================

        if website is None:  # 从全部网站刮削
            # =======================================================================先判断是不是国产，避免浪费时间
            if (
                mosaic == "国产"
                or mosaic == "國產"
                or (re.search(r"([^A-Z]|^)MD[A-Z-]*\d{4,}", file_number) and "MDVR" not in file_number)
                or re.search(r"MKY-[A-Z]+-\d{3,}", file_number)
            ):
                task_input.mosaic = "国产"
                res = await self._call_crawlers(task_input, self.config.website_guochan)

            # =======================================================================kin8
            elif file_number.startswith("KIN8"):
                website = Website.KIN8
                res = await self._call_specific_crawler(task_input, website)

            # =======================================================================同人
            elif file_number.startswith("DLID"):
                website = Website.GETCHU
                res = await self._call_specific_crawler(task_input, website)

            # =======================================================================里番
            elif "getchu" in file_path.lower() or "里番" in file_path or "裏番" in file_path:
                website = Website.GETCHU_DMM
                res = await self._call_specific_crawler(task_input, website)

            # =======================================================================Mywife No.1111
            elif "mywife" in file_path.lower():
                website = Website.MYWIFE
                res = await self._call_specific_crawler(task_input, website)

            # =======================================================================FC2-111111
            elif "FC2" in file_number.upper():
                file_number_1 = re.search(r"\d{5,}", file_number)
                if file_number_1:
                    file_number_1.group()
                    res = await self._call_crawlers(task_input, self.config.website_fc2)
                else:
                    raise Exception(f"未识别的 FC2 番号: {file_number}")

            # =======================================================================sexart.15.06.14
            elif re.search(r"[^.]+\.\d{2}\.\d{2}\.\d{2}", file_number) or (
                "欧美" in file_path and "东欧美" not in file_path
            ):
                res = await self._call_crawlers(task_input, self.config.website_oumei)

            # =======================================================================无码抓取:111111-111,n1111,HEYZO-1111,SMD-115
            elif mosaic == "无码" or mosaic == "無碼":
                res = await self._call_crawlers(task_input, self.config.website_wuma)

            # =======================================================================259LUXU-1111
            elif short_number or "SIRO" in file_number.upper():
                res = await self._call_crawlers(task_input, self.config.website_suren)

            # =======================================================================ssni00321
            elif re.match(r"\D{2,}00\d{3,}", file_number) and "-" not in file_number and "_" not in file_number:
                res = await self._call_crawlers(task_input, {Website.DMM})

            # =======================================================================剩下的（含匹配不了）的按有码来刮削
            else:
                res = await self._call_crawlers(task_input, self.config.website_youma)
        else:
            res = await self._call_specific_crawler(task_input, website)

        # ================================================网站请求结束================================================
        # ======================================超时或未找到返回

        number = file_number  # res.number 实际上并未设置, 此处取 file_number
        if appoint_number:
            number = appoint_number
        res.number = number  # 此处设置

        # 马赛克
        if leak:
            res.mosaic = "无码流出"
        elif destroyed:
            res.mosaic = "无码破解"
        elif wuma:
            res.mosaic = "无码"
        elif youma:
            res.mosaic = "有码"
        elif mosaic:
            res.mosaic = mosaic
        if not res.mosaic:
            if is_uncensored(number):
                res.mosaic = "无码"
            else:
                res.mosaic = "有码"

        # 原标题，用于amazon搜索
        res.originaltitle_amazon = res.originaltitle
        if res.actor_amazon:
            for each in res.actor_amazon:  # 去除演员名，避免搜索不到
                try:
                    end_actor = re.compile(rf" {each}$")
                    res.originaltitle_amazon = re.sub(end_actor, "", res.originaltitle_amazon)
                except Exception:
                    pass

        # VR 时下载小封面
        if "VR" in number:
            res.image_download = True

        return res

    def _get_site(self, task_input: CrawlTask, file_mode: FileMode):
        # 获取刮削网站
        website_name = None
        if file_mode == FileMode.Single:  # 刮削单文件（工具页面）
            website_name = Flags.website_name
        elif file_mode == FileMode.Again:  # 重新刮削
            website_temp = task_input.website_name
            if website_temp:
                website_name = website_temp
        elif self.config.scrape_like == "single":
            website_name = self.config.website_single

        return website_name

    async def run(self, task_input: CrawlTask, file_mode: FileMode) -> CrawlersResult:
        site = self._get_site(task_input, file_mode)
        if site is not None:
            site = Website(site)
        res = await self._crawl(task_input, site)
        return _deal_res(res)
