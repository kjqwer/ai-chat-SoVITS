<template>
  <el-dialog v-model="visible" :title="mode === 'add' ? '添加AI人格' : '编辑AI人格'" width="900px" @close="handleClose">
    <div class="dialog-content">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px" label-position="left">
        <!-- 基本信息 -->
        <div class="form-section">
          <h4 class="section-title">基本信息</h4>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="人格名称" prop="name">
                <el-input v-model="formData.name" placeholder="请输入人格名称，如：智能助手、创意伙伴等" clearable />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="人格描述" prop="description">
                <el-input v-model="formData.description" placeholder="请输入简短描述，如：友善、专业的AI助手" clearable />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 提示词设置 -->
        <div class="form-section">
          <h4 class="section-title">提示词设置</h4>
          <el-form-item label="系统提示词" prop="prompt">
            <el-input v-model="formData.prompt" type="textarea" :rows="12" placeholder="请输入详细的提示词，定义AI的性格、专长和回答风格..."
              show-word-limit maxlength="2000" />
          </el-form-item>
        </div>

        <!-- 预设模板 -->
        <div class="form-section">
          <h4 class="section-title">快速模板</h4>
          <div class="template-grid">
            <div v-for="template in templates" :key="template.id" class="template-card"
              @click="applyTemplate(template)">
              <div class="template-header">
                <span class="template-name">{{ template.name }}</span>
                <el-tag size="small" type="info">{{ template.category }}</el-tag>
              </div>
              <div class="template-desc">{{ template.description }}</div>
              <div class="template-preview">{{ truncateText(template.prompt, 100) }}</div>
            </div>
          </div>
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
          保存人格
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check } from '@element-plus/icons-vue'

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
  persona: {
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
  id: '',
  name: '',
  description: '',
  prompt: ''
}

const formData = ref({ ...defaultFormData })

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入人格名称', trigger: 'blur' },
    { min: 1, max: 30, message: '人格名称长度在 1 到 30 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入人格描述', trigger: 'blur' },
    { min: 5, max: 200, message: '人格描述长度在 5 到 200 个字符', trigger: 'blur' }
  ],
  prompt: [
    { required: true, message: '请输入提示词', trigger: 'blur' },
    { min: 20, max: 2000, message: '提示词长度在 20 到 2000 个字符', trigger: 'blur' }
  ]
}

// 预设模板
const templates = ref([
  {
    id: 'assistant',
    name: '智能助手',
    category: '通用',
    description: '友善、专业的AI助手',
    prompt: '你是一个友善、专业且富有知识的AI助手。请用清晰、有帮助的方式回答用户的问题。保持礼貌和耐心，如果不确定答案，请诚实说明。在回答时要考虑用户的需求，提供准确、有用的信息。'
  },
  {
    id: 'creative',
    name: '创意伙伴',
    category: '创意',
    description: '富有想象力的创意助手',
    prompt: '你是一个富有创意和想象力的AI伙伴。你善于头脑风暴、创意写作、艺术讨论和创新思维。用生动有趣的方式与用户交流，激发他们的创造力。鼓励用户跳出常规思维，探索新的可能性。'
  },
  {
    id: 'teacher',
    name: '知识导师',
    category: '教育',
    description: '耐心的教学助手',
    prompt: '你是一位耐心、博学的老师。擅长用简单易懂的方式解释复杂概念，提供学习建议和指导。根据学习者的水平调整解释的深度，鼓励提问和思考。用积极正面的语言，帮助用户建立学习信心。'
  },
  {
    id: 'analyst',
    name: '数据分析师',
    category: '专业',
    description: '逻辑严谨的分析专家',
    prompt: '你是一个逻辑严谨、客观理性的数据分析专家。擅长数据分析、问题解决和决策支持。用事实和逻辑来回答问题，提供结构化的分析和建议。在给出结论前，会详细说明分析过程和依据。'
  },
  {
    id: 'therapist',
    name: '心理咨询师',
    category: '生活',
    description: '温暖的心理支持者',
    prompt: '你是一个温暖、理解和支持性的心理咨询师。善于倾听，提供情感支持和建议。用轻松友好的语调交流，关心用户的感受和需求。保持同理心，帮助用户处理情绪问题，但不替代专业心理治疗。'
  },
  {
    id: 'programmer',
    name: '编程导师',
    category: '技术',
    description: '专业的编程指导',
    prompt: '你是一个经验丰富的编程导师。精通多种编程语言和技术栈，能够提供清晰的代码示例和解释。在回答编程问题时，会考虑最佳实践、性能优化和代码可读性。耐心地指导初学者，也能与有经验的开发者深入讨论技术细节。'
  }
])

// 监听人格变化
watch(
  () => props.persona,
  (newPersona) => {
    if (newPersona && Object.keys(newPersona).length > 0) {
      formData.value = {
        ...defaultFormData,
        ...newPersona
      }
    } else {
      formData.value = {
        ...defaultFormData,
        id: `persona_${Date.now()}`
      }
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

    // 如果是新增且没有ID，生成一个
    if (props.mode === 'add' && !formData.value.id) {
      formData.value.id = `persona_${Date.now()}`
    }

    // 发出保存事件
    emit('save', { ...formData.value })

    ElMessage.success('人格配置保存成功')
    visible.value = false
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    saving.value = false
  }
}

const applyTemplate = async (template) => {
  try {
    await ElMessageBox.confirm(
      `确定要应用"${template.name}"模板吗？这将覆盖当前的提示词内容。`,
      '确认应用模板',
      {
        type: 'info',
        confirmButtonText: '应用模板',
        cancelButtonText: '取消'
      }
    )

    formData.value.name = template.name
    formData.value.description = template.description
    formData.value.prompt = template.prompt

    ElMessage.success('模板应用成功')
  } catch {
    // 用户取消
  }
}

const truncateText = (text, maxLength) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}
</script>

<style scoped>
.dialog-content {
  max-height: 75vh;
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

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 15px;
}

.template-card {
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background-color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.template-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  transform: translateY(-2px);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.template-name {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.template-desc {
  color: #606266;
  font-size: 12px;
  margin-bottom: 10px;
}

.template-preview {
  color: #909399;
  font-size: 11px;
  line-height: 1.4;
  background-color: #f8f9fa;
  padding: 8px;
  border-radius: 4px;
  border-left: 3px solid #e4e7ed;
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

:deep(.el-textarea__inner) {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  line-height: 1.6;
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