# Silero VAD 集成说明

## 概述

GPT-SoVITS ASR模块现已集成 **Silero VAD**（语音活动检测）功能，可以自动检测音频中的语音片段，提高语音识别的准确性和效率。

## 功能特点

- ✅ **高精度检测**：基于深度学习的语音活动检测，优于传统VAD方法
- ✅ **轻量级模型**：模型仅1.8MB，快速加载
- ✅ **多种部署**：支持 PyTorch 和 ONNX 两种推理方式
- ✅ **灵活配置**：可调节检测阈值、最小语音时长等参数
- ✅ **无缝集成**：与现有ASR流程完美融合
- ✅ **多种接口**：提供HTTP API、Python API等多种调用方式

## 安装和配置

### 1. 自动安装
运行安装脚本会自动安装VAD依赖：
```bash
runtime\python.exe asr/install_runtime.py
```

### 2. 手动安装依赖
如果自动安装失败，可手动安装：
```bash
pip install torch>=1.11.0
pip install onnxruntime>=1.15.0
pip install torchaudio>=0.11.0
```

### 3. 配置VAD参数
编辑 `asr/config.json` 文件：
```json
{
  "vad": {
    "enabled": true,              // 是否启用VAD
    "engine": "silero",           // VAD引擎类型
    "model_type": "silero_vad",   // 模型类型
    "device": "auto",             // 设备: auto/cpu/cuda
    "threshold": 0.5,             // 语音检测阈值 (0-1)
    "min_speech_duration_ms": 250,   // 最小语音时长(毫秒)
    "max_speech_duration_s": 30.0,   // 最大语音时长(秒)
    "min_silence_duration_ms": 100,  // 最小静音时长(毫秒)
    "speech_pad_ms": 30,             // 语音片段填充(毫秒)
    "pre_process": true,             // 是否在ASR前预处理
    "return_segments": false         // 是否返回详细分段信息
  }
}
```

## API接口

### 1. VAD健康检查
```http
GET /asr/vad/health
```
检查VAD功能是否正常工作。

### 2. 语音片段检测
```http
POST /asr/vad/detect
Content-Type: multipart/form-data

file: <音频文件>
threshold: 0.5 (可选)
min_speech_duration_ms: 250 (可选)
```

响应示例：
```json
{
  "success": true,
  "segments": [
    {
      "start": 1.2,
      "end": 3.5,
      "confidence": 1.0,
      "duration": 2.3
    }
  ],
  "total_segments": 1,
  "total_speech_duration": 2.3
}
```

### 3. VAD分段语音识别
```http
POST /asr/recognize/vad
Content-Type: multipart/form-data

file: <音频文件>
return_segments: false (可选)
```

响应示例：
```json
{
  "success": true,
  "text": "这是识别出的完整文本",
  "confidence": 0.95,
  "vad_segments": 3,
  "recognized_segments": 2,
  "processing_method": "vad_segmented"
}
```

### 4. VAD音频分割
```http
POST /asr/vad/split
Content-Type: multipart/form-data

file: <音频文件>
output_format: wav (可选)
```

## Python API 使用

### 1. 基础VAD检测
```python
from asr.vad_engine import SileroVAD

# 创建VAD实例
vad = SileroVAD(model_type="silero_vad", device="auto")

# 加载模型
vad.load_model()

# 检测语音片段
segments = vad.process_audio_file("audio.wav")

for segment in segments:
    print(f"语音片段: {segment['start']:.2f}s - {segment['end']:.2f}s")
```

### 2. VAD集成ASR
```python
from asr.asr_engine import ASREngine
from asr.config import ASRConfig

# 创建配置，启用VAD
config = ASRConfig()
config.config["vad"]["enabled"] = True

# 创建ASR引擎
asr = ASREngine(config=config)

# 使用VAD分段识别
result = asr.recognize_with_vad("audio.wav")
print(f"识别结果: {result['text']}")
print(f"VAD片段数: {result['vad_segments']}")
```

### 3. 音频分割
```python
# 根据VAD结果分割音频
split_files = asr.split_audio_by_vad("input.wav", "output_dir/")

for file_path in split_files:
    print(f"分割文件: {file_path}")
```

## 参数调优指南

### 1. threshold (阈值)
- **默认值**: 0.5
- **范围**: 0.0 - 1.0
- **说明**: 语音检测的置信度阈值，越高越严格
- **调节建议**:
  - 噪音较多时提高到 0.6-0.7
  - 检测灵敏度不够时降低到 0.3-0.4

### 2. min_speech_duration_ms (最小语音时长)
- **默认值**: 250ms
- **说明**: 过短的检测结果会被过滤
- **调节建议**:
  - 处理快速语音时降低到 100-200ms
  - 过滤短噪音时提高到 500ms

### 3. max_speech_duration_s (最大语音时长)
- **默认值**: 30s
- **说明**: 过长的语音片段会被强制分割
- **调节建议**:
  - 处理长段落时提高到 60s
  - 需要短片段时降低到 10-15s

### 4. min_silence_duration_ms (最小静音时长)
- **默认值**: 100ms
- **说明**: 静音超过此时长才会分割语音
- **调节建议**:
  - 快速分割时降低到 50ms
  - 避免过度分割时提高到 200-500ms

## 性能优化

### 1. 设备选择
- **CPU模式**: 兼容性好，适合轻量场景
- **GPU模式**: 处理大批量音频时更快
- **Auto模式**: 自动选择最佳设备

### 2. 模型选择
- **silero_vad**: PyTorch模型，精度高，支持GPU加速
- **onnx**: ONNX模型，部署简单，CPU友好

### 3. 批处理优化
处理多个文件时，复用VAD实例：
```python
vad = SileroVAD()
vad.load_model()  # 只加载一次

for audio_file in audio_files:
    segments = vad.process_audio_file(audio_file)
    # 处理结果...
```

## 故障排除

### 1. VAD功能未启用
**症状**: API返回 "VAD功能未启用"
**解决**: 检查配置文件中 `vad.enabled` 是否为 `true`

### 2. 依赖缺失
**症状**: 启动时提示 "VAD不可用"
**解决**: 
```bash
pip install torch onnxruntime torchaudio
```

### 3. 模型加载失败
**症状**: "VAD模型加载失败"
**解决**: 
- 检查网络连接（首次需要下载模型）
- 尝试手动下载模型到缓存目录
- 切换到ONNX模式

### 4. 检测效果不理想
**解决方案**:
- 调整 `threshold` 参数
- 检查音频质量和采样率
- 尝试不同的 `min_speech_duration_ms` 设置

## 测试和验证

运行测试脚本验证VAD功能：
```bash
cd asr/examples
python test_vad.py
```

测试包括：
- ✅ 基础VAD功能测试
- ✅ 真实音频检测测试  
- ✅ VAD集成ASR测试
- ✅ 音频分割功能测试

## 最佳实践

1. **音频预处理**: 使用16kHz采样率的单声道音频效果最佳
2. **参数调优**: 根据具体应用场景调整VAD参数
3. **批量处理**: 处理大量文件时复用模型实例
4. **错误处理**: 实现VAD失败时的降级策略
5. **性能监控**: 监控VAD处理时间和准确率

## 更新日志

- **v1.0.0**: 初始集成Silero VAD功能
- 支持PyTorch和ONNX两种推理方式
- 提供完整的HTTP API接口
- 集成到现有ASR流程中
- 提供灵活的配置选项 