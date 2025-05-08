好的，我将根据提供的数据库结构和之前的讨论，详细检查并补充 PRD 中可能遗漏的功能和数据点，特别是关于数据获取、处理逻辑的细节，并纠正 Equity Value 计算中的一个潜在偏差。

以下是基于您的数据库 Schema 并考虑了更精细的数据处理和计算逻辑后的 PRD 更新。重点补充和修正了数据来源映射、计算公式细节、潜在的数据处理场景，并明确了 Equity Value 中“债务”的口径。

---

**DCF 估值脚本产品需求文档 (PRD) - 更新版 (详细检查与补充)**

**1. 引言**

本文档详细描述了一个基于数据库数据的DCF（现金流折现法）估值Python脚本的需求。该脚本旨在通过获取历史财务数据和市场数据，预测公司未来的自由现金流（Free Cash Flow, FCF），将其折现至当前时点，加上终值（代表预测期后的价值）的现值，从而得出公司的企业价值和股权价值，最终计算出隐含的股票价格。核心数据来源于预设的数据库结构，包括资产负债表、现金流量表、利润表、股票基本信息表以及其他必要的市场数据表。本方案将严格遵循附件中提供的DCF估值逻辑、计算顺序和公式定义，并使用已明确的数据库字段名称进行描述。

**2. 目标**

* 实现一套准确、可靠、可追溯数据来源的DCF估值计算流程。
* 利用现有数据库中的标准化财务数据和市场数据进行历史分析和未来预测。
* 提供清晰的估值结果，包括预测期FCF、WACC、终值、企业价值、股权价值和隐含股票价格。
* 支持用户输入关键预测假设和估值参数（如预测期、增长率、利润率、资本结构、退出乘数、无风险利率、市场风险溢价等），以进行敏感性分析。
* 模块化设计，便于开发、测试和维护。
* 输出结构化、易于理解的估值报告。

**3. 用户故事**

* 作为一个财务分析师，我希望能够输入公司代码和估值基准日期，脚本能自动从数据库获取历史数据，应用预设或自定义的预测假设，并进行完整的DCF估值计算，输出最终估值结果和关键中间过程的报告。
* 作为一个投资者，我希望能够调整关键的预测假设（如销售增长率、目标利润率、WACC、退出乘数），以便了解这些假设对公司估值的影响，并在报告中清晰展示。
* 作为一个研究员，我希望脚本能输出详细的计算过程、中间结果（如预测期财务报表关键项、每期FCF、贴现因子、各项现值）以及数据来源，以便我验证模型的逻辑和数据。

**4. 功能需求与模块设计**

核心思路：利用数据库作为数据源，通过结构化查询获取历史财务数据和股票信息，经过数据处理后，输入到DCF模型的各个计算模块进行预测和估值。

**4.1 数据库连接和数据查询模块 (`database_manager.py`)**

