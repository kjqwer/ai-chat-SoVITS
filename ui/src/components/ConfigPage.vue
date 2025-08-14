<template>
  <div class="config-page">
    <div class="page-header">
      <h1>配置管理</h1>
      <p>管理AI对话的配置参数和人格设置</p>
    </div>

    <div class="config-content">
      <!-- API配置管理 -->
      <el-card class="config-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon>
              <Key />
            </el-icon>
            <span>API配置</span>
            <el-button type="primary" size="small" @click="addApiConfig" style="margin-left: auto;">
              <el-icon>
                <Plus />
              </el-icon>
              添加API
            </el-button>
          </div>
        </template>

        <div v-if="apiConfigs.length === 0" class="empty-state">
          <el-empty description="暂无API配置">
            <el-button type="primary" @click="addApiConfig">添加第一个API配置</el-button>
          </el-empty>
        </div>

        <div v-else class="api-configs">
          <div v-for="(config, index) in apiConfigs" :key="index" class="api-config-item">
            <el-card shadow="hover">
              <template #header>
                <div class="api-header">
                  <span class="api-name">{{ config.name || `API配置 ${index + 1}` }}</span>
                  <div class="api-actions">
                    <el-tag v-if="config.isDefault" type="success" size="small">默认</el-tag>
                    <el-button text size="small" @click="editApiConfig(index)">
                      编辑
                    </el-button>
                    <el-button text size="small" type="danger" @click="deleteApiConfig(index)"
                      :disabled="apiConfigs.length === 1">
                      删除
                    </el-button>
                  </div>
                </div>
              </template>

              <div class="api-info">
                <div class="info-row">
                  <span class="label">API地址:</span>
                  <span class="value">{{ config.baseURL }}</span>
                </div>
                <div class="info-row">
                  <span class="label">模型:</span>
                  <span class="value">{{ config.model }}</span>
                </div>
                <div class="info-row">
                  <span class="label">API密钥:</span>
                  <span class="value">{{ maskApiKey(config.apiKey) }}</span>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </el-card>

      <!-- 人格配置管理 -->
      <el-card class="config-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon>
              <User />
            </el-icon>
            <span>AI人格设置</span>
            <el-button type="primary" size="small" @click="addPersona" style="margin-left: auto;">
              <el-icon>
                <Plus />
              </el-icon>
              添加人格
            </el-button>
          </div>
        </template>

        <div v-if="personas.length === 0" class="empty-state">
          <el-empty description="暂无人格配置">
            <el-button type="primary" @click="addPersona">添加第一个人格</el-button>
          </el-empty>
        </div>

        <div v-else class="personas">
          <div v-for="(persona, index) in personas" :key="persona.id" class="persona-item">
            <el-card shadow="hover">
              <template #header>
                <div class="persona-header">
                  <div class="persona-info">
                    <span class="persona-name">{{ persona.name }}</span>
                    <span class="persona-desc">{{ truncateText(persona.description, 10) }}</span>
                  </div>
                  <div class="persona-actions">
                    <el-button text size="small" @click="editPersona(index)">
                      编辑
                    </el-button>
                    <el-button text size="small" type="danger" @click="deletePersona(index)"
                      :disabled="personas.length === 1">
                      删除
                    </el-button>
                  </div>
                </div>
              </template>

              <div class="persona-prompt">
                <div class="prompt-label">提示词:</div>
                <div class="prompt-text">{{ truncateText(persona.prompt, 200) }}</div>
              </div>
            </el-card>
          </div>
        </div>
      </el-card>

      <!-- 保存按钮 -->
      <div class="save-actions">
        <el-button type="success" size="large" @click="saveConfig" :loading="saving">
          <el-icon>
            <Check />
          </el-icon>
          保存配置
        </el-button>
        <el-button size="large" @click="resetConfig">
          <el-icon>
            <RefreshLeft />
          </el-icon>
          重置配置
        </el-button>
      </div>
    </div>

    <!-- API配置编辑对话框 -->
    <ApiConfigDialog v-model="apiDialogVisible" :mode="apiDialogMode" :config="currentApiConfig"
      @save="handleApiConfigSave" />

    <!-- 人格编辑对话框 -->
    <PersonaDialog v-model="personaDialogVisible" :mode="personaDialogMode" :persona="currentPersona"
      @save="handlePersonaSave" />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Key,
  Plus,
  User,
  Check,
  RefreshLeft
} from '@element-plus/icons-vue'
import ApiConfigDialog from './ApiConfigDialog.vue'
import PersonaDialog from './PersonaDialog.vue'

