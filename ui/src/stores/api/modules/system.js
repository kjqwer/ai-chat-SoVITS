import { systemApi } from "../system.js";

export const systemModule = {
  state: () => ({
    systemStatus: null,
  }),

  actions: {
    async fetchSystemStatus() {
      try {
        const data = await systemApi.fetchSystemStatus();
        this.systemStatus = data;
        return data;
      } catch (error) {
        console.error("Failed to fetch system status:", error);
        throw error;
      }
    },
  },
}; 