#!/usr/bin/python
import json
import re
import time

from lxml import etree

from mdcx.config.manager import manager
from mdcx.crawlers.dmm_new.tv import DmmTvResponse, FanzaResp, dmm_tv_com_payload, fanza_tv_payload
from mdcx.models.base.web import check_url
from mdcx.models.log_buffer import LogBuffer


def get_title(html):
    result = html.xpath('//h1[@id="title"]/text()')
    if not result:
        result = html.xpath('//h1[@class="item fn bold"]/text()')
    return result[0].strip() if result else ""


def get_actor(html):
    result = html.xpath("//span[@id='performer']/a/text()")
    if not result:
        result = html.xpath("//td[@id='fn-visibleActor']/div/a/text()")
    if not result:
        result = html.xpath("//td[contains(text(),'出演者')]/following-sibling::td/a/text()")
    return ",".join(result)


def get_actor_photo(actor):
    actor = actor.split(",")
    data = {}
    for i in actor:
        actor_photo = {i: ""}
        data.update(actor_photo)
    return data


def get_mosaic(html):
    result = html.xpath('//li[@class="on"]/a/text()')
    return "里番" if result and result[0] == "アニメ" else "有码"


def get_studio(html):
    result = html.xpath("//td[contains(text(),'メーカー')]/following-sibling::td/a/text()")
    return result[0] if result else ""


def get_publisher(html, studio):
    result = html.xpath("//td[contains(text(),'レーベル')]/following-sibling::td/a/text()")
    return result[0] if result else studio


def get_runtime(html):
    result = html.xpath("//td[contains(text(),'収録時間')]/following-sibling::td/text()")
    if not result or not re.search(r"\d+", str(result[0])):
        result = html.xpath("//th[contains(text(),'収録時間')]/following-sibling::td/text()")
    if result and (r := re.search(r"\d+", str(result[0]))):
        return r.group()
    return ""


def get_series(html):
    result = html.xpath("//td[contains(text(),'シリーズ')]/following-sibling::td/a/text()")
    if not result:
        result = html.xpath("//th[contains(text(),'シリーズ')]/following-sibling::td/a/text()")
    return result[0] if result else ""


def get_year(release):
    if r := re.search(r"\d{4}", str(release)):
        return r.group()
    return ""


def get_release(html):
    result = html.xpath("//td[contains(text(),'発売日')]/following-sibling::td/text()")
    if not result:
        result = html.xpath("//th[contains(text(),'発売日')]/following-sibling::td/text()")
    if not result:
        result = html.xpath("//td[contains(text(),'配信開始日')]/following-sibling::td/text()")
    if not result:
        result = html.xpath("//th[contains(text(),'配信開始日')]/following-sibling::td/text()")

    release = result[0].strip().replace("/", "-") if result else ""
    result = re.findall(r"(\d{4}-\d{1,2}-\d{1,2})", release)
    return result[0] if result else ""


def get_tag(html):
    result = html.xpath("//td[contains(text(),'ジャンル')]/following-sibling::td/a/text()")
    if not result:
        result = html.xpath(
            "//div[@class='info__item']/table/tbody/tr/th[contains(text(),'ジャンル')]/following-sibling::td/a/text()"
        )
    return str(result).strip(" ['']").replace("', '", ",")


async def get_cover(html):
    temp_result = html.xpath('//meta[@property="og:image"]/@content')
    if temp_result:
        result = re.sub(r"pics.dmm.co.jp", r"awsimgsrc.dmm.co.jp/pics_dig", temp_result[0])
        if await check_url(result):
            return result.replace("ps.jpg", "pl.jpg")
        else:
            return temp_result[0].replace("ps.jpg", "pl.jpg")
    else:
        return ""


def get_poster(html, cover):
    return cover.replace("pl.jpg", "ps.jpg")


def get_extrafanart(html):
    result_list = html.xpath("//div[@id='sample-image-block']/a/@href")
    if not result_list:
        result_list = html.xpath("//a[@name='sample-image']/img/@data-lazy")
    i = 1
    result = []
    for each in result_list:
        each = each.replace(f"-{i}.jpg", f"jp-{i}.jpg")
        result.append(each)
        i += 1
    return result


