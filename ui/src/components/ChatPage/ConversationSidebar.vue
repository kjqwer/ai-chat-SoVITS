<template>
  <div class="conversation-sidebar">
    <div class="sidebar-header">
      <el-button type="primary" @click="createNewConversation" style="width: 100%; margin-bottom: 10px;" :icon="Plus">
        新建对话
      </el-button>

      <!-- 导入导出按钮组 -->
      <div class="import-export-actions">
        <el-button size="small" @click="triggerImport" :icon="Upload" style="flex: 1;">
          导入对话
        </el-button>
        <el-button size="small" @click="$emit('showExportDialog')" :icon="Download" style="flex: 1;"
          :disabled="chatStore.conversations.length === 0">
          批量导出
        </el-button>
      </div>

      <!-- 隐藏的文件输入 -->
      <input ref="fileInput" type="file" accept=".json" multiple style="display: none" @change="handleFileImport" />
    </div>

    <div class="persona-selector">
      <el-select v-model="currentPersonaId" placeholder="选择AI人格" style="width: 100%" @change="handlePersonaChange">
        <el-option v-for="persona in chatStore.personas" :key="persona.id" :label="persona.name" :value="persona.id">
          <div>
            <div style="font-weight: 500;">{{ persona.name }}</div>
            <div style="font-size: 12px; color: #909399;">{{ persona.description }}</div>
          </div>
        </el-option>
      </el-select>
    </div>

    <div class="conversations-list">
      <div v-for="conversation in chatStore.conversations" :key="conversation.id" class="conversation-item"
        :class="{ active: conversation.id === chatStore.currentConversationId }"
        @click="switchConversation(conversation.id)">
        <div class="conversation-content">
          <div class="conversation-title">{{ conversation.title }}</div>
          <div class="conversation-info">
            <span class="persona-name">{{ conversation.persona.name }}</span>
            <span class="message-count">{{ conversation.messages.length }}条消息</span>
          </div>
        </div>
        <div class="conversation-actions">
          <el-dropdown @click.stop>
            <el-button text :icon="More" size="small" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="exportConversation(conversation.id)">
                  <el-icon>
                    <Download />
                  </el-icon>
                  导出对话
                </el-dropdown-item>
                <el-dropdown-item @click="deleteConversation(conversation.id)" divided>
                  <el-icon>
                    <Delete />
                  </el-icon>
                  删除对话
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useChatStore } from '../../stores/chat.js'
import {
  Plus,
  More,
  Download,
  Upload,
  Delete
} from '@element-plus/icons-vue'

const chatStore = useChatStore()

// 响应式数据
const currentPersonaId = ref('')
const fileInput = ref(null)

// 事件定义
const emit = defineEmits(['showExportDialog'])

// 创建新对话
const createNewConversation = () => {
  chatStore.createConversation()
}

// 切换对话
const switchConversation = (conversationId) => {
  chatStore.switchConversation(conversationId)
}

// 删除对话
const deleteConversation = async (conversationId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？', '确认删除', {
      type: 'warning'
    })

    chatStore.deleteConversation(conversationId)
    ElMessage.success('对话已删除')
  } catch {
    // 用户取消删除
  }
}

// 导出对话
const exportConversation = (conversationId) => {
  chatStore.exportConversation(conversationId)
  ElMessage.success('对话已导出')
}

// 处理人格变化
const handlePersonaChange = async (personaId) => {
  try {
    const persona = chatStore.personas.find(p => p.id === personaId)
    if (persona) {
      await chatStore.setPersona(persona)
    }
  } catch (error) {
    console.error('设置人格失败:', error)
  }
}

// 触发文件导入
const triggerImport = () => {
  fileInput.value?.click()
}

// 处理文件导入
const handleFileImport = async (event) => {
  const files = Array.from(event.target.files)
  if (files.length === 0) return

  try {
    if (files.length === 1) {
      // 单文件导入
      await chatStore.importConversation(files[0])
      ElMessage.success('对话导入成功')
    } else {
      // 批量导入
      const results = await chatStore.importMultipleConversations(files)

      if (results.success > 0) {
        ElMessage.success(`成功导入 ${results.success} 个对话`)
      }

      if (results.failed > 0) {
        const errorMessage = `导入失败 ${results.failed} 个文件:\n${results.errors.join('\n')}`
        ElMessage.error(errorMessage)
      }
    }
  } catch (error) {
    ElMessage.error(`导入失败: ${error.message}`)
  } finally {
    // 清空文件输入
    event.target.value = ''
  }
}

// 监听store中的当前人格变化，同步到下拉框
watch(
  () => chatStore.currentPersona,
  (newPersona) => {
    if (newPersona && newPersona.id) {
      currentPersonaId.value = newPersona.id
    }
  },
  { immediate: true }
)

// 监听下拉框选择变化，同步到store
watch(
  () => currentPersonaId.value,
  (newPersonaId) => {
    if (newPersonaId) {
      const persona = chatStore.personas.find(p => p.id === newPersonaId)
      if (persona && persona.id !== chatStore.currentPersona?.id) {
        chatStore.currentPersona = persona
      }
    }
  }
)
</script>

<style scoped>
/* 左侧边栏 */
.conversation-sidebar {
  width: 300px;
  background-color: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.import-export-actions {
  display: flex;
  gap: 8px;
}

.persona-selector {
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  border-bottom: 1px solid #f8f8f8;
  transition: background-color 0.3s;
}

.conversation-item:hover {
  background-color: #f8f9fa;
}

.conversation-item.active {
  background-color: #e6f7ff;
  border-right: 3px solid #409eff;
}

.conversation-content {
  flex: 1;
  min-width: 0;
}

.conversation-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conversation-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.conversation-actions {
  margin-left: 10px;
}

/* 滚动条样式 */
.conversations-list::-webkit-scrollbar {
  width: 6px;
}

.conversations-list::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.conversations-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.conversations-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .conversation-sidebar {
    width: 250px;
  }
}
</style>