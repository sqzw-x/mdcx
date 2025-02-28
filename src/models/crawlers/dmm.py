#!/usr/bin/python
import json
import re
import time  # yapf: disable # NOQA: E402

import urllib3
from lxml import etree

from models.base.web import check_url, get_dmm_trailer, get_html, post_html

urllib3.disable_warnings()  # yapf: disable


# import traceback


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
    result = html.xpath("//td/a[contains(@href, 'article=maker')]/text()")
    return result[0] if result else ""


def get_publisher(html, studio):
    result = html.xpath("//td/a[contains(@href, 'article=label')]/text()")
    return result[0] if result else studio


def get_runtime(html):
    result = html.xpath("//td[contains(text(),'収録時間')]/following-sibling::td/text()")
    if not result or not re.search(r"\d+", str(result[0])):
        result = html.xpath("//th[contains(text(),'収録時間')]/following-sibling::td/text()")
    if result and re.search(r"\d+", str(result[0])):
        return re.search(r"\d+", str(result[0])).group()
    return ""


def get_series(html):
    result = html.xpath("//td[contains(text(),'シリーズ')]/following-sibling::td/a/text()")
    if not result:
        result = html.xpath("//th[contains(text(),'シリーズ')]/following-sibling::td/a/text()")
    return result[0] if result else ""


def get_year(release):
    return re.search(r"\d{4}", str(release)).group() if release else ""


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


def get_cover(html):
    result = html.xpath('//a[@id="sample-image1"]/img/@src')
    if result:
        # 替换域名并返回第一个匹配项
        return re.sub(r'pics.dmm.co.jp', r'awsimgsrc.dmm.co.jp/pics_dig', result[0])
    return ''  # 无匹配时返回空字符串


def get_poster(html, cover):
    result = html.xpath('//img[@class="tdmm"]/@src')
    if result:
        result = re.sub(r"pics.dmm.co.jp", r"awsimgsrc.dmm.co.jp/pics_dig", result[0])
        return result
    else:
        return cover.replace("pt.jpg", "ps.jpg")


def get_extrafanart(html):
    result_list = html.xpath("//div[@id='sample-image-block']/a/img/@src")
    if not result_list:
        result_list = html.xpath("//a[@name='sample-image']/img/@src")
    i = 1
    result = []
    for each in result_list:
        each = each.replace("-%s.jpg" % i, "jp-%s.jpg" % i)
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


def get_trailer(htmlcode, real_url):
    trailer_url = ""
    normal_cid = re.findall(r"onclick=\"sampleplay\('.+cid=([^/]+)/", htmlcode)
    vr_cid = re.findall(r"https://www.dmm.co.jp/digital/-/vr-sample-player/=/cid=([^/]+)", htmlcode)
    if normal_cid:
        cid = normal_cid[0]
        if "dmm.co.jp" in real_url:
            url = (
                "https://www.dmm.co.jp/service/digitalapi/-/html5_player/=/cid=%s/mtype=AhRVShI_/service=digital/floor=videoa/mode=/"
                % cid
            )
        else:
            url = (
                "https://www.dmm.com/service/digitalapi/-/html5_player/=/cid=%s/mtype=AhRVShI_/service=digital/floor=videoa/mode=/"
                % cid
            )

        result, htmlcode = get_html(url)
        try:
            var_params = re.findall(r" = ({[^;]+)", htmlcode)[0].replace(r"\/", "/")
            trailer_url = json.loads(var_params).get("bitrates")[-1].get("src")
            if trailer_url.startswith("//"):
                trailer_url = "https:" + trailer_url
        except:
            trailer_url = ""
    elif vr_cid:
        cid = vr_cid[0]
        temp_url = "https://cc3001.dmm.co.jp/vrsample/{0}/{1}/{2}/{2}vrlite.mp4".format(cid[:1], cid[:3], cid)
        trailer_url = check_url(temp_url)
    return trailer_url


