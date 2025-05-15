# 系统架构模式

## 核心架构 (Vue.js 前端 + FastAPI 后端 - Monorepo)
- **前端 UI (Vue.js):**
    - 使用 Vue.js (Vite, TypeScript, Pinia, Vue Router) 构建现代化的、交互式的用户界面。
    - 部署在 `packages/vue-frontend/`。
    - 通过 `packages/vue-frontend/src/services/apiClient.ts` 调用后端 API 获取数据和计算结果。
    - 使用 Pinia (`packages/vue-frontend/src/stores/`)进行状态管理。
- **后端 API (FastAPI):**
    - 部署在 `packages/fastapi-backend/`。
    - **职责:** 提供数据获取、核心 DCF 计算（支持单次计算和敏感性分析）、LLM 分析调用、股票筛选等服务。
    - **分层架构:** API 层 (Routers), 服务层 (包含估值协调、敏感性分析循环处理、LLM 调用、股票筛选服务), 数据访问层 (Data Fetchers), 计算模块 (拆分后的 DCF 逻辑)。
    - **依赖注入:** FastAPI 内建支持。
    - **数据验证/序列化:** 使用 Pydantic 模型。
    - **实现约束:** **所有模块的实现细节（特别是数据处理、计算公式和逻辑）必须严格遵循 `wiki/` 目录下的 PRD 和数据定义文档。**
- **共享类型 (`packages/shared-types/`):**
    - 使用 TypeScript 定义前后端共享的 API 数据结构接口，确保类型一致性。

## 前后端交互模式
- **API 通信:** 前端通过 RESTful API (JSON) 与后端 FastAPI 服务通信。
- **Pydantic 模型序列化与别名:**
    - FastAPI 后端使用 Pydantic 模型进行数据验证和序列化。
    - **关键行为:** 当 Pydantic 模型字段定义了别名 (e.g., `Field(alias="some_alias")`) 时，FastAPI 在将模型序列化为 JSON 响应时，**默认使用该别名作为 JSON 对象的键名**。
    - **前端影响:** 前端接收到的 JSON 对象的键名将是后端 Pydantic 模型中定义的别名（如果存在），而非原始字段名。
    - **共享类型的重要性:** `packages/shared-types/` 中定义的接口必须与前端实际接收到的 JSON 结构（即后端 Pydantic 模型序列化后的键名）保持一致。如果后端使用了别名，共享类型和前端组件逻辑中也必须使用这些别名作为属性/字段名。

## 设计模式应用
- **数据获取:** **策略模式 (Strategy Pattern)** (保持) 用于支持多市场数据源。
- **估值计算:** **模块化设计** (新) 将 DCF 计算流程拆分为多个职责单一的类/模块 (NWC, FCF, WACC, TV, PV, Equity Bridge)。
- **LLM 调用:** 
    - **统一接口与适配:** `api/llm_utils.py` 中的 `call_llm_api` 函数作为统一接口，根据传入的 `provider` 参数适配调用不同的 LLM 服务。
    - **支持的提供商:**
        - **DeepSeek:** 通过 `requests`库直接调用其 API。
        - **自定义 OpenAI 兼容模型:** 通过 `openai` Python SDK 调用，允许用户指定 API Base URL 和模型 ID。
    - **配置驱动:** API 密钥、默认模型 ID、默认 API Base URL（用于自定义模型）、以及 Temperature/Top-P/Max Tokens 等默认参数均从 `.env` 文件加载。前端 Vue.js UI 提供了详细的选项以覆盖这些默认参数，并将用户的选择传递给后端。
- **报告生成:** (已移除) 不再需要旧的报告生成模式。

## 数据处理
- **数据标准化:** (保持) 在 Data Fetcher 和 Data Processor 层进行。
- **配置管理:** **外部化配置** (新) 使用 `.env` 文件管理数据库凭证、API Keys、默认参数；使用配置文件管理 LLM Prompt 模板。

## 股票筛选器模块 (已整合到 FastAPI 后端和 Vue.js 前端)
- **定位:** 作为 Vue.js 前端应用的一个核心功能页面/视图，与“DCF估值”功能并列。
- **UI布局 (Vue.js):**
    - 筛选条件输入、数据显示状态、数据更新触发等 UI 元素在 `StockScreenerView.vue` 及其子组件中实现。
    - 筛选结果通过表格 (`StockScreenerResultsTable.vue`) 展示。
- **数据源与处理 (FastAPI 后端):**
    - 后端提供专门的 API 端点 (例如 `/api/v1/screener/stocks`) 处理股票筛选请求。
    - 该 API 端点封装了原 `stock_screener_data.py` 的逻辑，包括：
        - 调用 Tushare Pro API 获取股票基本信息 (`pro.stock_basic`) 和每日行情指标 (`pro.daily_basic`)。
        - `stock_basic` 和 `daily_basic` 数据在后端进行本地文件 (`.feather`) 持久化缓存，更新机制由API控制或前端触发。
        - 数据合并 (Pandas DataFrame) 和基础预处理在后端服务中完成。
- **与核心估值服务的关系与联动 (Vue.js 前端):**
    - **数据流:** 前端筛选器调用后端筛选API获取数据。
    - **功能联动:**
        - 筛选器用于初步筛选股票代码。
        - 在筛选结果表格的每一行，提供“进行估值”按钮或类似交互。
        - 点击后，前端路由导航到DCF估值页面，并将选定股票的 `ts_code` (或其他标识符) 作为参数传递或通过状态管理共享，预填充到DCF估值表单中。

## 错误处理
- **API 错误处理:** (保持) 定义统一的 HTTP 错误响应模型。
- **数据处理警告:** (新) `DataProcessor` 记录数据清洗和计算过程中的警告信息，并通过 API 传递给前端。
- **LLM 调用错误处理:** (新) 需要处理 LLM API 调用失败或返回异常的情况。

## 已知局限性与未来方向
- **行业适用性:**
    - 当前核心 DCF 估值逻辑主要针对非金融类企业设计。对于银行、保险、证券等金融行业，由于其财务报表结构和核心业务模式的显著差异，模型的适用性有限，估值结果可能存在较大偏差。
    - 系统会尝试识别金融行业公司，并在数据质量不佳时（通常由科目不匹配导致）在 UI 层面给出特别警告。
    - **未来方向:** 考虑通过策略模式或引入独立的估值模块，为金融等特定行业开发和集成更适用的估值模型（如 FCFE、剩余收益模型、内含价值模型等）。