def get_director(html):
    result = html.xpath("//td[contains(text(),'監督')]/following-sibling::td/a/text()")
    if not result:
        result = html.xpath("//th[contains(text(),'監督')]/following-sibling::td/a/text()")
    return result[0] if result else ""


def get_ountline(html):
    result = html.xpath(
        "normalize-space(string(//div[@class='wp-smplex']/preceding-sibling::div[contains(@class, 'mg-b20')][1]))"
    )
    return result.replace("「コンビニ受取」対象商品です。詳しくはこちらをご覧ください。", "").strip()


def get_score(html):
    result = html.xpath("//p[contains(@class,'d-review__average')]/strong/text()")
    return result[0].replace("\\n", "").replace("\n", "").replace("点", "") if result else ""


async def get_trailer(htmlcode, real_url):
    trailer_url = ""
    normal_cid = re.findall(r"onclick=\"sampleplay\('.+cid=([^/]+)/", htmlcode)
    vr_cid = re.findall(r"https://www.dmm.co.jp/digital/-/vr-sample-player/=/cid=([^/]+)", htmlcode)
    if normal_cid:
        cid = normal_cid[0]
        if "dmm.co.jp" in real_url:
            url = f"https://www.dmm.co.jp/service/digitalapi/-/html5_player/=/cid={cid}/mtype=AhRVShI_/service=digital/floor=videoa/mode=/"
        else:
            url = f"https://www.dmm.com/service/digitalapi/-/html5_player/=/cid={cid}/mtype=AhRVShI_/service=digital/floor=videoa/mode=/"

        htmlcode, error = await manager.computed.async_client.get_text(url)
        if htmlcode is None:
            return ""
        try:
            var_params = re.findall(r" = ({[^;]+)", htmlcode)[0].replace(r"\/", "/")
            trailer_url = json.loads(var_params).get("bitrates")[-1].get("src")
            if trailer_url.startswith("//"):
                trailer_url = "https:" + trailer_url
        except Exception:
            trailer_url = ""
    elif vr_cid:
        cid = vr_cid[0]
        temp_url = f"https://cc3001.dmm.co.jp/vrsample/{cid[:1]}/{cid[:3]}/{cid}/{cid}vrlite.mp4"
        trailer_url = await check_url(temp_url)
    return trailer_url


def get_real_url(
    html,
    number,
    number2,
    file_path,
):
    number_temp = number2.lower().replace("-", "")
    url_list = re.findall(r'detailUrl.*?(https.*?)\\",', html, re.S)
    # url_list = html.xpath("//p[@class='tmb']/a/@href")
    # https://tv.dmm.co.jp/list/?content=mide00726&i3_ref=search&i3_ord=1
    # https://www.dmm.co.jp/digital/videoa/-/detail/=/cid=mide00726/?i3_ref=search&i3_ord=2
    # https://www.dmm.com/mono/dvd/-/detail/=/cid=n_709mmrak089sp/?i3_ref=search&i3_ord=1
    # /cid=snis00900/
    # /cid=snis126/ /cid=snis900/ 图上面没有蓝光水印
    # /cid=h_346rebdb00017/
    # /cid=6snis027/ /cid=7snis900/

    number1 = number_temp.replace("000", "")
    number_pre = re.compile(f"(?<=[=0-9]){number_temp[:3]}")
    number_end = re.compile(f"{number_temp[-3:]}(?=(-[0-9])|([a-z]*)?[/&])")
    number_mid = re.compile(f"[^a-z]{number1}[^0-9]")
    temp_list = []
    for each in url_list:
        if (number_pre.search(each) and number_end.search(each)) or number_mid.search(each):
            cid_list = re.findall(r"(cid|content)=([^/&]+)", each)
            if cid_list:
                temp_list.append(each)
                cid = cid_list[0][1]
                if "-" in cid and cid[-2:] in file_path:  # 134cwx001-1
                    number = cid
    if not temp_list:  # 通过标题搜索
        # title_list = html.xpath("//p[@class='txt']/a//text()")
        title_list = re.findall(r'title\\":\\"(.*?)\\",', html, re.S)
        if title_list and url_list:
            full_title = number
            for i in range(len(url_list)):
                temp_title = title_list[i].replace("...", "").strip()
                if temp_title in full_title:
                    temp_url = url_list[i]
                    temp_list.append(temp_url)
                    cid = re.findall(r"(cid|content)=.*?([a-z]{3,})0*(\d{3,}[a-z]*)", temp_url)
                    if cid:
                        number = (cid[0][1] + "-" + cid[0][2]).upper()

    # 网址排序：digital(数据完整)  >  dvd(无前缀数字，图片完整)   >   prime（有发行日期）   >   premium（无发行日期）  >  s1（无发行日期）
    tv_list = []
    digital_list = []
    dvd_list = []
    prime_list = []
    monthly_list = []
    other_list = []
    for i in temp_list:
        if "tv.dmm.co.jp" in i:
            tv_list.append(i)
        elif "/digital/" in i:
            digital_list.append(i)
        elif "/dvd/" in i:
            dvd_list.append(i)
        elif "/prime/" in i:
            prime_list.append(i)
        elif "/monthly/" in i:
            monthly_list.append(i)
        else:
            other_list.append(i)
    dvd_list.sort(reverse=True)
    # 丢弃 tv_list, 因为获取其信息调用的后续 api 无法访问
    # 20250810 digital 重定向到 video.dmm.co.jp 且难以获取
    new_url_list = dvd_list + prime_list + monthly_list + digital_list + other_list
    real_url = new_url_list[0] if new_url_list else ""
    return real_url, number


