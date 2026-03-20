// AI 功能由后端环境变量 + 用户权限共同控制
// 开发环境默认开启，生产环境根据用户角色判断

const isDev = import.meta.env.DEV
const AI_ENABLED = isDev || import.meta.env.VITE_AI_ENABLED === 'true'

const DEFAULT_CONFIG = {
  provider: 'openai',
  apiKey: import.meta.env.VITE_API_KEY || '',
  baseUrl: import.meta.env.VITE_BASE_URL || 'https://ark.cn-beijing.volces.com/api/v3',
  model: import.meta.env.VITE_MODEL || 'deepseek-v3-0324',
}

export const isAIEnabled = () => {
  // 允许外部覆盖
  if (typeof window.__AI_ENABLED_OVERRIDE__ !== 'undefined') {
    return window.__AI_ENABLED_OVERRIDE__
  }
  return AI_ENABLED
}

// 设置 AI 功能开关（供外部调用）
export const setAIEnabled = (enabled) => {
  window.__AI_ENABLED_OVERRIDE__ = enabled
}

// 先定义getConfig
export const getConfig = () => {
  const saved = localStorage.getItem('mediapilot-api-config');
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch (e) {
      return DEFAULT_CONFIG;
    }
  }
  return DEFAULT_CONFIG;
};

// 然后初始化时从localStorage加载配置
let currentConfig = getConfig();

export const saveConfig = (config) => {
  localStorage.setItem('mediapilot-api-config', JSON.stringify(config));
};

export const updateConfig = (newConfig) => {
  currentConfig = { ...currentConfig, ...newConfig };
  saveConfig(currentConfig);
};

const createClient = () => {
  const apiKey = currentConfig.apiKey;
  const baseUrl = currentConfig.baseUrl;

  return {
    async chat(messages, options = {}) {
      const response = await fetch(`${baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model: currentConfig.model,
          messages,
          stream: options.stream || false,
          max_tokens: options.maxTokens || 1500,
          temperature: options.temperature || 0.6,
        }),
      });

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
      }

      return response.json();
    },

    async *chatStream(messages, options = {}) {
      const response = await fetch(`${baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          model: currentConfig.model,
          messages,
          stream: true,
          max_tokens: options.maxTokens || 1500,
          temperature: options.temperature || 0.6,
          // 添加推理相关参数加速
          extra_body: {
            max_completion_tokens: options.maxTokens || 1500,
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;

            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices?.[0]?.delta?.content;
              if (content) {
                yield content;
              }
            } catch (e) {
            }
          }
        }
      }
    },
  };
};

export const aiService = {
  async chat(messages) {
    const client = createClient();
    const result = await client.chat(messages);
    return result.choices[0].message.content;
  },

  async *chatStream(messages) {
    const client = createClient();
    for await (const chunk of client.chatStream(messages)) {
      yield chunk;
    }
  },

  async generateScript(topic, options = {}) {
    const prompt = `你是一个专业的短视频脚本创作专家。请为以下主题创作一个吸引人的短视频脚本：

主题：${topic}

要求：
1. 标题要吸引人，有网感
2. 开头3秒内抓住用户注意力
3. 内容有趣、实用、有共鸣
4. 结尾引导互动（点赞、评论、关注）
5. 语言口语化，接地气

请输出以下内容：
- 标题
- 钩子（开头3秒）
- 分镜头脚本（5-8个镜头）
- 话题标签

请直接输出，不要多余说明。`;

    const messages = [
      { role: 'system', content: '你是一个专业的短视频脚本创作专家。' },
      { role: 'user', content: prompt }
    ];

    const client = createClient();
    const result = await client.chat(messages);
    return result.choices[0].message.content;
  },
};

export { currentConfig };