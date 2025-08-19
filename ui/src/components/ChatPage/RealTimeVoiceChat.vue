<template>
  <div class="realtime-voice-chat">
    <!-- 主控制按钮 -->
    <div class="control-section">
      <el-button :type="isActive ? 'danger' : 'success'" :icon="isActive ? VideoPause : Microphone"
        @click="toggleRealtimeMode" :loading="apiStore.loading" circle size="large" class="realtime-button"
        :class="{ 'active': isActive, 'listening': isListening }">
      </el-button>

      <!-- 状态指示器 -->
      <div class="status-indicator" v-if="isActive">
        <div class="status-text">{{ statusText }}</div>
        <div class="listening-dots" v-if="isListening">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>

      <!-- 设置按钮 -->
      <el-button type="text" :icon="Setting" @click="showSettings = !showSettings" circle size="small"
        class="settings-button" title="设置">
      </el-button>
    </div>

    <!-- 设置面板 -->
    <div class="settings-panel" v-if="showSettings">
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>实时语音设置</span>
            <el-button type="text" @click="showSettings = false">
              <el-icon>
                <Close />
              </el-icon>
            </el-button>
          </div>
        </template>

        <div class="settings-content">
          <!-- 语音检测设置 -->
          <div class="setting-group">
            <h4>语音检测</h4>
            <el-form :model="settings" label-width="120px">
              <el-form-item label="静音检测时间">
                <el-input-number v-model="settings.silenceThreshold" :min="1" :max="10" :step="0.5"
                  controls-position="right" />
                <span class="unit">秒</span>
              </el-form-item>

              <el-form-item label="最小语音长度">
                <el-input-number v-model="settings.minSpeechDuration" :min="0.5" :max="5" :step="0.1"
                  controls-position="right" />
                <span class="unit">秒</span>
              </el-form-item>

              <el-form-item label="最大语音长度">
                <el-input-number v-model="settings.maxSpeechDuration" :min="5" :max="60" :step="1"
                  controls-position="right" />
                <span class="unit">秒</span>
              </el-form-item>
            </el-form>
          </div>

          <!-- 自动发送设置 -->
          <div class="setting-group">
            <h4>自动发送</h4>
            <el-form :model="settings" label-width="120px">
              <el-form-item label="启用自动发送">
                <el-switch v-model="settings.autoSend" />
              </el-form-item>

              <el-form-item label="置信度阈值" v-if="settings.autoSend">
                <el-slider v-model="settings.confidenceThreshold" :min="0" :max="1" :step="0.1"
                  :format-tooltip="(val) => `${(val * 100).toFixed(0)}%`" />
              </el-form-item>

              <el-form-item label="关键词触发" v-if="settings.autoSend">
                <el-input v-model="settings.triggerKeywords" placeholder="输入触发关键词，用逗号分隔" />
              </el-form-item>
            </el-form>
          </div>

          <!-- 高级设置 -->
          <div class="setting-group">
            <h4>高级设置</h4>
            <el-form :model="settings" label-width="120px">
              <el-form-item label="使用VAD">
                <el-switch v-model="settings.useVad" />
              </el-form-item>

              <el-form-item label="调试模式">
                <el-switch v-model="settings.debugMode" />
              </el-form-item>
            </el-form>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 调试信息 -->
    <div class="debug-panel" v-if="settings.debugMode && isActive">
      <el-card class="debug-card">
        <template #header>
          <span>调试信息</span>
        </template>
        <div class="debug-content">
          <div class="debug-item">
            <span>状态:</span>
            <span :class="debugStatusClass">{{ currentState }}</span>
          </div>
          <div class="debug-item">
            <span>录音时长:</span>
            <span>{{ formatTime(currentRecordingTime) }}</span>
          </div>
          <div class="debug-item">
            <span>静音时长:</span>
            <span>{{ formatTime(silenceTime) }}</span>
          </div>
          <div class="debug-item">
            <span>最后识别:</span>
            <span class="last-recognition">{{ lastRecognitionText || '无' }}</span>
          </div>
          <div class="debug-item">
            <span>置信度:</span>
            <span>{{ lastConfidence ? `${(lastConfidence * 100).toFixed(1)}%` : '无' }}</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useApiStore } from '../../stores/api.js'
