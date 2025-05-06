# 当前工作重点

## 项目状态
- **当前阶段:** Web 服务化改造 - Phase 1 (后端 API) 和 Phase 2 (前端基础) 完成。Phase 3 (后端核心估值增强) 主要部分完成。
- **目标:** 将现有 Python 命令行估值工具改造为前后端分离的 Web 应用。
- **技术选型:**
    - 后端: FastAPI
    - 前端: Next.js (App Router, TypeScript, Tailwind CSS)
- **核心架构决策:**
    - 后端 API 提供估值服务。
    - 前端负责用户交互和结果展示。
    - 后端 `DataFetcher` 采用策略模式以支持多市场（A 股、港股等）。

## 最新完成的工作 (后端核心估值增强)
- **`valuation_calculator.py`:**
    - [x] 确认 `get_other_analysis` (股息、增长) 和 `get_combo_valuations` (六种组合、投资建议) 方法已正确实现。
    - [x] 清理了因之前编辑中断导致的重复代码。
- **API 层:**
    - [x] `api/models.py`: 定义了详细的 Pydantic 请求 (`StockValuationRequest` 包含敏感度分析参数) 和响应模型 (`StockValuationResponse` 包含 `ValuationResultsContainer` 以容纳所有计算维度)。
    - [x] `api/main.py`: 更新了 `/api/v1/valuation` 端点逻辑，以调用 `ValuationCalculator` 的所有相关方法，并使用新的模型结构返回详细结果。
- **测试:**
    - [x] `tests/api/test_main.py`: 更新了 API 测试用例，修复了 `test_calculate_valuation_not_found`，并扩展了 `test_calculate_valuation_success` 以覆盖新的 API 响应结构和模拟计算器的输出。
- **调试与修复:**
    - [x] 诊断并修复了 `/api/v1/valuation` 端点调用 `calculator.get_combo_valuations` 时发生的 `TypeError: cannot unpack non-iterable NoneType object`。
    - [x] 根本原因确定为 `valuation_calculator.py` 中存在重复的 `get_combo_valuations` 方法定义，其中重复的方法缺少 `return` 语句，导致隐式返回 `None`。
    - [x] 通过添加和分析调试打印语句逐步定位问题，最终删除了重复的方法定义。
    - [x] 确认 `/api/v1/valuation` 端点现在可以成功返回 200 OK 和完整的估值结果。
    - [x] 清理了在调试过程中添加到 `api/main.py` 和 `valuation_calculator.py` 的所有 `DEBUG:` 打印语句（用于修复 TypeError）。
- **调试与修复 (数值准确性):**
    - [x] 诊断并修复了 PE、EV/EBITDA、派息率异常高的问题。根本原因确定为 `api/main.py` 和 `valuation_calculator.py` 中对 `total_shares` 单位处理不一致（获取的是实际股数，但错误地按万股处理并乘以了 10000）。已修正两处代码。
    - [x] 调查了 DCF (FCFE/FCFF) 估值结果显著偏高的问题。
    - [x] 通过添加 DEBUG 打印，确认高估值主要源于 `_get_growth_rates_for_dcf` 函数中基于历史自由现金流计算出的平均增长率 (`avg_growth`) 因历史数据波动（特别是正负转换）而异常高。
    - [x] 在 `_get_growth_rates_for_dcf` 中添加了增长率上限 (`reasonable_growth_cap = 0.25`) 逻辑，以限制过高的历史平均增长率对未来预测的影响。
    - [x] 修复了添加调试代码时引入的缩进错误。
    - [x] 通过 DEBUG 输出确认增长率上限逻辑已生效。
    - [x] 将 DCF 增长率上限配置移至 `.env` 文件 (`DCF_GROWTH_CAP`)。

