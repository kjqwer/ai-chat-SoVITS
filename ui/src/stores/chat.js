import { defineStore } from 'pinia'
import axios from 'axios'
import { useApiStore } from './api.js'

// 默认配置作为后备
const DEFAULT_CONFIG = {
  baseURL: 'https://api.openai.com/v1',
  apiKey: 'your-openai-api-key',
  model: 'gpt-3.5-turbo',
  defaultParams: {
    temperature: 0.7,
    max_tokens: 1000,
    top_p: 1,
    frequency_penalty: 0,
    presence_penalty: 0
  },
  timeout: 30000
}

const DEFAULT_PERSONAS = [
  {
    id: 'assistant',
    name: '智能助手',
    description: '友善、专业的AI助手',
    prompt: '你是一个友善、专业且富有知识的AI助手。请用清晰、有帮助的方式回答用户的问题。保持礼貌和耐心，如果不确定答案，请诚实说明。'
  }
]

// 全局配置变量
let AI_CONFIG = { ...DEFAULT_CONFIG }
let openaiClient = null

// 初始化配置
const initializeConfig = async () => {
  try {
    // 尝试从public目录加载配置
    const response = await fetch('/ai-config.json')
    if (response.ok) {
      const config = await response.json()
      AI_CONFIG = { ...DEFAULT_CONFIG, ...config.AI_CONFIG }
      console.log('AI配置加载成功:', AI_CONFIG.baseURL)
    } else {
      console.warn('未找到ai-config.json，使用默认配置')
    }
  } catch (error) {
    console.warn('加载AI配置失败，使用默认配置:', error)
  }
  
  // 创建OpenAI API客户端
  openaiClient = axios.create({
    baseURL: AI_CONFIG.baseURL,
    timeout: AI_CONFIG.timeout,
    headers: {
      'Authorization': `Bearer ${AI_CONFIG.apiKey}`,
      'Content-Type': 'application/json'
    }
  })
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    // 对话会话列表
    conversations: [],
    
    // 当前激活的对话ID
    currentConversationId: null,
    
    // 人格设置
    personas: [...DEFAULT_PERSONAS],
    currentPersona: DEFAULT_PERSONAS[0],
    
    // 配置加载状态
    configLoaded: false,
    
    // 加载状态
    loading: {
      sendMessage: false,
      generateAudio: false
    },
    
    // 错误信息
    errors: {},
    
    // 自动生成语音开关
    autoGenerateAudio: true
  }),

  getters: {
    // 获取当前对话
    currentConversation: (state) => {
      if (!state.currentConversationId) return null
      return state.conversations.find(conv => conv.id === state.currentConversationId)
    },
    
    // 获取当前对话的消息列表
    currentMessages: (state) => {
      const conversation = state.conversations.find(conv => conv.id === state.currentConversationId)
      return conversation ? conversation.messages : []
    },
    
    // 检查是否有加载中的操作
    isLoading: (state) => {
      return Object.values(state.loading).some(loading => loading)
    }
  },

  actions: {
    // 初始化配置
    async initializeConfig() {
      if (this.configLoaded) return
      
      await initializeConfig()
      
      // 加载人格配置
      try {
        const response = await fetch('/ai-config.json')
        if (response.ok) {
          const config = await response.json()
          if (config.DEFAULT_PERSONAS && Array.isArray(config.DEFAULT_PERSONAS)) {
            this.personas = config.DEFAULT_PERSONAS
            this.currentPersona = config.DEFAULT_PERSONAS[0]
          }
        }
      } catch (error) {
        console.warn('加载人格配置失败:', error)
      }
      
      this.configLoaded = true
    },

    // 创建新对话
    createConversation(title = null) {
      const conversation = {
        id: Date.now().toString(),
        title: title || `对话 ${this.conversations.length + 1}`,
        persona: this.currentPersona,
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date()
      }
      
      this.conversations.unshift(conversation)
      this.currentConversationId = conversation.id
      
      return conversation
    },

    // 删除对话
    deleteConversation(conversationId) {
      const index = this.conversations.findIndex(conv => conv.id === conversationId)
      if (index !== -1) {
        this.conversations.splice(index, 1)
        
        // 如果删除的是当前对话，切换到下一个对话
        if (this.currentConversationId === conversationId) {
          if (this.conversations.length > 0) {
            this.currentConversationId = this.conversations[0].id
          } else {
            this.currentConversationId = null
          }
        }
      }
    },

    // 切换对话
    switchConversation(conversationId) {
      this.currentConversationId = conversationId
    },

    // 设置人格
    setPersona(persona) {
      this.currentPersona = persona
      
      // 如果当前有对话，更新对话的人格设置
      if (this.currentConversation) {
        this.currentConversation.persona = persona
        this.currentConversation.updatedAt = new Date()
      }
    },

    // 回溯到指定消息
    rollbackToMessage(conversationId, messageIndex) {
      const conversation = this.conversations.find(conv => conv.id === conversationId)
      if (!conversation) return
      
      // 删除指定索引之后的所有消息
      conversation.messages = conversation.messages.slice(0, messageIndex + 1)
      conversation.updatedAt = new Date()
    },

    // 删除指定消息
    deleteMessage(conversationId, messageIndex) {
      const conversation = this.conversations.find(conv => conv.id === conversationId)
      if (!conversation) return
      
      conversation.messages.splice(messageIndex, 1)
      conversation.updatedAt = new Date()
    },

    // 发送消息给AI
    async sendMessage(content, conversationId = null) {
      try {
        // 确保配置已加载
        await this.initializeConfig()
        
        this.loading.sendMessage = true
        this.errors.sendMessage = null
        
        // 如果没有指定对话ID，使用当前对话或创建新对话
        const targetConversationId = conversationId || this.currentConversationId
        let conversation = this.conversations.find(conv => conv.id === targetConversationId)
        
        if (!conversation) {
          conversation = this.createConversation()
        }

        // 添加用户消息
        const userMessage = {
          id: Date.now().toString(),
          role: 'user',
          content: content,
          timestamp: new Date(),
          audioUrl: null
        }
        
        conversation.messages.push(userMessage)
        conversation.updatedAt = new Date()

        // 准备发送给OpenAI的消息
        const messages = [
          {
            role: 'system',
            content: conversation.persona.prompt
          },
          ...conversation.messages.map(msg => ({
            role: msg.role,
            content: msg.content
          }))
        ]

        // 调用OpenAI API
        const response = await openaiClient.post('/chat/completions', {
          model: AI_CONFIG.model,
          messages: messages,
          ...AI_CONFIG.defaultParams
        })

        const aiResponse = response.data.choices[0].message.content

        // 添加AI回复消息
        const aiMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: aiResponse,
          timestamp: new Date(),
          audioUrl: null,
          audioGenerating: false
        }
        
        conversation.messages.push(aiMessage)
        conversation.updatedAt = new Date()

        // 自动生成标题（如果是第一条消息）
        if (conversation.messages.length === 2) {
          conversation.title = this.generateConversationTitle(content)
        }

        // 如果开启了自动生成语音，则生成AI回复的语音
        if (this.autoGenerateAudio) {
          this.generateMessageAudio(conversation.id, aiMessage.id)
        }

        return aiMessage
      } catch (error) {
        this.errors.sendMessage = error.response?.data?.error?.message || error.message
        throw error
      } finally {
        this.loading.sendMessage = false
      }
    },

    // 为消息生成语音
    async generateMessageAudio(conversationId, messageId) {
      try {
        const conversation = this.conversations.find(conv => conv.id === conversationId)
        if (!conversation) return
        
        const message = conversation.messages.find(msg => msg.id === messageId)
        if (!message) return

        // 设置生成状态
        message.audioGenerating = true

        // 调用TTS API
        const apiStore = useApiStore()
        const audioBlob = await apiStore.textToSpeech(message.content)
        
        // 创建音频URL
        const audioUrl = URL.createObjectURL(audioBlob)
        message.audioUrl = audioUrl
        message.audioGenerating = false

        return audioUrl
      } catch (error) {
        const conversation = this.conversations.find(conv => conv.id === conversationId)
        const message = conversation?.messages.find(msg => msg.id === messageId)
        if (message) {
          message.audioGenerating = false
        }
        
        console.error('Failed to generate audio for message:', error)
        throw error
      }
    },

    // 重新生成AI回复
    async regenerateResponse(conversationId, messageIndex) {
      const conversation = this.conversations.find(conv => conv.id === conversationId)
      if (!conversation) return
      
      // 找到要重新生成的消息（应该是AI消息）
      const targetMessage = conversation.messages[messageIndex]
      if (!targetMessage || targetMessage.role !== 'assistant') return
      
      // 回溯到该消息的前一条（用户消息）
      this.rollbackToMessage(conversationId, messageIndex - 1)
      
      // 获取最后一条用户消息
      const lastUserMessage = conversation.messages[conversation.messages.length - 1]
      if (lastUserMessage && lastUserMessage.role === 'user') {
        // 重新发送消息
        await this.sendMessage(lastUserMessage.content, conversationId)
      }
    },

    // 生成对话标题
    generateConversationTitle(firstMessage) {
      // 简单的标题生成逻辑，取前20个字符
      const title = firstMessage.length > 20 
        ? firstMessage.substring(0, 20) + '...' 
        : firstMessage
      return title
    },

    // 清理音频资源
    cleanupAudioResources(conversationId = null) {
      const conversations = conversationId 
        ? [this.conversations.find(conv => conv.id === conversationId)]
        : this.conversations

      conversations.forEach(conversation => {
        if (!conversation) return
        conversation.messages.forEach(message => {
          if (message.audioUrl) {
            URL.revokeObjectURL(message.audioUrl)
            message.audioUrl = null
          }
        })
      })
    },

    // 导出对话
    exportConversation(conversationId) {
      const conversation = this.conversations.find(conv => conv.id === conversationId)
      if (!conversation) return null

      const exportData = {
        title: conversation.title,
        persona: conversation.persona.name,
        createdAt: conversation.createdAt,
        messages: conversation.messages.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp
        }))
      }

      const dataStr = JSON.stringify(exportData, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      
      const link = document.createElement('a')
      link.href = URL.createObjectURL(dataBlob)
      link.download = `conversation_${conversation.title.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      URL.revokeObjectURL(link.href)
    },

    // 切换自动生成语音
    toggleAutoGenerateAudio() {
      this.autoGenerateAudio = !this.autoGenerateAudio
    },

    // 清除错误
    clearError(type) {
      if (this.errors[type]) {
        this.errors[type] = null
      }
    }
  }
}) 