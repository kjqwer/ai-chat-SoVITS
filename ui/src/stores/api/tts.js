import { api } from "./core.js";

export const ttsApi = {
  // 文本转语音
  async textToSpeech(text) {
    const response = await api.post(
      "/tts",
      { text },
      {
        responseType: "blob",
      }
    );
    return response.data;
  },
}; 