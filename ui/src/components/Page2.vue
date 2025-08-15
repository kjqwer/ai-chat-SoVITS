<template>
  <div class="chat-page">
    <div class="chat-container">
      <!-- 左侧对话列表 -->
      <div class="conversation-sidebar">
        <div class="sidebar-header">
          <el-button type="primary" @click="createNewConversation" style="width: 100%; margin-bottom: 10px;"
            :icon="Plus">
            新建对话
          </el-button>

          <!-- 导入导出按钮组 -->
          <div class="import-export-actions">
            <el-button size="small" @click="triggerImport" :icon="Upload" style="flex: 1;">
              导入对话
            </el-button>
            <el-button size="small" @click="showExportDialog = true" :icon="Download" style="flex: 1;"
              :disabled="chatStore.conversations.length === 0">
              批量导出
            </el-button>
          </div>

          <!-- 隐藏的文件输入 -->
          <input ref="fileInput" type="file" accept=".json" multiple style="display: none" @change="handleFileImport" />
        </div>

        <div class="persona-selector">
          <el-select v-model="currentPersonaId" placeholder="选择AI人格" style="width: 100%" @change="handlePersonaChange">
            <el-option v-for="persona in chatStore.personas" :key="persona.id" :label="persona.name"
              :value="persona.id">
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
            <div class="control-group">
              <el-switch v-model="speechRecognitionEnabled" active-text="语音识别" inactive-text="" size="small" />
            </div>
            <div class="control-group">
              <el-switch v-model="chatStore.autoGenerateAudio" active-text="自动语音" inactive-text="" size="small"
                @change="chatStore.toggleAutoGenerateAudio" />
            </div>
            <div class="control-group">
              <el-switch v-model="autoPlayAudio" active-text="自动播放" inactive-text="" size="small"
                @change="toggleAutoPlayAudio" />
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
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
                        <div v-for="(version, versionIndex) in message.audioVersions" :key="version.id"
                          class="version-item" :class="{ active: versionIndex === message.currentAudioVersion }">
                          <el-button size="small"
                            :type="versionIndex === message.currentAudioVersion ? 'primary' : 'default'"
                            @click="switchAudioVersion(currentConversation.id, message.id, versionIndex)">
                            版本{{ versionIndex + 1 }}
                            <span v-if="version.isDefault" class="default-tag">(默认)</span>
                          </el-button>
                          <el-button size="small" text type="danger"
                            @click="deleteAudioVersion(currentConversation.id, message.id, versionIndex)"
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
                      <el-button size="small" text @click="generateAudio(currentConversation.id, message.id, true)"
                        :loading="message.audioGenerating">
                        <el-icon>
                          <Refresh />
                        </el-icon>
                        重新生成语音
                      </el-button>
                    </div>
                  </div>
                  <div v-else class="audio-actions">
                    <el-button size="small" text @click="generateAudio(currentConversation.id, message.id)"
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
                        <el-dropdown-item v-if="message.role === 'assistant'" @click="regenerateResponse(index)">
                          <el-icon>
                            <Refresh />
                          </el-icon>
                          重新生成
                        </el-dropdown-item>
                        <el-dropdown-item @click="rollbackToMessage(index)" divided>
                          <el-icon>
                            <ArrowLeft />
                          </el-icon>
                          回溯到此处
                        </el-dropdown-item>
                        <el-dropdown-item @click="deleteMessage(index)">
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

        <!-- 输入区域 -->
        <div class="input-area">
          <div class="input-container">
            <div class="input-with-voice">
              <el-input v-model="inputMessage" type="textarea" :rows="3" placeholder="输入你的消息或点击麦克风按钮录音..."
                @keydown.ctrl.enter="sendMessage" :disabled="chatStore.loading.sendMessage || isRecording" />

              <!-- 语音输入按钮 -->
              <div class="voice-input-button" v-if="speechRecognitionEnabled">
                <el-button :type="isRecording ? 'danger' : 'default'" :icon="isRecording ? VideoPause : Microphone"
                  @click="isRecording ? stopRecording() : startRecording()" :loading="apiStore.loading.asr" circle
                  size="large" class="record-button">
                </el-button>

                <!-- 录音时间显示 -->
                <div v-if="isRecording" class="recording-time">
                  <el-icon class="recording-icon">
                    <Microphone />
                  </el-icon>
                  {{ formatRecordingTime(recordingTime) }}
                </div>
              </div>
            </div>

            <div class="input-actions">
              <div class="input-hint">
                <span>Ctrl + Enter 发送</span>
                <span v-if="speechRecognitionEnabled && !isRecording" class="voice-hint">
                  • 点击麦克风录音
                </span>
                <span v-if="isRecording" class="recording-hint">
                  正在录音中，再次点击停止
                </span>
              </div>
              <el-button type="primary" @click="sendMessage" :loading="chatStore.loading.sendMessage"
                :disabled="!inputMessage.trim() || isRecording">
                <el-icon>
                  <Position />
                </el-icon>
                发送
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量导出对话框 -->
    <el-dialog v-model="showExportDialog" title="批量导出对话" width="500px">
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
          <el-button @click="showExportDialog = false">取消</el-button>
          <el-button type="primary" @click="exportSelectedConversations" :disabled="selectedConversations.length === 0">
            导出选中的对话 ({{ selectedConversations.length }})
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useChatStore } from '../stores/chat.js'
import { useApiStore } from '../stores/api.js'
import {
  Plus,
  More,
  Download,
  Upload,
  Delete,
  ChatDotRound,
  User,
  Avatar,
  Loading,
  Microphone,
  DocumentCopy,
  Refresh,
  ArrowLeft,
  Position,
  VideoPause,
  VideoPlay
} from '@element-plus/icons-vue'

