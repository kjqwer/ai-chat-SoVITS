import { useApiStore } from "../../api.js";

export const conversationsModule = {
  state: () => ({
    conversations: [],
    currentConversationId: null,
    loading: {
      sendMessage: false,
    },
    error: null,
  }),

  getters: {
    // 获取当前对话
    currentConversation: (state) => {
      if (!state.currentConversationId) return null;
      return state.conversations.find(
        (conv) => conv.id === state.currentConversationId
      );
    },

    // 获取当前对话的消息列表
    currentMessages: (state) => {
      const conversation = state.conversations.find(
        (conv) => conv.id === state.currentConversationId
      );
      return conversation ? conversation.messages : [];
    },
  },

  actions: {
    // 创建新对话
    createConversation(title = null, persona = null) {
      const conversation = {
        id: Date.now().toString(),
        title: title || `对话 ${this.conversations.length + 1}`,
        persona: persona,
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      this.conversations.unshift(conversation);
      this.currentConversationId = conversation.id;

      return conversation;
    },

    // 删除对话
    deleteConversation(conversationId) {
      const index = this.conversations.findIndex(
        (conv) => conv.id === conversationId
      );
      if (index !== -1) {
        this.conversations.splice(index, 1);

        // 如果删除的是当前对话，切换到下一个对话
        if (this.currentConversationId === conversationId) {
          if (this.conversations.length > 0) {
            this.currentConversationId = this.conversations[0].id;
          } else {
            this.currentConversationId = null;
          }
        }
      }
    },

    // 切换对话
    switchConversation(conversationId) {
      this.currentConversationId = conversationId;
    },

    // 回溯到指定消息
    rollbackToMessage(conversationId, messageIndex) {
      const conversation = this.conversations.find(
        (conv) => conv.id === conversationId
      );
      if (!conversation) return;

      // 删除指定索引之后的所有消息
      conversation.messages = conversation.messages.slice(0, messageIndex + 1);
      conversation.updatedAt = new Date();
    },

    // 删除指定消息
    deleteMessage(conversationId, messageIndex) {
      const conversation = this.conversations.find(
        (conv) => conv.id === conversationId
      );
      if (!conversation) return;

      conversation.messages.splice(messageIndex, 1);
      conversation.updatedAt = new Date();
    },

    // 生成对话标题
    generateConversationTitle(firstMessage) {
      // 简单的标题生成逻辑，取前20个字符
      const title =
        firstMessage.length > 20
          ? firstMessage.substring(0, 20) + "..."
          : firstMessage;
      return title;
    },

    // 更新对话人格
    updateConversationPersona(conversationId, persona) {
      const conversation = this.conversations.find(
        (conv) => conv.id === conversationId
      );
      if (conversation) {
        conversation.persona = persona;
        conversation.updatedAt = new Date();
      }
    },

    clearError() {
      this.error = null;
    },
  },
}; 