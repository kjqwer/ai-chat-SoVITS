<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>设置</h1>
      <p>配置GPT-SoVITS的模型、角色和推理参数</p>
    </div>

    <div class="settings-content">
      <!-- 模型设置 -->
      <el-card class="setting-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><Operation /></el-icon>
            <span>模型设置</span>
          </div>
        </template>
        
        <el-form label-width="120px">
          <el-form-item label="SoVITS模型">
            <el-select
              v-model="currentSovitsModel"
              placeholder="请选择模型"
              style="width: 100%"
              :loading="apiStore.loading.models"
              @change="handleModelChange"
            >
              <el-option
                v-for="model in apiStore.sovitsModels"
                :key="model.name"
                :label="model.name"
                :value="model.name"
              />
            </el-select>
            <div class="form-help-text">当前使用的SoVITS模型文件</div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 角色设置 -->
      <el-card class="setting-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><User /></el-icon>
            <span>角色设置</span>
          </div>
        </template>
        
        <el-form label-width="120px">
          <el-form-item label="当前角色">
            <el-select
              v-model="currentCharacter"
              placeholder="请选择或搜索角色"
              style="width: 100%"
              :loading="apiStore.loading.characters || characterSearchLoading"
              filterable
              clearable
              remote
              reserve-keyword
              :remote-method="handleCharacterSearch"
              @change="handleCharacterChange"
              @clear="handleCharacterClear"
            >
              <el-option
                v-for="character in filteredCharacters"
                :key="character.name"
                :label="character.name"
                :value="character.name"
              >
                <span style="float: left">{{ character.name }}</span>
                <span
                  v-if="character.is_current"
                  style="float: right; color: #67c23a; font-size: 12px;"
                >
                  当前
                </span>
              </el-option>
            </el-select>
            <div class="form-help-text">
              当前角色: {{ apiStore.currentCharacter || '未设置' }}
              <span v-if="apiStore.currentCharacterAudio">
                (参考音频: {{ apiStore.currentCharacterAudio }})
              </span>
              <div v-if="apiStore.characters.length > 0" style="margin-top: 5px; color: #909399;">
                共 {{ apiStore.characters.length }} 个角色可选
              </div>
            </div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 推理配置 -->
      <el-card class="setting-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><Setting /></el-icon>
            <span>推理配置</span>
            <el-button
              type="primary"
              size="small"
              :loading="apiStore.loading.config"
              @click="saveInferenceConfig"
              style="margin-left: auto;"
            >
              保存配置
            </el-button>
          </div>
        </template>
        
        <el-form :model="inferenceConfig" label-width="150px" class="inference-form">
          <!-- 语言设置 -->
          <div class="config-section">
            <h4>语言设置</h4>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item :label="CONFIG_LABELS.text_lang">
                  <el-select v-model="inferenceConfig.text_lang" style="width: 100%">
                    <el-option
                      v-for="option in LANGUAGE_OPTIONS"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.text_lang }}</div>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item :label="CONFIG_LABELS.prompt_lang">
                  <el-select v-model="inferenceConfig.prompt_lang" style="width: 100%">
                    <el-option
                      v-for="option in LANGUAGE_OPTIONS"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.prompt_lang }}</div>
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 文本处理 -->
          <div class="config-section">
            <h4>文本处理</h4>
            <el-form-item :label="CONFIG_LABELS.text_split_method">
              <el-select v-model="inferenceConfig.text_split_method" style="width: 100%">
                <el-option
                  v-for="option in TEXT_SPLIT_OPTIONS"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
              <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.text_split_method }}</div>
            </el-form-item>
          </div>

          <!-- 生成参数 -->
          <div class="config-section">
            <h4>生成参数</h4>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item :label="CONFIG_LABELS.top_k">
                  <el-slider
                    v-model="inferenceConfig.top_k"
                    :min="CONFIG_RANGES.top_k.min"
                    :max="CONFIG_RANGES.top_k.max"
                    :step="CONFIG_RANGES.top_k.step"
                    show-input
                    style="width: 100%"
                  />
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.top_k }}</div>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="CONFIG_LABELS.top_p">
                  <el-slider
                    v-model="inferenceConfig.top_p"
                    :min="CONFIG_RANGES.top_p.min"
                    :max="CONFIG_RANGES.top_p.max"
                    :step="CONFIG_RANGES.top_p.step"
                    show-input
                    style="width: 100%"
                  />
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.top_p }}</div>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="CONFIG_LABELS.temperature">
                  <el-slider
                    v-model="inferenceConfig.temperature"
                    :min="CONFIG_RANGES.temperature.min"
                    :max="CONFIG_RANGES.temperature.max"
                    :step="CONFIG_RANGES.temperature.step"
                    show-input
                    style="width: 100%"
                  />
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.temperature }}</div>
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 性能设置 -->
          <div class="config-section">
            <h4>性能设置</h4>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item :label="CONFIG_LABELS.batch_size">
                  <el-slider
                    v-model="inferenceConfig.batch_size"
                    :min="CONFIG_RANGES.batch_size.min"
                    :max="CONFIG_RANGES.batch_size.max"
                    :step="CONFIG_RANGES.batch_size.step"
                    show-input
                    style="width: 100%"
                  />
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.batch_size }}</div>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="CONFIG_LABELS.speed_factor">
                  <el-slider
                    v-model="inferenceConfig.speed_factor"
                    :min="CONFIG_RANGES.speed_factor.min"
                    :max="CONFIG_RANGES.speed_factor.max"
                    :step="CONFIG_RANGES.speed_factor.step"
                    show-input
                    style="width: 100%"
                  />
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.speed_factor }}</div>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="CONFIG_LABELS.fragment_interval">
                  <el-slider
                    v-model="inferenceConfig.fragment_interval"
                    :min="CONFIG_RANGES.fragment_interval.min"
                    :max="CONFIG_RANGES.fragment_interval.max"
                    :step="CONFIG_RANGES.fragment_interval.step"
                    show-input
                    style="width: 100%"
                  />
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.fragment_interval }}</div>
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 高级设置 -->
          <div class="config-section">
            <h4>高级设置</h4>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item :label="CONFIG_LABELS.repetition_penalty">
                  <el-slider
                    v-model="inferenceConfig.repetition_penalty"
                    :min="CONFIG_RANGES.repetition_penalty.min"
                    :max="CONFIG_RANGES.repetition_penalty.max"
                    :step="CONFIG_RANGES.repetition_penalty.step"
                    show-input
                    style="width: 100%"
                  />
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.repetition_penalty }}</div>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="CONFIG_LABELS.sample_steps">
                  <el-select v-model="inferenceConfig.sample_steps" style="width: 100%">
                    <el-option
                      v-for="option in SAMPLE_STEPS_OPTIONS"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.sample_steps }}</div>
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 开关设置 -->
          <div class="config-section">
            <h4>开关设置</h4>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item :label="CONFIG_LABELS.ref_text_free">
                  <el-switch v-model="inferenceConfig.ref_text_free" />
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.ref_text_free }}</div>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="CONFIG_LABELS.split_bucket">
                  <el-switch v-model="inferenceConfig.split_bucket" />
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.split_bucket }}</div>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="CONFIG_LABELS.parallel_infer">
                  <el-switch v-model="inferenceConfig.parallel_infer" />
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.parallel_infer }}</div>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item :label="CONFIG_LABELS.super_sampling">
                  <el-switch v-model="inferenceConfig.super_sampling" />
                  <div class="form-help-text">{{ CONFIG_DESCRIPTIONS.super_sampling }}</div>
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-form>
      </el-card>

      <!-- TTS测试 -->
      <el-card class="setting-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><Microphone /></el-icon>
            <span>文本转语音测试</span>
          </div>
        </template>
        
        <el-form label-width="120px">
          <el-form-item label="测试文本">
            <el-input
              v-model="testText"
              type="textarea"
              :rows="4"
              placeholder="请输入要合成的文本..."
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              :loading="apiStore.loading.tts"
              :disabled="!testText.trim() || !apiStore.currentCharacter"
              @click="handleTTS"
            >
              <el-icon><VideoPlay /></el-icon>
              生成语音
            </el-button>
            
            <el-button
              v-if="audioUrl"
              type="success"
              @click="playAudio"
            >
              <el-icon><VideoPlay /></el-icon>
              播放
            </el-button>
            
            <el-button
              v-if="audioUrl"
              @click="downloadAudio"
            >
              <el-icon><Download /></el-icon>
              下载
            </el-button>
          </el-form-item>
        </el-form>
        
        <!-- 音频播放器 -->
        <div v-if="audioUrl" style="margin-top: 15px;">
          <div style="margin-bottom: 8px; color: #606266; font-size: 14px;">
            <el-icon><Microphone /></el-icon>
            生成的音频文件 ({{ audioGeneratedTime ? formatDateTime(audioGeneratedTime) : '' }})
          </div>
          <audio
            ref="audioPlayer"
            controls
            style="width: 100%;"
            @loadstart="handleAudioLoadStart"
            @canplay="handleAudioCanPlay"
            @error="handleAudioError"
          >
            <source :src="audioUrl" type="audio/wav">
            您的浏览器不支持音频播放。
          </audio>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useApiStore } from '../stores/api.js'
