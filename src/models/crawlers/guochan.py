#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import re

import urllib3
import zhconv

urllib3.disable_warnings()  # yapf: disable


# import traceback
# import Function.config as cf


def get_lable_list():
    return ['传媒', '国产短视频', '国产精品', '国产AV', 'PsychoPorn色控', '叮叮映画', '涩会', '蜜桃影像传媒',
            '大番号番啪啪', 'REAL野性派', '豚豚创媒', '宫美娱乐', '肉肉传媒', '爱妃传媒', '天美传媒', '皇家华人',
            '91制片厂', '果冻传媒', 'O-STAR', '兔子先生', '杏吧原创', '杏吧独家', '辣椒原创', '麻豆传媒', '糖心',
            '麻豆传媒映画', '红斯灯影像', '绝对领域', '麻麻传媒', '渡边传媒', 'AV帝王', '桃花源', '蝌蚪传媒', 'SWAG',
            '麻豆', '杏吧']


def get_actor_list():
    return [
        '苏妲己',
        '苏畅',
        '宁洋子',
        '沈芯语',
        '艾秋',
        '吴梦梦',
        '尹媚',
        '张芸熙',
        '夏晴子',
        '白佳萱',
        '林思妤',
        '沈娜娜',
        '仙儿媛',
        '许安妮',
        '刘语珊',
        '刘思慧',
        '叶一涵',
        '林亦涵',
        '雪千夏',
        '欧美玲',
        '赵佳美',
        '李慕儿',
        '徐韵珊',
        '苏娅',
        '糖果屋',
        '王茜',
        '李婧琪',
        '夏滢',
        '顾伊梦',
        '杜冰若',
        '赵颖儿',
        '秦可欣',
        '莫安安',
        '安娜',
        '黎星若',
        '仙儿',
        '林予曦',
        '蒋佑怡',
        '许书曼',
        '白晶晶',
        '王有容',
        '琳希',
        '李恩琦',
        '赵美凤',
        '王欣',
        '徐筱欣',
        '黄雅曼',
        '伊靖瑶',
        '菲于娜',
        '罗瑾萱',
        '金丞熙',
        '李文雯',
        '苏清歌',
        '付妙菱',
        '钟丽琪',
        '张娅庭',
        '蜜苏',
        '凌薇',
        '叶凡舒',
        '董小宛',
        '程雨沫',
        '瑶贝',
        '郭瑶瑶',
        '李嘉欣',
        '辰悦',
        '李曼妮',
        '洛雪',
        '千鹤',
        '袁庭妮',
        '林思好',
        '张云熙',
        '杜鹃',
        '玛丽莲',
        '李茹',
        '何苗',
        '黄雪纯',
        '田恬',
        '李琼',
        '聂小倩',
        '张晴',
        '丁香',
        '林凤娇',
        '刘颖儿',
        '杨思敏',
        '李忆彤',
        '伊蒂丝',
        '绿帽先生',
        '戚小怜',
        '杨柳',
        '唐茜',
        '苏艾文',
        '张曼青',
        '斑斑',
        '孟若羽',
        '陈圆圆',
        '雷梦娜',
        '氖氖',
        '仙儿',
        '艾玛',
        '蔚曼',
        '静静',
        '艾瑞卡',
        '娜米',
        '莉娜',
        '乔安',
        '林子涵',
        '萱萱',
        '糖糖',
        '徐婕',
        '王欣',
        '白颖',
        '吴芮瑜',
        '韩棠',
        '季妍希',
        '沙耶香',
        '七七',
        '莉娜乔安',
        '美雪樱',
        '柚木结爱',
        '黑田奈奈',
        '王亦舒',
        '张雅婷',
        '李文静',
        '肖泳',
        '韩小雅',
        '神山奈奈',
        '白川麻衣',
        '茜茜',
        '夜夜',
        '高梨遥香',
        'HongKongDoll',
        '玩偶姐姐',
        '蘇妲己',
        '蘇暢',
        '寧洋子',
        '沈芯語',
        '吳夢夢',
        '張芸熙',
        '仙兒媛',
        '許安妮',
        '劉語珊',
        '劉思慧',
        '葉一涵',
        '歐美玲',
        '趙佳美',
        '李慕兒',
        '徐韻珊',
        '蘇婭',
        '夏瀅',
        '顧伊夢',
        '趙穎兒',
        '仙兒',
        '蔣佑怡',
        '許書曼',
        '趙美鳳',
        '黃雅曼',
        '伊靖瑤',
        '羅瑾萱',
        '蘇清歌',
        '鍾麗琪',
        '張婭庭',
        '蜜蘇',
        '葉凡舒',
        '瑤貝',
        '郭瑤瑤',
        '辰悅',
        '千鶴',
        '張雲熙',
        '杜鵑',
        '瑪麗蓮',
        '黃雪純',
        '李瓊',
        '聶小倩',
        '張晴',
        '林鳳嬌',
        '劉穎兒',
        '楊思敏',
        '李憶彤',
        '伊蒂絲',
        '綠帽先生',
        '戚小憐',
        '楊柳',
        '蘇艾文',
        '張曼青',
        '陳圓圓',
        '雷夢娜',
        '仙兒',
        '艾瑪',
        '靜靜',
        '喬安',
        '白穎',
        '吳芮瑜',
        '韓棠',
        '莉娜喬安',
        '美雪櫻',
        '柚木結愛',
        '張雅婷',
        '李文靜',
        '韓小雅',
        '高梨遙香',
    ]


