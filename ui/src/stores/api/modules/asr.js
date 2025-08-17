import { asrApi } from "../asr.js";

export const asrModule = {
  state: () => ({
    asrModelInfo: null,
    asrModelStatus: {},
    asrConfig: {},
    loading: false,
    error: null,
  }),

  getters: {
    isAsrModelLoaded: (state) => {
      return state.asrModelInfo?.is_loaded || false;
    },

    isFunAsrAvailable: (state) => {
      return state.asrModelInfo?.funasr_available || false;
    },

    isVadAvailable: (state) => {
      return state.asrModelInfo?.vad_available || false;
    },

    isVadEnabled: (state) => {
      return state.asrModelInfo?.vad_enabled || false;
    },
  },

  actions: {
    async fetchAsrModelInfo() {
      try {
        this.loading = true;
        this.error = null;

        const data = await asrApi.fetchAsrModelInfo();
        this.asrModelInfo = data;
        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchAsrModelStatus() {
      try {
        this.loading = true;
        this.error = null;

        const data = await asrApi.fetchAsrModelStatus();
        this.asrModelStatus = data;
        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchAsrConfig() {
      try {
        this.loading = true;
        this.error = null;

        const data = await asrApi.fetchAsrConfig();
        this.asrConfig = data;
        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async loadAsrModel() {
      try {
        this.loading = true;
        this.error = null;

        const data = await asrApi.loadAsrModel();
        
        // 刷新模型信息
        await this.fetchAsrModelInfo();
        
        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async unloadAsrModel() {
      try {
        this.loading = true;
        this.error = null;

        const data = await asrApi.unloadAsrModel();
        
        // 刷新模型信息
        await this.fetchAsrModelInfo();
        
        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async recognizeAudioFile(file, mode = "normal") {
      try {
        this.loading = true;
        this.error = null;

        const data = await asrApi.recognizeAudioFile(file, mode);
        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async recognizeAudioBlob(audioBlob, fileName = "audio.wav", mode = "normal") {
      try {
        this.loading = true;
        this.error = null;

        const data = await asrApi.recognizeAudioBlob(audioBlob, fileName, mode);
        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async migrateAsrModels(copyMode = true) {
      try {
        this.loading = true;
        this.error = null;

        const data = await asrApi.migrateAsrModels(copyMode);
        
        // 刷新模型状态
        await this.fetchAsrModelStatus();
        await this.fetchAsrConfig();
        
        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async cleanAsrCache() {
      try {
        this.loading = true;
        this.error = null;

        const data = await asrApi.cleanAsrCache();
        
        // 刷新模型状态
        await this.fetchAsrModelStatus();
        
        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async updateAsrConfig(asrConfig) {
      try {
        this.loading = true;
        this.error = null;

        const data = await asrApi.updateAsrConfig(asrConfig);
        this.asrConfig = data;
        
        // 刷新模型信息以获取最新的VAD状态
        await this.fetchAsrModelInfo();

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