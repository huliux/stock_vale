import { fetchEventSource } from '@microsoft/fetch-event-source';

/**
 * 研究配置接口
 */
export interface ResearchConfig {
  query: string;
  provider: string;
  thinkingModel: string;
  taskModel: string;
  searchProvider: string;
  language?: string;
  maxResult?: number;
  enableCitationImage?: boolean;
  enableReferences?: boolean;
}

/**
 * 进度事件类型
 */
export type StepType = 'report-plan' | 'serp-query' | 'task-list' | 'search-task' | 'final-report';
export type StatusType = 'start' | 'end';

/**
 * 进度事件接口
 */
export interface ProgressEvent {
  step: StepType;
  status: StatusType;
  name?: string;
  data?: any;
}

/**
 * 消息事件接口
 */
export interface MessageEvent {
  type: 'text';
  text: string;
}

/**
 * 回调函数接口
 */
export interface ResearchCallbacks {
  onMessage?: (text: string) => void;
  onProgress?: (progress: ProgressEvent) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
}

/**
 * Deep Research 服务客户端
 */
export class DeepResearchService {
  private baseUrl: string;
  private accessToken: string;

  /**
   * 构造函数
   * @param baseUrl Deep Research 服务的基础 URL
   * @param accessToken 访问令牌
   */
  constructor(baseUrl: string, accessToken: string) {
    this.baseUrl = baseUrl;
    this.accessToken = accessToken;
  }

  /**
   * 开始研究
   * @param config 研究配置
   * @param callbacks 回调函数
   * @returns 取消函数
   */
  async startResearch(config: ResearchConfig, callbacks: ResearchCallbacks) {
    const ctrl = new AbortController();

    try {
      // 使用代理URL避免CORS问题
      // 在开发环境中，我们使用Vite的代理功能
      // 在生产环境中，我们可以使用环境变量中配置的URL
      const apiUrl = '/api/sse'; // 使用相对路径，会被Vite代理到目标服务器

      console.log('Starting fetchEventSource to:', apiUrl);
      console.log('Request config:', JSON.stringify(config, null, 2));

      await fetchEventSource(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.accessToken}`,
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(config),
        signal: ctrl.signal,
        onmessage(msg) {
          try {
            // 打印接收到的消息，但不包括可能很长的数据内容
            console.log('Received message event:', msg.event);

            // 根据事件类型处理消息
            if (msg.event === 'progress') {
              try {
                const progressData = JSON.parse(msg.data);
                callbacks.onProgress?.(progressData as ProgressEvent);
              } catch (e) {
                console.error('Failed to parse progress data:', e);
              }
            }
            else if (msg.event === 'error') {
              try {
                const errorData = JSON.parse(msg.data);
                callbacks.onError?.(errorData.message || msg.data);
              } catch (e) {
                callbacks.onError?.(msg.data);
              }
            }
            else if (msg.event === 'message') {
              try {
                // 检查并清理可能的格式问题
                let cleanData = msg.data;
                if (typeof cleanData === 'string' && cleanData.includes('"})}')) {
                  cleanData = cleanData.replace('"})}', '"}');
                  console.log('Cleaned malformed JSON data');
                }

                const messageData = JSON.parse(cleanData);
                if (messageData.type === 'text' && messageData.text) {
                  callbacks.onMessage?.(messageData.text);
                } else {
                  callbacks.onMessage?.(msg.data);
                }
              } catch (e) {
                console.error('Failed to parse message data:', e);

                // 尝试提取文本内容
                if (typeof msg.data === 'string') {
                  const textMatch = msg.data.match(/"text":"([^"]*)"/);
                  if (textMatch && textMatch[1]) {
                    console.log('Extracted text from malformed JSON:', textMatch[1]);
                    callbacks.onMessage?.(textMatch[1]);
                  } else {
                    callbacks.onMessage?.(msg.data);
                  }
                } else {
                  callbacks.onMessage?.(msg.data);
                }
              }
            }
            else if (msg.event === 'infor') {
              console.log('Info event received:', msg.data);
            }
            else if (msg.event === 'reasoning') {
              try {
                const reasoningData = JSON.parse(msg.data);
                if (reasoningData.type === 'text' && reasoningData.text) {
                  // 可以选择是否将推理过程也显示给用户
                  // callbacks.onMessage?.(`[推理过程] ${reasoningData.text}`);
                  console.log('Reasoning process received');
                }
              } catch (e) {
                console.error('Failed to parse reasoning data:', e);
              }
            }
            else {
              // 处理没有明确事件类型的消息或默认消息
              console.log('Received unknown event type:', msg.event);

              // 尝试解析数据
              if (msg.data && typeof msg.data === 'string') {
                if (msg.data.startsWith('{')) {
                  try {
                    // 检查并清理可能的格式问题
                    let cleanData = msg.data;
                    if (cleanData.includes('"})}')) {
                      cleanData = cleanData.replace('"})}', '"}');
                      console.log('Cleaned malformed JSON data in unknown event');
                    }

                    const data = JSON.parse(cleanData);
                    if (data.type === 'text' && data.text) {
                      callbacks.onMessage?.(data.text);
                    } else {
                      callbacks.onMessage?.(msg.data);
                    }
                  } catch (e) {
                    console.error('Failed to parse JSON data:', e);

                    // 尝试提取文本内容
                    const textMatch = msg.data.match(/"text":"([^"]*)"/);
                    if (textMatch && textMatch[1]) {
                      console.log('Extracted text from malformed JSON in unknown event:', textMatch[1]);
                      callbacks.onMessage?.(textMatch[1]);
                    } else {
                      callbacks.onMessage?.(msg.data);
                    }
                  }
                } else {
                  callbacks.onMessage?.(msg.data);
                }
              }
            }
          } catch (err) {
            console.error('Failed to process message:', err);
            // 尝试直接使用消息数据
            if (msg && msg.data) {
              callbacks.onMessage?.(msg.data);
            }
          }
        },
        onclose() {
          console.log('Connection closed');
          callbacks.onComplete?.();
        },
        onerror(err) {
          console.error('Error in fetchEventSource:', err);
          callbacks.onError?.(err.message);
        },
        // 添加更多的错误处理
        async onopen(response) {
          console.log('Connection opened:', response.status);
          if (response.ok) {
            console.log('Response is OK');
            return; // 连接成功
          }
          if (response.status >= 400 && response.status < 500 && response.status !== 429) {
            console.error('Client error:', response.status);
            throw new Error(`Client error: ${response.status}`);
          }
          console.log('Proceeding with response:', response.status);
        },
      });
    } catch (err) {
      console.error('Error in startResearch:', err);
      const errorMessage = err instanceof Error ? err.message : String(err);
      console.error('Error message:', errorMessage);
      callbacks.onError?.(errorMessage);
    }

    return () => ctrl.abort(); // 返回取消函数
  }
}

/**
 * 创建 Deep Research 服务实例
 * 注意：baseUrl 不再需要，因为我们使用代理
 */
export const deepResearchService = new DeepResearchService(
  '', // 使用空字符串，因为我们使用代理
  import.meta.env.VITE_DEEP_RESEARCH_ACCESS_TOKEN || '123456'
);