import {
  LANGUAGE_OPTIONS,
  TEXT_SPLIT_OPTIONS,
  SAMPLE_STEPS_OPTIONS,
  CONFIG_RANGES,
  CONFIG_LABELS,
  CONFIG_DESCRIPTIONS
} from '../constants/config.js'

const apiStore = useApiStore()

// 响应式数据
const currentSovitsModel = ref('')
const currentCharacter = ref('')
const inferenceConfig = ref({})
const testText = ref('你好，这是一个测试语音合成的文本。')
const audioUrl = ref('')
const audioPlayer = ref(null)

// 角色搜索相关
const characterSearchLoading = ref(false)
const characterSearchQuery = ref('')
const filteredCharacters = ref([])

// 音频生成时间
const audioGeneratedTime = ref(null)

// 监听store中的推理配置变化
watch(
  () => apiStore.inferenceConfig,
  (newConfig) => {
    inferenceConfig.value = { ...newConfig }
  },
  { deep: true, immediate: true }
)

// 监听store中的当前模型变化
watch(
  () => apiStore.currentSovitsModel,
  (newModel) => {
    currentSovitsModel.value = newModel || ''
  },
  { immediate: true }
)

// 监听store中的当前角色变化
watch(
  () => apiStore.currentCharacter,
  (newCharacter) => {
    currentCharacter.value = newCharacter || ''
  },
  { immediate: true }
)

