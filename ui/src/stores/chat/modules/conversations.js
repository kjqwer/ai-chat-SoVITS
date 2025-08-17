import { useApiStore } from "../../api.js";

export const conversationsModule = {
  state: () => ({
    conversations: [],
    currentConversationId: null,
    loading: {
      sendMessage: false,
      loadConversations: false,
      createConversation: false,
      deleteConversation: false,
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
    // 从后端加载所有对话
    async loadConversations() {
      try {
        this.loading.loadConversations = true;
        this.error = null;

        const response = await fetch('/api/conversations/');
        if (!response.ok) {
          throw new Error(`加载对话失败: ${response.status}`);
        }

        const conversations = await response.json();
        this.conversations = conversations;

        // 如果没有当前对话但有对话列表，选择第一个
        if (!this.currentConversationId && conversations.length > 0) {
          this.currentConversationId = conversations[0].id;
        }

        return conversations;
      } catch (error) {
        this.error = error.message;
        console.error('加载对话失败:', error);
        throw error;
      } finally {
        this.loading.loadConversations = false;
      }
    },

    // 创建新对话
    async createConversation(title = null, persona = null) {
      try {
        this.loading.createConversation = true;
        this.error = null;

        const conversationData = {
          title: title || `对话 ${this.conversations.length + 1}`,
          persona: persona || this.currentPersona
        };

        const response = await fetch('/api/conversations/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(conversationData),
        });

        if (!response.ok) {
          throw new Error(`创建对话失败: ${response.status}`);
        }

        const conversation = await response.json();
        this.conversations.unshift(conversation);
        this.currentConversationId = conversation.id;

        return conversation;
      } catch (error) {
        this.error = error.message;
        console.error('创建对话失败:', error);
        throw error;
      } finally {
        this.loading.createConversation = false;
      }
    },

    // 删除对话
    async deleteConversation(conversationId) {
      try {
        this.loading.deleteConversation = true;
        this.error = null;

        const response = await fetch(`/api/conversations/${conversationId}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          throw new Error(`删除对话失败: ${response.status}`);
        }

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
      } catch (error) {
        this.error = error.message;
        console.error('删除对话失败:', error);
        throw error;
      } finally {
        this.loading.deleteConversation = false;
      }
    },

    // 切换对话
    switchConversation(conversationId) {
      this.currentConversationId = conversationId;
    },

    // 回溯到指定消息
    async rollbackToMessage(conversationId, messageIndex) {
      try {
        this.error = null;

        const response = await fetch(`/api/conversations/${conversationId}/rollback/${messageIndex}`, {
          method: 'POST',
        });

        if (!response.ok) {
          throw new Error(`回溯失败: ${response.status}`);
        }

        // 重新加载对话数据
        await this.loadConversations();
      } catch (error) {
        this.error = error.message;
        console.error('回溯失败:', error);
        throw error;
      }
    },

    // 删除指定消息
    async deleteMessage(conversationId, messageIndex) {
      try {
        this.error = null;

        const conversation = this.conversations.find(
          (conv) => conv.id === conversationId
        );
        if (!conversation) return;

        const message = conversation.messages[messageIndex];
        if (!message) return;

        const response = await fetch(`/api/conversations/${conversationId}/messages/${message.id}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          throw new Error(`删除消息失败: ${response.status}`);
        }

        // 重新加载对话数据
        await this.loadConversations();
      } catch (error) {
        this.error = error.message;
        console.error('删除消息失败:', error);
        throw error;
      }
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
    async updateConversationPersona(conversationId, persona) {
      try {
        const conversation = this.conversations.find(
          (conv) => conv.id === conversationId
        );
        if (conversation) {
          // 更新后端数据
          const response = await fetch(`/api/conversations/${conversationId}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ persona: persona }),
          });

          if (!response.ok) {
            throw new Error(`更新对话人格失败: ${response.status}`);
          }

          // 重新加载对话数据以确保同步
          await this.loadConversations();
        }
      } catch (error) {
        console.error('更新对话人格失败:', error);
        throw error;
      }
    },

    clearError() {
      this.error = null;
    },
  },
}; 