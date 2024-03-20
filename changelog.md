## 重要

### [每日构建](https://github.com/sqzw-x/mdcx/releases/tag/daily_release)

在此版本后, mdcx 将**降低**版本号变化频率, 版本号基本只用来处理会破坏配置文件兼容性的变更.
一般的功能更新与 bug 修复均通过 Github actions 每日构建, 可在上述链接下载.
发布页将显示最后一次提交时间, 时区为 UTC+0, 对应北京时间 +8h 即可.

得益于此, 任何代码提交均将在 24h 内被发布, 因此总是可以获取到最新版本.
代价是每日构建 **_不会在软件内提示更新_**, 需要手动前往上述页面查看.

除此之外, 请注意此后 **任何 issue 报告均需要包含提交 hash**, 这基本上取代了原来版本号的功能, 文件名中将自动包含提交 hash

## 新增

* 单文件刮削自动选择网站 by @
* 可设置刮削完成后自动创建 kodi actor 目录及自动创建软链接

## 修复

* madouqu year 获取
* iqqtv url
* 未知演员写入 nfo

<details>
<summary>Full Changelog</summary>

26af362 fix: write unknown actor to nfo (close #151)
a175c97 CI: fix daily release tag
bab46d7 CI: fix release.yml
96ee83b feat: 刮削完成后 自动创建actor目录 及 自动创建软链接 (close #142)
761db21 CI: daily release time
7ed3531 CI: daily release tag and log
7099844 feat: single file scraping without site selection
60122f1 CI: daily build
5b60511 chore
e4d7c7a fix: iqqtv default url (close #134)
e70294b fix(madouqu): year字段类型；处理失败时返回空值 (#129)

</details>