def get_number_list(number, appoint_number='', file_path=''):  # 处理国产番号
    file_name = os.path.splitext(os.path.split(file_path)[1])[0].upper() if file_path else ''
    number = number.upper()
    number_list = []  # 返回一个番号列表，用来搜索
    filename_list = []
    file_path_list = []
    result = []

    # 指定番号时，优先使用指定番号
    if appoint_number:
        number_list.append(appoint_number)
        file_name = appoint_number.upper()
        file_path_list.append(appoint_number)

    # 获取文件名，有文件名时，优先使用文件名来生成number，并转换为简体
    # 优先从文件名查找番号，找不到时，尝试从路径中查找
    else:
        file_name_1 = zhconv.convert(file_name, 'zh-cn') if file_name else zhconv.convert(number, 'zh-cn')
        file_name_1 = re.sub(r'-[^0-9]+?$', '', file_name_1)
        file_name_2 = os.path.splitext(os.path.split(file_path)[1])[0].upper() if file_path else ''
        file_name_2 = zhconv.convert(file_name_2, 'zh-cn') if file_name_2 else zhconv.convert(number, 'zh-cn')
        file_name_2 = re.sub(r'-[^0-9]+?$', '', file_name_2)
        file_path_list.extend([file_name_2, file_name_1])

    # 识别番号
    for file_name in file_path_list:

        # 91CM-081.田恬.李琼.继母与女儿.三.爸爸不在家先上妹妹再玩弄母亲.果冻传媒
        # 91MS-015.张淑仪.19岁D奶少女.被男友甩后下海.疯狂滥交高潮喷水.91制片厂
        if re.search(r'(91[A-Z]{2,})-?(\d{3,})', file_name):
            result = re.search(r'(91[A-Z]{2,})-?(\d{3,})', file_name)
            if result:
                number_normal = '%s-%s' % (result[1], result[2])
                number_has_nothing = '%s%s' % (result[1], result[2])
                number_has_space = '%s %s' % (result[1], result[2])
                number_list.extend([number_normal, number_has_nothing, number_has_space])

        # MDX-0236-02.沈娜娜.青梅竹马淫乱3P.麻豆传媒映画x逼哩逼哩blibli
        # MD-0140-2.蜜苏.家有性事EP2.爱在身边.麻豆传媒映画
        elif re.search(r'([A-Z]{2,})-?(\d{3,})-(\d+)', file_name):
            result = re.search(r'([A-Z]{2,})-?(\d{3,})-(\d+)', file_name)
            if result:
                number_normal = '%s-%s-%s' % (result[1], result[2], result[3])
                number_list.append(number_normal)

        # MXJ-0005.EP1.弥生美月.小恶魔高校生.与老师共度的放浪补课.麻豆传媒映画
        # MDJ0001 EP2  AV 淫兽鬼父 陈美惠  .TS
        # PMS-003.职场冰与火.EP3设局.宁静.苏文文.设局我要女人都臣服在我胯下.蜜桃影像传媒
        # 淫欲游戏王.EP6.情欲射龙门.性爱篇.郭童童.李娜.双英战龙根3P混战.麻豆传媒映画.ts
        # PMS-001 性爱公寓EP04 仨人.蜜桃影像传媒
        elif 'EP' in file_name:
            result = re.search(r'([A-Z]{2,})-?(\d{3,})(.*)(EP[\d]+)', file_name)
            if result:
                number_normal = '%s-%s.%s%s' % (result[1], result[2], result[3], result[4])
                number_normal = number_normal.replace('..', '.').replace(' ', '')
                number_1 = result[1] + result[2]
                number_list.append(number_normal)
                number_list.append(number_normal.replace('.', ' '))
                number_list.append(number_1)

                if len(result[2]) == 3:
                    number_normal = '%s-0%s.%s%s' % (result[1], result[2], result[3], result[4])
                    number_list.append(number_normal.replace('..', '.').replace(' ', ''))
            else:
                result = re.findall(r'([^. ]+\.EP[\d]+)\.', file_name)
                if result:
                    number_list.append(result[0])

        # MKY-HS-004.周寗.催情民宿.偷下春药3P干爆夫妇.麻豆传媒映画
        # PH-US-002.色控.音乐老师全裸诱惑.麻豆传媒映画
        # MKY-TX-002.林芊彤.淫行出租车.负心女的淫奸报复.麻豆传媒映画
        elif re.search(r'([A-Z]{2,})-([A-Z]{2,})-(\d+)', file_name):
            result = re.search(r'([A-Z]{2,})-([A-Z]{2,})-(\d+)', file_name)
            if result:
                number_normal = '%s-%s-%s' % (result[1], result[2], result[3])
                number_list.append(number_normal)

        # MDUS系列[中文字幕].LAX0025.性感尤物渴望激情猛操.RUCK ME LIKE A SEX DOLL.麻豆传媒映画
        elif 'MDUS系列' in file_name:
            result = re.search(r'([A-Z]{3,})-?(\d{3,})', file_name.replace('MDUS系列', ''))
            if result:
                number_normal = '%s-%s' % (result[1], result[2])
                number_no_line = '%s%s' % (result[1], result[2])
                number_list.extend([number_no_line, number_normal])

        # REAL野性派001-朋友的女友讓我最上火
        elif 'REAL野性派' in file_name:
            result = re.search(r'REAL野性派-?(\d{3,})', file_name)
            if result:
                number_no_line = 'REAL野性派%s' % (result[1])
                number_normal = 'REAL野性派-%s' % (result[1])
                number_list.extend([number_no_line, number_normal])

        # mini06.全裸家政.只为弟弟的学费打工.被玩弄的淫乱家政小妹.mini传媒
        elif re.search(r'([A-Z]{3,})-?(\d{2,})', file_name):
            result = re.search(r'([A-Z]{3,})-?(\d{2,})', file_name)
            if result:
                number_normal = '%s-%s' % (result[1], result[2])
                number_no_line = '%s%s' % (result[1], result[2])
                number_0_normal = '%s-0%s' % (result[1], result[2])
                number_0_no_line = '%s0%s' % (result[1], result[2])
                number_list.extend([number_normal, number_no_line, number_0_normal, number_0_no_line])

        # MDS-009.张芸熙.巨乳旗袍诱惑.搔首弄姿色气满点.麻豆传媒映画
        # MDS-0014苏畅.纯洁的爱爱.青梅竹马的性爱练习曲.麻豆传媒映画
        # MD-0208.夏晴子.苏清歌.荒诞家族淫游之春.快感刺激的极致调教.麻豆传媒映画
        # MDX-0184.沈娜娜.学生不乖怒操体罚.打屁股插穴样样来.麻豆传媒映画
        # MDXS-0011沈娜娜.足球宝贝射门淫球赚奖金
        # MDL-0002 夏晴子 苏语棠 请做我的奴隶 下集 在魔鬼面前每个人都是奴隶 麻豆传媒映画
        # MMZ-032.寻小小.女神的性辅导.我的老师是寻小小.麻豆出品X猫爪影像
        # MAD-022.穆雪.野性欢愉.爱豆x麻豆联合出品
        # MDWP-0013.璇元.淫行按摩院.麻豆传媒职场淫行系列
        # TT-005.孟若羽.F罩杯性感巨乳DJ.麻豆出品x宫美娱乐
        # MDS005 被雇主强上的熟女家政妇 大声呻吟被操到高潮 杜冰若
        elif re.search(r'([A-Z]{2,})-?(\d{3,})', file_name):
            result = re.search(r'([A-Z]{2,})-?(\d{3,})', file_name)
            if result:
                number_normal = '%s-%s' % (result[1], result[2])
                number_has_nothing = '%s%s' % (result[1], result[2])
                number_has_space = '%s %s' % (result[1], result[2])
                number_list.extend([number_normal, number_has_nothing, number_has_space])

                # 三位数改成四位数字的番号
                if len(result[2]) == 3:
                    number_normal_4 = '%s-0%s' % (result[1], result[2])
                    number_has_nothing_4 = '%s0%s' % (result[1], result[2])
                    number_has_space_4 = '%s 0%s' % (result[1], result[2])
                    number_list.extend([number_normal_4, number_has_nothing_4, number_has_space_4])
        if len(number_list):
            break

    # 台湾第一女优吴梦梦.OL误上痴汉地铁.惨遭多人轮番奸玩.麻豆传媒映画代理出品
    # PsychoPorn色控.找来大奶姐姐帮我乳交.麻豆传媒映画
    # 國産麻豆AV 麻豆番外 大番號女優空降上海 特別篇 沈芯語
    # 鲍鱼游戏SquirtGame.吸舔碰糖.失败者屈辱凌辱.麻豆传媒映画伙伴皇家华人
    # 导演系列 外卖员的色情体验 麻豆传媒映画
    # 过长时，可能有多余字段，取头尾
    real_file_name = os.path.splitext(os.path.split(file_path)[1])[0] if file_path else ''
    temp_filename_list = re.sub(r'[\W_]', ' ', real_file_name.upper()).replace('  ', ' ').replace('  ', ' ').split(' ')
    temp_filename_list = [i.strip() for i in temp_filename_list.copy() if i.strip()]
    lable_list = get_lable_list()
    if len(temp_filename_list) > 1:
        cc = True
        while cc:
            for lable in lable_list:
                if lable in temp_filename_list[0]:
                    temp_filename_list.pop(0)
                    break
                if lable in temp_filename_list[-1]:
                    temp_filename_list.pop()
                    break
            else:
                cc = False
        if len(temp_filename_list):
            for each in temp_filename_list:
                if len(each) > 7:
                    filename_list.append(each)
            filename_list.append(' '.join(temp_filename_list))
            if len(temp_filename_list) > 2:
                if len(''.join(temp_filename_list[:2])) > 10:
                    filename_list.append(' '.join(temp_filename_list[:2]))
                if len(''.join(temp_filename_list[2:])) > 10:
                    filename_list.append(' '.join(temp_filename_list[2:]))
            if len(temp_filename_list) > 3:
                if len(''.join(temp_filename_list[1:-1])) > 10:
                    filename_list.append(' '.join(temp_filename_list[1:-1]))
                if len(''.join(temp_filename_list[2:-2])) > 10:
                    filename_list.append(' '.join(temp_filename_list[2:-2]))
    else:
        filename_list.append(file_name[:30].strip())
        if len(file_name) > 38:
            filename_list.append(file_name[10:30].strip())

    # 把文件名加到列表
    filename_list.append(real_file_name)

    # 转繁体
    filename_list.append(zhconv.convert(filename_list[0], 'zh-hant'))

    # 去重去空
    new_number_list = []
    new_filename_list = []
    [new_number_list.append(i) for i in number_list if i and i not in new_number_list]
    [new_filename_list.append(i) for i in filename_list if i and i not in new_filename_list]
    return new_number_list, new_filename_list


