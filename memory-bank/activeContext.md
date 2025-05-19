# 当前活动上下文：Vue.js 前端完善与估值准确性保障

## 背景
项目前端技术栈已从 Streamlit 迁移到 Vue.js，并采用了 Monorepo 结构。在之前的会话中，我们对项目状态、旧版 Streamlit 功能 (`streamlit_app.py`) 以及 PRD 文档 (`wiki/` 目录) 进行了深入分析和讨论，明确了以 PRD 为准绳、确保估值结果准确性和功能完整性的核心目标。

## 新的核心决策 (已确认)
1.  **业务逻辑聚焦:**
    *   以 `wiki/` 目录下文档定义的最新 DCF 估值逻辑为绝对核心。
    *   PE、PB 等其他估值方法仅作为辅助参考信息展示。
    *   最终的投资建议将利用大语言模型 (LLM) 对各项结果进行综合分析后生成。
2.  **技术栈调整 (已完成):**
    *   **前端:** 采用 **Vue.js (Vite, TypeScript, Pinia, Vue Router)**。
    *   **后端:** 保留 FastAPI 后端。
    *   **项目结构:** 轻量级Monorepo结构 (`packages/fastapi-backend`, `packages/vue-frontend`, `packages/shared-types`)。
3.  **LLM 集成 (已完成):**
    *   支持 DeepSeek 和自定义 OpenAI 兼容模型。
    *   配置通过 `.env` 文件管理，前端提供参数覆盖。
4.  **代码结构优化 (已完成):**
    *   后端 DCF 核心计算逻辑已模块化。
5.  **预测逻辑简化 (已实现):**
    *   用户在界面上主要选择预测模式。
6.  **数据处理 (已实现):**
    *   `DataProcessor` 负责计算历史中位数，处理缺失值等。
7.  **敏感性分析 (已实现 - 后端部分):**
    *   WACC 轴后端中心化处理。
    *   EV/EBITDA 指标使用基准年实际 EBITDA。
8.  **DCF 隐含 PE 指标 (已实现):**
    *   在估值结果中增加显示。
9.  **股票筛选器功能 (已整合到 Vue.js 前端和 FastAPI 后端):**
    *   UI 和核心逻辑已在 Vue.js 中实现。
    *   后端 API (`/api/v1/screener/stocks`) 提供数据。
    *   数据源为 Tushare Pro API，使用 `.feather` 文件进行本地缓存。
10. **(重大决策) 前端技术栈与架构演进 (已完成):**
    *   前端框架已确定为 Vue.js。
    *   项目结构已调整为 Monorepo。
11. **工作准则 (新确立):**
    *   **估值结果准确性第一：** 与旧版（Streamlit + PRD）严格对齐。
    *   **功能完整性：** 不缺失旧版核心功能与PRD定义功能。
    *   **用户体验连续性：** 借鉴旧版优秀设计，优化交互。
    *   **代码质量与可维护性：** 遵循最佳实践。
    *   **严格遵循文档：** PRD为最高权威。
    *   **沟通与验证：** 持续与用户确认，通过案例测试。
12. **UI/UX 优化与技术升级 (新决策):**
    *   **技术选型**: 引入 Tailwind CSS 和 `shadcn-vue` (基于 `/unovue/shadcn-vue` 移植版) 以改进UI样式和组件。
    *   **导航结构调整**:
        *   一级导航：头部横向排列（股票筛选、绝对估值、深度研究、策略研究、回测模拟、实操记录）。
        *   二级导航/参数操作区：页面左侧。
        *   内容区：页面右侧。

## 当前状态
-   项目处于**执行模式 (ACT MODE)**。
-   **前端 (`packages/vue-frontend`):**
    *   `DcfParametersForm.vue`:
        *   支持全面的DCF参数输入。
        *   敏感性分析参数UI已简化为仅支持WACC和退出乘数。
        *   输入校验逻辑已得到增强。
    *   `DcfValuationView.vue`: 能够接收扩展参数并构建API请求。
    *   `DcfResultsDisplay.vue`:
        *   **“FCF现值 (PV of FCF)”列显示 "N/A" 问题**: 后端已修改，前端待验证。
        *   **TypeScript 错误**: 已通过修改 `shared-types` 解决，`@ts-ignore` 已移除。
        *   **敏感性分析结果渲染**: 渲染逻辑已审查，认为基本完整，待实际数据测试。
    *   股票筛选器页面及相关组件核心功能已实现。
    *   错误处理已统一到Pinia store。
    *   **当前布局**: 采用简单的Flexbox布局，侧边栏固定宽度，内容区可滚动，尚未实现完全的响应式设计。
