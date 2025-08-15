<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Microphone, 
  Upload, 
  Download, 
  Setting, 
  RefreshRight, 
  Delete,
  CircleCheck,
  CircleClose,
  Document,
  FolderOpened,
  VideoPlay,
  VideoPause,
  Edit,
  Search,
  Link,
  Warning
} from '@element-plus/icons-vue'
import VadConfigDialog from './VadConfigDialog.vue'

// 响应式数据
const loading = ref(false)
const modelStatus = ref({})
const asrConfig = ref({})
const modelInfo = ref({})
const recognitionResult = ref('')
const audioFile = ref(null)
const testingAudio = ref(false)

// VAD 相关状态
const vadEnabled = ref(false)
const vadStatus = ref({})
const vadSegments = ref([])
const vadLoading = ref(false)
const recognitionMode = ref('normal') // 'normal', 'vad'
const vadResult = ref('')
const splitFiles = ref([])
const showVadConfig = ref(false)

// 模型状态计算属性
const modelLoaded = computed(() => modelInfo.value.is_loaded || false)
const funasrAvailable = computed(() => modelInfo.value.funasr_available || false)
const vadAvailable = computed(() => modelInfo.value.vad_available || false)
const vadModelEnabled = computed(() => modelInfo.value.vad_enabled || false)

// API基础URL - 根据环境自动判断
const getAPIBase = () => {
  // 如果是开发环境且端口不是8000，使用完整URL
  if (import.meta.env.DEV && window.location.port !== '8000') {
    return 'http://localhost:8000/asr'
  }
  // 否则使用相对路径
  return '/asr'
}

const API_BASE = getAPIBase()

// 录音相关状态
const isRecording = ref(false)
const mediaRecorder = ref(null)
const audioChunks = ref([])
const recordingTime = ref(0)
const recordingTimer = ref(null)

