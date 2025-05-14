# 技术上下文 (Streamlit 应用 + FastAPI 后端)

## 核心技术栈
- **核心语言:** Python 3.10 (后端)
- **GUI 框架:** Streamlit (当前/旧前端), Vue.js (新前端 - 规划中)
- **后端 Web 框架:** FastAPI
- **ASGI 服务器:** Uvicorn (用于运行 FastAPI)
- **数据验证/序列化:** Pydantic (用于 FastAPI)
- **数据库交互:** SQLAlchemy, psycopg2-binary (PostgreSQL)
- **数据处理:** Pandas, NumPy
- **外部数据源:** Tushare Pro (用于股票行情、基本面及财务数据)
- **LLM API 调用:** requests (用于 DeepSeek), openai (用于自定义 OpenAI 兼容模型)
- **环境管理 (后端):** uv (管理虚拟环境和包依赖)
- **配置管理 (后端):** python-dotenv (.env 文件), pyproject.toml (依赖管理), uv.lock (依赖锁定), 配置文件 (用于 Prompt 模板)
- **测试:** pytest
- **代码质量:** black, flake8, ruff, pre-commit (推荐)

## 开发环境
- **IDE:** VS Code (配置为Monorepo工作区)
- **版本控制:** Git (采用Monorepo结构，包含 `packages/fastapi-backend`, `packages/vue-frontend`, `packages/shared-types`)

## 关键依赖 (示例)
### 后端 (`packages/fastapi-backend/pyproject.toml`)
- **运行依赖 (部分示例):** fastapi, uvicorn, sqlalchemy, psycopg2-binary, pandas, numpy, pydantic, python-dotenv, httpx, openai, tushare
- **开发依赖 (部分示例):** pytest, black, flake8, ruff, pre-commit
### 前端 - Streamlit (当前/旧 - `streamlit_app.py` 等根目录文件)
- **运行依赖:** streamlit, pandas, numpy, httpx (调用后端API)
### 前端 - Vue.js (新 - `packages/vue-frontend/package.json` - 规划中)
- **运行依赖 (预期示例):** vue, vue-router, pinia, axios (或 fetch)
- **开发依赖 (预期示例):** @vitejs/plugin-vue, typescript, eslint, prettier, vitest
