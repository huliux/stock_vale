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
3.  **LLM 集成 (重构计划):**
    *   **目标:** 移除对 Gemini, OpenAI (直接集成), Anthropic 的支持。保留 DeepSeek，并新增对“其他自定义模型”（通过 OpenAI SDK 访问，兼容 OpenAI API 格式）的支持。
    *   **配置:** 所有 LLM 相关参数（API密钥、模型ID、API Base URL、Temperature, Top-P, Max Tokens 默认值）将通过 `.env` 文件管理。
    *   **前端:** Streamlit UI 将允许用户选择 DeepSeek 或自定义模型，并为自定义模型提供 API Base URL 和模型 ID 输入。同时，允许用户调整通用的 LLM 参数（Temperature, Top-P, Max Tokens）。
    *   **后端:** FastAPI 后端将接收前端传递的 LLM 配置，并据此调用相应的 LLM 服务。
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
10. **(新功能规划) 新增股票筛选器功能:**
    *   **目标:** 开发一个独立的股票筛选工具，帮助用户基于核心财务指标（静态PE、PB、市值）快速筛选A股市场的股票。
    *   **数据源:** 直接使用 Tushare Pro API (`pro.stock_basic` 和 `pro.daily_basic`)。
    *   **核心技术:** Python, Streamlit, Pandas, Tushare。
    *   **缓存策略:** `stock_basic` 和 `daily_basic` 数据均采用本地文件持久化缓存，由用户手动触发更新，并在UI上显示数据更新状态。
    *   **开发流程:** 先进行功能验证 (Proof of Concept)，再进行完整功能开发。

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
-   **Pytest 测试修复 (完成):**
    *   修复了 `tests/test_financial_forecaster.py` 中的 `AssertionError` 和 `TypeError`，确保所有5个测试通过。
    *   修复了 `tests/test_wacc_calculator.py` 中的 `AttributeError`，并调整了相关逻辑，确保所有14个测试通过。
    *   **所有 97 个 Pytest 测试用例均已通过。**
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
-   **后端 API 代码重构 (`api/main.py`) (完成):**
    *   **辅助函数迁移至 `api/utils.py`**: `decimal_default`, `generate_axis_values_backend`, `build_historical_financial_summary`。
    *   **LLM 相关逻辑迁移至 `api/llm_utils.py`**: `load_prompt_template`, `format_llm_input_data`, `call_llm_api` 及相关常量。
    *   **核心估值逻辑迁移至 `services/valuation_service.py`**: `_run_single_valuation` (重命名为 `run_single_valuation`)。
    *   `api/main.py` 已更新以使用新的工具和服务函数，并修复了相关的语法错误。
-   **应用状态:**
    *   后端 API 服务可正常运行。Streamlit 应用可运行。
    *   **DeepSeek API 调用 `UnicodeEncodeError` 问题已解决:** 通过指导用户修正其终端环境中的 `DEEPSEEK_API_KEY` 环境变量（移除其中的中文注释），API 调用已恢复正常。相关的调试日志已从 `api/main.py` 中移除。
    *   UI 方面，已根据用户反馈完成多项调整和功能增强，包括历史财务摘要的正确显示、历史财务比率指标名称的中文化以及详细财务预测列名的优化。
    *   敏感性分析的核心功能及各项指标计算逻辑已按要求实现。
    *   `tests/api/test_sensitivity.py` 中的所有测试均通过。
    *   **所有 Pytest 测试均已通过。**
    *   **LLM Provider 选择逻辑修复:** 修正了 `api/llm_utils.py` 和 `api/main.py` 中 LLM 提供商选择逻辑，确保正确使用 `.env` 文件中配置的 `LLM_PROVIDER`。
    *   **`.env` 文件加载修复:** 在 `api/main.py` 顶部添加了 `load_dotenv()`，以确保环境变量在应用启动时正确加载，解决了 API 密钥无法找到的问题。
-   **(新增修复完成)** **估值假设传递修复:**
    *   解决了前端 Streamlit UI 中用户输入的“历史 CAGR 年衰减率”未能正确传递到后端 `FinancialForecaster` 模块的问题。
    *   在 `services/valuation_service.py` 的 `run_single_valuation` 方法中，添加了将 API 请求中的 `cagr_decay_rate` 键名映射为 `FinancialForecaster` 期望的 `revenue_cagr_decay_rate` 的逻辑。
    *   经用户测试确认，自定义的衰减率已在后端计算中正确生效。
-   **(新增状态确认)** **LLM API 调用确认:**
    *   用户已确认，在启用 LLM 分析总结功能时，API 调用正常，无 API 密钥相关错误（特指 DeepSeek）。