-   **共享类型 (`packages/shared-types`):**
    *   `ApiDcfValuationRequest`, `ApiSensitivityAnalysisRequest`, `ApiSensitivityAnalysisResult` 等相关类型已更新。
    *   `historical_financial_summary` 和 `historical_ratios_summary` 的类型定义已优化。
-   **后端 (`packages/fastapi-backend`):**
    *   API服务可正常运行。
    *   数据源调整（优先使用 `.feather` 缓存）已完成。
    *   敏感性分析计算逻辑已在后端实现。
    *   DCF估值API (`/api/v1/valuation`) 的请求和响应模型与前端 `shared-types` 基本兼容。
    *   股票筛选器API (`/api/v1/screener/stocks`) 当前不支持分页和可配置排序。
    *   `/screener/update-data` API 已修改为返回真实的缓存文件更新时间戳。

## 当前核心任务 (根据用户最新指示和PLAN MODE讨论结果)
**主要目标：优化前端UI/UX，实现页面自适应，并引入 `shadcn-vue` 组件库和Tailwind CSS。**
1.  **基础环境搭建**:
    *   在 `packages/vue-frontend` 中安装和配置 Tailwind CSS。
    *   初始化 `shadcn-vue` CLI 并配置。
2.  **全局布局重构 (`App.vue`)**:
    *   实现新的头部一级导航。
    *   调整主内容区域布局，为各模块内部的两栏布局做准备。
3.  **核心视图布局重构**:
    *   在 `DcfValuationView.vue`, `StockScreenerView.vue` 等一级模块视图内部实现“左侧参数/二级导航 + 右侧内容”的响应式两栏布局。
4.  **组件替换与样式美化**:
    *   逐步将现有HTML元素和自定义组件替换为 `shadcn-vue` 组件，并使用Tailwind CSS进行样式调整。

## 后续步骤 (在完成当前核心任务后，根据任务交接文档和PLAN MODE讨论梳理)
0.  **严格遵循规范:** **所有开发和修复工作必须严格遵循 `wiki/` 目录下的 PRD 和数据定义文档，并参考 `streamlit_app.py` 的实现细节以保证一致性。**
1.  **DCF参数表单 (`packages/vue-frontend/src/components/DcfParametersForm.vue`):**
    *   [已确认] 过渡年数默认值动态关联“预测期年数”的逻辑。
    *   [已增强] 所有参数的输入校验逻辑。
2.  **API客户端 (`packages/vue-frontend/src/services/apiClient.ts`) 与参数转换 (`DcfValuationView.vue`):**
    *   [已检查] `performDcfValuation` 函数的参数序列化逻辑（主要在 `DcfParametersForm.vue` 中）与后端 FastAPI Pydantic 模型基本一致。
3.  **前端 `DcfResultsDisplay.vue` 其他数据显示问题验证与跟进:**
    *   [待验证] “FCF现值 (PV of FCF)”列是否正确显示。
    *   [待验证] “基准年报”、部分“核心估值指标”（如安全边际、WACC、Ke）以及“详细财务预测”表格中的其他列是否正确显示和格式化。
4.  **后端API适配与确认 (大部分已完成):**
    *   **DCF估值API (`/api/v1/valuation`):** [已检查] 后端能够正确接收和处理前端参数，计算结果与PRD一致性待通过实际案例测试。
    *   **股票筛选器API (`/api/v1/screener/stocks`):** [已确认] 当前不支持分页、排序。可作为后续增强。
    *   **`/screener/update-data` API：** [已完成] 修改为返回真实的缓存数据更新时间戳。
5.  **其他待办 (优先级较低或待评估):**
    *   实现估值结果缓存与历史记录管理功能 (V2方案)。
    *   处理 Pytest 警告。
6.  **上下文窗口管理:** 在主要功能模块完成后, 或上下文窗口使用率显著增高时, 应使用 `new_task` 工具创建新任务。
7.  **记忆库更新:** 在每个有意义的工作阶段完成后，及时更新所有相关的记忆库文件。