const chatStore = useChatStore()
const apiStore = useApiStore()

// 响应式数据
const inputMessage = ref('')
const messagesContainer = ref(null)
const currentPersonaId = ref('')
const fileInput = ref(null)
const showExportDialog = ref(false)
const selectedConversations = ref([])
const selectAllConversations = ref(false)

// 语音识别相关状态
const isRecording = ref(false)
const mediaRecorder = ref(null)
const audioChunks = ref([])
const recordingTime = ref(0)
const recordingTimer = ref(null)
const speechRecognitionEnabled = ref(true)
const autoPlayAudio = ref(true)
const currentPlayingAudio = ref(null)

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

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim()) return

  try {
    const messageText = inputMessage.value
    await chatStore.sendMessage(messageText)
    inputMessage.value = ''

    // 滚动到底部
    await nextTick()
    scrollToBottom()

    // 如果开启了自动语音生成和自动播放，监听新消息的音频生成
    if (chatStore.autoGenerateAudio && autoPlayAudio.value) {
      const currentConv = chatStore.currentConversation
      if (currentConv && currentConv.messages.length > 0) {
        const lastMessage = currentConv.messages[currentConv.messages.length - 1]

        // 如果是AI消息且有音频生成
        if (lastMessage.role === 'assistant') {
          // 等待音频生成完成后自动播放
          const checkAudioGeneration = () => {
            if (lastMessage.audioVersions?.length > 0 && !lastMessage.audioGenerating) {
              const audioUrl = lastMessage.audioVersions[0]?.url
              if (audioUrl) {
                autoPlayGeneratedAudio(audioUrl)
              }
            } else if (lastMessage.audioGenerating) {
              // 如果还在生成中，继续等待
              setTimeout(checkAudioGeneration, 500)
            }
          }

          // 延迟检查，给音频生成一些时间
          setTimeout(checkAudioGeneration, 1000)
        }
      }
    }
  } catch (error) {
    ElMessage.error(`发送消息失败: ${error.message}`)
  }
}

// 生成音频
const generateAudio = async (conversationId, messageId, isRegenerate = false) => {
  try {
    await chatStore.generateMessageAudio(conversationId, messageId, isRegenerate)
    ElMessage.success('语音生成成功')

    // 如果开启了自动播放，播放生成的音频
    if (autoPlayAudio.value) {
      const message = chatStore.conversations
        .find(conv => conv.id === conversationId)?.messages
        .find(msg => msg.id === messageId)

      if (message?.audioVersions?.length > 0) {
        const currentVersion = message.currentAudioVersion >= 0 ? message.currentAudioVersion : 0
        const audioUrl = message.audioVersions[currentVersion]?.url
        if (audioUrl) {
          autoPlayGeneratedAudio(audioUrl)
        }
      }
    }
  } catch (error) {
    ElMessage.error('语音生成失败')
  }
}

