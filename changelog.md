## 新增

*

## 修复

* fc2hub 图片 URL
* 多版本视频刮削失败
* 男演员信息丢失
* 临时解决 dmm digital 无法爬取, 在搜索结果中降低其优先级

<details>
<summary>Full Changelog</summary>

cd52f02 合并 digital 和 video 类别
f8b779e fix: 降低 dmm ditigal 优先级 (#549)
2828565 feat: crawl cli
444eefd feat: config get_website_base_url
0b1ccef CI: add v1 release workflow to master
aa45e97 add dmm video parser
c5d98d4 fix: 未能正确 reduce all_actor 字段 (fix #554)
1baa6b7 new cralwer & parser
2931b52 chore: update CONTRIBUTING.md
357a637 fix: is_server 不起作用
2eb530b chore: 避免不必要的环境变量检查
c39ac4c chore: 允许使用 pip install -e . 安装
bd5b67e chore: 避免 config/models.py 对 manager.py 的依赖
63cf39b chore: add vscode settings for projects and workspace
2ff35dc feat: server & webui 基础实现 (#540)
4ce9def remove ui
2c6795c fix: 分集的 codec tag 重复 (fix #552)
81b36c3 fix: mosaic 初始值错误 (fix #550)
5fe4a1d fix: 多版本错误复用了 file_info (close #545)
a3fadf6 fix: fc2hub image URL (close #546)
2c43404 fix: 移除异步文件操作中的重试
3ee749e Ready for 2.0-beta-4
44f8bbc fix: 不移动文件时文件名称错误
0cdf98e fix: 文件操作多余的重试
fa52e71 fix: 读取模式 has_nfo_update 选项行为不正确 (close #539)
55a4f5c CI: run on review_requested, ready_for_review
7838c62 fix: str 名称冲突; llm_max_req_sec 可能为0 (close #538)
3c02ca6 CI: fix macos-latest not having x86 version
cff1cb4 CI: 使用 macos-latest x86_64 代替 macos-13 以解决 hdiutil: create failed - Resource busy
c739ad4 CI: debug 模式不清理构建过程中的临时文件
04c975f fix: missing socksio (fix #537)
65d726c dep: remove langid and opencv
3ae3294 CI: use run_command for subprocess calls
23a974a CI: fix not all arguments converted
7bb30ac CI: optmize build log
93decdd CI: fix windows color output; subprocess exception
67972b7 CI: fix windows encode error
a8db095 update uv.lock; remove useless files
745f799 CI: use build.py in CI
e791ea0 CI: 完善 build.py; 在 Windows 上验证
aca7ab8 CI: use python to build
ef912dc feat: add pyav for video metadata
cd688fd Ready for 2.0-beta-2
ab05ac3 fix: 未能正确从所有来源聚合某些字段
d15bd8b fix: CrawlersResult 未正确设置 number 字段
d0b7f19 doc: add uv sync and pre-commit install to CONTRIBUTING.md
d3ade91 CI: add lint workflow
077ac5a chore!: add ruff lint rules and fix lint errors
9b60a55 fix: not await _get_gfriends_actor_data (fix #524)
7b1df6e chore: add some type hints
fe3990c refactor: 区分 qt 和其它部分的 signal 调用
3d39257 chore
0c0ab31 update python to 3.13 in pyproject.toml; use uv for ci (#519)
a1a28cc refactor: move Flags.translate_by_list to config
ce39a16 chore: fix type errors
2f790c4 chore: rename extrafanart download function
b24ecf0 fix: fc2 extrafanart URL (fix #517)
ff175b5 chore: import
9c1b5cf fix: fc2 cover url (close #517)
cf1a837 fix: refactor break mac build script
d59ab45 fix: 主界面右侧标题多余的横线
2c10148 refactor: rename types and fix type check
8f7c553 remove typeddict definitions
28c4f83 refactor!: 消除所有 typeddict 并使用 dataclass 替代
2c0fe47 refactor: crawler 现在返回 dataclass
78de538 refactor: 移除 nfo_data country/website 字段; 为 crawler 结果创建 dataclass
5055df5 使用 CrawlTask dataclass 作为 crawler 输入
daf3cdd update README and add CONTRIBUTING.md
6bcd986 refactor!: 重组项目结构；初步消除 json data；添加 project.toml (#513)
72b2219 fix: missing return in_get_folder_path
1b2886f CI: fix github var
84b85e2 fix: cut_window (close #500)
3e829a3 CI: use input tag for release action
d62c32d CI: stop daily release
7593ea8 feat!: async & LLM translate (#463)

</details>
