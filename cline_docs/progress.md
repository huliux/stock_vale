# 当前项目进展

## 项目阶段
- **当前:** **项目重大改版 - 转向 Streamlit 和 LLM 集成 (进行中)**。
- **目标:** 构建一个以 DCF 估值为核心、Streamlit 为 GUI、并集成 LLM 进行分析总结的股票估值工具。

## 已完成工作
- **环境与配置优化:** (基本保持不变，后续需更新 .env.example)
    - [x] 创建了 `.gitignore`。
    - [x] 更新了 `requirements.txt` 添加开发工具 (后续需添加 streamlit, llm sdk)。
    - [x] 创建了 `.env.example` 模板 (后续需更新)。
    - [x] 修改 `data_fetcher.py` 使用 `.env` 加载数据库凭证。
    - [x] 修改 `main.py` 移除 `config.ini` 依赖。
    - [x] 删除了 `config.ini.example`。
    - [x] 创建并配置了 `.venv` 虚拟环境。
    - [x] 解决了 `psycopg2` 缺失问题。
- **规则与文档更新:**
    - [x] 更新了 `.clinerules` 目录下的规则文件以适应 Web 服务开发 (先前)。
    - [x] 更新了 `cline_docs` 记忆库文件以反映新的项目方向和计划 (部分完成，正在进行)。
- **Phase 1: 后端 API 开发 (FastAPI)** (基本完成，待根据新需求调整)
    - [x] 环境设置
    - [x] 创建 API 入口 (`api/main.py`)
    - [x] 重构 `DataFetcher`
    - [x] 定义 API 模型 (`api/models.py`)
    - [x] 创建 `/api/v1/valuation` 端点
    - [x] 实现端点逻辑 (调用旧 Fetcher, Calculator)
    - [x] 添加 CORS 配置
    - [x] 编写 API 测试 (`tests/api/test_main.py`)
- **Phase 2: 前端 UI 开发 (Next.js)**
    - [x] (已废弃) 初始化 Next.js 项目 (`frontend/`)
    - [x] (已废弃) 创建页面和组件
    - [x] (已废弃) 实现 API 调用逻辑
    - [x] (已废弃) 设计和实现基础 UI 样式
    - [x] (已废弃) 实现加载状态和错误处理
    - [x] (已废弃) 定义前端类型
- **Phase 3: 后端核心估值增强 (部分完成，待重构)**
    - [x] **数据获取:** 在 `data_fetcher.py` 中添加了获取 WACC 和 EV 计算所需额外字段的逻辑。
    - [x] **WACC 计算 (旧):** 在 `valuation_calculator.py` 中实现过 WACC 计算。
    - [x] **API 层 (旧):** 更新过 API 模型和逻辑以处理 WACC。
    - [x] **开发工作流脚本:** 创建 `start-dev.sh` 和 `stop-dev.sh`。
    - [x] **测试 (部分):** 更新过 API 测试，验证过脚本。
    - [x] **调试:** 解决过 TypeError 和数值准确性问题。
- **DCF估值逻辑深度优化 - 阶段一 (已完成)**
    - [x] **模块化重构**: 创建了 `data_processor.py` 和 `financial_forecaster.py`。
    - [x] **数据处理增强 (`data_processor.py`)**: 实现了数据清洗和历史财务比率/周转天数计算 (使用平均值)。
    - [x] **财务预测增强 (`financial_forecaster.py`)**: 实现了多阶段销售额预测、基于历史比率的利润表项目预测、营运资本预测和EBITDA计算。
    - [x] **DCF计算更新 (`valuation_calculator.py`)**: 添加了基于新预测数据的DCF计算方法。
    - [x] **主流程集成 (`main.py`)**: 集成了新的数据处理、预测和DCF计算流程。
    - [x] **测试修复**: 确保了相关测试通过。