// 响应式数据
const apiConfigs = ref([])
const personas = ref([])
const saving = ref(false)

// 对话框状态
const apiDialogVisible = ref(false)
const personaDialogVisible = ref(false)
const apiDialogMode = ref('add') // 'add' | 'edit'
const personaDialogMode = ref('add') // 'add' | 'edit'
const currentApiIndex = ref(-1)
const currentPersonaIndex = ref(-1)



// 当前编辑数据存储（用于传递给子组件）
const currentApiConfig = ref({})
const currentPersona = ref({})

// 加载配置
const loadConfig = async () => {
  try {
    const response = await fetch('/ai-config.json')
    if (response.ok) {
      const config = await response.json()

      // 处理API配置
      if (config.API_CONFIGS && Array.isArray(config.API_CONFIGS)) {
        apiConfigs.value = config.API_CONFIGS.map(cfg => ({
          ...cfg,
          timeout: cfg.timeout / 1000 // 转换为秒
        }))
      } else if (config.AI_CONFIG) {
        // 兼容旧格式
        apiConfigs.value = [{
          name: '默认配置',
          ...config.AI_CONFIG,
          timeout: config.AI_CONFIG.timeout / 1000,
          isDefault: true
        }]
      }

      // 处理人格配置
      if (config.DEFAULT_PERSONAS && Array.isArray(config.DEFAULT_PERSONAS)) {
        personas.value = [...config.DEFAULT_PERSONAS]
      }

      ElMessage.success('配置加载成功')
    } else {
      // 配置文件不存在，创建默认配置
      await createDefaultConfig()
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    await createDefaultConfig()
  }
}

// 创建默认配置
const createDefaultConfig = async () => {
  apiConfigs.value = [{
    name: '默认OpenAI配置',
    baseURL: 'https://api.openai.com/v1',
    apiKey: 'your-openai-api-key',
    model: 'gpt-3.5-turbo',
    timeout: 30,
    isDefault: true,
    defaultParams: {
      temperature: 0.7,
      max_tokens: 1000,
      top_p: 1,
      frequency_penalty: 0,
      presence_penalty: 0
    }
  }]

  personas.value = [{
    id: 'assistant',
    name: '智能助手',
    description: '友善、专业的AI助手',
    prompt: '你是一个友善、专业且富有知识的AI助手。请用清晰、有帮助的方式回答用户的问题。保持礼貌和耐心，如果不确定答案，请诚实说明。'
  }]

  ElMessage.info('已创建默认配置')
}

// 保存配置
const saveConfig = async () => {
  try {
    saving.value = true

    // 确保有默认API配置
    const hasDefault = apiConfigs.value.some(cfg => cfg.isDefault)
    if (!hasDefault && apiConfigs.value.length > 0) {
      apiConfigs.value[0].isDefault = true
    }

    // 构建配置对象
    const config = {
      API_CONFIGS: apiConfigs.value.map(cfg => ({
        ...cfg,
        timeout: cfg.timeout * 1000 // 转换为毫秒
      })),
      AI_CONFIG: apiConfigs.value.find(cfg => cfg.isDefault) || apiConfigs.value[0],
      DEFAULT_PERSONAS: personas.value
    }

    // 发送到后端保存
    const response = await fetch('/api/save-config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config)
    })

    if (response.ok) {
      ElMessage.success('配置保存成功')
    } else {
      throw new Error('保存失败')
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

// API配置管理
const addApiConfig = () => {
  currentApiConfig.value = {}
  apiDialogMode.value = 'add'
  currentApiIndex.value = -1
  apiDialogVisible.value = true
}

const editApiConfig = (index) => {
  currentApiConfig.value = { ...apiConfigs.value[index] }
  apiDialogMode.value = 'edit'
  currentApiIndex.value = index
  apiDialogVisible.value = true
}

const handleApiConfigSave = (config) => {
  if (config.isDefault) {
    // 如果设为默认，取消其他配置的默认状态
    apiConfigs.value.forEach(cfg => cfg.isDefault = false)
  }

  if (apiDialogMode.value === 'add') {
    apiConfigs.value.push({ ...config })
  } else {
    apiConfigs.value[currentApiIndex.value] = { ...config }
  }
}

const deleteApiConfig = async (index) => {
  try {
    await ElMessageBox.confirm('确定要删除这个API配置吗？', '确认删除', {
      type: 'warning'
    })

    apiConfigs.value.splice(index, 1)
    ElMessage.success('API配置已删除')
  } catch {
    // 用户取消删除
  }
}

// 人格管理
const addPersona = () => {
  currentPersona.value = {}
  personaDialogMode.value = 'add'
  currentPersonaIndex.value = -1
  personaDialogVisible.value = true
}

const editPersona = (index) => {
  currentPersona.value = { ...personas.value[index] }
  personaDialogMode.value = 'edit'
  currentPersonaIndex.value = index
  personaDialogVisible.value = true
}

const handlePersonaSave = (persona) => {
  if (personaDialogMode.value === 'add') {
    personas.value.push({ ...persona })
  } else {
    personas.value[currentPersonaIndex.value] = { ...persona }
  }
}

const deletePersona = async (index) => {
  try {
    await ElMessageBox.confirm('确定要删除这个人格配置吗？', '确认删除', {
      type: 'warning'
    })

    personas.value.splice(index, 1)
    ElMessage.success('人格配置已删除')
  } catch {
    // 用户取消删除
  }
}

// 重置配置
const resetConfig = async () => {
  try {
    await ElMessageBox.confirm('确定要重置所有配置吗？这将清除所有自定义设置。', '确认重置', {
      type: 'warning'
    })

    await createDefaultConfig()
    ElMessage.success('配置已重置')
  } catch {
    // 用户取消重置
  }
}

// 工具函数
const maskApiKey = (apiKey) => {
  if (!apiKey || apiKey.length <= 8) return '••••••••'
  return apiKey.substring(0, 4) + '••••••••' + apiKey.substring(apiKey.length - 4)
}

const truncateText = (text, maxLength) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 组件挂载时加载配置
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.config-page {
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

.config-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-card {
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

.empty-state {
  padding: 40px;
  text-align: center;
}

.api-configs,
.personas {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.api-config-item,
.persona-item {
  height: fit-content;
  min-height: 200px;
}

.persona-item .el-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.persona-item .el-card__body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.api-header,
.persona-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.api-name {
  font-weight: 500;
  color: #303133;
}

.api-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.api-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
}

.value {
  color: #303133;
  word-break: break-all;
}

.persona-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.persona-name {
  font-weight: 500;
  color: #303133;
}

.persona-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  display: block;
  margin-top: 4px;
}

.persona-actions {
  display: flex;
  gap: 8px;
}

.persona-prompt {
  margin-top: 15px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.prompt-label {
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
}

.prompt-text {
  color: #303133;
  line-height: 1.5;
  background-color: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 14px;
}

.save-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 30px 0;
}

:deep(.el-card__header) {
  background-color: #fafbfc;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 768px) {

  .api-configs,
  .personas {
    grid-template-columns: 1fr;
  }

  .save-actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>