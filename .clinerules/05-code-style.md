# 代码风格指南 (stock_vale 项目)

## 简要概述
本文档定义了 `stock_vale` 项目推荐的代码编写风格，旨在提高代码的可读性和可维护性。

## 后端 (Python)

### 核心规范
- **PEP 8**: 严格遵循 [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)。
- **代码格式化与检查**:
    - 使用 `black` 统一代码格式。
    - 使用 `flake8` 进行代码风格和潜在错误检查。
    - 强烈推荐配置 `pre-commit` 钩子，在提交前自动运行 `black` 和 `flake8`。
- **类型注解 (Type Hints)**: 必须为所有函数、方法参数和返回值添加类型注解 (PEP 484)。这有助于静态分析和提高代码清晰度。
    ```python
    def calculate_valuation(data: pd.DataFrame, discount_rate: float) -> dict[str, float]:
        # ... implementation ...
        return results
    ```
- **文档字符串 (Docstrings)**: 为所有模块、类、函数和方法编写清晰的文档字符串 (PEP 257)。推荐使用 Google 或 NumPy 风格的文档字符串。
    ```python
    def fetch_stock_data(symbol: str) -> pd.DataFrame:
        """Fetches historical stock data for a given symbol.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            A pandas DataFrame containing the historical stock data.
        """
        # ... implementation ...
    ```
- **命名约定**: 遵循 `.clinerules/04-project-structure.md` 中定义的命名约定（`snake_case` 用于变量/函数/文件名，`PascalCase` 用于类名）。
- **导入 (Imports)**:
    - 导入应分组：标准库、第三方库、本项目模块。
    - 每个导入语句单独一行。
    - 避免使用 `from module import *`。
- **注释**: 使用 `#` 进行行内注释，解释复杂或不直观的代码段。避免冗余注释。
- **代码行长度**: 建议每行不超过 88-100 个字符，以提高可读性。
- **数据类**: 优先使用 Pydantic 模型定义 API 请求/响应和内部数据结构。对于非 API 数据结构，可考虑 `dataclasses`。
- **金融计算**: 涉及精确金融计算时，使用 `decimal` 模块代替浮点数 (`float`) 以避免精度问题。
- **配置管理**:
    - 优先使用 `python-dotenv` 加载 `.env` 文件中的环境变量来管理配置（特别是敏感信息）。

### FastAPI & Pydantic 特定规范
- **路由函数**: 使用清晰、描述性的名称，参数和响应体必须使用 Pydantic 模型和类型提示。
- **Pydantic 模型**: 字段名使用 `snake_case`，并提供明确的类型注解。考虑添加 `Field` 进行验证或提供示例。

## 前端 (TypeScript/React)

### 核心规范
- **命名约定**:
    - **组件**: 使用 **PascalCase** (例如，`ValuationForm`, `ResultsCard`)。
    - **函数/变量**: 使用 **camelCase** (例如，`fetchValuation`, `isLoading`)。
    - **常量**: 使用 **UPPER_SNAKE_CASE** (例如，`API_ENDPOINT`)。
    - **类型/接口**: 使用 **PascalCase** (例如，`ValuationResponse`, `StockInfo`)。
- **组件类型**: 优先使用**函数式组件**和**箭头函数**语法。
- **状态管理**: 优先使用 React Hooks (`useState`, `useEffect`, `useContext`)。
- **TypeScript**: 充分利用 TypeScript 的类型系统，为 props、状态、函数参数和返回值添加明确的类型。避免使用 `any` 类型。
- **代码格式化**: (推荐) 使用 Prettier 或类似的工具统一代码格式。
- **错误处理**: 在 API 调用和用户交互中实现健壮的错误处理逻辑。
