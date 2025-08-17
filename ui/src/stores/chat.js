import { defineStore } from "pinia";
import {
  conversationsModule,
  personasModule,
  messagesModule,
  audioModule,
  importExportModule,
  configModule,
} from "./chat/modules/index.js";
import { mergeModuleStates, mergeModuleGetters, mergeModuleActions } from "./chat/utils.js";

// 所有模块
const modules = [
  conversationsModule,
  personasModule,
  messagesModule,
  audioModule,
  importExportModule,
  configModule,
];

export const useChatStore = defineStore("chat", {
  state: () => mergeModuleStates(modules),
  
  getters: {
    ...mergeModuleGetters(modules),
    
    // 全局getters
    isLoading: (state) => {
      return Object.values(state.loading || {}).some((loading) => loading);
    },
  },
  
  actions: {
    ...mergeModuleActions(modules),
    
    // ==================== 便捷方法 ====================
    
    // 创建新对话（带当前人格）
    createConversationWithCurrentPersona(title = null) {
      return this.createConversation(title, this.currentPersona);
    },
    
    // 初始化聊天store
    async initializeChatStore() {
      await this.initializeConfig();
      await this.loadPersonas();
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
