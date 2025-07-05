#!/usr/bin/env python3

import json
import re
import time  # yapf: disable # NOQA: E402

import urllib3
from lxml import etree
from lxml.html import soupparser

from models.base.web import curl_html, get_dmm_trailer
from models.core.json_data import LogBuffer

urllib3.disable_warnings()  # yapf: disable


# import traceback
# import Function.config as cf


def get_title(html):
    try:
        # 2025-07-05 number和title之间有竖线可能是以前的格式？目前看是没有的，一般是`ABC-123 xxx | FREE JAV BT` 这种格式
        raw = html.xpath("//title/text()")[0]
        raw = raw.replace("| FREE JAV BT", "")
        result = raw.split("|")
        if len(result) == 2:
            number = result[0].strip()
            title = " ".join(result[1:]).replace(number, "").strip()
        else:
            result = raw.split(" ")
            if len(result) > 2:
                number = result[0].strip()
                title = " ".join(result[1:]).strip()

        title = (
            title.replace("中文字幕", "")
            .replace("無碼", "")
            .replace("\\n", "")
            .replace("_", "-")
            .replace(number.upper(), "")
            .replace(number, "")
            .replace("--", "-")
            .strip()
        )
        if not title or "翻译错误" in title or "每日更新" in str(result):
            return "", ""
        return title, number
    except Exception:
        return "", ""


def get_actor(html):
    actor_result = html.xpath('//a[@class="actress"]/text()')
    av_man = [
        "貞松大輔",
        "鮫島",
        "森林原人",
        "黒田悠斗",
        "主観",
        "吉村卓",
        "野島誠",
        "小田切ジュン",
        "しみけん",
        "セツネヒデユキ",
        "大島丈",
        "玉木玲",
        "ウルフ田中",
        "ジャイアント廣田",
        "イセドン内村",
        "西島雄介",
        "平田司",
        "杉浦ボッ樹",
        "大沢真司",
        "ピエール剣",
        "羽田",
        "田淵正浩",
        "タツ",
        "南佳也",
        "吉野篤史",
        "今井勇太",
        "マッスル澤野",
        "井口",
        "松山伸也",
        "花岡じった",
        "佐川銀次",
        "およよ中野",
        "小沢とおる",
        "橋本誠吾",
        "阿部智広",
        "沢井亮",
        "武田大樹",
        "市川哲也",
        "???",
        "浅野あたる",
        "梅田吉雄",
        "阿川陽志",
        "素人",
        "結城結弦",
        "畑中哲也",
        "堀尾",
        "上田昌宏",
        "えりぐち",
        "市川潤",
        "沢木和也",
        "トニー大木",
        "横山大輔",
        "一条真斗",
        "真田京",
        "イタリアン高橋",
        "中田一平",
        "完全主観",
        "イェーイ高島",
        "山田万次郎",
        "澤地真人",
        "杉山",
        "ゴロー",
        "細田あつし",
        "藍井優太",
        "奥村友真",
        "ザーメン二郎",
        "桜井ちんたろう",
        "冴山トシキ",
        "久保田裕也",
        "戸川夏也",
        "北こうじ",
        "柏木純吉",
        "ゆうき",
        "トルティーヤ鈴木",
        "神けんたろう",
        "堀内ハジメ",
        "ナルシス小林",
        "アーミー",
        "池田径",
        "吉村文孝",
        "優生",
        "久道実",
        "一馬",
        "辻隼人",
        "片山邦生",
        "Qべぇ",
        "志良玉弾吾",
        "今岡爽紫郎",
        "工藤健太",
        "原口",
        "アベ",
        "染島貢",
        "岩下たろう",
        "小野晃",
        "たむらあゆむ",
        "川越将護",
        "桜木駿",
        "瀧口",
        "TJ本田",
        "園田",
        "宮崎",
        "鈴木一徹",
        "黒人",
        "カルロス",
        "天河",
        "ぷーてゃん",
        "左曲かおる",
        "富田",
        "TECH",
        "ムールかいせ",
        "健太",
        "山田裕二",
        "池沼ミキオ",
        "ウサミ",
        "押井敬之",
        "浅見草太",
        "ムータン",
        "フランクフルト林",
        "石橋豊彦",
        "矢野慎二",
        "芦田陽",
        "くりぼ",
        "ダイ",
        "ハッピー池田",
        "山形健",
        "忍野雅一",
        "渋谷優太",
        "服部義",
        "たこにゃん",
        "北山シロ",
        "つよぽん",
        "山本いくお",
        "学万次郎",
        "平井シンジ",
        "望月",
        "ゆーきゅん",
        "頭田光",
        "向理来",
        "かめじろう",
        "高橋しんと",
        "栗原良",
        "テツ神山",
        "タラオ",
        "真琴",
        "滝本",
        "金田たかお",
        "平ボンド",
        "春風ドギー",
        "桐島達也",
        "中堀健二",
        "徳田重男",
        "三浦屋助六",
        "志戸哲也",
        "ヒロシ",
        "オクレ",
        "羽目白武",
        "ジョニー岡本",
        "幸野賀一",
        "インフィニティ",
        "ジャック天野",
        "覆面",
        "安大吉",
        "井上亮太",
        "笹木良一",
        "艦長",
        "軍曹",
        "タッキー",
        "阿部ノボル",
        "ダウ兄",
        "まーくん",
        "梁井一",
        "カンパニー松尾",
        "大塚玉堂",
        "日比野達郎",
        "小梅",
        "ダイナマイト幸男",
        "タケル",
        "くるみ太郎",
        "山田伸夫",
        "氷崎健人",
    ]
    actor_list = [i.strip() for i in actor_result if i.replace("?", "")]
    all_actor_list = actor_list.copy()
    for each in all_actor_list:
        if each in av_man:
            actor_list.remove(each)
    actor = ",".join(actor_list)
    all_actor = ",".join(all_actor_list)
    actor = actor if "暫無" not in actor else ""
    all_actor = all_actor if "暫無" not in all_actor else ""
    return actor, all_actor


