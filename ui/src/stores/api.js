import { defineStore } from "pinia";
import {
  modelsModule,
  charactersModule,
  inferenceModule,
  ttsModule,
  systemModule,
  asrModule,
  vadModule,
} from "./api/modules/index.js";
import { mergeModuleStates, mergeModuleGetters, mergeModuleActions } from "./api/utils.js";

// 所有模块
const modules = [
  modelsModule,
  charactersModule,
  inferenceModule,
  ttsModule,
  systemModule,
  asrModule,
  vadModule,
];

export const useApiStore = defineStore("api", {
  state: () => mergeModuleStates(modules),
  
  getters: {
    ...mergeModuleGetters(modules),
    
    // 全局getters
    isLoading: (state) => {
      return state.loading || false;
    },
  },
  
  actions: {
    ...mergeModuleActions(modules),
    
    // 初始化数据
    async initializeData() {
      try {
        await Promise.all([
          this.fetchSovitsModels(),
          this.fetchCharacters(),
          this.fetchInferenceConfig(),
          this.fetchSystemStatus(),
        ]);
      } catch (error) {
        console.error("Failed to initialize data:", error);
      }
    },

    // 初始化ASR数据
    async initializeAsrData() {
      try {
        await Promise.all([
          this.fetchAsrModelInfo(),
          this.fetchAsrModelStatus(),
          this.fetchAsrConfig(),
          this.fetchVadStatus(),
        ]);
      } catch (error) {
        console.error("Failed to initialize ASR data:", error);
      }
    },

    // 刷新所有ASR状态
    async refreshAsrStatus() {
      try {
        await Promise.all([
          this.fetchAsrModelInfo(),
          this.fetchAsrModelStatus(),
          this.fetchAsrConfig(),
          this.fetchVadStatus(),
        ]);
      } catch (error) {
        console.error("Failed to refresh ASR status:", error);
        throw error;
      }
    },

    // 检查ASR是否就绪
    async checkAsrReady() {
      try {
        await this.fetchAsrModelInfo();
        return this.isAsrModelLoaded && this.isFunAsrAvailable;
      } catch (error) {
        console.error("Failed to check ASR readiness:", error);
        return false;
      }
    },

    // 快速语音识别 (自动选择最佳模式)
    async quickRecognize(audioInput, options = {}) {
      try {
        // 检查ASR是否就绪
        if (!await this.checkAsrReady()) {
          throw new Error("ASR模型未就绪，请先加载模型");
        }

        // 自动选择识别模式
        const mode = this.isVadEnabled && options.useVad !== false ? "vad" : "normal";
        
        // 根据输入类型选择方法
        if (audioInput instanceof File) {
          return await this.recognizeAudioFile(audioInput, mode);
        } else if (audioInput instanceof Blob) {
          const fileName = options.fileName || "audio.wav";
          return await this.recognizeAudioBlob(audioInput, fileName, mode);
        } else {
          throw new Error("不支持的音频输入类型");
        }
      } catch (error) {
        throw error;
      }
    },

    // 更新VAD配置 (需要同时更新ASR配置)
    async updateVadConfig(vadConfig) {
      try {
        // 更新完整的ASR配置，包括VAD部分
        const newAsrConfig = {
          ...this.asrConfig,
          vad: vadConfig
        };

        await this.updateAsrConfig(newAsrConfig);
        this.vadConfig = vadConfig;

        return { success: true };
      } catch (error) {
        throw error;
      }
    },

    // 清除所有错误
    clearAllErrors() {
      modules.forEach(module => {
        if (module.actions && module.actions.clearError) {
          this.clearError();
        }
      });
    },
  },
});