// 获取模型状态
const getModelStatus = async () => {
  try {
    loading.value = true
    const response = await fetch(`${API_BASE}/models/status`)
    if (response.ok) {
      const text = await response.text()
      try {
        modelStatus.value = JSON.parse(text)
      } catch (e) {
        console.error('JSON解析错误:', text)
        throw new Error('服务器返回了无效的JSON数据')
      }
    } else {
      throw new Error(`获取模型状态失败: ${response.status}`)
    }
  } catch (error) {
    console.error('获取模型状态错误:', error)
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

// 获取模型信息
const getModelInfo = async () => {
  try {
    const response = await fetch(`${API_BASE}/model/info`)
    if (response.ok) {
      const text = await response.text()
      try {
        modelInfo.value = JSON.parse(text)
      } catch (e) {
        console.error('JSON解析错误:', text)
        throw new Error('服务器返回了无效的JSON数据')
      }
    } else {
      throw new Error(`获取模型信息失败: ${response.status}`)
    }
  } catch (error) {
    console.error('获取模型信息错误:', error)
    ElMessage.error(error.message)
  }
}

// 获取ASR配置
const getAsrConfig = async () => {
  try {
    const response = await fetch(`${API_BASE}/models/config`)
    if (response.ok) {
      asrConfig.value = await response.json()
      vadEnabled.value = asrConfig.value.vad?.enabled || false
    } else {
      throw new Error('获取ASR配置失败')
    }
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 获取VAD状态
const getVadStatus = async () => {
  try {
    const response = await fetch(`${API_BASE}/vad/health`)
    if (response.ok) {
      vadStatus.value = await response.json()
    } else {
      throw new Error('获取VAD状态失败')
    }
  } catch (error) {
    console.error('获取VAD状态错误:', error)
    vadStatus.value = { status: 'error', error: error.message }
  }
}

// 加载模型
const loadModel = async () => {
  try {
    loading.value = true
    ElMessage.info('正在加载ASR模型，请稍候...')

    const response = await fetch(`${API_BASE}/model/load`, {
      method: 'POST'
    })

    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        ElMessage.success('模型加载成功')
        await getModelInfo()
      } else {
        throw new Error(result.message || '模型加载失败')
      }
    } else {
      throw new Error('模型加载请求失败')
    }
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

// 卸载模型
const unloadModel = async () => {
  try {
    loading.value = true
    const response = await fetch(`${API_BASE}/model/unload`, {
      method: 'POST'
    })

    if (response.ok) {
      ElMessage.success('模型已卸载')
      await getModelInfo()
    } else {
      throw new Error('模型卸载失败')
    }
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

// 迁移模型
const migrateModels = async (copyMode = true) => {
  try {
    const action = copyMode ? '复制' : '移动'
    await ElMessageBox.confirm(
      `确定要${action}模型到本地目录吗？这可能需要一些时间。`,
      `${action}模型`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      }
    )

    loading.value = true
    ElMessage.info(`正在${action}模型，请稍候...`)

    const response = await fetch(`${API_BASE}/models/migrate?copy_mode=${copyMode}`, {
      method: 'POST'
    })

    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        ElMessage.success(result.message)
        await Promise.all([getModelStatus(), getAsrConfig()])
      } else {
        throw new Error(result.message || `模型${action}失败`)
      }
    } else {
      throw new Error(`模型${action}请求失败`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}

// 清理缓存
const cleanCache = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清理缓存中的模型吗？请确保本地模型已存在。',
      '清理缓存',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    loading.value = true
    const response = await fetch(`${API_BASE}/models/clean_cache`, {
      method: 'POST'
    })

    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        ElMessage.success(result.message)
        await getModelStatus()
      } else {
        throw new Error(result.message || '缓存清理失败')
      }
    } else {
      throw new Error('缓存清理请求失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}

// 文件上传处理
const handleFileUpload = async (file) => {
  try {
    testingAudio.value = true
    recognitionResult.value = ''
    vadResult.value = ''
    vadSegments.value = []

    console.log(`上传文件: ${file.name}, 大小: ${file.size} bytes, 类型: ${file.type}`)

    // 检查文件对象
    const actualFile = file.raw || file
    if (!actualFile || !actualFile.name) {
      throw new Error('无效的文件对象')
    }

    console.log(`实际文件对象:`, actualFile)

    const formData = new FormData()
    
    // 根据模式选择 API 端点和参数
    let endpoint = `${API_BASE}/recognize/file`
    let message = '正在识别音频，请稍候...'

    console.log('当前识别模式:', recognitionMode.value)
    console.log('VAD模型启用状态:', vadModelEnabled.value)

    if (recognitionMode.value === 'vad' && vadModelEnabled.value) {
      endpoint = `${API_BASE}/recognize/vad`
      message = '正在使用VAD分段识别音频，请稍候...'
      formData.append('file', actualFile, actualFile.name)  // VAD API 使用 'file'
      formData.append('return_segments', 'true')
      console.log('使用VAD端点:', endpoint)
    } else {
      formData.append('audio_file', actualFile, actualFile.name)  // 常规API 使用 'audio_file'
      console.log('使用常规端点:', endpoint)
    }

    ElMessage.info(message)

    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData
    })

    if (response.ok) {
      const text = await response.text()
      try {
        const result = JSON.parse(text)
        console.log('识别结果:', result) // 添加调试信息
        
        if (result.success) {
          recognitionResult.value = result.text

          // 如果是VAD模式，显示额外信息
          if (recognitionMode.value === 'vad') {
            console.log('VAD模式结果:', {
              vad_segments: result.vad_segments,
              recognized_segments: result.recognized_segments,
              processing_method: result.processing_method,
              detailed_results: result.detailed_results
            })
            
            // 检查是否有VAD相关数据
            if (result.vad_segments !== undefined) {
              vadResult.value = `VAD分段识别完成\n` +
                `检测到 ${result.vad_segments || 0} 个语音片段\n` +
                `成功识别 ${result.recognized_segments || 0} 个片段\n` +
                `处理方法: ${result.processing_method || 'unknown'}\n\n` +
                `识别结果: ${result.text}`

              if (result.detailed_results && Array.isArray(result.detailed_results)) {
                vadSegments.value = result.detailed_results
                console.log('VAD分段详情:', result.detailed_results)
              }
            } else {
              vadResult.value = `识别结果: ${result.text}\n\n注意: 未检测到VAD分段信息，可能使用了常规识别模式`
            }
          }

          ElMessage.success('音频识别完成')
        } else {
          recognitionResult.value = `识别失败: ${result.error}`
          ElMessage.error(result.error)
        }
      } catch (e) {
        console.error('JSON解析错误:', text)
        recognitionResult.value = '识别结果解析失败'
        ElMessage.error('识别结果解析失败')
      }
    } else {
      const errorText = await response.text()
      console.error('文件上传识别失败:', response.status, errorText)
      throw new Error(`音频识别请求失败: ${response.status}`)
    }
  } catch (error) {
    console.error('文件上传错误:', error)
    recognitionResult.value = `识别失败: ${error.message}`
    ElMessage.error(error.message)
  } finally {
    testingAudio.value = false
  }

  return false // 阻止自动上传
}

// VAD 检测语音片段
const detectVadSegments = async (file) => {
  try {
    vadLoading.value = true
    vadSegments.value = []

    const actualFile = file.raw || file
    if (!actualFile || !actualFile.name) {
      throw new Error('无效的文件对象')
    }

    const formData = new FormData()
    formData.append('file', actualFile, actualFile.name)

    ElMessage.info('正在检测语音片段，请稍候...')

    const response = await fetch(`${API_BASE}/vad/detect`, {
      method: 'POST',
      body: formData
    })

    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        vadSegments.value = result.segments || []
        const totalDuration = result.total_speech_duration || 0
        ElMessage.success(`检测完成，发现 ${result.total_segments} 个语音片段，总时长 ${totalDuration.toFixed(2)}s`)
      } else {
        throw new Error(result.error || 'VAD检测失败')
      }
    } else {
      throw new Error('VAD检测请求失败')
    }
  } catch (error) {
    console.error('VAD检测错误:', error)
    ElMessage.error(error.message)
  } finally {
    vadLoading.value = false
  }

  return false // 阻止自动上传
}

// VAD 音频分割
const splitAudioByVad = async (file) => {
  try {
    vadLoading.value = true
    splitFiles.value = []

    const actualFile = file.raw || file
    if (!actualFile || !actualFile.name) {
      throw new Error('无效的文件对象')
    }

    const formData = new FormData()
    formData.append('file', actualFile, actualFile.name)
    formData.append('output_format', 'wav')

    ElMessage.info('正在分割音频，请稍候...')

    const response = await fetch(`${API_BASE}/vad/split`, {
      method: 'POST',
      body: formData
    })

    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        splitFiles.value = result.files || []
        ElMessage.success(`音频分割完成，生成 ${result.total_segments} 个片段`)
      } else {
        throw new Error(result.error || '音频分割失败')
      }
    } else {
      throw new Error('音频分割请求失败')
    }
  } catch (error) {
    console.error('VAD分割错误:', error)
    ElMessage.error(error.message)
  } finally {
    vadLoading.value = false
  }

  return false // 阻止自动上传
}