import { useChatStore } from '../../stores/chat.js'
import {
  Microphone,
  VideoPause,
  Close,
  Setting,
  VideoCamera
} from '@element-plus/icons-vue'

const apiStore = useApiStore()
const chatStore = useChatStore()

// Props
const props = defineProps({
  enabled: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['messageRecognized', 'stateChanged', 'audioPlaybackStarted', 'audioPlaybackEnded'])

// 响应式数据
const isActive = ref(false)
const isListening = ref(false)
const showSettings = ref(false)
const currentState = ref('idle')
const currentRecordingTime = ref(0)
const silenceTime = ref(0)
const lastRecognitionText = ref('')
const lastConfidence = ref(0)
// 新增：智能停顿检测相关
const hasDetectedSpeech = ref(false)  // 是否已检测到语音
const gracePeriodTimer = ref(null)    // 宽限期定时器
// 新增：语音检测相关
const hasValidSpeech = ref(false)     // 是否检测到有效语音
const speechStartTime = ref(0)        // 语音开始时间

// 录音相关
const mediaRecorder = ref(null)
const audioChunks = ref([])
const recordingTimer = ref(null)
const silenceTimer = ref(null)
const vadProcessor = ref(null)
const audioContext = ref(null)
const analyser = ref(null)
const microphone = ref(null)
const dataArray = ref(null)
const vadCheckInterval = ref(null)

// 设置
const settings = ref({
  silenceThreshold: 1.5,        // 静音检测阈值（秒）- 降低阈值，让录音更快停止
  minSpeechDuration: 1.0,       // 最小语音长度（秒）
  maxSpeechDuration: 30.0,      // 最大语音长度（秒）
  autoSend: true,               // 自动发送
  confidenceThreshold: 0.5,     // 置信度阈值
  triggerKeywords: '',          // 触发关键词
  useVad: true,
  debugMode: false,              // 调试模式
  // 新增：智能停顿检测
  smartPauseDetection: true,    // 启用智能停顿检测
  pauseGracePeriod: 0.5        // 停顿宽限期（秒）- 降低宽限期
})

// 计算属性
const statusText = computed(() => {
  switch (currentState.value) {
    case 'listening':
      return '正在监听...'
    case 'recording':
      return '正在录音...'
    case 'processing':
      return '正在识别...'
    case 'waiting':
      return '等待回复...'
    default:
      return '已停止'
  }
})

const debugStatusClass = computed(() => {
  return {
    'status-idle': currentState.value === 'idle',
    'status-listening': currentState.value === 'listening',
    'status-recording': currentState.value === 'recording',
    'status-processing': currentState.value === 'processing',
    'status-waiting': currentState.value === 'waiting'
  }
})

// 方法
const toggleRealtimeMode = async () => {
  if (isActive.value) {
    await stopRealtimeMode()
  } else {
    await startRealtimeMode()
  }
}

const startRealtimeMode = async () => {
  try {
    // 检查ASR是否就绪
    if (!await apiStore.checkAsrReady()) {
      ElMessage.error('ASR模型未就绪，请先加载模型')
      return
    }

    // 获取麦克风权限
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true
      }
    })

    // 初始化录音
    await initializeRecording(stream)

    isActive.value = true
    currentState.value = 'listening'
    isListening.value = true

    // 开始监听
    startListening()

    ElMessage.success('实时语音模式已启动')
    emit('stateChanged', { active: true, state: 'listening' })

  } catch (error) {
    console.error('启动实时语音模式失败:', error)
    ElMessage.error('无法启动实时语音模式: ' + error.message)
  }
}

const stopRealtimeMode = async () => {
  try {
    isActive.value = false
    isListening.value = false
    currentState.value = 'idle'

    // 清理资源
    cleanupRecording()
    clearAllTimers()

    ElMessage.info('实时语音模式已停止')
    emit('stateChanged', { active: false, state: 'idle' })

  } catch (error) {
    console.error('停止实时语音模式失败:', error)
  }
}

