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
        console.log('开始生成音频:', messageId);

        // 调用TTS API生成音频并保存到后端
        const ttsRequest = {
          text: message.content,
          conversation_id: conversationId,
          message_id: messageId
        };

        const response = await fetch('/tts/conversation', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(ttsRequest),
        });

        if (!response.ok) {
          throw new Error(`TTS生成失败: ${response.status}`);
        }

        const audioResult = await response.json();

        // 重新加载对话数据以获取最新的音频版本信息
        await this.loadConversations();

        // 更新当前消息的音频生成状态
        const updatedConversation = this.conversations.find(
          (conv) => conv.id === conversationId
        );
        const updatedMessage = updatedConversation?.messages.find(
          (msg) => msg.id === messageId
        );
        if (updatedMessage) {
          updatedMessage.audioGenerating = false;
          
          // 如果是重新生成，将当前版本设置为最新生成的版本
          if (isRegenerate && updatedMessage.audioVersions?.length > 0) {
            const latestVersionIndex = updatedMessage.audioVersions.length - 1
            await this.switchAudioVersion(conversationId, messageId, latestVersionIndex)
            console.log('已切换到最新生成的音频版本:', latestVersionIndex)
          }
        }

        console.log('音频生成完成:', audioResult.audio_url);
        return audioResult.audio_url;
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
    async switchAudioVersion(conversationId, messageId, versionIndex) {
      try {
        const conversation = this.conversations.find(
          (conv) => conv.id === conversationId
        );
        if (!conversation) return;

        const message = conversation.messages.find((msg) => msg.id === messageId);
        if (!message) return;

        if (versionIndex >= 0 && versionIndex < message.audioVersions.length) {
          const response = await fetch(`/api/conversations/${conversationId}/messages/${messageId}/audio/current?version_index=${versionIndex}`, {
            method: 'PUT',
          });

          if (!response.ok) {
            throw new Error(`切换音频版本失败: ${response.status}`);
          }

          // 重新加载对话数据
          await this.loadConversations();
        }
      } catch (error) {
        console.error('切换音频版本失败:', error);
        throw error;
      }
    },

    // 删除语音版本
    async deleteAudioVersion(conversationId, messageId, versionIndex) {
      try {
        const conversation = this.conversations.find(
          (conv) => conv.id === conversationId
        );
        if (!conversation) return;

        const message = conversation.messages.find((msg) => msg.id === messageId);
        if (!message || !message.audioVersions) return;

        if (versionIndex >= 0 && versionIndex < message.audioVersions.length) {
          const version = message.audioVersions[versionIndex];
          
          const response = await fetch(`/api/conversations/${conversationId}/messages/${messageId}/audio/${version.id}`, {
            method: 'DELETE',
          });

          if (!response.ok) {
            throw new Error(`删除音频版本失败: ${response.status}`);
          }

          // 重新加载对话数据
          await this.loadConversations();
        }
      } catch (error) {
        console.error('删除音频版本失败:', error);
        throw error;
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