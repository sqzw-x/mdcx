## 修复

* 运行时异常 TypeError: 'module' object is not callable
* llm_max_req_sec 除零异常
* 读取模式 has_nfo_update 选项行为不正确
* 不移动文件时未按模板渲染文件名称

<details>
<summary>Full Changelog</summary>

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
cbaa181 format
09bef3c feat: add and update some config; bug fix (#476)
050cca9 feat: add workflow to close stale issues
b75fdbf fix: 人名繁简转换可能导致错误 (close #477)
6678740 fix: yesjav url changed (close #488)
103af12 fix: cut_pic close image
6fc157d fix: image may not be closed properly (fix #481)
f6eea9d chore: update mapping_actor.xml (#480)
ae2ef17 bug fix and refactor (#475)

</details>
