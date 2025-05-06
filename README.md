# 股票估值 Web 服务

## 项目概述

本项目是一个前后端分离的 Web 服务，旨在提供股票估值分析功能。它将原有的命令行估值工具改造为现代化的 Web 应用，方便用户通过 API 或 Web 界面进行交互。

- **后端 (FastAPI):** 提供核心的数据获取和估值计算 API。
- **前端 (Next.js):** 提供用户友好的界面，用于输入股票代码、设置参数并展示详细的估值结果。

## 主要功能

### 后端 API (`/api/v1/valuation`)
- **数据获取:** 从数据库获取指定股票的基本信息、财务数据、分红数据和最新价格。
- **核心估值计算:**
    - **WACC 计算:** 基于公司财务数据和市场参数计算加权平均资本成本。
    - **相对估值:** 计算当前 PE、PB、EV/EBITDA。
    - **绝对估值 (DCF):**
        - 支持 FCFF 和 FCFE 模型。
        - 区分**基本资本性支出 (Basic Capex)** 和 **完整资本性支出 (Full Capex)**。
        - 使用计算出的 WACC 作为核心折现率进行敏感性分析。
    - **绝对估值 (DDM):** 基于历史分红和股权成本 (Ke) 进行估值。
    - **其他分析:** 计算股息率、派息率、3年平均分红、营收/净利润3年CAGR。
    - **综合分析:** 提供六种不同权重组合的估值结果。
    - **投资建议:** 基于 DCF (Basic Capex) 估值和安全边际生成买入/卖出/持有建议。
- **API 交互:**
    - 支持通过 POST 请求提交股票代码和可选的敏感性分析参数（PE/PB/EV_EBITDA 倍数、增长率）。
    - 返回包含所有计算结果的详细 JSON 响应。
    - 提供 Swagger UI (`/docs`) 用于 API 文档和测试。

### 前端界面 (开发中)
- **用户输入:** 提供表单让用户输入股票代码。
- **结果展示:** 清晰地展示后端返回的各项估值指标、分析结果和投资建议。
- **交互:** (未来) 可能支持用户调整敏感性分析参数。

## 技术栈

- **后端:** Python, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Pandas, python-dotenv
- **前端:** TypeScript, React, Next.js (App Router), Tailwind CSS
- **数据库:** PostgreSQL (需要自行准备和配置)
- **开发工具:** Git, VS Code, venv, pip, pytest, npm/yarn

## 使用方法

### 1. 环境准备
- 克隆仓库。
- 准备 PostgreSQL 数据库，并根据 `data_fetcher.py` 中的表结构导入所需数据。
- 创建 Python 虚拟环境并激活。

### 2. 后端设置与运行
- **安装依赖:**
  ```bash
  pip install -r requirements.txt
  ```
- **配置环境变量:**
  - 复制 `.env.example` 为 `.env`。
  - 在 `.env` 文件中填入正确的数据库连接信息 (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`)。
  - （可选）配置 WACC 计算所需的默认市场参数 (`DEFAULT_BETA`, `RISK_FREE_RATE`, `MARKET_RISK_PREMIUM`, `DEFAULT_COST_OF_DEBT`)。
- **运行后端服务:**
  ```bash
  # 推荐使用 uvicorn 运行，支持热重载
  uvicorn api.main:app --reload --host 0.0.0.0 --port 8124
  ```
- **访问 API 文档:** 服务运行后，在浏览器中打开 `http://localhost:8124/docs` 查看 Swagger UI。

### 3. 前端设置与运行
- **进入前端目录:**
  ```bash
  cd frontend
  ```
- **安装依赖:**
  ```bash
  # 根据你的包管理器选择
  npm install
  # 或者
  # yarn install
  ```
- **运行前端开发服务器:**
  ```bash
  # 根据你的包管理器选择
  npm run dev
  # 或者
  # yarn dev
  ```
- **访问前端界面:** 在浏览器中打开 `http://localhost:3000`。

### 4. 使用
- 通过前端界面输入股票代码（例如 `600519.SH`）并提交。
- 或者，直接通过 API 工具（如 Postman, curl 或 Swagger UI）向 `http://localhost:8124/api/v1/valuation` 发送 POST 请求，请求体类似：
  ```json
  {
    "ts_code": "600519.SH"
    // 可以添加可选参数，如 "pe_multiples": [10, 15, 20]
  }
  ```

## 项目结构

```
.
├── api/                  # 后端 FastAPI 应用
│   ├── main.py           # API 入口和路由
│   └── models.py         # Pydantic 请求/响应模型
├── cline_docs/           # Cline 记忆库 (项目文档)
├── frontend/             # 前端 Next.js 应用
│   ├── public/
│   ├── src/
│   ├── next.config.ts
│   ├── package.json
│   └── ...
├── tests/                # 后端测试
│   └── api/
│       └── test_main.py  # API 端点测试
├── .clinerules/          # Cline 规则文件
├── .env.example          # 环境变量模板
├── .gitignore
├── data_fetcher.py       # 数据获取逻辑
├── requirements.txt      # 后端 Python 依赖
├── valuation_calculator.py # 核心估值计算逻辑
└── README.md             # 本文件
```

## 联系方式

- **作者**: Forest
- **邮箱**: forest@example.com
