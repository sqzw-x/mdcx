# MDCx

![python](https://img.shields.io/badge/Python-3.9-3776AB.svg?style=flat&logo=python&logoColor=white)

## 上游项目

* [yoshiko2/Movie_Data_Capture](https://github.com/yoshiko2/Movie_Data_Capture): CLI 工具,
  开源版本现已不活跃, 新版本已闭源商业化.
* [moyy996/AVDC](https://github.com/moyy996/AVDC): 上述项目早期的一个 Fork, 使用 PyQt 实现了图形界面, 已停止维护
* @Hermit/MDCx: AVDC 的 Fork, 一度在 [anyabc/something](https://github.com/anyabc/something/releases) 分发源代码及可执行文件.
* 2023-11-3 @anyabc 因未知原因销号删库, 其分发的最后一个版本号为 20231014.

向相关开发者表示敬意.

## 关于本项目

* 本项目基于 @Hermit/MDCx, 对代码进行了大幅的重构与拆分, 以提高可维护性
* MacOS 版本为自动构建, 不保证可用性
* 尽管重构了大部分代码, 但由于代码耦合度仍然很高, 可维护性很差, 因此仅修复 bug, 不考虑加入新功能
* 当然如果直接 PR 也可以

## 构建

> 一般情况请勿自行构建, 至 [Release](https://github.com/sqzw-x/mdcx/releases) 下载最新版

#### Windows 7

Windows 7 上需使用 Python 3.8 构建, 代码及依赖均兼容, 可在本地自行构建. 也可使用 GitHub Actions 构建:

1. fork 本仓库, 在仓库设置中启用 Actions
2. 参考 [为存储库创建配置变量](https://docs.github.com/zh/actions/learn-github-actions/variables#creating-configuration-variables-for-a-repository), 设置 `BUILD_FOR_WINDOWS_LEGACY` 变量, 值非空即可
3. 在 Actions 中手动运行 `Build and Release`

#### macOS

低版本 macOS: 需注意 opencv 兼容性问题, 参考 [issue #82](https://github.com/sqzw-x/mdcx/issues/82#issuecomment-1947973961).
也可使用 GitHub Actions 构建, 步骤同上, 需设置 `BUILD_FOR_MACOS_LEGACY` 变量, 值非空即可;
以及 `MACOS_LEGACY_CV_VERSION` 变量, 值为兼容的 `opencv-contrib-python-headless` 版本

ARM64(AArch64) 架构: 可本地构建. 若欲使用 GitHub Actions 构建, 需 [添加自托管的运行器](https://docs.github.com/zh/actions/hosting-your-own-runners/managing-self-hosted-runners/adding-self-hosted-runners),
并设置 `SELF_HOSTED_MACOS_ARM64_RUNNER` 变量

## 开发

### 环境准备
- python 3.9
- Windows 10/11
- macOS 10.15.7+

### 准备源码
- 方式1: 下载 [仓库源码](https://github.com/sqzw-x/mdcx/archive/refs/heads/master.zip) 或 [Release源码](https://github.com/sqzw-x/mdcx/archive/refs/tags/daily_release.zip)，下载后解压
- 方式2: git克隆项目
  ```bash
  git clone https://github.com/sqzw-x/mdcx.git
  ```

### 运行
#### Windows

- cmd
```batch
cd /d D:\dev\mdcx
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=.\src;%PYTHONPATH%
python main.py
```

- powershell
```powershell
cd D:\dev\mdcx
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "./src;$env:PYTHONPATH"
python main.py
```

#### macOS

```bash
cd /path/to/mdcx
python -m venv venv
source venv/bin/activate
pip install -r requirements-mac.txt
export PYTHONPATH=./src:$PYTHONPATH
python main.py
```

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