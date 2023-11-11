#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

from models.config.config import config
from models.crawlers import airav


def main(number, appoint_url='', log_info='', req_web='', language='zh_cn'):
    all_language = config.title_language + config.outline_language + config.actor_language + \
                   config.tag_language + config.series_language + config.studio_language
    if 'cn.airav.wiki' in appoint_url:
        appoint_url = appoint_url.replace('cn.airav.wiki', 'jp.airav.wiki')
    elif 'www.airav.wiki' in appoint_url:
        appoint_url = appoint_url.replace('www.airav.wiki', 'jp.airav.wiki')
    elif 'jp.airav.wiki' in appoint_url:
        appoint_url = appoint_url
    json_data = json.loads(airav.main(number, appoint_url, log_info, req_web, 'jp'))
    if not json_data['airav']['jp']['title']:
        json_data['airav']['zh_cn'] = json_data['airav']['jp']
        json_data['airav']['zh_tw'] = json_data['airav']['jp']
        return json.dumps(
            json_data,
            ensure_ascii=False,
            sort_keys=False,
            indent=4,
            separators=(',', ': '),
        )

    log_info = json_data['airav']['jp']['log_info']
    req_web = json_data['airav']['jp']['req_web']

    if 'zh_cn' in all_language:
        language = 'zh_cn'
        appoint_url = json_data['airav']['jp']['website'].replace('jp.airav.wiki', 'cn.airav.wiki')

    elif 'zh_tw' in all_language:
        language = 'zh_tw'
        appoint_url = json_data['airav']['jp']['website'].replace('jp.airav.wiki', 'www.airav.wiki')

    json_data_zh = json.loads(airav.main(number, appoint_url, log_info, req_web, language))
    dic = json_data_zh['airav'][language]
    dic['originaltitle'] = json_data['airav']['jp']['originaltitle']
    dic['originalplot'] = json_data['airav']['jp']['originalplot']
    json_data['airav'].update({'zh_cn': dic, 'zh_tw': dic})

    js = json.dumps(
        json_data,
        ensure_ascii=False,
        sort_keys=False,
        indent=4,
        separators=(',', ': '),
    )  # .encode('UTF-8')
    return js


if __name__ == '__main__':
    # print(main('', 'https://cn.airav.wiki/video/DOCP-324'))
    # print(main('ALDN-107'))
    # print(main('APNS-259', language='zh_cn'))
    print(main('ISRD-006'))
    # print(main('abs-141'))
    # print(main('HYSD-00083'))
    # print(main('IESP-660'))
    # print(main('n1403'))
    # print(main('GANA-1910'))
    # print(main('heyzo-1031'))
    # print(main_us('x-art.19.11.03'))
    # print(main('032020-001'))
    # print(main('S2M-055'))
    # print(main('LUXU-1217'))
    # print(main('1101132', ''))
    # print(main('OFJE-318'))
    # print(main('110119-001'))
    # print(main('abs-001'))
    # print(main('SSIS-090', ''))
    # print(main('SSIS-090', ''))
    # print(main('SNIS-016', ''))
    # print(main('HYSD-00083', ''))
    # print(main('IESP-660', ''))
    # print(main('n1403', ''))
    # print(main('GANA-1910', ''))
    # print(main('heyzo-1031', ''))
    # print(main_us('x-art.19.11.03'))
    # print(main('032020-001', ''))
    # print(main('S2M-055', ''))
    # print(main('LUXU-1217', ''))
    # print(main_us('x-art.19.11.03', ''))
