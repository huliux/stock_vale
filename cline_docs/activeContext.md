# 当前活动上下文：项目重大改版规划完成 - 转向 Streamlit 和 LLM 集成

## 背景
在完成 DCF 估值逻辑优化第一阶段（提升预测精细度）后，与用户进行了深入讨论，确定了项目新的发展方向和技术栈。

## 新的核心决策 (已确认)
1.  **业务逻辑聚焦:**
    *   以 `wiki/` 目录下文档定义的最新 DCF 估值逻辑为绝对核心。
    *   删除旧的 DCF 估值逻辑和估值组合逻辑 (`get_combo_valuations` 方法将移除或重构)。
    *   PE、PB 等其他估值方法仅作为辅助参考信息展示。
    *   最终的投资建议将利用大语言模型 (LLM) 对各项结果进行综合分析后生成。
2.  **技术栈调整:**
    *   **前端:** 废弃并删除原有的 Next.js 前端 (`frontend/` 目录)。采用 **Streamlit** 构建新的 GUI。
    *   **后端:** 保留 FastAPI 后端，继续提供 JSON 数据接口，但需重构和增强。
    *   **报告:** 移除旧的非 JSON 报告生成器 (`generators/` 目录)。所有结果通过 Streamlit 展示。
3.  **LLM 集成:**
    *   后端 API 负责收集数据、构建 Prompt (模板来自配置文件)、调用外部 LLM 服务（支持 Gemini, OpenAI, Anthropic, DeepSeek，通过 `.env` 配置），并将分析摘要返回。
4.  **代码结构优化:**
    *   后端 DCF 核心计算逻辑将从 `valuation_calculator.py` 拆分到更小、职责更单一的模块 (`wacc_calculator.py`, `terminal_value_calculator.py`, `present_value_calculator.py`, `equity_bridge_calculator.py`, `fcf_calculator.py`, `nwc_calculator.py`)。
5.  **预测逻辑简化:**
    *   用户在界面上主要选择预测模式（使用历史中位数 vs. 过渡到目标值），而非强制输入所有目标值。系统自动计算历史中位数。
6.  **数据处理:**
    *   `DataProcessor` 负责计算历史中位数，处理缺失值 (NULL->0, 跳过无效期, 记录警告)，提取基本信息和最新 PE/PB。

## 当前状态
-   项目处于**执行模式 (ACT MODE)**。
-   已完成新方向的规划和任务梳理。
-   已完成**阶段一：清理与准备** (删除 `frontend/` 和 `generators/` 目录)。
-   已完成**阶段二：后端重构与增强**：
    *   DCF 计算逻辑模块化完成。
    *   `DataProcessor` 和 `FinancialForecaster` 功能增强完成（包括历史中位数、CAGR、预测模式等）。
    *   API 接口 (`api/main.py`, `api/models.py`) 已更新，调用新模块，调整响应结构（包含详细预测表），并集成了 LLM 调用逻辑（当前配置为 DeepSeek）。
    *   依赖 (`requirements.txt`) 和配置 (`.env.example`, `config/llm_prompt_template.md`) 已更新。
-   已完成**阶段三：Streamlit UI 开发与调试**：
    *   创建了 `streamlit_app.py`，包含输入控件、API 调用逻辑和结果展示区（包括基本信息、DCF结果、详细预测表、LLM摘要）。
    *   解决了 Streamlit 布局错误 (`StreamlitAPIException`)，实现了两列布局。
    *   添加了投资建议引导说明和情景分析占位符。
-   已完成**阶段一：清理与准备**：删除了旧的前端和报告生成器代码，以及部分重构后不再需要的 Python 文件。
-   **调试:**
    *   解决了多轮测试中发现的 `TypeError` (float/Decimal), `AttributeError`, `IndentationError`, `KeyError` 等问题。
    *   解决了总股本单位错误，使每股价值计算合理。
    *   确认 PE/PB 数据源为 `valuation_metrics` 表，并更新了 `DataFetcher`。
    *   确认 LLM (DeepSeek) API 调用成功。
