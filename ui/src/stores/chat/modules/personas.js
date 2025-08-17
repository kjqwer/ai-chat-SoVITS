import { DEFAULT_PERSONAS } from "../core.js";
import { useApiStore } from "../../api.js";

export const personasModule = {
  state: () => ({
    personas: [...DEFAULT_PERSONAS],
    currentPersona: DEFAULT_PERSONAS[0],
  }),

  actions: {
    // 设置人格
    async setPersona(persona) {
      this.currentPersona = persona;

      // 如果当前有对话，更新对话的人格设置
      if (this.currentConversationId) {
        this.updateConversationPersona(this.currentConversationId, persona);
      }

      // 刷新API store中的系统状态
      const apiStore = useApiStore();
      try {
        await apiStore.fetchSystemStatus();
      } catch (error) {
        console.warn("刷新系统状态失败:", error);
      }
    },

    // 加载人格配置
    async loadPersonas() {
      try {
        const response = await fetch("/ai-config.json");
        if (response.ok) {
          const config = await response.json();
          if (
            config.DEFAULT_PERSONAS &&
            Array.isArray(config.DEFAULT_PERSONAS)
          ) {
            this.personas = config.DEFAULT_PERSONAS;
            this.currentPersona = config.DEFAULT_PERSONAS[0];
          }
        }
      } catch (error) {
        console.warn("加载人格配置失败:", error);
      }
    },
  },
}; 