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
- **环境设置与调试:**
    - [x] 创建了 Python 虚拟环境 (`.venv`)。
    - [x] 解决了 Python 3.13 下 `numpy` 安装失败的问题。
    - [x] 解决了数据库连接失败的问题（通过创建和提示配置 `.env` 文件）。
    - [x] 解决了多处 `TypeError` (包括 float/Decimal), `AttributeError`, `IndentationError`, `KeyError`。
    - [x] 解决了总股本单位错误，使每股价值计算合理。
    - [x] 确认 PE/PB 数据源为 `valuation_metrics` 表，并更新了 `DataFetcher`。
    - [x] 确认 LLM (DeepSeek) API 调用成功。

## 剩余任务 (新计划)
- **项目重大改版 - 阶段四：测试与完善**
    - [x] **单元测试:** 修复了重构后所有模块（API, DataProcessor, Calculators）中先前失败的 20 个单元测试。所有 85 个测试现在均通过。
        *   修复了 `tests/api/test_main.py` 中的类型和断言错误 (先前任务)。
        *   修复了 `tests/test_data_processor.py` 中的 NaN 处理、fixture 和警告断言错误 (先前任务)。
        *   修复了 `tests/test_equity_bridge_calculator.py` 中的 NaN 处理和异常捕获逻辑。
        *   修复了 `tests/test_fcf_calculator.py` 中的 mock 目标和错误消息断言。
        *   修复了 `tests/test_financial_forecaster.py` 中的类型错误、属性错误、列名检查和数值计算/断言错误。
        *   修复了 `tests/test_nwc_calculator.py` 中的警告消息断言。
        *   修复了 `tests/test_present_value_calculator.py` 中的数值比较、异常处理和 NaN 检查逻辑及错误消息断言。
        *   修复了 `tests/test_terminal_value_calculator.py` 中的缩进错误、数值比较、类型错误和错误消息断言。
        *   修复了 `tests/test_wacc_calculator.py` 中的类型错误、数值比较和错误消息断言。
    - [ ] **Streamlit UI 完善:** (可选) 根据测试结果和用户反馈，优化布局（特别是右侧LLM区域）、交互和错误处理。
    - [ ] **优化投资建议呈现:** (可选) 调整 Prompt 或解析 LLM 输出，提供更明确的投资评级。
    - [ ] **实现情景分析功能:** (未来功能)
    - [ ] **Memory Bank 更新:** (当前正在进行) 确保所有文档与最终代码状态一致。
    - [ ] **规则文件更新:** (可选) 检查并更新 `.clinerules/`。
    - [ ] **规范符合性检查:** (持续进行) 确保所有实现都已对照 `wiki/` 文档进行验证。

## 当前状态
- 后端 API 和 Streamlit 前端的主要功能已实现，包括 DCF 计算流程、LLM 集成（配置为 DeepSeek）和结果展示。
- 端到端测试已通过，应用可正常运行并返回合理结果（PE/PB、每股价值等）。
- 存在已知的数据警告（如 D&A/Revenue 配对问题），这是由数据源限制引起的，已有降级处理逻辑。

## 已知问题
- **数据警告:** 计算历史中位数时，某些指标（如 D&A/Revenue）可能因数据不足或不匹配而无法计算，程序会记录警告并使用默认值。
- **UI 样式:** (暂时搁置) 右侧 LLM 摘要列的显示效果有待优化。

## 决策演变
- (保持不变) ...
- **明确了 WACC 参数可由前端配置并通过 API 传递。**
- **开发了 `start-dev.sh` 和 `stop-dev.sh` 以简化开发流程。**
- **启动并完成了DCF估值逻辑的深度优化工作第一阶段。**
- **项目重大转向：采用 Streamlit 替代 Next.js，移除旧报告生成器，集成 LLM 进行分析总结，后端 DCF 逻辑模块化，简化预测假设输入。**
- **LLM 提供商切换：从 Gemini 切换到 DeepSeek。**
- **数据获取逻辑调整：分离 PE/PB 获取逻辑，修复多个数据获取和处理中的错误。**
- **添加了日志记录功能。**