* **功能：** 负责建立与预设数据库的连接，执行SQL查询获取估值所需的所有历史数据和最新市场数据。
* **数据源：** 使用用户提供的 `balance_sheet`, `cash_flow`, `income_statement`, 和 `valuation_metrics` 表结构。**潜在数据源遗漏：** 需要确定无风险利率和市场风险溢价的数据来源。如果数据库中没有单独的表，则需要将它们明确为用户输入参数，并在PRD中说明。
* **输入：** 股票代码（`ts_code`），估值基准日期，需要查询的历史年数。
* **输出：** 结构化的历史财务数据（如 pandas DataFrame），包含所需的科目明细和日期/报告期信息。应能获取至少过去 N 年的年度数据（`report_type='ANN'`）以及在估值基准日或之前距离最近的一个报告期（通常是年度报告，`report_type='ANN'`）的财务数据和最新的市场数据（根据估值基准日查找最近的 `trade_date`）。报告期类型 (`end_type`) 应优先选择合并报表 ('归母')，如果不可得，需要有备选逻辑或报错提示。
* **关键查询字段映射：**
    * **`balance_sheet` (历史及最新):** `ts_code`, `end_date`, `total_cur_assets` (流动资产合计), `money_cap` (货币资金), `total_cur_liab` (流动负债合计), `short_loan` (短期借款), `non_cur_liab_due_1y` (一年内到期的非流动负债), `long_borr` (长期借款), `bond_payable` (应付债券), `minority_int` (少数股东权益), `total_share` (期末总股本 - *注意：用于历史 NWC 计算，最终股本以 valuation_metrics 为准*), `total_liab` (负债合计 - *注意：此字段用于总负债概念，但 Equity Value 调整通常使用附息债务，需在处理模块明确*), `oth_eqt_tools_p_shr` (其他权益工具(优先股) - 如果需要考虑优先股)。
    * **`cash_flow` (历史):** `ts_code`, `end_date`, `depr_fa_coga_dpba` (固定资产折旧、油气资产折耗、生产性生物资产折旧), `amort_intang_assets` (无形资产摊销), `use_right_asset_dep` (使用权资产折旧 - 新准则，也计入 D&A), `c_pay_acq_const_fiolta` (购建固定资产、无形资产和其他长期资产支付的现金 - Capex), `c_cash_equ_end_period` (期末现金及现金等价物余额 - *可用于现金校验或作为 money_cap 的备选*)。
    * **`income_statement` (历史):** `ts_code`, `end_date`, `revenue` (营业收入), `operate_profit` (营业利润), `income_tax` (所得税费用), `total_profit` (利润总额 - 用于税率计算基础), `ebitda` (息税折旧摊销前利润 - TV 计算基础), `fin_exp_int_exp` (财务费用:利息费用 - 计算税前债务成本关键), `fin_exp_int_inc` (财务费用:利息收入 - 计算税前债务成本时考虑)。
    * **`valuation_metrics` (最新):** `ts_code`, `trade_date`, `total_share` (总股本（亿）- *最终每股价值计算的关键*), `close` (收盘价), `beta` (Beta值).
    * **查询逻辑细节：**
        * 获取历史数据：根据 `ts_code`，选择 `report_type='ANN'`，`end_type='归母'`，按 `end_date` 降序排列，取最近 N 条记录。
        * 获取最新资产负债表：根据 `ts_code`，选择 `report_type='ANN'`，`end_type='归母'`，`end_date` 在估值基准日或之前，按 `end_date` 降序排列，取最近 1 条记录。
        * 获取最新估值指标：根据 `ts_code`，选择 `trade_date` 在估值基准日或之前，按 `trade_date` 降序排列，取最近 1 条记录。

**4.2 数据准备和处理模块 (`data_processor.py`)**

* **功能：** 接收从数据库获取的原始数据，进行清洗、标准化、计算派生指标，处理潜在的数据异常和缺失值，并将历史数据整理成适合预测模块和WACC计算模块使用的格式。
* **输入：** 原始历史财务数据（通常为 pandas DataFrame），最新资产负债表和估值数据。
* **输出：** 整理后的历史数据 DataFrame，包含计算DCF所需的核心指标的历史趋势；提取用于WACC计算的最新市场数据和资本结构数据。
* **关键处理和计算：**
    * **数据清洗与缺失值处理：** 对关键数值字段进行检查，将 NULL 或非数字值转换为 0 或 NaN，并根据业务逻辑决定是否进行填充（如使用前一期数据、平均值或提示错误）。
    * 确保数据按报告期排序。
    * 计算历史折旧摊销合计：`cash_flow.depr_fa_coga_dpba` + `cash_flow.amort_intang_assets` (+ `cash_flow.use_right_asset_dep` 如果适用)。
    * 计算历史营业利润率 (`operate_profit` / `revenue`)。
    * 计算历史税率：`income_tax` / `total_profit`。需处理 `total_profit` 为 0 或负数的情况。可以设定一个最小有效税率或使用预设的法定税率作为底线。
    * 计算历史 Capex 占收入比 (`c_pay_acq_const_fiolta` / `revenue`)。注意 `c_pay_acq_const_fiolta` 通常是负值，计算比率时应取绝对值或处理符号。
    * 计算历史 D&A 占收入比 (历史折旧摊销合计 / `revenue`)。
    * 计算历史营运资本各项周转天数或占收入/成本的比例 (如 应收账款周转天数 = `accounts_receiv` / (`revenue` / 360))。需要根据数据库字段确定具体计算所需的科目 (`accounts_receiv` 或 `accounts_receiv_bill` 等)，以及使用收入或营业成本 (`oper_cost`) 作为分母。
    * 计算历史**营运资本净额 (NWC)**：
        $NWC = \text{total\_cur\_assets} - \text{money\_cap} - (\text{total\_cur\_liab} - \text{short\_loan} - \text{non\_cur\_liab\_due\_1y})$
        使用 `balance_sheet` 表中相应字段。
    * 提取WACC计算所需的最新数据（使用最新的报告期或交易日数据）：
        * 总附息债务：`latest_balance_sheet.short_loan` + `latest_balance_sheet.non_cur_liab_due_1y` + `latest_balance_sheet.long_borr` + `latest_balance_sheet.bond_payable`. **遗漏考虑：** 数据库中可能存在其他附息债务科目，需核实并包含。目前假设这四个字段涵盖了所有附息债务。
        * 少数股东权益：`latest_balance_sheet.minority_int`。
        * 现金及现金等价物：`latest_balance_sheet.money_cap`。
        * 总股本：`latest_valuation_metrics.total_share` (注意单位为亿)。
        * 最新收盘价：`latest_valuation_metrics.close`。
        * Beta值：`latest_valuation_metrics.beta`。
        * 最新税前债务成本 (Rd)：需要一种方法来获取。可以是：a) 用户输入； b) 基于最新或历史 `fin_exp_int_exp` / 总附息债务平均余额 来估算历史成本并作为 Rd 的参考或起点。明确 Rd 的确定方法是必要的。
        * 边际所得税率：用户输入。
    * 提取最终估值调整所需最新数据：`latest_balance_sheet.total_liab` (如果 Equity Value 计算使用此口径), `latest_balance_sheet.oth_eqt_tools_p_shr`, `latest_balance_sheet.minority_int`, `latest_balance_sheet.money_cap`, `latest_valuation_metrics.total_share`. **重要修正：** Equity Value 计算应使用 **总附息债务** 而非 `total_liab`。应根据上述计算的总附息债务进行调整。

