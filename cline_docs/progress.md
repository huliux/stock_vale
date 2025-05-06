# 当前项目进展

## 项目阶段
- **当前:** Web 服务化改造 - Phase 1 (后端 API) 和 Phase 2 (前端基础) 完成。Phase 3 (后端核心估值增强) 主要部分完成。
- **目标:** 将 CLI 工具转变为前后端分离的 Web 应用。

## 已完成工作
- **环境与配置优化:** (保持不变)
    - 创建了 `.gitignore`。
    - 更新了 `requirements.txt` 添加开发工具。
    - 创建了 `.env.example` 模板。
    - 修改 `data_fetcher.py` 使用 `.env` 加载数据库凭证，硬编码表/字段名。
    - 修改 `main.py` 移除 `config.ini` 依赖。
    - 删除了 `config.ini.example`。
    - 创建并配置了 `.venv` 虚拟环境。
    - 解决了 `psycopg2` 缺失问题。
    - 解决了 `valuation_calculator.py` 中残留的 `config.ini` 读取问题。
- **规则与文档更新:** (保持不变)
    - 更新了 `.clinerules` 目录下的规则文件以适应 Web 服务开发。
    - 更新了 `cline_docs` 记忆库文件以反映新的项目方向和计划。
- **Phase 1: 后端 API 开发 (FastAPI)**
    - [x] 环境设置 (添加 fastapi, uvicorn, httpx 依赖)
    - [x] 创建 API 入口 (`api/main.py`)
    - [x] 重构 `DataFetcher` (定义 BaseDataFetcher, AshareDataFetcher)
    - [x] 定义 API 模型 (Pydantic in `api/models.py`)
    - [x] 创建 `/api/v1/valuation` 端点
    - [x] 实现端点逻辑 (调用 Fetcher, Calculator)
    - [x] 添加 CORS 配置
    - [x] 编写 API 测试 (`tests/api/test_main.py`, 存在一个失败用例)
- **Phase 2: 前端 UI 开发 (Next.js)**
    - [x] 初始化 Next.js 项目 (`frontend/`)
    - [x] 创建页面 (`page.tsx`) 和组件 (`ValuationForm`, `ResultsDisplay`)
    - [x] 实现 API 调用逻辑 (`page.tsx`)
    - [x] 设计和实现基础 UI 样式 (Tailwind CSS in components)
    - [x] 实现加载状态和错误处理 (`page.tsx`)
    - [x] 定义前端类型 (`types/api.ts`)
- **Phase 3: 后端核心估值增强 (主要部分)**
    - [x] **数据获取:** (部分完成) 在 `data_fetcher.py` 中添加了获取 WACC 和 EV 计算所需额外字段的逻辑 (`money_cap`, `lt_borr`, `st_borr`, `bond_payable`, `ebit`, `ebitda`)。
    - [x] **WACC 计算:** 在 `valuation_calculator.py` 中实现 `calculate_wacc` 方法。
    - [x] **估值计算 (`valuation_calculator.py`):**
        - [x] 修复 `calculate_ev` (使用实际数据，处理现金缺失)。
        - [x] 修改 `calculate_fcff_fcfe` 以支持 Basic/Full Capex。
        - [x] 重构 DCF 方法 (重命名, 使用 WACC +/- 1% 作为折现率, 调用正确的 Capex 类型)。
        - [x] 实现 DDM 估值 (`calculate_ddm_valuation`)。
        - [x] 实现其他分析 (`get_other_analysis` - 股息、增长)。
        - [x] 实现综合分析 (`get_combo_valuations` - 六种组合、投资建议规则)。
        - [ ] 处理 NaN 值 (部分完成，需要进一步审查)。
    - [x] **API 层:**
        - [x] `api/models.py`: 定义了完整的请求和响应模型。
        - [x] `api/main.py`: 更新了 API 端点逻辑以调用所有计算并返回新模型。
    - [x] **测试:**
        - [x] `tests/api/test_main.py`: 更新测试用例以覆盖新 API 结构。
        - [x] `tests/api/test_main.py`: 修复了 `test_calculate_valuation_not_found` 失败用例。
    - [x] **配置:** 更新 `.env.example` 添加 WACC 参数 (`DEFAULT_BETA`, `RISK_FREE_RATE`, `MARKET_RISK_PREMIUM`, `DEFAULT_COST_OF_DEBT`)。
    - [x] **调试 (TypeError):** 解决了 `/api/v1/valuation` 端点因重复方法定义导致的 `TypeError`。
    - [x] **调试 (数值准确性):**
        - [x] 修复了 PE, EV/EBITDA, Payout Ratio 异常高的问题 (修正 `total_shares` 单位处理)。
        - [x] 调查并确认 DCF 估值偏高源于历史自由现金流波动导致的增长率计算问题。
        - [x] 在 `_get_growth_rates_for_dcf` 中添加增长率上限 (25%) 逻辑。
        - [x] 修复了添加调试代码时引入的缩进错误。
        - [x] 确认增长率上限逻辑已生效。
        - [x] 将 DCF 增长率上限配置移至 `.env` 文件。

