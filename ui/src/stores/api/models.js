import { api } from "./core.js";

export const modelsApi = {
  // 获取SoVITS模型列表
  async fetchSovitsModels() {
    const response = await api.get("/models/sovits");
    return response.data;
  },

  // 设置当前SoVITS模型
  async setSovitsModel(modelName) {
    const response = await api.post(
      `/models/sovits/set?model_name=${encodeURIComponent(modelName)}`
    );
    return response.data;
  },
}; 