## 下一步计划 (当前)
- **后端核心估值逻辑重构 (已完成):**
    - [x] **修改 `valuation_calculator.py` (`get_combo_valuations`):**
        - 移除了相对估值 (PE/PB) 在组合计算中的权重。
        - 实现了新的绝对估值组合定义，使用描述性别名 (如 `FCFE_Basic`, `Avg_FCF_Basic`, `Composite_Valuation` 等) 作为键名，并处理了无效依赖项。每个组合结果现在包含 `value` 和 `safety_margin_pct`。
        - 实现了新的“综合估值”计算逻辑 (FCFE_Basic=40%, 其余有效组合均分60%)。
        - 重构了投资建议逻辑：基于安全边际（使用 FCFE Basic 和 DDM 的最低值计算），并参考 `FCFE_Basic`, `Avg_FCFE_Basic_DDM` 和 `Composite_Valuation`。
    - [x] **修改 `api/models.py` (`ValuationResultsContainer`):** 更新了 `combo_valuations` 字典结构以反映新的别名键和嵌套结构 (`Optional[Dict[str, Optional[Dict[str, Optional[float]]]]]`)。
    - [x] **(已完成)** 从 API 请求模型和端点移除 `dcf_growth_cap` 参数。
- **下一步计划 (潜在方向):**
    - **后端增强:** 进一步优化增长率计算、处理 NaN 值、验证数据获取可靠性。
    - **前端改进:** 美化 `ResultsDisplay` 组件、添加用户反馈、输入验证。
    - 添加更精细的加载状态和错误提示。
    - 实现输入验证。
- **后端增强:**
    - 完善 `DataFetcher` 策略模式，添加对其他市场（如港股）的支持 (`HKDataFetcher`)。
    - 在 `ValuationCalculator` 中实现更多估值模型或完善现有模型（例如，处理 NaN 值）。
    - 添加日志记录。
- **联调与部署:**
    - 进行更全面的端到端测试。
    - 考虑 Docker 化部署。

## 当前决策和考虑事项
- **项目结构:** 后端在根目录，API 在 `api/`；前端在 `frontend/`。
- **数据流:** 前端 (localhost:3000) -> 后端 API (localhost:8124) -> 前端展示。
- **API 响应:** API 现在返回一个包含多种估值模型结果、分析和建议的综合结构 (`ValuationResultsContainer`)。
- **测试:** 后端 API 测试 (`test_calculate_valuation_success`) 现在覆盖了新的响应结构，并且之前失败的 `test_calculate_valuation_not_found` 已修复。
- **资本性支出 (Capex):** 明确区分 Basic Capex (`c_pay_acq_const_fiolta`) 和 Full Capex (`stot_out_inv_act`) 并在 DCF 计算中体现。
- **折现率 (Discount Rate):** 采用计算出的 WACC 作为 DCF 和 DDM 的中心折现率，并进行敏感性分析 (e.g., WACC +/- 1%)，替代原用户输入方式。
- **投资建议:**
    - 基于格雷厄姆的安全边际理念。
    - 安全边际使用 DCF FCFE Basic (X) 和 DDM (D) 的最低估值结果计算。
    - 建议理由需参考 X, B 和综合估值。
- **相对估值:** PE, PB, EV/EBITDA 仅作为参考指标展示，不纳入组合估值加权计算。
- **组合估值:**
    - 定义了新的绝对估值组合，使用描述性别名 (如 `FCFE_Basic`, `Avg_FCF_Basic`, `Composite_Valuation`)。
    - 每个组合结果包含估值 (`value`) 和对应的安全边际 (`safety_margin_pct`)。
    - 最终“综合估值” (`Composite_Valuation`) 采用特定权重：`FCFE_Basic` (40%)，其余有效组合均分 60%。无效组合不参与计算。
- **DCF 增长率上限:** (保持不变) 通过 `.env` 文件中的 `DCF_GROWTH_CAP` 配置，默认为 0.25。
- **现金估算:** (保持不变) 在无法直接获取货币资金时，接受使用占总资产百分比估算 EV 中的现金部分。

## 学习和项目洞察
- 从 CLI 到 Web 服务的转变需要考虑 API 设计、数据序列化、前后端通信和异步处理（FastAPI 天然支持）。
- 提前考虑多市场支持的架构设计能避免未来的大规模重构。
- 准确定义和区分不同类型的资本性支出对 DCF 估值至关重要。
- 使用计算出的 WACC 作为折现率比依赖用户输入更严谨。
- 投资建议需要明确的规则和基于核心估值方法的安全边际判断。
- 详细的 Pydantic 模型对于定义和验证复杂的 API 响应结构非常有帮助。
- Mocking 在测试 FastAPI 端点时至关重要，特别是当涉及到外部依赖（如数据库）或复杂的内部逻辑（如 `ValuationCalculator`）时。