## 剩余任务 (Web 服务开发)
- **Phase 3: 后端核心估值增强 (当前)**
    - [x] **重构估值组合与建议 (`valuation_calculator.py`, `api/models.py`):**
        - 移除了相对估值在组合计算中的权重。
        - 实现了新的绝对估值组合，使用描述性别名，并为每个组合计算了安全边际百分比，存储在嵌套字典中 (`{'value': ..., 'safety_margin_pct': ...}`)。
        - 实现了新的“综合估值” (`Composite_Valuation`) 加权计算 (FCFE_Basic=40%, 其他均分60%)。
        - 重构了投资建议逻辑 (基于安全边际 - FCFE Basic & DDM，参考 FCFE_Basic, Avg_FCFE_Basic_DDM, Composite_Valuation)。
        - 更新了 API 模型以反映新的组合结构（包含安全边际）和别名。
    - [ ] **估值计算 (`valuation_calculator.py`):** 进一步审查和处理潜在的 NaN 值问题。
    - [ ] **数据获取:** 验证 WACC/EV 所需字段是否总能可靠获取，考虑备用方案。
    - [ ] **DCF 增长率优化 (可选):** 考虑更稳健的历史增长率计算方法。
- **Phase 3/4: 其他改进与增强 (后续)**
    - [ ] **前端:** 美化 `ResultsDisplay` 样式和布局以展示更丰富的数据（包括新的组合和参考信息）。
    - [ ] **前端:** 添加更精细的用户反馈 (e.g., Toast 通知)。
    - [ ] **前端:** 实现输入验证。
    - [ ] **后端:** 完善 `DataFetcher` 策略模式 (e.g., 添加 `HKDataFetcher`)。
    - [ ] **后端:** 添加日志记录。
- **Phase 4: 联调与部署准备 (后续)**
    - [ ] 前后端联调测试 (更全面)。
    - [ ] (可选) Docker化。

## 当前状态
- 后端 API (FastAPI) 和基础前端 (Next.js) 已开发完成并可运行。
- 后端核心估值逻辑已增强，API 现在可以返回包含多种模型、分析和建议的详细结果。
- 前端可以调用后端 API 获取并展示**增强后**的估值结果（但前端展示尚未更新以匹配新数据结构）。
- 项目结构符合预期 (`api/`, `frontend/`, `tests/` 等)。
- API 测试已更新并通过。
- `/api/v1/valuation` 端点现在可以成功返回 200 OK 和完整的估值结果，PE/EV/Payout Ratio 数值已修正。
- DCF 估值中基于历史数据的增长率计算已加入上限限制 (25%)。
- **下一步:** 验证增长率上限对 DCF 结果的影响，继续 Phase 3 的收尾工作（NaN 值处理）或开始其他改进。

## 已知问题
- 应用增长率上限后的 DCF 估值结果的合理性有待验证。
- 估值计算中可能仍存在未完全处理的 `nan` 值问题 (待审查)。
- 前端 `ResultsDisplay` 组件尚未更新以展示 API 返回的全部详细信息。

## 决策演变
- 确定了向前后端分离的 Web 服务架构演进的方向。
- 选定了 FastAPI (后端) 和 Next.js (前端) 作为核心技术栈。
- 确定了通过策略模式支持多市场数据源的架构方案。
- **明确了资本性支出 (Capex) 的区分:** Basic Capex (`c_pay_acq_const_fiolta`) 和 Full Capex (`stot_out_inv_act`)。
- **确定了折现率方案:** 计算 WACC 并将其作为 DCF/DDM 的中心折现率，进行敏感性分析。
- **确定了投资建议逻辑:** 基于安全边际 (使用 FCFE Basic 和 DDM 最低值计算)，并参考 `FCFE_Basic`, `Avg_FCFE_Basic_DDM` 和 `Composite_Valuation`。
- **确定了相对估值处理:** 仅作参考，不纳入组合加权。
- **确定了新的组合估值体系:** 定义了使用描述性别名的组合（每个组合包含 `value` 和 `safety_margin_pct`）及最终综合估值的加权方法。
- **接受了 EV 计算中的现金估算** (在无法获取精确数据时)。
- **识别了 DCF 历史增长率计算的敏感性问题** 并引入了基于 `.env` 配置的上限限制。
