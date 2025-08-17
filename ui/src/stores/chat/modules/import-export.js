export const importExportModule = {
  state: () => ({
    loading: {
      import: false,
      export: false,
    },
    error: null,
  }),

  actions: {
    // 导出对话
    exportConversation(conversationId) {
      const conversation = this.conversations.find(
        (conv) => conv.id === conversationId
      );
      if (!conversation) return null;

      const exportData = {
        title: conversation.title,
        persona: conversation.persona.name,
        createdAt: conversation.createdAt,
        messages: conversation.messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp,
        })),
      };

      const dataStr = JSON.stringify(exportData, null, 2);
      const dataBlob = new Blob([dataStr], { type: "application/json" });

      const link = document.createElement("a");
      link.href = URL.createObjectURL(dataBlob);
      link.download = `conversation_${conversation.title.replace(
        /[^a-zA-Z0-9]/g,
        "_"
      )}_${Date.now()}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      URL.revokeObjectURL(link.href);
    },

    // 导入对话
    async importConversation(file) {
      try {
        this.loading.import = true;
        this.error = null;

        if (!file || file.type !== "application/json") {
          throw new Error("请选择有效的JSON文件");
        }

        const text = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (e) => resolve(e.target.result);
          reader.onerror = (e) => reject(new Error("文件读取失败"));
          reader.readAsText(file);
        });

        const importData = JSON.parse(text);

        // 验证导入数据格式
        if (
          !importData.title ||
          !importData.messages ||
          !Array.isArray(importData.messages)
        ) {
          throw new Error("无效的对话文件格式");
        }

        // 查找匹配的人格，如果没有找到则使用默认人格
        let persona = this.personas.find((p) => p.name === importData.persona);
        if (!persona) {
          persona = this.currentPersona || this.personas[0];
        }

        // 创建新对话
        const conversation = {
          id: Date.now().toString(),
          title: importData.title + " (导入)",
          persona: persona,
          createdAt: importData.createdAt
            ? new Date(importData.createdAt)
            : new Date(),
          updatedAt: new Date(),
          messages: importData.messages.map((msg) => ({
            id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
            audioVersions: [],
            currentAudioVersion: -1,
            audioGenerating: false,
          })),
        };

        // 添加到对话列表
        this.conversations.unshift(conversation);

        // 切换到导入的对话
        this.currentConversationId = conversation.id;

        return conversation;
      } catch (error) {
        this.error = error.message;
        console.error("导入对话失败:", error);
        throw error;
      } finally {
        this.loading.import = false;
      }
    },

    // 批量导入对话
    async importMultipleConversations(files) {
      const results = {
        success: 0,
        failed: 0,
        errors: [],
      };

      for (let i = 0; i < files.length; i++) {
        try {
          await this.importConversation(files[i]);
          results.success++;
        } catch (error) {
          results.failed++;
          results.errors.push(`${files[i].name}: ${error.message}`);
        }
      }

      return results;
    },

    clearError() {
      this.error = null;
    },
  },
}; 