<template>
  <div class="messages-container" ref="messagesContainer">
    <div v-if="!currentConversation || currentMessages.length === 0" class="empty-chat">
      <el-empty description="开始新的对话吧！">
        <template #image>
          <el-icon size="60" color="#409eff">
            <ChatDotRound />
          </el-icon>
        </template>
      </el-empty>
    </div>

    <div v-else class="messages-list">
      <div v-for="(message, index) in currentMessages" :key="message.id" class="message-item"
        :class="{ 'user-message': message.role === 'user', 'ai-message': message.role === 'assistant' }">
        <div class="message-content">
          <div class="message-header">
            <div class="message-role">
              <el-icon v-if="message.role === 'user'">
                <User />
              </el-icon>
              <el-icon v-else>
                <Avatar />
              </el-icon>
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
              <el-icon class="is-loading">
                <Loading />
              </el-icon>
              正在生成语音...
            </div>
            <div v-else-if="message.audioVersions && message.audioVersions.length > 0" class="audio-player">
              <!-- 当前版本音频播放器 -->
              <audio v-if="message.currentAudioVersion >= 0 && message.audioVersions[message.currentAudioVersion]"
                :key="`${message.id}-${message.currentAudioVersion}`" controls style="width: 100%">
                <source :src="message.audioVersions[message.currentAudioVersion].url" type="audio/wav">
              </audio>

              <!-- 版本切换和管理 -->
              <div v-if="message.audioVersions.length > 1" class="audio-versions">
                <div class="versions-header">
                  <span class="versions-label">语音版本 ({{ message.audioVersions.length }}个):</span>
                </div>
                <div class="versions-list">
                  <div v-for="(version, versionIndex) in message.audioVersions" :key="version.id" class="version-item"
                    :class="{ active: versionIndex === message.currentAudioVersion }">
                    <el-button size="small" :type="versionIndex === message.currentAudioVersion ? 'primary' : 'default'"
                      @click="$emit('switchAudioVersion', currentConversation.id, message.id, versionIndex)">
                      版本{{ versionIndex + 1 }}
                      <span v-if="version.isDefault" class="default-tag">(默认)</span>
                    </el-button>
                    <el-button size="small" text type="danger"
                      @click="$emit('deleteAudioVersion', currentConversation.id, message.id, versionIndex)"
                      v-if="message.audioVersions.length > 1">
                      <el-icon>
                        <Delete />
                      </el-icon>
                    </el-button>
                  </div>
                </div>
              </div>

              <!-- 重新生成语音按钮 -->
              <div class="audio-actions">
                <el-button size="small" text @click="$emit('generateAudio', currentConversation.id, message.id, true)"
                  :loading="message.audioGenerating">
                  <el-icon>
                    <Refresh />
                  </el-icon>
                  重新生成语音
                </el-button>
              </div>
            </div>
            <div v-else class="audio-actions">
              <el-button size="small" text @click="$emit('generateAudio', currentConversation.id, message.id)"
                :loading="message.audioGenerating">
                <el-icon>
                  <Microphone />
                </el-icon>
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
                    <el-icon>
                      <DocumentCopy />
                    </el-icon>
                    复制
                  </el-dropdown-item>
                  <el-dropdown-item v-if="message.role === 'assistant'" @click="$emit('regenerateResponse', index)">
                    <el-icon>
                      <Refresh />
                    </el-icon>
                    重新生成
                  </el-dropdown-item>
                  <el-dropdown-item @click="$emit('rollbackToMessage', index)" divided>
                    <el-icon>
                      <ArrowLeft />
                    </el-icon>
                    回溯到此处
                  </el-dropdown-item>
                  <el-dropdown-item @click="$emit('deleteMessage', index)">
                    <el-icon>
                      <Delete />
                    </el-icon>
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
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useChatStore } from '../../stores/chat.js'
import {
  ChatDotRound,
  User,
  Avatar,
  Loading,
  Microphone,
  DocumentCopy,
  Refresh,
  ArrowLeft,
  More,
  Delete
} from '@element-plus/icons-vue'

const chatStore = useChatStore()

// Props
const props = defineProps({
  autoScrollToBottom: {
    type: Boolean,
    default: true
  }
})

// 事件定义
const emit = defineEmits([
  'generateAudio',
  'switchAudioVersion',
  'deleteAudioVersion',
  'regenerateResponse',
  'rollbackToMessage',
  'deleteMessage'
])

// 响应式数据
const messagesContainer = ref(null)

// 计算属性
const currentConversation = computed(() => chatStore.currentConversation)
const currentMessages = computed(() => chatStore.currentMessages)

// 复制消息
const copyMessage = async (content) => {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
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
    if (props.autoScrollToBottom) {
      nextTick(() => {
        scrollToBottom()
      })
    }
  }
)

// 暴露方法给父组件
defineExpose({
  scrollToBottom
})
</script>

<style scoped>
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

.audio-versions {
  margin-top: 10px;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.versions-header {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #dee2e6;
  font-weight: 500;
}

.versions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.version-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.version-item .el-button {
  min-width: 80px;
  font-size: 12px;
}

.version-item .default-tag {
  background-color: #e1f3d8;
  color: #67c23a;
  border-radius: 3px;
  padding: 1px 4px;
  font-size: 10px;
  font-weight: bold;
  margin-left: 4px;
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

/* 滚动条样式 */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .message-content {
    max-width: 85%;
  }
}
</style>