def get_real_url(html, number, number2, file_path):
    number_temp = number2.lower().replace("-", "")
    url_list = html.xpath("//p[@class='tmb']/a/@href")

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
                if "-" in cid:  # 134cwx001-1
                    if cid[-2:] in file_path:
                        number = cid
    if not temp_list:  # 通过标题搜索
        title_list = html.xpath("//p[@class='txt']/a//text()")
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
    new_url_list = digital_list + dvd_list + prime_list + monthly_list + other_list
    real_url = new_url_list[0] if new_url_list else ""
    return real_url, number


# invalid API
def get_tv_jp_data(real_url):
    cid = re.findall(r"content=([^&/]+)", real_url)[0]
    headers = {
        "Content-Type": "application/json",
        "content-length": "3174",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    }
    data = {
        "operationName": "GetFanzaTvContentDetail",
        "variables": {"id": cid, "device": "BROWSER", "playDevice": "BROWSER", "isLoggedIn": False},
        "query": "query GetFanzaTvContentDetail($id: ID!, $device: Device!, $isLoggedIn: Boolean!, $playDevice: PlayDevice!) {\n  fanzaTV(device: $device) {\n    content(id: $id) {\n      __typename\n      id\n      contentType\n      shopName\n      shopOption\n      shopType\n      title\n      description\n      packageImage\n      packageLargeImage\n      noIndex\n      ppvShopName\n      viewingRights(device: $playDevice) @include(if: $isLoggedIn) {\n        isStreamable\n        __typename\n      }\n      startDeliveryAt\n      endDeliveryAt\n      isBeingDelivered\n      hasBookmark @include(if: $isLoggedIn)\n      sampleMovie {\n        url\n        thumbnail\n        __typename\n      }\n      samplePictures {\n        image\n        imageLarge\n        __typename\n      }\n      actresses {\n        id\n        name\n        __typename\n      }\n      histrions {\n        id\n        name\n        __typename\n      }\n      directors {\n        id\n        name\n        __typename\n      }\n      series {\n        id\n        name\n        __typename\n      }\n      maker {\n        id\n        name\n        __typename\n      }\n      label {\n        id\n        name\n        __typename\n      }\n      genres {\n        id\n        name\n        __typename\n      }\n      playInfo(withResume: $isLoggedIn, device: $device) {\n        parts {\n          contentId\n          number\n          duration\n          resumePoint\n          __typename\n        }\n        resumePartNumber\n        highestQualityName\n        duration\n        __typename\n      }\n      reviewSummary {\n        averagePoint\n        reviewerCount\n        reviewCommentCount\n        __typename\n      }\n      reviews(first: 5) {\n        edges {\n          node {\n            id\n            reviewerName\n            reviewerId\n            title\n            point\n            hasSpoiler\n            comment\n            date\n            postEvaluationCount\n            helpfulVoteCount\n            isReviewerPurchased\n            __typename\n          }\n          __typename\n        }\n        pageInfo {\n          endCursor\n          hasNextPage\n          __typename\n        }\n        total\n        __typename\n      }\n      fanzaTvRecommendations: itemBasedRecommendations(\n        device: $device\n        shop: FANZA_TV\n        limit: 30\n      ) {\n        id\n        title\n        packageImage\n        averageReviewPoint\n        price\n        salePrice\n        __typename\n      }\n      fanzaPpvRecommendations: itemBasedRecommendations(\n        device: $device\n        shop: VIDEO\n        limit: 30\n      ) {\n        id\n        title\n        packageImage\n        averageReviewPoint\n        price\n        salePrice\n        __typename\n      }\n    }\n    userBasedRecommendations(place: DETAIL_PAGE, limit: 30) @include(if: $isLoggedIn) {\n      id\n      title\n      packageImage\n      averageReviewPoint\n      price\n      salePrice\n      __typename\n    }\n    __typename\n  }\n}\n",
    }

    result, response = post_html(
        "https://api.tv.dmm.co.jp/graphql", headers=headers, json=data, json_data=True, keep=False
    )
    if result and response.get("data"):
        api_data = response["data"]["fanzaTV"]["content"]
        title = api_data["title"]
        outline = api_data["description"]
        actor_list = []
        for each in api_data["actresses"]:
            actor_list.append(each["name"])
        actor = ",".join(actor_list)
        poster_url = api_data["packageImage"]
        cover_url = api_data["packageLargeImage"]
        tag_list = []
        for each in api_data["genres"]:
            tag_list.append(each["name"])
        tag = ",".join(tag_list)
        # release = api_data['title']
        # year = api_data['title']
        try:
            runtime = str(int(api_data["playInfo"]["duration"] / 60))
        except:
            runtime = ""
        try:
            score = api_data["reviewSummary"]["averagePoint"]
        except:
            score = ""
        try:
            series = api_data["series"]["name"]
        except:
            series = ""
        try:
            director = api_data["directors"][0]["name"]
        except:
            director = ""
        try:
            studio = api_data["maker"]["name"]
        except:
            studio = ""
        try:
            publisher = api_data["label"][0]["name"]
        except:
            publisher = ""
        extrafanart = []
        for each in api_data["samplePictures"]:
            if each["imageLarge"]:
                extrafanart.append(each["imageLarge"])
        try:
            trailer_url = api_data["sampleMovie"]["url"].replace("hlsvideo", "litevideo")
            cid = re.findall(r"([^/]+)/playlist.m3u8", trailer_url)[0]
            trailer = trailer_url.replace("playlist.m3u8", cid + "_sm_w.mp4")
            trailer = get_dmm_trailer(trailer)

        except:
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
            director,
            studio,
            publisher,
            extrafanart,
            trailer,
            "",
        )
    else:
        return False, "未找到数据", "", "", "", "", "", "", "", "", "", "", "", "", "", ""