- **项目重大改版 - 阶段一：清理与准备 (已完成)**
    - [x] 备份并删除 `frontend/` 目录。
    - [x] 清理并删除 `generators/` 目录及相关报告生成代码。
    - [x] 检查 `.gitignore` (无需修改)。
    - [x] 删除了不再需要的 Python 文件 (`main.py`, `valuation_calculator.py`, `report_generator.py`, `utils/report_utils.py`, `models/stock_data.py`)。
- **项目重大改版 - 阶段二：后端重构与增强 (已完成)**
    - [x] **DCF 计算逻辑模块化:**
        - [x] 创建并实现了 `wacc_calculator.py`, `terminal_value_calculator.py`, `present_value_calculator.py`, `equity_bridge_calculator.py`, `fcf_calculator.py`, `nwc_calculator.py`。
    - [x] **数据处理增强 (`DataProcessor`):**
        - [x] 更新以提取基本信息、最新指标（PE/PB 从外部传入）、最新 BS。
        - [x] 更新 `clean_data` 逻辑。
        - [x] 更新 `calculate_historical_ratios_and_turnovers` 使用中位数，处理缺失值，计算历史 CAGR。
        - [x] 添加了必要的 getter 方法。
        - [x] 修复了处理 `stock_basic` 字典的 `AttributeError`。
    - [x] **财务预测增强 (`FinancialForecaster`):**
        - [x] 更新 `predict_revenue` 使用历史 CAGR 和衰减率。
        - [x] 更新预测逻辑以支持“历史中位数”和“过渡到目标值”两种模式 (`_predict_metric_with_mode`)。
        - [x] 修复了 `Decimal` 和 `NoneType` 相关的 `TypeError`。
    - [x] **数据获取器更新 (`DataFetcher`):**
        - [x] 添加了 `get_latest_pe_pb` 方法（目前因数据库结构问题返回 None）。
        - [x] 修正了获取历史财务数据的方法调用 (`get_raw_financial_data`)。
        - [x] 添加了数据库连接测试。
        - [x] 修复了 `IndentationError`。
    - [x] **API 接口更新 (`api/main.py`, `api/models.py`):**
        - [x] 更新 API 调用流程以使用新的计算器和数据获取方法。
        - [x] 调整了数据检查逻辑。
        - [x] 更新了 `ValuationResultsContainer` 模型以包含 `detailed_forecast_table`。
        - [x] 更新了 API 响应以包含详细预测表。
        - [x] 集成了 LLM 调用逻辑（配置为 DeepSeek），包括 Prompt 格式化和 API Key 处理。
        - [x] 添加了日志记录功能 (`logging` 模块)。
        - [x] 修复了 `AttributeError` 和 `KeyError`。
        - [x] 添加了对终值计算参数的校验和默认值处理。
    - [x] **依赖与配置更新:**
        - [x] 更新 `requirements.txt`，移除了版本限制，添加了 `google-generativeai` 和 `requests`。
        - [x] 创建了 `.env` 文件。
        - [x] 更新了 `.env.example`。
        - [x] 更新了 Prompt 模板文件 (`config/llm_prompt_template.md`)。
