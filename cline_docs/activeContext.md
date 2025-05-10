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
-   **Streamlit UI 界面优化与问题修复 (大部分完成):**
    *   **指标字体:** `st.metric` 中数值的字体大小已通过 CSS 调整。
    *   **区块边框样式:** 经过多次尝试（包括直接 `div` 包裹、`st.container` 与 CSS 相邻兄弟选择器组合），最终根据用户反馈，移除了所有为“基本信息”、“估值结果”区块以及单个“豆腐块”添加的边框和背景样式。目前仅保留字体大小调整。
    *   **“查看 DCF 详细构成”板块移除:** 已从 `streamlit_app.py` 中移除该 `st.expander`。
    *   **“预测数据”表格索引:** 成功隐藏了“预测数据”表格的默认数字索引列，通过将 `year` 列设置为 DataFrame 的索引实现，使其显示效果与敏感性分析表格一致。
    *   **LLM 总结选项:** “启用 LLM 分析总结”复选框的默认状态已修改为不勾选 (False)。
    *   **隐含永续增长率:** 新增功能，当使用退出乘数法计算终值时，反推并显示“隐含永续增长率”。后端API已更新模型和计算逻辑，前端UI在“估值结果”第一行（调整为7列）第5块显示此指标。
    *   **基准年报日期显示:** 新增功能，在Streamlit UI的“基本信息”部分下方显示估值所依据的财务报表基准日期。
    *   **WACC权重模式默认值:** Streamlit UI中“WACC 权重模式”的默认选项已更改为“使用最新市场价值计算权重”。
    *   **退出乘数显示:** Streamlit UI中“估值结果”第二行（调整为7列）末尾增加显示当前估值假设使用的“退出乘数”。
    *   **UI分隔线:** 在Streamlit UI的“基本信息”和“估值结果”两个板块之间增加了一条横线。
    *   **敏感性分析轴标签修复:** 修复了敏感性分析轴因步长设置不当导致标签显示错误的问题，以及因标签格式化精度不足导致Styler报错的问题。
    *   **历史财务摘要显示问题修复 (完成):** 解决了 Streamlit UI 中“历史财务摘要”表格无法正确显示资产负债表数据且不可滚动的问题。通过修改 `api/main.py` 中构建历史财务摘要数据的逻辑，确保了所有报表类型（包括资产负债表）的数据都能正确传递给前端并显示。
    *   **历史财务比率指标名称中文化 (完成):** 在 Streamlit UI 的“历史财务比率 (中位数)”表格中，将从 API 获取的英文指标键名替换为用户友好的中文名称。
    *   **详细财务预测列名优化 (完成):** 为 Streamlit UI 中“详细财务预测”表格的列名补充了中文解释，使其更易于理解。
-   **Streamlit UI 代码重构 (`streamlit_app.py`) (完成):**
    *   **辅助函数迁移:** 将多个辅助函数和常量迁移到 `st_utils.py`。
    *   **页面配置与标题渲染拆分:** 封装到 `render_page_config_and_title()`。
    *   **侧边栏输入渲染拆分:** 封装到 `render_sidebar_inputs()`，返回输入字典。
    *   **估值结果渲染拆分 (`render_valuation_results` 内部):**
        *   基本信息区块拆分为 `render_basic_info_section()`。
        *   估值结果摘要区块拆分为 `render_valuation_summary_section()`。
        *   数据警告与行业提示分别拆分为 `render_data_warnings()` 和 `render_special_industry_warning()`。
        *   敏感性分析区块拆分为 `render_sensitivity_analysis_section()`。
        *   高级分析区块拆分为 `render_advanced_analysis_section()`。
        *   LLM总结区块拆分为 `render_llm_summary_section()`。
    *   主函数 `render_valuation_results` 逻辑简化，主要负责协调和调用各子渲染函数。
    *   应用经重构后可成功运行。
-   **应用状态:**
    *   后端 API 服务可正常运行。Streamlit 应用可运行。
    *   **DeepSeek API 调用 `UnicodeEncodeError` 问题已解决:** 通过指导用户修正其终端环境中的 `DEEPSEEK_API_KEY` 环境变量（移除其中的中文注释），API 调用已恢复正常。相关的调试日志已从 `api/main.py` 中移除。
    *   UI 方面，已根据用户反馈完成多项调整和功能增强，包括历史财务摘要的正确显示、历史财务比率指标名称的中文化以及详细财务预测列名的优化。
    *   敏感性分析的核心功能及各项指标计算逻辑已按要求实现。
    *   `tests/api/test_sensitivity.py` 中的所有测试均通过。

## 当前目标
-   **(已完成)** Streamlit UI 界面根据近期用户反馈完成调整和功能增强（包括隐含永续增长率、基准年报日期、WACC默认模式、退出乘数显示、UI分隔线、敏感性分析轴标签修复）。
-   **(已完成)** 运行 `pytest tests/api/test_sensitivity.py`，所有12个测试用例通过。
-   **(已完成)** 解决 Streamlit UI 中“历史财务摘要”表格资产负债表数据显示不全的问题。
-   **(已完成)** Streamlit UI 中“历史财务比率 (中位数)”表格指标名称中文化。
-   **(已完成)** Streamlit UI 中“详细财务预测”表格列名优化，补充中文解释。
-   **(已完成)** 解决 DeepSeek API 调用时的 `UnicodeEncodeError` 问题（已定位原因为环境变量污染，用户确认修正后 API 调用正常，调试代码已清理）。
-   **(已完成)** **金融行业适应性提示与文档更新:**
    -   UI层面: 后端API (`api/main.py`, `api/models.py`) 和前端 (`streamlit_app.py`) 已更新，当检测到金融行业股票且存在较多数据问题时，会显示特定的警告信息。
    -   文档层面: `README.md`, `cline_docs/projectbrief.md`, `cline_docs/systemPatterns.md`, `cline_docs/progress.md` 已更新，说明当前DCF模型对金融行业的局限性。
-   **记忆库更新:** (进行中) 本次 `activeContext.md` 和 `progress.md` 等记忆库文件正在更新以反映最新项目状态，特别是 `streamlit_app.py` 的重构。

## 后续步骤 (优先级排序)
0.  **严格遵循规范:** **所有开发和修复工作必须严格遵循 `wiki/` 目录下的 PRD 和数据定义文档。**
1.  **记忆库更新:** 完成 `activeContext.md` 和 `progress.md` 的更新，以反映 `streamlit_app.py` 重构的完成。
2.  **上下文窗口管理:** 当前上下文窗口使用率约为 20% (重构后可能会降低)。继续保持关注。
3.  **确认用户满意度:** 用户已确认重构后的应用可成功运行。后续可进一步确认UI细节和整体体验。
4.  **添加敏感性分析测试:** (部分完成) `tests/api/test_sensitivity.py` 已通过。评估是否需要在其他地方为敏感性分析逻辑补充更多测试。
5.  **优化投资建议呈现:** (可选，可放入新任务) 调整 Prompt 或解析 LLM 输出，提供更明确的投资评级。
6.  **规则文件更新:** (可选) 检查并更新 `.clinerules/`。
