#!/usr/bin/env python3
import re
import time
import traceback

from mdcx.config.manager import manager
from mdcx.models.log_buffer import LogBuffer


def get_actor(page_data):
    actor_new_list = []
    for each in page_data["actress"]:
        actor_new_list.append(each["name"].replace(" ", ""))
    return ",".join(actor_new_list)


def get_actor_photo(actor):
    actor = actor.split(",")
    data = {}
    for i in actor:
        actor_photo = {i: ""}
        data.update(actor_photo)
    return data


def get_extrafanart(page_data):
    result = []
    for each in page_data["media"]:
        result.append("https://www.prestige-av.com/api/media/" + each["path"])
    return result


def get_year(release):
    try:
        result = str(re.search(r"\d{4}", release).group())
        return result
    except Exception:
        return release


def get_tag(page_data):
    new_list = []
    for each in page_data["genre"]:
        new_list.append(each["name"])
    return ",".join(new_list)


def get_real_url(html_search, number):
    result = html_search["hits"]["hits"]
    for each in result:
        productUuid = each["_source"]["productUuid"]
        deliveryItemId = each["_source"]["deliveryItemId"]
        if deliveryItemId.endswith(number.upper()):
            return "https://www.prestige-av.com/api/product/" + productUuid
    return ""


async def main(
    number,
    appoint_url="",
    **kwargs,
):
    start_time = time.time()
    website_name = "prestige"
    LogBuffer.req().write(f"-> {website_name}")
    real_url = appoint_url.replace("goods", "api/product")
    image_cut = "right"
    image_download = True
    search_url = ""
    mosaic = ""
    web_info = "\n       "
    LogBuffer.info().write(" \n    🌐 prestige")
    debug_info = ""
    poster = ""

    # search_url = https://www.prestige-av.com/api/search?isEnabledQuery=true&searchText=abw-130&isEnableAggregation=false&release=false&reservation=false&soldOut=false&from=0&aggregationTermsSize=0&size=20
    # real_url = https://www.prestige-av.com/api/product/2e4a2de8-7275-4803-bb07-7585fd4f2ff3

    try:  # 捕获主动抛出的异常
        if not real_url:
            # 通过搜索获取real_url
            search_url = f"https://www.prestige-av.com/api/search?isEnabledQuery=true&searchText={number}&isEnableAggregation=false&release=false&reservation=false&soldOut=false&from=0&aggregationTermsSize=0&size=20"
            debug_info = f"搜索地址: {search_url} "
            LogBuffer.info().write(web_info + debug_info)

            # ========================================================================搜索番号
            html_search, error = await manager.config_v1.async_client.get_json(search_url)
            if html_search is None:
                debug_info = f"网络请求错误: {error} "
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

            real_url = get_real_url(html_search, number)
            if not real_url:
                debug_info = "搜索结果: 未匹配到番号！"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

        if real_url:
            # 'https://www.prestige-av.com/goods/2e4a2de8-7275-4803-bb07-7585fd4f2ff3'
            # 'https://www.prestige-av.com/api/product/2e4a2de8-7275-4803-bb07-7585fd4f2ff3'
            debug_info = f"番号地址: {real_url.replace('api/product', 'goods')} "
            LogBuffer.info().write(web_info + debug_info)
            page_data, error = await manager.config_v1.async_client.get_json(real_url)
            if page_data is None:
                debug_info = f"网络请求错误: {error} "
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

            title = page_data["title"].replace("【配信専用】", "")
            if not title:
                debug_info = "数据获取失败: 未获取到 title！"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            outline = page_data["body"]
            actor = get_actor(page_data)
            actor_photo = get_actor_photo(actor)
            # https://www.prestige-av.com/api/media/goods/prestige/abw/130/pf_abw-130.jpg
            try:
                poster = "https://www.prestige-av.com/api/media/" + page_data["thumbnail"]["path"]
                if "noimage" in poster:
                    poster = ""
            except Exception:
                poster = ""
            try:
                cover_url = "https://www.prestige-av.com/api/media/" + page_data["packageImage"]["path"]
            except Exception:
                cover_url = ""
            try:
                release = page_data["sku"][0]["salesStartAt"][:10]
            except Exception:
                release = ""
            year = get_year(release)
            runtime = str(page_data["playTime"])
            score = ""
            try:
                series = page_data["series"]["name"]
            except Exception:
                series = ""
            tag = get_tag(page_data)
            try:
                director = page_data["directors"][0]["name"]
            except Exception:
                director = ""
            try:
                studio = page_data["maker"]["name"]
            except Exception:
                studio = ""
            try:
                publisher = page_data["label"]["name"]
            except Exception:
                publisher = ""
            extrafanart = get_extrafanart(page_data)
            try:
                trailer = "https://www.prestige-av.com/api/media/" + page_data["movie"]["path"]
            except Exception:
                trailer = ""
            mosaic = "有码"
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
                    "source": "prestige",
                    "actor_photo": actor_photo,
                    "thumb": cover_url,
                    "poster": poster,
                    "extrafanart": extrafanart,
                    "trailer": trailer,
                    "image_download": image_download,
                    "image_cut": image_cut,
                    "mosaic": mosaic,
                    "website": real_url.replace("api/product", "goods"),
                    "wanted": "",
                }
                debug_info = "数据获取成功！"
                LogBuffer.info().write(web_info + debug_info)

            except Exception as e:
                debug_info = f"数据生成出错: {str(e)}"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
    except Exception as e:
        print(traceback.format_exc())
        LogBuffer.error().write(str(e))
        dic = {
            "title": "",
            "thumb": "",
            "website": "",
        }
    dic = {
        "official": {"zh_cn": dic, "zh_tw": dic, "jp": dic},
        website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic},
    }
    LogBuffer.req().write(f"({round(time.time() - start_time)}s) ")
    return dic


if __name__ == "__main__":
    # yapf: disable
    # print(main('abw-130'))
    print(main('FCP-150'))  # print(main('fakwm-064', appoint_url='https://www.prestige-av.com/goods/dcb86b74-195b-46c4-8ced-71f5f3ce5c3c?skuId=ABW-344'))  # 有导演  # print(main('ABW-343'))  # 无图