// 切换音频版本
const switchAudioVersion = (conversationId, messageId, versionIndex) => {
  try {
    chatStore.switchAudioVersion(conversationId, messageId, versionIndex)
    ElMessage.success('已切换到语音版本')
  } catch (error) {
    ElMessage.error('切换语音版本失败')
  }
}

// 删除音频版本
const deleteAudioVersion = async (conversationId, messageId, versionIndex) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除语音版本 ${versionIndex + 1} 吗？这将删除该版本的所有音频文件。`,
      '确认删除',
      { type: 'warning' }
    )
    chatStore.deleteAudioVersion(conversationId, messageId, versionIndex)
    ElMessage.success('语音版本已删除')
  } catch {
    // 用户取消
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
    showExportDialog.value = false
    selectedConversations.value = []
    selectAllConversations.value = false
  } catch (error) {
    ElMessage.error('导出失败')
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

// ==================== 语音识别相关方法 ====================

// 开始录音
const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true
      }
    })

    // 选择音频格式
    let mimeType = 'audio/webm;codecs=opus'
    let fileExtension = 'webm'

    if (MediaRecorder.isTypeSupported('audio/wav')) {
      mimeType = 'audio/wav'
      fileExtension = 'wav'
    } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
      mimeType = 'audio/webm;codecs=opus'
      fileExtension = 'webm'
    } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
      mimeType = 'audio/ogg;codecs=opus'
      fileExtension = 'ogg'
    }

    mediaRecorder.value = new MediaRecorder(stream, { mimeType })
    audioChunks.value = []

    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data)
      }
    }

    mediaRecorder.value.onstop = async () => {
      const audioBlob = new Blob(audioChunks.value, { type: mimeType })
      await processRecordedAudio(audioBlob, fileExtension)

      // 停止所有音频轨道
      stream.getTracks().forEach(track => track.stop())
    }

    mediaRecorder.value.start()
    isRecording.value = true
    recordingTime.value = 0

    // 开始计时
    recordingTimer.value = setInterval(() => {
      recordingTime.value++
    }, 1000)

    ElMessage.success('开始录音')
  } catch (error) {
    console.error('录音启动失败:', error)
    ElMessage.error('无法访问麦克风，请检查权限设置')
  }
}

// 停止录音
const stopRecording = () => {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
    isRecording.value = false

    if (recordingTimer.value) {
      clearInterval(recordingTimer.value)
      recordingTimer.value = null
    }

    ElMessage.info('录音已停止，正在处理...')
  }
}

// 处理录制的音频
const processRecordedAudio = async (audioBlob, fileExtension = 'webm') => {
  try {
    // 检查音频文件大小
    if (audioBlob.size === 0) {
      throw new Error('录音文件为空，请重新录音')
    }

    // 转换音频格式（如果需要）
    let finalBlob = audioBlob
    let fileName = `recording.${fileExtension}`

    if (fileExtension === 'webm') {
      try {
        finalBlob = await convertWebMToWAV(audioBlob)
        fileName = 'recording.wav'
      } catch (convertError) {
        console.warn('音频转换失败，使用原始格式:', convertError)
      }
    }

    // 使用API store进行语音识别
    const result = await apiStore.recognizeAudioBlob(finalBlob, fileName, 'normal')

    if (result.success && result.text) {
      // 将识别结果填入输入框
      inputMessage.value = result.text
      ElMessage.success('语音识别完成')
    } else {
      throw new Error(result.detail || '识别失败')
    }
  } catch (error) {
    console.error('语音识别失败:', error)
    ElMessage.error(`语音识别失败: ${error.message}`)
  }
}

// WebM转WAV的辅助函数
const convertWebMToWAV = async (webmBlob) => {
  return new Promise((resolve, reject) => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const fileReader = new FileReader()

    fileReader.onload = async (event) => {
      try {
        const arrayBuffer = event.target.result
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

        // 转换为WAV格式
        const wavBuffer = audioBufferToWav(audioBuffer)
        const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' })
        resolve(wavBlob)
      } catch (error) {
        reject(error)
      }
    }

    fileReader.onerror = reject
    fileReader.readAsArrayBuffer(webmBlob)
  })
}

// 音频Buffer转WAV格式
const audioBufferToWav = (buffer) => {
  const length = buffer.length
  const arrayBuffer = new ArrayBuffer(44 + length * 2)
  const view = new DataView(arrayBuffer)
  const sampleRate = buffer.sampleRate

  // WAV文件头
  const writeString = (offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i))
    }
  }

  writeString(0, 'RIFF')
  view.setUint32(4, 36 + length * 2, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeString(36, 'data')
  view.setUint32(40, length * 2, true)

  // 写入音频数据
  const channelData = buffer.getChannelData(0)
  let offset = 44
  for (let i = 0; i < length; i++) {
    const sample = Math.max(-1, Math.min(1, channelData[i]))
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true)
    offset += 2
  }

  return arrayBuffer
}

// 格式化录音时间
const formatRecordingTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 切换自动播放音频
const toggleAutoPlayAudio = () => {
  autoPlayAudio.value = !autoPlayAudio.value
  ElMessage.info(autoPlayAudio.value ? '已开启自动播放语音' : '已关闭自动播放语音')
}

// 自动播放音频
const autoPlayGeneratedAudio = (audioUrl) => {
  if (!autoPlayAudio.value) return

  try {
    // 停止当前播放的音频
    if (currentPlayingAudio.value) {
      currentPlayingAudio.value.pause()
      currentPlayingAudio.value.currentTime = 0
    }

    // 创建新的Audio对象并播放
    const audio = new Audio(audioUrl)
    currentPlayingAudio.value = audio

    audio.onended = () => {
      currentPlayingAudio.value = null
    }

    audio.onerror = (error) => {
      console.error('音频播放失败:', error)
      currentPlayingAudio.value = null
    }

    audio.play().catch(error => {
      console.error('音频自动播放失败:', error)
      // 浏览器阻止自动播放时的处理
    })
  } catch (error) {
    console.error('音频播放出错:', error)
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

// 清理录音资源
const cleanupRecording = () => {
  if (isRecording.value) {
    stopRecording()
  }
  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
    recordingTimer.value = null
  }
  if (currentPlayingAudio.value) {
    currentPlayingAudio.value.pause()
    currentPlayingAudio.value = null
  }
}

// 组件卸载时清理
onUnmounted(() => {
  cleanupRecording()
  window.removeEventListener('beforeunload', cleanupRecording)
})

// 监听选中对话的变化，自动更新全选状态
watch(
  () => selectedConversations.value.length,
  (newLength) => {
    const totalConversations = chatStore.conversations.length
    selectAllConversations.value = newLength > 0 && newLength === totalConversations
  }
)

// 组件挂载时初始化配置并创建第一个对话（如果没有的话）
onMounted(async () => {
  await chatStore.initializeConfig()

  if (chatStore.conversations.length === 0) {
    chatStore.createConversation('欢迎对话')
  }

  // 初始化ASR功能
  try {
    await apiStore.initializeAsrData()
    console.log('ASR功能初始化完成')
  } catch (error) {
    console.warn('ASR功能初始化失败:', error)
    speechRecognitionEnabled.value = false
  }

  // 监听页面离开，清理资源
  window.addEventListener('beforeunload', cleanupRecording)
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

.chat-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.control-group {
  display: flex;
  align-items: center;
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
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.voice-hint {
  color: #409eff;
}

.recording-hint {
  color: #f56c6c;
  font-weight: 500;
}

/* 语音输入相关样式 */
.input-with-voice {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.voice-input-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.record-button {
  width: 50px !important;
  height: 50px !important;
  font-size: 20px;
  transition: all 0.3s ease;
}

.record-button:hover {
  transform: scale(1.05);
}

.recording-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #f56c6c;
  font-weight: 500;
  white-space: nowrap;
}

.recording-icon {
  color: #f56c6c;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }

  100% {
    opacity: 1;
  }
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