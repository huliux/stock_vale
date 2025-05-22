<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { deepResearchService, type ProgressEvent } from '@/services/deepResearchService';
import { renderMarkdown } from '@/utils/markdown';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'vue-sonner';

// 检查是否为开发环境
const isDev = import.meta.env.DEV;

const props = defineProps({
  stockCode: {
    type: String,
    default: ''
  },
  stockName: {
    type: String,
    default: ''
  }
});

// toast 已直接从 vue-sonner 导入
const report = ref('');
const isLoading = ref(false);
const progress = ref<ProgressEvent | null>(null);
const cancelResearch = ref<(() => void) | null>(null);

// 根据股票代码和名称自动生成研究主题
const researchTopic = computed(() => {
  if (!props.stockCode) return '';

  return props.stockName ?
    `对${props.stockName}(${props.stockCode})的深度财务分析和投资价值研究` :
    `对股票${props.stockCode}的深度财务分析和投资价值研究`;
});

// 监听股票代码变化，重置研究状态
watch(() => props.stockCode, () => {
  if (!isLoading.value) {
    report.value = '';
  }
});

// 开始研究
const startResearch = async () => {
  if (!props.stockCode) {
    toast.error('请先选择股票');
    return;
  }

  report.value = '';
  isLoading.value = true;

  try {
    console.log('开始研究，主题:', researchTopic.value);

    // 添加调试信息
    if (isDev) {
      report.value = '正在连接到深度研究服务...\n\n';
    }

    cancelResearch.value = await deepResearchService.startResearch(
      {
        query: researchTopic.value,
        provider: 'deepseek', // 使用 deepseek 作为 AI 提供商
        thinkingModel: 'deepseek-chat', // 思考模型
        taskModel: 'deepseek-chat', // 任务模型
        searchProvider: 'model', // 使用模型自带的搜索功能
        language: 'zh-CN', // 使用中文
        maxResult: 5, // 最大搜索结果数
        enableCitationImage: true, // 启用引用图片
        enableReferences: true // 启用引用链接
      },
      {
        onMessage: (text) => {
          console.log('收到消息:', text?.substring(0, 50) + (text && text.length > 50 ? '...' : ''));

          // 处理文本，避免重复添加相同的内容
          if (text && typeof text === 'string') {
            // 检查是否是JSON字符串
            if (text.trim().startsWith('{') && text.includes('type')) {
              try {
                // 修复格式问题：移除可能的额外字符
                let cleanedText = text;
                // 如果JSON后面有额外的字符，尝试清理
                if (text.includes('"})}')) {
                  cleanedText = text.replace('"})}', '"}');
                }

                const jsonData = JSON.parse(cleanedText);
                if (jsonData.type === 'text' && jsonData.text) {
                  // 如果是JSON格式的文本消息，只添加text字段
                  report.value += jsonData.text;
                } else {
                  // 否则添加整个JSON字符串
                  report.value += text;
                }
              } catch (e) {
                // 如果解析失败，尝试提取有用的部分
                console.warn('JSON解析失败，尝试提取文本:', e);

                // 尝试提取 "text":"..." 部分
                const textMatch = text.match(/"text":"([^"]*)"/);
                if (textMatch && textMatch[1]) {
                  report.value += textMatch[1];
                } else {
                  // 如果无法提取，直接添加原始文本
                  report.value += text;
                }
              }
            } else {
              // 不是JSON格式，直接添加文本
              report.value += text;
            }
          }
        },
        onProgress: (progressEvent) => {
          console.log('进度更新:', progressEvent);
          progress.value = progressEvent;
        },
        onError: (errorMessage) => {
          console.error('研究过程出错:', errorMessage);
          toast.error(`研究过程出错: ${errorMessage}`);
          isLoading.value = false;
        },
        onComplete: () => {
          console.log('研究完成');
          isLoading.value = false;
          progress.value = null;
          toast.success('研究完成');
        }
      }
    );

    console.log('研究请求已发送，等待结果...');
  } catch (error) {
    console.error('启动研究失败:', error);
    const errorMessage = error instanceof Error ? error.message : String(error);
    toast.error(`启动研究失败: ${errorMessage}`);
    isLoading.value = false;
  }
};

// 取消研究
const handleCancel = () => {
  if (cancelResearch.value) {
    cancelResearch.value();
    cancelResearch.value = null;
    isLoading.value = false;
    toast.info('已取消研究');
  }
};

// 获取进度步骤的中文名称
const getStepName = (step: string): string => {
  const stepMap: Record<string, string> = {
    'report-plan': '研究计划',
    'serp-query': '搜索查询',
    'task-list': '任务列表',
    'search-task': '搜索任务',
    'final-report': '最终报告'
  };
  return stepMap[step] || step;
};

// 获取状态的中文名称
const getStatusName = (status: string): string => {
  const statusMap: Record<string, string> = {
    'start': '开始',
    'end': '完成'
  };
  return statusMap[status] || status;
};
</script>

<template>
  <Card class="w-full">
    <CardHeader>
      <CardTitle>AI深度研究</CardTitle>
    </CardHeader>
    <CardContent>
      <div v-if="!isLoading && !report" class="flex flex-col gap-4">
        <p>点击下方按钮开始对{{ stockName || '所选股票' }}进行AI深度研究</p>
        <Button @click="startResearch" :disabled="!stockCode">开始研究</Button>
      </div>

      <div v-if="isLoading" class="flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="font-medium">正在研究: {{ progress ? getStepName(progress.step) : '准备中' }}</p>
            <p class="text-sm text-muted-foreground">{{ progress?.status ? getStatusName(progress.status) : '' }} {{
              progress?.name || '' }}</p>
          </div>
          <Button variant="outline" @click="handleCancel">取消</Button>
        </div>
        <Skeleton v-if="!report" class="h-[200px] w-full" />
      </div>

      <div v-if="report" class="mt-4">
        <Separator class="my-4" />
        <div class="prose prose-blue dark:prose-invert max-w-none">
          <!-- 使用v-html渲染Markdown -->
          <div v-html="renderMarkdown(report)"></div>
        </div>
      </div>

      <!-- 调试信息 -->
      <div v-if="isLoading && isDev" class="mt-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-md">
        <h3 class="text-sm font-medium mb-2">调试信息</h3>
        <pre class="text-xs overflow-auto max-h-40">{{ progress }}</pre>
      </div>
    </CardContent>
  </Card>
</template>

<style scoped>
/* 添加必要的样式 */
:deep(.prose) {
  max-width: 100%;
}

:deep(.prose pre) {
  background-color: #f3f4f6;
  border-radius: 0.375rem;
  padding: 1rem;
  overflow-x: auto;
}

:deep(.prose code) {
  color: #ef4444;
  background-color: rgba(239, 68, 68, 0.1);
  padding: 0.2em 0.4em;
  border-radius: 0.25rem;
}

:deep(.prose blockquote) {
  border-left: 4px solid #e5e7eb;
  padding-left: 1rem;
  font-style: italic;
}

:deep(.prose table) {
  width: 100%;
  border-collapse: collapse;
}

:deep(.prose th, .prose td) {
  padding: 0.5rem;
  border: 1px solid #e5e7eb;
}

:deep(.prose th) {
  background-color: #f9fafb;
}
</style>
