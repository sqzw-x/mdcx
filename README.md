# MDCx

![python](https://img.shields.io/badge/Python-3.9-3776AB.svg?style=flat&logo=python&logoColor=white)

## 项目缘由

* 一切的起源是 [yoshiko2/Movie_Data_Capture](https://github.com/yoshiko2/Movie_Data_Capture), 这是一个 CLI 工具,
  开源版本现已不活跃, 新版本已闭源商业化.

* [moyy996/AVDC](https://github.com/moyy996/AVDC) 是上述项目早期的一个 Fork, 使用 PyQt 实现了图形界面, 但早已无人维护.

* 在 AVDC 基础上, @Hermit 开发并维护了 MDCx 项目,
  并通过 [anyabc/something](https://github.com/anyabc/something/releases) 仓库的 release 分发源代码及可执行文件.

* 2023.11.3 月, @anyabc 因未知原因销号删库, 其分发的最后一个版本号为 20231014.

向以上相关开发者表示敬意.

## 关于本项目

* 本项目基于 MDCx, 从功能而言并无变化, 不过对代码进行了大幅的重构与拆分, 以提高可维护性
* 由于我没有 MacOS 设备, 因此无法提供相应平台的二进制构建及打包脚本
* 尽管重构了大部分代码, 但由于代码耦合度仍然很高, 可维护性很差, 因此仅修复 bug, 不考虑加入新功能
* 当然如果直接 PR 也可以

## 开发相关

项目环境为 Python 3.9. 以下内容可能有助于理解及修改代码.

### 打包

安装 `pyinstaller` 后运行 `build.ps1`, 打包文件在 `dist` 目录下

### 如何添加新配置项

1. 在 `config.ini.default` 中添加配置项及其默认值, 值类型可以是字符串, 整数, 浮点数
2. 如果此值非字符串, 在 `src/models/config/config_manual.py` 中将配置键加入 `INT_KEY` 或 `FLOAT_KEY` 中
3. 修改 `src/models/config/config_generator.py` 中的 `CONFIG_STR`, 这用于生成默认配置文件
4. 修改 `src.models.config.config.MDCxConfig.save_config` 方法, 将新配置项加入模板字符串中, 这用于保存配置文件
5. 运行 `src/models/config/config_generator.py`, 这将更新 `src/models/config/config_generated.py`
6. 现在可以通过 `from models.config.config import config` 导入配置, 并通过 `config.<key>` 获取对应值, 且支持 IDE 补全
7. 按下一节所述在设置界面中添加对应的控件
8. 修改 `src/controllers/main_window/` 目录下 `load_config.py` 及 `save_config.py`, 以实现与图形界面的交互

### 如何修改图形界面

* `src/views/MDCx.ui` 定义了主窗口, `src/views/posterCutTool.ui` 是图片裁剪窗口, 可使用 Qt Designer 或 Qt Creator 编辑
* 修改后运行 `pyuic5 src\views\MDCx.ui -o src\views\MDCx.py` 生成对应的 Python 代码
* 如需设置控件事件等, 需修改 `src.controllers.main_window.init.Init_Singal`
* 所有事件处理函数均在 `src/controllers/main_window/main_window.py`

### 代码结构说明

* `src/models` 中包括全部业务逻辑, 其中:
* `config` 目录包括配置管理相关的代码
* `base` 目录包括基本的功能函数, 它们耦合度较低
* `core` 包括核心功能实现, 其中 `scraper.py` 包括刮削过程的实现
* `signals.py` 包括 Qt 信号量, 这是 MC 解耦的关键, 它也负责日志打印
* `config` 和 `signal` 是预定义的单例, 可以在任何位置导入使用
* `views` 和 `controllers` 结构相对简单, 可参考上文说明