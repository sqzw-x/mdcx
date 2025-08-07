# 开发

## 环境准备

### 依赖

* [uv](https://docs.astral.sh/uv/getting-started/installation/)
* pnpm

### clone

```bash
git clone https://github.com/sqzw-x/mdcx.git
cd mdcx
uv sync --all-extras --dev
uv run pre-commit install
uv pip install -e .
```

## Run

启动 qt 版本

```bash
uv run main.py
```

启动 web server

```bash
# 构建前端
cd ui && pnpm i && pnpm build && cd ..

# Windows
$env:MDCX_DEV=1; uv run server.py

# Linux/macOS
MDCX_DEV=1 uv run server.py
```

## Test

Python 侧使用 pytest

```bash
uv run pytest
```

## 如何添加新配置项

1. 在 `mdcx/config/manager.py` `ConfigSchema` 类中添加配置键及默认值, 支持 str, int, float, bool 类型
2. 通过 `from mdcx.models.config.manager import config` 导入配置, 并通过 `config.<key>` 访问配置项
3. 按下一节所述在设置界面中添加对应的控件, 修改 `mdcx/controllers/main_window/` 目录下 `load_config.py` 及 `save_config.py`, 以实现 UI 绑定

## 如何修改图形界面

* `mdcx/views/MDCx.ui` 定义了主窗口, `mdcx/views/posterCutTool.ui` 是图片裁剪窗口, 可使用 Qt Designer 或 Qt Creator 编辑
* 修改后运行 `./scripts/pyuic.sh` 生成对应的 Python 代码
* 如需设置控件事件等, 需修改 `mdcx.controllers.main_window.init.Init_Singal`
* 所有事件处理函数均在 `mdcx/controllers/main_window/main_window.py` 及 `mdcx/controllers/main_window/handlers.py`

## 代码结构说明

```bash
mdcx
├── mdcx # 源代码目录
│   ├── config # 配置管理
│   ├── controllers # Qt UI 控制器
│   │   └── main_window
│   ├── crawlers # 各网站爬虫
│   ├── models # 业务逻辑
│   │   ├── base
│   │   ├── core
│   │   └── tools
│   ├── server # Web server
│   │   ├── api
│   │   │   └── v1
│   │   └── ws
│   ├── utils
│   └── views # Qt UI 定义
├── scripts # 开发/构建脚本
│   ├── build.sh # 构建 Qt 版本
│   ├── changelog.sh # 生成变更日志模板
│   └── pyuic.sh # 从 Qt UI 生成 Python 代码
├── tests # 测试
└── ui # WebUI 前端
    ├── dist # 构建结果
    └── src
```