def get_actor_photo(actor):
    actor = actor.split(",")
    data = {}
    for i in actor:
        actor_photo = {i: ""}
        data.update(actor_photo)
    return data


def get_runtime(html):
    result = html.xpath(
        '//span[contains(text(), "时长") or contains(text(), "時長") or contains(text(), "収録時間")]/following-sibling::*//text()'
    )
    if result:
        result = re.findall(r"\d+", result[0])
    return result[0] if result else ""


def get_series(html):
    result = html.xpath('//span[contains(text(), "系列")]/following-sibling::*//text()')
    return "".join(result).strip() if result else ""


def get_director(html):
    result = html.xpath(
        '//span[contains(text(), "导演") or contains(text(), "導演") or contains(text(), "監督")]/following-sibling::*//text()'
    )
    return result[0] if result else ""


def get_studio(html):
    result = html.xpath(
        '//span[contains(text(), "制作") or contains(text(), "製作") or contains(text(), "メーカー")]/following-sibling::*//text()'
    )
    return result[0] if result else ""


def get_publisher(html):
    result = html.xpath('//span[contains(text(), "发行") or contains(text(), "發行")]/following-sibling::*//text()')
    return result[0] if result else ""


def get_release(html):
    result = html.xpath('//span[contains(text(), "日期") or contains(text(), "発売日")]/following-sibling::*//text()')
    return result[0] if result else ""


def get_year(release):
    result = re.findall(r"\d{4}", release)
    return result[0] if result else ""


def get_tag(html):
    result = html.xpath('//a[@class="genre"]//text()')
    tag = ""
    for each in result:
        tag += each.strip().replace("，", "") + ","
    return tag.strip(",")


