#!/usr/bin/env python3
"""
FunASR命令行工具
用于测试语音识别功能
"""

import argparse
import sys
import json
from pathlib import Path

from .asr_engine import ASREngine


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="FunASR语音识别命令行工具")
    parser.add_argument("audio_file", help="音频文件路径")
    parser.add_argument("--model", default="iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch", 
                       help="ASR模型名称")
    parser.add_argument("--output", "-o", help="输出结果到文件")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="输出格式")
    
    args = parser.parse_args()
    
    # 检查音频文件
    audio_path = Path(args.audio_file)
    if not audio_path.exists():
        print(f"错误: 音频文件不存在: {audio_path}", file=sys.stderr)
        sys.exit(1)
    
    # 创建ASR引擎
    print(f"正在初始化ASR引擎，模型: {args.model}")
    asr_engine = ASREngine(args.model)
    
    # 加载模型
    print("正在加载模型...")
    if not asr_engine.load_model():
        print("错误: 模型加载失败", file=sys.stderr)
        sys.exit(1)
    
    # 识别音频
    print(f"正在识别音频: {audio_path}")
    result = asr_engine.recognize_audio_file(audio_path)
    
    # 格式化输出
    if args.format == "json":
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        if result["success"]:
            output = result["text"]
        else:
            output = f"识别失败: {result.get('error', '未知错误')}"
    
    # 输出结果
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"结果已保存到: {args.output}")
    else:
        print("\n识别结果:")
        print(output)
    
    # 清理
    asr_engine.unload_model()


if __name__ == "__main__":
    main() 