**4.3 财务预测模块 (`financial_forecaster.py`)**

* **功能：** 根据处理后的历史数据和用户定义的预测假设，预测未来各年的关键财务指标。
* **输入：** 整理后的历史数据（包含历史比率），用户定义的预测期年数，关键预测假设（销售增长率、目标营业利润率、目标所得税率、D&A占收入比、Capex占收入比、各项营运资本周转天数或占收入比等）。
* **输出：** 预测期各年的预测财务数据，包括但不限于：`revenue` (营业收入)、`operate_profit` (营业利润)、预测 EBITDA, 预测所得税费用、预测折旧摊销、预测资本性支出、预测营运资本各项明细。
* **关键预测项和方法细节：**
    * **预测收入：** 基于前一年预测收入和用户输入的增长率。增长率可以逐年输入，或设定一个初始高增长率然后线性下降到一个永续增长率（如果模型支持）。
    * **预测营业利润：** 基于预测收入和用户输入的目标营业利润率。利润率可以设定为常数，或从历史水平逐渐过渡到目标水平。
    * **预测所得税费用：** 基于预测利润总额 (`operate_profit` +/- 非经营损益) 或营业利润，乘以用户输入的目标所得税率。需要明确是否考虑非经营损益的预测。初期可以简化为只对营业利润征税。
    * **预测折旧摊销：** 基于预测收入乘以用户设定的 D&A 占收入比。比率可以参考历史平均或设定目标值。
    * **预测资本性支出：** 基于预测收入乘以用户设定的 Capex 占收入比。比率可以参考历史平均或设定目标值。
    * **预测营运资本各项：** 基于预测收入或成本（需确定预测使用哪个作为驱动因素）和用户设定的周转天数或比例，预测年末余额。例如，预测应收账款 = 预测收入 / 360 * 目标应收账款周转天数。预测年末营运资本各项余额是计算预测 ΔNWC 的基础。

**4.4 营运资本计算模块 (`working_capital_calculator.py`)**

