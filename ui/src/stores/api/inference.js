import { api } from "./core.js";

export const inferenceApi = {
  // 获取推理配置
  async fetchInferenceConfig() {
    const response = await api.get("/config/inference");
    return response.data;
  },

  // 更新推理配置
  async updateInferenceConfig(config) {
    const response = await api.post("/config/inference", config);
    return response.data;
  },
}; 