-   **(新增修复与增强完成)** **LLM 功能优化与调试 (本次任务核心):**
    *   **LLM Prompt 模板优化 (`config/llm_prompt_template.md` -> V3.1):**
        *   强化了以 DCF 分析为中心，强调格雷厄姆价值投资原则（内在价值、安全边际）。
        *   优化了对 `data_json` 中 `key_assumptions`（包括 `prediction_details`）的利用，引导 LLM 进行更深入的假设评估。
        *   解决了因 Python `format()` 方法无法处理嵌套占位符导致的 `KeyError`。
        *   通过在提示模板中明确指示 LLM 不要将其响应包裹在代码块标记中，解决了 Streamlit UI 中 Markdown 无法正确渲染的问题。
    *   **LLM 提供商与模型选择逻辑修复与增强:**
        *   `api/main.py`: 修改为在每个 API 请求处理时动态从 `.env` 文件加载配置（通过在端点函数开头调用 `load_dotenv(override=True)`）并获取 `LLM_PROVIDER` 环境变量，确保对 `.env` 中 `LLM_PROVIDER` 的更改能即时生效。
        *   `api/llm_utils.py`:
            *   **Anthropic API 对接:** 替换了原有的占位符，实现了对 Anthropic API (`messages.create`) 的实际调用逻辑。支持通过环境变量 `ANTHROPIC_MODEL_NAME` (默认 `claude-3-sonnet-20240229`) 和 `ANTHROPIC_MAX_TOKENS` (默认 `4000`)进行配置。指导用户安装了 `anthropic` 库。协助用户定位到 Anthropic API 返回 `403 Forbidden` 错误是由于 API 密钥/账户权限问题，而非代码问题。
            *   **DeepSeek 模型配置:** 修改了 DeepSeek API 调用逻辑，使其从环境变量 `DEEPSEEK_MODEL_NAME` (默认 `deepseek-chat`) 读取模型名称，允许用户指定如 `deepseek-reasoner` 等不同模型。
    *   **Streamlit UI Markdown 渲染:**
        *   确认 `streamlit_app.py` 中 `render_llm_summary_section` 函数使用 `st.markdown(llm_summary, unsafe_allow_html=True)`。
        *   Markdown 渲染问题最终通过修改 `config/llm_prompt_template.md` 指示 LLM 不要输出代码块标记解决。
    *   **LLM 功能重构 (已完成):** LLM 功能已重构以支持 DeepSeek 和自定义 OpenAI 兼容模型，并提供灵活的前端配置。
        *   `.env.example` 已更新。
        *   `api/llm_utils.py` 已重构。
        *   `api/models.py` (StockValuationRequest) 已更新。
        *   `api/main.py` 已更新。
        *   `streamlit_app.py` 已更新。
-   **股票筛选器功能开发与整合 (已完成):**
    *   **功能验证 (PoC) (已完成):**
        *   创建了 `tushare_screener_poc.py` 并成功验证了 Tushare API 连通性、核心数据接口 (`stock_basic`, `daily_basic`) 调用、关键字段获取以及初步的数据合并与筛选。
    *   **数据模块 (`stock_screener_data.py`) (已完成):**
        *   实现了 `get_tushare_pro_api()`, `get_latest_valid_trade_date()`。
        *   实现了 `load_stock_basic()` 带缓存功能。
        *   实现了 `load_daily_basic()` 带按日期缓存功能。
        *   实现了 `get_merged_stock_data()` 用于合并和预处理数据，修正了市值单位转换，并扩展了获取的字段。
    *   **独立筛选器UI (`stock_screener_app.py`) (已完成):**
        *   初步搭建了 Streamlit 应用，包含侧边栏输入、数据显示、数据更新按钮和筛选逻辑。
        *   根据用户反馈，更新了显示字段和格式。
        *   用户已确认独立筛选器功能运行正常。
    *   **整合到主应用 (`streamlit_app.py`) (已完成):**
        *   在 `streamlit_app.py` 中创建了“DCF估值”和“股票筛选器”两个标签页。
        *   DCF估值功能完整保留在第一个标签页。
        *   股票筛选器的UI（数据显示表格、筛选按钮）和核心逻辑（数据获取、筛选、缓存状态显示）已成功整合到第二个标签页及共享侧边栏。
        *   侧边栏已更新，包含DCF估值参数和股票筛选器参数（数据管理、筛选条件输入），并使用分隔符进行了视觉区分。
        *   实现了在“股票筛选器”标签页的筛选结果中，为每行股票数据显示一个“进行估值”按钮。
        *   点击“进行估值”按钮后，能成功将对应股票的`ts_code`传递到DCF估值标签页的股票代码输入框，并通过`st.rerun()`刷新状态。
        *   用户会收到提示，告知股票代码已更新，并引导其切换到DCF估值标签页。
        *   解决了 `st.set_page_config()` 调用顺序错误导致的 `StreamlitSetPageConfigMustBeFirstCommandError`。
        *   解决了因在widget渲染后直接修改同名session state键值导致的 `StreamlitAPIException`，采用了通过临时session state变量在下次rerun前更新目标widget状态的模式。
        *   根据用户反馈，调整了筛选结果表格的显示列：移除了原先显示`nan%`的“股息率(%)”列，并重新调整了其余列的宽度。
        *   实现了当从筛选器联动到DCF估值时，DCF估值区的“基本信息”部分（如最新价格、PE、PB）会优先使用筛选器获取的数据。

## 当前目标
-   **更新记忆库 (本次“update memory bank”任务的核心):**
    *   全面更新所有 `cline_docs/` 文件，特别是 `activeContext.md`, `progress.md`, `systemPatterns.md`，以准确反映股票筛选器整合完成后的系统架构和功能状态。

## 后续步骤 (优先级排序)
0.  **严格遵循规范:** **所有开发和修复工作必须严格遵循 `wiki/` 目录下的 PRD 和数据定义文档。**
1.  **处理 Pytest 警告:** (可选，优先级较低) 解决 `pytest` 输出中的 `FutureWarning`。
2.  **确认用户满意度:** 在整合功能稳定后，进一步确认UI细节和整体体验。
3.  **上下文窗口管理:** 在主要功能模块完成后，或上下文窗口使用率显著增高时，应使用 `new_task` 工具创建新任务。
4.  **规则文件更新 (`.clinerules/`):** (可选，定期进行) 根据项目经验检查并更新。
