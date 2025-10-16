# Ollama 本地大模型翻译功能

## 功能概述

MDCx 现在支持使用 Ollama 本地大模型进行翻译，这为用户提供了一个完全本地化的翻译解决方案，无需依赖外部 API 服务。

## 新增功能

### 1. 翻译服务选项
- 在翻译服务列表中新增了 "Ollama" 选项
- 支持与其他翻译服务（有道、谷歌、DeepL、LLM）混合使用
- 可以设置翻译优先级，Ollama 可以排在任意位置

### 2. Ollama 配置选项
- **Ollama API Host**: Ollama 服务地址（默认：http://localhost:11434）
- **Ollama 模型名称**: 要使用的模型名称（默认：qwen2.5:7b）
- **Ollama 提示词**: 翻译提示词模板（支持 {content} 和 {lang} 占位符）
- **Ollama 读取超时**: 请求超时时间（默认：120秒）
- **Ollama 每秒最大请求数**: 限流设置（默认：0.5）
- **Ollama 最大尝试次数**: 失败重试次数（默认：3）
- **Ollama 温度**: 生成随机性（默认：0.3）

## 使用方法

### 1. 安装和启动 Ollama

```bash
# 安装 Ollama（如果尚未安装）
# Windows: 下载安装包从 https://ollama.ai
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# 启动 Ollama 服务
ollama serve
```

### 2. 下载推荐模型

```bash
# 下载中文支持较好的模型（推荐）
ollama pull qwen2.5:7b

# 或者下载其他模型
ollama pull llama3.2:3b
ollama pull gemma2:9b
```

### 3. 配置 MDCx

1. 打开 MDCx 设置界面
2. 进入"翻译配置"部分
3. 在"翻译服务"中添加或调整 "Ollama" 的位置
4. 配置 Ollama 相关参数：
   - 确保 "Ollama API Host" 指向正确的地址
   - 设置 "Ollama 模型名称" 为已下载的模型
   - 根据需要调整其他参数

### 4. 测试翻译功能

运行测试脚本验证配置：

```bash
python test_ollama_translation.py
```

## 推荐模型

### 中文翻译推荐模型

1. **qwen2.5:7b** - 阿里通义千问，中文支持优秀
2. **qwen2.5:14b** - 更大版本，翻译质量更高
3. **llama3.2:3b** - Meta 模型，多语言支持
4. **gemma2:9b** - Google 模型，翻译质量好

### 模型选择建议

- **性能优先**: qwen2.5:7b, llama3.2:3b
- **质量优先**: qwen2.5:14b, gemma2:9b
- **资源受限**: qwen2.5:1.5b, llama3.2:1b

## 优势特点

### 1. 完全本地化
- 无需网络连接
- 数据隐私保护
- 无 API 费用

### 2. 高度可定制
- 支持自定义提示词
- 可调整生成参数
- 支持多种模型切换

### 3. 稳定可靠
- 不受外部服务影响
- 内置重试机制
- 模型可用性检查

## 故障排除

### 常见问题

1. **模型不可用**
   - 确保 Ollama 服务正在运行
   - 检查模型是否已下载
   - 验证模型名称是否正确

2. **翻译失败**
   - 检查网络连接（如果使用远程 Ollama）
   - 增加超时时间设置
   - 降低请求频率限制

3. **翻译质量不佳**
   - 尝试不同的模型
   - 调整温度参数
   - 优化提示词模板

### 调试方法

1. 查看 MDCx 日志输出
2. 运行测试脚本验证配置
3. 使用 Ollama CLI 测试模型：

```bash
# 测试模型是否工作
ollama run qwen2.5:7b "请翻译：Hello World"
```

## 技术实现

### 核心组件

1. **OllamaClient**: Ollama API 客户端
2. **ollama_translate**: 翻译接口函数
3. **配置集成**: 与现有配置系统无缝集成
4. **错误处理**: 完善的错误处理和重试机制

### API 兼容性

- 支持 Ollama API v1
- 兼容所有 Ollama 支持的模型
- 支持流式和非流式生成

## 更新日志

- **v2.0.0**: 新增 Ollama 本地大模型翻译支持
- 添加完整的配置选项
- 实现模型可用性检查
- 集成到现有翻译流程

## 贡献

欢迎提交 Issue 和 Pull Request 来改进 Ollama 翻译功能！

---

*注意：使用 Ollama 翻译需要本地安装 Ollama 服务并下载相应模型，首次使用可能需要较长时间下载模型文件。*