// 监听角色列表变化
watch(
  () => apiStore.characters,
  (newCharacters) => {
    filteredCharacters.value = [...newCharacters]
  },
  { deep: true, immediate: true }
)

// 处理模型改变
const handleModelChange = async (modelName) => {
  try {
    await apiStore.setSovitsModel(modelName)
    ElMessage.success('模型设置成功')
  } catch (error) {
    ElMessage.error(`模型设置失败: ${error.message}`)
  }
}

// 处理角色改变
const handleCharacterChange = async (characterName) => {
  try {
    await apiStore.setCharacter(characterName)
    ElMessage.success('角色设置成功')
  } catch (error) {
    ElMessage.error(`角色设置失败: ${error.message}`)
  }
}

// 角色搜索处理
const handleCharacterSearch = (query) => {
  characterSearchQuery.value = query
  filterCharacters(query)
}

// 过滤角色
const filterCharacters = (query) => {
  if (!query) {
    filteredCharacters.value = [...apiStore.characters]
    return
  }
  
  const lowerQuery = query.toLowerCase()
  filteredCharacters.value = apiStore.characters.filter(character =>
    character.name.toLowerCase().includes(lowerQuery)
  )
}

// 清除角色选择
const handleCharacterClear = () => {
  currentCharacter.value = ''
  characterSearchQuery.value = ''
  filteredCharacters.value = [...apiStore.characters]
}

// 保存推理配置
const saveInferenceConfig = async () => {
  try {
    await apiStore.updateInferenceConfig(inferenceConfig.value)
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error(`配置保存失败: ${error.message}`)
  }
}

// 处理TTS
const handleTTS = async () => {
  if (!testText.value.trim()) {
    ElMessage.warning('请输入测试文本')
    return
  }
  
  if (!apiStore.currentCharacter) {
    ElMessage.warning('请先设置角色')
    return
  }

  try {
    const audioBlob = await apiStore.textToSpeech(testText.value)
    
    // 清理旧的音频URL
    if (audioUrl.value) {
      URL.revokeObjectURL(audioUrl.value)
    }
    
    // 创建新的音频URL
    audioUrl.value = URL.createObjectURL(audioBlob)
    audioGeneratedTime.value = new Date()
    
    // 等待DOM更新后重新加载音频
    await nextTick()
    if (audioPlayer.value) {
      audioPlayer.value.load() // 重新加载音频源
      // 可选：自动播放新生成的音频
      // audioPlayer.value.play()
    }
    
    ElMessage.success('语音生成成功！点击播放按钮收听')
  } catch (error) {
    ElMessage.error(`语音生成失败: ${error.message}`)
  }
}

// 播放音频
const playAudio = () => {
  if (audioPlayer.value) {
    audioPlayer.value.play()
  }
}

// 下载音频
const downloadAudio = () => {
  if (audioUrl.value) {
    const link = document.createElement('a')
    link.href = audioUrl.value
    link.download = `tts_output_${Date.now()}.wav`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

// 音频事件处理
const handleAudioLoadStart = () => {
  console.log('Audio loading started')
}

const handleAudioCanPlay = () => {
  console.log('Audio can play')
}

const handleAudioError = (e) => {
  console.error('Audio error:', e)
  ElMessage.error('音频播放出错')
}

// 格式化时间
const formatDateTime = (date) => {
  const now = new Date(date)
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  return `${hours}:${minutes}:${seconds}`
}

// 组件卸载时清理音频URL
onMounted(() => {
  return () => {
    if (audioUrl.value) {
      URL.revokeObjectURL(audioUrl.value)
    }
  }
})
</script>

<style scoped>
.settings-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 500;
}

.page-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.setting-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #303133;
}

.inference-form {
  max-width: none;
}

.config-section {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f2f5;
}

.config-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.config-section h4 {
  margin: 0 0 20px 0;
  color: #409eff;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-section h4::before {
  content: '';
  width: 4px;
  height: 16px;
  background-color: #409eff;
  border-radius: 2px;
}

.form-help-text {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
  line-height: 1.4;
}

:deep(.el-slider) {
  margin-right: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

:deep(.el-card__header) {
  background-color: #fafbfc;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-switch) {
  margin-right: 10px;
}
</style> 