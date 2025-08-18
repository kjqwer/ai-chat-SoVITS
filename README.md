# GPT-SoVITS AI对话集成项目

基于 GPT-SoVITS 魔改的自用小项目，集成了 AI 对话功能和 TTS 语音合成，特点是只关注推理，运行只要选择角色和模型，什么都不用设置，ui自动集成第三方ai开始对话。

## 视频演示

观看完整功能演示：

<video width="100%" controls>
  <source src="https://sywb.top/Staticfiles/%E8%A7%86%E9%A2%91%E6%BC%94%E7%A4%BA.mp4" type="video/mp4">
  您的浏览器不支持视频播放。
</video>


## 快速开始

### 1. 启动服务
```bash

# 直接运行（运行前打包ui，生成dist，或者直接解压ui里的dist即可）
python GPT_SoVITS/backend_api.py

# 或使用批处理文件（runtime运行时，模型和音频请去官方包那里下载，如果只是想使用语音合成就改为推理bat）
启动服务.bat
```

### 2. 访问界面
- 前端界面：http://localhost:8000
- API文档：http://localhost:8000/docs

### 3. 配置修改
编辑 `ui/public/ai-config.json` 可以修改：
- AI API 配置（支持 OpenAI、阿里云等）
- 模型参数
- 角色人格设置

## 项目结构

```
├── GPT_SoVITS/           # 后端 API 服务
├── ui/                   # 前端界面
│   ├── public/
│   │   └── ai-config.json    # AI 配置文件
│   └── dist/             # 构建输出
├── reference_audios/     # 角色参考音频
│   ├── emotions/         # 按情感分类的音频
│   │   └── 角色名/
│   │       └── 中文/
│   │           ├── 【开心】你好世界.wav
│   │           ├── 【伤心】我很难过.wav
│   │           └── ...
│   └── randoms/          # 随机音频（需要配对的.lab文件）
│       └── 角色名/
│           └── 中文/
│               ├── audio1.wav
│               ├── audio1.lab   # 对应的文本标注
│               └── ...
└── 启动服务.bat          # 启动脚本
```

### 音频文件放置说明

**emotions 目录**：
- 文件名格式：`【情感】文本内容.wav`
- 系统会自动选择"开心"情感的音频作为默认参考
- 支持多种情感标签，如：开心、伤心、愤怒等

**randoms 目录**：
- 音频文件：`*.wav`
- 文本文件：`*.lab`（与音频文件同名，包含对应文本）
- 用于更丰富的音频样本

## 使用说明

1. **设置页面**：配置 TTS 模型、角色、推理参数
2. **AI对话页面**：与 AI 进行对话，自动生成语音回复
3. **对话管理**：支持多个对话会话，可回溯到任意消息重新开始

## 注意事项

- 需要配置有效的 AI API 密钥
- 确保 `reference_audios` 目录包含角色音频文件
- 首次使用需要选择模型和角色

---

*个人自用项目，基于 GPT-SoVITS 开发*

## 相关链接

- **GPT-SoVITS 官方项目**：https://github.com/RVC-Boss/GPT-SoVITS 