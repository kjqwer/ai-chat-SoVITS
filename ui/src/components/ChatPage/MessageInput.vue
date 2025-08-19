<template>
  <div class="input-area">
    <div class="input-container">
      <!-- 文本输入区域 -->
      <div class="text-input-section">
        <el-input v-model="inputMessage" type="textarea" :rows="3" placeholder="输入你的消息或按住右侧麦克风按钮录音..."
          @keydown.ctrl.enter="handleSendMessage" :disabled="chatStore.loading.sendMessage || isRecording"
          class="message-input" />

        <div class="input-actions">
          <div class="input-hint">
            <span>Ctrl + Enter 发送</span>
            <span v-if="isRecording" class="recording-hint">
              正在录音中，松开停止
            </span>
          </div>
          <el-button type="primary" @click="handleSendMessage" :loading="chatStore.loading.sendMessage"
            :disabled="!inputMessage.trim() || isRecording" class="send-button">
            <el-icon>
              <Position />
            </el-icon>
            发送
          </el-button>
        </div>
      </div>

      <!-- 语音输入按钮-->
      <div class="voice-input-section" v-if="speechRecognitionEnabled">
        <div class="voice-buttons-container">
          <!-- 实时语音按钮 -->
          <div class="voice-button-wrapper">
            <el-button type="success" :icon="VideoCamera" @click="toggleRealtimeMode" :loading="apiStore.loading" circle
              size="large" class="realtime-voice-button" :class="{ 'active': isRealtimeActive }" title="实时语音对话">
            </el-button>
            <div class="button-label">实时对话</div>
          </div>

          <!-- 传统录音按钮 -->
          <div class="voice-button-wrapper">
            <el-button :type="isRecording ? 'danger' : 'primary'" :icon="isRecording ? VideoPause : Microphone"
              @mousedown="startRecording" @mouseup="stopRecording" @mouseleave="stopRecording"
              @touchstart="handleTouchStart" @touchend="handleTouchEnd" @touchcancel="handleTouchEnd"
              :loading="apiStore.loading" circle size="large" class="voice-button"
              :class="{ 'recording': isRecording, 'pressing': isPressing }" title="按住录音">
            </el-button>
            <div class="button-label">按住录音</div>
          </div>
        </div>

        <!-- 录音状态指示器 -->
        <div v-if="isRecording" class="recording-indicator">
          <div class="recording-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <div class="recording-time">{{ formatRecordingTime(recordingTime) }}</div>
        </div>

        <!-- 实时语音状态 -->
        <div class="realtime-hint" v-if="isRealtimeActive">
          实时对话中
        </div>
      </div>
    </div>

    <!-- 实时语音对话组件 -->
    <RealTimeVoiceChat v-if="isRealtimeActive" :enabled="speechRecognitionEnabled"
      @messageRecognized="handleRealtimeMessage" @stateChanged="handleRealtimeStateChange"
      @audioPlaybackStarted="handleRealtimeAudioPlaybackStarted"
      @audioPlaybackEnded="handleRealtimeAudioPlaybackEnded" />
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useChatStore } from '../../stores/chat.js'
import { useApiStore } from '../../stores/api.js'
import {
  Microphone,
  Position,
  VideoPause,
  VideoCamera
} from '@element-plus/icons-vue'
import RealTimeVoiceChat from './RealTimeVoiceChat.vue'

const chatStore = useChatStore()
const apiStore = useApiStore()

// Props
const props = defineProps({
  speechRecognitionEnabled: {
    type: Boolean,
    default: true
  }
})

// 事件定义
const emit = defineEmits(['sendMessage', 'audioPlaybackStarted', 'audioPlaybackEnded'])

// 响应式数据
const inputMessage = ref('')
const isRecording = ref(false)
const isPressing = ref(false)
const isRealtimeActive = ref(false)
const mediaRecorder = ref(null)
const audioChunks = ref([])
const recordingTime = ref(0)
const recordingTimer = ref(null)
const touchStartTime = ref(0)

// 发送消息
const handleSendMessage = () => {
  if (!inputMessage.value.trim()) return

  emit('sendMessage', inputMessage.value)
  inputMessage.value = ''
}

// 切换实时语音模式
const toggleRealtimeMode = () => {
  if (isRealtimeActive.value) {
    stopRealtimeMode()
  } else {
    startRealtimeMode()
  }
}

// 启动实时语音模式
const startRealtimeMode = () => {
  isRealtimeActive.value = true
  // 如果正在录音，先停止
  if (isRecording.value) {
    stopRecording()
  }
}

// 停止实时语音模式
const stopRealtimeMode = () => {
  isRealtimeActive.value = false
}

// 处理实时语音识别结果
const handleRealtimeMessage = (data) => {
  if (data.autoSend) {
    // 自动发送模式，直接发送消息给ChatPage
    emit('sendMessage', data.text)
  } else {
    // 手动模式，填入输入框
    inputMessage.value = data.text
  }
}