async def get_tv_jp_data(real_url):
    cid = re.findall(r"content=([^&/]+)", real_url)[0]
    response, error = await manager.computed.async_client.post_json(
        "https://api.tv.dmm.co.jp/graphql", json_data=fanza_tv_payload(cid)
    )
    if response is None:
        return False, "未找到数据", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
    resp = FanzaResp.model_validate(response)
    api_data = resp.data.fanzaTvPlus.content
    title = api_data.title
    outline = api_data.description
    release = api_data.startDeliveryAt  # 2025-05-17T20:00:00Z
    year = release[:4]
    actors = [actress.name for actress in api_data.actresses]
    actor = ",".join(actors)
    poster_url = api_data.packageImage
    cover_url = api_data.packageLargeImage
    tags = [genre.name for genre in api_data.genres]
    tag = ",".join(tags)
    runtime = str(int(api_data.playInfo.duration / 60))
    score = str(api_data.reviewSummary.averagePoint)
    series = api_data.series.name
    directors = api_data.directors
    studio = api_data.maker.name
    publisher = api_data.label.name
    extrafanart = []
    for sample_pic in api_data.samplePictures:
        if sample_pic.imageLarge:
            extrafanart.append(sample_pic.imageLarge)

    # https://cc3001.dmm.co.jp/hlsvideo/freepv/s/ssi/ssis00497/playlist.m3u8
    trailer_url = api_data.sampleMovie.url.replace("hlsvideo", "litevideo")
    cid_match = re.search(r"/([^/]+)/playlist.m3u8", trailer_url)
    if cid_match:
        cid = cid_match.group(1)
        trailer = trailer_url.replace("playlist.m3u8", cid + "_sm_w.mp4")
    else:
        trailer = ""
    return (
        True,
        title,
        outline,
        actor,
        poster_url,
        cover_url,
        tag,
        runtime,
        score,
        series,
        directors,
        studio,
        publisher,
        extrafanart,
        trailer,
        year,
    )


async def get_tv_com_data(number):
    response, error = await manager.computed.async_client.post_json(
        "https://api.tv.dmm.com/graphql", json_data=dmm_tv_com_payload(number)
    )
    if response is None:
        return False, "未找到数据", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
    response = DmmTvResponse.model_validate(response)
    api_data = response.data.video
    title = api_data.titleName
    outline = api_data.description
    actors = [item.actorName for item in api_data.casts]
    actor = ",".join(actors)
    poster_url = api_data.packageImage
    cover_url = api_data.keyVisualImage
    tags = []
    for each in api_data.genres:
        tags.append(each.name)
    tag = ",".join(tags)
    # release = api_data.startPublicAt  # 2025-05-17T20:00:00Z
    year = str(api_data.productionYear)
    score = str(api_data.reviewSummary.averagePoint)
    directors = [item.staffName for item in api_data.staffs if item.roleName == "監督"]
    director = ",".join(directors)
    studio = [item.staffName for item in api_data.staffs if item.roleName in ["制作プロダクション", "制作", "制作著作"]]
    publisher = studio
    return (
        True,
        title,
        outline,
        actor,
        poster_url,
        cover_url,
        tag,
        "",
        score,
        "",
        director,
        studio,
        publisher,
        "",
        "",
        year,
    )