const initializeRecording = async (stream) => {
  // 初始化Web Audio API（用于VAD检测）
  if (settings.value.useVad) {
    try {
      audioContext.value = new (window.AudioContext || window.webkitAudioContext)()
      microphone.value = audioContext.value.createMediaStreamSource(stream)
    } catch (error) {
      console.warn('Web Audio API初始化失败，将使用简单VAD:', error)
    }
  }

  // 选择音频格式
  let mimeType = 'audio/webm;codecs=opus'

  if (MediaRecorder.isTypeSupported('audio/wav')) {
    mimeType = 'audio/wav'
  } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
    mimeType = 'audio/webm;codecs=opus'
  } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
    mimeType = 'audio/ogg;codecs=opus'
  }

  mediaRecorder.value = new MediaRecorder(stream, { mimeType })
  audioChunks.value = []

  mediaRecorder.value.ondataavailable = (event) => {
    if (event.data.size > 0) {
      audioChunks.value.push(event.data)
    }
  }

  mediaRecorder.value.onstop = async () => {
    if (audioChunks.value.length > 0) {
      await processAudioChunk()
    }
  }
}

const startListening = () => {
  // 检查录音器状态
  if (!mediaRecorder.value || mediaRecorder.value.state !== 'inactive') {
    if (settings.value.debugMode) {
      console.log('录音器状态不正确，无法开始录音:', mediaRecorder.value?.state)
    }
    return
  }

  // 重置状态
  currentRecordingTime.value = 0
  silenceTime.value = 0
  hasDetectedSpeech.value = false

  // 开始录音
  mediaRecorder.value.start()
  currentState.value = 'recording'
  isListening.value = true

  if (settings.value.debugMode) {
    console.log('开始录音，状态:', mediaRecorder.value.state)
  }

  // 开始计时
  recordingTimer.value = setInterval(() => {
    currentRecordingTime.value++

    // 检查最大录音时长
    if (currentRecordingTime.value >= settings.value.maxSpeechDuration) {
      if (settings.value.debugMode) {
        console.log('达到最大录音时长，停止录音')
      }
      stopCurrentRecording()
    }
  }, 1000)

  // 开始静音检测
  startSilenceDetection()
}

const startSilenceDetection = () => {
  // 重置静音时间和语音检测状态
  silenceTime.value = 0
  hasDetectedSpeech.value = false

  if (settings.value.useVad && audioContext.value) {
    // 使用Web Audio API进行VAD检测
    startVadDetection()
  } else {
    // 使用简单的定时器模拟
    silenceTimer.value = setInterval(() => {
      silenceTime.value++

      if (settings.value.debugMode) {
        console.log('简单VAD检测，静音时间:', silenceTime.value, '已检测到语音:', hasDetectedSpeech.value)
      }

      // 智能停顿检测：如果已经检测到语音，给予宽限期
      let effectiveThreshold = settings.value.silenceThreshold
      if (hasDetectedSpeech.value && settings.value.smartPauseDetection) {
        effectiveThreshold += settings.value.pauseGracePeriod
        if (settings.value.debugMode) {
          console.log('启用宽限期，有效阈值:', effectiveThreshold)
        }
      }

      // 如果静音时间超过阈值，停止录音
      if (silenceTime.value >= settings.value.silenceThreshold) {
        if (settings.value.debugMode) {
          console.log('静音时间超过阈值，停止录音，有效语音:', hasValidSpeech.value)
        }
        stopCurrentRecording()
        // 停止VAD检测
        clearInterval(vadCheckInterval.value)
        vadCheckInterval.value = null
      }
    }, 1000)
  }
}