- **项目重大改版 - 阶段三：Streamlit UI 开发 (进行中)**
    - [x] 创建了 `streamlit_app.py`。
    - [x] 实现了用户输入界面。
    - [x] 实现了 API 调用逻辑。
    - [x] 实现了结果展示（包括基本信息、DCF 核心结果、详细构成、详细预测表、LLM 分析摘要、数据警告）。
    - [x] 增加了 API 请求超时时间。
    - [x] 修正了 API 请求 payload 中的键名错误。
    - [x] 调整了结果显示布局（分离 LLM 结果，实现两列布局）。
    - [x] 添加了投资建议引导说明和情景分析占位符。
    - [x] **指标字体大小调整:** `st.metric` 中数值的字体大小已通过 CSS 成功调整。
    - [x] **区块边框样式迭代与移除:** 经过多次尝试（包括直接 `div` 包裹、`st.container` 与 CSS 相邻兄弟选择器组合），最终根据用户反馈，移除了所有为“基本信息”、“估值结果”区块以及单个“豆腐块”添加的边框和背景样式。目前仅保留字体大小调整。
    - [x] **“查看 DCF 详细构成”板块移除:** `st.expander` 已成功从 UI 中移除。
    - [x] **“预测数据”表格索引隐藏:** 经过多次尝试（包括 Styler 的 `hide_index()` 和 DataFrame 的 `reset_index(drop=True)`），最终通过将 `year` 列设置为 DataFrame 的索引，成功隐藏了默认的数字索引列。
    - [x] **LLM 总结选项默认值更改:** “启用 LLM 分析总结”复选框的默认状态已成功修改为不勾选 (False)。
    - [x] **隐含永续增长率功能:** 后端计算逻辑、API模型更新、前端UI展示（估值结果第一行第5块）。
    - [x] **基准年报日期显示:** 后端数据准备、API模型更新、前端UI展示。
    - [x] **WACC权重模式默认值调整:** Streamlit UI中默认选项改为“使用最新市场价值计算权重”。
    - [x] **退出乘数显示:** Streamlit UI中“估值结果”第二行增加显示“退出乘数”。
    - [x] **UI分隔线:** 在“基本信息”和“估值结果”之间添加了横线。
    - [x] **敏感性分析轴标签修复:** 修复了敏感性分析轴因步长设置不当导致标签显示错误的问题，以及因标签格式化精度不足导致Styler报错的问题。
    - [x] **历史财务摘要显示问题修复:** 解决了 Streamlit UI 中“历史财务摘要”表格无法正确显示资产负债表数据且不可滚动的问题。
    - [x] **历史财务比率指标名称中文化:** 在 Streamlit UI 的“历史财务比率 (中位数)”表格中，将英文指标键名替换为用户友好的中文名称。
    - [x] **详细财务预测列名优化:** 为 Streamlit UI 中“详细财务预测”表格的列名补充了中文解释。
    - [x] **`streamlit_app.py` 代码重构 (完成):**
        - [x] 辅助函数和常量迁移到 `st_utils.py`。
        - [x] 页面配置与标题渲染拆分为 `render_page_config_and_title()`。
        - [x] 侧边栏输入渲染拆分为 `render_sidebar_inputs()`。
        - [x] `render_valuation_results` 函数内部的主要UI区块（基本信息、估值结果摘要、数据警告、行业提示、敏感性分析、高级分析、LLM总结）均已拆分为独立的渲染函数。
        - [x] 主函数 `render_valuation_results` 逻辑简化。
        - [x] 重构后的应用可成功运行。
- **后端 API (`api/main.py`) 代码拆分与重构 (完成):**
    - [x] **创建 `api/utils.py`**: 迁移通用辅助函数 (`decimal_default`, `generate_axis_values_backend`, `build_historical_financial_summary`)。
    - [x] **创建 `api/llm_utils.py`**: 迁移 LLM 相关函数 (`load_prompt_template`, `format_llm_input_data`, `call_llm_api`) 及配置常量。
    - [x] **创建 `services/valuation_service.py`**: 迁移核心估值逻辑 (`run_single_valuation`)。
    - [x] **更新 `api/main.py`**: 移除已迁移代码，更新导入，并修复了因先前重构引入的语法错误。
- **金融行业适应性提示 (UI & 文档):**
    - [x] **UI层面:** 后端API (`api/main.py`, `api/models.py`) 和前端 (`streamlit_app.py`) 已更新，当检测到金融行业股票且存在较多数据问题时，会显示特定的警告信息。
    - [x] **文档层面:** `README.md`, `cline_docs/projectbrief.md`, `cline_docs/systemPatterns.md` 已更新，说明当前DCF模型对金融行业的局限性。
