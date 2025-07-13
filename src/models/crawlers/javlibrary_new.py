#!/usr/bin/env python3


from models.config.manager import config
from models.crawlers import javlibrary


async def main(
    number,
    appoint_url="",
    language="zh_cn",
    **kwargs,
):
    all_language = (
        config.title_language
        + config.outline_language
        + config.actor_language
        + config.tag_language
        + config.series_language
        + config.studio_language
    )
    appoint_url = appoint_url.replace("/cn/", "/ja/").replace("/tw/", "/ja/")
    json_data = await javlibrary.main(number, appoint_url, "jp")
    if not json_data["javlibrary"]["jp"]["title"]:
        json_data["javlibrary"]["zh_cn"] = json_data["javlibrary"]["jp"]
        json_data["javlibrary"]["zh_tw"] = json_data["javlibrary"]["jp"]
        return json_data

    if "zh_cn" in all_language:
        language = "zh_cn"
        appoint_url = json_data["javlibrary"]["jp"]["website"].replace("/ja/", "/cn/")
    elif "zh_tw" in all_language:
        language = "zh_tw"
        appoint_url = json_data["javlibrary"]["jp"]["website"].replace("/ja/", "/tw/")

    json_data_zh = await javlibrary.main(number, appoint_url, language)
    dic = json_data_zh["javlibrary"][language]
    dic["originaltitle"] = json_data["javlibrary"]["jp"]["originaltitle"]
    dic["originalplot"] = json_data["javlibrary"]["jp"]["originalplot"]
    json_data["javlibrary"].update({language: dic})
    return json_data


if __name__ == "__main__":
    # print(main('SSIS-118', 'https://www.javlibrary.com/cn/?v=javme5ly4e'))
    print(
        main("abs-141")
    )  # print(main('HYSD-00083'))  # print(main('IESP-660'))  # print(main('n1403'))  # print(main('GANA-1910'))  # print(main('heyzo-1031'))  # print(main_us('x-art.19.11.03'))  # print(main('032020-001'))  # print(main('S2M-055'))  # print(main('LUXU-1217'))  # print(main('1101132', ''))  # print(main('OFJE-318'))  # print(main('110119-001'))  # print(main('abs-001'))  # print(main('SSIS-090', ''))  # print(main('SSIS-090', ''))  # print(main('SNIS-016', ''))  # print(main('HYSD-00083', ''))  # print(main('IESP-660', ''))  # print(main('n1403', ''))  # print(main('GANA-1910', ''))  # print(main('heyzo-1031', ''))  # print(main_us('x-art.19.11.03'))  # print(main('032020-001', ''))  # print(main('S2M-055', ''))  # print(main('LUXU-1217', ''))  # print(main_us('x-art.19.11.03', ''))
