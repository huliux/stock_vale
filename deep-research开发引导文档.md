Copilot said: 让我帮你分析这个仓库的主要业务逻辑和功能： 这是一个名为 Deep Research 的项目，它是一个基于多种 LLM（大语言模型）的深度研究工具。其主要功能和运行逻辑如下： ### 1. 核心功能： 1.
让我帮你分析这个仓库的主要业务逻辑和功能：

这是一个名为 Deep Research 的项目，它是一个基于多种 LLM（大语言模型）的深度研究工具。其主要功能和运行逻辑如下：

1. 核心功能：
深度研究报告生成

能在约2分钟内生成全面的研究报告
支持多语言（英语、简体中文、西班牙语）
可以根据需要调整阅读级别和文章长度
多模型支持

支持多种主流大语言模型：
Gemini
OpenAI
Anthropic
Deepseek
Grok
Mistral
Azure OpenAI
其他 OpenAI 兼容的 LLMs
Web 搜索集成

支持多种搜索引擎：
Searxng
Tavily
Firecrawl
Exa
Bocha
知识库功能

支持上传和处理多种格式文件（文本、Office、PDF等）
可生成本地知识库
支持知识图谱生成
2. 具体运行逻辑：
项目的运行流程分为四个主要阶段：

研究主题阶段
Mermaid
flowchart TB
    A[输入研究主题] --> B[可选: 使用本地研究资源]
    B --> C[开始思考/重新思考]
提出想法阶段
Mermaid
flowchart TB
    A[系统提问] --> B[系统输出研究计划]
    B --> C[系统生成SERP查询]
信息收集阶段
Mermaid
flowchart TB
    A[初始研究] --> B[基于SERP查询检索本地资源]
    A --> C[基于SERP查询收集网络信息]
    B --> D[深入研究]
    C --> D
    D --> E{需要更深入研究?}
    E -->|是| D
    E -->|否| F[完成收集]
报告生成阶段
汇总所有研究材料
生成综合性的 Markdown 报告
支持报告重新生成
3. 技术实现：
API 支持

提供 SSE（Server-Sent Events）API
支持 MCP（Model Context Protocol）服务器
支持本地和服务器端 API 调用
部署选项

支持多平台快速部署（Vercel、Cloudflare 等）
提供 Docker 部署方式
支持静态页面部署
数据隐私

所有研究数据和生成的报告都存储在本地
不收集或传输研究数据到外部服务器
4. 扩展功能：
编辑功能

支持 WYSIWYM 和 Markdown 两种编辑模式
可以在项目的任何阶段调整研究内容
支持从特定阶段重新开始研究
多用途集成

可作为深度研究服务（SaaS）通过 SSE API 使用
可通过 MCP 服务在其他 AI 服务中使用
支持 PWA（渐进式网页应用）
支持多密钥负载以提高 API 响应效率
要了解更具体的某个功能或技术实现细节，我可以为你深入分析相关代码。你有什么特别想了解的方面吗？

You said: 介绍项目目录以及各文件夹、文件的职责作用
介绍项目目录以及各文件夹、文件的职责作用
13 referencesCopilot said: 通过分析源代码，我来为你介绍这个项目的目录结构和主要文件的职责： ### 1. 根目录结构： ``` - src/
通过分析源代码，我来为你介绍这个项目的目录结构和主要文件的职责：

1. 根目录结构：
Code
- src/                  # 源代码目录
- public/              # 静态资源目录
- docs/                # 文档目录
- next.config.ts       # Next.js 配置文件
- package.json         # 项目依赖配置
- Dockerfile          # Docker 构建配置
2. src 目录主要结构：
Code
src/
├── app/               # 应用程序主目录 (Next.js App Router)
│   ├── api/          # API 路由处理
│   ├── page.tsx      # 主页面组件
│   └── manifest.json # PWA 配置文件
│
├── components/        # 组件目录
│   ├── ui/           # UI 基础组件
│   ├── Internal/     # 内部组件
│   ├── Research/     # 研究相关组件
│   └── Knowledge/    # 知识库相关组件
│
├── libs/             # 库文件目录
│   └── mcp-server/   # MCP 服务器实现
│
├── hooks/            # React Hooks
│
├── store/            # 状态管理
│
└── utils/            # 工具函数
3. 主要文件职责：
应用核心文件：
src/app/page.tsx