- **环境设置与调试:**
    - [x] 创建了 Python 虚拟环境 (`.venv`)。
    - [x] 解决了 Python 3.13 下 `numpy` 安装失败的问题。
    - [x] 解决了数据库连接失败的问题（通过创建和提示配置 `.env` 文件）。
    - [x] 解决了多处 `TypeError` (包括 float/Decimal), `AttributeError`, `IndentationError`, `KeyError`。
    - [x] 解决了总股本单位错误，使每股价值计算合理。
    - [x] 确认 PE/PB 数据源为 `valuation_metrics` 表，并更新了 `DataFetcher`。
    - [x] **确认 LLM (DeepSeek) API 调用成功:** 解决了因环境变量 `DEEPSEEK_API_KEY` 包含中文注释导致的 `UnicodeEncodeError` 问题。通过指导用户修正其终端环境中的环境变量，API 调用已恢复正常。相关的调试日志已从 `api/main.py` 中移除。
- **WACC 权重模式实现:**
    - [x] **后端:** 修改 `wacc_calculator.py`, `api/models.py`, `api/main.py` 以支持基于 "target" 或 "market" 模式计算 WACC 权重。
    - [x] **前端:** 修改 `streamlit_app.py` 添加模式选择 UI，并动态控制目标债务比例输入框。
    - [x] **测试:** 用户已确认 WACC 权重模式功能符合预期。
- **敏感性分析功能实现:**
    - [x] **后端:** 创建 `api/sensitivity_models.py`。修改 `api/models.py` 引入新模型。重构 `api/main.py` 以支持敏感性分析计算循环和结果返回。
    - [x] **前端:** 修改 `streamlit_app.py` 添加敏感性分析配置 UI 和结果展示表格。
    - [x] **前端UI布局与回调:** 敏感性分析UI模块已移至侧边栏，相关控件已添加 `on_change` 回调。WACC中心值计算逻辑已更新。退出乘数默认值已修改。
    - [x] **WACC 轴后端中心化处理:** API 模型、后端逻辑、前端请求和 UI 提示均已更新，并经用户确认功能正常。
    - [x] **EV/EBITDA 指标修正:** `DataProcessor` 添加了获取基准年实际 EBITDA 的方法，`api/main.py` 更新了敏感性分析中 EV/EBITDA 的计算逻辑以使用此值。前端标签已确认为 "EV/EBITDA (初期)"，与逻辑一致。
    - [x] **DCF 隐含 PE 指标添加:** `DataProcessor` 更新以提取最近年报 `diluted_eps`，API 模型和后端逻辑更新以计算并返回 `dcf_implied_diluted_pe`，前端 UI 更新以展示此指标。相关显示问题已解决，通过修正 `streamlit_app.py` 中的重复函数定义并清理代码，确保了指标在UI上正确渲染。

