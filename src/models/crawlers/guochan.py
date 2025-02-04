#!/usr/bin/env python3

import os.path
import re

import urllib3
import zhconv

from models.base.number import remove_escape_string

urllib3.disable_warnings()  # yapf: disable


# import traceback
# import Function.config as cf


def get_lable_list():
    return [
        "麻豆传媒",
        "91茄子",
        "Ed Mosaic",
        "HongKongDoll",
        "JVID",
        "MINI传媒",
        "SA国际传媒",
        "TWAV",
        "乌鸦传媒",
        "乐播传媒",
        "优蜜传媒",
        "偶蜜国际",
        "叮叮映画",
        "哔哩传媒",
        "大象传媒",
        "天美传媒",
        "开心鬼传媒",
        "微密圈",
        "扣扣传媒",
        "抖阴传媒",
        "星空无限传媒",
        "映秀传媒",
        "杏吧传媒",
        "果冻传媒",
        "模密传媒",
        "爱污传媒",
        "爱神传媒",
        "爱豆传媒",
        "狂点映像",
        "猛料原创",
        "猫爪影像",
        "皇家华人",
        "精东影业",
        "糖心VLOG",
        "维秘传媒",
        "草莓视频",
        "萝莉社",
        "蜜桃传媒",
        "西瓜影视",
        "起点传媒",
        "香蕉视频",
        "PsychoPorn色控",
        "蜜桃影像传媒",
        "大番号番啪啪",
        "REAL野性派",
        "豚豚创媒",
        "宫美娱乐",
        "肉肉传媒",
        "爱妃传媒",
        "91制片厂",
        "O-STAR",
        "兔子先生",
        "杏吧原创",
        "杏吧独家",
        "辣椒原创",
        "麻豆传媒映画",
        "红斯灯影像",
        "绝对领域",
        "麻麻传媒",
        "渡边传媒",
        "AV帝王",
        "桃花源",
        "蝌蚪传媒",
        "SWAG",
        "麻豆",
        "杏吧",
        "糖心",
        "国产短视频",
        "国产精品",
        "国产AV",
        "涩会",
    ]