def get_tv_com_data(number):
    headers = {
        "Content-Type": "application/json",
        "content-length": "10501",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    }
    data = {
        "operationName": "GetVideo",
        "variables": {
            "seasonId": number,
            "contentId": "",
            "device": "BROWSER",
            "playDevice": "BROWSER",
            "isLoggedIn": False,
            "isContentId": False,
        },
        "query": "query GetVideo($seasonId: ID!, $contentId: ID!, $device: Device!, $playDevice: PlayDevice!, $isLoggedIn: Boolean!, $isContentId: Boolean!) {\n  video(id: $seasonId) {\n    id\n    seasonType\n    hasBookmark @include(if: $isLoggedIn)\n    titleName\n    seasonName\n    highlight(format: HTML)\n    description(format: HTML)\n    notices(format: HTML)\n    packageImage\n    productionYear\n    isNewArrival\n    isPublic\n    isExclusive\n    isBeingDelivered\n    viewingTypes\n    campaign {\n      name\n      endAt\n      __typename\n    }\n    rating {\n      category\n      __typename\n    }\n    casts {\n      castName\n      actorName\n      person {\n        id\n        __typename\n      }\n      __typename\n    }\n    staffs {\n      roleName\n      staffName\n      person {\n        id\n        __typename\n      }\n      __typename\n    }\n    categories {\n      name\n      id\n      __typename\n    }\n    genres {\n      name\n      id\n      __typename\n    }\n    copyright\n    relatedItems(device: $device) {\n      videos {\n        seasonId\n        video {\n          id\n          titleName\n          packageImage\n          isNewArrival\n          isExclusive\n          __typename\n        }\n        __typename\n      }\n      books {\n        seriesId\n        title\n        thumbnail\n        url\n        __typename\n      }\n      mono {\n        banner\n        url\n        __typename\n      }\n      scratch {\n        banner\n        url\n        __typename\n      }\n      onlineCrane {\n        banner\n        url\n        __typename\n      }\n      __typename\n    }\n    ... on VideoSeason {\n      ...CommonVideoSeason\n      __typename\n    }\n    ... on VideoLegacySeason {\n      ...CommonVideoLegacySeason\n      __typename\n    }\n    ... on VideoStageSeason {\n      ...CommonVideoStageSeason\n      __typename\n    }\n    ... on VideoSpotLiveSeason {\n      ...CommonVideoSpotLiveSeason\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment CommonVideoSeason on VideoSeason {\n  __typename\n  metaDescription: description(format: PLAIN)\n  keyVisualImage\n  keyVisualWithoutLogoImage\n  reviewSummary {\n    averagePoint\n    reviewerCount\n    reviewCommentCount\n    __typename\n  }\n  relatedSeasons {\n    id\n    title\n    __typename\n  }\n  upcomingEpisode {\n    svodProduct {\n      startDeliveryAt\n      __typename\n    }\n    __typename\n  }\n  continueWatching @include(if: $isLoggedIn) {\n    resumePoint\n    contentId\n    content {\n      episodeImage\n      episodeTitle\n      episodeNumber\n      episodeNumberName\n      viewingRights(device: $playDevice) {\n        isStreamable\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  priceSummary {\n    lowestPrice\n    discountedLowestPrice\n    __typename\n  }\n  episode(id: $contentId) @include(if: $isContentId) {\n    id\n    episodeTitle\n    episodeImage\n    episodeNumber\n    episodeNumberName\n    episodeDetail\n    playInfo {\n      highestQuality\n      isSupportHDR\n      highestAudioChannelLayout\n      duration\n      audioRenditions\n      textRenditions\n      __typename\n    }\n    viewingRights(device: $playDevice) {\n      isDownloadable\n      isStreamable\n      __typename\n    }\n    ppvExpiration @include(if: $isLoggedIn) {\n      expirationType\n      viewingExpiration\n      viewingStartExpiration\n      startDeliveryAt\n      __typename\n    }\n    freeProduct {\n      contentId\n      __typename\n    }\n    ppvProducts {\n      ...VideoPPVProductTag\n      __typename\n    }\n    svodProduct {\n      startDeliveryAt\n      __typename\n    }\n    __typename\n  }\n  episodes(type: MAIN, first: 1) {\n    edges {\n      node {\n        id\n        sampleMovie\n        episodeTitle\n        episodeNumber\n        episodeNumberName\n        playInfo {\n          highestQuality\n          isSupportHDR\n          highestAudioChannelLayout\n          duration\n          audioRenditions\n          textRenditions\n          __typename\n        }\n        viewingRights(device: $playDevice) {\n          isDownloadable\n          isStreamable\n          downloadableFiles @include(if: $isLoggedIn) {\n            quality {\n              name\n              displayName\n              displayPriority\n              __typename\n            }\n            totalFileSize\n            parts {\n              partNumber\n              fileSize\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        ppvExpiration @include(if: $isLoggedIn) {\n          expirationType\n          viewingExpiration\n          viewingStartExpiration\n          startDeliveryAt\n          __typename\n        }\n        freeProduct {\n          contentId\n          __typename\n        }\n        ppvProducts {\n          ...VideoPPVProductTag\n          __typename\n        }\n        svodProduct {\n          startDeliveryAt\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    total\n    __typename\n  }\n  purchasedContents(first: 1) @include(if: $isLoggedIn) {\n    edges {\n      node {\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    __typename\n  }\n  specialEpisode: episodes(type: SPECIAL, first: 1) {\n    total\n    __typename\n  }\n  pvEpisode: episodes(type: PV, first: 1) {\n    edges {\n      node {\n        id\n        sampleMovie\n        playInfo {\n          duration\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    total\n    __typename\n  }\n}\n\nfragment VideoPPVProductTag on VideoPPVProduct {\n  id\n  isOnSale\n  isBeingDelivered\n  isPurchased @include(if: $isLoggedIn)\n  price {\n    price\n    salePrice\n    __typename\n  }\n  __typename\n}\n\nfragment CommonVideoLegacySeason on VideoLegacySeason {\n  __typename\n  metaDescription: description(format: PLAIN)\n  packageLargeImage\n  reviewSummary {\n    averagePoint\n    reviewerCount\n    reviewCommentCount\n    __typename\n  }\n  sampleMovie {\n    url\n    thumbnail\n    __typename\n  }\n  samplePictures {\n    image\n    imageLarge\n    __typename\n  }\n  sampleMovie {\n    url\n    thumbnail\n    __typename\n  }\n  reviewSummary {\n    averagePoint\n    __typename\n  }\n  priceSummary {\n    lowestPrice\n    discountedLowestPrice\n    __typename\n  }\n  continueWatching @include(if: $isLoggedIn) {\n    partNumber\n    resumePoint\n    contentId\n    content {\n      playInfo {\n        parts {\n          contentId\n          __typename\n        }\n        __typename\n      }\n      viewingRights(device: $playDevice) {\n        isStreamable\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  content {\n    id\n    contentType\n    viewingRights(device: $playDevice) {\n      isStreamable\n      isDownloadable\n      downloadableFiles @include(if: $isLoggedIn) {\n        quality {\n          name\n          displayName\n          displayPriority\n          __typename\n        }\n        totalFileSize\n        parts {\n          partNumber\n          fileSize\n          __typename\n        }\n        __typename\n      }\n      windowsURLSchemes: appURLSchemes(app: WINDOWS_VR) @include(if: $isLoggedIn) {\n        partNumber\n        url\n        __typename\n      }\n      iosURLSchemes: appURLSchemes(app: IOS_VR) @include(if: $isLoggedIn) {\n        partNumber\n        url\n        __typename\n      }\n      androidURLSchemes: appURLSchemes(app: ANDROID_VR) @include(if: $isLoggedIn) {\n        partNumber\n        url\n        __typename\n      }\n      __typename\n    }\n    playInfo {\n      duration\n      audioRenditions\n      textRenditions\n      highestQuality\n      isSupportHDR\n      highestAudioChannelLayout\n      parts {\n        contentId\n        number\n        __typename\n      }\n      __typename\n    }\n    ppvExpiration @include(if: $isLoggedIn) {\n      expirationType\n      viewingExpiration\n      viewingStartExpiration\n      startDeliveryAt\n      __typename\n    }\n    freeProduct {\n      contentId\n      __typename\n    }\n    ppvProducts {\n      ...VideoPPVProductTag\n      __typename\n    }\n    svodProduct {\n      startDeliveryAt\n      __typename\n    }\n    __typename\n  }\n  series {\n    id\n    name\n    __typename\n  }\n}\n\nfragment CommonVideoStageSeason on VideoStageSeason {\n  __typename\n  metaDescription: description(format: PLAIN)\n  keyVisualImage\n  keyVisualWithoutLogoImage\n  reviewSummary {\n    averagePoint\n    reviewerCount\n    reviewCommentCount\n    __typename\n  }\n  priceSummary {\n    lowestPrice\n    discountedLowestPrice\n    __typename\n  }\n  allPerformances {\n    performanceDate\n    contents {\n      id\n      episodeTitle\n      priority\n      startLivePerformanceAt\n      ppvProducts {\n        ...VideoPPVProductTag\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  purchasedContents(first: 1) @include(if: $isLoggedIn) {\n    edges {\n      node {\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    __typename\n  }\n}\n\nfragment CommonVideoSpotLiveSeason on VideoSpotLiveSeason {\n  __typename\n  metaDescription: description(format: PLAIN)\n  keyVisualImage\n  keyVisualWithoutLogoImage\n  episodes(type: MAIN, first: 1) {\n    edges {\n      node {\n        id\n        episodeTitle\n        episodeNumber\n        episodeNumberName\n        viewingRights(device: $playDevice) {\n          isStreamable\n          __typename\n        }\n        ppvExpiration @include(if: $isLoggedIn) {\n          expirationType\n          viewingExpiration\n          viewingStartExpiration\n          startDeliveryAt\n          __typename\n        }\n        freeProduct {\n          contentId\n          __typename\n        }\n        ppvProducts {\n          ...VideoPPVProductTag\n          __typename\n        }\n        svodProduct {\n          startDeliveryAt\n          __typename\n        }\n        playInfo {\n          audioRenditions\n          textRenditions\n          duration\n          highestQuality\n          isSupportHDR\n          highestAudioChannelLayout\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",
    }

    result, response = post_html(
        "https://api.tv.dmm.com/graphql", headers=headers, json=data, json_data=True, keep=False
    )
    if result and response.get("data"):
        api_data = response["data"]["video"]
        title = api_data["titleName"]
        outline = api_data["description"]
        actor_list = []
        for each in api_data["casts"]:
            actor_list.append(each["actorName"])
        actor = ",".join(actor_list)
        poster_url = api_data["packageImage"]
        cover_url = api_data["packageLargeImage"]
        tag_list = []
        for each in api_data["genres"]:
            tag_list.append(each["name"])
        tag = ",".join(tag_list)
        # release = api_data['title']
        year = str(api_data["productionYear"])
        try:
            runtime = str(int(api_data["playInfo"]["duration"] / 60))
        except:
            runtime = ""
        try:
            score = str(api_data["reviewSummary"]["averagePoint"])
        except:
            score = ""
        try:
            series = api_data["series"]["name"]
        except:
            series = ""
        try:
            director = api_data["directors"][0]["name"]
        except:
            director = ""
        try:
            studio = api_data["staffs"][0]["staffName"]
        except:
            studio = ""
        publisher = studio
        extrafanart = []
        for each in api_data["samplePictures"]:
            if each["imageLarge"]:
                extrafanart.append(each["imageLarge"])
        try:
            trailer_url = api_data["sampleMovie"]["url"].replace("hlsvideo", "litevideo")
            cid = re.findall(r"([^/]+)/playlist.m3u8", trailer_url)[0]
            trailer = trailer_url.replace("playlist.m3u8", cid + "_sm_w.mp4")
            trailer = get_dmm_trailer(trailer)

        except:
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
            director,
            studio,
            publisher,
            extrafanart,
            trailer,
            year,
        )
    else:
        return False, "未找到数据", "", "", "", "", "", "", "", "", "", "", "", "", "", ""