TypeScript
// 主页面组件，集成了以下功能模块：
- Header         // 页面头部
- Topic          // 研究主题
- Feedback       // 反馈组件
- SearchResult   // 搜索结果
- FinalReport    // 最终报告
- History        // 历史记录
- Knowledge      // 知识库
- Setting        // 设置面板
src/app/api/

mcp/[...slug]/route.ts - MCP 服务器 API 路由处理
utils.ts - API 通用工具和配置
组件文件：
UI 组件 (src/components/ui/)

TypeScript
- table.tsx     // 表格组件
- label.tsx     // 标签组件
// ... 其他基础 UI 组件
Knowledge 组件 (src/components/Knowledge/)

TypeScript
- Content.tsx   // 知识内容编辑器组件
工具和功能文件：
src/hooks/useAccurateTimer.ts

TypeScript
// 提供精确的计时器功能
- start()       // 开始计时
- stop()        // 停止计时
- formattedTime // 格式化时间显示
src/libs/mcp-server/shared/transport.ts

TypeScript
// MCP 服务器传输层实现
- Transport 接口定义
- 消息处理机制
src/utils/text.ts

TypeScript
// 文本处理工具
- splitText()   // 文本分块处理
4. 配置文件：
next.config.ts

TypeScript
// Next.js 配置
- API 代理设置
- 环境变量配置
- 构建选项
manifest.json

JSON
// PWA 配置
- 应用信息
- 图标配置
- 显示设置
注意：这只是基于可见的代码文件分析，可能还有其他文件和目录未在搜索结果中显示。要查看完整的项目结构，你可以访问 GitHub 仓库。

每个目录和文件都遵循了清晰的职责分离原则：

app/ 处理路由和页面
components/ 包含所有 React 组件
libs/ 包含可复用的库代码
hooks/ 存放自定义 React Hooks
utils/ 提供通用工具函数
store/ 管理应用状态
项目使用了现代的 Next.js 框架，采用了 TypeScript 进行开发，并支持 PWA 特性，文件组织结构清晰，便于维护和扩展。

You said: 该项目的MVP是什么，实现路径是什么，请详细拆解
该项目的MVP是什么，实现路径是什么，请详细拆解
20 referencesCopilot said: 基于代码分析，让我为你详细拆解这个项目的 MVP（最小可行产品）和实现路径： ### MVP 核心功能定义： 1. **基础研究功能**
基于代码分析，让我为你详细拆解这个项目的 MVP（最小可行产品）和实现路径：

MVP 核心功能定义：
基础研究功能

输入研究主题
生成研究计划
执行网络搜索
生成综合报告
必要的 AI 集成

支持至少一个 LLM（如 Gemini）
支持至少一个搜索引擎
实现基本的思考和任务模型
最小用户界面

研究主题输入
研究过程展示
最终报告显示
基本设置选项
实现路径：
1. 基础架构搭建 (Phase 1)
项目初始化

TypeScript
// 使用 Next.js 创建项目
- 设置 TypeScript 配置
- 配置基础开发环境
核心类实现

TypeScript
// src/utils/deep-research/index.ts
class DeepResearch {
  async writeReportPlan(query: string)
  async generateSERPQuery(reportPlan: string)
  async runSearchTask(tasks: DeepResearchSearchTask[])
  async writeFinalReport(reportPlan: string, tasks: SearchResult[])
}
2. AI 集成实现 (Phase 2)
LLM 接入

TypeScript
// 实现 AI Provider 接口
interface AIProvider {
  baseURL: string;
  apiKey: string;
  provider: string;
  thinkingModel: string;
  taskModel: string;
}
搜索引擎集成

TypeScript
// 实现搜索提供者接口
interface SearchProvider {
  baseURL: string;
  apiKey: string;
  provider: string;
  maxResult: number;
}
3. 用户界面开发 (Phase 3)
主要组件开发

TypeScript
// src/components/Research/
- Topic.tsx      // 研究主题输入
- Feedback.tsx   // 反馈显示
- SearchResult.tsx // 搜索结果
- FinalReport.tsx  // 最终报告
基础状态管理

TypeScript
// src/store/
- global.ts     // 全局状态
- setting.ts    // 设置状态
4. API 实现 (Phase 4)
SSE API

TypeScript
// src/app/api/sse/
interface SSEConfig {
  query: string;
  provider: string;
  thinkingModel: string;
  taskModel: string;
  searchProvider: string;
}
事件处理

TypeScript
// 实现事件类型
type EventTypes = 
  | "info"
  | "message"
  | "reasoning"
  | "progress"
  | "error"