// 处理实时语音状态变化
const handleRealtimeStateChange = (state) => {
  isRealtimeActive.value = state.active
}

// 处理实时语音音频播放事件
const handleRealtimeAudioPlaybackStarted = () => {
  emit('audioPlaybackStarted')
}

const handleRealtimeAudioPlaybackEnded = () => {
  emit('audioPlaybackEnded')
}

// 触摸开始处理
const handleTouchStart = (event) => {
  event.preventDefault()
  touchStartTime.value = Date.now()
  isPressing.value = true
  startRecording()
}

// 触摸结束处理
const handleTouchEnd = (event) => {
  event.preventDefault()
  isPressing.value = false
  // 防止误触，如果按住时间太短就不录音
  const pressDuration = Date.now() - touchStartTime.value
  if (pressDuration > 100) {
    stopRecording()
  }
}

// 开始录音
const startRecording = async () => {
  if (isRecording.value) return // 防止重复启动

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
    isPressing.value = false

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

// 清理录音资源
const cleanupRecording = () => {
  if (isRecording.value) {
    stopRecording()
  }
  if (isRealtimeActive.value) {
    stopRealtimeMode()
  }
  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
    recordingTimer.value = null
  }
}

// 组件卸载时清理
onUnmounted(() => {
  cleanupRecording()
})

// 暴露方法给父组件
defineExpose({
  cleanupRecording,
  inputMessage,
  startRealtimeMode,
  stopRealtimeMode,
  isRealtimeActive
})
</script>

<style scoped>
/* 输入区域 */
.input-area {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  background-color: #fafafa;
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  /* 改为center，让子元素在容器中垂直居中 */
  gap: 15px;
}

.text-input-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
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



.recording-hint {
  color: #f56c6c;
  font-weight: 500;
}

/* 输入框样式 */
.message-input {
  border-radius: 12px;
  transition: all 0.3s ease;
}

.message-input:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-input:focus-within {
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 发送按钮样式 */
.send-button {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.send-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

/* 语音输入相关样式 */
.voice-input-section {
  flex: 0 0 auto;
  /* 固定宽度 */
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-width: 180px;
  padding: 12px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 16px;
  border: 1px solid #e4e7ed;
}

.voice-buttons-container {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 8px;
}

.voice-button-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
}

.voice-button-wrapper:hover .button-label {
  color: #409eff;
  transform: translateY(-1px);
}

.button-label {
  font-size: 11px;
  color: #909399;
  text-align: center;
  font-weight: 500;
  transition: all 0.3s ease;
}

.voice-button {
  width: 52px !important;
  height: 52px !important;
  font-size: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 50% !important;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.15);
  border: 2px solid transparent;
}

.voice-button:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  border-color: rgba(64, 158, 255, 0.3);
}

.voice-button.recording {
  background-color: #f56c6c !important;
  border-color: #f56c6c !important;
  color: white !important;
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(245, 108, 108, 0.4);
}

.voice-button.pressing {
  background-color: #409eff !important;
  /* 按压状态下的背景色 */
  border-color: #409eff !important;
  color: white !important;
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(64, 158, 255, 0.4);
}

/* 实时语音按钮样式 */
.realtime-voice-button {
  width: 52px !important;
  height: 52px !important;
  font-size: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 50% !important;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.15);
  border: 2px solid transparent;
}

.realtime-voice-button:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  border-color: rgba(103, 194, 58, 0.3);
}

.realtime-voice-button.active {
  background-color: #67c23a !important;
  border-color: #67c23a !important;
  color: white !important;
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(103, 194, 58, 0.4);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 20px rgba(103, 194, 58, 0.4);
  }

  50% {
    box-shadow: 0 0 30px rgba(103, 194, 58, 0.6);
  }

  100% {
    box-shadow: 0 0 20px rgba(103, 194, 58, 0.4);
  }
}

.realtime-hint {
  color: #67c23a;
  font-size: 12px;
  text-align: center;
  margin-top: 8px;
  font-weight: 600;
  background: rgba(103, 194, 58, 0.1);
  padding: 4px 12px;
  border-radius: 12px;
  border: 1px solid rgba(103, 194, 58, 0.2);
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #f56c6c;
  font-weight: 600;
  white-space: nowrap;
  background: rgba(245, 108, 108, 0.1);
  padding: 6px 12px;
  border-radius: 12px;
  border: 1px solid rgba(245, 108, 108, 0.2);
  margin-top: 8px;
}

.recording-dots {
  display: flex;
  gap: 2px;
}

.recording-dots span {
  display: inline-block;
  width: 6px;
  height: 6px;
  background-color: #f56c6c;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

.recording-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.recording-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

.recording-dots span:nth-child(3) {
  animation-delay: 0s;
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
</style>