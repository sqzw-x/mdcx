## 修复

* fc2 cover/extrafanart URL
* 获取 gfriends 数据失败
* regression: CrawlersResult 未正确设置 number 字段
* regression: 未能正确从所有来源聚合某些字段

## 开发

* 全面迁移到 python3.13
* 使用 pyproject.toml 和 uv 进行依赖管理
* 重构项目结构
* 使用 dataclass 替代 TypedDict
* 添加更多 type hints
* 添加 lint 规则及 CI 流程和 pre-commit hook

<details>
<summary>Full Changelog</summary>

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