5. 核心工作流实现 (Phase 5)
Mermaid
flowchart TB
    A[输入研究主题] --> B[生成研究计划]
    B --> C[生成搜索查询]
    C --> D[执行搜索任务]
    D --> E[生成最终报告]

    subgraph 搜索流程
        D --> D1[本地资源搜索]
        D --> D2[网络搜索]
        D1 --> D3[结果整合]
        D2 --> D3
    end
拓展功能规划：
第一阶段拓展

研究历史记录
报告编辑功能
多 LLM 支持
第二阶段拓展

文件上传
本地知识库
SSE API & MCP 服务
第三阶段拓展

知识图谱生成
多语言支持
PWA 支持
关键技术实现：
思考模型实现

TypeScript
// 思考模型流程
thinkingProcess: {
  input -> 问题分析 -> 计划生成 -> 搜索查询
}
任务模型实现

TypeScript
// 任务模型流程
taskProcess: {
  搜索结果 -> 信息提取 -> 内容整合 -> 报告生成
}
实时反馈机制

TypeScript
// 使用 SSE 实现实时进度反馈
onMessage: (event, data) => {
  if (event === "progress") {
    console.log(`[${data.step}]: ${data.status}`);
  }
}
部署路线：
快速部署方案

Vercel 一键部署
Cloudflare Pages 部署
Docker 容器化部署
环境配置

bash
# 基础配置
- AI Provider API 配置
- 搜索引擎 API 配置
- 安全访问密码设置
这个实现路径遵循渐进式开发原则，从核心功能开始，逐步添加更多功能，确保系统的可用性和稳定性。每个阶段都有明确的目标和可测试的输出，便于开发和质量控制。

You said: 我想在其它项目复刻基础研究功能和用户界面，通过SSE API来使用本仓库服务，应该怎么做
我想在其它项目复刻基础研究功能和用户界面，通过SSE API来使用本仓库服务，应该怎么做
1 referenceCopilot said: 让我帮你规划如何在其他项目中复刻基础研究功能并通过 SSE API 使用本仓库服务。我会分成几个主要部分来说明： ### 1. 基础架构搭建 ```typescript // 1.
让我帮你规划如何在其他项目中复刻基础研究功能并通过 SSE API 使用本仓库服务。我会分成几个主要部分来说明：

1. 基础架构搭建
TypeScript
// 1. 创建基本项目结构
src/
  ├── components/     // UI 组件
  │   ├── Research/
  │   │   ├── Topic.tsx       // 研究主题输入
  │   │   ├── Progress.tsx    // 进度显示
  │   │   ├── Report.tsx      // 报告显示
  │   │   └── index.tsx       // 研究组件整合
  │   └── common/            // 通用组件
  ├── services/      // API 服务
  │   └── research.ts         // 研究服务接口
  ├── types/         // 类型定义
  │   └── research.ts         // 研究相关类型
  └── utils/         // 工具函数
      └── sse.ts             // SSE 工具
2. 类型定义
TypeScript
// src/types/research.ts

// 配置接口
interface ResearchConfig {
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

// 事件类型
type EventType = 'infor' | 'message' | 'reasoning' | 'progress' | 'error';

// 进度事件
interface ProgressEvent {
  step: 'report-plan' | 'serp-query' | 'task-list' | 'search-task' | 'final-report';
  status: 'start' | 'end';
  name?: string;
  data?: any;
}

// 消息事件
interface MessageEvent {
  type: 'text';
  text: string;
}
3. SSE 服务实现
TypeScript
// src/services/research.ts
import { fetchEventSource } from '@microsoft/fetch-event-source';

export class ResearchService {
  private baseUrl: string;
  private accessToken?: string;

  constructor(baseUrl: string, accessToken?: string) {
    this.baseUrl = baseUrl;
    this.accessToken = accessToken;
  }

