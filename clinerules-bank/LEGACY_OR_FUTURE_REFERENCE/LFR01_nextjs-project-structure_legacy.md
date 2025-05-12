# 项目结构指南 (stock_vale 项目 - Web 服务化)

## 简要概述
本文档定义了 `stock_vale` 项目在进行前后端分离改造后的推荐文件和目录结构。
**注意：此结构主要针对设想中的 Next.js 前端，当前 `stock_vale` 项目已转向 Streamlit 前端。此文档作为历史参考或未来可能的技术选型参考。**

## 整体结构
- **`/` (根目录)**: 包含后端代码、配置文件和通用文档。
- **`/frontend/`**: 包含前端 Next.js 应用代码。

## 后端 (根目录或 `/backend/`)

- **`/api/`** (推荐):
    - `main.py`: FastAPI 应用入口点。
    - `routers/`: 存放 API 路由模块 (例如 `valuation.py`)。
    - `models.py`: 存放 Pydantic 请求/响应模型。
    - `services.py`: (可选) 存放业务逻辑服务层。
- **`/core/`** (或保留在根目录):
    - `data_fetcher.py`: 数据获取逻辑 (可能包含 `AshareDataFetcher`, `HKshareDataFetcher` 等)。
    - `valuation_calculator.py`: 核心估值计算逻辑。
    - `report_generator.py`: (可能不再直接需要，或转为生成 JSON 数据的辅助类)。
- **`/models/`**:
    - `stock_data.py`: (可能被 Pydantic 模型替代或共存) 定义内部数据结构。
- **`/utils/`**:
    - 存放可重用的工具函数。
- **`/tests/`**:
    - 存放后端单元测试和集成测试代码。
- **`requirements.txt`**: Python 运行依赖。
- **`requirements-dev.txt`** (推荐): Python 开发依赖。
- **`.env.example`**: 环境变量模板。
- **`.gitignore`**: Git 忽略规则。
- **`README.md`**: 项目说明。
- **`pytest.ini`** (可选): pytest 配置。
- **`.pre-commit-config.yaml`** (可选): pre-commit 配置。

## 前端 (`/frontend/`)

- **`/src/app/`**: Next.js App Router 核心目录。
    - `page.tsx`: 应用主页面。
    - `layout.tsx`: 应用根布局。
    - `globals.css`: 全局 CSS (用于 Tailwind 指令)。
    - `api/`: (可选) Next.js API 路由 (如果前端需要自己的简单后端逻辑)。
    - `(routes)/`: 其他页面路由目录。
- **`/src/components/`**: 可重用 React 组件。
    - `ui/`: 通用 UI 组件 (Button, Input, Card)。
    - `features/`: 特定功能组件 (e.g., `valuation/ValuationForm.tsx`)。
- **`/src/lib/`** 或 **`/src/utils/`**: 前端工具函数。
- **`/src/services/`** (可选): API 调用服务。
- **`/src/types/`**: TypeScript 类型定义。
- **`/public/`**: 静态资源 (图片, 字体)。
- **`tailwind.config.ts`**: Tailwind CSS 配置文件。
- **`tsconfig.json`**: TypeScript 配置文件。
- **`package.json`**: Node.js 项目配置和依赖。
- **`yarn.lock`** 或 **`package-lock.json`**: 包管理器锁文件。
- **`.gitignore`**: 前端特定的 Git 忽略规则 (通常 Next.js 会自动生成)。
- **`next.config.mjs`**: Next.js 配置文件。

## 命名约定 (保持不变)
- **Python 文件名/变量/函数**: `snake_case`。
- **Python 类名**: `PascalCase`。
- **TypeScript/React 组件/类型**: `PascalCase`。
- **TypeScript/React 函数/变量**: `camelCase`。
