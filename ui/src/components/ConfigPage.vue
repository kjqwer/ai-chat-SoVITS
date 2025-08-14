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
        <!-- 变更提醒 -->
        <div v-if="hasChanges" class="changes-warning">
          <el-alert title="您有未保存的配置修改" type="warning" :closable="false" show-icon style="margin-bottom: 20px;">
            请点击"保存配置"按钮保存您的修改，否则刷新页面后将丢失所有更改。
          </el-alert>
        </div>

        <div class="action-buttons">
          <el-button :type="hasChanges ? 'warning' : 'success'" size="large" @click="saveConfig" :loading="saving"
            :disabled="!hasChanges" :class="{ 'save-button-highlight': hasChanges }" title="保存所有配置修改，或使用快捷键 Ctrl+S">
            <el-icon>
              <Check />
            </el-icon>
            {{ hasChanges ? '保存配置 *' : '保存配置' }}
          </el-button>
          <el-button size="large" @click="resetConfig">
            <el-icon>
              <RefreshLeft />
            </el-icon>
            重置配置
          </el-button>
          <el-button type="info" size="large" @click="diagnoseConfig">
            <el-icon>
              <Tools />
            </el-icon>
            诊断配置
          </el-button>
        </div>
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
import { ref, onMounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import {
  Key,
  Plus,
  User,
  Check,
  RefreshLeft,
  Tools
} from '@element-plus/icons-vue'
import ApiConfigDialog from './ApiConfigDialog.vue'
import PersonaDialog from './PersonaDialog.vue'
import { useChatStore } from '../stores/chat.js'

// Store引用
const chatStore = useChatStore()

// 响应式数据
const apiConfigs = ref([])
const personas = ref([])
const saving = ref(false)

// 添加原始配置用于变更检测
const originalApiConfigs = ref([])
const originalPersonas = ref([])

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

// 计算是否有变更
const hasChanges = computed(() => {
  return JSON.stringify(apiConfigs.value) !== JSON.stringify(originalApiConfigs.value) ||
    JSON.stringify(personas.value) !== JSON.stringify(originalPersonas.value)
})

// 加载配置
const loadConfig = async () => {
  try {
    // 改为从API端点加载配置
    const response = await fetch('/api/get-config')
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

      // 保存原始配置
      originalApiConfigs.value = JSON.parse(JSON.stringify(apiConfigs.value))
      originalPersonas.value = JSON.parse(JSON.stringify(personas.value))

      ElMessage.success('配置加载成功')
    } else {
      // 配置文件不存在，创建默认配置
      await createDefaultConfig()
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    // 尝试从静态文件加载作为后备
    await loadConfigFromStaticFile()
  }
}

// 从静态文件加载配置（后备方案）
const loadConfigFromStaticFile = async () => {
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

      // 保存原始配置
      originalApiConfigs.value = JSON.parse(JSON.stringify(apiConfigs.value))
      originalPersonas.value = JSON.parse(JSON.stringify(personas.value))

      ElMessage.success('配置加载成功')
    } else {
      await createDefaultConfig()
    }
  } catch (error) {
    console.error('从静态文件加载配置失败:', error)
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

  // 保存原始配置
  originalApiConfigs.value = JSON.parse(JSON.stringify(apiConfigs.value))
  originalPersonas.value = JSON.parse(JSON.stringify(personas.value))

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
    const defaultConfig = apiConfigs.value.find(cfg => cfg.isDefault) || apiConfigs.value[0]
    const config = {
      API_CONFIGS: apiConfigs.value.map(cfg => ({
        ...cfg,
        timeout: cfg.timeout * 1000 // 转换为毫秒
      })),
      AI_CONFIG: {
        ...defaultConfig,
        timeout: defaultConfig.timeout * 1000 // 确保AI_CONFIG中的timeout也转换为毫秒
      },
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
      // 保存成功后更新原始配置，清除变更状态
      originalApiConfigs.value = JSON.parse(JSON.stringify(apiConfigs.value))
      originalPersonas.value = JSON.parse(JSON.stringify(personas.value))
      ElMessage.success('配置保存成功')
      // 重新加载聊天配置
      await chatStore.reloadConfig()
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

  // 提示用户保存配置
  if (hasChanges.value) {
    ElMessage.info('请点击"保存配置"按钮保存您的修改')
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

  // 提示用户保存配置
  if (hasChanges.value) {
    ElMessage.info('请点击"保存配置"按钮保存您的修改')
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

// 诊断配置
const diagnoseConfig = async () => {
  try {
    let diagnosticInfo = '# 配置诊断报告\n\n'

    // 检查API配置
    diagnosticInfo += '## API配置检查\n'
    if (apiConfigs.value.length === 0) {
      diagnosticInfo += '❌ 没有配置任何API\n'
    } else {
      diagnosticInfo += `✅ 已配置 ${apiConfigs.value.length} 个API\n`

      apiConfigs.value.forEach((config, index) => {
        diagnosticInfo += `\n### API配置 ${index + 1}: ${config.name}\n`
        diagnosticInfo += `- 地址: ${config.baseURL}\n`
        diagnosticInfo += `- 模型: ${config.model}\n`
        diagnosticInfo += `- 超时: ${config.timeout}秒 (${config.timeout * 1000}ms)\n`
        diagnosticInfo += `- 默认配置: ${config.isDefault ? '是' : '否'}\n`

        // 检查API配置问题
        if (!config.apiKey || config.apiKey === 'your-openai-api-key') {
          diagnosticInfo += '⚠️ API密钥未设置或使用默认值\n'
        }
        if (config.timeout < 10) {
          diagnosticInfo += '⚠️ 超时时间过短，可能导致请求失败\n'
        }
        if (config.timeout > 60) {
          diagnosticInfo += '⚠️ 超时时间过长，用户体验不佳\n'
        }
      })
    }

    // 检查人格配置
    diagnosticInfo += '\n## 人格配置检查\n'
    if (personas.value.length === 0) {
      diagnosticInfo += '❌ 没有配置任何AI人格\n'
    } else {
      diagnosticInfo += `✅ 已配置 ${personas.value.length} 个AI人格\n`
      personas.value.forEach((persona, index) => {
        diagnosticInfo += `\n### 人格 ${index + 1}: ${persona.name}\n`
        diagnosticInfo += `- 描述: ${persona.description}\n`
        diagnosticInfo += `- 提示词长度: ${persona.prompt?.length || 0} 字符\n`

        if (!persona.prompt || persona.prompt.length < 10) {
          diagnosticInfo += '⚠️ 提示词过短，可能影响AI表现\n'
        }
      })
    }

    // 检查配置保存状态
    diagnosticInfo += '\n## 配置状态检查\n'
    if (hasChanges.value) {
      diagnosticInfo += '⚠️ 有未保存的配置修改\n'
    } else {
      diagnosticInfo += '✅ 所有配置都已保存\n'
    }

    // 检查常见问题
    diagnosticInfo += '\n## 常见问题检查\n'

    // 检查超时配置
    const timeoutIssues = apiConfigs.value.filter(cfg => cfg.timeout <= 1)
    if (timeoutIssues.length > 0) {
      diagnosticInfo += '🚨 发现超时配置异常:\n'
      timeoutIssues.forEach(cfg => {
        diagnosticInfo += `- "${cfg.name}": ${cfg.timeout}秒 → 这会导致"timeout of ${cfg.timeout * 1000}ms exceeded"错误\n`
      })
      diagnosticInfo += '\n**解决方案**: 将超时时间调整为30秒或更长\n'
    }

    // 显示诊断结果
    await ElMessageBox.alert(diagnosticInfo, '配置诊断报告', {
      confirmButtonText: '知道了',
      type: 'info',
      dangerouslyUseHTMLString: false,
      customClass: 'diagnostic-dialog'
    })

  } catch (error) {
    ElMessage.error('诊断配置时出错')
    console.error('配置诊断错误:', error)
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

  // 页面离开前检查未保存的配置
  const handleBeforeUnload = (event) => {
    if (hasChanges.value) {
      event.preventDefault()
      event.returnValue = '您有未保存的配置修改，确定要离开吗？'
      return '您有未保存的配置修改，确定要离开吗？'
    }
  }

  // 快捷键保存配置 (Ctrl+S)
  const handleKeyDown = (event) => {
    if (event.ctrlKey && event.key === 's') {
      event.preventDefault()
      if (hasChanges.value && !saving.value) {
        saveConfig()
        ElMessage.info('使用快捷键 Ctrl+S 保存配置')
      }
    }
  }

  window.addEventListener('beforeunload', handleBeforeUnload)
  document.addEventListener('keydown', handleKeyDown)

  // 组件卸载时清理事件监听器
  return () => {
    window.removeEventListener('beforeunload', handleBeforeUnload)
    document.removeEventListener('keydown', handleKeyDown)
  }
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
  flex-direction: column;
  align-items: center;
  padding: 30px 0;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.changes-warning {
  width: 100%;
  max-width: 600px;
  margin-bottom: 20px;
}

/* 保存按钮高亮效果 */
.save-button-highlight {
  position: relative;
  overflow: hidden;
  animation: pulse 2s infinite;
}

.save-button-highlight::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.save-button-highlight:hover::before {
  left: 100%;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }

  50% {
    opacity: 0.8;
  }

  100% {
    opacity: 1;
  }
}

:deep(.el-card__header) {
  background-color: #fafbfc;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

/* 诊断对话框样式 */
:deep(.diagnostic-dialog) {
  max-width: 800px;
}

:deep(.diagnostic-dialog .el-message-box__content) {
  max-height: 500px;
  overflow-y: auto;
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

/* 响应式设计 */
@media (max-width: 768px) {

  .api-configs,
  .personas {
    grid-template-columns: 1fr;
  }

  .save-actions {
    padding: 20px 10px;
  }

  .action-buttons {
    flex-direction: column;
    align-items: center;
    gap: 15px;
  }

  .action-buttons .el-button {
    width: 100%;
    max-width: 200px;
  }

  .changes-warning {
    padding: 0 10px;
  }

  :deep(.diagnostic-dialog) {
    max-width: 95vw;
  }
}
</style>