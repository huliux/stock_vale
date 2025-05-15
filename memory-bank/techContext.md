# 技术上下文 (Vue.js 前端 + FastAPI 后端 - Monorepo)

## 核心技术栈
- **核心语言:** Python 3.10 (后端), TypeScript (前端)
- **前端 GUI 框架:** Vue.js (Vite)
- **前端状态管理:** Pinia
- **前端路由:** Vue Router
- **后端 Web 框架:** FastAPI
- **ASGI 服务器:** Uvicorn (用于运行 FastAPI)
- **数据验证/序列化:** Pydantic (用于 FastAPI)
- **数据库交互:** SQLAlchemy, psycopg2-binary (PostgreSQL)
- **数据处理:** Pandas, NumPy
- **外部数据源:** Tushare Pro (用于股票行情、基本面及财务数据)
- **LLM API 调用:** requests (用于 DeepSeek), openai (用于自定义 OpenAI 兼容模型)
- **环境管理 (后端):** uv (管理虚拟环境和包依赖)
- **环境管理 (前端):** npm (或 yarn/pnpm)
- **配置管理 (后端):** python-dotenv (.env 文件), pyproject.toml (依赖管理), uv.lock (依赖锁定), 配置文件 (用于 Prompt 模板)
- **测试 (后端):** pytest
- **测试 (前端):** Vitest (规划中)
- **代码质量 (后端):** black, ruff, pre-commit (推荐)
- **代码质量 (前端):** ESLint, Prettier (推荐)
- **共享类型:** TypeScript (`packages/shared-types/`)

## 开发环境
- **IDE:** VS Code (配置为Monorepo工作区)
- **版本控制:** Git (采用Monorepo结构，包含 `packages/fastapi-backend`, `packages/vue-frontend`, `packages/shared-types`)

## 关键依赖 (示例)
### 后端 (`packages/fastapi-backend/pyproject.toml`)
- **运行依赖 (部分示例):** fastapi, uvicorn, sqlalchemy, psycopg2-binary, pandas, numpy, pydantic, python-dotenv, httpx, openai, tushare
- **开发依赖 (部分示例):** pytest, black, ruff, pre-commit
### 前端 - Vue.js (`packages/vue-frontend/package.json`)
- **运行依赖 (部分示例):** vue, vue-router, pinia, axios (或 fetch API)
- **开发依赖 (部分示例):** @vitejs/plugin-vue, typescript, eslint, prettier, vitest, @vue/tsconfig
### 共享类型 (`packages/shared-types/package.json`)
- **开发依赖 (部分示例):** typescript