def main(number, appoint_url="", log_info="", req_web="", language="jp", file_path=""):
    start_time = time.time()
    website_name = "dmm"
    req_web += "-> %s" % website_name
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
    digital = re.findall(r"[A-Za-z]+-?(\d+)", number)
    if digital and len(digital[0]) >= 5 and digital[0].startswith("00"):
        number = number.replace(digital[0], digital[0][2:])
    number_00 = number.lower().replace("-", "00")  # 搜索结果多，但snis-027没结果
    number_no_00 = number.lower().replace("-", "")  # 搜索结果少
    web_info = "\n       "
    log_info += " \n    🌐 dmm"
    debug_info = ""

    if not appoint_url:
        real_url = "https://www.dmm.co.jp/search/=/searchstr=%s/sort=ranking/" % number_00  # 带00
        debug_info = "搜索地址: %s " % real_url
        log_info += web_info + debug_info
    else:
        debug_info = "番号地址: %s " % real_url
        log_info += web_info + debug_info

    try:
        # tv.dmm未屏蔽非日本ip，此处请求页面，看是否可以访问
        if "tv.dmm." not in real_url:
            result, htmlcode = get_html(real_url, cookies=cookies)
            if not result:  # 请求失败
                debug_info = "网络请求错误: %s " % htmlcode
                log_info += web_info + debug_info
                raise Exception(debug_info)

            if re.findall("foreignError", htmlcode):  # 非日本地区限制访问
                debug_info = "地域限制, 请使用日本节点访问！"
                log_info += web_info + debug_info
                raise Exception(debug_info)

            html = etree.fromstring(htmlcode, etree.HTMLParser())

            # 未指定详情页地址时，获取详情页地址（刚才请求的是搜索页）
            if not appoint_url:
                real_url, number = get_real_url(html, number, number, file_path)
                if not real_url:
                    debug_info = "搜索结果: 未匹配到番号！"
                    log_info += web_info + debug_info
                    if number_no_00 != number_00:
                        real_url = (
                            "https://www.dmm.co.jp/search/=/searchstr=%s/sort=ranking/" % number_no_00
                        )  # 不带00，旧作 snis-027
                        debug_info = "再次搜索地址: %s " % real_url
                        log_info += web_info + debug_info
                        result, htmlcode = get_html(real_url, cookies=cookies)
                        if not result:  # 请求失败
                            debug_info = "网络请求错误: %s " % htmlcode
                            log_info += web_info + debug_info
                            raise Exception(debug_info)
                        html = etree.fromstring(htmlcode, etree.HTMLParser())
                        real_url, number = get_real_url(html, number, number_no_00, file_path)
                        if not real_url:
                            debug_info = "搜索结果: 未匹配到番号！"
                            log_info += web_info + debug_info

                # 写真
                if not real_url:
                    real_url = "https://www.dmm.com/search/=/searchstr=%s/sort=ranking/" % number_no_00
                    debug_info = "再次搜索地址: %s " % real_url
                    log_info += web_info + debug_info
                    result, htmlcode = get_html(real_url, cookies=cookies)
                    if not result:  # 请求失败
                        debug_info = "网络请求错误: %s " % htmlcode
                        log_info += web_info + debug_info
                        raise Exception(debug_info)
                    html = etree.fromstring(htmlcode, etree.HTMLParser())
                    real_url, number0 = get_real_url(html, number, number_no_00, file_path)
                    if not real_url:
                        debug_info = "搜索结果: 未匹配到番号！"
                        log_info += web_info + debug_info

                elif real_url.find("?i3_ref=search&i3_ord") != -1:  # 去除url中无用的后缀
                    real_url = real_url[: real_url.find("?i3_ref=search&i3_ord")]

                debug_info = "番号地址: %s " % real_url
                log_info += web_info + debug_info

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
                debug_info = "再次搜索地址: %s " % real_url
            else:
                debug_info = "番号地址: %s " % real_url
                number_00 = re.findall(r"season=([^&]+)", real_url)[0] if "season=" in real_url else number_00
            log_info += web_info + debug_info
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
            ) = get_tv_com_data(number_00)
            if not result:
                debug_info = "数据获取失败: %s " % title
                log_info += web_info + debug_info
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
            ) = get_tv_jp_data(real_url)
            if not result:
                debug_info = "数据获取失败: %s " % title
                log_info += web_info + debug_info
                raise Exception(debug_info)
        else:
            result, htmlcode = get_html(real_url, cookies=cookies)
            html = etree.fromstring(htmlcode, etree.HTMLParser())
            if not result:
                debug_info = "网络请求错误: %s " % htmlcode
                log_info += web_info + debug_info
                raise Exception(debug_info)

            # 分析详情页
            if "404 Not Found" in str(
                html.xpath("//span[@class='d-txten']/text()")
            ):  # 如果页面有404，表示传入的页面地址不对
                debug_info = "404! 页面地址错误！"
                log_info += web_info + debug_info
                raise Exception(debug_info)

            title = get_title(html).strip()  # 获取标题
            if not title:
                debug_info = "数据获取失败: 未获取到title！"
                log_info += web_info + debug_info
                raise Exception(debug_info)
            try:
                actor = get_actor(html)  # 获取演员
                cover_url = get_cover(html)  # 获取 cover
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
                trailer = get_trailer(htmlcode, real_url)
                mosaic = get_mosaic(html)
            except Exception as e:
                # print(traceback.format_exc())
                debug_info = "出错: %s" % str(e)
                log_info += web_info + debug_info
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
                "cover": cover_url,
                "poster": poster_url,
                "extrafanart": extrafanart,
                "trailer": trailer,
                "image_download": image_download,
                "image_cut": image_cut,
                "log_info": log_info,
                "error_info": "",
                "req_web": req_web
                + "(%ss) "
                % (
                    round(
                        (time.time() - start_time),
                    )
                ),
                "mosaic": mosaic,
                "wanted": "",
            }
            debug_info = "数据获取成功！"
            log_info += web_info + debug_info
            dic["log_info"] = log_info
        except Exception as e:
            debug_info = "数据生成出错: %s" % str(e)
            log_info += web_info + debug_info
            raise Exception(debug_info)

    except Exception as e:
        # print(traceback.format_exc())
        debug_info = str(e)
        dic = {
            "title": "",
            "cover": "",
            "website": "",
            "log_info": log_info,
            "error_info": debug_info,
            "req_web": req_web
            + "(%ss) "
            % (
                round(
                    (time.time() - start_time),
                )
            ),
        }
    dic = {website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic}}
    js = json.dumps(dic, ensure_ascii=False, sort_keys=False, indent=4, separators=(",", ": "))  # .encode('UTF-8')
    return js


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
    # print(main('GLOD-148'
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
    # print(main('FAKWM-064', 'https://tv.dmm.com/vod/detail/?season=5497fakwm00064'))
    pass