## 剩余任务 (新计划)
- **项目重大改版 - 阶段四：敏感性分析与完善**
    - [x] **敏感性分析UI布局调整:** UI模块已移至侧边栏，相关控件已添加 `on_change` 回调。
    - [x] **敏感性分析功能测试 (WACC轴后端中心化):** 用户手动测试 UI 交互、计算流程和结果展示，确认功能正常。
    - [x] **敏感性分析功能测试 (EV/EBITDA 指标修正):** 用户手动测试 UI 交互、计算流程和结果展示，确认 EV/EBITDA 指标计算正确。
    - [x] **敏感性分析功能测试 (DCF 隐含 PE 指标显示):** DCF 隐含 PE 指标已在 Streamlit UI 中正确显示和计算。前端代码 (`streamlit_app.py`) 中的重复函数定义问题已解决。
    - [x] **添加敏感性分析测试 (`tests/api/test_sensitivity.py`):** (已完成) 补充并修复了 `tests/api/test_sensitivity.py` 中的后端单元测试和 API 集成测试，覆盖敏感性分析逻辑。
        *   [x] 修复了 `api/main.py` 中 `regenerate_axis_if_needed` 函数的逻辑及 `MetricType` 导入问题。
        *   [x] 更新了 `api/sensitivity_models.py` 中的 `SUPPORTED_SENSITIVITY_OUTPUT_METRICS` 以包含 `dcf_implied_pe`。
        *   [x] 移除了 `tests/api/test_sensitivity.py` 中不必要的 `call_count` 断言。
        *   [x] 修正了 `tests/api/test_sensitivity.py` 中对 `base_valuation_summary` 的引用。
        *   [x] 统一并修正了所有 `side_effect` 函数中的 `StockValuationRequest` 对象获取逻辑。
        *   [x] 修正了测试中 `get_latest_metrics` 的 mock 数据。
        *   [x] 解决了 `tests/api/test_sensitivity.py` 中的 `IndentationError` 和后续的断言错误，所有12个测试用例均通过。
    - [x] **单元测试:** (已完成) 修复了所有先前失败的测试。
        *   修复了 `tests/api/test_main.py` 中的类型和断言错误 (先前任务)。
        *   修复了 `tests/test_data_processor.py` 中的 NaN 处理、fixture 和警告断言错误 (先前任务)。
        *   修复了 `tests/test_equity_bridge_calculator.py` 中的 NaN 处理和异常捕获逻辑。
        *   修复了 `tests/test_fcf_calculator.py` 中的 mock 目标和错误消息断言。
        *   修复了 `tests/test_financial_forecaster.py` 中的类型错误、属性错误、列名检查和数值计算/断言错误 (当前任务)。
        *   修复了 `tests/test_nwc_calculator.py` 中的警告消息断言。
        *   修复了 `tests/test_present_value_calculator.py` 中的数值比较、异常处理和 NaN 检查逻辑及错误消息断言。
        *   修复了 `tests/test_terminal_value_calculator.py` 中的缩进错误、数值比较、类型错误和错误消息断言。
        *   修复了 `tests/test_wacc_calculator.py` 中的类型错误、数值比较和错误消息断言，以及方法调用错误 (当前任务)。
        *   **所有 97 个 Pytest 测试用例均已通过。**
    - [ ] **Streamlit UI 完善:** (可选，优先级降低) 根据测试结果和用户反馈，优化布局（特别是右侧LLM区域）、交互和错误处理。
    - [ ] **优化投资建议呈现:** (可选，优先级降低) 调整 Prompt 或解析 LLM 输出，提供更明确的投资评级。
    - [x] **Memory Bank 更新:** (已完成) 更新文档以反映 Pytest 测试修复、LLM Provider 修复以及 `.env` 加载逻辑的修复。
    - [x] **LLM Prompt 模板优化 (`config/llm_prompt_template.md` -> V3.1):**
        - [x] 强化 DCF 分析中心思想和格雷厄姆原则。
        - [x] 优化对 `data_json` 中 `key_assumptions` 的利用。
        - [x] 解决 `KeyError` (因 Python `format()` 无法处理嵌套占位符)。
        - [x] 指示 LLM 不要将其响应包裹在代码块中，以修复 Streamlit UI Markdown 渲染问题。
    - [x] **LLM 提供商与模型选择逻辑修复与增强:**
        - [x] `api/main.py`: 实现请求时动态加载 `.env` (通过 `load_dotenv(override=True)`) 并获取 `LLM_PROVIDER`。
        - [x] `api/llm_utils.py`:
            - [x] **Anthropic API 对接:** 实现实际 API 调用逻辑，支持通过环境变量配置模型名称和最大 token 数。
            - [x] **DeepSeek 模型配置:** 实现从环境变量读取 DeepSeek 模型名称。
    - [x] **Streamlit UI Markdown 渲染问题:** 通过修改提示模板解决。
    - [ ] **LLM 功能重构 (进行中):**
        - [x] 更新 `.env.example` 以包含新的 LLM 相关环境变量。
        - [x] 重构 `api/llm_utils.py` 以支持 DeepSeek 和自定义 OpenAI 兼容模型，并处理新的配置参数。
        - [x] 更新 `api/models.py` 中的 `StockValuationRequest` 以包含新的 LLM 配置字段。
        - [x] 更新 `api/main.py` 以从请求中读取新的 LLM 配置并传递给 `call_llm_api`。
        - [x] 更新 `streamlit_app.py` 以添加新的 LLM 配置 UI 元素，并将用户选择传递到后端。
    - [x] **LLM 功能重构 (已完成):**
        - [x] 更新 `.env.example` 以包含新的 LLM 相关环境变量。
        - [x] 重构 `api/llm_utils.py` 以支持 DeepSeek 和自定义 OpenAI 兼容模型，并处理新的配置参数。
        - [x] 更新 `api/models.py` 中的 `StockValuationRequest` 以包含新的 LLM 配置字段。
        - [x] 更新 `api/main.py` 以从请求中读取新的 LLM 配置并传递给 `call_llm_api`。
        - [x] 更新 `streamlit_app.py` 以添加新的 LLM 配置 UI 元素，并将用户选择传递到后端。
    - [ ] **规则文件更新:** (可选) 检查并更新 `.clinerules/`。
    - [ ] **规范符合性检查:** (持续进行) 确保所有实现都已对照 `wiki/` 文档进行验证。

