# ⚠️ 注意: 此版本与旧版本的配置文件不兼容, 使用此版本保存的配置文件将无法在旧版本中使用, 请备份配置文件后再升级, 并且不要用新版本加载备份文件

## 新增

- 刮削过程可以立刻创建软链接
- DMM 2K分辨率的横版封面 (#301)
- 数据源 fc2ppvdb (#401)
- 更新内置演员映射表

## 修复

- wiki 获取演员信息失败
- DMM 四位数番号只需补零到五位
- 无法根据文件大小进行清理
- 裁剪图片路径未清空
- fc2hub, javday 默认 url
- 若干 DMM 失效问题

## 开发相关

- 在 MacOS 上从源代码运行时将读取项目目录下的 `MDCx.config` 文件, 与 Windows 上的行为一致, 不再读取 `~/.mdcx/MDCx.config`. 打包后行为未发生变化. 这可以有效隔离开发环境的配置文件.
- 增加配置项更容易了, 详见 `readme`

<details>
<summary>Full Changelog</summary>

2135104 CI: 构建流程优化和依赖升级 (#424)
2d3b7bd CI: 添加脚本权限; 修复 mac 构建脚本
3830a21 refactor: 优化配置路径管理
7890018 fix: get_mac_default_config_folder
416ce08 fix: 通过 config 访问 manager 上的字段
03919a9 fix: 无法正确根据文件大小进行清理
7e8f0c3 fix(web): typo
4befead fix: 网络检测异常日志
624b420 fix: missing import (fix #423)
b105bcf 修正 xml 格式错误，增加注释 (#421)
77474fa feat!:优化配置管理与UI绑定 (#420)
f976f92 更新：mapping_actor.xml 去重，更新，修正 (#418)
f1f83f8 fix: get actor info from wiki (fix #415)
5aa9946 feat: add website fc2ppvdb (#401)
9d55e2a fix: dmm 四位数序号只需补零到五位 (close #393)
d609557 fix: Logbuffer 未释放 (#375)
34c89ab fix: 默认使用 opencv 获取分辨率, 否则使用 ffprobe
5e033b3 fix: adjust subprocess flags for cross-platform compatibility in get_video_size function
b35ef5b fix(file): 移动失败文件时不能移动到父/祖先目录 (fix #251)
dea801e refactor! (#372)
90c1a43 fix: dmm xpath; 检测高清图片 url 是否有效; 修复Dmm搜索 (#357)
edb8fbc fix: dmm cover download (#356)
1f30c32 feat: pyupgrade
b36e607 fix(config): 避免 ruff 格式化生成的代码; 生成代码尽量符合规范
540b35b style: use ruff to format code
4285f0b style: use pyupgrade
602d195 add: build with uv venv
f4e03d3 chore: 移除无用文件
89e1df1 fix: change pic_title_list xpath (#315)
ecc04b0 fix: dmm.py empty main block (#305)
f5b4261 feat: DMM 2K分辨率的横版封面 (#301)
4da2048 docs: 授权许可 (#298)
1cd7fad feat: 刮削过程中立刻创建软链接
667f106 fix: race
5de2804 chore: format
7c9d183 opt: 创建软链接时不对网络文件进行有效性检查
afcbf85 fix: 裁剪图片路径未清空
b07bfa1 fix: unexpected exceptions
50a8eec fix: fc2hub, javday url (fix#265)

</details>