def get_actor_list():
    return [
        "Madison Summers",
        "Spencer Bradley",
        "Madison Morgan",
        "Rosalyn Sphinx",
        "Braylin Bailey",
        "Whitney Wright",
        "Victoria Voxxx",
        "Alexia Anders",
        "Bella Rolland",
        "Violet Myers",
        "Sophia Leone",
        "Violet Starr",
        "Eliza Ibarra",
        "HongKongDoll",
        "Keira Croft",
        "April Olsen",
        "Avery Black",
        "Amber Moore",
        "Anny Aurora",
        "Skylar Snow",
        "Harley Haze",
        "Paige Owens",
        "Vanessa Sky",
        "MasukuChan",
        "Kate Bloom",
        "Kimmy Kimm",
        "Ana Foxxx",
        "Lexi Luna",
        "Gia Derza",
        "Skye Blue",
        "Nico Love",
        "Alyx Star",
        "Ryan Reid",
        "Kira Noir",
        "Karma Rx",
        "下面有根棒棒糖",
        "Vivian姐",
        "COLA酱",
        "cola醬",
        "Stacy",
        "ROXIE",
        "真木今日子",
        "小七软同学",
        "Chloe",
        "Alona",
        "小日向可怜",
        "NANA",
        "玩偶姐姐",
        "粉色情人",
        "桥本香菜",
        "冉冉学姐",
        "小二先生",
        "饼干姐姐",
        "Rona",
        "不见星空",
        "米娜学姐",
        "阿蛇姐姐",
        "樱花小猫",
        "樱井美里",
        "宸荨樱桃",
        "樱空桃桃",
        "牛奶泡芙",
        "91兔兔",
        "棉花糖糖",
        "桥本爱菜",
        "许木学长",
        "MOMO",
        "驯鹿女孩",
        "高梨遥香",
        "DORY",
        "冬月结衣",
        "Aida",
        "香菜公主",
        "藤田美绪",
        "浅尾美羽",
        "天音美纱",
        "中条爱莉",
        "三月樱花",
        "Emma",
        "Vita",
        "千夜喵喵",
        "水原圣子",
        "白川麻衣",
        "池田奈美",
        "西村莉娜",
        "A天使爱",
        "中野惠子",
        "麻衣CC",
        "樱桃空空",
        "LENA",
        "小泽纱香",
        "木下日葵",
        "中岛芳子",
        "弥生美月",
        "逢见梨花",
        "宇佐爱花",
        "沙月芽衣",
        "羽月萌音",
        "前田由美",
        "伊东爱瑠",
        "Misa",
        "绿帽先生",
        "莉娜乔安",
        "柚木结爱",
        "黑田奈奈",
        "神山奈奈",
        "孟若羽",
        "夏晴子",
        "吴梦梦",
        "沈娜娜",
        "李蓉蓉",
        "林思妤",
        "仙儿媛",
        "金宝娜",
        "季妍希",
        "温芮欣",
        "吴文淇",
        "苏语棠",
        "秦可欣",
        "吴芳宜",
        "李娜娜",
        "乐奈子",
        "宋南伊",
        "小水水",
        "白允儿",
        "管明美",
        "雪千夏",
        "苏清歌",
        "玥可岚",
        "梁芸菲",
        "白熙雨",
        "小敏儿",
        "楚梦舒",
        "柚子猫",
        "姚宛儿",
        "宋雨川",
        "舒可芯",
        "苏念瑾",
        "白沛瑶",
        "林沁儿",
        "唐雨菲",
        "李允熙",
        "张芸熙",
        "寻小小",
        "白靖寒",
        "钟宛冰",
        "李薇薇",
        "米菲兔",
        "雷梦娜",
        "董悦悦",
        "袁子仪",
        "赖畇希",
        "王以欣",
        "夏禹熙",
        "狐不妖",
        "凌波丽",
        "黎芷萱",
        "陆斑比",
        "辛尤里",
        "小猫咪",
        "顾桃桃",
        "南芊允",
        "岚湘庭",
        "林芊彤",
        "梁佳芯",
        "林凤娇",
        "明日香",
        "绫波丽",
        "邓紫晴",
        "赵一曼",
        "吴茜茜",
        "锅锅酱",
        "倪哇哇",
        "潘雨曦",
        "吴恺彤",
        "美杜莎",
        "郭童童",
        "陈可心",
        "莫夕慈",
        "沈芯语",
        "董小宛",
        "苏艾文",
        "翁雨澄",
        "赵晓涵",
        "小桃酱",
        "宋东琳",
        "香月怜",
        "李文雯",
        "白若冰",
        "徐夜夜",
        "真希波",
        "爱丽丝",
        "张宇芯",
        "金善雅",
        "李依依",
        "苏安亚",
        "奶咪酱",
        "白葵司",
        "罗瑾萱",
        "宁洋子",
        "小夜夜",
        "白晶晶",
        "张雅婷",
        "吴心语",
        "林曼芸",
        "项子甯",
        "吳芳宜",
        "苏小小",
        "文冰冰",
        "韩宝儿",
        "白星雨",
        "林怡梦",
        "张欣妍",
        "七濑恋",
        "白思吟",
        "吴凯彤",
        "溫芮欣",
        "林可菲",
        "黎芷媗",
        "御梦子",
        "苏雨彤",
        "古伊娜",
        "聂小倩",
        "陈圆圆",
        "沙美辰",
        "林妙可",
        "乐淆雪",
        "李恩娜",
        "周晴晴",
        "杨思敏",
        "李曼妮",
        "戚小怜",
        "谢语彤",
        "王筱璐",
        "卢珊珊",
        "程诗诗",
        "林玥玥",
        "白瞳瞳",
        "魏乔安",
        "米胡桃",
        "施子涵",
        "北野爱",
        "杜冰若",
        "玛丽莲",
        "胡蓉蓉",
        "万静雪",
        "花语柔",
        "萧悦儿",
        "林晓雪",
        "兰心洁",
        "神谷怜",
        "唐雨霏",
        "鸡蛋饼",
        "沈湘妮",
        "费爵娜",
        "小美惠",
        "大奶露",
        "向若云",
        "苏小沫",
        "榨汁姬",
        "陈星然",
        "夏雨荷",
        "姚彤彤",
        "莫云雪",
        "艾瑞卡",
        "黄雪纯",
        "赵雅琳",
        "叶宸欣",
        "伊琬琳",
        "陈美惠",
        "金巧巧",
        "陈美琳",
        "陆思涵",
        "顾小北",
        "陈小雨",
        "维里娜",
        "兔小白",
        "叶子红",
        "美凉子",
        "李丹彤",
        "李微微",
        "白婷婷",
        "艾米酱",
        "刘小姗",
        "白童童",
        "张琪琪",
        "Yua",
        "小玩子",
        "岚可彤",
        "都可可",
        "李慕儿",
        "叶一涵",
        "赵佳美",
        "董小婉",
        "钟丽琪",
        "韩小雅",
        "杨朵儿",
        "叶梦语",
        "程雨沫",
        "张曼青",
        "纪妍希",
        "伊婉琳",
        "凌雨萱",
        "潘甜甜",
        "美竹玲",
        "韩依人",
        "奈奈子",
        "林雪漫",
        "宋甜甜",
        "陆雪琪",
        "宋妮可",
        "陆子欣",
        "范可可",
        "许依然",
        "苏小新",
        "蒋梦琳",
        "李可欣",
        "小鹿酱",
        "小林杏",
        "陶杏儿",
        "明步奈",
        "苏宁儿",
        "白潼潼",
        "增田枫",
        "特污兔",
        "何安汝",
        "倪菀儿",
        "唐可可",
        "口罩酱",
        "小千绪",
        "糖糖儿",
        "许安妮",
        "李婧琪",
        "刘思慧",
        "欧阳晶",
        "欧美玲",
        "林亦涵",
        "钟以彤",
        "许书曼",
        "付妙菱",
        "伊靖瑶",
        "张娅庭",
        "韩小野",
        "宫泽蓝",
        "冯思雨",
        "林小樱",
        "刘颖儿",
        "莫潇潇",
        "胡心瑶",
        "林雨露",
        "苏婧薇",
        "许月珍",
        "陈若瑶",
        "吴芮瑜",
        "叶如梦",
        "刘依依",
        "吴语菲",
        "张妮妮",
        "林子涵",
        "张子瑜",
        "周卿卿",
        "李师师",
        "苏语堂",
        "方紫璐",
        "袁采菱",
        "刘清韵",
        "李曼丽",
        "刘小雯",
        "姬咲华",
        "高小颜",
        "蔡晓雨",
        "梁如意",
        "林语桐",
        "王小妮",
        "唐月琴",
        "星谷瞳",
        "何小丽",
        "张婉妍",
        "酒井爱",
        "张秀玲",
        "晚晚酱",
        "薛梦琪",
        "李乐乐",
        "张佳晨",
        "程媛媛",
        "沐语柔",
        "安琪拉",
        "韩倪希",
        "苏妲己",
        "白佳萱",
        "刘语珊",
        "徐韵珊",
        "糖果屋",
        "顾伊梦",
        "赵颖儿",
        "莫安安",
        "黎星若",
        "林予曦",
        "蒋佑怡",
        "王有容",
        "李恩琦",
        "赵美凤",
        "徐筱欣",
        "黄雅曼",
        "菲于娜",
        "金丞熙",
        "叶凡舒",
        "郭瑶瑶",
        "李嘉欣",
        "袁庭妮",
        "林思好",
        "张云熙",
        "李忆彤",
        "伊蒂丝",
        "沙耶香",
        "美雪樱",
        "王亦舒",
        "李文静",
        "鸡教练",
        "斑斑",
        "坏坏",
        "糖糖",
        "艾秋",
        "凌薇",
        "莉娜",
        "韩棠",
        "苡若",
        "尤莉",
        "优娜",
        "林嫣",
        "徐蕾",
        "周甯",
        "唐茜",
        "香菱",
        "佳芯",
        "湘湘",
        "米欧",
        "斑比",
        "蜜苏",
        "小婕",
        "艾熙",
        "娃娃",
        "艾玛",
        "雪霏",
        "夜夜",
        "欣欣",
        "乔安",
        "羽芮",
        "美酱",
        "师师",
        "玖玖",
        "橙子",
        "晨曦",
        "苏娅",
        "黎儿",
        "晨晨",
        "嘉洛",
        "小遥",
        "苏畅",
        "琪琪",
        "苡琍",
        "李慕",
        "心萱",
        "昀希",
        "黎娜",
        "乐乐",
        "樱桃",
        "桐桐",
        "苏璇",
        "安娜",
        "悠悠",
        "茉莉",
        "宛冰",
        "静静",
        "丝丝",
        "菲菲",
        "樱樱",
        "波妮",
        "唐芯",
        "小野",
        "何苗",
        "甜心",
        "瑶瑶",
        "小捷",
        "薇薇",
        "美樱",
        "宁静",
        "欧妮",
        "吉吉",
        "小桃",
        "绯丽",
        "嘉琪",
        "咪妮",
        "雯茜",
        "小洁",
        "李琼",
        "唐霏",
        "岚玥",
        "熙熙",
        "米娅",
        "舒舒",
        "斯斯",
        "欣怡",
        "妍儿",
        "阿雅",
        "宋可",
        "畇希",
        "柔伊",
        "雅沁",
        "惠敏",
        "露露",
        "艾悠",
        "娜娜",
        "李娜",
        "肖云",
        "王玥",
        "林洋",
        "清洛",
        "艾鲤",
        "依涵",
        "半雪",
        "琦琦",
        "莎莎",
        "小冉",
        "琳怡",
        "莉奈",
        "梅子",
        "啤儿",
        "瑶贝",
        "杨柳",
        "童汐",
        "米亚",
        "琳达",
        "晴天",
        "KK",
        "紫宸",
        "淑怡",
        "花花",
        "金铭",
        "程葳",
        "妍希",
        "咪妃",
        "茜茜",
        "小蜜",
        "凌萱",
        "觅嫣",
        "涵涵",
        "欲梦",
        "美琳",
        "杜鹃",
        "许诺",
        "兮兮",
        "白鹿",
        "虞姬",
        "丽萨",
        "蔷薇",
        "小影",
        "优优",
        "茶茶",
        "可儿",
        "甜甜",
        "憨憨",
        "波尼",
        "依颂",
        "依依",
        "思思",
        "芳情",
        "月牙",
        "小爱",
        "淳儿",
        "苗方",
        "茶理",
        "苹果",
        "苏然",
        "陶子",
        "董欣",
        "羽熙",
        "清沐",
        "林襄",
        "娃诺",
        "洁咪",
        "小昭",
        "球球",
        "紫萱",
        "南兰",
        "安琪",
        "可乐",
        "夏露",
        "诗琪",
        "陈韵",
        "丽娜",
        "苏旋",
        "月月",
        "石榴",
        "米兰",
        "恩恩",
        "西子",
        "芷萱",
        "酥酥",
        "王茜",
        "千鹤",
        "雪见",
        "姜洁",
        "张晴",
        "辰悦",
        "丁香",
        "白颖",
        "穆娜",
        "小芳",
        "吉娜",
        "秋霞",
        "无双",
        "夏宝",
        "舒涵",
        "小柔",
        "小小",
        "璇元",
        "米砂",
        "余丽",
        "美嘉",
        "莉莉",
        "奈奈",
        "黑糖",
        "晴子",
        "多乙",
        "徐婕",
        "闵闵",
        "小雪",
        "洋洋",
        "明儿",
        "苏茜",
        "芯怡",
        "姚茜",
        "百合",
        "婉婷",
        "小乔",
        "芽芽",
        "婕珍",
        "乔乔",
        "紫寒",
        "小薇",
        "菜菜",
        "洁米",
        "夏天",
        "灵枝",
        "语伊",
        "徐艳",
        "王佩",
        "希汶",
        "雅捷",
        "喵喵",
        "尤奈",
        "仙儿",
        "氖氖",
        "蔚曼",
        "田恬",
        "颂潮",
        "小婵",
        "千凌",
        "李燕",
        "林芳",
        "杨桃",
        "艾莉",
        "落落",
        "冯雪",
        "王蓉",
        "妖妖",
        "雨晨",
        "心雪",
        "穆雪",
        "韩焉",
        "邱月",
        "檀雅",
        "柯柯",
        "七七",
        "鱼儿",
        "丹丹",
        "简一",
        "淑仪",
        "小哇",
        "朵儿",
        "妲己",
        "云朵",
        "唐菲",
        "邦妮",
        "白英",
        "夏夏",
        "安安",
        "小艺",
        "丽丽",
        "敏敏",
        "空空",
        "椿芽",
        "小言",
        "李蕊",
        "水水",
        "小鱼",
        "艾艾",
        "尹媚",
        "夏滢",
        "琳希",
        "王欣",
        "洛雪",
        "李茹",
        "娜米",
        "萱萱",
        "肖泳",
    ]


