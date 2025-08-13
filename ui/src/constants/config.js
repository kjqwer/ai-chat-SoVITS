// 语言选项 (V2版本)
export const LANGUAGE_OPTIONS = [
  { label: '中文', value: '中文' },
  { label: '英文', value: '英文' },
  { label: '日文', value: '日文' },
  { label: '粤语', value: '粤语' },
  { label: '韩文', value: '韩文' },
  { label: '中英混合', value: '中英混合' },
  { label: '日英混合', value: '日英混合' },
  { label: '粤英混合', value: '粤英混合' },
  { label: '韩英混合', value: '韩英混合' },
  { label: '多语种混合', value: '多语种混合' },
  { label: '多语种混合(粤语)', value: '多语种混合(粤语)' }
]

// 文本分割方法选项
export const TEXT_SPLIT_OPTIONS = [
  { label: '不切', value: '不切' },
  { label: '凑四句一切', value: '凑四句一切' },
  { label: '凑50字一切', value: '凑50字一切' },
  { label: '按中文句号。切', value: '按中文句号。切' },
  { label: '按英文句号.切', value: '按英文句号.切' },
  { label: '按标点符号切', value: '按标点符号切' }
]

// 采样步数选项
export const SAMPLE_STEPS_OPTIONS = [
  { label: '4', value: 4 },
  { label: '8', value: 8 },
  { label: '16', value: 16 },
  { label: '32', value: 32 },
  { label: '64', value: 64 },
  { label: '128', value: 128 }
]

// 推理配置参数范围
export const CONFIG_RANGES = {
  top_k: { min: 1, max: 100, step: 1 },
  top_p: { min: 0, max: 1, step: 0.05 },
  temperature: { min: 0, max: 1, step: 0.05 },
  batch_size: { min: 1, max: 200, step: 1 },
  speed_factor: { min: 0.6, max: 1.65, step: 0.05 },
  fragment_interval: { min: 0.01, max: 1, step: 0.01 },
  repetition_penalty: { min: 0, max: 2, step: 0.05 }
}

// 推理配置字段标签
export const CONFIG_LABELS = {
  text_lang: '文本语种',
  prompt_lang: '参考音频语种',
  top_k: 'Top K',
  top_p: 'Top P',
  temperature: '温度',
  text_split_method: '文本分割方法',
  batch_size: '批处理大小',
  speed_factor: '语速',
  ref_text_free: '无参考文本模式',
  split_bucket: '分桶处理',
  fragment_interval: '分段间隔(秒)',
  parallel_infer: '并行推理',
  repetition_penalty: '重复惩罚',
  sample_steps: '采样步数',
  super_sampling: '超级采样'
}

// 推理配置字段描述
export const CONFIG_DESCRIPTIONS = {
  text_lang: '要合成的文本的语种',
  prompt_lang: '参考音频的语种',
  top_k: '控制词汇选择的多样性，值越小越保守',
  top_p: '控制生成的随机性，值越小越确定',
  temperature: '控制输出的随机性，值越小越稳定',
  text_split_method: '长文本的分割方式',
  batch_size: '批处理大小，影响推理速度和内存占用',
  speed_factor: '语速调节，1.0为正常语速',
  ref_text_free: '是否使用无参考文本模式',
  split_bucket: '是否启用分桶处理优化',
  fragment_interval: '音频片段间的间隔时间',
  parallel_infer: '是否启用并行推理加速',
  repetition_penalty: '重复惩罚系数，减少重复内容',
  sample_steps: '采样步数，仅对V3/V4模型生效',
  super_sampling: '是否启用超级采样提升质量'
} 