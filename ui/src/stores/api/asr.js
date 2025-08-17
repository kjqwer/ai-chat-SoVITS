import { api } from "./core.js";

export const asrApi = {
  // 获取ASR模型信息
  async fetchAsrModelInfo() {
    const response = await api.get("/asr/model/info");
    return response.data;
  },

  // 获取ASR模型状态
  async fetchAsrModelStatus() {
    const response = await api.get("/asr/models/status");
    return response.data;
  },

  // 获取ASR配置
  async fetchAsrConfig() {
    const response = await api.get("/asr/models/config");
    return response.data;
  },

  // 加载ASR模型
  async loadAsrModel() {
    const response = await api.post("/asr/model/load");
    return response.data;
  },

  // 卸载ASR模型
  async unloadAsrModel() {
    const response = await api.post("/asr/model/unload");
    return response.data;
  },

  // 语音识别 - 文件上传
  async recognizeAudioFile(file, mode = "normal") {
    const formData = new FormData();
    
    // 根据模式选择端点和参数
    let endpoint = "/asr/recognize/file";
    if (mode === "vad") {
      endpoint = "/asr/recognize/vad";
      formData.append("file", file);
      formData.append("return_segments", "true");
    } else {
      formData.append("audio_file", file);
    }

    const response = await api.post(endpoint, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  },

  // 语音识别 - Blob数据
  async recognizeAudioBlob(audioBlob, fileName = "audio.wav", mode = "normal") {
    const formData = new FormData();
    
    // 根据模式选择端点和参数
    let endpoint = "/asr/recognize/file";
    if (mode === "vad") {
      endpoint = "/asr/recognize/vad";
      formData.append("file", audioBlob, fileName);
      formData.append("return_segments", "true");
    } else {
      formData.append("audio_file", audioBlob, fileName);
    }

    const response = await api.post(endpoint, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  },

  // 迁移模型
  async migrateAsrModels(copyMode = true) {
    const response = await api.post(`/asr/models/migrate?copy_mode=${copyMode}`);
    return response.data;
  },

  // 清理缓存
  async cleanAsrCache() {
    const response = await api.post("/asr/models/clean_cache");
    return response.data;
  },

  // 更新ASR配置
  async updateAsrConfig(asrConfig) {
    const response = await api.post("/asr/config/update", asrConfig);
    return response.data;
  },
}; 