  async startResearch(config: ResearchConfig, callbacks: {
    onMessage?: (text: string) => void;
    onProgress?: (progress: ProgressEvent) => void;
    onError?: (error: string) => void;
    onComplete?: () => void;
  }) {
    const ctrl = new AbortController();

    try {
      await fetchEventSource(`${this.baseUrl}/api/sse`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.accessToken && {
            'Authorization': `Bearer ${this.accessToken}`
          })
        },
        body: JSON.stringify(config),
        signal: ctrl.signal,
        onmessage(msg) {
          try {
            const data = JSON.parse(msg.data);
            
            switch (msg.event) {
              case 'message':
                callbacks.onMessage?.(data.text);
                break;
              case 'progress':
                callbacks.onProgress?.(data);
                break;
              case 'error':
                callbacks.onError?.(data.message);
                break;
            }
          } catch (err) {
            console.error('Failed to parse message:', err);
          }
        },
        onclose() {
          callbacks.onComplete?.();
        },
        onerror(err) {
          callbacks.onError?.(err.message);
        },
      });
    } catch (err) {
      callbacks.onError?.(err.message);
    }

    return () => ctrl.abort(); // 返回取消函数
  }
}
4. UI 组件实现
TypeScript
// src/components/Research/Topic.tsx
import { useState } from 'react';

export const Topic = ({ onSubmit }) => {
  const [query, setQuery] = useState('');
  
  return (
    <div>
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="输入研究主题..."
      />
      <button onClick={() => onSubmit(query)}>
        开始研究
      </button>
    </div>
  );
};

// src/components/Research/Progress.tsx
export const Progress = ({ step, status, name }) => {
  return (
    <div>
      <div>当前步骤: {step}</div>
      <div>状态: {status}</div>
      {name && <div>任务: {name}</div>}
    </div>
  );
};

// src/components/Research/Report.tsx
import ReactMarkdown from 'react-markdown';