def get_number_list(number, appoint_number="", file_path=""):  # 处理国产番号
    # 国产匹配番号或标题前也可以先排除路径中多余字符
    if file_path:
        file_path = remove_escape_string(file_path)

    file_name = os.path.splitext(os.path.split(file_path)[1])[0].upper() if file_path else ""
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
        file_name_1 = zhconv.convert(file_name, "zh-cn") if file_name else zhconv.convert(number, "zh-cn")
        file_name_1 = re.sub(r"-[^0-9]+?$", "", file_name_1)
        file_name_2 = os.path.splitext(os.path.split(file_path)[1])[0].upper() if file_path else ""
        file_name_2 = zhconv.convert(file_name_2, "zh-cn") if file_name_2 else zhconv.convert(number, "zh-cn")
        file_name_2 = re.sub(r"-[^0-9]+?$", "", file_name_2)
        file_path_list.extend([file_name_2, file_name_1])

    # 识别番号
    for file_name in file_path_list:
        # 91CM-081.田恬.李琼.继母与女儿.三.爸爸不在家先上妹妹再玩弄母亲.果冻传媒
        # 91MS-015.张淑仪.19岁D奶少女.被男友甩后下海.疯狂滥交高潮喷水.91制片厂
        if re.search(r"(91[A-Z]{2,})-?(\d{3,})", file_name):
            result = re.search(r"(91[A-Z]{2,})-?(\d{3,})", file_name)
            if result:
                number_normal = f"{result[1]}-{result[2]}"
                number_has_nothing = f"{result[1]}{result[2]}"
                number_has_space = f"{result[1]} {result[2]}"
                number_list.extend([number_normal, number_has_nothing, number_has_space])

        # MDX-0236-02.沈娜娜.青梅竹马淫乱3P.麻豆传媒映画x逼哩逼哩blibli
        # MD-0140-2.蜜苏.家有性事EP2.爱在身边.麻豆传媒映画
        elif re.search(r"([A-Z]{2,})-?(\d{3,})-(\d+)", file_name):
            result = re.search(r"([A-Z]{2,})-?(\d{3,})-(\d+)", file_name)
            if result:
                number_normal = f"{result[1]}-{result[2]}-{result[3]}"
                number_list.append(number_normal)

        # MXJ-0005.EP1.弥生美月.小恶魔高校生.与老师共度的放浪补课.麻豆传媒映画
        # MDJ0001 EP2  AV 淫兽鬼父 陈美惠  .TS
        # PMS-003.职场冰与火.EP3设局.宁静.苏文文.设局我要女人都臣服在我胯下.蜜桃影像传媒
        # 淫欲游戏王.EP6.情欲射龙门.性爱篇.郭童童.李娜.双英战龙根3P混战.麻豆传媒映画.ts
        # PMS-001 性爱公寓EP04 仨人.蜜桃影像传媒
        elif "EP" in file_name:
            result = re.search(r"([A-Z]{2,})-?(\d{3,})(.*)(EP[\d]+)", file_name)
            if result:
                number_normal = f"{result[1]}-{result[2]}.{result[3]}{result[4]}"
                number_normal = number_normal.replace("..", ".").replace(" ", "")
                number_1 = result[1] + result[2]
                number_list.append(number_normal)
                number_list.append(number_normal.replace(".", " "))
                number_list.append(number_1)

                if len(result[2]) == 3:
                    number_normal = f"{result[1]}-0{result[2]}.{result[3]}{result[4]}"
                    number_list.append(number_normal.replace("..", ".").replace(" ", ""))
            else:
                result = re.findall(r"([^. ]+\.EP[\d]+)\.", file_name)
                if result:
                    number_list.append(result[0])

        # MKY-HS-004.周寗.催情民宿.偷下春药3P干爆夫妇.麻豆传媒映画
        # PH-US-002.色控.音乐老师全裸诱惑.麻豆传媒映画
        # MKY-TX-002.林芊彤.淫行出租车.负心女的淫奸报复.麻豆传媒映画
        elif re.search(r"([A-Z]{2,})-([A-Z]{2,})-(\d+)", file_name):
            result = re.search(r"([A-Z]{2,})-([A-Z]{2,})-(\d+)", file_name)
            if result:
                number_normal = f"{result[1]}-{result[2]}-{result[3]}"
                number_list.append(number_normal)

        # MDUS系列[中文字幕].LAX0025.性感尤物渴望激情猛操.RUCK ME LIKE A SEX DOLL.麻豆传媒映画
        elif "MDUS系列" in file_name:
            result = re.search(r"([A-Z]{3,})-?(\d{3,})", file_name.replace("MDUS系列", ""))
            if result:
                number_normal = f"{result[1]}-{result[2]}"
                number_no_line = f"{result[1]}{result[2]}"
                number_list.extend([number_no_line, number_normal])

        # REAL野性派001-朋友的女友讓我最上火
        elif "REAL野性派" in file_name:
            result = re.search(r"REAL野性派-?(\d{3,})", file_name)
            if result:
                number_no_line = "REAL野性派%s" % (result[1])
                number_normal = "REAL野性派-%s" % (result[1])
                number_list.extend([number_no_line, number_normal])

        # mini06.全裸家政.只为弟弟的学费打工.被玩弄的淫乱家政小妹.mini传媒
        elif re.search(r"([A-Z]{3,})-?(\d{2,})", file_name):
            result = re.search(r"([A-Z]{3,})-?(\d{2,})", file_name)
            if result:
                number_normal = f"{result[1]}-{result[2]}"
                number_no_line = f"{result[1]}{result[2]}"
                number_0_normal = f"{result[1]}-0{result[2]}"
                number_0_no_line = f"{result[1]}0{result[2]}"
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
        elif re.search(r"([A-Z]{2,})-?(\d{3,})", file_name):
            result = re.search(r"([A-Z]{2,})-?(\d{3,})", file_name)
            if result:
                number_normal = f"{result[1]}-{result[2]}"
                number_has_nothing = f"{result[1]}{result[2]}"
                number_has_space = f"{result[1]} {result[2]}"
                number_list.extend([number_normal, number_has_nothing, number_has_space])

                # 三位数改成四位数字的番号
                if len(result[2]) == 3:
                    number_normal_4 = f"{result[1]}-0{result[2]}"
                    number_has_nothing_4 = f"{result[1]}0{result[2]}"
                    number_has_space_4 = f"{result[1]} 0{result[2]}"
                    number_list.extend([number_normal_4, number_has_nothing_4, number_has_space_4])
        if len(number_list):
            break
    # 番号识别将纯数字和字母放在最前面（将长度最短的放前面即可），刮削网站一般也只取 number_list 第一项进行搜索，其他用于搜索结果页比对
    sorted_number_list = sorted(number_list, key=lambda x: len(x))

    # 以下处理没有番号的作品
    # 台湾第一女优吴梦梦.OL误上痴汉地铁.惨遭多人轮番奸玩.麻豆传媒映画代理出品
    # PsychoPorn色控.找来大奶姐姐帮我乳交.麻豆传媒映画
    # 國産麻豆AV 麻豆番外 大番號女優空降上海 特別篇 沈芯語
    # 鲍鱼游戏SquirtGame.吸舔碰糖.失败者屈辱凌辱.麻豆传媒映画伙伴皇家华人
    # 导演系列 外卖员的色情体验 麻豆传媒映画
    # 过长时，可能有多余字段，取头尾
    real_file_name = os.path.splitext(os.path.split(file_path)[1])[0] if file_path else ""
    temp_filename_list = re.sub(r"[\W_]", " ", real_file_name.upper()).replace("  ", " ").replace("  ", " ").split(" ")
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
            filename_list.append(" ".join(temp_filename_list))
            if len(temp_filename_list) > 2:
                if len("".join(temp_filename_list[:2])) > 10:
                    filename_list.append(" ".join(temp_filename_list[:2]))
                if len("".join(temp_filename_list[2:])) > 10:
                    filename_list.append(" ".join(temp_filename_list[2:]))
            if len(temp_filename_list) > 3:
                if len("".join(temp_filename_list[1:-1])) > 10:
                    filename_list.append(" ".join(temp_filename_list[1:-1]))
                if len("".join(temp_filename_list[2:-2])) > 10:
                    filename_list.append(" ".join(temp_filename_list[2:-2]))
    else:
        filename_list.append(file_name[:30].strip())
        if len(file_name) > 38:
            filename_list.append(file_name[10:30].strip())

    # 把文件名加到列表
    filename_list.append(real_file_name)

    # 演员后面的第一句成功刮削概率较高，插入列表第一项
    # 超级丝袜控180大长腿女神▌苹果▌我的室友 第八篇 黑丝女仆骚丁小穴湿淋淋 肉棒塞满激怼爆射
    # 17205-最新极品天花板小萝莉▌粉色情人▌摄影师的威胁 粗屌爆艹少女白虎嫩鲍 极速刮擦蜜壶淫靡下体
    # 潮喷淫娃御姐〖小水水〗和异地大奶女友开房，激情互舔口爆高潮喷水，黑丝美腿女神极度淫骚 潮喷不停
    # 极品爆乳鲜嫩美穴貌美尤物▌苏美奈▌家政女仆的肉体服务 肏到羞耻喷汁 极射中出鲜嫩美穴
    # 【小酒改头换面】，罕见大胸嫩妹，小伙今夜捡到宝了
    if u := re.search(r"(【.+】|▌.+▌|〖.+〗|『.+』)[,，\- ]?(\S{6,18}?)[,，\-  ]", real_file_name):
        search_char = u.group(2)
        filename_list.insert(0, search_char)

    # 转繁体
    filename_list.append(zhconv.convert(filename_list[0], "zh-hant"))

    # 去重去空
    new_number_list = []
    new_filename_list = []
    [new_number_list.append(i) for i in sorted_number_list if i and i not in new_number_list]
    [new_filename_list.append(i) for i in filename_list if i and i not in new_filename_list]
    return new_number_list, new_filename_list


