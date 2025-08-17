import { initializeConfig } from "../core.js";

export const configModule = {
  state: () => ({
    configLoaded: false,
  }),

  actions: {
    // 初始化配置
    async initializeConfig(forceReload = false) {
      if (this.configLoaded && !forceReload) return;

      await initializeConfig();

      // 加载人格配置
      await this.loadPersonas();

      // 迁移旧的音频数据结构
      this.migrateAudioData();

      this.configLoaded = true;
    },

    // 重新加载配置
    async reloadConfig() {
      this.configLoaded = false;
      await this.initializeConfig(true);
      console.log("配置已重新加载");
    },

    // 迁移旧的音频数据结构到新的版本结构
    migrateAudioData() {
      this.conversations.forEach((conversation) => {
        if (!conversation || !conversation.messages) return;

        conversation.messages.forEach((message) => {
          // 如果消息还使用旧的audioUrl结构，迁移到新结构
          if (message.audioUrl && !message.audioVersions) {
            message.audioVersions = [
              {
                id: Date.now().toString(),
                url: message.audioUrl,
                timestamp: message.timestamp || new Date(),
                isDefault: true,
              },
            ];
            message.currentAudioVersion = 0;
            // 保留audioUrl以便兼容性，但主要使用新结构
          }

          // 确保新消息有正确的结构
          if (!message.audioVersions) {
            message.audioVersions = [];
          }
          if (message.currentAudioVersion === undefined) {
            message.currentAudioVersion =
              message.audioVersions.length > 0 ? 0 : -1;
          }
        });
      });
    },
  },
}; 