const startVadDetection = () => {
  // 创建音频分析器
  analyser.value = audioContext.value.createAnalyser()
  analyser.value.fftSize = 256
  analyser.value.smoothingTimeConstant = 0.8

  // 连接麦克风到分析器
  microphone.value.connect(analyser.value)

  // 创建数据数组
  dataArray.value = new Uint8Array(analyser.value.frequencyBinCount)

  // 开始VAD检测
  vadCheckInterval.value = setInterval(() => {
    // 检查录音器状态，如果状态不正确则停止VAD检测
    if (!mediaRecorder.value || mediaRecorder.value.state !== 'recording') {
      if (settings.value.debugMode) {
        console.log('录音器状态不正确，停止VAD检测:', mediaRecorder.value?.state)
      }
      clearInterval(vadCheckInterval.value)
      vadCheckInterval.value = null
      return
    }

    analyser.value.getByteFrequencyData(dataArray.value)

    // 计算音频能量
    const energy = dataArray.value.reduce((sum, value) => sum + value, 0) / dataArray.value.length

    // 检测是否有语音活动（降低阈值，使其更容易检测到语音）
    const isSpeech = energy > 20 // 降低阈值

    if (isSpeech) {
      // 检测到语音，重置静音时间
      silenceTime.value = 0

      // 标记有效语音检测
      if (!hasValidSpeech.value) {
        hasValidSpeech.value = true
        speechStartTime.value = Date.now()
        if (settings.value.debugMode) {
          console.log('检测到有效语音开始，能量:', energy)
        }
      }

      if (settings.value.debugMode) {
        console.log('检测到语音活动，能量:', energy)
      }
    } else {
      // 静音，增加静音时间
      silenceTime.value += 0.1 // 每100ms增加0.1秒

      if (settings.value.debugMode) {
        console.log('静音中，静音时间:', silenceTime.value.toFixed(1), '能量:', energy, '有效语音:', hasValidSpeech.value)
      }

      // 如果静音时间超过阈值，停止录音
      if (silenceTime.value >= settings.value.silenceThreshold) {
        if (settings.value.debugMode) {
          console.log('静音时间超过阈值，停止录音，有效语音:', hasValidSpeech.value)
        }
        stopCurrentRecording()
        // 停止VAD检测
        clearInterval(vadCheckInterval.value)
        vadCheckInterval.value = null
      }
    }
  }, 100) // 每100ms检查一次
}

const stopCurrentRecording = () => {
  if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
    if (settings.value.debugMode) {
      console.log('停止录音，当前状态:', mediaRecorder.value.state)
    }

    mediaRecorder.value.stop()
    currentState.value = 'processing'
    isListening.value = false

    // 停止计时器
    clearRecordingTimer()
    clearSilenceTimer()

    // 停止VAD检测
    if (vadCheckInterval.value) {
      clearInterval(vadCheckInterval.value)
      vadCheckInterval.value = null
    }
  } else {
    if (settings.value.debugMode) {
      console.log('录音器状态不正确，无法停止:', mediaRecorder.value?.state)
    }
    // 即使状态不正确，也要清理状态
    currentState.value = 'processing'
    isListening.value = false
    clearRecordingTimer()
    clearSilenceTimer()

    // 停止VAD检测
    if (vadCheckInterval.value) {
      clearInterval(vadCheckInterval.value)
      vadCheckInterval.value = null
    }
  }
}

const processAudioChunk = async () => {
  try {
    const audioBlob = new Blob(audioChunks.value, { type: mediaRecorder.value.mimeType })

    if (settings.value.debugMode) {
      console.log('处理音频块，大小:', audioBlob.size, '字节，时长:', currentRecordingTime.value, '秒', '有效语音:', hasValidSpeech.value)
    }

    // 检查是否检测到有效语音
    if (!hasValidSpeech.value) {
      if (settings.value.debugMode) {
        console.log('未检测到有效语音，跳过识别')
      }
      resetRecording()
      return
    }

    // 检查音频长度
    if (currentRecordingTime.value < settings.value.minSpeechDuration) {
      if (settings.value.debugMode) {
        console.log('音频太短，重新开始监听')
      }
      // 音频太短，重新开始监听
      resetRecording()
      return
    }

    // 语音识别
    if (settings.value.debugMode) {
      console.log('开始语音识别...')
    }

    const result = await apiStore.quickRecognize(audioBlob, {
      useVad: settings.value.useVad
    })

    if (settings.value.debugMode) {
      console.log('语音识别结果:', result)
    }

    if (result.success && result.text) {
      lastRecognitionText.value = result.text
      lastConfidence.value = result.confidence || 0

      // 标记已检测到有效语音
      hasDetectedSpeech.value = true

      if (settings.value.debugMode) {
        console.log('识别成功:', result.text, '置信度:', lastConfidence.value, '已标记语音检测')
      }

      // 检查是否需要自动发送
      if (shouldAutoSend(result)) {
        if (settings.value.debugMode) {
          console.log('自动发送消息:', result.text)
        }
        await sendRecognizedMessage(result.text)
      } else {
        if (settings.value.debugMode) {
          console.log('手动模式，发送识别结果给父组件')
        }
        // 发送识别结果给父组件
        emit('messageRecognized', {
          text: result.text,
          confidence: lastConfidence.value,
          autoSend: false
        })
      }
    } else {
      console.warn('语音识别失败:', result)
    }

    // 重置录音状态
    resetRecording()

  } catch (error) {
    console.error('处理音频失败:', error)
    resetRecording()
  }
}