* **功能：** 根据财务预测模块输出的营运资本各项预测余额，计算预测期各年的营运资本净额及其年度变化。
* **输入：** 预测期各年末的营运资本各项预测余额（如预测的 `total_cur_assets`, `money_cap`, `total_cur_liab`, `short_loan`, `non_cur_liab_due_1y` 等）。
* **输出：** 预测期各年末的营运资本净额 (NWC) 和预测期各年的营运资本净额变化 (ΔNWC)。
* **关键计算：**
    * **营运资本净额 (NWC):** 使用与数据处理模块中定义一致的公式计算预测期各年末的NWC，使用预测的科目余额。
        $NWC_{预测期末} = \text{预测期末total\_cur\_assets} - \text{预测期末money\_cap} - (\text{预测期末total\_cur\_liab} - \text{预测期末short\_loan} - \text{预测期末non\_cur\_liab\_due\_1y})$
    * **营运资本净额变化 (ΔNWC):** 计算本年末NWC与上年末NWC（或基准日NWC）的差额。第一年的 ΔNWC 使用预测年 1 NWC 减去基准日（最新报告期）的 NWC。
        $\Delta NWC_t = NWC_t - NWC_{t-1}$ (其中 $t$ 为预测年份, $NWC_0$ 为基准日 NWC)

**4.5 FCF 计算模块 (`fcf_calculator.py`)**

* **功能：** 接收预测期各年的营业利润、所得税率、折旧摊销、资本性支出和营运资本净额变化数据，计算每年的无杠杆自由现金流 (UFCF)。
* **输入：** 预测期各年的 `operate_profit`, 所得税率, 折旧摊销, 资本性支出, ΔNWC。这些数据来自 `financial_forecaster.py` 和 `working_capital_calculator.py`。
* **输出：** 预测期各年的 UFCF 值。
* **关键计算 (根据附件Excel逻辑):**
    $UFCF_t = \text{operate\_profit}_t \times (1 - \text{所得税率}_t) + \text{折旧摊销}_t - \text{资本性支出}_t - \Delta NWC_t$
    * **注意：** 此处使用的折旧摊销和资本性支出应是预测模块预测的值，其预测方法在 4.3 中基于历史的 cash_flow 表字段进行。所得税率是预测模块使用的目标税率。

**4.6 WACC 计算模块 (`wacc_calculator.py`)**

* **功能：** 根据获取和处理后的数据以及用户设定的参数，计算公司的加权平均资本成本 (WACC)。
* **输入：** 无风险利率 (Rf，**明确来源：用户输入或独立市场数据表**)，市场风险溢价 (MRP，**明确来源：用户输入或独立市场数据表**)，公司Beta值 (`beta`，从最新 `valuation_metrics` 获取)，最新计算的总附息债务，最新现金及现金等价物 (`money_cap`)，最新总股本 (`total_share`)，最新收盘价 (`close`)，用户设定的边际所得税率，税前债务成本 (Rd，**明确来源：用户输入或估算方法**)。
* **输出：** 计算出的 WACC 值。
* **关键计算:**
    * **股权成本 (Re) 使用 CAPM 模型:**
        $Re = Rf + \text{beta} \times MRP$
    * **市场价值的股权 (E):**
        $E = \text{最新的valuation\_metrics.total\_share} \times 10^8 \times \text{最新的valuation\_metrics.close}$ (**注意：total_share 单位是亿，需乘以 10^8 转换为股数**)
    * **市场价值的债务 (D):** 使用账面价值近似，即 `最新的总附息债务` (计算自 `short_loan` + `non_cur_liab_due_1y` + `long_borr` + `bond_payable`)。
        $D = \text{最新的balance\_sheet.short\_loan} + \text{最新的balance\_sheet.non\_cur\_liab\_due\_1y} + \text{最新的balance\_sheet.long\_borr} + \text{最新的balance\_sheet.bond\_payable}$
    * **公司总资本的市场价值 (V):**
        $V = E + D$
    * **股权权重 (We):**
        $We = E / V$
    * **债务权重 (Wd)::**
        $Wd = D / V$
    * **税后债务成本 (Rd_after_tax):**
        $Rd\_{after\_tax} = Rd \times (1 - \text{边际所得税率})$
    * **WACC 公式:**
        $WACC = We \times Re + Wd \times Rd\_{after\_tax}$

**4.7 终值计算模块 (`terminal_value_calculator.py`)**

* **功能：** 计算预测期结束后的公司价值（终值）。采用退出乘数法。
* **输入：** 预测期最后一年的 EBITDA 预测值，用户设定的退出乘数 (Exit Multiple)。
    * 预测期最后一年的 EBITDA = 预测期最后一年的 `operate_profit` + 预测期最后一年的折旧摊销 (计算值)。
