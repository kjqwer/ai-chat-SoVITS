import { defineStore } from "pinia";
import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

export const useApiStore = defineStore("api", {
  state: () => ({
    // 模型相关
    sovitsModels: [],
    currentSovitsModel: null,

    // 角色相关
    characters: [],
    currentCharacter: null,
    currentCharacterAudio: null,

    // ASR相关
    asrModelInfo: null,
    asrModelStatus: {},
    asrConfig: {},
    vadStatus: null,
    vadConfig: {},

    // 系统状态
    systemStatus: null,

    // 推理配置
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

    // 加载状态
    loading: {
      models: false,
      characters: false,
      tts: false,
      config: false,
      asr: false,
      vad: false,
    },

    // 错误信息
    errors: {},
  }),

  getters: {
    // 获取当前模型
    getCurrentModel: (state) => {
      return state.sovitsModels.find((model) => model.is_current) || null;
    },

    // 获取当前角色
    getCurrentCharacter: (state) => {
      return state.characters.find((char) => char.is_current) || null;
    },

    // 检查是否有加载中的请求
    isLoading: (state) => {
      return Object.values(state.loading).some((loading) => loading);
    },

    // ASR相关getters
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
    // 获取SoVITS模型列表
    async fetchSovitsModels() {
      try {
        this.loading.models = true;
        this.errors.models = null;

        const response = await api.get("/models/sovits");
        this.sovitsModels = response.data;
        this.currentSovitsModel = this.getCurrentModel?.name || null;

        return response.data;
      } catch (error) {
        this.errors.models = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.models = false;
      }
    },

    // 设置当前SoVITS模型
    async setSovitsModel(modelName) {
      try {
        this.loading.models = true;
        this.errors.models = null;

        const response = await api.post(
          `/models/sovits/set?model_name=${encodeURIComponent(modelName)}`
        );

        // 更新本地状态
        this.sovitsModels.forEach((model) => {
          model.is_current = model.name === modelName;
        });
        this.currentSovitsModel = modelName;

        return response.data;
      } catch (error) {
        this.errors.models = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.models = false;
      }
    },

    // 获取角色列表
    async fetchCharacters() {
      try {
        this.loading.characters = true;
        this.errors.characters = null;

        const response = await api.get("/characters");
        this.characters = response.data;

        const currentChar = this.getCurrentCharacter;
        this.currentCharacter = currentChar?.name || null;

        return response.data;
      } catch (error) {
        this.errors.characters = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.characters = false;
      }
    },

    // 设置当前角色
    async setCharacter(characterName) {
      try {
        this.loading.characters = true;
        this.errors.characters = null;

        const response = await api.post(
          `/characters/set?character_name=${encodeURIComponent(characterName)}`
        );

        // 更新本地状态
        this.characters.forEach((char) => {
          char.is_current = char.name === characterName;
        });
        this.currentCharacter = characterName;
        this.currentCharacterAudio = response.data.audio_text;

        return response.data;
      } catch (error) {
        this.errors.characters = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.characters = false;
      }
    },

    // 获取推理配置
    async fetchInferenceConfig() {
      try {
        this.loading.config = true;
        this.errors.config = null;

        const response = await api.get("/config/inference");
        this.inferenceConfig = response.data;

        return response.data;
      } catch (error) {
        this.errors.config = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.config = false;
      }
    },

    // 更新推理配置
    async updateInferenceConfig(config) {
      try {
        this.loading.config = true;
        this.errors.config = null;

        const response = await api.post("/config/inference", config);
        this.inferenceConfig = response.data.config;

        return response.data;
      } catch (error) {
        this.errors.config = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.config = false;
      }
    },

    // 文本转语音
    async textToSpeech(text) {
      try {
        this.loading.tts = true;
        this.errors.tts = null;

        const response = await api.post(
          "/tts",
          { text },
          {
            responseType: "blob",
          }
        );

        return response.data;
      } catch (error) {
        this.errors.tts = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.tts = false;
      }
    },

    // 获取系统状态
    async fetchSystemStatus() {
      try {
        const response = await api.get("/status");
        this.systemStatus = response.data;
        return response.data;
      } catch (error) {
        console.error("Failed to fetch system status:", error);
        throw error;
      }
    },

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

    // 清除错误
    clearError(type) {
      if (this.errors[type]) {
        this.errors[type] = null;
      }
    },

    // 清除所有错误
    clearAllErrors() {
      this.errors = {};
    },

    // ==================== ASR 相关方法 ====================

    // 获取ASR模型信息
    async fetchAsrModelInfo() {
      try {
        this.loading.asr = true;
        this.errors.asr = null;

        const response = await api.get("/asr/model/info");
        this.asrModelInfo = response.data;
        return response.data;
      } catch (error) {
        this.errors.asr = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.asr = false;
      }
    },

    // 获取ASR模型状态
    async fetchAsrModelStatus() {
      try {
        this.loading.asr = true;
        this.errors.asr = null;

        const response = await api.get("/asr/models/status");
        this.asrModelStatus = response.data;
        return response.data;
      } catch (error) {
        this.errors.asr = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.asr = false;
      }
    },

    // 获取ASR配置
    async fetchAsrConfig() {
      try {
        this.loading.asr = true;
        this.errors.asr = null;

        const response = await api.get("/asr/models/config");
        this.asrConfig = response.data;
        this.vadConfig = response.data.vad || {};
        return response.data;
      } catch (error) {
        this.errors.asr = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.asr = false;
      }
    },

    // 加载ASR模型
    async loadAsrModel() {
      try {
        this.loading.asr = true;
        this.errors.asr = null;

        const response = await api.post("/asr/model/load");
        
        // 刷新模型信息
        await this.fetchAsrModelInfo();
        
        return response.data;
      } catch (error) {
        this.errors.asr = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.asr = false;
      }
    },

    // 卸载ASR模型
    async unloadAsrModel() {
      try {
        this.loading.asr = true;
        this.errors.asr = null;

        const response = await api.post("/asr/model/unload");
        
        // 刷新模型信息
        await this.fetchAsrModelInfo();
        
        return response.data;
      } catch (error) {
        this.errors.asr = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.asr = false;
      }
    },

    // 语音识别 - 文件上传
    async recognizeAudioFile(file, mode = "normal") {
      try {
        this.loading.asr = true;
        this.errors.asr = null;

        const formData = new FormData();
        
        // 根据模式选择端点和参数
        let endpoint = "/asr/recognize/file";
        if (mode === "vad") {
          endpoint = "/asr/recognize/vad";
          formData.append("file", file);
          formData.append("return_segments", "true");
        } else {
          formData.append("audio_file", file);
        }

        const response = await api.post(endpoint, formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });

        return response.data;
      } catch (error) {
        this.errors.asr = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.asr = false;
      }
    },

    // 语音识别 - Blob数据
    async recognizeAudioBlob(audioBlob, fileName = "audio.wav", mode = "normal") {
      try {
        this.loading.asr = true;
        this.errors.asr = null;

        const formData = new FormData();
        
        // 根据模式选择端点和参数
        let endpoint = "/asr/recognize/file";
        if (mode === "vad") {
          endpoint = "/asr/recognize/vad";
          formData.append("file", audioBlob, fileName);
          formData.append("return_segments", "true");
        } else {
          formData.append("audio_file", audioBlob, fileName);
        }

        const response = await api.post(endpoint, formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });

        return response.data;
      } catch (error) {
        this.errors.asr = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.asr = false;
      }
    },

    // ==================== VAD 相关方法 ====================

    // 获取VAD状态
    async fetchVadStatus() {
      try {
        this.loading.vad = true;
        this.errors.vad = null;

        const response = await api.get("/asr/vad/health");
        this.vadStatus = response.data;
        return response.data;
      } catch (error) {
        this.errors.vad = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.vad = false;
      }
    },

    // VAD检测语音片段
    async detectVadSegments(file, options = {}) {
      try {
        this.loading.vad = true;
        this.errors.vad = null;

        const formData = new FormData();
        formData.append("file", file);
        
        // 添加VAD参数
        if (options.threshold !== undefined) {
          formData.append("threshold", options.threshold.toString());
        }
        if (options.min_speech_duration_ms !== undefined) {
          formData.append("min_speech_duration_ms", options.min_speech_duration_ms.toString());
        }
        if (options.max_speech_duration_s !== undefined) {
          formData.append("max_speech_duration_s", options.max_speech_duration_s.toString());
        }
        if (options.min_silence_duration_ms !== undefined) {
          formData.append("min_silence_duration_ms", options.min_silence_duration_ms.toString());
        }
        if (options.speech_pad_ms !== undefined) {
          formData.append("speech_pad_ms", options.speech_pad_ms.toString());
        }

        const response = await api.post("/asr/vad/detect", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });

        return response.data;
      } catch (error) {
        this.errors.vad = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.vad = false;
      }
    },

    // VAD分割音频
    async splitAudioByVad(file, outputFormat = "wav") {
      try {
        this.loading.vad = true;
        this.errors.vad = null;

        const formData = new FormData();
        formData.append("file", file);
        formData.append("output_format", outputFormat);

        const response = await api.post("/asr/vad/split", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });

        return response.data;
      } catch (error) {
        this.errors.vad = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.vad = false;
      }
    },

    // 更新VAD配置
    async updateVadConfig(vadConfig) {
      try {
        this.loading.vad = true;
        this.errors.vad = null;

        // 更新完整的ASR配置，包括VAD部分
        const newAsrConfig = {
          ...this.asrConfig,
          vad: vadConfig
        };

        const response = await api.post("/asr/config/update", newAsrConfig);
        
        // 更新本地状态
        this.asrConfig = response.data;
        this.vadConfig = vadConfig;
        
        // 刷新模型信息以获取最新的VAD状态
        await this.fetchAsrModelInfo();

        return response.data;
      } catch (error) {
        this.errors.vad = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.vad = false;
      }
    },

    // ==================== ASR 管理方法 ====================

    // 迁移模型
    async migrateAsrModels(copyMode = true) {
      try {
        this.loading.asr = true;
        this.errors.asr = null;

        const response = await api.post(`/asr/models/migrate?copy_mode=${copyMode}`);
        
        // 刷新模型状态
        await this.fetchAsrModelStatus();
        await this.fetchAsrConfig();
        
        return response.data;
      } catch (error) {
        this.errors.asr = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.asr = false;
      }
    },

    // 清理缓存
    async cleanAsrCache() {
      try {
        this.loading.asr = true;
        this.errors.asr = null;

        const response = await api.post("/asr/models/clean_cache");
        
        // 刷新模型状态
        await this.fetchAsrModelStatus();
        
        return response.data;
      } catch (error) {
        this.errors.asr = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading.asr = false;
      }
    },

    // ==================== 便捷方法 ====================

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
  },
});