const shouldAutoSend = (result) => {
  if (!settings.value.autoSend) return false

  // 检查置信度
  if (result.confidence && result.confidence < settings.value.confidenceThreshold) {
    return false
  }

  // 检查触发关键词
  if (settings.value.triggerKeywords) {
    const keywords = settings.value.triggerKeywords.split(',').map(k => k.trim())
    const hasKeyword = keywords.some(keyword =>
      result.text.toLowerCase().includes(keyword.toLowerCase())
    )
    if (!hasKeyword) return false
  }

  return true
}

const sendRecognizedMessage = async (text) => {
  try {
    if (settings.value.debugMode) {
      console.log('发送识别消息:', text)
    }

    // 检查聊天状态，如果正在等待回复则暂停监听
    if (chatStore.loading.sendMessage) {
      currentState.value = 'waiting'
      isListening.value = false
    }

    // 发送消息给父组件，让ChatPage处理发送和自动播放
    emit('messageRecognized', {
      text: text,
      confidence: lastConfidence.value,
      autoSend: true
    })

    if (settings.value.debugMode) {
      console.log('消息已发送给ChatPage，等待TTS播放...')
    }

  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败: ' + error.message)

    // 即使发送失败，也要重新开始监听
    if (isActive.value) {
      currentState.value = 'listening'
      isListening.value = true
      startListening()
    }
  }
}

const resetRecording = () => {
  audioChunks.value = []
  currentRecordingTime.value = 0
  silenceTime.value = 0
  hasDetectedSpeech.value = false
  hasValidSpeech.value = false
  speechStartTime.value = 0

  // 清理所有定时器
  clearAllTimers()

  if (isActive.value) {
    // 延迟一点时间再开始新的录音，确保之前的录音完全结束
    setTimeout(() => {
      if (isActive.value && mediaRecorder.value) {
        // 检查录音器状态，如果状态不正确，重新初始化
        if (mediaRecorder.value.state !== 'inactive') {
          if (settings.value.debugMode) {
            console.log('录音器状态异常，重新初始化:', mediaRecorder.value.state)
          }
          // 重新获取麦克风权限并初始化
          reinitializeRecording()
        } else {
          currentState.value = 'listening'
          isListening.value = true
          startListening()
        }
      }
    }, 500)
  }
}

// 重新初始化录音
const reinitializeRecording = async () => {
  try {
    // 清理旧的录音器
    cleanupRecording()

    // 重新获取麦克风权限
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true
      }
    })

    // 重新初始化录音
    await initializeRecording(stream)

    // 开始监听
    currentState.value = 'listening'
    isListening.value = true
    startListening()

    if (settings.value.debugMode) {
      console.log('录音器重新初始化成功')
    }
  } catch (error) {
    console.error('重新初始化录音失败:', error)
    ElMessage.error('录音器重新初始化失败')
  }
}

const clearRecordingTimer = () => {
  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
    recordingTimer.value = null
  }
}

const clearSilenceTimer = () => {
  if (silenceTimer.value) {
    clearInterval(silenceTimer.value)
    silenceTimer.value = null
  }
}

const clearAllTimers = () => {
  clearRecordingTimer()
  clearSilenceTimer()

  // 清理VAD检测定时器
  if (vadCheckInterval.value) {
    clearInterval(vadCheckInterval.value)
    vadCheckInterval.value = null
  }
}

