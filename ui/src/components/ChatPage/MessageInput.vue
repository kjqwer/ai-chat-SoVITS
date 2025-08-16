<template>
  <div class="input-area">
    <div class="input-container">
      <div class="input-with-voice">
        <el-input v-model="inputMessage" type="textarea" :rows="3" placeholder="输入你的消息或点击麦克风按钮录音..."
          @keydown.ctrl.enter="handleSendMessage" :disabled="chatStore.loading.sendMessage || isRecording" />

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
        <el-button type="primary" @click="handleSendMessage" :loading="chatStore.loading.sendMessage"
          :disabled="!inputMessage.trim() || isRecording">
          <el-icon>
            <Position />
          </el-icon>
          发送
        </el-button>
      </div>
    </div>
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
  VideoPause
} from '@element-plus/icons-vue'

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
const emit = defineEmits(['sendMessage'])

// 响应式数据
const inputMessage = ref('')
const isRecording = ref(false)
const mediaRecorder = ref(null)
const audioChunks = ref([])
const recordingTime = ref(0)
const recordingTimer = ref(null)

// 发送消息
const handleSendMessage = () => {
  if (!inputMessage.value.trim()) return

  emit('sendMessage', inputMessage.value)
  inputMessage.value = ''
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

// 清理录音资源
const cleanupRecording = () => {
  if (isRecording.value) {
    stopRecording()
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
  inputMessage
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
</style>