def get_extra_info(title, file_path, info_type, tag="", actor="", series=""):
    all_info = title + file_path + tag + actor + series

    # 未找到标签时，从各种信息里匹配，忽略大小写
    if info_type == "tag":
        tag_list = []
        all_tag = get_lable_list()
        for each in all_tag:
            if re.search(f"{each}", all_info, re.IGNORECASE):
                tag_list.append(each)
        new_tag_list = []
        [new_tag_list.append(i) for i in tag_list if i and i not in new_tag_list]
        return ",".join(new_tag_list)

    # 未找到演员时，看热门演员是否在标题和各种信息里，人名完全匹配
    if info_type == "actor":
        actor_list = []
        all_actor = get_actor_list()
        for each in all_actor:
            if re.search(rf"\b{each}\b", all_info, re.IGNORECASE):
                actor_list.append(each)
        new_actor_list = []
        [new_actor_list.append(i) for i in actor_list if i and i not in new_actor_list]
        return ",".join(new_actor_list)

    # 未找到系列时，从各种信息里匹配，没有相关数据，预留逻辑
    if info_type == "series":
        series_list = []
        all_series = get_lable_list()
        for each in all_series:
            if each in all_info.upper():
                series_list.append(each)
        new_series_list = []
        [new_series_list.append(i) for i in series_list if i and i not in new_series_list]
        return ",".join(new_series_list)


