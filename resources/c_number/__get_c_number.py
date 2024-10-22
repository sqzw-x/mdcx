import json
import os
import random
import re
import time

import requests
from lxml import etree

'''
请使用国外节点！！！国内节点有 cloudFlare 盾！！！
'''

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
    'cookie': 'cPNj_2132_saltkey=GoOo4lK1; _safe=ywf36pjm4p5uo9q839yzk6b7jdt6oizh',
}


def save_log(error_info):
    with open('_错误信息.txt', 'a', encoding='utf-8') as f:
        f.write(error_info)


def remove_char(ch):
    char_list = [
        '【独家自译】',
        '【自提征用】',
        '【自译征用】',
        '【自提字幕】',
        '[自提征用]',
        '[自译征用]',
        '导演剪辑最终版',
        '(完整字幕版)',
        '[完整字幕]',
        '（正常字体版）',
        '[高清中文字幕]',
        '[高清中文字幕',
        '高清中文字幕]',
        '【高清中文字幕】',
        '无码流出版',
        '无码流出',
        '无码破解版',
        '无码破解',
        'TOKYO-HOT-',
        '韩文转译版',
        '独家听译版',
        '完整版',
        '特别版',
        '完全版',
        '时间轴修复版',
        '堂友',
        '()',
        '自提征用】',
        '[独家自译]',
        '[会员专享]',
        '[无码]',
        '（完整字幕版）',
        '【独家自提】',
        '【听译征用】',
        '【FANZA独占】',
        '【配信専用】',
        '[ ]',
        '[字幕]',
        '[] ',
        '[]',
    ]
    for each in char_list:
        ch = ch.replace(each, '')
    ch = ch.replace('FC2PPV', 'FC2').replace('  ', ' ').strip().strip('-')
    return ch


def get_c_number():
    i = 1
    json_filename = 'c_number.json'
    if not os.path.exists(json_filename):
        with open(json_filename, 'w', encoding='utf-8') as f:
            f.write('{}')
    with open(json_filename, 'r', encoding='utf-8') as data:
        json_data = {}
        json_data1 = json.load(data)
        for key, value in json_data1.items():
            if re.search(r'\d{4}-\d{2}-\d{2}', key):
                print(key)
                continue
            if not re.search(r'\d', key):
                continue
            if '-' not in key and '_' not in key and not re.search(r'^N\d{4,}', key):
                print(key)
            if '.' in key:
                print(key)
                continue
            value = remove_char(value)
            if '.' not in key and len(value) > 10:
                json_data[key] = value
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(
            json_data,
            f,
            ensure_ascii=False,
            sort_keys=True,
            indent=4,
            separators=(',', ': '),
        )

    while i:
        url = (f'https://www.sehuatang.org/forum-103-{i}.html')
        # 获取当前页面信息
        try:
            res = requests.get(url, headers=headers)
        except:
            print('获取当前页面信息失败！信息已保存到：_错误信息.txt')
            # print(res.text)
            error_info = '\nPA 获取当前页面信息失败！\n' + url + '\n'
            i -= 1
        else:
            # 将html转成 Element对象，以便使用xpath定位
            html = etree.HTML(res.text.replace('encoding="utf-8"', ''))
            if i == 1:
                page_total = html.xpath('//a[@class="last"]/text()')[0][-3:]
                print('当前共 {} 页数据！'.format(page_total))
            print('\n' + '**' * 20)
            print(f'开始下载第 {i} 页数据...\n页面地址：{url}')
            # 获取当前页面帖子列表
            try:
                post_info = html.xpath('//tbody[contains(@id, "normal")]/tr/th/a[2]')
            except:
                print('获取当前页面帖子列表失败！信息已保存到：_错误信息.txt')
                error_info = '\nL 获取当前页面帖子列表失败！\n' + url + '\n'
                save_log(error_info)
            else:
                post_number = len(post_info)
                print(f'帖子数量：{post_number}')
                j = 0
                for each in post_info:
                    j += 1
                    post_title = each.text
                    # url_adress = each.attrib['href']
                    # 2021-06-01 發行日期: 2021-05-27 [大陆简化字][完美主义控][6000码率纯净版] NUKA-046 鶴川牧子
                    if 'KBPS' in post_title:
                        a = post_title[post_title.find('KBPS'):]
                        b = a[a.find(']') + 1:].strip()
                        number = b[:b.find(' ')]
                        title = b[b.find(' ') + 1:]
                    elif '6000' in post_title:
                        a = post_title[post_title.find('6000'):]
                        b = a[a.find(']') + 1:].strip()
                        number = b[:b.find(' ')]
                        title = b[b.find(' ') + 1:]
                    elif '3000' in post_title:
                        post_title1 = post_title.replace('[经典老片]', '')
                        a = post_title1[post_title1.find('3000'):]
                        b = a[a.find(']') + 1:].strip()
                        number = b[:b.find(' ')]
                        title = b[b.find(' ') + 1:]
                    elif '5500' in post_title:
                        post_title1 = post_title.replace('[经典老片]', '')
                        a = post_title1[post_title1.find('5500'):]
                        b = a[a.find(']') + 1:].strip()
                        number = b[:b.find(' ')]
                        title = b[b.find(' ') + 1:]
                    # missax.17.03.13.lana.rhoades.please.help.me-请帮帮我
                    elif re.search(r'\.\d{2}\.\d{2}\.\d{2}', post_title):
                        number = post_title[:post_title.find('-')]
                        title = post_title[post_title.find('-') + 1:]
                    # JUL-618 【第一次！】madonna初登场！【
                    elif re.findall(r'^[A-Za-z0-9-_ ]+', post_title):
                        number = re.findall(r'^[A-Za-z0-9-]+', post_title)[0]
                        title = post_title.replace(number, '').strip()
                    else:
                        number = post_title[:post_title.find(' ')]
                        title = post_title[post_title.find(' ') + 1:]
                    number = number.upper().replace(' - ', '').replace(' -', '').replace('- ', '').strip().strip('-')
                    if not re.search(r'\d', number):
                        continue
                    if '.' in number:
                        continue
                    title = remove_char(title)
                    if len(title) < 11:
                        continue
                    json_data[number] = title
                    print(j)
                    print(post_title)
                    print(number + ' : ' + title)
            print(f'\n当前第 {i} 页数据...\n页面地址：{url}')
            print('**' * 20)
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(
                    json_data,
                    f,
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=4,
                    separators=(',', ': '),
                )
            if i < int(page_total):
                i += 1
            else:
                i = 0
            time.sleep(random.randint(1, 3))


if __name__ == "__main__":
    print('.......')
    try:
        os.remove('_错误信息.txt')
    except:
        pass
    get_c_number()
    print('\n\n# ===== 处理完成！ ===== #\n')