- **新功能：股票筛选器开发 (进行中)**
    - [x] **阶段零：功能验证 (Proof of Concept)**
        - [x] 编写 `tushare_screener_poc.py` 验证脚本。
        - [x] 验证 Tushare Pro API Token 及 `pro.stock_basic`, `pro.daily_basic` 接口调用。
        - [x] 确认关键数据字段 (静态PE, PB, 市值) 的获取。
        - [x] 初步测试数据合并与基于简单条件的筛选。
        - [x] 向用户报告验证结果，确认技术路径可行性。
    - [x] **阶段一：数据获取与缓存模块实现 (`stock_screener_data.py`)**
        - [x] 实现 `get_tushare_pro_api()`, `get_latest_valid_trade_date()`。
        - [x] 实现 `load_stock_basic()` 数据获取与本地文件缓存逻辑 (用户手动触发更新，UI显示更新日期)。
        - [x] 实现 `load_daily_basic()` 数据获取与本地文件缓存逻辑 (用户手动触发更新，UI显示数据对应交易日和拉取日期)。
        - [x] 实现 `get_merged_stock_data()` 用于合并和预处理数据，修正市值单位，扩展字段。
    - [x] **阶段二：独立 Streamlit UI 界面实现 (`stock_screener_app.py`)**
        - [x] 创建筛选器主页面结构。
        - [x] 实现侧边栏筛选条件输入组件 (静态PE范围, PB范围, 市值范围)。
        - [x] 实现数据更新按钮 (“更新股票基础数据”, “更新每日行情指标”)。
        - [x] 实现数据显示更新状态的文本提示 (最后更新日期, 数据交易日)。
        - [x] 实现主内容区筛选结果的表格展示 (`st.dataframe`)，并根据用户反馈调整显示字段和格式。
        - [x] 实现“开始筛选”按钮及与筛选逻辑的交互。
        - [x] 用户确认独立筛选器功能运行正常。
    - [x] **阶段三：整合筛选器到主估值应用 (`streamlit_app.py`) (已完成)**
        - [x] **代码结构准备和UI框架搭建:**
            - [x] 在 `streamlit_app.py` 中创建了“DCF估值”和“股票筛选器”两个标签页。
            - [x] DCF估值功能完整保留在第一个标签页。
            - [x] 股票筛选器的UI（数据显示表格、筛选按钮）和核心逻辑（数据获取、筛选、缓存状态显示）已成功整合到第二个标签页及共享侧边栏。
            - [x] 侧边栏已更新，包含DCF估值参数和股票筛选器参数（数据管理、筛选条件输入），并使用分隔符进行了视觉区分。
        - [x] **筛选器逻辑与数据流实现:**
            - [x] 调整并统一了 `st.session_state` 管理。
            - [x] 实现了“开始筛选”按钮在整合环境下的逻辑。
            - [x] 确保了数据更新按钮功能正常。
        - [x] **筛选结果与估值功能联动实现:**
            - [x] 在筛选结果表格中为每行数据添加了“进行估值”按钮。
            - [x] 实现了点击按钮后自动填充股票代码到估值输入区并切换标签页的逻辑。
            - [x] 用户会收到提示，告知股票代码已更新，并引导其切换到DCF估值标签页。
        - [x] **错误修复与代码优化:**
            - [x] 解决了 `st.set_page_config()` 调用顺序错误导致的 `StreamlitSetPageConfigMustBeFirstCommandError`。
            - [x] 解决了因在widget渲染后直接修改同名session state键值导致的 `StreamlitAPIException`。
            - [x] 调整了筛选结果表格的显示列，移除了“股息率(%)”列。
            - [x] 优化了DCF估值区基本信息显示，优先使用筛选器数据。
    - [ ] **阶段四：测试与文档 (整合后)**
        - [ ] 完整功能流程测试 (数据更新 -> 筛选 -> 点击联动按钮 -> 查看估值输入)。
        - [ ] 用户界面和体验测试。
        - [ ] (可选) 补充必要的单元测试。
        - [x] 更新所有相关的 `cline_docs/` 文档以反映筛选器功能的最终实现和整合状态 (当前正在进行)。

