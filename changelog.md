## 重要
此版本移除了 cloudscraper, 并将 curl-cffi 升级至 0.6.0b9.  

这一改动旨在解决 curl 请求出现的相关问题, 但并未经过充分测试.
若网络请求出现问题, 可暂回退至 120240207 版本, 并提交 issue.

现在代码及依赖完全兼容 python 3.8, 可以使用 python 3.8 构建以在 Windows 7 上运行.
由于二者均已停止支持, 因此并不提供官方构建.
## 新增
* UI: hscangku & cableav 指定网站刮削
* macos img 构建 by @
## 修复
* dmm 搜索页标题 xpath
* 裁剪图片 - 打开图片 处理结果保存至影片目录

<details>
<summary>Full Changelog</summary>

15a06ba feat(web)!: del cloudscraper; bump curl-cffi to 0.6.0b9
ca38e46 fix(nfo): python3.8 unsupported with expression
b314755 fix(dmm): title xpath (#90)
edd43a4 CI: refine macos build
5af0b14 fix(dmm): wrong comment (#80)
9f2315a Fix: 裁剪图片保存至原目录 (#86)
eb8207b UI: 添加新网站; 移除 hdouban

</details>
