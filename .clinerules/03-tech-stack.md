# 技术栈指南 (stock_vale 项目)

## 简要概述
本文档定义了 `stock_vale` 项目（Web 服务化改造后）使用的核心技术和库。

## 后端 (Python)

### 核心语言
- **Python 3.x**: 后端主要编程语言。

### 主要库与框架
- **FastAPI**: 高性能 Web 框架，用于构建 API。
- **Uvicorn**: ASGI 服务器，用于运行 FastAPI 应用。
- **Pydantic**: 用于数据验证和 API 模型定义。
- **SQLAlchemy**: 用于与数据库进行交互。
- **psycopg2-binary**: PostgreSQL 数据库驱动。
- **Pandas**: 用于数据处理和分析。
- **NumPy**: 用于数值计算。
- **python-dotenv**: 用于加载 `.env` 文件。

## 前端 (TypeScript)

### 核心语言与框架
- **TypeScript**: 前端主要编程语言。
- **React**: UI 库。
- **Next.js (App Router)**: React 框架，用于构建应用和路由。

### 主要库与工具
- **Tailwind CSS**: 原子化 CSS 框架，用于样式设计。
- **npm / yarn**: 包管理器（根据项目初始化选择）。
- **axios / fetch**: 用于向后端 API 发送请求。

## 通用开发工具
- **Git**: 版本控制。
- **VS Code**: 首选的代码编辑器。
- **venv**: Python 虚拟环境管理。
- **pip**: Python 包管理。
- **pytest**: Python 后端测试框架。
- **black**: Python 代码格式化。
- **flake8**: Python 代码风格检查。
- **pre-commit**: (推荐) Git 钩子管理。
