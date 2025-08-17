import { modelsApi } from "../models.js";

export const modelsModule = {
  state: () => ({
    sovitsModels: [],
    currentSovitsModel: null,
    loading: false,
    error: null,
  }),

  getters: {
    getCurrentModel: (state) => {
      return state.sovitsModels.find((model) => model.is_current) || null;
    },
  },

  actions: {
    async fetchSovitsModels() {
      try {
        this.loading = true;
        this.error = null;

        const data = await modelsApi.fetchSovitsModels();
        this.sovitsModels = data;
        this.currentSovitsModel = this.getCurrentModel?.name || null;

        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async setSovitsModel(modelName) {
      try {
        this.loading = true;
        this.error = null;

        const data = await modelsApi.setSovitsModel(modelName);

        // 更新本地状态
        this.sovitsModels.forEach((model) => {
          model.is_current = model.name === modelName;
        });
        this.currentSovitsModel = modelName;

        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    clearError() {
      this.error = null;
    },
  },
}; 