def get_cover(html):
    try:
        result = html.xpath(
            "//img[@class='video-cover rounded lazyload' or @class='col-lg-2 col-md-2 col-sm-6 col-12 lazyload']/@data-src"
        )[0]
        if "no_preview_lg" in result or "http" not in result:
            return ""
    except Exception:
        result = ""
    return result


def get_extrafanart(html):  # 获取封面链接
    extrafanart_list = html.xpath("//a[@class='tile-item']/@href")
    if "#preview-video" in str(extrafanart_list):
        extrafanart_list.pop(0)
    return extrafanart_list


def get_trailer(html):  # 获取预览片
    trailer_url_list = html.xpath("//video[@id='preview-video']/source/@src")
    return get_dmm_trailer(trailer_url_list[0]) if trailer_url_list else ""


def get_mosaic(title, actor):
    title += actor
    if "無碼" in title or "無修正" in title or "Uncensored" in title:
        mosaic = "无码"
    else:
        mosaic = ""
    return mosaic


def main(
    number,
    appoint_url="",
    language="jp",
):
    # https://freejavbt.com/VRKM-565
    start_time = time.time()
    website_name = "freejavbt"
    LogBuffer.req().write(f"-> {website_name}")
    real_url = appoint_url
    title = ""
    cover_url = ""
    poster_url = ""
    image_download = False
    image_cut = "right"
    web_info = "\n       "
    debug_info = ""
    real_url = f"https://freejavbt.com/{number}"
    LogBuffer.info().write("\n    🌐 freejavbt")
    if appoint_url:
        real_url = appoint_url.replace("/zh/", "/").replace("/en/", "/").replace("/ja/", "/")

    try:  # 捕获主动抛出的异常
        debug_info = f"番号地址: {real_url} "
        LogBuffer.info().write(web_info + debug_info)

        result, html_info = curl_html(real_url)
        if not result:
            debug_info = f"请求错误: {html_info}"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)

        # 判断返回内容是否有问题
        if not html_info:
            debug_info = "未匹配到番号！"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)

        html_detail = etree.fromstring(html_info, etree.HTMLParser())
        
        
        # docker版本正常，但在macOS会解析失败，猜测是emoji等特殊字符导致的，删除emoji后可解析正常。
        # 搜索emoji正则: [\u{1F601}-\u{1F64F}\u{2702}-\u{27B0}\u{1F680}-\u{1F6C0}\u{1F170}-\u{1F251}\u{1F600}-\u{1F636}\u{1F681}-\u{1F6C5}\u{1F30D}-\u{1F567}]
        # 另外，使用`lxml.html.soupparser.fromstring`可以解析成功。
        if html_detail is None:
            debug_info = "HTML 解析失败，etree 返回 None"
            LogBuffer.error().write(web_info + debug_info)
            # 尝试soupparser
            html_detail = soupparser.fromstring(html_info)
            if html_detail is None:
                debug_info = "HTML 解析失败，soupparser 返回 None"
                LogBuffer.error().write(web_info + debug_info)
                raise Exception(debug_info)

        # ========================================================================收集信息
        title, number = get_title(html_detail)  # 获取标题并去掉头尾歌手名
        if not title or "single-video-info col-12" not in html_info:
            debug_info = "数据获取失败: 番号标题不存在！"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)
        actor, all_actor = get_actor(html_detail)  # 获取actor
        actor_photo = get_actor_photo(actor)
        all_actor_photo = get_actor_photo(all_actor)
        cover_url = get_cover(html_detail)  # 获取cover

        # poster_url = cover_url.replace('/covers/', '/thumbs/')
        outline = ""
        tag = get_tag(html_detail)
        release = get_release(html_detail)
        year = get_year(release)
        runtime = get_runtime(html_detail)
        score = ""
        series = get_series(html_detail)
        director = get_director(html_detail)
        studio = get_studio(html_detail)
        publisher = get_publisher(html_detail)
        extrafanart = get_extrafanart(html_detail)
        trailer = get_trailer(html_detail)
        website = real_url
        mosaic = get_mosaic(title, actor)
        try:
            dic = {
                "number": number,
                "title": title,
                "originaltitle": title,
                "actor": actor,
                "all_actor": all_actor,
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
                "source": "freejavbt",
                "actor_photo": actor_photo,
                "all_actor_photo": all_actor_photo,
                "cover": cover_url,
                "poster": poster_url,
                "extrafanart": extrafanart,
                "trailer": trailer,
                "image_download": image_download,
                "image_cut": image_cut,
                "mosaic": mosaic,
                "website": website,
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
            "cover": "",
            "website": "",
        }
    dic = {website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic}}
    js = json.dumps(
        dic,
        ensure_ascii=False,
        sort_keys=False,
        indent=4,
        separators=(",", ": "),
    )  # .encode('UTF-8')
    LogBuffer.req().write(f"({round((time.time() - start_time))}s) ")
    return js


