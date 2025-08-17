import { api } from "./core.js";

export const vadApi = {
  // 获取VAD状态
  async fetchVadStatus() {
    const response = await api.get("/asr/vad/health");
    return response.data;
  },

  // VAD检测语音片段
  async detectVadSegments(file, options = {}) {
    const formData = new FormData();
    formData.append("file", file);
    
    // 添加VAD参数
    if (options.threshold !== undefined) {
      formData.append("threshold", options.threshold.toString());
    }
    if (options.min_speech_duration_ms !== undefined) {
      formData.append("min_speech_duration_ms", options.min_speech_duration_ms.toString());
    }
    if (options.max_speech_duration_s !== undefined) {
      formData.append("max_speech_duration_s", options.max_speech_duration_s.toString());
    }
    if (options.min_silence_duration_ms !== undefined) {
      formData.append("min_silence_duration_ms", options.min_silence_duration_ms.toString());
    }
    if (options.speech_pad_ms !== undefined) {
      formData.append("speech_pad_ms", options.speech_pad_ms.toString());
    }

    const response = await api.post("/asr/vad/detect", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  },

  // VAD分割音频
  async splitAudioByVad(file, outputFormat = "wav") {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("output_format", outputFormat);

    const response = await api.post("/asr/vad/split", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  },
}; 