// 切换识别模式
const switchRecognitionMode = (mode) => {
  console.log('切换识别模式到:', mode)
  recognitionMode.value = mode
  recognitionResult.value = ''
  vadResult.value = ''
  vadSegments.value = []
}

// 处理VAD配置更新
const handleVadConfigUpdate = async (newConfig) => {
  try {
    // 这里应该调用API更新配置
    // 模拟API调用
    console.log('更新VAD配置:', newConfig)

    // 更新本地配置
    if (asrConfig.value.vad) {
      Object.assign(asrConfig.value.vad, newConfig)
    } else {
      asrConfig.value.vad = newConfig
    }

    vadEnabled.value = newConfig.enabled

    // 刷新状态
    await Promise.all([getModelInfo(), getVadStatus()])

    ElMessage.success('VAD配置已更新')
  } catch (error) {
    ElMessage.error('配置更新失败: ' + error.message)
  }
}

// 刷新所有数据
const refreshAll = async () => {
  await Promise.all([
    getModelStatus(),
    getModelInfo(),
    getAsrConfig(),
    getVadStatus()
  ])
}

// 格式化文件大小
const formatSize = (sizeStr) => {
  return sizeStr || '0 B'
}

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

    // 尝试支持的音频格式，选择后端支持的格式
    let mimeType = 'audio/webm;codecs=opus'
    let fileExtension = 'webm'

    // 后端支持的格式: .m4a, .wav, .aac, .mp3, .ogg, .flac
    if (MediaRecorder.isTypeSupported('audio/wav')) {
      mimeType = 'audio/wav'
      fileExtension = 'wav'
    } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
      mimeType = 'audio/webm;codecs=opus'
      fileExtension = 'webm'
    } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
      mimeType = 'audio/ogg;codecs=opus'
      fileExtension = 'ogg'
    } else if (MediaRecorder.isTypeSupported('audio/mp3')) {
      mimeType = 'audio/mp3'
      fileExtension = 'mp3'
    }

    // 避免使用MP4格式，因为后端不支持.mp4扩展名

    console.log(`使用音频格式: ${mimeType}`)

    mediaRecorder.value = new MediaRecorder(stream, {
      mimeType: mimeType
    })

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
    testingAudio.value = true
    recognitionResult.value = ''
    vadResult.value = ''
    vadSegments.value = []

    console.log(`处理录音文件: ${audioBlob.size} bytes, 格式: ${fileExtension}`)

    // 检查音频文件大小
    if (audioBlob.size === 0) {
      throw new Error('录音文件为空，请重新录音')
    }

    // 如果是WebM格式，尝试转换为WAV格式
    let finalBlob = audioBlob
    let fileName = `recording.${fileExtension}`

    if (fileExtension === 'webm') {
      try {
        // 尝试使用Web Audio API转换
        finalBlob = await convertWebMToWAV(audioBlob)
        fileName = 'recording.wav'
        console.log('成功转换WebM为WAV')
      } catch (convertError) {
        console.warn('音频转换失败，使用原始格式:', convertError)
        // 如果转换失败，仍然使用原始格式
      }
    }

    const formData = new FormData()
    
    // 根据模式选择 API 端点和参数 (录音也支持VAD)
    let endpoint = `${API_BASE}/recognize/file`
    let message = '正在识别录音，请稍候...'

    console.log('录音识别 - 当前模式:', recognitionMode.value)
    console.log('录音识别 - VAD启用状态:', vadModelEnabled.value)

    if (recognitionMode.value === 'vad' && vadModelEnabled.value) {
      endpoint = `${API_BASE}/recognize/vad`
      message = '正在使用VAD分段识别录音，请稍候...'
      formData.append('file', finalBlob, fileName)  // VAD API 使用 'file'
      formData.append('return_segments', 'true')
      console.log('录音识别使用VAD端点:', endpoint)
    } else {
      formData.append('audio_file', finalBlob, fileName)  // 常规API 使用 'audio_file'
      console.log('录音识别使用常规端点:', endpoint)
    }

    ElMessage.info(message)

    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData
    })

    if (response.ok) {
      const text = await response.text()
      try {
        const result = JSON.parse(text)
        console.log('录音识别结果:', result) // 添加调试信息
        
        if (result.success) {
          recognitionResult.value = result.text

          // 如果是VAD模式，显示额外信息 (录音也支持VAD)
          if (recognitionMode.value === 'vad') {
            console.log('录音VAD模式结果:', {
              vad_segments: result.vad_segments,
              recognized_segments: result.recognized_segments,
              processing_method: result.processing_method,
              detailed_results: result.detailed_results
            })
            
            // 检查是否有VAD相关数据
            if (result.vad_segments !== undefined) {
              vadResult.value = `VAD分段识别完成\n` +
                `检测到 ${result.vad_segments || 0} 个语音片段\n` +
                `成功识别 ${result.recognized_segments || 0} 个片段\n` +
                `处理方法: ${result.processing_method || 'unknown'}\n\n` +
                `识别结果: ${result.text}`

              if (result.detailed_results && Array.isArray(result.detailed_results)) {
                vadSegments.value = result.detailed_results
                console.log('录音VAD分段详情:', result.detailed_results)
              }
            } else {
              vadResult.value = `识别结果: ${result.text}\n\n注意: 未检测到VAD分段信息，可能使用了常规识别模式`
            }
          }

          ElMessage.success('录音识别完成')
        } else {
          recognitionResult.value = `识别失败: ${result.error}`
          ElMessage.error(result.error)
        }
      } catch (e) {
        console.error('JSON解析错误:', text)
        recognitionResult.value = '识别结果解析失败'
        ElMessage.error('识别结果解析失败')
      }
    } else {
      const errorText = await response.text()
      console.error('服务器响应:', response.status, errorText)
      throw new Error(`音频识别请求失败: ${response.status}`)
    }
  } catch (error) {
    console.error('录音识别错误:', error)
    recognitionResult.value = `识别失败: ${error.message}`
    ElMessage.error(error.message)
  } finally {
    testingAudio.value = false
  }
}

