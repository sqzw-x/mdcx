# MDCx

![python](https://img.shields.io/badge/Python-3.9-3776AB.svg?style=flat&logo=python&logoColor=white)

## 上游项目

* [yoshiko2/Movie_Data_Capture](https://github.com/yoshiko2/Movie_Data_Capture): CLI 工具,
  开源版本现已不活跃, 新版本已闭源商业化.
* [moyy996/AVDC](https://github.com/moyy996/AVDC): 上述项目早期的一个 Fork, 使用 PyQt 实现了图形界面, 已停止维护
* @Hermit/MDCx: AVDC 的 Fork, 一度在 [anyabc/something](https://github.com/anyabc/something/releases) 分发源代码及可执行文件.
* 2023-11-3 @anyabc 因未知原因销号删库, 其分发的最后一个版本号为 20231014.
* 本项目基于 @Hermit/MDCx, 对代码进行了大幅的重构与拆分, 以提高可维护性

向相关开发者表示敬意.

## 构建

> 一般情况请勿自行构建, 至 [Release](https://github.com/sqzw-x/mdcx/releases) 下载最新版

### Windows 7

> 即将放弃对 Windows 7 的支持. [#494](https://github.com/sqzw-x/mdcx/issues/494)

Windows 7 上需使用 Python 3.8 构建, 代码及依赖均兼容, 可在本地自行构建. 也可使用 GitHub Actions 构建:

1. fork 本仓库, 在仓库设置中启用 Actions
2. 参考 [为存储库创建配置变量](https://docs.github.com/zh/actions/learn-github-actions/variables#creating-configuration-variables-for-a-repository), 设置 `BUILD_FOR_WINDOWS_LEGACY` 变量, 值非空即可
3. 在 Actions 中手动运行 `Build and Release`

### macOS

低版本 macOS: 需注意 opencv 兼容性问题, 参考 [issue #82](https://github.com/sqzw-x/mdcx/issues/82#issuecomment-1947973961).
也可使用 GitHub Actions 构建, 步骤同上, 需设置 `BUILD_FOR_MACOS_LEGACY` 变量, 值非空即可;
以及 `MACOS_LEGACY_CV_VERSION` 变量, 值为兼容的 `opencv-contrib-python-headless` 版本

## 授权许可

本插件项目在 GPLv3 许可授权下发行。此外，如果使用本项目表明还额外接受以下条款：

* 本项目仅供学习以及技术交流使用
* 请勿在公共社交平台上宣传此项目
* 使用本软件时请遵守当地法律法规
* 法律及使用后果由使用者自己承担
* 禁止将本软件用于任何的商业用途
