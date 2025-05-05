# 当前工作重点

## 项目状态
- **当前阶段:** Web 服务化改造 - 计划完成，准备开始实施。
- **目标:** 将现有 Python 命令行估值工具改造为前后端分离的 Web 应用。
- **技术选型:**
    - 后端: FastAPI
    - 前端: Next.js (App Router, TypeScript, Tailwind CSS)
- **核心架构决策:**
    - 后端 API 提供估值服务。
    - 前端负责用户交互和结果展示。
    - 后端 `DataFetcher` 采用策略模式以支持多市场（A 股、港股等）。

## 最新完成的工作 (环境与规则更新)
- 更新了 `.clinerules` 目录下的所有规则文件，以匹配 Web 服务开发的技术栈、架构和规范。
- 更新了 `cline_docs` 记忆库中的 `projectbrief.md` 和 `productContext.md` 以反映新的项目目标和价值。
- (之前的环境优化工作保持记录)

## 下一步计划 (Phase 1: 后端 API 开发)
1.  **环境设置:**
    *   将 `fastapi` 和 `uvicorn[standard]` 添加到 `requirements.txt` (或 `requirements-dev.txt`)。
    *   创建 API 入口文件 `api/main.py` (暂定)。
2.  **重构 `DataFetcher`:**
    *   定义 `BaseDataFetcher` 抽象基类。
    *   将现有逻辑重构为 `AshareDataFetcher(BaseDataFetcher)`。
    *   定义标准化的内部数据结构 (如 Pydantic 模型)。
    *   实现数据标准化逻辑。
3.  **定义 API 模型 (Pydantic):**
    *   创建 `api/models.py`。
    *   定义 `StockValuationRequest` 和 `StockValuationResponse`。
4.  **创建 API 端点:**
    *   在 `api/main.py` 中创建 `/api/v1/valuation` POST 端点。
    *   实现端点逻辑：接收请求 -> 识别市场 -> 实例化对应 Fetcher -> 获取并标准化数据 -> 实例化 Calculator -> 计算 -> 返回 Response。
5.  **CORS 配置:** 添加 CORS 中间件。
6.  **测试:** 编写基本的 API 端点测试。

## 当前决策和考虑事项
- **项目结构:** 决定在根目录创建 `frontend/` 目录，后端代码暂留根目录，API 相关代码放入 `api/`。
- **多市场支持:** 确认通过策略模式重构 `DataFetcher` 是实现可扩展性的关键。
- **数据流:** 前端发送股票代码 -> 后端 API 处理计算 -> 后端返回 JSON -> 前端展示。

## 学习和项目洞察
- 从 CLI 到 Web 服务的转变需要考虑 API 设计、数据序列化、前后端通信和异步处理（FastAPI 天然支持）。
- 提前考虑多市场支持的架构设计能避免未来的大规模重构。
