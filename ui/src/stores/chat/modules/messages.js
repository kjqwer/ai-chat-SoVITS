import { openaiClient, AI_CONFIG, initializeConfig } from "../core.js";
import { useApiStore } from "../../api.js";

export const messagesModule = {
  state: () => ({
    loading: {
      sendMessage: false,
      generateAudio: false,
    },
    error: null,
    autoGenerateAudio: true,
  }),

  actions: {
    // 发送消息给AI
    async sendMessage(content, conversationId = null) {
      try {
        // 确保配置已加载
        await initializeConfig();

        this.loading.sendMessage = true;
        this.error = null;

        // 如果没有指定对话ID，使用当前对话或创建新对话
        const targetConversationId =
          conversationId || this.currentConversationId;
        let conversation = this.conversations.find(
          (conv) => conv.id === targetConversationId
        );

        if (!conversation) {
          conversation = this.createConversation();
        }

        // 添加用户消息
        const userMessage = {
          id: Date.now().toString(),
          role: "user",
          content: content,
          timestamp: new Date(),
          audioVersions: [], // 改为支持多个语音版本
          currentAudioVersion: -1, // 当前播放的版本索引，-1表示没有音频
        };

        conversation.messages.push(userMessage);
        conversation.updatedAt = new Date();

        // 准备发送给OpenAI的消息
        const messages = [
          {
            role: "system",
            content: conversation.persona.prompt,
          },
          ...conversation.messages.map((msg) => ({
            role: msg.role,
            content: msg.content,
          })),
        ];

        // 调用OpenAI API
        const response = await openaiClient.post("/chat/completions", {
          model: AI_CONFIG.model,
          messages: messages,
          ...AI_CONFIG.defaultParams,
        });

        const aiResponse = response.data.choices[0].message.content;

        // 添加AI回复消息
        const aiMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: aiResponse,
          timestamp: new Date(),
          audioVersions: [], // 改为支持多个语音版本
          currentAudioVersion: -1, // 当前播放的版本索引，-1表示没有音频
          audioGenerating: false,
        };

        conversation.messages.push(aiMessage);
        conversation.updatedAt = new Date();

        // 自动生成标题（如果是第一条消息）
        if (conversation.messages.length === 2) {
          conversation.title = this.generateConversationTitle(content);
        }

        // 如果开启了自动生成语音，则生成AI回复的语音
        if (this.autoGenerateAudio) {
          this.generateMessageAudio(conversation.id, aiMessage.id);
        }

        return aiMessage;
      } catch (error) {
        this.error = error.response?.data?.error?.message || error.message;
        throw error;
      } finally {
        this.loading.sendMessage = false;
      }
    },

    // 重新生成AI回复
    async regenerateResponse(conversationId, messageIndex) {
      const conversation = this.conversations.find(
        (conv) => conv.id === conversationId
      );
      if (!conversation) return;

      // 找到要重新生成的消息（应该是AI消息）
      const targetMessage = conversation.messages[messageIndex];
      if (!targetMessage || targetMessage.role !== "assistant") return;

      // 回溯到该消息的前一条（用户消息）
      this.rollbackToMessage(conversationId, messageIndex - 1);

      // 获取最后一条用户消息
      const lastUserMessage =
        conversation.messages[conversation.messages.length - 1];
      if (lastUserMessage && lastUserMessage.role === "user") {
        // 重新发送消息
        await this.sendMessage(lastUserMessage.content, conversationId);
      }
    },

    // 切换自动生成语音
    toggleAutoGenerateAudio() {
      this.autoGenerateAudio = !this.autoGenerateAudio;
    },

    clearError() {
      this.error = null;
    },
  },
}; 