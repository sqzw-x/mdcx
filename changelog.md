## 新增

* 点击左下角可直接查看 daily_release
* 添加网站 javday
* 更灵活的图片裁剪工具

## 修复

* iqqtv, airav_cc
* 有道翻译
* Google Translate 混合标题和简介
* wiki 演员信息
* 日文演员名不进行繁简转换
* 其他错误修复

## 其他

由于本人最近较为繁忙, issue 和 PR 可能无法及时回应.

此外重申: 原则上不考虑加入新功能, 因此添加新网站等 issue 将被直接关闭, 请谅解.


<details>
<summary>Full Changelog</summary>

7cd1fbe fix: iqqtv ( #246), airav_cc (#251) (#264)
3950f99 fix: 有道翻译 (#261)
19ecef6 fix: wiki字段 (#260)
677884b fix: wiki fields (fix #255)
1cc1a88 fix: 图片裁剪同名时无法生成
928724b fix: close #237
9704c1d remove test
39c358a fix: google translate 混合多行文本
3c9638f fix: numpy 2.0 incompatibility(close #234)
1649b55 修复madouqu番号获取
cc3bf58 修复madouqu番号获取
7efda28 docs: 源码运行
b63509c fix: crawlers; logging; add referer header (#221)
daff178 fix: 番号后缀顺序允许设置分辨率 (close #204)
dff05d3 feat: 图片裁剪工具允许任意大小及位置 (close #203)
e89dc18 fix: 当演员名包含假名时不进行繁简转换; 更新 zhcdict.json (close #194)
58af476 CI: macos aarch64; allow workflow_disspatch (#199)
fb4262c Fix Issue 197 (#202)
e345697 chore: 完善番号官网映射 (#192)
8940684 feat: add website javday (#172)
f49516a fix: dont remove slash (close #165)
28432b1 CI: only delete before build
57ce07f CI: delete old daily build
ff818b9 fix: UI not set from config (#164)
5c9fcc9 fix: airavcc cover url relative path (close #157)
b39b85f CI: commit sha

</details>