if __name__ == "__main__":
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
                          file_path='aaa/MDUS系列[中文字幕].LAX0025.性感尤物渴望激情猛操.RuCK ME LIKE A SEX DOLL.麻豆传媒映画.TS'))  # get_number_list('91CM-081', file_path='REAL野性派001-朋友的女友讓我最上火.TS')  # get_number_list('91CM-081', file_path='MDS-009.张芸熙.巨乳旗袍诱惑.搔首弄姿色气满点.麻豆传媒映画.TS')  # get_number_list('91CM-081', file_path='MDS005 被雇主强上的熟女家政妇 大声呻吟被操到高潮 杜冰若.mp4.TS')  # get_number_list('91CM-081', file_path='TT-005.孟若羽.F罩杯性感巨乳DJ.麻豆出品x宫美娱乐.TS')  # get_number_list('91CM-081', file_path='台湾第一女优吴梦梦.OL误上痴汉地铁.惨遭多人轮番奸玩.麻豆传媒映画代理出品.TS')  # get_number_list('91CM-081', file_path='PsychoPorn色控.找来大奶姐姐帮我乳交.麻豆传媒映画.TS')  # get_number_list('91CM-081', file_path='鲍鱼游戏SquirtGame.吸舔碰糖.失败者屈辱凌辱.TS')  # get_number_list('91CM-081', file_path='导演系列 外卖员的色情体验 麻豆传媒映画.TS')  # get_number_list('91CM-081', file_path='MDS007 骚逼女友在作妖-硬上男友当玩具 叶一涵.TS')  # get_number_list('MDM-002') # 去掉标题最后的发行商  # get_number_list('MDS-007') # 数字要四位才能搜索到，即 MDS-0007 MDJ001 EP1 我的女优物语陈美惠.TS  # get_number_list('MDS-007', file_path='MDJ001 EP1 我的女优物语陈美惠.TS') # 数字要四位才能搜索到，即 MDJ-0001.EP1  # get_number_list('91CM-090') # 带横线才能搜到  # get_number_list('台湾SWAG chloebabe 剩蛋特辑 干爆小鹿')   # 带空格才能搜到  # get_number_list('淫欲游戏王EP2')  # 不带空格才能搜到  # get_number_list('台湾SWAG-chloebabe-剩蛋特輯-幹爆小鹿')  # get_number_list('MD-0020')  # get_number_list('mds009')  # get_number_list('mds02209')  # get_number_list('女王的SM调教')  # get_number_list('91CM202')  # get_number_list('91CM-202')
