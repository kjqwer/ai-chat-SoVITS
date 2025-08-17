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
          conversation = await this.createConversationWithCurrentPersona();
        }

        // 立即添加用户消息到后端并显示
        const userMessageData = {
          role: "user",
          content: content
        };

        const userResponse = await fetch(`/api/conversations/${conversation.id}/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(userMessageData),
        });

        if (!userResponse.ok) {
          throw new Error(`添加用户消息失败: ${userResponse.status}`);
        }

        const userMessage = await userResponse.json();

        // 立即重新加载对话数据以显示用户消息
        await this.loadConversations();

        // 重新获取最新的对话数据
        const updatedConversation = this.conversations.find(
          (conv) => conv.id === conversation.id
        );

        // 准备发送给OpenAI的消息
        const messages = [
          {
            role: "system",
            content: updatedConversation.persona.prompt,
          },
          ...updatedConversation.messages.map((msg) => ({
            role: msg.role,
            content: msg.content,
          })),
          {
            role: "user",
            content: content,
          }
        ];

        // 调用OpenAI API
        const response = await openaiClient.post("/chat/completions", {
          model: AI_CONFIG.model,
          messages: messages,
          ...AI_CONFIG.defaultParams,
        });

        const aiResponse = response.data.choices[0].message.content;

        // 添加AI回复消息到后端
        const aiMessageData = {
          role: "assistant",
          content: aiResponse
        };

        const aiResponse2 = await fetch(`/api/conversations/${conversation.id}/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(aiMessageData),
        });

        if (!aiResponse2.ok) {
          throw new Error(`添加AI消息失败: ${aiResponse2.status}`);
        }

        const aiMessage = await aiResponse2.json();

        // 自动生成标题（如果是第一条消息）
        if (conversation.messages.length === 1) { // 修改为1，因为现在用户消息已经添加了
          const title = this.generateConversationTitle(content);
          await fetch(`/api/conversations/${conversation.id}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title: title }),
          });
        }

        // 重新加载对话数据以显示AI消息
        await this.loadConversations();

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