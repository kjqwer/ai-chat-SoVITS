<template>
  <el-dialog v-model="dialogVisible" title="批量导出对话" width="500px" @close="handleClose">
    <div class="export-dialog-content">
      <p>选择要导出的对话:</p>
      <div class="conversation-checkboxes">
        <el-checkbox v-model="selectAllConversations" @change="handleSelectAllChange" style="margin-bottom: 10px;">
          全选
        </el-checkbox>
        <div class="checkbox-list">
          <el-checkbox v-for="conversation in chatStore.conversations" :key="conversation.id"
            v-model="selectedConversations" :label="conversation.id" style="display: block; margin-bottom: 8px;">
            {{ conversation.title }} ({{ conversation.messages.length }}条消息)
          </el-checkbox>
        </div>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="exportSelectedConversations" :disabled="selectedConversations.length === 0">
          导出选中的对话 ({{ selectedConversations.length }})
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useChatStore } from '../../stores/chat.js'

const chatStore = useChatStore()

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

// 事件定义
const emit = defineEmits(['update:modelValue'])

// 响应式数据
const dialogVisible = ref(props.modelValue)
const selectedConversations = ref([])
const selectAllConversations = ref(false)

// 监听modelValue变化
watch(
  () => props.modelValue,
  (newVal) => {
    dialogVisible.value = newVal
  }
)

// 监听dialogVisible变化
watch(
  () => dialogVisible.value,
  (newVal) => {
    emit('update:modelValue', newVal)
  }
)

// 全选/取消全选对话
const handleSelectAllChange = (value) => {
  if (value) {
    selectedConversations.value = chatStore.conversations.map(conv => conv.id)
  } else {
    selectedConversations.value = []
  }
}

// 导出选中的对话
const exportSelectedConversations = () => {
  if (selectedConversations.value.length === 0) return

  try {
    if (selectedConversations.value.length === 1) {
      // 单个对话导出
      chatStore.exportConversation(selectedConversations.value[0])
      ElMessage.success('对话导出成功')
    } else {
      // 批量导出
      const exportData = selectedConversations.value.map(id => {
        const conversation = chatStore.conversations.find(conv => conv.id === id)
        if (!conversation) return null

        return {
          title: conversation.title,
          persona: conversation.persona.name,
          createdAt: conversation.createdAt,
          messages: conversation.messages.map(msg => ({
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp
          }))
        }
      }).filter(Boolean)

      const dataStr = JSON.stringify(exportData, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })

      const link = document.createElement('a')
      link.href = URL.createObjectURL(dataBlob)
      link.download = `conversations_batch_${Date.now()}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      URL.revokeObjectURL(link.href)
      ElMessage.success(`成功导出 ${selectedConversations.value.length} 个对话`)
    }

    // 关闭对话框并重置选择
    handleClose()
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 关闭对话框
const handleClose = () => {
  dialogVisible.value = false
  selectedConversations.value = []
  selectAllConversations.value = false
}

// 监听选中对话的变化，自动更新全选状态
watch(
  () => selectedConversations.value.length,
  (newLength) => {
    const totalConversations = chatStore.conversations.length
    selectAllConversations.value = newLength > 0 && newLength === totalConversations
  }
)
</script>

<style scoped>
/* 导出对话框样式 */
.export-dialog-content {
  max-height: 400px;
  overflow-y: auto;
}

.conversation-checkboxes {
  padding: 10px 0;
}

.checkbox-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
  background-color: #fafafa;
}

.checkbox-list .el-checkbox {
  width: 100%;
  margin-right: 0;
}
</style>