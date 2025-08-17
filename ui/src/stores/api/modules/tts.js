import { ttsApi } from "../tts.js";

export const ttsModule = {
  state: () => ({
    loading: false,
    error: null,
  }),

  actions: {
    async textToSpeech(text) {
      try {
        this.loading = true;
        this.error = null;

        const data = await ttsApi.textToSpeech(text);
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