* **输出：** 计算出的终值 (Terminal Value, TV)。
* **关键计算:**
    $TV = \text{预测期最后一年的 EBITDA} \times \text{退出乘数}$
    * **潜在遗漏：** 如果也支持永续增长法，需要增加永续增长率 (g) 的输入和计算逻辑：$TV = \frac{UFCF_{预测期末年} \times (1+g)}{WACC - g}$。目前仅要求退出乘数法，此项不属于当前遗漏。

**4.8 估值模块 (`valuation_model.py`)**

* **功能：** 接收预测期各年的UFCF、计算出的WACC、终值，并结合最新的资产负债表数据，计算各项现金流现值、企业价值、股权价值和隐含股票价格。
* **输入：** 预测期各年的UFCF（来自 `fcf_calculator.py`），计算出的WACC（来自 `wacc_calculator.py`），终值（来自 `terminal_value_calculator.py`），最新的总附息债务，最新的现金及现金等价物 (`money_cap`)，最新的少数股东权益 (`minority_int`)，最新的优先股 (`oth_eqt_tools_p_shr`)，最新的总股本 (`total_share` 从 `valuation_metrics` 获取)。
* **输出：** 预测期各年FCF的现值、终值的现值、企业价值(EV)、隐含股权价值、隐含股票价格。
* **关键计算:**
    * **贴现因子 (Discount Factor, DF):**
        $DF_t = \frac{1}{(1 + WACC)^t}$
        * **注意：** 这里的 $t$ 是从估值基准日到现金流发生时点的时间。如果预测期从当年年末开始，则第一年现金流的 $t=1$，第二年 $t=2$ 等。终值TV的 $t$ 为预测期年数。如果预测期从次年年初开始，则可能需要调整 $t$ 的计算（例如 $t-1$ 或使用 mid-period discounting）。**明确折现时点假设** 是必要的。当前采用年末折现。
    * **预测期 FCF 现值 (PV of UFCF):**
        $PV(UFCF_t) = UFCF_t \times DF_t$
    * **终值现值 (PV of TV):**
        $PV(TV) = TV \times DF_{预测期年数}$
    * **企业价值 (Enterprise Value, EV):**
        $EV = \sum_{t=1}^{\text{预测期年数}} PV(UFCF_t) + PV(TV)$
    * **隐含股权价值 (Implied Equity Value):** **重要修正：根据标准DCF和附件Excel的“有息负债净额”概念，此处应使用总附息债务进行调整，而非 `total_liab`。**
        $\text{隐含股权价值} = EV - \text{最新的总附息债务} - \text{最新的优先股} - \text{最新的少数股东权益} + \text{最新的现金及现金等价物}$
        * **说明:**
            * $\text{最新的总附息债务}$: 来自 `data_processor.py` 计算。
            * $\text{最新的优先股}$: 来自 `latest_balance_sheet.oth_eqt_tools_p_shr` 或 0。
            * $\text{最新的少数股东权益}$: 来自 `latest_balance_sheet.minority_int`。
            * $\text{最新的现金及现金等价物}$: 来自 `latest_balance_sheet.money_cap`。
    * **全面摊薄已发行股票数量:** 来自 `latest_valuation_metrics.total_share` (单位为亿)。计算时需转换为股数。
    * **隐含股票价格 (Implied Share Price):**
        $\text{隐含股票价格} = \frac{\text{隐含股权价值}}{\text{最新的valuation\_metrics.total\_share} \times 10^8}$ (**注意总股本单位转换**)
    * **潜在遗漏：** 稀释计算。如果数据库提供可转债、期权等信息，或用户提供相关数据，可以在此模块增加全面摊薄股本的计算逻辑。目前简化为只使用总股本。

**4.9 主程序 (`main.py`)**

