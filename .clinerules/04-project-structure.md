# 项目结构指南 (stock_vale 项目)

## 简要概述
本文档定义了 `stock_vale` 项目推荐的文件和目录结构。

## 核心目录与文件
- **`/` (根目录)**:
    - `main.py`: 项目主入口点。
    - `data_fetcher.py`: 负责数据获取逻辑。
    - `valuation_calculator.py`: 包含核心估值计算逻辑。
    - `report_generator.py`: 协调报告生成过程。
    - `requirements.txt`: 项目依赖列表。
    - `config.ini.example`: 配置文件模板，实际配置应使用 `config.ini` (不提交到版本库)。
    - `.env.example`: 环境变量模板（如果使用 .env）。
    - `README.md`: 项目说明文档。
    - `.gitignore`: 定义版本控制忽略规则。
    - `pytest.ini` (可选): pytest 配置文件。
    - `.pre-commit-config.yaml` (可选): pre-commit 配置文件。
- **`/generators/`**:
    - 包含不同格式报告的具体生成器类（例如 `html_report_generator.py`, `markdown_report_generator.py`）。
    - 应包含一个 `base_report_generator.py` 作为基类。
- **`/models/`**:
    - 定义项目中使用的数据结构或数据类（例如 `stock_data.py`）。
- **`/utils/`**:
    - 存放可重用的工具函数（例如 `report_utils.py`）。
- **`/reports/`**:
    - 存放生成的估值报告文件。此目录通常不提交到版本库。
- **`/cline_docs/`**:
    - 存放与 Cline 交互相关的文档（记忆库文件）。
- **`/tests/`**:
    - 存放单元测试和集成测试代码。

## 命名约定
- **文件名**: 使用小写字母和下划线 (`snake_case`)，例如 `data_fetcher.py`。
- **类名**: 使用大驼峰命名法 (`PascalCase`)，例如 `HtmlReportGenerator`。
- **函数/方法名**: 使用小写字母和下划线 (`snake_case`)，例如 `calculate_dcf_valuation`。
- **变量名**: 使用小写字母和下划线 (`snake_case`)。