## 当前状态
- 后端 API 和 Streamlit 前端（DCF估值部分）的主要功能已实现。
- **LLM 功能 (已完成重构):**
    - 支持 DeepSeek 和自定义 OpenAI 兼容模型，提供灵活的前端配置。
    - Prompt 模板 (`config/llm_prompt_template.md`) 已优化至 V3.1。
- **股票筛选器 (已完成整合):**
    - 股票筛选器功能已成功整合到主应用 `streamlit_app.py` 中，作为独立的标签页，并实现了与DCF估值功能的联动。
- **DeepSeek API 调用 `UnicodeEncodeError` 问题已解决** (在之前的迭代中)。
- 敏感性分析功能已实现。
- 后端 API 服务可正常运行。
- **所有 97 个 Pytest 测试用例均已通过。**
- 存在已知的数据警告（如 D&A/Revenue 配对问题），这是由数据源限制引起的，已有降级处理逻辑。

## 已知问题
- **Pytest 警告:** `pytest` 输出中存在一些与 pandas 未来版本相关的 `FutureWarning`，不影响当前测试结果，但建议后续处理。
- **数据警告:** 计算历史中位数时，某些指标（如 D&A/Revenue）可能因数据不足或不匹配而无法计算，程序会记录警告并使用默认值。
- **金融行业估值准确性:** 当前通用DCF模型对金融行业（银行、保险、证券）的适用性有限，估值结果可能存在较大偏差。已在UI和文档中添加提示。
- **UI 样式:** (暂时搁置) 右侧 LLM 摘要列的显示效果有待优化。
- **测试覆盖:** (部分解决) `tests/api/test_sensitivity.py` 已覆盖部分敏感性分析场景。WACC 权重模式的特定单元/集成测试以及其他可能的敏感性分析场景测试可能仍需补充。

## 决策演变
- (保持不变) ...
- **明确了 WACC 参数可由前端配置并通过 API 传递。**
- **开发了 `start-dev.sh` 和 `stop-dev.sh` 以简化开发流程。**
- **启动并完成了DCF估值逻辑的深度优化工作第一阶段。**
- **项目重大转向：采用 Streamlit 替代 Next.js，移除旧报告生成器，集成 LLM 进行分析总结，后端 DCF 逻辑模块化，简化预测假设输入。**
- **LLM 提供商切换：从 Gemini 切换到 DeepSeek。**
- **数据获取逻辑调整：分离 PE/PB 获取逻辑，修复多个数据获取和处理中的错误。**
- **添加了日志记录功能。**
- **敏感性分析 WACC 轴处理方式确定：后端基于实际计算的 WACC、步长和点数重新生成轴列表。**
- **敏感性分析 EV/EBITDA 指标修正：使用基准年实际 EBITDA 作为分母。**
- **DCF 隐含 PE 指标添加：使用最近年报的稀释每股收益 (diluted_eps) 计算。**
- **Streamlit UI 迭代：根据用户反馈，完成了字体大小调整、边框样式处理（最终移除）、特定板块移除、表格索引隐藏及 LLM 选项默认值修改。**
