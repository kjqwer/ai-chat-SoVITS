<template>
  <div class="chat-page">
    <div class="chat-container">
      <!-- 左侧对话列表 -->
      <div class="conversation-sidebar">
        <div class="sidebar-header">
          <el-button
            type="primary"
            @click="createNewConversation"
            style="width: 100%"
            :icon="Plus"
          >
            新建对话
          </el-button>
        </div>

        <div class="persona-selector">
          <el-select
            v-model="chatStore.currentPersona"
            placeholder="选择AI人格"
            style="width: 100%"
            @change="handlePersonaChange"
          >
            <el-option
              v-for="persona in chatStore.personas"
              :key="persona.id"
              :label="persona.name"
              :value="persona"
            >
              <div>
                <div style="font-weight: 500;">{{ persona.name }}</div>
                <div style="font-size: 12px; color: #909399;">{{ persona.description }}</div>
              </div>
            </el-option>
          </el-select>
        </div>

        <div class="conversations-list">
          <div
            v-for="conversation in chatStore.conversations"
            :key="conversation.id"
            class="conversation-item"
            :class="{ active: conversation.id === chatStore.currentConversationId }"
            @click="switchConversation(conversation.id)"
          >
            <div class="conversation-content">
              <div class="conversation-title">{{ conversation.title }}</div>
              <div class="conversation-info">
                <span class="persona-name">{{ conversation.persona.name }}</span>
                <span class="message-count">{{ conversation.messages.length }}条消息</span>
              </div>
            </div>
            <div class="conversation-actions">
              <el-dropdown @click.stop>
                <el-button
                  text
                  :icon="More"
                  size="small"
                />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="exportConversation(conversation.id)">
                      <el-icon><Download /></el-icon>
                      导出对话
                    </el-dropdown-item>
                    <el-dropdown-item @click="deleteConversation(conversation.id)" divided>
                      <el-icon><Delete /></el-icon>
                      删除对话
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧聊天区域 -->
      <div class="chat-main">
        <!-- 聊天头部 -->
        <div class="chat-header">
          <div class="chat-title">
            <h3>{{ currentConversation?.title || 'AI对话' }}</h3>
            <div class="chat-info">
              <span v-if="currentConversation">
                当前人格: {{ currentConversation.persona.name }}
              </span>
            </div>
          </div>
          <div class="chat-controls">
            <el-switch
              v-model="chatStore.autoGenerateAudio"
              active-text="自动语音"
              inactive-text=""
              @change="chatStore.toggleAutoGenerateAudio"
            />
          </div>
        </div>

        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesContainer">
          <div v-if="!currentConversation || currentMessages.length === 0" class="empty-chat">
            <el-empty description="开始新的对话吧！">
              <template #image>
                <el-icon size="60" color="#409eff"><ChatDotRound /></el-icon>
              </template>
            </el-empty>
          </div>
          
          <div v-else class="messages-list">
            <div
              v-for="(message, index) in currentMessages"
              :key="message.id"
              class="message-item"
              :class="{ 'user-message': message.role === 'user', 'ai-message': message.role === 'assistant' }"
            >
              <div class="message-content">
                <div class="message-header">
                                     <div class="message-role">
                     <el-icon v-if="message.role === 'user'"><User /></el-icon>
                     <el-icon v-else><Avatar /></el-icon>
                     {{ message.role === 'user' ? '你' : currentConversation.persona.name }}
                   </div>
                  <div class="message-time">
                    {{ formatTime(message.timestamp) }}
                  </div>
                </div>
                
                <div class="message-text">{{ message.content }}</div>
                
                <!-- AI消息的音频播放 -->
                <div v-if="message.role === 'assistant'" class="message-audio">
                  <div v-if="message.audioGenerating" class="audio-generating">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    正在生成语音...
                  </div>
                  <div v-else-if="message.audioUrl" class="audio-player">
                    <audio controls style="width: 100%">
                      <source :src="message.audioUrl" type="audio/wav">
                    </audio>
                  </div>
                  <div v-else class="audio-actions">
                    <el-button
                      size="small"
                      text
                      @click="generateAudio(currentConversation.id, message.id)"
                      :loading="message.audioGenerating"
                    >
                      <el-icon><Microphone /></el-icon>
                      生成语音
                    </el-button>
                  </div>
                </div>
                
                <!-- 消息操作 -->
                <div class="message-actions">
                  <el-dropdown @click.stop>
                    <el-button text size="small" :icon="More" />
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="copyMessage(message.content)">
                          <el-icon><DocumentCopy /></el-icon>
                          复制
                        </el-dropdown-item>
                        <el-dropdown-item 
                          v-if="message.role === 'assistant'"
                          @click="regenerateResponse(index)"
                        >
                          <el-icon><Refresh /></el-icon>
                          重新生成
                        </el-dropdown-item>
                                                 <el-dropdown-item @click="rollbackToMessage(index)" divided>
                           <el-icon><ArrowLeft /></el-icon>
                           回溯到此处
                         </el-dropdown-item>
                        <el-dropdown-item @click="deleteMessage(index)">
                          <el-icon><Delete /></el-icon>
                          删除消息
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <div class="input-container">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="输入你的消息..."
              @keydown.ctrl.enter="sendMessage"
              :disabled="chatStore.loading.sendMessage"
            />
            <div class="input-actions">
              <div class="input-hint">Ctrl + Enter 发送</div>
              <el-button
                type="primary"
                @click="sendMessage"
                :loading="chatStore.loading.sendMessage"
                :disabled="!inputMessage.trim()"
              >
                <el-icon><Position /></el-icon>
                发送
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useChatStore } from '../stores/chat.js'
import {
  Plus,
  More,
  Download,
  Delete,
  ChatDotRound,
  User,
  Avatar,
  Loading,
  Microphone,
  DocumentCopy,
  Refresh,
  ArrowLeft,
  Position
} from '@element-plus/icons-vue'

