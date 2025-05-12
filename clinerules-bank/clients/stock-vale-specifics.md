# `stock_vale` 项目特定规则与决策点

本文档记录了 `stock_vale` 项目中一些特有的、不易泛化到其他通用规则中的决策、业务逻辑侧重点、特定技术选型的原因或特定模块的实现要点。它是对 `clinerules-bank/core/` 中通用规则的补充，并为理解 `stock_vale` 项目的独特性提供上下文。

## 1. 核心业务逻辑依据

*   **`wiki/` 目录下的 PRD 文档：**
    *   这是 `stock_vale` 项目所有业务逻辑（特别是 DCF 估值模型细节、财务数据处理规则、指标计算公式等）的 **唯一且最终的依据 (Source of Truth)**。
    *   任何与估值相关的编码、修改或讨论，都必须以此为准。
    *   与 Cline 协作时，应优先引用 `wiki/` 文档内容来阐述业务需求。
    *   *(参考通用规则：`core/C03_development-practices/DP03_business-logic-source-of-truth.md`)*

## 2. 项目架构与技术选型特定点

*   **前端技术选型：Streamlit**
    *   **背景：** 项目初期曾考虑或尝试过 Next.js 前端，后转向 Streamlit。
    *   **原因：** Streamlit 更能快速构建数据密集型、交互式的分析应用，尤其适合 Python 技术栈为主的团队快速迭代。
    *   **影响：** 前端相关的规则和实践主要围绕 Streamlit 展开。与 Next.js 相关的规则（如 Tailwind CSS 使用）可视为历史参考或未来潜在方向。
    *   *(参考 `cline_docs/activeContext.md` 中的决策演变)*
*   **后端核心计算模块拆分：**
    *   DCF 估值逻辑被细分为多个独立的计算器模块 (`WaccCalculator`, `FcfCalculator`, `TerminalValueCalculator`, `PresentValueCalculator`, `EquityBridgeCalculator`, `NwcCalculator`)。
    *   **原因：** 提高代码的可测试性、可维护性和复用性，降低单个模块的复杂度。
    *   *(参考 `cline_docs/systemPatterns.md` 和 `cline_docs/activeContext.md`)*
*   **LLM 集成策略：**
    *   **当前支持：** DeepSeek 和自定义 OpenAI 兼容模型。
    *   **Prompt 工程：** `config/llm_prompt_template.md` (V3.1) 经过特定优化，强调以 DCF 分析为中心、格雷厄姆价值投资原则，并指导 LLM 如何利用关键假设进行深入评估。
    *   **配置管理：** LLM 相关参数（API Key, Base URL, Model ID, Temperature, Top-P, Max Tokens）均通过 `.env` 文件管理，并允许用户在 Streamlit UI 中进行部分覆盖。
    *   *(参考 `cline_docs/activeContext.md` 和 `cline_docs/systemPatterns.md`)*

## 3. 特定功能实现要点

*   **敏感性分析 WACC 轴处理：**
    *   当 WACC 作为敏感性分析轴时，后端使用基础计算得到的实际 `wacc_used` 作为中心点，并结合前端提供的 `step` 和 `points` 重新生成该轴的值列表。
    *   *(参考 `cline_docs/activeContext.md`)*
*   **EV/EBITDA 指标计算 (敏感性分析中)：**
    *   EBITDA 分母使用基准年份的实际 EBITDA 值。
    *   *(参考 `cline_docs/activeContext.md`)*
*   **DCF 隐含 PE 指标：**
    *   基于最近年报的 `diluted_eps` 计算。
    *   *(参考 `cline_docs/activeContext.md`)*
*   **金融行业估值局限性提示：**
    *   由于当前 DCF 模型主要针对非金融企业，对于金融行业股票，系统会在数据质量不佳时（通常由科目不匹配导致）在 UI 层面给出特别警告。
    *   *(参考 `cline_docs/systemPatterns.md` 和 `cline_docs/activeContext.md`)*

## 4. `cline_docs/` (记忆库) 的核心地位

*   `cline_docs/` 目录下的所有 Markdown 文件（`activeContext.md`, `progress.md`, `systemPatterns.md`, `techContext.md`, `projectbrief.md`, `productContext.md`）是 Cline 理解本项目当前状态、历史决策、技术细节和未来方向的最重要信息源。
*   这些文档的及时更新对于与 Cline 高效协作至关重要。

## 5. 测试覆盖率特例

*   **核心估值算法覆盖率：** 要求达到接近 100% 的单元测试覆盖率。
    *   *(源自原 `clinerules-bank/01-coding.md`)*

---

本文档会随着 `stock_vale` 项目的演进而持续更新，记录下那些使其区别于一般项目的特定实践和决策。