* **功能：** 协调调用其他模块，定义输入参数和预测假设，执行完整的DCF估值流程，并生成输出报告。
* **主要流程:**
    1.  加载配置信息（数据库连接、默认假设）。
    2.  接收用户输入或读取配置文件，获取估值参数：股票代码、估值基准日期、预测期年数、关键预测假设（增长率、利润率、税率、Capex/D&A比率、NWC周转天数/比例等）、WACC参数（Rf, MRP, Rd, 边际税率）、终值参数（退出乘数）。
    3.  调用 `database_manager.py` 获取历史财务数据和最新的市场/估值数据。
    4.  调用 `data_processor.py` 进行数据清洗、处理，计算历史 NWC 和其他比率，并提取 WACC 和最终估值调整所需的关键历史/最新数据（包括计算总附息债务）。处理潜在的数据异常和缺失。
    5.  调用 `financial_forecaster.py` 进行未来财务指标预测（收入、利润、EBITDA、D&A、Capex、营运资本各项）。
    6.  调用 `working_capital_calculator.py` 计算预测期各年的 NWC 及其变化。
    7.  调用 `fcf_calculator.py` 计算预测期各年的 UFCF。
    8.  调用 `wacc_calculator.py` 计算 WACC。
    9.  调用 `terminal_value_calculator.py` 计算终值。
    10. 调用 `valuation_model.py` 计算各项现金流现值、企业价值、股权价值和隐含股票价格（包括隐含 EV/EBITDA）。
    11. 调用报告生成逻辑，格式化并输出最终估值报告。
    12. (可选) 将结果保存到数据库或文件中。
* **潜在遗漏：** 用户输入参数的验证和默认值设置。错误处理和日志记录的详细实现。

**5. 数据来源与数据库 Schema**

数据来源于您提供的数据库表结构。详细的 CREATE TABLE 语句已在上一版中列出。在此强调一些关键字段的使用：

* **`balance_sheet`**: `total_cur_assets`, `money_cap`, `total_cur_liab`, `short_loan`, `non_cur_liab_due_1y`, `long_borr`, `bond_payable`, `minority_int`, `total_share`, `total_liab`, `oth_eqt_tools_p_shr`.
* **`cash_flow`**: `depr_fa_coga_dpba`, `amort_intang_assets`, `use_right_asset_dep`, `c_pay_acq_const_fiolta`.
* **`income_statement`**: `revenue`, `operate_profit`, `income_tax`, `total_profit`, `ebitda`, `fin_exp_int_exp`, `fin_exp_int_inc`.
* **`valuation_metrics`**: `trade_date`, `total_share` (亿), `close`, `beta`.
* **其他市场数据**: **（需要明确来源）** 无风险利率 (Rf), 市场风险溢价 (MRP).

**6. 计算顺序推理**

计算顺序与上一版相同，确保数据依赖性：数据获取 -> 数据处理 -> 预测 -> 营运资本计算 -> FCF 计算 -> WACC 计算 -> 终值计算 -> 估值计算 -> 报告输出。

**7. 关键公式回顾 (使用数据库字段名称和修正)**

* 历史折旧摊销合计 = `cash_flow.depr_fa_coga_dpba` + `cash_flow.amort_intang_assets` (+ `cash_flow.use_right_asset_dep`)
* $NWC = \text{total\_cur\_assets} - \text{money\_cap} - (\text{total\_cur\_liab} - \text{short\_loan} - \text{non\_cur\_liab\_due\_1y})$
* $\Delta NWC_t = NWC_t - NWC_{t-1}$
* $UFCF_t = \text{operate\_profit}_t \times (1 - \text{所得税率}_t) + \text{折旧摊销}_t - \text{资本性支出}_t - \Delta NWC_t$
* $Re = Rf + \text{beta} \times MRP$
* $\text{市场价值的股权 } (E) = \text{最新的valuation\_metrics.total\_share} \times 10^8 \times \text{最新的valuation\_metrics.close}$
* $\text{总附息债务 } (D) = \text{最新的balance\_sheet.short\_loan} + \text{最新的balance\_sheet.non\_cur\_liab\_due\_1y} + \text{最新的balance\_sheet.long\_borr} + \text{最新的balance\_sheet.bond\_payable}$
* $V = E + D$
* $WACC = \frac{E}{V} \times Re + \frac{D}{V} \times Rd \times (1 - \text{边际所得税率})$
* $TV = (\text{预测期最后一年的operate\_profit} + \text{预测期最后一年的折旧摊销}) \times \text{退出乘数}$
* $DF_t = \frac{1}{(1 + WACC)^t}$
* $PV(CF) = CF \times DF$
* $EV = \sum PV(UFCF) + PV(TV)$
* $\text{隐含股权价值} = EV - \text{最新的总附息债务} - \text{最新的balance\_sheet.oth\_eqt\_tools\_p\_shr} - \text{最新的balance\_sheet.minority\_int} + \text{最新的balance\_sheet.money\_cap}$
* $\text{隐含股票价格} = \frac{\text{隐含股权价值}}{\text{最新的valuation\_metrics.total\_share} \times 10^8}$
* $\text{隐含 EV/EBITDA} = \frac{EV}{\text{预测期最后一年的 EBITDA}}$

