#!/usr/bin/env python3
"""
测试 Ollama 翻译功能
使用方法：
1. 确保 Ollama 服务正在运行 (ollama serve)
2. 下载一个中文模型，例如：ollama pull qwen2.5:7b
3. 运行此脚本：python test_ollama_translation.py
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mdcx.config.models import Config, TranslateConfig
from mdcx.config.enums import Translator
from mdcx.config.computed import Computed
from mdcx.base.translate import ollama_translate


async def test_ollama_translation():
    """测试 Ollama 翻译功能"""
    print("🚀 开始测试 Ollama 翻译功能...")
    
    # 创建测试配置
    config = Config()
    config.translate_config = TranslateConfig(
        ollama_url="http://localhost:11434",
        ollama_model="qwen2.5:7b",
        ollama_prompt="请将以下文本翻译为{lang}。只输出翻译结果，不要任何解释。\n{content}",
        ollama_read_timeout=120,
        ollama_max_req_sec=0.5,
        ollama_max_try=3,
        ollama_temperature=0.3,
    )
    
    # 初始化计算配置
    computed = Computed(config)
    
    # 测试文本
    test_title = "美少女戦士セーラームーン"
    test_outline = "月野うさぎは普通の中学2年生。ある日、黒猫のルナと出会い、セーラームーンとして戦うことになる。"
    
    print(f"📝 测试标题: {test_title}")
    print(f"📝 测试简介: {test_outline}")
    print()
    
    try:
        # 检查模型是否可用
        print("🔍 检查 Ollama 模型是否可用...")
        is_available = await computed.ollama_client.check_model_available(config.translate_config.ollama_model)
        
        if not is_available:
            print(f"❌ 模型 {config.translate_config.ollama_model} 不可用")
            print("💡 请确保：")
            print("   1. Ollama 服务正在运行 (ollama serve)")
            print(f"   2. 已下载模型 (ollama pull {config.translate_config.ollama_model})")
            return False
        
        print(f"✅ 模型 {config.translate_config.ollama_model} 可用")
        print()
        
        # 执行翻译
        print("🔄 开始翻译...")
        translated_title, translated_outline, error = await ollama_translate(
            test_title, test_outline, "简体中文"
        )
        
        if error:
            print(f"❌ 翻译失败: {error}")
            return False
        
        print("✅ 翻译成功！")
        print(f"📖 翻译标题: {translated_title}")
        print(f"📖 翻译简介: {translated_outline}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False
    
    finally:
        # 清理资源
        await computed.ollama_client.close()


async def main():
    """主函数"""
    print("=" * 60)
    print("🧪 Ollama 翻译功能测试")
    print("=" * 60)
    
    success = await test_ollama_translation()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 测试通过！Ollama 翻译功能工作正常")
    else:
        print("💥 测试失败！请检查 Ollama 配置")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