async def main(
    number,
    appoint_url="",
    file_path="",
    **kwargs,
):
    start_time = time.time()
    website_name = "dmm"
    LogBuffer.req().write(f"-> {website_name}")
    cookies = {"cookie": "uid=abcd786561031111; age_check_done=1;"}
    real_url = appoint_url
    title = ""
    cover_url = ""
    poster_url = ""
    mosaic = "有码"
    release = ""
    year = ""
    image_download = False
    image_cut = "right"
    dic = {}
    if x := re.findall(r"[A-Za-z]+-?(\d+)", number):
        digits = x[0]
        if len(digits) >= 5 and digits.startswith("00"):
            number = number.replace(digits, digits[2:])
        elif len(digits) == 4:
            number = number.replace("-", "0")  # DSVR-1698 -> dsvr01698 https://github.com/sqzw-x/mdcx/issues/393
    number_00 = number.lower().replace("-", "00")  # 搜索结果多，但snis-027没结果
    number_no_00 = number.lower().replace("-", "")  # 搜索结果少
    web_info = "\n       "
    LogBuffer.info().write(" \n    🌐 dmm")
    debug_info = ""

    if not appoint_url:
        real_url = f"https://www.dmm.co.jp/search/=/searchstr={number_00}/sort=ranking/"  # 带00
        debug_info = f"搜索地址: {real_url} "
        LogBuffer.info().write(web_info + debug_info)
    else:
        debug_info = f"番号地址: {real_url} "
        LogBuffer.info().write(web_info + debug_info)

    try:
        # tv.dmm未屏蔽非日本ip，此处请求页面，看是否可以访问
        if "tv.dmm." not in real_url:
            htmlcode, error = await manager.computed.async_client.get_text(real_url, cookies=cookies)
            if htmlcode is None:  # 请求失败
                debug_info = f"网络请求错误: {error} "
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

            if re.findall("foreignError", htmlcode):  # 非日本地区限制访问
                debug_info = "地域限制, 请使用日本节点访问！"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

            # html = etree.fromstring(htmlcode, etree.HTMLParser())

            # 未指定详情页地址时，获取详情页地址（刚才请求的是搜索页）
            if not appoint_url:
                real_url, number = get_real_url(htmlcode, number, number, file_path)
                if not real_url:
                    debug_info = "搜索结果: 未匹配到番号！"
                    LogBuffer.info().write(web_info + debug_info)
                    if number_no_00 != number_00:
                        real_url = f"https://www.dmm.co.jp/search/=/searchstr={number_no_00}/sort=ranking/"  # 不带00，旧作 snis-027
                        debug_info = f"再次搜索地址: {real_url} "
                        LogBuffer.info().write(web_info + debug_info)
                        htmlcode, error = await manager.computed.async_client.get_text(real_url, cookies=cookies)
                        if htmlcode is None:  # 请求失败
                            debug_info = f"网络请求错误: {error} "
                            LogBuffer.info().write(web_info + debug_info)
                            raise Exception(debug_info)
                        # html = etree.fromstring(htmlcode, etree.HTMLParser())
                        real_url, number = get_real_url(htmlcode, number, number_no_00, file_path)
                        if not real_url:
                            debug_info = "搜索结果: 未匹配到番号！"
                            LogBuffer.info().write(web_info + debug_info)

                # 写真
                if not real_url:
                    real_url = f"https://www.dmm.com/search/=/searchstr={number_no_00}/sort=ranking/"
                    debug_info = f"再次搜索地址: {real_url} "
                    LogBuffer.info().write(web_info + debug_info)
                    htmlcode, error = await manager.computed.async_client.get_text(real_url, cookies=cookies)
                    if htmlcode is None:  # 请求失败
                        debug_info = f"网络请求错误: {error} "
                        LogBuffer.info().write(web_info + debug_info)
                        raise Exception(debug_info)
                    # html = etree.fromstring(htmlcode, etree.HTMLParser())
                    real_url, number0 = get_real_url(htmlcode, number, number_no_00, file_path)
                    if not real_url:
                        debug_info = "搜索结果: 未匹配到番号！"
                        LogBuffer.info().write(web_info + debug_info)

                elif real_url.find("?i3_ref=search&i3_ord") != -1:  # 去除url中无用的后缀
                    real_url = real_url[: real_url.find("?i3_ref=search&i3_ord")]

                debug_info = f"番号地址: {real_url} "
                LogBuffer.info().write(web_info + debug_info)

        # 获取详情页信息
        if not real_url or "tv.dmm.com" in real_url:
            if not real_url:
                if number_00.lower().startswith("lcvr"):
                    number_00 = "5125" + number_00
                elif number_no_00.lower().startswith("ionxt"):
                    number_00 = "5125" + number_no_00
                elif number_00.lower().startswith("ymd"):
                    number_00 = "5394" + number_00
                elif number_00.lower().startswith("fakwm"):
                    number_00 = "5497" + number_00
                elif number_00.lower().startswith("ftbd"):
                    number_00 = "5533" + number_00
                elif (
                    number_00.lower().startswith("ugm")
                    or number_00.lower().startswith("dmi")
                    or number_00.lower().startswith("whm")
                ):
                    number_00 = "5083" + number_00
                    number_00 = "5083" + number_00
                real_url = f"https://tv.dmm.com/vod/detail/?season={number_00}"
                debug_info = f"再次搜索地址: {real_url} "
            else:
                debug_info = f"番号地址: {real_url} "
                number_00 = re.findall(r"season=([^&]+)", real_url)[0] if "season=" in real_url else number_00
            LogBuffer.info().write(web_info + debug_info)
            (
                result,
                title,
                outline,
                actor,
                poster_url,
                cover_url,
                tag,
                runtime,
                score,
                series,
                director,
                studio,
                publisher,
                extrafanart,
                trailer,
                year,
            ) = await get_tv_com_data(number_00)
            if not result:
                debug_info = f"数据获取失败: {title} "
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
        elif "tv.dmm.co.jp" in real_url:
            (
                result,
                title,
                outline,
                actor,
                poster_url,
                cover_url,
                tag,
                runtime,
                score,
                series,
                director,
                studio,
                publisher,
                extrafanart,
                trailer,
                year,
            ) = await get_tv_jp_data(real_url)
            if not result:
                debug_info = f"数据获取失败: {title} "
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
        else:
            htmlcode, error = await manager.computed.async_client.get_text(real_url, cookies=cookies)
            if htmlcode is None:
                debug_info = f"网络请求错误: {error} "
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            html = etree.fromstring(htmlcode, etree.HTMLParser())

            # 分析详情页
            if "404 Not Found" in str(
                html.xpath("//span[@class='d-txten']/text()")
            ):  # 如果页面有404，表示传入的页面地址不对
                debug_info = "404! 页面地址错误！"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

            title = get_title(html).strip()  # 获取标题
            if not title:
                debug_info = "数据获取失败: 未获取到title！"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            try:
                actor = get_actor(html)  # 获取演员
                cover_url = await get_cover(html)  # 获取 cover
                outline = get_ountline(html)
                tag = get_tag(html)
                release = get_release(html)
                year = get_year(release)
                runtime = get_runtime(html)
                score = get_score(html)
                series = get_series(html)
                director = get_director(html)
                studio = get_studio(html)
                publisher = get_publisher(html, studio)
                extrafanart = get_extrafanart(html)
                poster_url = get_poster(html, cover_url)
                trailer = await get_trailer(htmlcode, real_url)
                mosaic = get_mosaic(html)
            except Exception as e:
                # print(traceback.format_exc())
                debug_info = f"出错: {str(e)}"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
        actor_photo = get_actor_photo(actor)
        if "VR" in title:
            image_download = True
        try:
            dic = {
                "number": number,
                "title": title,
                "originaltitle": title,
                "actor": actor,
                "outline": outline,
                "originalplot": outline,
                "tag": tag,
                "release": release,
                "year": year,
                "runtime": runtime,
                "score": score,
                "series": series,
                "director": director,
                "studio": studio,
                "publisher": publisher,
                "source": "dmm",
                "website": real_url,
                "actor_photo": actor_photo,
                "thumb": cover_url,
                "poster": poster_url,
                "extrafanart": extrafanart,
                "trailer": trailer,
                "image_download": image_download,
                "image_cut": image_cut,
                "mosaic": mosaic,
                "wanted": "",
            }
            debug_info = "数据获取成功！"
            LogBuffer.info().write(web_info + debug_info)

        except Exception as e:
            debug_info = f"数据生成出错: {str(e)}"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)

    except Exception as e:
        # print(traceback.format_exc())
        LogBuffer.error().write(str(e))
        dic = {
            "title": "",
            "thumb": "",
            "website": "",
        }
    dic = {website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic}}
    LogBuffer.req().write(f"({round(time.time() - start_time)}s) ")
    return dic


