# GPT-SoVITS TTS API 服务

这是一个基于 FastAPI 的 GPT-SoVITS TTS 后端服务，提供简化的文本转语音功能。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动服务

```bash
python backend_api.py
```

服务将在 `http://localhost:8000` 启动。

## API 接口文档

### 1. 获取 SoVITS 模型列表

**GET** `/models/sovits`

返回所有可用的 SoVITS 模型及当前使用的模型。

**响应示例：**
```json
[
  {
    "name": "model1.pth",
    "path": "model1.pth",
    "is_current": true
  },
  {
    "name": "model2.pth", 
    "path": "model2.pth",
    "is_current": false
  }
]
```

### 2. 设置当前 SoVITS 模型

**POST** `/models/sovits/set?model_name={model_name}`

设置要使用的 SoVITS 模型。

**参数：**
- `model_name` (query): 模型名称

**响应示例：**
```json
{
  "message": "Model set successfully",
  "model": "model1.pth"
}
```

### 3. 获取角色列表

**GET** `/characters`

返回所有可用的角色及当前选择的角色。

**响应示例：**
```json
[
  {
    "name": "角色1",
    "is_current": true
  },
  {
    "name": "角色2",
    "is_current": false
  }
]
```

### 4. 设置当前角色

**POST** `/characters/set?character_name={character_name}`

设置要使用的角色。系统会自动选择该角色的开心音频作为参考音频。

**参数：**
- `character_name` (query): 角色名称

**响应示例：**
```json
{
  "message": "Character set successfully",
  "character": "角色1",
  "audio_path": "reference_audios/emotions/角色1/中文/【开心】你好世界.wav",
  "audio_text": "你好世界"
}
```

### 5. 文本转语音

**POST** `/tts`

将输入的文本转换为语音。

**请求体：**
```json
{
  "text": "要合成的文本内容"
}
```

**响应：**
返回生成的音频文件（WAV格式）。

### 6. 获取推理配置

**GET** `/config/inference`

获取当前的推理配置参数。

**响应示例：**
```json
{
  "text_lang": "中文",
  "prompt_lang": "中文",
  "top_k": 5,
  "top_p": 1.0,
  "temperature": 1.0,
  "text_split_method": "凑四句一切",
  "batch_size": 20,
  "speed_factor": 1.0,
  "ref_text_free": false,
  "split_bucket": true,
  "fragment_interval": 0.3,
  "parallel_infer": true,
  "repetition_penalty": 1.35,
  "sample_steps": 32,
  "super_sampling": false
}
```

### 7. 更新推理配置

**POST** `/config/inference`

更新推理配置参数。

**请求体示例：**
```json
{
  "temperature": 0.8,
  "speed_factor": 1.2,
  "batch_size": 10
}
```

### 8. 获取系统状态

**GET** `/status`

获取当前系统状态。

**响应示例：**
```json
{
  "current_sovits_model": "model1.pth",
  "current_character": "角色1", 
  "current_character_audio": "你好世界",
  "device": "cuda",
  "version": "v2",
  "model_version": "v2"
}
```

## 使用流程

1. **启动服务** - 运行 `python backend_api.py`
2. **设置模型** - 调用 `/models/sovits/set` 设置要使用的 SoVITS 模型
3. **设置角色** - 调用 `/characters/set` 设置要使用的角色
4. **生成语音** - 调用 `/tts` 传入文本生成语音

## Python 客户端示例

```python
import requests
import json

# 服务器地址
BASE_URL = "http://localhost:8000"

# 1. 获取模型列表
response = requests.get(f"{BASE_URL}/models/sovits")
models = response.json()
print("可用模型:", [m["name"] for m in models])

# 2. 设置模型（如果需要）
if models:
    model_name = models[0]["name"]
    response = requests.post(f"{BASE_URL}/models/sovits/set", params={"model_name": model_name})
    print("设置模型:", response.json())

# 3. 获取角色列表
response = requests.get(f"{BASE_URL}/characters")
characters = response.json()
print("可用角色:", [c["name"] for c in characters])

# 4. 设置角色
if characters:
    character_name = characters[0]["name"]
    response = requests.post(f"{BASE_URL}/characters/set", params={"character_name": character_name})
    print("设置角色:", response.json())

# 5. 生成语音
tts_data = {"text": "你好，这是一个测试语音合成的文本。"}
response = requests.post(f"{BASE_URL}/tts", json=tts_data)

if response.status_code == 200:
    # 保存音频文件
    with open("output.wav", "wb") as f:
        f.write(response.content)
    print("语音生成成功，已保存为 output.wav")
else:
    print("生成失败:", response.json())
```

## 注意事项

1. 确保 `reference_audios` 目录结构正确，包含角色的参考音频文件
2. 角色名称通过 URL 查询参数传递，避免中文编码问题
3. 系统会自动为每个角色选择"开心"情感的音频作为参考
4. 默认使用中文语言进行合成
5. 推理配置可以通过 API 动态调整

## 交互式 API 文档

启动服务后，访问 `http://localhost:8000/docs` 查看 Swagger UI 格式的交互式 API 文档。 