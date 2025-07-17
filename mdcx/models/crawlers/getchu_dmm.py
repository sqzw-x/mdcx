#!/usr/bin/env python3


from mdcx.models.crawlers import dmm, getchu


async def main(
    number,
    appoint_url="",
    file_path="",
    **kwargs,
):
    json_data_getchu = await getchu.main(number, appoint_url)
    json_data_new = json_data_getchu["getchu"]["jp"]

    poster = json_data_new.get("poster")
    outline = json_data_new.get("outline")
    if json_data_new["title"]:
        number = json_data_new["number"]
        if number.startswith("DLID") or "dl.getchu" in appoint_url:
            return json_data_getchu
    json_data_dmm = await dmm.main(number, appoint_url, file_path)
    if json_data_dmm["dmm"]["jp"]["title"]:
        json_data_new.update(json_data_dmm["dmm"]["jp"])
        if poster:  # 使用 getchu 封面
            json_data_new["poster"] = poster
        if outline:  # 使用 getchu 简介
            json_data_new["outline"] = outline
            json_data_new["originalplot"] = outline
    return {
        "getchu_dmm": {
            "zh_cn": json_data_new,
            "zh_tw": json_data_new,
            "jp": json_data_new,
        }
    }


if __name__ == "__main__":
    # yapf: disable
    # print(main('コンビニ○○Z 第三話 あなた、ヤンクレママですよね。旦那に万引きがバレていいんですか？'))
    # print(main('[PoRO]エロコンビニ店長 泣きべそ蓮っ葉・栞～お仕置きじぇらしぃナマ逸機～'))
    # print(main('ACHDL-1159'))
    # print(main('好きにしやがれ GOTcomics'))    # 書籍，没有番号 # dmm 没有
    # print(main('ACMDP-1005')) # 有时间、导演，上下集ACMDP-1005B
    # print(main('ISTU-5391'))    # dmm 没有
    # print(main('INH-392'))
    # print(main('OVA催眠性指導 ＃4宮島椿の場合')) # 都没有
    # print(main('OVA催眠性指導 ＃5宮島椿の場合')) # 都没有
    # print(main('GLOD-148')) # getchu 没有
    # print(main('(18禁アニメ) (無修正) 紅蓮 第1幕 「鬼」 (spursengine 960x720 h.264 aac)'))
    print(main('誘惑 ～始発の章～'))  # print(main('ISTU-5391', appoint_url='http://www.getchu.com/soft.phtml?id=1180483'))  # print(main('SPY×FAMILY Vol.1 Blu-ray Disc＜初回生産限定版＞'))    # dmm 没有
