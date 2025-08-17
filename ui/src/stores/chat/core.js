import axios from "axios";

// 默认配置作为后备
const DEFAULT_CONFIG = {
  baseURL: "https://api.openai.com/v1",
  apiKey: "your-openai-api-key",
  model: "gpt-3.5-turbo",
  defaultParams: {
    temperature: 0.7,
    max_tokens: 1000,
    top_p: 1,
    frequency_penalty: 0,
    presence_penalty: 0,
  },
  timeout: 30000,
};

const DEFAULT_PERSONAS = [
  {
    id: "assistant",
    name: "智能助手",
    description: "友善、专业的AI助手",
    prompt:
      "你是一个友善、专业且富有知识的AI助手。请用清晰、有帮助的方式回答用户的问题。保持礼貌和耐心，如果不确定答案，请诚实说明。",
  },
];

// 全局配置变量
let AI_CONFIG = { ...DEFAULT_CONFIG };
let openaiClient = null;

// 初始化配置
const initializeConfig = async () => {
  try {
    // 尝试从public目录加载配置
    const response = await fetch("/ai-config.json");
    if (response.ok) {
      const config = await response.json();
      AI_CONFIG = { ...DEFAULT_CONFIG, ...config.AI_CONFIG };
      console.log("AI配置加载成功:", AI_CONFIG.baseURL);
    } else {
      console.warn("未找到ai-config.json，使用默认配置");
    }
  } catch (error) {
    console.warn("加载AI配置失败，使用默认配置:", error);
  }

  // 创建OpenAI API客户端
  openaiClient = axios.create({
    baseURL: AI_CONFIG.baseURL,
    timeout: AI_CONFIG.timeout,
    headers: {
      Authorization: `Bearer ${AI_CONFIG.apiKey}`,
      "Content-Type": "application/json",
    },
  });
};

export { 
  DEFAULT_CONFIG, 
  DEFAULT_PERSONAS, 
  AI_CONFIG, 
  openaiClient, 
  initializeConfig 
}; 