-   **单元测试修复 (当前工作):**
    *   系统地运行了 `pytest` 并识别出重构后各模块（API, DataProcessor, Calculators）中的 20 个单元测试失败。
    *   逐一分析并修复了所有失败的测试用例，主要涉及：
        *   类型错误 (`Decimal` vs `float`, `numpy.int64` vs `Decimal`)。
        *   `pytest.approx` 与 `Decimal` 的兼容性问题。
        *   `NaN` 值处理逻辑。
        *   异常处理逻辑（确保 `try-except` 块覆盖范围正确）。
        *   测试断言与代码实际输出（包括错误消息、计算结果）的不匹配。
        *   测试 fixture 或测试用例本身逻辑与被测代码不一致。
    *   修改的文件包括所有 `tests/test_*.py` 文件以及对应的计算器模块 (`equity_bridge_calculator.py`, `fcf_calculator.py`, `financial_forecaster.py`, `present_value_calculator.py`, `terminal_value_calculator.py`, `wacc_calculator.py`)。
    *   最终运行 `pytest` 确认所有 85 个测试全部通过。
-   **WACC 权重模式实现 (进行中):**
    *   根据用户要求，增加了 WACC 计算的灵活性。
    *   修改了 `wacc_calculator.py`，允许根据 `wacc_weight_mode` 参数选择使用“目标债务比例”或“最新市场价值权重”来计算 WACC。
        *   修改了 `api/models.py` 和 `api/main.py` 以支持新的 `wacc_weight_mode` 参数传递。
        *   修改了 `streamlit_app.py`，添加了前端 UI 选项来控制 WACC 权重模式，并动态调整“目标债务比例”输入框的可用性。
    *   **测试通过:** 用户已确认 WACC 权重模式功能符合预期。
-   **敏感性分析功能实现 (已完成，待测试):**
    *   **后端:** 创建了 `api/sensitivity_models.py` 定义相关模型。修改了 `api/models.py` 引入新模型。重构了 `api/main.py`，封装了核心估值逻辑，并添加了处理敏感性分析请求、执行循环计算、返回二维结果表的逻辑。
    *   **前端:** 修改了 `streamlit_app.py`，在主页面添加了敏感性分析配置区域（轴选择、步长/点数输入、自动生成可编辑的值列表），并添加了展示二维结果表格的逻辑。
-   **应用状态:** 当前应用已包含敏感性分析的基础功能（后端计算逻辑和前端配置/展示框架）。单元测试和集成测试尚未针对此功能更新。存在已知的数据警告。

## 当前目标
-   **测试敏感性分析功能:** 需要用户在 Streamlit UI 上测试新添加的敏感性分析功能，包括：
    *   UI 交互是否流畅（参数选择、值列表生成与编辑）。
    *   启用分析后，后端计算是否能正常完成并返回结果。
    *   结果表格是否能正确显示。
    *   不同轴参数组合下的计算结果是否符合预期。
-   **更新记忆库:** (已完成) 更新文档以反映敏感性分析功能的实现。

## 后续步骤 (优先级排序)
0.  **严格遵循规范:** **所有开发和修复工作必须严格遵循 `wiki/` 目录下的 PRD 和数据定义文档。**
1.  **测试敏感性分析功能 (当前):** 用户手动测试。
2.  **添加敏感性分析测试:** (后续任务) 补充后端单元测试和 API 集成测试。
3.  **完善 Streamlit UI:** (可选，可放入新任务) 根据测试结果和用户反馈，优化布局（特别是右侧LLM区域）、交互和错误处理，包括敏感性分析部分的细节（如中心值高亮）。
3.  **优化投资建议呈现:** (可选，可放入新任务) 调整 Prompt 或解析 LLM 输出，提供更明确的投资评级。
4.  **规则文件更新:** (可选) 检查并更新 `.clinerules/`。
