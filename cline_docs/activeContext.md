# 当前活动上下文：项目重大改版规划完成 - 转向 Streamlit 和 LLM 集成

## 背景
在完成 DCF 估值逻辑优化第一阶段（提升预测精细度）后，与用户进行了深入讨论，确定了项目新的发展方向和技术栈。

## 新的核心决策 (已确认)
1.  **业务逻辑聚焦:**
    *   以 `wiki/` 目录下文档定义的最新 DCF 估值逻辑为绝对核心。
    *   删除旧的 DCF 估值逻辑和估值组合逻辑 (`get_combo_valuations` 方法将移除或重构)。
    *   PE、PB 等其他估值方法仅作为辅助参考信息展示。
    *   最终的投资建议将利用大语言模型 (LLM) 对各项结果进行综合分析后生成。
2.  **技术栈调整:**
    *   **前端:** 废弃并删除原有的 Next.js 前端 (`frontend/` 目录)。采用 **Streamlit** 构建新的 GUI。
    *   **后端:** 保留 FastAPI 后端，继续提供 JSON 数据接口，但需重构和增强。
    *   **报告:** 移除旧的非 JSON 报告生成器 (`generators/` 目录)。所有结果通过 Streamlit 展示。
3.  **LLM 集成:**
    *   后端 API 负责收集数据、构建 Prompt (模板来自配置文件)、调用外部 LLM 服务（支持 Gemini, OpenAI, Anthropic, DeepSeek，通过 `.env` 配置），并将分析摘要返回。
4.  **代码结构优化:**
    *   后端 DCF 核心计算逻辑将从 `valuation_calculator.py` 拆分到更小、职责更单一的模块 (`wacc_calculator.py`, `terminal_value_calculator.py`, `present_value_calculator.py`, `equity_bridge_calculator.py`, `fcf_calculator.py`, `nwc_calculator.py`)。
5.  **预测逻辑简化:**
    *   用户在界面上主要选择预测模式（使用历史中位数 vs. 过渡到目标值），而非强制输入所有目标值。系统自动计算历史中位数。
6.  **数据处理:**
    *   `DataProcessor` 负责计算历史中位数，处理缺失值 (NULL->0, 跳过无效期, 记录警告)，提取基本信息和最新 PE/PB。
7.  **敏感性分析 WACC 轴处理:**
    *   当 WACC 作为敏感性分析轴时，后端将使用基础计算得到的实际 `wacc_used` 作为中心点，并结合前端提供的 `step` 和 `points` 重新生成该轴的值列表进行分析，忽略前端编辑的 `values` 列表内容。
8.  **敏感性分析 EV/EBITDA 指标:**
    *   计算敏感性分析中的 EV/EBITDA 指标时，EBITDA 分母使用基准年份的实际 EBITDA 值。
9.  **DCF 隐含 PE 指标:**
    *   在估值结果中增加显示 DCF 隐含稀释 PE (基于最近年报的 `diluted_eps`)。