export const Report = ({ content }) => {
  return (
    <div className="report">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
};
5. 主组件整合
TypeScript
// src/components/Research/index.tsx
import { useState } from 'react';
import { ResearchService } from '../../services/research';
import { Topic } from './Topic';
import { Progress } from './Progress';
import { Report } from './Report';

const researchService = new ResearchService(
  'https://your-deep-research-instance.com',
  'YOUR_ACCESS_TOKEN'
);

export const Research = () => {
  const [progress, setProgress] = useState(null);
  const [report, setReport] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (query: string) => {
    setReport('');
    setError('');
    
    await researchService.startResearch(
      {
        query,
        provider: 'google',
        thinkingModel: 'gemini-2.0-flash-thinking-exp',
        taskModel: 'gemini-2.0-flash-exp',
        searchProvider: 'model',
        language: 'zh-CN'
      },
      {
        onMessage: (text) => {
          setReport(prev => prev + text);
        },
        onProgress: (progressEvent) => {
          setProgress(progressEvent);
        },
        onError: (errorMessage) => {
          setError(errorMessage);
        },
        onComplete: () => {
          setProgress(null);
        }
      }
    );
  };

  return (
    <div className="research-container">
      <Topic onSubmit={handleSubmit} />
      {progress && <Progress {...progress} />}
      {error && <div className="error">{error}</div>}
      <Report content={report} />
    </div>
  );
};
6. 使用说明
安装依赖
bash
npm install @microsoft/fetch-event-source react-markdown
配置环境变量
env
DEEP_RESEARCH_API_URL=https://your-deep-research-instance.com
DEEP_RESEARCH_ACCESS_TOKEN=your-access-token
在项目中使用
TypeScript
import { Research } from './components/Research';

function App() {
  return (
    <div className="app">
      <h1>深度研究助手</h1>
      <Research />
    </div>
  );
}
7. 样式建议
CSS
.research-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.progress {
  margin: 20px 0;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 4px;
}

.report {
  margin-top: 20px;
  padding: 20px;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.error {
  color: red;
  padding: 10px;
  margin: 10px 0;
  background: #fff2f2;
  border-radius: 4px;
}
这个实现提供了基础的研究功能，包括：

研究主题输入
实时进度显示
Markdown 格式的报告展示
错误处理
可取消的研究过程
你可以根据需要扩展这个基础实现，添加更多功能如：

研究历史记录
报告编辑功能
主题设置
国际化支持
更详细的进度展示
自定义研究参数配置
记住要在实际部署时替换 API URL 和访问令牌，并确保你的 Deep Research 实例正确配置了 CORS 策略以允许你的前端应用访问。

You said: await researchService.startResearch(
    await researchService.startResearch(
      {
        query,
        provider: 'google',
        thinkingModel: 'gemini-2.0-flash-thinking-exp',
        taskModel: 'gemini-2.0-flash-exp',
        searchProvider: 'model',
        language: 'zh-CN'
      },
这里是什么意思，第三方项目是选择配置的意思吗，实际配置是在当前仓库项目中配好吗。

DEEP_RESEARCH_API_URL=https://your-deep-research-instance.com
DEEP_RESEARCH_ACCESS_TOKEN=your-access-token
访问令牌在哪里配置，顺序步骤是什么
Copilot said: 让我帮你理解这些配置参数和设置步骤。 ### 1. 配置参数解析 ```typescript { query,
让我帮你理解这些配置参数和设置步骤。

1. 配置参数解析
TypeScript
{
  query,                                  // 用户输入的研究主题
  provider: 'google',                     // 使用的 AI 提供商
  thinkingModel: 'gemini-2.0-flash-thinking-exp', // 思考模型
  taskModel: 'gemini-2.0-flash-exp',     // 任务模型
  searchProvider: 'model',                // 搜索提供商
  language: 'zh-CN'                       // 输出语言
}
这些参数需要与 Deep Research 服务端的配置相匹配。也就是说：

服务端（Deep Research 项目）需要先配置好：

TypeScript
// Deep Research 服务端的环境变量配置
GOOGLE_GENERATIVE_AI_API_KEY=你的Google API密钥
GOOGLE_GENERATIVE_AI_API_BASE_URL=https://generativelanguage.googleapis.com
ACCESS_PASSWORD=你设置的访问密码
客户端（你的第三方项目）则使用这些已配置的服务：

TypeScript
// 客户端只需要知道服务地址和访问令牌
DEEP_RESEARCH_API_URL=Deep Research部署的地址
DEEP_RESEARCH_ACCESS_TOKEN=在Deep Research设置的ACCESS_PASSWORD
2. 完整配置步骤
步骤一：部署 Deep Research 服务
克隆 Deep Research 仓库：
bash
git clone https://github.com/u14app/deep-research.git
cd deep-research
创建环境变量文件：
bash
cp env.tpl .env
配置环境变量（以 Google AI 为例）：
bash
# .env 文件
GOOGLE_GENERATIVE_AI_API_KEY=你的Google API密钥
ACCESS_PASSWORD=设置一个访问密码   # 这个密码就是其他项目访问时需要的令牌
部署服务：
bash
# 使用 Vercel 部署
vercel deploy

# 或者使用 Docker 部署
docker pull xiangfa/deep-research
docker run -d --name deep-research \
  -p 3333:3000 \
  -e GOOGLE_GENERATIVE_AI_API_KEY=你的密钥 \
  -e ACCESS_PASSWORD=你的访问密码 \
  xiangfa/deep-research
步骤二：配置第三方项目
在你的项目中创建环境变量文件：
bash
# .env 文件
DEEP_RESEARCH_API_URL=http://your-server:3333  # Deep Research 部署的地址
DEEP_RESEARCH_ACCESS_TOKEN=上面设置的ACCESS_PASSWORD  # Deep Research 中设置的访问密码
创建研究服务实例：
TypeScript
// src/services/research.ts
const researchService = new ResearchService(
  process.env.DEEP_RESEARCH_API_URL,
  process.env.DEEP_RESEARCH_ACCESS_TOKEN
);
使用服务时的参数配置：
TypeScript
await researchService.startResearch({
  query,                    // 用户输入的研究主题
  provider: 'google',       // 必须与服务端配置的 AI 提供商匹配
  thinkingModel: 'gemini-2.0-flash-thinking-exp',  // 必须是服务端支持的模型
  taskModel: 'gemini-2.0-flash-exp',
  searchProvider: 'model',
  language: 'zh-CN'
}, {
  onMessage: (text) => {
    // 处理返回的文本
  },
  onProgress: (progress) => {
    // 处理进度更新
  }
});
3. 重要说明
服务端配置：

AI 提供商的 API 密钥
访问密码（ACCESS_PASSWORD）
支持的模型和功能
客户端配置：

Deep Research 服务的URL
访问令牌（就是服务端的 ACCESS_PASSWORD）
研究参数（必须与服务端支持的配置匹配）
配置顺序：

先部署并配置 Deep Research 服务
记录服务URL和设置的访问密码
在第三方项目中配置这些信息
根据服务端支持的配置调用 API
注意事项：

provider、thinkingModel、taskModel 必须是服务端支持的值
访问令牌必须匹配服务端的 ACCESS_PASSWORD
确保网络连接和 CORS 配置正确
这样，你的第三方项目就可以通过 SSE API 来使用 Deep Research 的功能，而具体的 AI 模型调用和复杂处理都在 Deep Research 服务端进行。

You said: 部署服务只支持docker吗，其它部署方式如何设置ACCESS_PASSWORD
部署服务只支持docker吗，其它部署方式如何设置ACCESS_PASSWORD
Copilot said: Deep Research 支持多种部署方式，让我帮你详细说明每种部署方式如何设置 ACCESS_PASSWORD。 ### 1. Vercel 部署 1.
Deep Research 支持多种部署方式，让我帮你详细说明每种部署方式如何设置 ACCESS_PASSWORD。

1. Vercel 部署
点击一键部署按钮：
Markdown
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fu14app%2Fdeep-research&project-name=deep-research&repository-name=deep-research)
在 Vercel 项目设置中配置环境变量：
bash
# 必需的环境变量
ACCESS_PASSWORD=你的访问密码
GOOGLE_GENERATIVE_AI_API_KEY=你的Gemini API密钥

# 可选：如果使用其他AI提供商
OPENAI_API_KEY=你的OpenAI API密钥
ANTHROPIC_API_KEY=你的Anthropic API密钥
# ... 其他AI提供商的配置
配置步骤：

在 Vercel 控制台中选择你的项目
进入 "Settings" -> "Environment Variables"
添加环境变量 ACCESS_PASSWORD
重新部署项目使配置生效
2. Cloudflare Pages 部署
首先按照部署指南设置项目

在 Cloudflare Pages 配置环境变量：

bash
# 在 Cloudflare Pages 的环境变量设置中
ACCESS_PASSWORD=你的访问密码
GOOGLE_GENERATIVE_AI_API_KEY=你的API密钥
配置步骤：

进入 Cloudflare Pages 控制台
选择你的项目
点击 "Settings" -> "Environment variables"
添加环境变量
保存并触发重新部署
3. 静态部署
构建静态文件：
bash
# 首先设置环境变量
export ACCESS_PASSWORD=你的访问密码
export GOOGLE_GENERATIVE_AI_API_KEY=你的API密钥

# 然后构建
pnpm build:export
部署 out 目录到任何静态托管服务：
GitHub Pages
Netlify
自己的静态服务器
4. Docker 部署
bash
# 方式1: 使用环境变量
docker run -d --name deep-research \
  -p 3333:3000 \
  -e ACCESS_PASSWORD=你的访问密码 \
  -e GOOGLE_GENERATIVE_AI_API_KEY=你的API密钥 \
  xiangfa/deep-research

# 方式2: 使用 docker-compose
version: '3.9'
services:
  deep-research:
    image: xiangfa/deep-research
    container_name: deep-research
    environment:
      - ACCESS_PASSWORD=你的访问密码
      - GOOGLE_GENERATIVE_AI_API_KEY=你的API密钥
    ports:
      - 3333:3000
5. 本地开发部署
克隆项目：
bash
git clone https://github.com/u14app/deep-research.git
cd deep-research
配置环境变量：
bash
# 复制环境变量模板
cp env.tpl .env.local  # 开发环境
# 或
cp env.tpl .env        # 生产环境

# 编辑环境变量文件
ACCESS_PASSWORD=你的访问密码
GOOGLE_GENERATIVE_AI_API_KEY=你的API密钥
安装依赖并运行：
bash
pnpm install
pnpm dev  # 开发环境
# 或
pnpm build && pnpm start  # 生产环境
访问密码使用建议
密码强度：
使用足够长的随机字符串（建议至少16字符）
包含大小写字母、数字和特殊字符
避免使用容易猜测的内容
环境隔离：
bash
# 开发环境
ACCESS_PASSWORD=dev_password_xxxxx

# 生产环境
ACCESS_PASSWORD=prod_password_xxxxx
定期更换：
建议定期更换访问密码
更换后需要更新所有使用此服务的客户端
密码管理：
使用密码管理器安全存储
避免在代码或公共场所暴露
使用环境变量或密钥管理服务存储
验证部署是否成功
使用测试路径检查服务状态：
bash
curl -X GET https://你的域名/api/sse/live?query=test&password=你的访问密码
在浏览器中访问并检查是否需要密码：
Code
https://你的域名/api/sse/live?query=test&password=你的访问密码
这样，无论你选择哪种部署方式，只要正确设置了 ACCESS_PASSWORD，第三方项目就可以通过这个密码作为访问令牌来调用 API 了。记住要保护好这个密码，因为它控制着对你的 Deep Research 服务的访问权限。