const chatStore = useChatStore()

// 响应式数据
const inputMessage = ref('')
const messagesContainer = ref(null)

// 计算属性
const currentConversation = computed(() => chatStore.currentConversation)
const currentMessages = computed(() => chatStore.currentMessages)

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
const handlePersonaChange = (persona) => {
  chatStore.setPersona(persona)
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  
  try {
    await chatStore.sendMessage(inputMessage.value)
    inputMessage.value = ''
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (error) {
    ElMessage.error(`发送消息失败: ${error.message}`)
  }
}

// 生成音频
const generateAudio = async (conversationId, messageId) => {
  try {
    await chatStore.generateMessageAudio(conversationId, messageId)
    ElMessage.success('语音生成成功')
  } catch (error) {
    ElMessage.error('语音生成失败')
  }
}

// 复制消息
const copyMessage = async (content) => {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 重新生成回复
const regenerateResponse = async (messageIndex) => {
  try {
    await chatStore.regenerateResponse(chatStore.currentConversationId, messageIndex)
    await nextTick()
    scrollToBottom()
  } catch (error) {
    ElMessage.error('重新生成失败')
  }
}

// 回溯到消息
const rollbackToMessage = async (messageIndex) => {
  try {
    await ElMessageBox.confirm(
      `确定要回溯到第 ${messageIndex + 1} 条消息吗？这将删除后面的所有消息。`,
      '确认回溯',
      { type: 'warning' }
    )
    
    chatStore.rollbackToMessage(chatStore.currentConversationId, messageIndex)
    ElMessage.success('已回溯到指定消息')
  } catch {
    // 用户取消
  }
}

// 删除消息
const deleteMessage = async (messageIndex) => {
  try {
    await ElMessageBox.confirm('确定要删除这条消息吗？', '确认删除', {
      type: 'warning'
    })
    
    chatStore.deleteMessage(chatStore.currentConversationId, messageIndex)
    ElMessage.success('消息已删除')
  } catch {
    // 用户取消
  }
}

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) { // 小于1分钟
    return '刚刚'
  } else if (diff < 3600000) { // 小于1小时
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) { // 小于1天
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString().slice(0, 5)
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 监听消息变化，自动滚动到底部
watch(
  () => currentMessages.value.length,
  () => {
    nextTick(() => {
      scrollToBottom()
    })
  }
)

// 组件挂载时初始化配置并创建第一个对话（如果没有的话）
onMounted(async () => {
  await chatStore.initializeConfig()
  
  if (chatStore.conversations.length === 0) {
    chatStore.createConversation('欢迎对话')
  }
})
</script>

<style scoped>
.chat-page {
  height: 100vh;
  background-color: #f5f5f5;
}

.chat-container {
  display: flex;
  height: 100%;
}

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

/* 聊天主区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: white;
}

.chat-header {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-title h3 {
  margin: 0 0 5px 0;
  color: #303133;
}

.chat-info {
  font-size: 14px;
  color: #909399;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-chat {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-item {
  display: flex;
  flex-direction: column;
}

.message-item.user-message {
  align-items: flex-end;
}

.message-item.ai-message {
  align-items: flex-start;
}

.message-content {
  max-width: 70%;
  position: relative;
}

.user-message .message-content {
  background-color: #409eff;
  color: white;
  border-radius: 18px 18px 4px 18px;
  padding: 12px 16px;
}

.ai-message .message-content {
  background-color: #f0f2f5;
  color: #303133;
  border-radius: 18px 18px 18px 4px;
  padding: 12px 16px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.user-message .message-header {
  color: rgba(255, 255, 255, 0.8);
}

.ai-message .message-header {
  color: #909399;
}

.message-role {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

.message-text {
  line-height: 1.5;
  word-wrap: break-word;
}

.message-audio {
  margin-top: 10px;
}

.audio-generating {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.audio-player audio {
  max-width: 300px;
}

.audio-actions {
  margin-top: 5px;
}

.message-actions {
  position: absolute;
  top: -5px;
  right: -35px;
  opacity: 0;
  transition: opacity 0.3s;
}

.message-content:hover .message-actions {
  opacity: 1;
}

/* 输入区域 */
.input-area {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  background-color: #fafafa;
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.input-hint {
  font-size: 12px;
  color: #909399;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .conversation-sidebar {
    width: 250px;
  }
  
  .message-content {
    max-width: 85%;
  }
}

/* 滚动条样式 */
.conversations-list::-webkit-scrollbar,
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.conversations-list::-webkit-scrollbar-track,
.messages-container::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.conversations-list::-webkit-scrollbar-thumb,
.messages-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.conversations-list::-webkit-scrollbar-thumb:hover,
.messages-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style> 