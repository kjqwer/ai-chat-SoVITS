#!/usr/bin/env python3
"""
FunASR测试示例
演示如何使用ASR模块进行语音识别
"""

import sys
import os
import asyncio
import requests
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from asr import ASREngine


async def test_asr_engine():
    """测试ASR引擎"""
    print("=== 测试 ASR 引擎 ===")
    
    # 创建ASR引擎
    engine = ASREngine()
    
    # 加载模型
    print("正在加载模型...")
    success = engine.load_model()
    if not success:
        print("❌ 模型加载失败")
        return
    
    print("✅ 模型加载成功")
    
    # 获取模型信息
    info = engine.get_model_info()
    print(f"模型信息: {json.dumps(info, ensure_ascii=False, indent=2)}")
    
    # 测试音频文件识别（如果有测试音频文件）
    test_audio_path = Path(__file__).parent / "test_audio.wav"
    if test_audio_path.exists():
        print(f"正在识别音频: {test_audio_path}")
        result = engine.recognize_audio_file(test_audio_path)
        print(f"识别结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    else:
        print("⚠️ 未找到测试音频文件")
    
    # 卸载模型
    engine.unload_model()
    print("✅ 模型已卸载")


def test_api_endpoints():
    """测试API端点"""
    print("\n=== 测试 API 端点 ===")
    
    base_url = "http://localhost:8000"
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/asr/health")
        print(f"健康检查: {response.status_code} - {response.json()}")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
        return
    
    # 测试获取模型信息
    try:
        response = requests.get(f"{base_url}/asr/model/info")
        print(f"模型信息: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"获取模型信息失败: {e}")
    
    # 测试加载模型
    try:
        response = requests.post(f"{base_url}/asr/model/load")
        print(f"加载模型: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"加载模型失败: {e}")
    
    # 测试支持的格式
    try:
        response = requests.get(f"{base_url}/asr/supported_formats")
        print(f"支持的格式: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"获取支持格式失败: {e}")


def create_test_audio():
    """创建测试音频文件（使用numpy生成简单音频）"""
    try:
        import numpy as np
        import soundfile as sf
        
        # 生成简单的测试音频（440Hz正弦波，1秒）
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.3 * np.sin(2 * np.pi * 440 * t)
        
        test_audio_path = Path(__file__).parent / "test_audio.wav"
        sf.write(test_audio_path, audio_data, sample_rate)
        print(f"✅ 创建测试音频文件: {test_audio_path}")
        return test_audio_path
        
    except ImportError:
        print("⚠️ 无法创建测试音频，请安装 numpy 和 soundfile")
        return None


async def test_websocket():
    """测试WebSocket连接"""
    print("\n=== 测试 WebSocket ===")
    
    try:
        import websockets
        import base64
        
        uri = "ws://localhost:8000/asr/ws"
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 发送加载模型请求
            await websocket.send(json.dumps({
                "type": "config",
                "load_model": True
            }))
            
            # 接收响应
            response = await websocket.recv()
            print(f"模型加载响应: {response}")
            
            # 如果有测试音频，发送音频数据
            test_audio_path = Path(__file__).parent / "test_audio.wav"
            if test_audio_path.exists():
                with open(test_audio_path, 'rb') as f:
                    audio_data = base64.b64encode(f.read()).decode()
                
                await websocket.send(json.dumps({
                    "type": "audio_data",
                    "data": audio_data,
                    "format": "wav",
                    "sample_rate": 16000
                }))
                
                # 接收识别结果
                result = await websocket.recv()
                print(f"识别结果: {result}")
            
    except ImportError:
        print("⚠️ 无法测试WebSocket，请安装 websockets")
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")


def main():
    """主函数"""
    print("🎤 FunASR 语音识别模块测试")
    print("=" * 50)
    
    # 检查依赖
    try:
        import funasr
        print("✅ FunASR 已安装")
    except ImportError:
        print("❌ FunASR 未安装，请运行: pip install funasr")
        return
    
    # 创建测试音频文件
    create_test_audio()
    
    # 测试ASR引擎
    asyncio.run(test_asr_engine())
    
    # 测试API端点
    test_api_endpoints()
    
    # 测试WebSocket
    asyncio.run(test_websocket())
    
    print("\n✅ 测试完成")


if __name__ == "__main__":
    main() 