if __name__ == "__main__":
    # yapf: disable
    # print(main('080815_130'))   # trailer url is http, not https
    # print(main('', 'https://javdb.com/v/dWmGB'))
    # print(main('ssis-118'))
    # print(main('DANDY-520', ''))    # 预告片默认低品质dm，改成高品质dmb
    # print(main('PPPD-653'))
    print(main('SSNI-531'))  # print(main('ssis-330')) # 预告片  # print(main('n1403'))  # print(main('SKYHD-014'))       # 无预览图  # print(main('FC2-424646'))     # 无番号  # print(main('CWPBD-168'))  # print(main('BadMilfs.22.04.02'))  # print(main('vixen.19.12.10'))  # print(main('CEMD-133'))  # print(main('FC2-880652')) # 无番号  # print(main('PLA-018'))  # print(main('SIVR-060'))  # print(main('STCV-067'))  # print(main('ALDN-107'))  # print(main('DSVR-1205'))    # 无标题  # print(main('SIVR-100'))  # print(main('FC2-2787433'))  # print(main('MIDV-018'))  # print(main('MIDV-018', appoint_url='https://javdb.com/v/BnMY9'))  # print(main('SVSS-003'))  # print(main('SIVR-008'))  # print(main('blacked.21.07.03'))  # print(main('FC2-1262472'))  # 需要登录  # print(main('HUNTB-107'))  # 预告片返回url错误，只有https  # print(main('FC2-2392657'))                                                  # 需要登录  # print(main('GS-067'))                                                       # 两个同名番号  # print(main('MIDE-022'))  # print(main('KRAY-001'))  # print(main('ssis-243'))  # print(main('MIDE-900', 'https://javdb.com/v/MZp24?locale=en'))  # print(main('TD-011'))  # print(main('stars-011'))    # 发行商SOD star，下载封面  # print(main('stars-198'))  # 发行商SOD star，下载封面  # print(main('mium-748'))  # print(main('KMHRS-050'))    # 剧照第一张作为poster  # print(main('SIRO-4042'))  # print(main('snis-035'))  # print(main('vixen.18.07.18', ''))  # print(main('vixen.16.08.02', ''))  # print(main('SNIS-016', ''))  # print(main('bangbros18.19.09.17'))  # print(main('x-art.19.11.03'))  # print(main('abs-141'))  # print(main('HYSD-00083'))  # print(main('IESP-660'))  # print(main('GANA-1910'))  # print(main('heyzo-1031'))  # print(main('032020-001'))  # print(main('S2M-055'))  # print(main('LUXU-1217'))  # print(main('SSIS-001', ''))  # print(main('SSIS-090', ''))  # print(main('HYSD-00083', ''))  # print(main('IESP-660', ''))  # print(main('n1403', ''))  # print(main('GANA-1910', ''))  # print(main('heyzo-1031', ''))  # print(main_us('x-art.19.11.03'))  # print(main('032020-001', ''))  # print(main('S2M-055', ''))  # print(main('LUXU-1217', ''))  # print(main_us('x-art.19.11.03', ''))