// 格式化录音时间
const formatRecordingTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// WebM转WAV函数
const convertWebMToWAV = async (webmBlob) => {
  return new Promise((resolve, reject) => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const fileReader = new FileReader()

    fileReader.onload = async () => {
      try {
        const arrayBuffer = fileReader.result
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

        // 转换为WAV格式
        const wavBuffer = audioBufferToWav(audioBuffer)
        const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' })

        resolve(wavBlob)
      } catch (error) {
        reject(error)
      }
    }

    fileReader.onerror = () => reject(new Error('文件读取失败'))
    fileReader.readAsArrayBuffer(webmBlob)
  })
}

// 将AudioBuffer转换为WAV格式
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

// 组件挂载时初始化
onMounted(async () => {
  await refreshAll()
  
  // 调试VAD状态
  console.log('组件加载完成时的状态:')
  console.log('vadAvailable:', vadAvailable.value)
  console.log('vadModelEnabled:', vadModelEnabled.value)
  console.log('modelInfo:', modelInfo.value)
  console.log('asrConfig:', asrConfig.value)
})
</script>

<template>
  <div class="asr-page">
    <el-container>
      <el-header style="padding: 20px;">
        <div style="display: flex; align-items: center; justify-content: between;">
          <div>
            <h2 style="margin: 0; color: #303133;">
              <el-icon style="margin-right: 8px;">
                <Microphone />
              </el-icon>
              ASR 语音识别管理
            </h2>
            <p style="margin: 5px 0 0 0; color: #909399; font-size: 14px;">
              管理FunASR模型，测试语音识别功能，支持Silero VAD语音活动检测
            </p>
          </div>
          <el-button type="primary" :icon="RefreshRight" @click="refreshAll" :loading="loading">
            刷新状态
          </el-button>
        </div>
      </el-header>

      <el-main style="padding: 0 20px 20px;">
        <el-row :gutter="20">
          <!-- 左侧：模型状态和管理 -->
          <el-col :span="12">
            <!-- 模型状态卡片 -->
            <el-card shadow="hover" style="margin-bottom: 20px;">
              <template #header>
                <div style="display: flex; align-items: center;">
                  <el-icon style="margin-right: 8px;">
                    <Setting />
                  </el-icon>
                  <span>模型状态</span>
                </div>
              </template>

              <!-- 基本信息 -->
              <el-row style="margin-bottom: 20px;">
                <el-col :span="8">
                  <el-statistic title="FunASR状态">
                    <template #title>
                      <div style="display: inline-flex; align-items: center;">
                        FunASR状态
                      </div>
                    </template>
                    <template #value>
                      <span :style="{ color: funasrAvailable ? '#67C23A' : '#F56C6C' }">
                        {{ funasrAvailable ? '可用' : '不可用' }}
                      </span>
                    </template>
                  </el-statistic>
                </el-col>
                <el-col :span="8">
                  <el-statistic title="模型状态">
                    <template #value>
                      <span :style="{ color: modelLoaded ? '#67C23A' : '#E6A23C' }">
                        {{ modelLoaded ? '已加载' : '未加载' }}
                      </span>
                    </template>
                  </el-statistic>
                </el-col>
                <el-col :span="8">
                  <el-statistic title="VAD状态">
                    <template #title>
                      <div style="display: inline-flex; align-items: center;">
                        <el-icon style="margin-right: 4px;">
                          <Search />
                        </el-icon>
                        VAD状态
                      </div>
                    </template>
                    <template #value>
                      <span :style="{ color: vadModelEnabled ? '#67C23A' : '#909399' }">
                        {{ vadModelEnabled ? '已启用' : '未启用' }}
                      </span>
                    </template>
                  </el-statistic>
                </el-col>
              </el-row>

              <!-- 模型操作按钮 -->
              <div style="text-align: center; margin-bottom: 20px;">
                <el-button type="success" :icon="Download" @click="loadModel" :loading="loading"
                  :disabled="!funasrAvailable || modelLoaded">
                  加载模型
                </el-button>
                <el-button type="warning" :icon="Delete" @click="unloadModel" :loading="loading"
                  :disabled="!modelLoaded">
                  卸载模型
                </el-button>
              </div>

              <!-- 模型详细信息 -->
              <el-descriptions title="模型信息" :column="1" border size="small">
                <el-descriptions-item label="模型名称">
                  {{ modelInfo.model_name || 'N/A' }}
                </el-descriptions-item>
                <el-descriptions-item label="加载状态">
                  <el-tag :type="modelLoaded ? 'success' : 'info'" size="small">
                    {{ modelLoaded ? '已加载' : '未加载' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="FunASR可用性">
                  <el-tag :type="funasrAvailable ? 'success' : 'danger'" size="small">
                    {{ funasrAvailable ? '可用' : '不可用' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="VAD引擎">
                  <el-tag :type="vadAvailable ? 'success' : 'info'" size="small">
                    {{ vadAvailable ? 'Silero VAD 可用' : 'VAD 不可用' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="VAD启用状态" v-if="vadAvailable">
                  <el-tag :type="vadModelEnabled ? 'success' : 'warning'" size="small">
                    {{ vadModelEnabled ? '已启用' : '未启用' }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <!-- 模型管理卡片 -->
            <el-card shadow="hover">
              <template #header>
                <div style="display: flex; align-items: center;">
                  <el-icon style="margin-right: 8px;">
                    <FolderOpened />
                  </el-icon>
                  <span>模型管理</span>
                </div>
              </template>

              <!-- 模型文件状态 -->
              <div style="margin-bottom: 20px;" v-if="Object.keys(modelStatus).length > 0">
                <h4 style="margin-bottom: 15px;">模型文件状态</h4>
                <div v-for="(status, modelName) in modelStatus" :key="modelName" style="margin-bottom: 15px;">
                  <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <el-tag size="small" style="margin-right: 10px;">{{ status.type.toUpperCase() }}</el-tag>
                    <span style="font-size: 12px; color: #606266;">{{ modelName }}</span>
                  </div>
                  <el-row :gutter="10">
                    <el-col :span="12">
                      <div style="display: flex; align-items: center;">
                        <el-icon :color="status.cache_exists ? '#67C23A' : '#C0C4CC'" style="margin-right: 5px;">
                          <CircleCheck v-if="status.cache_exists" />
                          <CircleClose v-else />
                        </el-icon>
                        <span style="font-size: 12px;">缓存: {{ formatSize(status.cache_size) }}</span>
                      </div>
                    </el-col>
                    <el-col :span="12">
                      <div style="display: flex; align-items: center;">
                        <el-icon :color="status.local_exists ? '#67C23A' : '#C0C4CC'" style="margin-right: 5px;">
                          <CircleCheck v-if="status.local_exists" />
                          <CircleClose v-else />
                        </el-icon>
                        <span style="font-size: 12px;">本地: {{ formatSize(status.local_size) }}</span>
                      </div>
                    </el-col>
                  </el-row>
                </div>
              </div>

              <!-- 管理操作按钮 -->
              <div style="text-align: center;">
                <el-button type="primary" :icon="Download" @click="migrateModels(true)" :loading="loading"
                  style="margin-bottom: 10px;">
                  复制模型到本地
                </el-button>
                <br>
                <el-button type="warning" :icon="Upload" @click="migrateModels(false)" :loading="loading" size="small">
                  移动到本地
                </el-button>
                <el-button type="danger" :icon="Delete" @click="cleanCache" :loading="loading" size="small">
                  清理缓存
                </el-button>
              </div>
            </el-card>
          </el-col>

          <!-- 右侧：语音识别测试 -->
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <div style="display: flex; align-items: center;">
                    <el-icon style="margin-right: 8px;">
                      <Document />
                    </el-icon>
                    <span>语音识别测试</span>
                  </div>
                  <!-- 识别模式选择 -->
                  <el-radio-group v-model="recognitionMode" size="small" @change="switchRecognitionMode"
                    :disabled="!vadModelEnabled && recognitionMode !== 'normal'">
                    <el-radio-button label="normal">常规识别</el-radio-button>
                    <el-radio-button label="vad" :disabled="!vadModelEnabled">
                      <el-icon style="margin-right: 4px;">
                        <Search />
                      </el-icon>
                      VAD分段
                    </el-radio-button>
                  </el-radio-group>
                </div>
              </template>

              <!-- 录音控制区域 -->
              <div style="margin-bottom: 20px;">
                <el-card shadow="never" style="background-color: #f8f9fa;">
                  <div style="text-align: center;">
                    <h4 style="margin-bottom: 15px;">现场录音</h4>

                    <!-- 录音按钮 -->
                    <div style="margin-bottom: 15px;">
                      <el-button v-if="!isRecording" type="danger" size="large" round :icon="Microphone"
                        @click="startRecording" :disabled="testingAudio">
                        开始录音
                      </el-button>

                      <el-button v-else type="warning" size="large" round :icon="VideoPause" @click="stopRecording">
                        停止录音
                      </el-button>
                    </div>

                    <!-- 录音状态 -->
                    <div v-if="isRecording" style="color: #F56C6C; font-size: 16px; font-weight: bold;">
                      <el-icon style="margin-right: 5px;" class="recording-pulse">
                        <Microphone />
                      </el-icon>
                      录音中... {{ formatRecordingTime(recordingTime) }}
                    </div>
                  </div>
                </el-card>
              </div>

              <!-- 文件上传区域 -->
              <div style="margin-bottom: 20px;">
                <el-upload :before-upload="handleFileUpload" :show-file-list="false"
                  accept=".wav,.mp3,.m4a,.mp4,.flac,.aac,.ogg,.webm" drag style="width: 100%;" :disabled="isRecording">
                  <el-icon style="font-size: 67px; color: #C0C4CC;">
                    <Upload />
                  </el-icon>
                  <div style="color: #606266; margin-top: 16px;">
                    将音频文件拖到此处，或<em>点击上传</em>
                  </div>
                  <div style="color: #909399; font-size: 12px; margin-top: 8px;">
                    支持 WAV, MP3, M4A, MP4, FLAC, AAC, OGG, WebM 格式
                  </div>
                </el-upload>
              </div>

              <!-- 识别结果 -->
              <div>
                <h4 style="margin-bottom: 10px; display: flex; align-items: center;">
                  <span>{{ recognitionMode === 'vad' ? 'VAD分段识别结果' : '识别结果' }}</span>
                  <el-icon v-if="testingAudio" style="margin-left: 10px;">
                    <RefreshRight class="rotating" />
                  </el-icon>
                </h4>
                <el-input :model-value="recognitionMode === 'vad' ? vadResult : recognitionResult" type="textarea"
                  :rows="recognitionMode === 'vad' ? 6 : 8"
                  :placeholder="recognitionMode === 'vad' ? 'VAD分段识别结果将显示在这里...' : '上传音频文件后，识别结果将显示在这里...'" readonly
                  style="font-family: monospace;" />

                <!-- VAD分段详情 -->
                <div v-if="recognitionMode === 'vad' && vadSegments.length > 0" style="margin-top: 15px;">
                  <h5 style="margin-bottom: 10px;">
                    <el-icon style="margin-right: 4px;">
                      <Edit />
                    </el-icon>
                    语音片段详情 ({{ vadSegments.length }} 个片段)
                  </h5>
                  <el-table :data="vadSegments" size="small" style="width: 100%;" max-height="200">
                    <el-table-column prop="segment_id" label="片段" width="60" align="center" />
                    <el-table-column label="时间范围" width="120" align="center">
                      <template #default="scope">
                        {{ scope.row.start.toFixed(2) }}s - {{ scope.row.end.toFixed(2) }}s
                      </template>
                    </el-table-column>
                    <el-table-column label="时长" width="80" align="center">
                      <template #default="scope">
                        {{ scope.row.duration.toFixed(2) }}s
                      </template>
                    </el-table-column>
                    <el-table-column prop="text" label="识别文本" show-overflow-tooltip />
                    <el-table-column label="置信度" width="80" align="center">
                      <template #default="scope">
                        {{ (scope.row.confidence * 100).toFixed(1) }}%
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>

              <!-- 支持的格式说明 -->
              <el-alert :title="recognitionMode === 'vad' ? 'VAD分段识别说明' : '支持的音频格式'" type="info" show-icon
                :closable="false" style="margin-top: 15px;">
                <template #default>
                  <div style="font-size: 12px;">
                    <div v-if="recognitionMode === 'vad'">
                      <strong>VAD分段识别：</strong>先使用Silero VAD检测语音片段，然后对每个片段进行语音识别，最后合并结果。
                      <br>
                      <strong>优势：</strong>提高长音频识别准确性，自动过滤静音片段，支持详细的时间戳信息。
                      <br>
                      <strong>适用场景：</strong>会议录音、播客、有较多停顿的语音内容。
                    </div>
                    <div v-else>
                      <strong>支持格式：</strong>WAV (.wav), MP3 (.mp3), M4A (.m4a), MP4 (.mp4), FLAC (.flac), AAC (.aac),
                      OGG (.ogg), WebM (.webm)
                    </div>
                  </div>
                </template>
              </el-alert>
            </el-card>
          </el-col>
        </el-row>

        <!-- VAD 独立功能区域 -->
        <el-row v-if="vadAvailable" style="margin-top: 20px;">
          <el-col :span="24">
            <el-card shadow="hover">
              <template #header>
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <div style="display: flex; align-items: center;">
                    <el-icon style="margin-right: 8px;">
                      <Search />
                    </el-icon>
                    <span>VAD 语音活动检测</span>
                  </div>
                  <div style="display: flex; align-items: center; gap: 10px;">
                    <el-tag :type="vadModelEnabled ? 'success' : 'warning'" size="small">
                      {{ vadModelEnabled ? 'VAD已启用' : 'VAD未启用' }}
                    </el-tag>
                    <el-button :icon="Setting" size="small" @click="showVadConfig = true" :disabled="!vadAvailable">
                      配置
                    </el-button>
                  </div>
                </div>
              </template>

              <div v-if="!vadModelEnabled">
                <el-alert title="VAD功能未启用" type="warning" show-icon :closable="false" style="margin-bottom: 15px;">
                  <template #default>
                    <div style="font-size: 14px;">
                      请在配置文件中启用VAD功能：<code>asr/config.json</code> 中设置 <code>"vad.enabled": true</code>
                    </div>
                  </template>
                </el-alert>
              </div>

              <div v-else>
                <el-row :gutter="20">
                  <!-- VAD检测 -->
                  <el-col :span="8">
                    <el-card shadow="never" style="background-color: #f8f9fa;">
                      <div style="text-align: center;">
                        <h4 style="margin-bottom: 15px;">
                          <el-icon style="margin-right: 4px;">
                            <Search />
                          </el-icon>
                          语音片段检测
                        </h4>
                        <el-upload :before-upload="detectVadSegments" :show-file-list="false"
                          accept=".wav,.mp3,.m4a,.mp4,.flac,.aac,.ogg,.webm" :disabled="vadLoading || isRecording">
                          <el-button type="primary" :icon="Search" :loading="vadLoading" style="width: 100%;">
                            检测语音片段
                          </el-button>
                        </el-upload>
                        <div style="font-size: 12px; color: #909399; margin-top: 8px;">
                          检测音频中的语音活动区域
                        </div>
                      </div>
                    </el-card>
                  </el-col>

                  <!-- VAD分割 -->
                  <el-col :span="8">
                    <el-card shadow="never" style="background-color: #f8f9fa;">
                      <div style="text-align: center;">
                        <h4 style="margin-bottom: 15px;">
                          <el-icon style="margin-right: 4px;">
                            <Edit />
                          </el-icon>
                          音频智能分割
                        </h4>
                        <el-upload :before-upload="splitAudioByVad" :show-file-list="false"
                          accept=".wav,.mp3,.m4a,.mp4,.flac,.aac,.ogg,.webm" :disabled="vadLoading || isRecording">
                          <el-button type="warning" :icon="Edit" :loading="vadLoading" style="width: 100%;">
                            分割音频文件
                          </el-button>
                        </el-upload>
                        <div style="font-size: 12px; color: #909399; margin-top: 8px;">
                          根据语音活动自动分割音频
                        </div>
                      </div>
                    </el-card>
                  </el-col>

                  <!-- VAD状态 -->
                  <el-col :span="8">
                    <el-card shadow="never" style="background-color: #f8f9fa;">
                      <div style="text-align: center;">
                        <h4 style="margin-bottom: 15px;">
                          <el-icon style="margin-right: 4px;">
                            <Link />
                          </el-icon>
                          VAD状态监控
                        </h4>
                        <div style="margin-bottom: 10px;">
                          <el-tag :type="vadStatus.status === 'healthy' ? 'success' :
                            vadStatus.status === 'disabled' ? 'warning' : 'danger'" size="large">
                            {{ vadStatus.status === 'healthy' ? '运行正常' :
                              vadStatus.status === 'disabled' ? '已禁用' : '运行异常' }}
                          </el-tag>
                        </div>
                        <div style="font-size: 12px; color: #909399;">
                          {{ vadStatus.status === 'healthy' ? 'VAD引擎工作正常' :
                            vadStatus.status === 'disabled' ? 'VAD功能已禁用' :
                              vadStatus.error || '状态未知' }}
                        </div>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>

                <!-- VAD检测结果 -->
                <div v-if="vadSegments.length > 0" style="margin-top: 20px;">
                  <h4 style="margin-bottom: 15px;">
                    <el-icon style="margin-right: 4px;">
                      <Document />
                    </el-icon>
                    检测到的语音片段 ({{ vadSegments.length }} 个)
                  </h4>
                  <el-table :data="vadSegments" stripe style="width: 100%;" max-height="300">
                    <el-table-column prop="segment_id" label="片段编号" width="100" align="center" />
                    <el-table-column label="开始时间" width="100" align="center">
                      <template #default="scope">
                        {{ scope.row.start.toFixed(2) }}s
                      </template>
                    </el-table-column>
                    <el-table-column label="结束时间" width="100" align="center">
                      <template #default="scope">
                        {{ scope.row.end.toFixed(2) }}s
                      </template>
                    </el-table-column>
                    <el-table-column label="持续时长" width="100" align="center">
                      <template #default="scope">
                        {{ scope.row.duration.toFixed(2) }}s
                      </template>
                    </el-table-column>
                    <el-table-column label="置信度" width="100" align="center">
                      <template #default="scope">
                        <el-tag :type="scope.row.confidence > 0.8 ? 'success' :
                          scope.row.confidence > 0.6 ? 'warning' : 'danger'" size="small">
                          {{ (scope.row.confidence * 100).toFixed(1) }}%
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="text" label="识别文本" show-overflow-tooltip />
                  </el-table>
                </div>

                <!-- 分割文件结果 -->
                <div v-if="splitFiles.length > 0" style="margin-top: 20px;">
                  <h4 style="margin-bottom: 15px;">
                    <el-icon style="margin-right: 4px;">
                      <FolderOpened />
                    </el-icon>
                    分割后的音频文件 ({{ splitFiles.length }} 个)
                  </h4>
                  <el-table :data="splitFiles" stripe style="width: 100%;" max-height="200">
                    <el-table-column prop="segment_id" label="片段" width="80" align="center" />
                    <el-table-column prop="filename" label="文件名" show-overflow-tooltip />
                    <el-table-column label="文件大小" width="120" align="center">
                      <template #default="scope">
                        {{ (scope.row.file_size / 1024).toFixed(1) }} KB
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="100" align="center">
                      <template #default="scope">
                        <el-button type="primary" size="small" :icon="Download" disabled>
                          下载
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                  <el-alert title="提示" type="info" show-icon :closable="false" style="margin-top: 10px;">
                    <template #default>
                      <div style="font-size: 12px;">
                        分割后的文件保存在服务器临时目录中。实际应用中需要实现文件下载功能。
                      </div>
                    </template>
                  </el-alert>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 使用说明 -->
        <el-row style="margin-top: 20px;">
          <el-col :span="24">
            <el-collapse>
              <el-collapse-item title="💡 VAD 功能使用说明" name="vad-guide">
                <div style="padding: 10px 20px;">
                  <el-row :gutter="20">
                    <el-col :span="8">
                      <h4>🎯 什么是VAD？</h4>
                      <p style="font-size: 14px; line-height: 1.6;">
                        VAD (Voice Activity Detection) 是语音活动检测技术，能够自动识别音频中的语音和非语音片段。
                        本系统集成了先进的 Silero VAD 引擎，提供高精度的语音检测能力。
                      </p>
                    </el-col>

                    <el-col :span="8">
                      <h4>⚡ 主要功能</h4>
                      <ul style="font-size: 14px; line-height: 1.6;">
                        <li><strong>VAD分段识别：</strong>提高长音频识别准确性</li>
                        <li><strong>语音片段检测：</strong>标注音频中的语音时间段</li>
                        <li><strong>智能音频分割：</strong>自动分割音频为语音片段</li>
                        <li><strong>实时状态监控：</strong>监控VAD引擎运行状态</li>
                      </ul>
                    </el-col>

                    <el-col :span="8">
                      <h4>🔧 使用建议</h4>
                      <ul style="font-size: 14px; line-height: 1.6;">
                        <li><strong>会议录音：</strong>使用VAD分段识别模式</li>
                        <li><strong>播客处理：</strong>先检测语音片段，再进行识别</li>
                        <li><strong>长音频：</strong>使用智能分割功能</li>
                        <li><strong>参数调优：</strong>根据音频质量调整检测阈值</li>
                      </ul>
                    </el-col>
                  </el-row>

                  <el-divider />

                  <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px;">
                    <h5 style="margin-top: 0;">📊 参数说明</h5>
                    <el-row :gutter="20" style="font-size: 13px;">
                      <el-col :span="6">
                        <strong>检测阈值 (0.1-0.9):</strong><br>
                        控制语音检测的严格程度，阈值越高越严格。
                      </el-col>
                      <el-col :span="6">
                        <strong>最小语音时长:</strong><br>
                        过短的检测结果将被过滤，避免噪音干扰。
                      </el-col>
                      <el-col :span="6">
                        <strong>最大语音时长:</strong><br>
                        过长的片段将被分割，便于处理。
                      </el-col>
                      <el-col :span="6">
                        <strong>最小静音时长:</strong><br>
                        静音超过此时长才会分割语音片段。
                      </el-col>
                    </el-row>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </el-col>
        </el-row>
      </el-main>
    </el-container>

    <!-- VAD 配置对话框 -->
    <VadConfigDialog v-model="showVadConfig" :vad-config="asrConfig.vad || {}"
      @config-updated="handleVadConfigUpdate" />
  </div>
</template>

<style scoped>
.asr-page {
  height: 100vh;
  background-color: #f5f5f5;
}

.el-header {
  background-color: white;
  border-bottom: 1px solid #e4e7ed;
}

.el-main {
  background-color: #f5f5f5;
}

.rotating {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.recording-pulse {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.5;
    transform: scale(1.1);
  }

  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.el-card {
  border-radius: 8px;
}

.el-card :deep(.el-card__header) {
  background-color: #fafafa;
  border-bottom: 1px solid #ebeef5;
}

.el-upload-dragger {
  border-radius: 6px;
}

.el-descriptions :deep(.el-descriptions__label) {
  font-weight: 500;
}
</style>