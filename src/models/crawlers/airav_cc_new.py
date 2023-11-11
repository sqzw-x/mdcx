#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

from models.config.config import config
from models.crawlers import airav_cc


def main(number, appoint_url='', log_info='', req_web='', language='zh_cn'):
    all_language = config.title_language + config.outline_language + config.actor_language + \
                   config.tag_language + config.series_language + config.studio_language
    if 'airav.cc/cn/' in appoint_url:
        appoint_url = appoint_url.replace('airav.cc/cn/', 'airav.cc/jp/')
    elif 'airav.cc/playon.aspx' in appoint_url:
        appoint_url = appoint_url.replace('airav.cc/playon.aspx', 'airav.cc/jp/playon.aspx')
    json_data = json.loads(airav_cc.main(number, appoint_url, log_info, req_web, 'jp'))
    if not json_data['airav_cc']['jp']['title']:
        json_data['airav_cc']['zh_cn'] = json_data['airav_cc']['jp']
        json_data['airav_cc']['zh_tw'] = json_data['airav_cc']['jp']
        return json.dumps(
            json_data,
            ensure_ascii=False,
            sort_keys=False,
            indent=4,
            separators=(',', ': '),
        )

    log_info = json_data['airav_cc']['jp']['log_info']
    req_web = json_data['airav_cc']['jp']['req_web']

    if 'zh_cn' in all_language:
        language = 'zh_cn'
        appoint_url = json_data['airav_cc']['jp']['website'].replace('airav.cc/jp/', 'airav.cc/cn/')
    elif 'zh_tw' in all_language:
        language = 'zh_tw'
        appoint_url = json_data['airav_cc']['jp']['website'].replace('airav.cc/jp/', 'airav.cc/')

    json_data_zh = json.loads(airav_cc.main(number, appoint_url, log_info, req_web, language))
    dic = json_data_zh['airav_cc'][language]
    dic['originaltitle'] = json_data['airav_cc']['jp']['originaltitle']
    dic['originalplot'] = json_data['airav_cc']['jp']['originalplot']
    json_data['airav_cc'].update({'zh_cn': dic, 'zh_tw': dic})

    js = json.dumps(
        json_data,
        ensure_ascii=False,
        sort_keys=False,
        indent=4,
        separators=(',', ': '),
    )  # .encode('UTF-8')
    return js


if __name__ == '__main__':
    print(main('', 'https://airav.cc/playon.aspx?hid=99-21-46640'))
    # print(main('ISRD-006'))
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