**8. 非功能性需求**

* **数据验证与鲁棒性：** 增加对输入数据（用户假设）和从数据库获取数据的合理性验证（例如，检查关键字段是否为非负、是否符合财务逻辑）。在数据缺失或异常时，脚本应能优雅处理（如填充默认值、跳过计算、记录警告或报错）。
* **单位一致性：** 确保所有计算过程中金额和股本单位的一致性（例如，统一为元或万元），特别是在从数据库获取数据时处理 `valuation_metrics.total_share` 的亿股单位。
* **报告单位：** 在报告中明确所有数值的单位（例如：元、万元、亿元、%）。
* **日志记录：** 记录关键步骤、数据来源、使用的假设和任何警告/错误，方便调试和审计。

**9. 未来扩展考虑**

* 支持多种预测模型（简单增长、驱动因素分析、回归模型等）。
* 支持永续增长法作为终值计算的替代方案。
* 实现敏感性分析和情景分析功能。
* 集成数据可视化库生成图表（历史趋势、预测曲线、估值瀑布图等）。
* 考虑处理非年度报告数据进行更频繁或滚动估值。
* 增加详细的稀释股本计算逻辑。
* 支持读取外部配置文件加载假设，而非硬编码或命令行输入。
* 支持将结果和使用的假设保存回数据库。

**10. 输出报告规范**

... (报告内容和格式与上一版基本一致，但需确保其中的计算值是基于本次更新明确的公式和数据口径)

**10.1 报告标题与基本信息**
**10.2 关键输入参数与假设** (在此明确 Rf, MRP, Rd 的来源，并注明总附息债务、现金、少数股东权益、优先股是基于最新报告期数据)
**10.3 历史财务数据摘要** (确保折旧摊销、NWC, ΔNWC 的计算使用 PRD 中明确的字段)
**10.4 预测期财务数据与 UFCF 详情** (确保预测的 EBITDA, 所得税, D&A, Capex, NWC, ΔNWC 计算是基于 PRD 中预测模块的逻辑)
**10.5 终值计算详情** (确保预测期末年 EBITDA 计算正确)
**10.6 估值结果详情** (**重要：确保“减: 总负债”一行更正为“减: 总附息债务”，并且其取值和计算逻辑与 4.8 中的修正一致。** 同时确保总股本的单位转换在计算中和报告展示中正确。)
**10.7 免责声明**

---

**总结遗漏和补充点：**

1.  **Rf 和 MRP 数据来源：** PRD 中提到数据库或用户输入，但没有明确数据库中的具体表或字段。需在实现中明确来源，并在 PRD 中注明（例如：当前版本假设用户输入）。
2.  **税前债务成本 (Rd) 的确定方法：** 明确是用户输入，还是基于历史利息费用 (`fin_exp_int_exp`) 与附息债务的比例进行估算。需在 PRD 中注明采用哪种方法。
3.  **Equity Value 计算中的债务口径：** 修正了从 `total_liab` 为基础改为以 **总附息债务** 为基础，这更符合标准 DCF 模型，并与 WACC 计算中的债务口径一致。公式和相关描述已在 4.8 和 10.6 中修正。
4.  **总股本单位转换：** 强调了 `valuation_metrics.total_share` 的单位（亿）并在每股价值计算公式中加入了 $10^8$ 的转换。
5.  **数据清洗和异常处理：** 增加了对数据清洗、缺失值处理和数据验证的描述，这是实际开发中非常重要的部分。
6.  **预测方法细节：** 对预测方法（如增长率如何逐年变化、比率如何趋向目标值）给出了更详细的说明，虽然没有指定具体的数学模型，但明确了需要考虑的逻辑。
7.  **折现时点：** 明确了使用年末折现作为当前假设。
8.  **其他潜在附息债务：** 提醒核实 `balance_sheet` 中是否存在除 `short_loan`, `non_cur_liab_due_1y`, `long_borr`, `bond_payable` 之外的其他需要计入总附息债务的科目。目前PRD基于这四个字段。

这份更新的PRD应该更全面地反映了实现 DCF 估值脚本所需的各项功能和数据处理细节，特别是与您提供的数据库 Schema 之间的映射关系，并纠正了 Equity Value 计算的关键口径问题。