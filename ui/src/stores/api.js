import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const useApiStore = defineStore('api', {
  state: () => ({
    // 模型相关
    sovitsModels: [],
    currentSovitsModel: null,
    
    // 角色相关
    characters: [],
    currentCharacter: null,
    currentCharacterAudio: null,
    
    // 系统状态
    systemStatus: null,
    
    // 推理配置
    inferenceConfig: {
      text_lang: '中文',
      prompt_lang: '中文',
      top_k: 5,
      top_p: 1.0,
      temperature: 1.0,
      text_split_method: '凑四句一切',
      batch_size: 20,
      speed_factor: 1.0,
      ref_text_free: false,
      split_bucket: true,
      fragment_interval: 0.3,
      parallel_infer: true,
      repetition_penalty: 1.35,
      sample_steps: 32,
      super_sampling: false
    },
    
    // 加载状态
    loading: {
      models: false,
      characters: false,
      tts: false,
      config: false
    },
    
    // 错误信息
    errors: {}
  }),

  getters: {
    // 获取当前模型
    getCurrentModel: (state) => {
      return state.sovitsModels.find(model => model.is_current) || null
    },
    
    // 获取当前角色
    getCurrentCharacter: (state) => {
      return state.characters.find(char => char.is_current) || null
    },
    
    // 检查是否有加载中的请求
    isLoading: (state) => {
      return Object.values(state.loading).some(loading => loading)
    }
  },

  actions: {
    // 获取SoVITS模型列表
    async fetchSovitsModels() {
      try {
        this.loading.models = true
        this.errors.models = null
        
        const response = await api.get('/models/sovits')
        this.sovitsModels = response.data
        this.currentSovitsModel = this.getCurrentModel?.name || null
        
        return response.data
      } catch (error) {
        this.errors.models = error.response?.data?.detail || error.message
        throw error
      } finally {
        this.loading.models = false
      }
    },

    // 设置当前SoVITS模型
    async setSovitsModel(modelName) {
      try {
        this.loading.models = true
        this.errors.models = null
        
        const response = await api.post(`/models/sovits/set?model_name=${encodeURIComponent(modelName)}`)
        
        // 更新本地状态
        this.sovitsModels.forEach(model => {
          model.is_current = model.name === modelName
        })
        this.currentSovitsModel = modelName
        
        return response.data
      } catch (error) {
        this.errors.models = error.response?.data?.detail || error.message
        throw error
      } finally {
        this.loading.models = false
      }
    },

    // 获取角色列表
    async fetchCharacters() {
      try {
        this.loading.characters = true
        this.errors.characters = null
        
        const response = await api.get('/characters')
        this.characters = response.data
        
        const currentChar = this.getCurrentCharacter
        this.currentCharacter = currentChar?.name || null
        
        return response.data
      } catch (error) {
        this.errors.characters = error.response?.data?.detail || error.message
        throw error
      } finally {
        this.loading.characters = false
      }
    },

    // 设置当前角色
    async setCharacter(characterName) {
      try {
        this.loading.characters = true
        this.errors.characters = null
        
        const response = await api.post(`/characters/set?character_name=${encodeURIComponent(characterName)}`)
        
        // 更新本地状态
        this.characters.forEach(char => {
          char.is_current = char.name === characterName
        })
        this.currentCharacter = characterName
        this.currentCharacterAudio = response.data.audio_text
        
        return response.data
      } catch (error) {
        this.errors.characters = error.response?.data?.detail || error.message
        throw error
      } finally {
        this.loading.characters = false
      }
    },

    // 获取推理配置
    async fetchInferenceConfig() {
      try {
        this.loading.config = true
        this.errors.config = null
        
        const response = await api.get('/config/inference')
        this.inferenceConfig = response.data
        
        return response.data
      } catch (error) {
        this.errors.config = error.response?.data?.detail || error.message
        throw error
      } finally {
        this.loading.config = false
      }
    },

    // 更新推理配置
    async updateInferenceConfig(config) {
      try {
        this.loading.config = true
        this.errors.config = null
        
        const response = await api.post('/config/inference', config)
        this.inferenceConfig = response.data.config
        
        return response.data
      } catch (error) {
        this.errors.config = error.response?.data?.detail || error.message
        throw error
      } finally {
        this.loading.config = false
      }
    },

    // 文本转语音
    async textToSpeech(text) {
      try {
        this.loading.tts = true
        this.errors.tts = null
        
        const response = await api.post('/tts', { text }, {
          responseType: 'blob'
        })
        
        return response.data
      } catch (error) {
        this.errors.tts = error.response?.data?.detail || error.message
        throw error
      } finally {
        this.loading.tts = false
      }
    },

    // 获取系统状态
    async fetchSystemStatus() {
      try {
        const response = await api.get('/status')
        this.systemStatus = response.data
        return response.data
      } catch (error) {
        console.error('Failed to fetch system status:', error)
        throw error
      }
    },

    // 初始化数据
    async initializeData() {
      try {
        await Promise.all([
          this.fetchSovitsModels(),
          this.fetchCharacters(),
          this.fetchInferenceConfig(),
          this.fetchSystemStatus()
        ])
      } catch (error) {
        console.error('Failed to initialize data:', error)
      }
    },

    // 清除错误
    clearError(type) {
      if (this.errors[type]) {
        this.errors[type] = null
      }
    },

    // 清除所有错误
    clearAllErrors() {
      this.errors = {}
    }
  }
}) 