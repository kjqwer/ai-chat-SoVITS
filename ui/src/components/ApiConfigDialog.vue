<template>
  <el-dialog v-model="visible" :title="mode === 'add' ? '添加API配置' : '编辑API配置'" width="800px" @close="handleClose">
    <div class="dialog-content">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="140px" label-position="left">
        <!-- 基本信息 -->
        <div class="form-section">
          <h4 class="section-title">基本信息</h4>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="配置名称" prop="name">
                <el-input v-model="formData.name" placeholder="请输入配置名称，如：OpenAI官方、Azure等" clearable />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="模型名称" prop="model">
                <el-input v-model="formData.model" placeholder="如：gpt-3.5-turbo、gpt-4等" clearable />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="API地址" prop="baseURL">
            <el-input v-model="formData.baseURL" placeholder="请输入完整的API地址" clearable />
            <div class="form-help">
              <div class="help-item">
                <strong>OpenAI官方：</strong>
                <code>https://api.openai.com/v1</code>
              </div>
              <div class="help-item">
                <strong>Azure OpenAI：</strong>
                <code>https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2023-05-15</code>
              </div>
            </div>
          </el-form-item>

          <el-form-item label="API密钥" prop="apiKey">
            <el-input v-model="formData.apiKey" type="password" placeholder="请输入API密钥" show-password clearable />
            <div class="form-help">
              <el-icon>
                <Warning />
              </el-icon>
              API密钥将会被加密存储，页面上只显示部分字符
            </div>
          </el-form-item>
        </div>

        <!-- 请求配置 -->
        <div class="form-section">
          <h4 class="section-title">请求配置</h4>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="请求超时" prop="timeout">
                <el-input-number v-model="formData.timeout" :min="5" :max="300" :step="5" style="width: 100%" />
                <template #append>秒</template>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="设为默认">
                <el-switch v-model="formData.isDefault" active-text="是" inactive-text="否" />
                <div class="form-help">设为默认后，新对话将使用此API配置</div>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 模型参数 -->
        <div class="form-section">
          <h4 class="section-title">模型参数</h4>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="Temperature">
                <div class="slider-container">
                  <el-slider v-model="formData.defaultParams.temperature" :min="0" :max="2" :step="0.1" show-input
                    :input-size="'small'" />
                </div>
                <div class="form-help">控制输出的随机性，0-2之间，值越高越随机</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="Max Tokens">
                <el-input-number v-model="formData.defaultParams.max_tokens" :min="100" :max="4000" :step="100"
                  style="width: 100%" />
                <div class="form-help">单次回答的最大字符数限制</div>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="Top P">
                <div class="slider-container">
                  <el-slider v-model="formData.defaultParams.top_p" :min="0" :max="1" :step="0.05" show-input
                    :input-size="'small'" />
                </div>
                <div class="form-help">核采样参数，控制生成的多样性</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="Frequency Penalty">
                <div class="slider-container">
                  <el-slider v-model="formData.defaultParams.frequency_penalty" :min="-2" :max="2" :step="0.1"
                    show-input :input-size="'small'" />
                </div>
                <div class="form-help">频率惩罚，减少重复内容</div>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="Presence Penalty">
                <div class="slider-container">
                  <el-slider v-model="formData.defaultParams.presence_penalty" :min="-2" :max="2" :step="0.1" show-input
                    :input-size="'small'" />
                </div>
                <div class="form-help">存在惩罚，鼓励谈论新话题</div>
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose" size="large">
          取消
        </el-button>
        <el-button type="primary" @click="handleSave" size="large" :loading="saving">
          <el-icon>
            <Check />
          </el-icon>
          保存配置
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Warning } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  mode: {
    type: String,
    default: 'add', // 'add' | 'edit'
    validator: (value) => ['add', 'edit'].includes(value)
  },
  config: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'save'])

// 响应式数据
const formRef = ref(null)
const saving = ref(false)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 表单数据
const defaultFormData = {
  name: '',
  baseURL: 'https://api.openai.com/v1',
  apiKey: '',
  model: 'gpt-3.5-turbo',
  timeout: 30,
  isDefault: false,
  defaultParams: {
    temperature: 0.7,
    max_tokens: 1000,
    top_p: 1,
    frequency_penalty: 0,
    presence_penalty: 0
  }
}

const formData = ref({ ...defaultFormData })

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' },
    { min: 2, max: 50, message: '配置名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  baseURL: [
    { required: true, message: '请输入API地址', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL地址', trigger: 'blur' }
  ],
  apiKey: [
    { required: true, message: '请输入API密钥', trigger: 'blur' },
    { min: 10, message: 'API密钥长度至少10个字符', trigger: 'blur' }
  ],
  model: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ]
}

// 监听配置变化
watch(
  () => props.config,
  (newConfig) => {
    if (newConfig && Object.keys(newConfig).length > 0) {
      formData.value = {
        ...defaultFormData,
        ...newConfig,
        defaultParams: {
          ...defaultFormData.defaultParams,
          ...newConfig.defaultParams
        }
      }
    } else {
      formData.value = { ...defaultFormData }
    }
  },
  { immediate: true, deep: true }
)

// 监听对话框显示状态
watch(visible, (newVisible) => {
  if (newVisible) {
    // 重置表单验证状态
    setTimeout(() => {
      formRef.value?.clearValidate()
    }, 100)
  }
})

// 方法
const handleClose = () => {
  visible.value = false
}

const handleSave = async () => {
  try {
    await formRef.value.validate()
    saving.value = true

    // 发出保存事件
    emit('save', { ...formData.value })

    ElMessage.success('API配置保存成功')
    visible.value = false
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.dialog-content {
  max-height: 70vh;
  overflow-y: auto;
  padding: 0 10px;
}

.form-section {
  margin-bottom: 30px;
  padding: 20px;
  background-color: #fafafa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.section-title {
  margin: 0 0 20px 0;
  color: #409eff;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title::before {
  content: '';
  width: 4px;
  height: 16px;
  background-color: #409eff;
  border-radius: 2px;
}

.form-help {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.form-help .help-item {
  margin-bottom: 4px;
}

.form-help code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  color: #e6a23c;
}

.form-help .el-icon {
  margin-right: 4px;
  color: #e6a23c;
}

.slider-container {
  padding-right: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  padding: 20px 0 10px 0;
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: #606266;
}

:deep(.el-input-group__append) {
  background-color: #f5f7fa;
  color: #909399;
  border-color: #dcdfe6;
}

:deep(.el-slider__input) {
  width: 80px !important;
}

/* 滚动条样式 */
.dialog-content::-webkit-scrollbar {
  width: 6px;
}

.dialog-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>