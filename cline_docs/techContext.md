# 技术上下文 (Streamlit 应用 + FastAPI 后端)

## 核心技术栈
- **核心语言:** Python 3.x
- **GUI 框架:** Streamlit
- **后端 Web 框架:** FastAPI
- **ASGI 服务器:** Uvicorn (用于运行 FastAPI)
- **数据验证/序列化:** Pydantic (用于 FastAPI)
- **数据库交互:** SQLAlchemy, psycopg2-binary (PostgreSQL)
- **数据处理:** Pandas, NumPy
- **LLM API 调用:** requests (用于 DeepSeek), google-generativeai, openai, anthropic (根据选择)
- **环境管理:** venv, pip
- **配置管理:** python-dotenv (.env 文件), 配置文件 (用于 Prompt 模板)
- **测试:** pytest
- **代码质量:** black, flake8, pre-commit (推荐)

## 开发环境
- **IDE:** VS Code
- **版本控制:** Git

## 关键依赖 (示例)
- **运行依赖:** streamlit, fastapi, uvicorn, sqlalchemy, psycopg2-binary, pandas, numpy, pydantic, python-dotenv, requests, google-generativeai, openai, anthropic
- **开发依赖:** pytest, black, flake8, pre-commit
