<template>
    <el-dialog v-model="visible" title="VAD 配置设置" width="600px" :before-close="handleClose">
        <div class="vad-config">
            <el-form :model="config" label-width="150px" size="default">
                <el-form-item label="启用VAD">
                    <el-switch v-model="config.enabled" active-text="启用" inactive-text="禁用" />
                    <div class="form-tip">
                        启用后将使用Silero VAD进行语音活动检测
                    </div>
                </el-form-item>

                <el-form-item label="检测阈值">
                    <el-slider v-model="config.threshold" :min="0.1" :max="0.9" :step="0.1" show-input
                        :input-size="'small'" />
                    <div class="form-tip">
                        语音检测的置信度阈值，越高越严格 (0.1-0.9)
                    </div>
                </el-form-item>

                <el-form-item label="最小语音时长">
                    <el-input-number v-model="config.min_speech_duration_ms" :min="50" :max="2000" :step="50"
                        controls-position="right" />
                    <span style="margin-left: 8px; color: #909399;">毫秒</span>
                    <div class="form-tip">
                        过短的检测结果将被过滤 (50-2000ms)
                    </div>
                </el-form-item>

                <el-form-item label="最大语音时长">
                    <el-input-number v-model="config.max_speech_duration_s" :min="5" :max="120" :step="5"
                        controls-position="right" />
                    <span style="margin-left: 8px; color: #909399;">秒</span>
                    <div class="form-tip">
                        过长的语音片段将被强制分割 (5-120s)
                    </div>
                </el-form-item>

                <el-form-item label="最小静音时长">
                    <el-input-number v-model="config.min_silence_duration_ms" :min="50" :max="1000" :step="50"
                        controls-position="right" />
                    <span style="margin-left: 8px; color: #909399;">毫秒</span>
                    <div class="form-tip">
                        静音超过此时长才会分割语音 (50-1000ms)
                    </div>
                </el-form-item>

                <el-form-item label="语音填充时长">
                    <el-input-number v-model="config.speech_pad_ms" :min="0" :max="200" :step="10"
                        controls-position="right" />
                    <span style="margin-left: 8px; color: #909399;">毫秒</span>
                    <div class="form-tip">
                        在语音片段前后添加的填充时间 (0-200ms)
                    </div>
                </el-form-item>

                <el-form-item label="ASR前预处理">
                    <el-switch v-model="config.pre_process" active-text="启用" inactive-text="禁用" />
                    <div class="form-tip">
                        在语音识别前使用VAD进行预处理
                    </div>
                </el-form-item>

                <el-form-item label="返回分段信息">
                    <el-switch v-model="config.return_segments" active-text="返回" inactive-text="不返回" />
                    <div class="form-tip">
                        是否在识别结果中返回详细的分段信息
                    </div>
                </el-form-item>

                <el-form-item label="模型类型">
                    <el-select v-model="config.model_type" style="width: 200px;">
                        <el-option label="Silero VAD (PyTorch)" value="silero_vad" />
                        <el-option label="ONNX Runtime" value="onnx" />
                    </el-select>
                    <div class="form-tip">
                        选择VAD推理引擎类型
                    </div>
                </el-form-item>

                <el-form-item label="设备类型">
                    <el-select v-model="config.device" style="width: 200px;">
                        <el-option label="自动选择" value="auto" />
                        <el-option label="CPU" value="cpu" />
                        <el-option label="GPU" value="cuda" />
                    </el-select>
                    <div class="form-tip">
                        选择VAD推理设备
                    </div>
                </el-form-item>
            </el-form>

            <!-- 预设配置 -->
            <el-divider content-position="left">快速配置</el-divider>
            <div class="preset-configs">
                <el-button @click="applyPreset('high_accuracy')" type="primary" size="small">
                    高精度模式
                </el-button>
                <el-button @click="applyPreset('fast_mode')" type="success" size="small">
                    快速模式
                </el-button>
                <el-button @click="applyPreset('sensitive')" type="warning" size="small">
                    敏感模式
                </el-button>
                <el-button @click="resetToDefault" type="info" size="small">
                    恢复默认
                </el-button>
            </div>
        </div>

        <template #footer>
            <div class="dialog-footer">
                <el-button @click="handleClose">取消</el-button>
                <el-button type="primary" @click="handleSave" :loading="saving">
                    保存配置
                </el-button>
            </div>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, watch, reactive } from 'vue'
import { ElMessage } from 'element-plus'

// Props
const props = defineProps({
    modelValue: {
        type: Boolean,
        default: false
    },
    vadConfig: {
        type: Object,
        default: () => ({})
    }
})

// Emits
const emit = defineEmits(['update:modelValue', 'config-updated'])

// Data
const visible = ref(props.modelValue)
const saving = ref(false)

// 默认配置
const defaultConfig = {
    enabled: true,
    engine: "silero",
    model_type: "silero_vad",
    device: "auto",
    threshold: 0.5,
    min_speech_duration_ms: 250,
    max_speech_duration_s: 30.0,
    min_silence_duration_ms: 100,
    speech_pad_ms: 30,
    pre_process: true,
    return_segments: false
}

// 配置数据
const config = reactive({ ...defaultConfig, ...props.vadConfig })

// 预设配置
const presets = {
    high_accuracy: {
        threshold: 0.7,
        min_speech_duration_ms: 300,
        max_speech_duration_s: 30.0,
        min_silence_duration_ms: 200,
        speech_pad_ms: 50,
        pre_process: true,
        return_segments: true
    },
    fast_mode: {
        threshold: 0.4,
        min_speech_duration_ms: 150,
        max_speech_duration_s: 60.0,
        min_silence_duration_ms: 50,
        speech_pad_ms: 20,
        pre_process: true,
        return_segments: false
    },
    sensitive: {
        threshold: 0.3,
        min_speech_duration_ms: 100,
        max_speech_duration_s: 20.0,
        min_silence_duration_ms: 100,
        speech_pad_ms: 40,
        pre_process: true,
        return_segments: true
    }
}

// Watch
watch(() => props.modelValue, (newVal) => {
    visible.value = newVal
})

watch(visible, (newVal) => {
    emit('update:modelValue', newVal)
})

// Methods
const handleClose = () => {
    visible.value = false
}

const handleSave = async () => {
    try {
        saving.value = true

        // 这里应该调用API保存配置
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 500))

        emit('config-updated', { ...config })
        ElMessage.success('VAD配置已保存')
        visible.value = false
    } catch (error) {
        ElMessage.error('保存配置失败: ' + error.message)
    } finally {
        saving.value = false
    }
}

const applyPreset = (presetName) => {
    const preset = presets[presetName]
    if (preset) {
        Object.assign(config, preset)
        ElMessage.success(`已应用${presetName === 'high_accuracy' ? '高精度' :
            presetName === 'fast_mode' ? '快速' : '敏感'}模式配置`)
    }
}

const resetToDefault = () => {
    Object.assign(config, defaultConfig)
    ElMessage.info('已恢复默认配置')
}
</script>

<style scoped>
.vad-config {
    max-height: 600px;
    overflow-y: auto;
}

.form-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
    line-height: 1.4;
}

.preset-configs {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.dialog-footer {
    text-align: right;
}

:deep(.el-form-item__label) {
    font-weight: 500;
}

:deep(.el-slider__input) {
    width: 100px;
}
</style>