const cleanupRecording = () => {
  // 清理所有定时器
  clearAllTimers()

  if (mediaRecorder.value) {
    if (mediaRecorder.value.state === 'recording') {
      mediaRecorder.value.stop()
    }

    // 停止所有音频轨道
    if (mediaRecorder.value.stream) {
      mediaRecorder.value.stream.getTracks().forEach(track => track.stop())
    }

    mediaRecorder.value = null
  }

  // 清理Web Audio API资源
  if (analyser.value) {
    analyser.value.disconnect()
    analyser.value = null
  }

  if (microphone.value) {
    microphone.value.disconnect()
    microphone.value = null
  }

  if (audioContext.value) {
    audioContext.value.close()
    audioContext.value = null
  }
}

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 监听聊天状态变化
watch(() => chatStore.loading.sendMessage, (isLoading) => {
  if (isLoading && isActive.value) {
    currentState.value = 'waiting'
    isListening.value = false
    if (settings.value.debugMode) {
      console.log('检测到消息发送中，暂停监听')
    }
  } else if (!isLoading && isActive.value && currentState.value === 'waiting') {
    // 回复完成，等待TTS播放
    if (settings.value.debugMode) {
      console.log('消息发送完成，等待TTS播放...')
    }

    // 给TTS生成和播放一些时间，然后重新开始监听
    setTimeout(() => {
      if (isActive.value) {
        if (settings.value.debugMode) {
          console.log('TTS播放时间结束，重新开始监听')
        }
        currentState.value = 'listening'
        isListening.value = true
        startListening()
      }
    }, 5000) // 给5秒时间让TTS生成和播放
  }
})

// 组件卸载时清理
onUnmounted(() => {
  stopRealtimeMode()

  // 清理宽限期定时器
  if (gracePeriodTimer.value) {
    clearTimeout(gracePeriodTimer.value)
    gracePeriodTimer.value = null
  }
})

// 暴露方法
defineExpose({
  startRealtimeMode,
  stopRealtimeMode,
  isActive,
  currentState
})
</script>

<style scoped>
.realtime-voice-chat {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
}

.control-section {
  display: flex;
  align-items: center;
  gap: 15px;
}

.realtime-button {
  width: 60px !important;
  height: 60px !important;
  font-size: 24px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 50% !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.realtime-button:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.realtime-button.active {
  background-color: #67c23a !important;
  border-color: #67c23a !important;
  color: white !important;
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(103, 194, 58, 0.4);
}

.realtime-button.listening {
  background-color: #409eff !important;
  border-color: #409eff !important;
  color: white !important;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 20px rgba(64, 158, 255, 0.4);
  }

  50% {
    box-shadow: 0 0 30px rgba(64, 158, 255, 0.6);
  }

  100% {
    box-shadow: 0 0 20px rgba(64, 158, 255, 0.4);
  }
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
}

.settings-button {
  color: #909399;
  transition: all 0.3s ease;
}

.settings-button:hover {
  color: #409eff;
  transform: scale(1.1);
}

.status-text {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.listening-dots {
  display: flex;
  gap: 3px;
}

.listening-dots span {
  display: inline-block;
  width: 8px;
  height: 8px;
  background-color: #409eff;
  border-radius: 50%;
  animation: pulse-dots 1.5s infinite;
}

.listening-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.listening-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

.listening-dots span:nth-child(3) {
  animation-delay: 0s;
}

@keyframes pulse-dots {

  0%,
  80%,
  100% {
    opacity: 0.3;
    transform: scale(0.8);
  }

  40% {
    opacity: 1;
    transform: scale(1);
  }
}

.settings-panel {
  margin-top: 10px;
}

.settings-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.setting-group h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.unit {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}

.debug-panel {
  margin-top: 10px;
}

.debug-card {
  border-radius: 8px;
  background-color: #fafafa;
}

.debug-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.debug-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 12px;
}

.debug-item span:first-child {
  color: #606266;
  font-weight: 500;
}

.debug-item span:last-child {
  color: #303133;
  font-family: monospace;
}

.status-idle {
  color: #909399;
}

.status-listening {
  color: #409eff;
}

.status-recording {
  color: #67c23a;
}

.status-processing {
  color: #e6a23c;
}

.status-waiting {
  color: #f56c6c;
}

.last-recognition {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>