# 股票估值分析工具 (Streamlit + FastAPI + LLM)

## 项目概述

本项目是一个使用 Streamlit 作为用户界面、FastAPI 作为后端 API 的股票估值分析工具。它以 DCF（自由现金流折现）模型为核心，结合大语言模型 (LLM) 提供深入的股票价值分析和投资建议摘要。

- **后端 (FastAPI):** 提供数据获取、模块化的 DCF 估值计算和 LLM 分析调用服务。
- **前端 (Streamlit):** 提供用户友好的图形界面，方便输入股票代码和估值假设，并清晰展示详细估值结果、预测数据和 LLM 生成的分析摘要。

## 主要功能

### 后端 API (`/api/v1/valuation`)
- **数据获取:** 从数据库获取指定股票的基本信息、历史财务数据、最新指标等。
- **数据处理 (`DataProcessor`):** 清洗数据、计算历史财务比率/周转天数中位数、历史 CAGR 等。
- **财务预测 (`FinancialForecaster`):** 基于历史数据和用户假设，预测未来多年的财务报表项目（收入、利润表、NWC 等）。支持“历史中位数”和“过渡到目标值”两种模式。
- **核心 DCF 计算 (模块化):**
    - **NWC 计算 (`NwcCalculator`):** 计算历史和预测期的净营运资本及变动。
    - **FCF 计算 (`FcfCalculator`):** 基于预测数据计算无杠杆自由现金流 (UFCF)。
    - **WACC 计算 (`WaccCalculator`):** 基于市场参数和公司数据计算加权平均资本成本 (WACC) 和股权成本 (Ke)。支持目标资本结构或基于市值的计算。
    - **终值计算 (`TerminalValueCalculator`):** 支持退出倍数法和永续增长法（增长率受无风险利率限制）计算终值。
    - **现值计算 (`PresentValueCalculator`):** 计算预测期 UFCF 和终值的现值。
    - **股权价值计算 (`EquityBridgeCalculator`):** 从企业价值桥接到股权价值和每股价值。
- **LLM 分析:**
    - 整合估值结果和关键财务数据，构建 Prompt。
    - 调用外部大语言模型 API (通过 `.env` 配置，支持 DeepSeek, OpenAI, Anthropic, Gemini 等)。
    - 返回 LLM 生成的估值分析摘要和投资建议。
- **API 交互:**
    - 通过 POST 请求提交股票代码、市场和估值假设。
    - 返回包含详细估值结果、预测表、LLM 摘要和数据警告的 JSON 响应。
    - 提供 Swagger UI (`/docs`) 用于 API 文档和测试。

### 前端用户界面 (`streamlit_app.py`)
- **用户输入:** 选择股票代码、市场，输入 DCF 估值假设（如预测年限、WACC 参数、终值方法及参数、增长率衰减等）。
- **结果展示:**
    - 股票基本信息。
    - DCF 核心结果（企业价值、股权价值、每股价值）。
    - 详细估值构成（UFCF 现值、终值现值、净债务等）。
    - 详细的年度财务预测表。
    - LLM 生成的分析摘要和投资建议。
    - 数据处理和计算过程中的警告信息。

## 技术栈

- **后端:** Python, FastAPI, Uvicorn, Pydantic, SQLAlchemy, psycopg2-binary, Pandas, NumPy, python-dotenv, requests, google-generativeai, openai, anthropic
- **前端:** Streamlit
- **数据库:** PostgreSQL (需要自行准备和配置)
- **测试:** pytest
- **开发工具:** Git, VS Code, venv, pip, black, flake8, pre-commit (推荐)

## 使用方法

### 1. 环境准备
- 克隆仓库。
- 准备 PostgreSQL 数据库，并根据 `wiki/数据库表文档.md` 和 `data_fetcher.py` 中的表结构导入所需数据。
- 创建 Python 虚拟环境并激活 (`python -m venv .venv` & `source .venv/bin/activate`)。

### 2. 后端与前端设置与运行
- **安装依赖:**
  ```bash
  pip install -r requirements.txt
  ```
- **配置环境变量:**
  - 复制 `.env.example` 为 `.env`。
  - 在 `.env` 文件中填入正确的数据库连接信息 (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`)。
  - 配置所需的大语言模型 API Key (例如 `DEEPSEEK_API_KEY`) 和基础 URL (如果需要)。
  - （可选）配置 WACC 计算所需的默认市场参数。
- **运行 Streamlit 应用 (包含后端调用):**
  ```bash
  streamlit run streamlit_app.py
  ```
  *注意: 当前 `streamlit_app.py` 会直接调用后端逻辑。如果需要独立运行 FastAPI 后端（例如用于 API 调试），可以使用 `uvicorn api.main:app --reload --host 0.0.0.0 --port 8124` 并相应调整 Streamlit 中的 API 调用地址。*

### 3. 使用
- 应用运行后，在浏览器中打开 Streamlit 界面。
- 输入股票代码（例如 `600519.SH`）、选择市场，调整估值假设。
- 点击“开始估值”按钮查看结果。
- （可选）通过 API 工具（如 Postman, curl 或访问 `http://localhost:8124/docs` 如果独立运行后端）向 `/api/v1/valuation` 发送 POST 请求。

## 项目结构

```
.
├── api/                  # 后端 FastAPI 应用 (主要入口和模型)
│   ├── main.py           # API 入口和路由
│   └── models.py         # Pydantic 请求/响应模型
├── cline_docs/           # Cline 记忆库 (项目文档)
├── config/               # 配置文件
│   └── llm_prompt_template.md # LLM Prompt 模板
├── tests/                # 后端单元测试
│   ├── api/              # API 测试
│   └── test_*.py         # 各模块测试文件
├── .clinerules/          # Cline 规则文件
├── .env.example          # 环境变量模板
├── .gitignore
├── data_fetcher.py       # 数据获取逻辑
├── data_processor.py     # 数据处理逻辑
├── financial_forecaster.py # 财务预测逻辑
├── nwc_calculator.py     # NWC 计算模块
├── fcf_calculator.py     # FCF 计算模块
├── wacc_calculator.py    # WACC 计算模块
├── terminal_value_calculator.py # 终值计算模块
├── present_value_calculator.py  # 现值计算模块
├── equity_bridge_calculator.py # 股权价值计算模块
├── requirements.txt      # Python 依赖
├── streamlit_app.py      # Streamlit 前端应用入口
└── README.md             # 本文件
```

## 联系方式

- **作者**: Forest
- **邮箱**: forest@example.com
