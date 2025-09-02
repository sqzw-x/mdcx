## 重大变更

* mdcx 现在使用 JSON 作为配置文件格式, 原 ini 配置可正常读取, 会被自动转换为 JSON;
ini 配置文件现在是只读的, 所有对配置的更改都将**仅写入 JSON 文件**
* mdcx 现在需要 Python 3.13.4 及以上版本, 因此不再支持 Windows 7
* 重构 `刮削网站` 配置逻辑
  * 移除 `优先使用官网数据` 选项, `official` 现在是一个普通的来源网站, 可在优先级设置中使用
  * 移除各字段的 `排除网站` 和 `刮削设置 (列出的网站, 尽量补全, 不单独刮削)` 选项
  * 旧配置将自动转换

## 新增

* ✨ 使用 LLM API 进行翻译; 支持任何兼容 OpenAI 接口的服务
* ✨ 全新的 crawler 框架, 并基于此重新实现 dmm/javdb 刮削器
* ✨ 支持使用浏览器请求 dmm digital 页面, 需要安装 Chrome 浏览器; 可在 `网络-网站设置` 中开启/关闭此功能

## 开发

* 彻底重构主要代码, 大大提升代码质量和可维护性
* 并发策略由多线程改为异步
* 使用 pydantic 进行配置管理
* 全面迁移到 Python 3.13
* 使用 pyproject.toml 和 uv 进行依赖管理
* 重构项目结构
* 添加 lint 规则, CI 流程和 pre-commit hook

<details>
<summary>Full Changelog</summary>

54b1481 CI: remove unused environment variable
cd79039 CI: 使用 220* 版本号创建正式发布
ca4dea3 Ready for version 220250903
512290a fix: 首个水印位置与设置不符 (fix #663)
9f526dd Ready for version 220250903
7382940 fix: 提高成功列表和剩余列表的读取效率, 避免访问文件系统 (fix #662)
89f9e9f chore: 使用 issue 选择模板链接
bbb4057 chore: update issue templates
25a47d6 chore: update issue templates
eb5bbd4 chore: update issue template
e943894 chore: 使用 issue 模板链接
959b8c7 chore: 移除 daily_release 链接
f22d99a Ready for version 220250902
bbcc987 fix: 未向 tag 中添加演员 (fix #661)
dda0432 refactor: 精简参数; 优化 nfo 输出逻辑
5e731ee dev: 添加 bump 和 changelog 脚本
4ecb46a fix: writelines does not add newlines (fix #660)
cff48e2 Ready for version 220250901
c7f7e80 fix: 在 Windows 上以管理员权限运行时启动 Chrome 失败 (fix #640)
9df00a3 update lock file
17b211b fix: 提高最低 Python 版本至 3.13.4 以支持 os.path.ALLOW_MISSING (fix #654)
46ef20a fix: 无法判断失败情况 (#656)
42f8076 chore: 替换废弃的 thread getName 为 name 属性
a6e0392 fix: 检查 remain/success.txt 中路径有效性 (fix #654)
f3e5561 fix: 使用 None 代替 Path() 作为空值 (fix #648)
bc1e092 chore: 调整部分默认设置
1cfdc63 fix: 切换配置文件目录 (#648)
77a6ba9 Ready for version 220250832
61bed85 fix: 初始化部分加锁
80028f6 fix: cli tool
39458c1 fix: dmm digital parser
f325daa Ready for version 220250831
40ed706 fix: emby url end slash
b0123d8 fix: 无法补全头像
203732c Ready for version 220250830
44f2088 fix: 使用 removesuffix 替换 re.sub
d3d8dc9 fix: 正确填充 year 字段
8a994a4 fix: 移除下载图片时的冗余检查
a480ec5 fix: 发生异常时正确关闭浏览器页面; 改进异常处理
2b7659b update changelog; fix 拒绝未知的 delete Path('.') 调用
a7c9793 Ready for version 220250829
f69f94b fix: 图片裁剪导致崩溃
18ed067 fix: 使用枚举配置项
55ddff3 fix: 配置无法另存为
7a0a2b5 fix: 移除无用的网络配置项; 优化配置出错时的处理 (fix #634)
90180b1 fix: patchright 依赖项未打包
0d1f25f fix: config API 改为使用 JSON 格式
f968082 fix: 另存为功能改为 JSON 格式
2cf3afa fix: 删除不存在文件时忽略异常; 提前过滤忽略目录; 使 os.walk 非阻塞
3291476 fix: 正确跳过忽略的目录
9238ff1 fix: 全角分隔符识别
ae60318 Ready for version 220250826
4bec690 chore: 调整项目结构; 修复 bug (#631)
c7863ae refactor!: 使用 pathlib 处理路径
287adb1 fix: website_youma 转换; 保存配置后重新加载
e645f9d chore: fix test
9838a89 feat!: add browser & migrate to pydantic config (#622)
252d392 fix: mono multi line outline (fix #599)
243d6ae Ready for 2.0-beta-8
b566511 fix: 缺少某些 | 分隔字段
e012654 chore: 用字段名区分 | 分隔的字符串列表
4e81aad feat!: 使用 pydantic model 和 json 格式配置文件 (#587)
0db76b2 chore: 允许 crawl 调用多个 site
7fe78de update .gitignore
a7fc17f fix: get_filesize may raise exception (#593) (fix #571)
64d5dbf fix: 仅保留必要字段以避免 Pydantic 验证失败
1d7650f fix: v1 crawler return list or str (fix #585)
a88df37 Ready for 2.0-beta-7
1b309b7 fix: 未能正确处理 v1 crawler 返回结果 (fix #581)
a7a3e35 fix: all_actors 不全时未能使用 actors 补全; 统一二者的后处理 (fix #583 #582)
ac5419f feat: 尝试生成 aws image url (fix #584)
dc2e123 Ready for 2.0-beta-6
8844975 fix: aws image; 优化 crawl 日志输出
a0e8f43 feat!: 新的 crawler 框架; 重新实现 dmm/javdb (#574)
104e5f7 fix: 无 all_actor 字段时应从 actor 获取 (fix #565)
bedc22f Ready for 2.0-beta-5
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