## 当前状态
-   项目处于**执行模式 (ACT MODE)**。
-   已完成新方向的规划和任务梳理。
-   已完成**阶段一：清理与准备**。
-   已完成**阶段二：后端重构与增强**。
-   已完成**阶段三：Streamlit UI 开发与调试**。
-   **单元测试修复:** 所有 85 个测试全部通过（不含敏感性分析和 WACC 模式）。
-   **WACC 权重模式实现:** 后端和前端逻辑完成，用户测试通过。
-   **敏感性分析功能实现:**
    *   **后端:** 基础计算逻辑和多指标表格生成完成。
    *   **前端:** 配置 UI（移至侧边栏）、结果展示逻辑完成。
    *   **WACC 轴后端中心化处理 (完成 & 测试通过):** API 模型、后端逻辑、前端请求和 UI 提示均已更新，用户确认功能正常。
    *   **EV/EBITDA 指标修正 (完成 & 测试通过):**
        *   `DataProcessor` 已更新，添加 `get_latest_actual_ebitda()` 方法。
        *   `api/main.py` 已更新，在敏感性分析中计算 EV/EBITDA 时使用基准年实际 EBITDA。
        *   前端 `streamlit_app.py` 中对应指标的显示名称已确认为 "EV/EBITDA (初期)"，与逻辑一致。
    *   **DCF 隐含 PE 指标添加 (完成):**
        *   `DataProcessor` 已更新，提取最近年报的 `diluted_eps`。
        *   API 模型 (`DcfForecastDetails`) 已更新，添加 `dcf_implied_diluted_pe` 字段。
        *   `api/main.py` 已更新，计算此隐含 PE 并加入响应。
        *   `streamlit_app.py` 已更新，在 UI 中展示此隐含 PE。前端代码中的重复函数定义问题已解决，确保了指标的正确渲染，相关调试代码已移除。
        *   **DCF 隐含稀释 PE 指标已在 Streamlit UI 中正确显示。**
    *   修复了 `api/main.py` 中 `regenerate_axis_if_needed` 函数的逻辑，以正确处理 WACC 轴和其他类型轴（如 `exit_multiple`）的值生成，特别是当输入 `values` 列表为空但提供了 `step` 和 `points` 时。
    *   修复了 `api/main.py` 中 `regenerate_axis_if_needed` 函数内部因未导入 `MetricType` 而导致的 `NameError`。
    *   更新了 `api/sensitivity_models.py` 中的 `SUPPORTED_SENSITIVITY_OUTPUT_METRICS`，添加了 `"dcf_implied_pe"`。
    *   移除了 `tests/api/test_sensitivity.py` 中 `test_sensitivity_api_dcf_implied_pe_calculation` 测试里对 `get_latest_diluted_eps.call_count` 的不必要断言。
    *   修正了 `tests/api/test_sensitivity.py` 中 `test_sensitivity_api_overall_flow` 测试里对 `base_valuation_summary` 的引用，改为 `dcf_forecast_details`，并修正了其内部 `side_effect_overall_flow` 函数中对 `stock_valuation_request_obj` 的引用。
    *   所有三个 `side_effect` 函数 (`side_effect_ev_ebitda`, `side_effect_dcf_pe`, `side_effect_overall_flow`) 中的 `StockValuationRequest` 对象获取逻辑已统一并修正。
    *   在 `test_sensitivity_api_ev_ebitda_calculation` 和 `test_sensitivity_api_dcf_implied_pe_calculation` 以及 `test_sensitivity_api_overall_flow` 中添加/修正了对 `MockDataProcessor.return_value.get_latest_metrics.return_value` 的 mock，以确保提供正确的 `latest_annual_diluted_eps` 和 `latest_actual_ebitda`。
    *   **`tests/api/test_sensitivity.py` 修复完成:**
        *   通过 `write_to_file` 修正了 `side_effect_dcf_pe` 函数的缩进，解决了 `IndentationError`。
        *   修正了 `test_sensitivity_api_dcf_implied_pe_calculation` 测试中对 `column_values` 的期望值。
        *   所有12个测试用例在 `tests/api/test_sensitivity.py` 中均已通过。
-   **Streamlit UI 界面优化 (完成):**
    *   **指标字体:** `st.metric` 中数值的字体大小已通过 CSS 调整。
    *   **区块边框样式:** 经过多次尝试（包括直接 `div` 包裹、`st.container` 与 CSS 相邻兄弟选择器组合），最终根据用户反馈，移除了所有为“基本信息”、“估值结果”区块以及单个“豆腐块”添加的边框和背景样式。目前仅保留字体大小调整。
    *   **“查看 DCF 详细构成”板块移除:** 已从 `streamlit_app.py` 中移除该 `st.expander`。
    *   **“预测数据”表格索引:** 成功隐藏了“预测数据”表格的默认数字索引列，通过将 `year` 列设置为 DataFrame 的索引实现，使其显示效果与敏感性分析表格一致。
    *   **LLM 总结选项:** “启用 LLM 分析总结”复选框的默认状态已修改为不勾选 (False)。
-   **应用状态:** 后端 API 服务可正常运行。Streamlit 应用可运行，并已根据用户反馈完成多项 UI 调整。敏感性分析的核心功能及各项指标计算逻辑已按要求实现。`tests/api/test_sensitivity.py` 中的所有测试均通过。

## 当前目标
-   **(已完成)** Streamlit UI 界面根据近期用户反馈完成调整。
-   **(已完成)** 运行 `pytest tests/api/test_sensitivity.py`，所有12个测试用例通过。
-   **记忆库更新:** (进行中) 更新所有 `cline_docs/` 中的记忆库文件以反映最新项目状态。

## 后续步骤 (优先级排序)
0.  **严格遵循规范:** **所有开发和修复工作必须严格遵循 `wiki/` 目录下的 PRD 和数据定义文档。**
1.  **确认用户满意度:** 在完成记忆库更新后，与用户确认当前 Streamlit UI 状态是否满足所有要求。
2.  **添加敏感性分析测试:** (部分完成) `tests/api/test_sensitivity.py` 已通过。评估是否需要在其他地方为敏感性分析逻辑补充更多测试。
3.  **优化投资建议呈现:** (可选，可放入新任务) 调整 Prompt 或解析 LLM 输出，提供更明确的投资评级。
4.  **规则文件更新:** (可选) 检查并更新 `.clinerules/`。
