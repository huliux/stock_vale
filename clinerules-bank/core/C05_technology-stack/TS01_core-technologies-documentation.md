# 核心技术栈文档化指南

本文档提供了关于如何记录和维护项目核心技术栈信息的指导原则和建议模板。清晰的技术栈文档有助于团队成员（包括新成员和 AI 助手）快速了解项目所依赖的关键技术、库和框架，并确保技术选型的一致性。

## 1. 为什么需要文档化核心技术栈？

*   **快速上手：** 帮助新团队成员或协作者快速了解项目的技术基础。
*   **技术选型依据：** 记录选择特定技术的理由（如果重要或有争议），供未来参考。
*   **依赖管理：** 作为识别和管理项目关键依赖的起点。
*   **一致性：** 确保团队在开发过程中使用统一和批准的技术组件。
*   **AI 协作：** 为 AI 助手（如 Cline）提供准确的技术上下文，以便其生成更相关的代码和建议。
*   **维护与升级：** 在未来进行技术升级或迁移时，提供清晰的现有技术栈画像。

## 2. 技术栈文档应包含的核心内容

一份清晰的技术栈文档通常应按层面（如后端、前端、数据库、通用工具等）组织，并包含以下信息：

*   **层面/分类 (e.g., Backend, Frontend, Database, DevOps, Testing):**
    *   **核心语言与运行时 (Core Language & Runtime):**
        *   例如：Python 3.9, Node.js 18.x, Java 17 (OpenJDK).
        *   版本号非常重要。
    *   **主要框架与库 (Key Frameworks & Libraries):**
        *   列出该层面使用的核心框架和重要库。
        *   例如：
            *   后端：FastAPI, Spring Boot, Django, Express.js.
            *   前端：React, Angular, Vue.js, Next.js, Streamlit.
            *   数据处理：Pandas, NumPy, Spark.
            *   数据库交互：SQLAlchemy, Hibernate, TypeORM.
        *   同样，注明主要版本。
    *   **选择理由 (Rationale for Key Choices - Optional but Recommended):**
        *   对于一些关键或非主流的技术选型，简要说明选择该技术的原因（如性能、生态、团队熟悉度、特定功能需求）。
*   **数据存储 (Data Storage):**
    *   **数据库类型：** PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, etc.
    *   **版本：**
    *   **ORM/ODM (if any):**
*   **消息队列 (Message Queues - if applicable):**
    *   RabbitMQ, Kafka, Redis Streams, etc.
*   **DevOps 与基础设施 (DevOps & Infrastructure - if applicable):**
    *   **容器化：** Docker, Kubernetes.
    *   **CI/CD 工具：** Jenkins, GitLab CI, GitHub Actions.
    *   **云平台：** AWS, Azure, GCP (及使用的核心服务).
    *   **配置管理工具：** Ansible, Chef, Puppet.
*   **版本控制 (Version Control):**
    *   Git (通常是标准).

## 3. 技术栈文档模板示例

```markdown
# 项目核心技术栈：[项目名称]

## 1. 后端

*   **核心语言与运行时:**
    *   [语言] [版本] (例如, Python 3.10)
*   **主要框架与库:**
    *   [Web 框架] [版本] (例如, FastAPI 0.95.0) - *理由 (可选): [简述选择原因]*
    *   [ORM/数据交互库] [版本] (例如, SQLAlchemy 1.4)
    *   [数据验证/序列化库] [版本] (例如, Pydantic 1.10)
    *   [其他重要库...]
*   **ASGI/WSGI 服务器 (如适用):**
    *   [服务器名称] [版本] (例如, Uvicorn 0.20.0)

## 2. 前端 (如果适用)

*   **核心语言与运行时:**
    *   [语言] [版本] (例如, TypeScript 4.8, Node.js 18.x for build)
*   **主要框架与库:**
    *   [UI 框架/库] [版本] (例如, React 18.2, Streamlit 1.20.0)
    *   [状态管理库] [版本] (可选, 例如, Redux, Zustand)
    *   [CSS 方案] (例如, Tailwind CSS, CSS Modules, Styled Components)
    *   [HTTP 客户端] (例如, Axios, Fetch API)
    *   [其他重要库...]

## 3. 数据存储

*   **主数据库:**
    *   [类型] [版本] (例如, PostgreSQL 14.5)
    *   [驱动/客户端库] (例如, psycopg2-binary)
*   **缓存 (如适用):**
    *   [类型] [版本] (例如, Redis 7.0)

## 4. DevOps 与基础设施 (摘要)

*   **版本控制:** Git
*   **容器化 (推荐):** Docker
*   **CI/CD (推荐):** [工具名称]
*   *(其他根据项目实际情况填写)*

## 5. 关键开发依赖与工具

*   参考 `TS02_development-tooling.md` (或本文档后续章节)。
```

---

维护一份清晰、准确的技术栈文档，对于项目的长期健康发展至关重要。它应被视为一个“活文档”，随着项目的演进和技术选型的变化而更新。