if __name__ == "__main__":
    # yapf: disable
    # print(main('ipz-825'))    # 普通，有预告片
    # print(main('SIVR-160'))     # vr，有预告片
    # print(main('enfd-5301'))  # 写真，有预告片
    # print(main('h_346rebdb00017'))  # 无预告片
    # print(main('', 'https://www.dmm.com/mono/dvd/-/detail/=/cid=n_641enfd5301/'))
    # print(main('', 'https://www.dmm.co.jp/rental/ppr/-/detail/=/cid=4ssis243/?i3_ref=search&i3_ord=1'))
    # print(main('NKD-229'))
    # print(main('rebdb-017'))         # 测试搜索，无视频
    # print(main('STARS-199'))    # poster图片
    # print(main('ssis301'))  # 普通预告片
    # print(main('hnvr00015'))
    # print(main('QNBM-094'))
    # print(main('ssis-243'))
    # print(main('1459525'))
    # print(main('ssni888'))    # detail-sample-movie 1个
    # print(main('snis-027'))
    # print(main('gs00002'))
    # print(main('SMBD-05'))
    # print(main('cwx-001', file_path='134cwx001-1.mp4'))
    # print(main('ssis-222'))
    # print(main('snis-036'))
    # print(main('GLOD-148'))
    # print(main('（抱き枕カバー付き）自宅警備員 1stミッション イイナリ巨乳長女・さやか～編'))    # 番号最后有字母
    # print(main('エロコンビニ店長 泣きべそ蓮っ葉・栞〜お仕置きじぇらしぃナマ逸機〜'))
    # print(main('初めてのヒトヅマ 第4話 ビッチな女子の恋愛相談'))
    # print(main('ACMDP-1035'))
    # print(main('JUL-066'))
    # print(main('mide-726'))
    # print(main('1dandy520'))
    # print(main('ome-210'))
    # print(main('ftbd-042'))
    # print(main('mmrak-089'))
    # print(main('', 'https://tv.dmm.co.jp/list/?content=juny00018'))
    # print(main('snis-900'))
    # print(main('n1581'))
    # print(main('ssni-888'))
    # print(main('ssni00888'))
    # print(main('ssni-288'))
    # print(main('mbf-033'))
    # print(main('', 'https://www.dmm.co.jp/digital/videoa/-/detail/=/cid=ssni00288/'))
    # print(main('俺をイジメてた地元ヤンキーの巨乳彼女を寝とって復讐を果たす話 The Motion Anime'))  # 模糊匹配 MAXVR-008
    # print(main('', 'https://www.dmm.co.jp/mono/dvd/-/detail/=/cid=h_173dhry23/'))   # 地域限制
    # print(main('ssni00288'))
    # print(main('ssni00999'))
    # print(main('ipx-292'))
    # print(main('wicp-002')) # 无视频
    # print(main('ssis-080'))
    # print(main('DV-1562'))
    # print(main('mide00139', "https://www.dmm.co.jp/digital/videoa/-/detail/=/cid=mide00139"))
    # print(main('mide00139', ""))
    # print(main('kawd00969'))
    # print(main('', 'https://tv.dmm.com/vod/detail/?title=5533ftbd00042&season=5533ftbd00042'))
    # print(main('stars-779'))
    # print(main('FAKWM-001', 'https://tv.dmm.com/vod/detail/?season=5497fakwm00001'))
    print(main('FAKWM-064', 'https://tv.dmm.com/vod/detail/?season=5497fakwm00064'))