if __name__ == '__main__':
    # yapf: disable
    # get_number_list('Md0165-4')
    # get_number_list('GDCM-018')
    # get_number_list('MKY-JB-010')
    # get_number_list('PMC-085', file_path='PMC/PMC-085.雪霏.出差借宿小姨子乱伦姐夫.特别照顾的肉体答谢.蜜桃影像传媒.ts')
    # get_number_list('TM-0165', file_path='TM0165.王小妮.妈妈的性奴之路.性感少妇被儿子和同学调教成性奴.天美传媒')
    # print(get_number_list('mini06.全裸家政.只為弟弟的學費打工.被玩弄的淫亂家政小妹.mini傳媒'))
    # get_number_list('mini06', file_path='mini06.全裸家政.只為弟弟的學費打工.被玩弄的淫亂家政小妹.mini傳媒')
    # get_number_list('mini06.全裸家政.只为弟弟的学费打工.被玩弄的淫乱家政小妹.mini传媒')
    # get_number_list('', file_path='夏日回忆 贰')
    # get_number_list('MDX-0016')
    # get_number_list('MDSJ-0004')
    # get_number_list('RS-020')
    # get_number_list('PME-018.雪霏.禽兽小叔迷奸大嫂.性感身材任我玩弄.蜜桃影像传媒', file_path='PME-018.雪霏.禽兽小叔迷奸大嫂.性感身材任我玩弄.蜜桃影像传媒')
    # get_number_list('老公在外出差家里的娇妻被入室小偷强迫性交 - 美酱')
    # get_number_list('', file_path='夏日回忆 贰 HongKongDoll玩偶姐姐.短篇集.夏日回忆 贰.Summer Memories.Part 2.mp4')
    # get_number_list('', file_path='HongKongDoll玩偶姐姐.短篇集.夏日回忆 贰.Summer Memories.Part 2.mp4')
    # get_number_list('', file_path="【HongKongDoll玩偶姐姐.短篇集.情人节特辑.Valentine's Day Special-cd2"))
    # get_number_list('', file_path='PMC-062 唐茜.綠帽丈夫連同新弟怒操出軌老婆.強拍淫蕩老婆被操 唐茜.ts')
    # get_number_list('', file_path='MKY-HS-004.周寗.催情民宿.偷下春药3P干爆夫妇.麻豆传媒映画')
    # get_number_list('淫欲游戏王.EP6', appoint_number='淫欲游戏王.EP5', file_path='淫欲游戏王.EP6.情欲射龙门.性爱篇.郭童童.李娜.双英战龙根3P混战.麻豆传媒映画.ts') # EP不带.才能搜到
    # get_number_list('', file_path='PMS-003.职场冰与火.EP3设局.宁静.苏文文.设局我要女人都臣服在我胯下.蜜桃影像传媒')
    # get_number_list('', file_path='PMS-001 性爱公寓EP04 仨人.蜜桃影像传媒.ts')
    # get_number_list('', file_path='PMS-001.性爱公寓EP03.ts')
    # get_number_list('', file_path='MDX-0236-02.沈娜娜.青梅竹马淫乱3P.麻豆传媒映画x逼哩逼哩blibli.ts')
    # get_number_list('', file_path='淫欲游戏王.EP6.情欲射龙门.性爱篇.郭童童.李娜.双英战龙根3P混战.麻豆传媒映画.ts')
    # # get_number_list('', file_path='淫欲游戏王.EP6.情欲射龙门.性爱篇.郭童童.李娜.双英战龙根3P混战.麻豆传媒映画.ts')
    # get_number_list('', file_path='麻豆傳媒映畫原版 兔子先生 我的女友是女優 女友是AV女優是怎樣的體驗-美雪樱')   # 简体搜不到
    # get_number_list('', file_path='麻豆傳媒映畫原版 兔子先生 拉麵店搭訕超可愛少女下-柚木结爱.TS')
    # '麻豆傳媒映畫原版 兔子先生 拉麵店搭訕超可愛少女下-柚木結愛', '麻豆傳媒映畫原版 兔子先生 拉麵店搭訕超可愛少女下-', ' 兔子先生 拉麵店搭訕超可愛少女下-柚木結愛']
    # get_number_list('', file_path='麻豆傳媒映畫原版 兔子先生 我的女友是女優 女友是AV女優是怎樣的體驗-美雪樱.TS')
    # get_number_list('', file_path='PMS-001 性爱公寓EP02 女王 蜜桃影像传媒 -莉娜乔安.TS')
    # get_number_list('91CM-081', file_path='91CM-081.田恬.李琼.继母与女儿.三.爸爸不在家先上妹妹再玩弄母亲.果冻传媒.mp4')
    # get_number_list('91CM-081', file_path='MDJ-0001.EP3.陈美惠.淫兽寄宿家庭.我和日本父子淫乱的一天.麻豆传媒映画.mp4')
    # get_number_list('91CM-081', file_path='MDJ0001 EP2  AV 淫兽鬼父 陈美惠  .TS')
    # get_number_list('91CM-081', file_path='MXJ-0005.EP1.弥生美月.小恶魔高校生.与老师共度的放浪补课.麻豆传媒映画.TS')
    # get_number_list('91CM-081', file_path='MKY-HS-004.周寗.催情民宿.偷下春药3P干爆夫妇.麻豆传媒映画.TS')
    # get_number_list('91CM-081', file_path='PH-US-002.色控.音乐老师全裸诱惑.麻豆传媒映画.TS')
    # get_number_list('91CM-081', file_path='MDX-0236-02.沈娜娜.青梅竹马淫乱3P.麻豆传媒映画x逼哩逼哩blibli.TS')
    # get_number_list('91CM-081', file_path='MD-0140-2.蜜苏.家有性事EP2.爱在身边.麻豆传媒映画.TS')
    print(get_number_list('91CM-081',
                          file_path='aaa/MDUS系列[中文字幕].LAX0025.性感尤物渴望激情猛操.RuCK ME LIKE A SEX DOLL.麻豆传媒映画.TS'))
    # get_number_list('91CM-081', file_path='REAL野性派001-朋友的女友讓我最上火.TS')
    # get_number_list('91CM-081', file_path='MDS-009.张芸熙.巨乳旗袍诱惑.搔首弄姿色气满点.麻豆传媒映画.TS')
    # get_number_list('91CM-081', file_path='MDS005 被雇主强上的熟女家政妇 大声呻吟被操到高潮 杜冰若.mp4.TS')
    # get_number_list('91CM-081', file_path='TT-005.孟若羽.F罩杯性感巨乳DJ.麻豆出品x宫美娱乐.TS')
    # get_number_list('91CM-081', file_path='台湾第一女优吴梦梦.OL误上痴汉地铁.惨遭多人轮番奸玩.麻豆传媒映画代理出品.TS')
    # get_number_list('91CM-081', file_path='PsychoPorn色控.找来大奶姐姐帮我乳交.麻豆传媒映画.TS')
    # get_number_list('91CM-081', file_path='鲍鱼游戏SquirtGame.吸舔碰糖.失败者屈辱凌辱.TS')
    # get_number_list('91CM-081', file_path='导演系列 外卖员的色情体验 麻豆传媒映画.TS')
    # get_number_list('91CM-081', file_path='MDS007 骚逼女友在作妖-硬上男友当玩具 叶一涵.TS')
    # get_number_list('MDM-002') # 去掉标题最后的发行商
    # get_number_list('MDS-007') # 数字要四位才能搜索到，即 MDS-0007 MDJ001 EP1 我的女优物语陈美惠.TS
    # get_number_list('MDS-007', file_path='MDJ001 EP1 我的女优物语陈美惠.TS') # 数字要四位才能搜索到，即 MDJ-0001.EP1
    # get_number_list('91CM-090') # 带横线才能搜到
    # get_number_list('台湾SWAG chloebabe 剩蛋特辑 干爆小鹿')   # 带空格才能搜到
    # get_number_list('淫欲游戏王EP2')  # 不带空格才能搜到
    # get_number_list('台湾SWAG-chloebabe-剩蛋特輯-幹爆小鹿')
    # get_number_list('MD-0020')
    # get_number_list('mds009')
    # get_number_list('mds02209')
    # get_number_list('女王的SM调教')
    # get_number_list('91CM202')
    # get_number_list('91CM-202')
