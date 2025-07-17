#!/usr/bin/env python3
from mdcx.crawlers import iqqtv


async def main(
    number,
    appoint_url="",
    language="zh_cn",
    **kwargs,
):
    appoint_url = appoint_url.replace("/cn/", "/jp/").replace("iqqtv.cloud/player", "iqqtv.cloud/jp/player")
    json_data = await iqqtv.main(number, appoint_url, "jp")
    if not json_data["iqqtv"]["jp"]["title"] or language == "jp":
        json_data["iqqtv"]["zh_cn"] = json_data["iqqtv"]["jp"]
        json_data["iqqtv"]["zh_tw"] = json_data["iqqtv"]["jp"]
        return json_data

    if language == "zh_cn":
        appoint_url = json_data["iqqtv"]["jp"]["website"].replace("/jp/", "/cn/")
    elif language == "zh_tw":
        appoint_url = json_data["iqqtv"]["jp"]["website"].replace("/jp/", "/")

    json_data_zh = await iqqtv.main(number, appoint_url, language)
    dic = json_data_zh["iqqtv"][language]
    dic["originaltitle"] = json_data["iqqtv"]["jp"]["originaltitle"]
    dic["originalplot"] = json_data["iqqtv"]["jp"]["originalplot"]
    json_data["iqqtv"].update({language: dic})

    return json_data


if __name__ == "__main__":
    print(main("abs-141"))
    # print(main('HYSD-00083'))
    # print(main('IESP-660'))
    # print(main('n1403'))  # print(main('GANA-1910'))  # print(main('heyzo-1031'))  # print(main_us('x-art.19.11.03'))  # print(main('032020-001'))  # print(main('S2M-055'))  # print(main('LUXU-1217'))

    # print(main('1101132', ''))  # print(main('OFJE-318'))  # print(main('110119-001'))  # print(main('abs-001'))  # print(main('SSIS-090', ''))  # print(main('SSIS-090', ''))  # print(main('SNIS-016', ''))  # print(main('HYSD-00083', ''))  # print(main('IESP-660', ''))  # print(main('n1403', ''))  # print(main('GANA-1910', ''))  # print(main('heyzo-1031', ''))  # print(main_us('x-art.19.11.03'))  # print(main('032020-001', ''))  # print(main('S2M-055', ''))  # print(main('LUXU-1217', ''))  # print(main_us('x-art.19.11.03', ''))
