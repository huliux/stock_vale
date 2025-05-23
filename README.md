# StockVale - 专业股票估值分析系统

## 项目概述
StockVale是一个专业的股票估值分析系统，基于Vue.js + FastAPI + LLM技术栈构建，提供全面的股票筛选、DCF估值计算、敏感性分析和深度研究工具。系统采用现代化的前端界面和模块化的后端架构，支持多市场数据源和可扩展的估值模型。

## 主要功能
- **股票筛选器**：基于PE、PB、市值等指标筛选股票，支持多种视图模式
- **DCF估值模型**：专业的现金流折现估值计算，包含详细的财务预测和敏感性分析
- **敏感性分析**：基于WACC和退出乘数的双维度敏感性分析，直观展示估值范围
- **深度研究**：利用LLM技术提供投资建议和深度分析报告
- **多种视图模式**：表格、卡片和图表多种方式展示数据和结果
- **数据导出**：支持CSV格式导出筛选和估值结果

## 系统架构
项目采用Monorepo结构组织代码，包含三个主要包：

```
stock_vale/
├── packages/
│   ├── vue-frontend/      # Vue.js 3 + TypeScript + Tailwind CSS 前端
│   ├── fastapi-backend/   # FastAPI + Python 后端
│   └── shared-types/      # 共享TypeScript类型定义
└── ...
```

### 技术栈
- **前端**：Vue 3 + TypeScript + Vite + Pinia + Vue Router + Tailwind CSS + shadcn-vue
- **后端**：FastAPI + Python + Tushare API
- **LLM集成**：支持DeepSeek和自定义OpenAI兼容模型

### 核心组件
- **前端**：
  - `DcfValuationView.vue`：DCF估值主视图
  - `StockScreenerView.vue`：股票筛选器视图
  - `DcfParametersForm.vue`：估值参数表单
  - `DcfResultsDisplay.vue`：估值结果展示
  - `StockScreenerResultsTable.vue`：筛选结果表格
  - `SensitivityHeatmap.vue`：敏感性分析热图

- **后端**：
  - `data_processor.py`：数据处理核心
  - `financial_forecaster.py`：财务预测模块
  - `fcf_calculator.py`：自由现金流计算
  - `terminal_value_calculator.py`：终值计算
  - `present_value_calculator.py`：现值计算
  - `wacc_calculator.py`：加权平均资本成本计算
  - `stock_screener_service.py`：股票筛选服务

## 快速开始

### 环境要求
- Node.js 18+
- Python 3.10+
- Docker & Docker Compose (可选)

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/stock_vale.git
cd stock_vale
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，填入必要的API密钥和配置
```

3. 安装uv（Python包管理工具）：
```bash
# 使用pip安装uv
pip install uv

# 或者使用curl安装（Linux/macOS）
curl -sSf https://install.python-poetry.org | python3 -

# 或者使用PowerShell安装（Windows）
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

4. 创建并激活Python虚拟环境：
```bash
# 进入后端目录
cd packages/fastapi-backend

# 使用uv创建虚拟环境
uv venv .venv

# 激活虚拟环境（Linux/macOS）
source .venv/bin/activate

# 激活虚拟环境（Windows）
.venv\Scripts\activate
```

5. 安装依赖：

**使用Docker (推荐)**
```bash
docker-compose up
```

**手动安装**
```bash
# 安装前端依赖
cd packages/vue-frontend
npm install

# 安装后端依赖
cd ../fastapi-backend
uv pip install -r requirements.txt
```

4. 启动服务：

**使用Docker**
```bash
# 已在docker-compose up步骤中启动
```

**手动启动**
```bash
# 启动前端开发服务器
cd packages/vue-frontend
npm run dev

# 启动后端API服务
cd ../fastapi-backend
uvicorn api.main:app --host 0.0.0.0 --port 8125 --reload
```

5. 访问应用：
   - 前端: http://localhost:5173
   - 后端API: http://localhost:8125/docs

## 使用指南

### 股票筛选
1. 导航至"股票筛选"页面
2. 设置筛选条件（PE、PB、市值等）
3. 点击"筛选"按钮获取结果
4. 切换不同视图模式（表格/卡片/图表）查看结果
5. 可选择导出结果或进行批量估值

### DCF估值
1. 导航至"绝对估值"页面
2. 输入股票代码并选择市场
3. 设置估值参数（预测期、增长率、折现率等）
4. 点击"计算"按钮获取估值结果
5. 查看详细的财务预测、现金流折现和敏感性分析结果

### 深度研究
1. 导航至"深度研究"页面
2. 输入股票代码并选择研究主题
3. 系统将调用LLM生成深度分析报告
4. 查看包含投资建议、风险分析和行业对比的研究报告

## 开发指南

### 前端开发
```bash
cd packages/vue-frontend
npm run dev        # 启动开发服务器
npm run build      # 构建生产版本
npm run test:unit  # 运行单元测试
npm run lint       # 运行代码检查
```

### 后端开发
```bash
cd packages/fastapi-backend
uvicorn api.main:app --reload  # 启动开发服务器
pytest                         # 运行测试
```

### 项目结构
- `packages/vue-frontend/src/components/` - Vue组件
- `packages/vue-frontend/src/views/` - 页面视图
- `packages/vue-frontend/src/stores/` - Pinia状态管理
- `packages/vue-frontend/src/services/` - API服务
- `packages/fastapi-backend/api/` - FastAPI应用
- `packages/fastapi-backend/services/` - 业务服务
- `packages/shared-types/src/` - 共享类型定义

## 贡献指南
1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

