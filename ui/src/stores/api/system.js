import { api } from "./core.js";

export const systemApi = {
  // 获取系统状态
  async fetchSystemStatus() {
    const response = await api.get("/status");
    return response.data;
  },
}; 