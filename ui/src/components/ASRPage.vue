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
  VideoPause
} from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const modelStatus = ref({})
const asrConfig = ref({})
const modelInfo = ref({})
const recognitionResult = ref('')
const audioFile = ref(null)
const testingAudio = ref(false)

// 模型状态计算属性
const modelLoaded = computed(() => modelInfo.value.is_loaded || false)
const funasrAvailable = computed(() => modelInfo.value.funasr_available || false)

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
    } else {
      throw new Error('获取ASR配置失败')
    }
  } catch (error) {
    ElMessage.error(error.message)
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
    
    console.log(`上传文件: ${file.name}, 大小: ${file.size} bytes, 类型: ${file.type}`)
    
    // 检查文件对象
    const actualFile = file.raw || file
    if (!actualFile || !actualFile.name) {
      throw new Error('无效的文件对象')
    }
    
    console.log(`实际文件对象:`, actualFile)
    
    const formData = new FormData()
    formData.append('audio_file', actualFile, actualFile.name)
    
    ElMessage.info('正在识别音频，请稍候...')
    
    const response = await fetch(`${API_BASE}/recognize/file`, {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const text = await response.text()
      try {
        const result = JSON.parse(text)
        if (result.success) {
          recognitionResult.value = result.text
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

// 刷新所有数据
const refreshAll = async () => {
  await Promise.all([
    getModelStatus(),
    getModelInfo(),
    getAsrConfig()
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
    formData.append('audio_file', finalBlob, fileName)
    
    ElMessage.info('正在识别录音，请稍候...')
    
    const response = await fetch(`${API_BASE}/recognize/file`, {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const text = await response.text()
      try {
        const result = JSON.parse(text)
        if (result.success) {
          recognitionResult.value = result.text
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
})
</script>

<template>
  <div class="asr-page">
    <el-container>
      <el-header style="padding: 20px;">
        <div style="display: flex; align-items: center; justify-content: between;">
          <div>
            <h2 style="margin: 0; color: #303133;">
              <el-icon style="margin-right: 8px;"><Microphone /></el-icon>
              ASR 语音识别管理
            </h2>
            <p style="margin: 5px 0 0 0; color: #909399; font-size: 14px;">
              管理FunASR模型，测试语音识别功能
            </p>
          </div>
          <el-button 
            type="primary" 
            :icon="RefreshRight"
            @click="refreshAll"
            :loading="loading"
          >
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
                  <el-icon style="margin-right: 8px;"><Setting /></el-icon>
                  <span>模型状态</span>
                </div>
              </template>

              <!-- 基本信息 -->
              <el-row style="margin-bottom: 20px;">
                <el-col :span="12">
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
                <el-col :span="12">
                  <el-statistic title="模型状态">
                    <template #value>
                      <span :style="{ color: modelLoaded ? '#67C23A' : '#E6A23C' }">
                        {{ modelLoaded ? '已加载' : '未加载' }}
                      </span>
                    </template>
                  </el-statistic>
                </el-col>
              </el-row>

              <!-- 模型操作按钮 -->
              <div style="text-align: center; margin-bottom: 20px;">
                <el-button 
                  type="success" 
                  :icon="Download"
                  @click="loadModel"
                  :loading="loading"
                  :disabled="!funasrAvailable || modelLoaded"
                >
                  加载模型
                </el-button>
                <el-button 
                  type="warning"
                  :icon="Delete"
                  @click="unloadModel"
                  :loading="loading"
                  :disabled="!modelLoaded"
                >
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
              </el-descriptions>
            </el-card>

            <!-- 模型管理卡片 -->
            <el-card shadow="hover">
              <template #header>
                <div style="display: flex; align-items: center;">
                  <el-icon style="margin-right: 8px;"><FolderOpened /></el-icon>
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
                <el-button 
                  type="primary"
                  :icon="Download"
                  @click="migrateModels(true)"
                  :loading="loading"
                  style="margin-bottom: 10px;"
                >
                  复制模型到本地
                </el-button>
                <br>
                <el-button 
                  type="warning"
                  :icon="Upload"
                  @click="migrateModels(false)"
                  :loading="loading"
                  size="small"
                >
                  移动到本地
                </el-button>
                <el-button 
                  type="danger"
                  :icon="Delete"
                  @click="cleanCache"
                  :loading="loading"
                  size="small"
                >
                  清理缓存
                </el-button>
              </div>
            </el-card>
          </el-col>

          <!-- 右侧：语音识别测试 -->
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <div style="display: flex; align-items: center;">
                  <el-icon style="margin-right: 8px;"><Document /></el-icon>
                  <span>语音识别测试</span>
                </div>
              </template>

                             <!-- 录音控制区域 -->
               <div style="margin-bottom: 20px;">
                 <el-card shadow="never" style="background-color: #f8f9fa;">
                   <div style="text-align: center;">
                     <h4 style="margin-bottom: 15px;">现场录音</h4>
                     
                     <!-- 录音按钮 -->
                     <div style="margin-bottom: 15px;">
                       <el-button
                         v-if="!isRecording"
                         type="danger"
                         size="large"
                         round
                         :icon="Microphone"
                         @click="startRecording"
                         :disabled="testingAudio"
                       >
                         开始录音
                       </el-button>
                       
                       <el-button
                         v-else
                         type="warning"
                         size="large"
                         round
                         :icon="VideoPause"
                         @click="stopRecording"
                       >
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
                 <el-upload
                   :before-upload="handleFileUpload"
                   :show-file-list="false"
                   accept=".wav,.mp3,.m4a,.mp4,.flac,.aac,.ogg,.webm"
                   drag
                   style="width: 100%;"
                   :disabled="isRecording"
                 >
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
                  <span>识别结果</span>
                  <el-icon v-if="testingAudio" style="margin-left: 10px;">
                    <RefreshRight class="rotating" />
                  </el-icon>
                </h4>
                <el-input
                  v-model="recognitionResult"
                  type="textarea"
                  :rows="8"
                  placeholder="上传音频文件后，识别结果将显示在这里..."
                  readonly
                  style="font-family: monospace;"
                />
              </div>

              <!-- 支持的格式说明 -->
              <el-alert
                title="支持的音频格式"
                type="info"
                show-icon
                :closable="false"
                style="margin-top: 15px;"
              >
                                 <template #default>
                   <div style="font-size: 12px;">
                     WAV (.wav), MP3 (.mp3), M4A (.m4a), MP4 (.mp4), FLAC (.flac), AAC (.aac), OGG (.ogg), WebM (.webm)
                   </div>
                 </template>
              </el-alert>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
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