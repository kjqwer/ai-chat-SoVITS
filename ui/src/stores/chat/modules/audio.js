import { useApiStore } from "../../api.js";

export const audioModule = {
  state: () => ({
    loading: {
      generateAudio: false,
    },
    error: null,
  }),

  actions: {
    // 为消息生成语音
    async generateMessageAudio(
      conversationId,
      messageId,
      isRegenerate = false
    ) {
      try {
        const conversation = this.conversations.find(
          (conv) => conv.id === conversationId
        );
        if (!conversation) return;

        const message = conversation.messages.find(
          (msg) => msg.id === messageId
        );
        if (!message) return;

        // 设置生成状态
        message.audioGenerating = true;

        // 调用TTS API
        const apiStore = useApiStore();
        const audioBlob = await apiStore.textToSpeech(message.content);

        // 创建音频URL
        const audioUrl = URL.createObjectURL(audioBlob);

        // 创建新的语音版本
        const newVersion = {
          id: Date.now().toString(),
          url: audioUrl,
          timestamp: new Date(),
          isDefault: message.audioVersions.length === 0, // 第一个版本为默认版本
        };

        // 如果是重新生成，添加到版本列表；如果是第一次生成，也添加到版本列表
        message.audioVersions.push(newVersion);

        // 设置当前播放版本为最新生成的版本
        message.currentAudioVersion = message.audioVersions.length - 1;

        message.audioGenerating = false;

        return audioUrl;
      } catch (error) {
        const conversation = this.conversations.find(
          (conv) => conv.id === conversationId
        );
        const message = conversation?.messages.find(
          (msg) => msg.id === messageId
        );
        if (message) {
          message.audioGenerating = false;
        }

        console.error("Failed to generate audio for message:", error);
        throw error;
      }
    },

    // 切换语音版本
    switchAudioVersion(conversationId, messageId, versionIndex) {
      const conversation = this.conversations.find(
        (conv) => conv.id === conversationId
      );
      if (!conversation) return;

      const message = conversation.messages.find((msg) => msg.id === messageId);
      if (!message) return;

      if (versionIndex >= 0 && versionIndex < message.audioVersions.length) {
        message.currentAudioVersion = versionIndex;
      }
    },

    // 删除语音版本
    deleteAudioVersion(conversationId, messageId, versionIndex) {
      const conversation = this.conversations.find(
        (conv) => conv.id === conversationId
      );
      if (!conversation) return;

      const message = conversation.messages.find((msg) => msg.id === messageId);
      if (!message || !message.audioVersions) return;

      if (versionIndex >= 0 && versionIndex < message.audioVersions.length) {
        // 释放URL对象
        const version = message.audioVersions[versionIndex];
        if (version.url) {
          URL.revokeObjectURL(version.url);
        }

        // 删除版本
        message.audioVersions.splice(versionIndex, 1);

        // 调整当前播放版本索引
        if (message.currentAudioVersion === versionIndex) {
          // 如果删除的是当前播放的版本
          if (message.audioVersions.length === 0) {
            message.currentAudioVersion = -1;
          } else if (versionIndex >= message.audioVersions.length) {
            message.currentAudioVersion = message.audioVersions.length - 1;
          }
        } else if (message.currentAudioVersion > versionIndex) {
          // 如果删除的版本在当前版本之前，需要调整索引
          message.currentAudioVersion--;
        }
      }
    },

    // 清理音频资源
    cleanupAudioResources(conversationId = null) {
      const conversations = conversationId
        ? [this.conversations.find((conv) => conv.id === conversationId)]
        : this.conversations;

      conversations.forEach((conversation) => {
        if (!conversation) return;
        conversation.messages.forEach((message) => {
          // 清理新的音频版本结构
          if (message.audioVersions && message.audioVersions.length > 0) {
            message.audioVersions.forEach((version) => {
              if (version.url) {
                URL.revokeObjectURL(version.url);
              }
            });
            message.audioVersions = [];
            message.currentAudioVersion = -1;
          }

          // 兼容旧的音频结构
          if (message.audioUrl) {
            URL.revokeObjectURL(message.audioUrl);
            message.audioUrl = null;
          }
        });
      });
    },

    clearError() {
      this.error = null;
    },
  },
}; 