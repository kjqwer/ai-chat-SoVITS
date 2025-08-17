import { inferenceApi } from "../inference.js";

export const inferenceModule = {
  state: () => ({
    inferenceConfig: {
      text_lang: "中文",
      prompt_lang: "中文",
      top_k: 5,
      top_p: 1.0,
      temperature: 1.0,
      text_split_method: "凑四句一切",
      batch_size: 20,
      speed_factor: 1.0,
      ref_text_free: false,
      split_bucket: true,
      fragment_interval: 0.3,
      parallel_infer: true,
      repetition_penalty: 1.35,
      sample_steps: 32,
      super_sampling: false,
    },
    loading: false,
    error: null,
  }),

  actions: {
    async fetchInferenceConfig() {
      try {
        this.loading = true;
        this.error = null;

        const data = await inferenceApi.fetchInferenceConfig();
        this.inferenceConfig = data;

        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async updateInferenceConfig(config) {
      try {
        this.loading = true;
        this.error = null;

        const data = await inferenceApi.updateInferenceConfig(config);
        this.inferenceConfig = data.config;

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