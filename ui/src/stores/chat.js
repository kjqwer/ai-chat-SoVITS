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
