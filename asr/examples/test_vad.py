"""
Silero VAD 测试示例
演示如何使用VAD功能进行语音活动检测
"""

import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import numpy as np
import soundfile as sf
from asr.vad_engine import SileroVAD
from asr.asr_engine import ASREngine
from asr.config import ASRConfig

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_vad_basic():
    """基础VAD测试"""
    print("=" * 50)
    print("基础VAD测试")
    print("=" * 50)
    
    try:
        # 创建VAD实例
        vad = SileroVAD(model_type="silero_vad", device="auto")
        
        # 加载模型
        if not vad.load_model():
            print("❌ VAD模型加载失败")
            return False
        
        print("✅ VAD模型加载成功")
        
        # 创建测试音频（1秒的正弦波）
        sample_rate = 16000
        duration = 3.0  # 3秒
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # 创建包含语音和静音的测试音频
        # 前1秒：静音
        # 中间1秒：模拟语音（正弦波）
        # 后1秒：静音
        audio = np.zeros_like(t)
        speech_start = int(sample_rate * 1.0)
        speech_end = int(sample_rate * 2.0)
        audio[speech_start:speech_end] = 0.5 * np.sin(2 * np.pi * 440 * t[speech_start:speech_end])
        
        # 保存测试音频
        test_audio_path = "test_audio.wav"
        sf.write(test_audio_path, audio, sample_rate)
        print(f"✅ 创建测试音频: {test_audio_path}")
        
        # 进行VAD检测
        segments = vad.process_audio_file(test_audio_path)
        
        print(f"\n检测结果:")
        print(f"检测到 {len(segments)} 个语音片段")
        
        for i, segment in enumerate(segments):
            print(f"片段 {i+1}: {segment['start']:.2f}s - {segment['end']:.2f}s (时长: {segment['duration']:.2f}s)")
        
        # 清理
        try:
            os.unlink(test_audio_path)
        except:
            pass
        
        return True
        
    except Exception as e:
        logger.error(f"VAD基础测试失败: {e}")
        return False


def test_vad_with_real_audio():
    """使用真实音频文件测试VAD"""
    print("=" * 50)
    print("真实音频VAD测试")
    print("=" * 50)
    
    # 查找音频文件
    audio_files = []
    for ext in ['.wav', '.mp3', '.flac', '.m4a']:
        audio_files.extend(Path('.').glob(f'*{ext}'))
        audio_files.extend(Path('..').glob(f'*{ext}'))
    
    if not audio_files:
        print("⚠️ 未找到音频文件，跳过真实音频测试")
        return True
    
    audio_file = audio_files[0]
    print(f"使用音频文件: {audio_file}")
    
    try:
        vad = SileroVAD()
        if not vad.load_model():
            print("❌ VAD模型加载失败")
            return False
        
        # 检测语音片段
        segments = vad.process_audio_file(audio_file)
        
        print(f"\n检测结果:")
        print(f"文件: {audio_file}")
        print(f"检测到 {len(segments)} 个语音片段")
        
        total_duration = sum(seg['duration'] for seg in segments)
        print(f"总语音时长: {total_duration:.2f}秒")
        
        for i, segment in enumerate(segments):
            print(f"片段 {i+1}: {segment['start']:.2f}s - {segment['end']:.2f}s (时长: {segment['duration']:.2f}s)")
        
        return True
        
    except Exception as e:
        logger.error(f"真实音频VAD测试失败: {e}")
        return False


def test_asr_with_vad():
    """测试VAD集成的ASR功能"""
    print("=" * 50)
    print("VAD集成ASR测试")
    print("=" * 50)
    
    try:
        # 创建配置，启用VAD
        config = ASRConfig()
        config.config["vad"]["enabled"] = True
        config.config["vad"]["pre_process"] = True
        config.config["vad"]["return_segments"] = True
        
        # 创建ASR引擎
        asr = ASREngine(config=config)
        
        print(f"VAD启用状态: {asr.vad_enabled}")
        print(f"VAD配置: {asr.vad_config}")
        
        # 查找音频文件
        audio_files = []
        for ext in ['.wav', '.mp3', '.flac', '.m4a']:
            audio_files.extend(Path('.').glob(f'*{ext}'))
            audio_files.extend(Path('..').glob(f'*{ext}'))
        
        if not audio_files:
            print("⚠️ 未找到音频文件，跳过ASR+VAD测试")
            return True
        
        audio_file = audio_files[0]
        print(f"使用音频文件: {audio_file}")
        
        if asr.vad_enabled:
            # 测试VAD分段识别
            result = asr.recognize_with_vad(audio_file)
            
            print(f"\nVAD+ASR识别结果:")
            print(f"成功: {result.get('success', False)}")
            print(f"文本: {result.get('text', '')}")
            print(f"置信度: {result.get('confidence', 0):.2f}")
            print(f"VAD片段数: {result.get('vad_segments', 0)}")
            print(f"识别片段数: {result.get('recognized_segments', 0)}")
            print(f"处理方法: {result.get('processing_method', 'unknown')}")
            
            if result.get('detailed_results'):
                print("\n详细分段结果:")
                for segment in result['detailed_results']:
                    print(f"  片段 {segment['segment_id']}: {segment['start']:.2f}s-{segment['end']:.2f}s | {segment['text']}")
        
        return True
        
    except Exception as e:
        logger.error(f"VAD集成ASR测试失败: {e}")
        return False


def test_vad_splitting():
    """测试VAD音频分割功能"""
    print("=" * 50)
    print("VAD音频分割测试")
    print("=" * 50)
    
    try:
        # 查找音频文件
        audio_files = []
        for ext in ['.wav', '.mp3', '.flac', '.m4a']:
            audio_files.extend(Path('.').glob(f'*{ext}'))
            audio_files.extend(Path('..').glob(f'*{ext}'))
        
        if not audio_files:
            print("⚠️ 未找到音频文件，跳过音频分割测试")
            return True
        
        audio_file = audio_files[0]
        print(f"使用音频文件: {audio_file}")
        
        vad = SileroVAD()
        if not vad.load_model():
            print("❌ VAD模型加载失败")
            return False
        
        # 创建输出目录
        output_dir = Path("vad_output")
        output_dir.mkdir(exist_ok=True)
        
        # 分割音频
        split_files = vad.split_audio_by_vad(audio_file, output_dir)
        
        print(f"\n分割结果:")
        print(f"生成了 {len(split_files)} 个音频片段")
        
        for i, file_path in enumerate(split_files):
            file_size = os.path.getsize(file_path) / 1024  # KB
            print(f"  片段 {i+1}: {os.path.basename(file_path)} ({file_size:.1f} KB)")
        
        return True
        
    except Exception as e:
        logger.error(f"VAD音频分割测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🎤 Silero VAD 功能测试")
    print("=" * 60)
    
    tests = [
        ("基础VAD功能", test_vad_basic),
        ("真实音频VAD", test_vad_with_real_audio),
        ("VAD集成ASR", test_asr_with_vad),
        ("VAD音频分割", test_vad_splitting),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 运行测试: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ 通过" if success else "❌ 失败"
            print(f"测试结果: {status}")
        except Exception as e:
            logger.error(f"测试 {test_name} 出现异常: {e}")
            results.append((test_name, False))
            print(f"测试结果: ❌ 异常")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")
    
    print(f"\n总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有VAD功能测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查配置和依赖")


if __name__ == "__main__":
    main() 