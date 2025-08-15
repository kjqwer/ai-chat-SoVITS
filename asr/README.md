# FunASR 语音识别模块

基于 FunASR 的语音到文本识别模块，提供完整的语音识别功能。

## 功能特性

- 🎯 基于 FunASR 的高精度中文语音识别
- 🚀 支持多种音频格式 (WAV, MP3, M4A, FLAC, AAC, OGG)
- 🌐 提供 REST API 和 WebSocket 接口
- ⚡ 异步处理，支持并发请求
- 🔧 可配置的模型参数
- 📝 详细的识别结果（文本、置信度、时间戳等）
- 🎤 支持说话人识别和标点符号预测

## 安装依赖

```bash
# 安装基础依赖
pip install -r asr/requirements.txt

# 或者安装 FunASR
pip install funasr
```

## 快速开始

### 1. 启动 ASR 服务

将 ASR 模块集成到主服务中：

```python
# 在 GPT_SoVITS/backend_api.py 中添加
from asr import asr_router
from asr.websocket_server import websocket_router

app.include_router(asr_router)
app.include_router(websocket_router)
```

### 2. 使用 REST API

#### 上传音频文件识别
```bash
curl -X POST "http://localhost:8000/asr/recognize/file" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "audio_file=@example.wav"
```

#### 识别网络音频
```bash
curl -X POST "http://localhost:8000/asr/recognize/url" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "url=https://example.com/audio.wav"
```

#### 模型管理
```bash
# 加载模型
curl -X POST "http://localhost:8000/asr/model/load"

# 获取模型信息
curl -X GET "http://localhost:8000/asr/model/info"

# 卸载模型
curl -X POST "http://localhost:8000/asr/model/unload"
```

### 3. 使用命令行工具

```bash
# 识别音频文件
python -m asr.cli audio.wav

# 指定输出格式和文件
python -m asr.cli audio.wav --format json --output result.json

# 使用自定义模型
python -m asr.cli audio.wav --model "your-model-name"
```

### 4. 使用 WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/asr/ws');

// 加载模型
ws.send(JSON.stringify({
    type: 'config',
    load_model: true
}));

// 发送音频数据
ws.send(JSON.stringify({
    type: 'audio_data',
    data: base64AudioData,
    format: 'wav',
    sample_rate: 16000
}));

// 接收识别结果
ws.onmessage = function(event) {
    const result = JSON.parse(event.data);
    if (result.type === 'recognition_result') {
        console.log('识别结果:', result.text);
    }
};
```

## API 接口说明

### REST API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/asr/recognize/file` | POST | 上传音频文件识别 |
| `/asr/recognize/url` | POST | 识别网络音频文件 |
| `/asr/model/load` | POST | 加载 ASR 模型 |
| `/asr/model/unload` | POST | 卸载 ASR 模型 |
| `/asr/model/info` | GET | 获取模型信息 |
| `/asr/health` | GET | 健康检查 |
| `/asr/supported_formats` | GET | 获取支持的音频格式 |

### WebSocket API

连接地址：`ws://localhost:8000/asr/ws`

#### 消息格式

**配置消息：**
```json
{
  "type": "config",
  "load_model": true
}
```

**音频数据：**
```json
{
  "type": "audio_data",
  "data": "base64编码的音频数据",
  "format": "wav",
  "sample_rate": 16000
}
```

**响应格式：**
```json
{
  "type": "recognition_result",
  "success": true,
  "text": "识别的文本内容",
  "confidence": 0.95,
  "timestamp": [[0, 1000, "识别"], [1000, 2000, "的文本"]],
  "segments": [...]
}
```

## 配置说明

配置文件位置：`asr/config.json`

```json
{
  "model": {
    "name": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    "vad_model": "fsmn-vad",
    "punc_model": "ct-punc",
    "spk_model": "cam++",
    "device": "auto"
  },
  "audio": {
    "sample_rate": 16000,
    "max_duration": 300,
    "supported_formats": [".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg"]
  },
  "api": {
    "max_file_size": 52428800,
    "timeout": 30
  }
}
```

### 环境变量配置

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `ASR_MODEL_NAME` | ASR 模型名称 | `iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch` |
| `ASR_DEVICE` | 设备类型 | `auto` |
| `ASR_SAMPLE_RATE` | 采样率 | `16000` |
| `ASR_MAX_DURATION` | 最大音频时长（秒） | `300` |
| `ASR_MAX_FILE_SIZE` | 最大文件大小（字节） | `52428800` |
| `ASR_TIMEOUT` | 超时时间（秒） | `30` |

## 支持的模型

### 中文模型
- `iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch` (默认)
- `iic/speech_paraformer_asr_nat-zh-cn-16k-common-vocab8404-pytorch`
- `iic/speech_conformer_asr_nat-zh-cn-16k-aishell1-vocab4234-pytorch`

### 英文模型
- `iic/speech_paraformer-large_asr_nat-en-16k-common-vocab10020-pytorch`
- `iic/speech_conformer_asr_nat-en-16k-librispeech-vocab5000-pytorch`

### 多语言模型
- `iic/speech_paraformer-large_asr_nat-multilingual-16k-vocab10020-pytorch`

## 错误处理

常见错误及解决方案：

1. **模型加载失败**
   - 检查网络连接
   - 确认模型名称正确
   - 检查存储空间是否足够

2. **音频格式不支持**
   - 检查音频文件格式
   - 转换为支持的格式

3. **识别失败**
   - 检查音频质量
   - 确认音频长度不超过限制
   - 检查模型是否已加载

## 性能优化

1. **模型缓存**：首次加载后模型会保持在内存中
2. **异步处理**：使用线程池处理识别请求
3. **文件清理**：自动清理临时文件
4. **错误重试**：自动重试失败的请求

## 开发指南

### 扩展新功能

1. 在 `asr_engine.py` 中添加新的识别方法
2. 在 `asr_api.py` 中添加对应的 API 端点
3. 更新配置文件支持新参数
4. 添加单元测试

### 自定义模型

```python
from asr import ASREngine

# 使用自定义模型
engine = ASREngine(model_name="your-custom-model")
engine.load_model()

result = engine.recognize_audio_file("audio.wav")
print(result["text"])
```

## 许可证

本模块基于原项目许可证开发。 