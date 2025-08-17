import { vadApi } from "../vad.js";

export const vadModule = {
  state: () => ({
    vadStatus: null,
    vadConfig: {},
    loading: false,
    error: null,
  }),

  actions: {
    async fetchVadStatus() {
      try {
        this.loading = true;
        this.error = null;

        const data = await vadApi.fetchVadStatus();
        this.vadStatus = data;
        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async detectVadSegments(file, options = {}) {
      try {
        this.loading = true;
        this.error = null;

        const data = await vadApi.detectVadSegments(file, options);
        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async splitAudioByVad(file, outputFormat = "wav") {
      try {
        this.loading = true;
        this.error = null;

        const data = await vadApi.splitAudioByVad(file, outputFormat);
        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async updateVadConfig(vadConfig) {
      try {
        this.loading = true;
        this.error = null;

        this.vadConfig = vadConfig;
        return { success: true };
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