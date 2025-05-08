好的，感谢您提供详细的数据库表结构定义。这使得PRD更加具体和可执行。我将把这些精确的表结构融入文档中，并根据您的要求增加关于最终报告数据内容和呈现形式的描述。

以下是更新后的PRD：

---

**DCF 估值脚本产品需求文档 (PRD) - 更新版**

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
* **数据源：** 使用用户提供的 `balance_sheet`, `cash_flow`, `income_statement`, 和 `valuation_metrics` 表结构。
* **输入：** 股票代码（`ts_code`），估值基准日期，需要查询的历史年数。
* **输出：** 结构化的历史财务数据（如 pandas DataFrame），包含所需的科目明细和日期/报告期信息。应能获取至少过去5年的年度数据（`report_type='ANN'`）以及最新的年度或报告期结束为估值基准日的数据（`end_type`='归母'或其他适用类型）。需要获取最新的资产负债表数据用于最终的股权价值计算。需要获取最新的 `valuation_metrics` 数据。
* **关键查询：** 根据 `ts_code`, `end_date`, `report_type='ANN'`, `end_type='归母'`（或其他适用类型）从相关表中提取数据。

    * 从 `balance_sheet` 获取历史和最新数据，关键字段包括但不限于：`ts_code`, `end_date`, `total_cur_assets`, `money_cap`, `total_cur_liab`, `short_loan`, `non_cur_liab_due_1y`, `long_borr`, `bond_payable`, `minority_int`, `total_share`.
    * 从 `cash_flow` 获取历史数据，关键字段包括但不限于：`ts_code`, `end_date`, `depr_fa_coga_dpba` (或 `depr_fa_coga_dpds`), `amort_intang_assets`, `c_pay_acq_const_fiolta`.
    * 从 `income_statement` 获取历史数据，关键字段包括但不限于：`ts_code`, `end_date`, `revenue`, `operate_profit`, `income_tax`, `total_profit` (用于税率计算), `ebitda`, `fin_exp_int_exp`.
    * 从 `valuation_metrics` 获取最新数据（根据估值基准日查找最近的交易日），关键字段包括但不限于：`ts_code`, `trade_date`, `total_share`, `close`, `beta`.
    * （如果需要）从其他市场数据表获取无风险利率、市场风险溢价等数据。

**4.2 数据准备和处理模块 (`data_processor.py`)**

* **功能：** 接收从数据库获取的原始数据，进行清洗、标准化、计算派生指标，并将历史数据整理成适合预测模块和WACC计算模块使用的格式。处理缺失值（如用0填充或根据业务逻辑插值）。
* **输入：** 原始历史财务数据（通常为 pandas DataFrame），最新资产负债表和估值数据。
* **输出：** 整理后的历史数据 DataFrame，包含计算DCF所需的核心指标的历史趋势；提取用于WACC计算的最新市场数据和资本结构数据。
* **关键处理和计算：**
    * 确保数据按报告期排序。
    * 计算**营运资本净额 (NWC)**的历史值。根据附件Excel逻辑和提供的 `balance_sheet` 字段：
        $NWC = \text{total\_cur\_assets} - \text{money\_cap} - (\text{total\_cur\_liab} - \text{short\_loan} - \text{non\_cur\_liab\_due\_1y})$
    * 计算历史折旧摊销合计：使用 `cash_flow` 表中的字段 `depr_fa_coga_dpba` + `amort_intang_assets`。
    * 计算其他必要的历史比率和趋势（如营业利润率 (`operate_profit` / `revenue`)、所得税率 (`income_tax` / `total_profit` 或 `operate_profit`)、Capex/Revenue (`c_pay_acq_const_fiolta` / `revenue`)、D&A/Revenue (历史折旧摊销合计 / `revenue`)、各项营运资本周转天数或占收入比等）作为预测依据。
    * 提取WACC计算所需的最新数据（使用最新的报告期或交易日数据）：
        * 总债务：`st_borr` + `non_cur_liab_due_1y` + `lt_borr` + `bond_payable` (从最新 `balance_sheet` 获取)。
        * 少数股东权益：`minority_int` (从最新 `balance_sheet` 获取)。
        * 现金及现金等价物：`money_cap` (从最新 `balance_sheet` 获取，或 `c_cash_equ_end_period` 从最新 `cash_flow` 获取，需要确定统一口径，此处沿用前述PRD使用 `money_cap`)。
        * 总股本：`total_share` (从最新 `valuation_metrics` 获取)。
        * 最新收盘价：`close` (从最新 `valuation_metrics` 获取)。
        * Beta值：`beta` (从最新 `valuation_metrics` 获取)。
        * 税前债务成本 (Rd)：需要通过历史财务费用（`fin_exp_int_exp` 从 `income_statement` 获取）与历史债务余额（从 `balance_sheet` 获取）的比率估算，或使用外部数据，或者作为用户输入参数。初期可简化为用户输入。
        * 边际所得税率：用户输入或根据历史所得税费用计算历史有效税率作为参考。

**4.3 财务预测模块 (`financial_forecaster.py`)**

* **功能：** 根据处理后的历史数据和用户定义的预测假设，预测未来各年的关键财务指标。
* **输入：** 整理后的历史数据，用户定义的预测期年数，关键预测假设（销售增长率、营业利润率、目标所得税率、D&A占收入比、Capex占收入比、各项营运资本周转天数或占收入比等）。
* **输出：** 预测期各年的预测财务数据，包括但不限于：`revenue` (营业收入)、`operate_profit` (营业利润)、`income_tax` (所得税费用)、折旧摊销、资本性支出、营运资本各项明细（如应收账款 (`accounts_receiv` 或 `accounts_receiv_bill`), 存货 (`inventories`), 应付账款 (`acct_payable` 或 `accounts_pay`), 货币资金 (`money_cap`), 短期借款 (`short_loan`), 一年内到期的非流动负债 (`non_cur_liab_due_1y`) 等）。
* **关键预测：** 基于用户输入的增长率、利润率、费用率、周转率等假设，结合历史数据趋势进行预测。例如，`revenue` 的预测基于增长率；`operate_profit` = `revenue` * 营业利润率；折旧摊销 = `revenue` * D&A占收入比；资本性支出 = `revenue` * Capex占收入比；各项营运资本科目余额基于预测收入或成本及周转天数/比例预测。

**4.4 营运资本计算模块 (`working_capital_calculator.py`)**

* **功能：** 根据财务预测模块输出的营运资本各项预测余额，计算预测期各年的营运资本净额及其年度变化。
* **输入：** 预测期各年末的营运资本各项预测余额。
* **输出：** 预测期各年末的营运资本净额 (NWC) 和预测期各年的营运资本净额变化 (ΔNWC)。
* **关键计算：**
    * **营运资本净额 (NWC):** 使用与数据处理模块中定义一致的公式计算预测期各年末的NWC，使用预测的科目余额：
        $NWC_{预测期末} = \text{预测期末total\_cur\_assets} - \text{预测期末money\_cap} - (\text{预测期末total\_cur\_liab} - \text{预测期末short\_loan} - \text{预测期末non\_cur\_liab\_due\_1y})$
    * **营运资本净额变化 (ΔNWC):** 计算本年末NWC与上年末NWC（或基准日NWC）的差额。
        $\Delta NWC_t = NWC_t - NWC_{t-1}$ (其中 $t$ 为预测年份)

**4.5 FCF 计算模块 (`fcf_calculator.py`)**

* **功能：** 接收预测期各年的营业利润、所得税率、折旧摊销、资本性支出和营运资本净额变化数据，计算每年的无杠杆自由现金流 (UFCF)。
* **输入：** 预测期各年的 `operate_profit`, 所得税率, 折旧摊销, 资本性支出, ΔNWC。这些数据来自 `financial_forecaster.py` 和 `working_capital_calculator.py`。
* **输出：** 预测期各年的 UFCF 值。
* **关键计算 (根据附件Excel逻辑):**
    $UFCF_t = \text{operate\_profit}_t \times (1 - \text{所得税率}_t) + \text{折旧摊销}_t - \text{资本性支出}_t - \Delta NWC_t$

**4.6 WACC 计算模块 (`wacc_calculator.py`)**

* **功能：** 根据获取和处理后的数据以及用户设定的参数，计算公司的加权平均资本成本 (WACC)。
* **输入：** 无风险利率 (Rf)，市场风险溢价 (MRP)，公司Beta值 (`beta`)，目标资本结构 (或使用最新市值和债务总额计算市场价值权重)，公司的边际所得税率 (用户输入)，税前债务成本 (Rd，用户输入或估算)。
    * `beta`, `total_share`, `close` 来自 `data_processor.py` 从最新 `valuation_metrics` 获取。
    * 最新总债务 (计算自 `st_borr`, `non_cur_liab_due_1y`, `lt_borr`, `bond_payable`) 来自 `data_processor.py` 从最新 `balance_sheet` 获取。
    * 最新少数股东权益 (`minority_int`) 来自 `data_processor.py` 从最新 `balance_sheet` 获取（在股权价值计算中减除，不计入WACC分母）。
* **输出：** 计算出的 WACC 值。
* **关键计算:**
    * **股权成本 (Re) 使用 CAPM 模型:**
        $Re = Rf + \text{beta} \times MRP$
    * **市场价值的股权 (E):**
        $E = \text{最新的total\_share} \times \text{最新的close}$
    * **市场价值的债务 (D):** 使用账面价值近似，即 `最新的总债务` (计算自 `st_borr` + `non_cur_liab_due_1y` + `lt_borr` + `bond_payable`)。
        $D = \text{最新的short\_loan} + \text{最新的non\_cur\_liab\_due\_1y} + \text{最新的long\_borr} + \text{最新的bond\_payable}$
    * **公司总资本的市场价值 (V):**
        $V = E + D$
    * **股权权重 (We):**
        $We = E / V$
    * **债务权重 (Wd):**
        $Wd = D / V$
    * **税后债务成本 (Rd_after_tax):**
        $Rd\_{after\_tax} = Rd \times (1 - \text{边际所得税率})$
    * **WACC 公式:**
        $WACC = We \times Re + Wd \times Rd\_{after\_tax}$
        或
        $WACC = \frac{E}{V} \times Re + \frac{D}{V} \times Rd \times (1 - \text{边际所得税率})$

**4.7 终值计算模块 (`terminal_value_calculator.py`)**

* **功能：** 计算预测期结束后的公司价值（终值）。采用退出乘数法。
* **输入：** 预测期最后一年的 EBITDA 预测值，用户设定的退出乘数 (Exit Multiple)。
    * 预测期最后一年的 EBITDA = 预测期最后一年的 `operate_profit` + 预测期最后一年的折旧摊销。
* **输出：** 计算出的终值 (Terminal Value, TV)。
* **关键计算:**
    $TV = \text{预测期最后一年的 EBITDA} \times \text{退出乘数}$

**4.8 估值模块 (`valuation_model.py`)**

* **功能：** 接收预测期各年的UFCF、计算出的WACC、终值，并结合最新的资产负债表数据，计算各项现金流现值、企业价值、股权价值和隐含股票价格。
* **输入：** 预测期各年的UFCF（来自 `fcf_calculator.py`），计算出的WACC（来自 `wacc_calculator.py`），终值（来自 `terminal_value_calculator.py`），最新的资产负债表数据（`total_liab`, `money_cap`, `minority_int` 等）和最新的总股本 (`total_share`)。
* **输出：** 预测期各年FCF的现值、终值的现值、企业价值(EV)、隐含股权价值、隐含股票价格。
* **关键计算:**
    * **贴现因子 (Discount Factor, DF):**
        $DF_t = \frac{1}{(1 + WACC)^t}$
        * **说明:** $t$ 为折现期数，即从估值基准日到该现金流发生时点的时间。例如，预测第一年FCF的折现期为1，第二年为2，以此类推。终值的折现期为预测期年数。
    * **预测期 FCF 现值 (PV of UFCF):**
        $PV(UFCF_t) = UFCF_t \times DF_t$
    * **终值现值 (PV of TV):**
        $PV(TV) = TV \times DF_{预测期年数}$
    * **企业价值 (Enterprise Value, EV):**
        $EV = \sum_{t=1}^{\text{预测期年数}} PV(UFCF_t) + PV(TV)$
    * **隐含股权价值 (Implied Equity Value):** 根据PRD原文定义，并映射数据库字段。
        $\text{隐含股权价值} = EV - \text{总负债} - \text{优先股} - \text{少数股东权益} + \text{现金及现金等价物}$
        * **说明:**
            * $\text{总负债}$: 最新值，从最新 `balance_sheet` 获取 `total_liab`。*注意：此处与附件Excel的“有息负债净额”定义略有不同，遵循PRD原文的“总负债”口径。*
            * $\text{优先股}$: 最新值，从最新 `balance_sheet` 获取 `oth_eqt_tools_p_shr` 或假设为0。
            * $\text{少数股东权益}$: 最新值，从最新 `balance_sheet` 获取 `minority_int`。
            * $\text{现金及现金等价物}$: 最新值，从最新 `balance_sheet` 获取 `money_cap` 或从最新 `cash_flow` 获取 `c_cash_equ_end_period`。此处使用 `money_cap`。
    * **全面摊薄已发行股票数量:** 获取最新的 `total_share` (总股本)，从最新 `valuation_metrics` 获取。初期不考虑稀释。
    * **隐含股票价格 (Implied Share Price):**
        $\text{隐含股票价格} = \frac{\text{隐含股权价值}}{\text{全面摊薄已发行股票数量}}$

**4.9 主程序 (`main.py`)**

* **功能：** 协调调用其他模块，定义输入参数和预测假设，执行完整的DCF估值流程，并生成输出报告。
* **主要流程:**
    1.  配置数据库连接信息。
    2.  接收用户输入或读取配置文件，获取估值参数：股票代码、估值基准日期、预测期年数、关键预测假设（销售增长率、利润率、capex/da比率、营运资本周转天数等）、WACC参数（Rf, MRP, Rd, 边际税率）、终值参数（退出乘数）。
    3.  调用 `database_manager.py` 获取历史财务数据、最新资产负债表数据和最新的市场/估值数据。
    4.  调用 `data_processor.py` 进行数据清洗、处理，计算历史NWC，并提取WACC和最终估值调整所需的关键历史/最新数据。
    5.  调用 `financial_forecaster.py` 进行未来财务指标预测。
    6.  调用 `working_capital_calculator.py` 计算预测期各年的NWC及其变化。
    7.  调用 `fcf_calculator.py` 计算预测期各年的UFCF。
    8.  调用 `wacc_calculator.py` 计算WACC。
    9.  调用 `terminal_value_calculator.py` 计算终值。
    10. 调用 `valuation_model.py` 计算各项现金流现值、企业价值、股权价值和隐含股票价格。
    11. 调用报告生成逻辑，输出最终估值报告。
    12. (可选) 将结果保存到数据库或文件中。

**5. 数据来源与数据库 Schema**

数据来源于您提供的数据库表结构。以下是精确的 CREATE TABLE 语句：

```sql
 -- 资产负债表
 CREATE TABLE balance_sheet(
      ts_code varchar(20) NOT NULL,
      ann_date date NOT NULL,
      f_ann_date date,
      end_date date NOT NULL,
      report_type varchar(10),
      comp_type varchar(1),
      end_type varchar(10) NOT NULL,
      total_share numeric(20,4),
      cap_rese numeric(20,4),
      undistr_porfit numeric(20,4),
      surplus_rese numeric(20,4),
      special_rese numeric(20,4),
      money_cap numeric(20,4),
      trad_asset numeric(20,4),
      notes_receiv numeric(20,4),
      accounts_receiv numeric(20,4),
      oth_receiv numeric(20,4),
      prepayment numeric(20,4),
      div_receiv numeric(20,4),
      int_receiv numeric(20,4),
      inventories numeric(20,4),
      amor_exp numeric(20,4),
      nca_within_1y numeric(20,4),
      sett_rsrv numeric(20,4),
      loanto_oth_bank_fi numeric(20,4),
      premium_receiv numeric(20,4),
      reinsur_receiv numeric(20,4),
      reinsur_res_receiv numeric(20,4),
      pur_resale_fa numeric(20,4),
      oth_cur_assets numeric(20,4),
      total_cur_assets numeric(20,4),
      fa_avail_for_sale numeric(20,4),
      htm_invest numeric(20,4),
      lt_eqt_invest numeric(20,4),
      invest_real_estate numeric(20,4),
      time_deposits numeric(20,4),
      oth_assets numeric(20,4),
      lt_rec numeric(20,4),
      fix_assets numeric(20,4),
      cip numeric(20,4),
      const_materials numeric(20,4),
      fixed_assets_disp numeric(20,4),
      produc_bio_assets numeric(20,4),
      oil_and_gas_assets numeric(20,4),
      intan_assets numeric(20,4),
      r_and_d numeric(20,4),
      goodwill numeric(20,4),
      lt_amor_exp numeric(20,4),
      defer_tax_assets numeric(20,4),
      decr_in_disbur numeric(20,4),
      oth_nca numeric(20,4),
      total_nca numeric(20,4),
      cash_reser_cb numeric(20,4),
      depos_in_oth_bfi numeric(20,4),
      prec_metals numeric(20,4),
      deriv_assets numeric(20,4),
      rr_reins_une_prem numeric(20,4),
      rr_reins_outstd_cla numeric(20,4),
      rr_reins_lins_liab numeric(20,4),
      rr_reins_lthins_liab numeric(20,4),
      refund_depos numeric(20,4),
      ph_pledge_loans numeric(20,4),
      refund_cap_depos numeric(20,4),
      indep_acct_assets numeric(20,4),
      client_depos numeric(20,4),
      client_prov numeric(20,4),
      transac_seat_fee numeric(20,4),
      invest_as_receiv numeric(20,4),
      total_assets numeric(20,4),
      lt_borr numeric(20,4),
      st_borr numeric(20,4),
      cb_borr numeric(20,4),
      depos_ib_deposits numeric(20,4),
      loan_oth_bank numeric(20,4),
      trading_fl numeric(20,4),
      notes_payable numeric(20,4),
      acct_payable numeric(20,4),
      adv_receipts numeric(20,4),
      sold_for_repur_fa numeric(20,4),
      comm_payable numeric(20,4),
      payroll_payable numeric(20,4),
      taxes_payable numeric(20,4),
      int_payable numeric(20,4),
      div_payable numeric(20,4),
      oth_payable numeric(20,4),
      acc_exp numeric(20,4),
      deferred_inc numeric(20,4),
      st_bonds_payable numeric(20,4),
      payable_to_reinsurer numeric(20,4),
      rsrv_insur_cont numeric(20,4),
      acting_trading_sec numeric(20,4),
      acting_uw_sec numeric(20,4),
      non_cur_liab_due_1y numeric(20,4),
      oth_cur_liab numeric(20,4),
      total_cur_liab numeric(20,4),
      bond_payable numeric(20,4),
      lt_payable numeric(20,4),
      specific_payables numeric(20,4),
      estimated_liab numeric(20,4),
      defer_tax_liab numeric(20,4),
      defer_inc_non_cur_liab numeric(20,4),
      oth_ncl numeric(20,4),
      total_ncl numeric(20,4),
      depos_oth_bfi numeric(20,4),
      deriv_liab numeric(20,4),
      depos numeric(20,4),
      agency_bus_liab numeric(20,4),
      oth_liab numeric(20,4),
      prem_receiv_adva numeric(20,4),
      depos_received numeric(20,4),
      ph_invest numeric(20,4),
      reser_une_prem numeric(20,4),
      reser_outstd_claims numeric(20,4),
      reser_lins_liab numeric(20,4),
      reser_lthins_liab numeric(20,4),
      indept_acc_liab numeric(20,4),
      pledge_borr numeric(20,4),
      indem_payable numeric(20,4),
      policy_div_payable numeric(20,4),
      total_liab numeric(20,4),
      treasury_share numeric(20,4),
      ordin_risk_reser numeric(20,4),
      forex_differ numeric(20,4),
      invest_loss_unconf numeric(20,4),
      minority_int numeric(20,4),
      total_hldr_eqy_exc_min_int numeric(20,4),
      total_hldr_eqy_inc_min_int numeric(20,4),
      total_liab_hldr_eqy numeric(20,4),
      lt_payroll_payable numeric(20,4),
      oth_comp_income numeric(20,4),
      oth_eqt_tools numeric(20,4),
      oth_eqt_tools_p_shr numeric(20,4),
      lending_funds numeric(20,4),
      acc_receivable numeric(20,4),
      st_fin_payable numeric(20,4),
      payables numeric(20,4),
      hfs_assets numeric(20,4),
      hfs_sales numeric(20,4),
      cost_fin_assets numeric(20,4),
      fair_value_fin_assets numeric(20,4),
      cip_total numeric(20,4),
      oth_pay_total numeric(20,4),
      long_pay_total numeric(20,4),
      debt_invest numeric(20,4),
      oth_debt_invest numeric(20,4),
      oth_eq_invest numeric(20,4),
      oth_illiq_fin_assets numeric(20,4),
      oth_eq_ppbond numeric(20,4),
      receiv_financing numeric(20,4),
      use_right_assets numeric(20,4),
      lease_liab numeric(20,4),
      contract_assets numeric(20,4),
      contract_liab numeric(20,4),
      accounts_receiv_bill numeric(20,4),
      accounts_pay numeric(20,4),
      oth_rcv_total numeric(20,4),
      fix_assets_total numeric(20,4),
      update_flag varchar(1) NOT NULL,
      PRIMARY KEY(ts_code,end_date,end_type,update_flag)
 );
 -- 现金流量表
 CREATE TABLE cash_flow(
      ts_code varchar(20) NOT NULL,
      ann_date date NOT NULL,
      f_ann_date date,
      end_date date NOT NULL,
      comp_type varchar(1),
      report_type varchar(10),
      end_type varchar(10) NOT NULL,
      net_profit numeric(20,4),
      finan_exp numeric(20,4), -- 注意此字段与 income_statement.fin_exp 可能重复，且非利息费用，实际计算税前债务成本应使用 income_statement.fin_exp_int_exp
      c_fr_sale_sg numeric(20,4),
      recp_tax_rends numeric(20,4),
      n_depos_incr_fi numeric(20,4),
      n_incr_loans_cb numeric(20,4),
      n_inc_borr_oth_fi numeric(20,4),
      prem_fr_orig_contr numeric(20,4),
      n_incr_insured_dep numeric(20,4),
      n_reinsur_prem numeric(20,4),
      n_incr_disp_tfa numeric(20,4),
      ifc_cash_incr numeric(20,4),
      n_incr_disp_faas numeric(20,4),
      n_incr_loans_oth_bank numeric(20,4),
      n_cap_incr_repur numeric(20,4),
      c_fr_oth_operate_a numeric(20,4),
      c_inf_fr_operate_a numeric(20,4),
      c_paid_goods_s numeric(20,4),
      c_paid_to_for_empl numeric(20,4),
      c_paid_for_taxes numeric(20,4),
      n_incr_clt_loan_adv numeric(20,4),
      n_incr_dep_cbob numeric(20,4),
      c_pay_claims_orig_inco numeric(20,4),
      pay_handling_chrg numeric(20,4),
      pay_comm_insur_plcy numeric(20,4),
      oth_cash_pay_oper_act numeric(20,4),
      st_cash_out_act numeric(20,4),
      n_cashflow_act numeric(20,4), -- 经营活动产生的现金流量净额 (直接法或调整后)
      oth_recp_ral_inv_act numeric(20,4),
      c_disp_withdrwl_invest numeric(20,4),
      c_recp_return_invest numeric(20,4),
      n_recp_disp_fiolta numeric(20,4),
      n_recp_disp_sobu numeric(20,4),
      stot_inflows_inv_act numeric(20,4),
      c_pay_acq_const_fiolta numeric(20,4), -- 购建固定资产、无形资产和其他长期资产支付的现金 (Capex)
      c_paid_invest numeric(20,4),
      n_disp_subs_oth_biz numeric(20,4),
      oth_pay_ral_inv_act numeric(20,4),
      n_incr_pledge_loan numeric(20,4),
      stot_out_inv_act numeric(20,4),
      n_cashflow_inv_act numeric(20,4), -- 投资活动产生的现金流量净额
      c_recp_borrow numeric(20,4),
      proc_issue_bonds numeric(20,4),
      oth_cash_recp_ral_fnc_act numeric(20,4),
      stot_cash_in_fnc_act numeric(20,4),
      free_cashflow numeric(20,4), -- 注意此字段是否是DCF需要的UFCF，通常不是，DCF需要单独计算
      c_prepay_amt_borr numeric(20,4),
      c_pay_dist_dpcp_int_exp numeric(20,4), -- 分配股利、利润或偿付利息支付的现金 (付息)
      incl_dvd_profit_paid_sc_ms numeric(20,4),
      oth_cashpay_ral_fnc_act numeric(20,4),
      stot_cashout_fnc_act numeric(20,4),
      n_cash_flows_fnc_act numeric(20,4), -- 筹资活动产生的现金流量净额
      eff_fx_flu_cash numeric(20,4),
      n_incr_cash_cash_equ numeric(20,4),
      c_cash_equ_beg_period numeric(20,4), -- 期初现金及现金等价物余额
      c_cash_equ_end_period numeric(20,4), -- 期末现金及现金等价物余额
      c_recp_cap_contrib numeric(20,4),
      incl_cash_rec_saims numeric(20,4),
      uncon_invest_loss numeric(20,4),
      prov_depr_assets numeric(20,4), -- 加:资产减值准备 (可能与D&A相关，需确认口径)
      depr_fa_coga_dpba numeric(20,4), -- 固定资产折旧、油气资产折耗、生产性生物资产折旧
      amort_intang_assets numeric(20,4), -- 无形资产摊销
      lt_amort_deferred_exp numeric(20,4),
      decr_deferred_exp numeric(20,4),
      incr_acc_exp numeric(20,4),
      loss_disp_fiolta numeric(20,4),
      loss_scr_fa numeric(20,4),
      loss_fv_chg numeric(20,4),
      invest_loss numeric(20,4),
      decr_def_inc_tax_assets numeric(20,4),
      incr_def_inc_tax_liab numeric(20,4),
      decr_inventories numeric(20,4), -- 存货的减少 (营运资本变动项)
      decr_oper_payable numeric(20,4), -- 经营性应收项目的减少 (营运资本变动项)
      incr_oper_payable numeric(20,4), -- 经营性应付项目的增加 (营运资本变动项)
      others numeric(20,4),
      im_net_cashflow_oper_act numeric(20,4), -- 经营活动产生的现金流量净额(间接法)
      conv_debt_into_cap numeric(20,4),
      conv_copbonds_due_within_1y numeric(20,4),
      fa_fnc_leases numeric(20,4),
      im_n_incr_cash_equ numeric(20,4),
      net_dism_capital_add numeric(20,4),
      net_cash_rece_sec numeric(20,4),
      credit_impa_loss numeric(20,4),
      use_right_asset_dep numeric(20,4), -- 使用权资产折旧 (新准则下D&A项)
      oth_loss_asset numeric(20,4),
      end_bal_cash numeric(20,4),
      beg_bal_cash numeric(20,4),
      end_bal_cash_equ numeric(20,4), -- 期末现金及现金等价物余额
      beg_bal_cash_equ numeric(20,4), -- 期初现金及现金等价物余额
      update_flag varchar(1) NOT NULL,
      PRIMARY KEY(ts_code,end_date,end_type,update_flag)
 );
 -- 利润表
 CREATE TABLE income_statement(
      ts_code varchar(20) NOT NULL,
      ann_date date NOT NULL,
      f_ann_date date,
      end_date date NOT NULL,
      report_type varchar(10),
      comp_type varchar(1),
      end_type varchar(10) NOT NULL,
      basic_eps numeric(20,4),
      diluted_eps numeric(20,4),
      total_revenue numeric(20,4), -- 营业总收入
      revenue numeric(20,4), -- 营业收入 (通常用于核心收入预测)
      int_income numeric(20,4), -- 利息收入
      prem_earned numeric(20,4),
      comm_income numeric(20,4),
      n_commis_income numeric(20,4),
      n_oth_income numeric(20,4),
      n_oth_b_income numeric(20,4),
      prem_income numeric(20,4),
      out_prem numeric(20,4),
      une_prem_reser numeric(20,4),
      reins_income numeric(20,4),
      n_sec_tb_income numeric(20,4),
      n_sec_uw_income numeric(20,4),
      n_asset_mg_income numeric(20,4),
      oth_b_income numeric(20,4), -- 其他业务收入
      fv_value_chg_gain numeric(20,4),
      invest_income numeric(20,4), -- 投资净收益
      ass_invest_income numeric(20,4),
      forex_gain numeric(20,4),
      total_cogs numeric(20,4), -- 营业总成本
      oper_cost numeric(20,4), -- 营业成本
      int_exp numeric(20,4), -- 利息支出 (财务费用中的一部分)
      comm_exp numeric(20,4),
      biz_tax_surchg numeric(20,4),
      sell_exp numeric(20,4), -- 销售费用
      admin_exp numeric(20,4), -- 管理费用
      fin_exp numeric(20,4), -- 财务费用总额
      assets_impair_loss numeric(20,4),
      prem_refund numeric(20,4),
      compens_payout numeric(20,4),
      reser_insur_liab numeric(20,4),
      div_payt numeric(20,4),
      reins_exp numeric(20,4),
      oper_exp numeric(20,4), -- 营业支出 (通常与total_cogs相关)
      compens_payout_refu numeric(20,4),
      insur_reser_refu numeric(20,4),
      reins_cost_refund numeric(20,4),
      other_bus_cost numeric(20,4), -- 其他业务成本
      operate_profit numeric(20,4), -- 营业利润 (UFCF计算基础)
      non_oper_income numeric(20,4), -- 营业外收入
      non_oper_exp numeric(20,4), -- 营业外支出
      nca_disploss numeric(20,4), -- 非流动资产处置净损失 (与Capex口径相关的调整项)
      total_profit numeric(20,4), -- 利润总额 (税前利润)
      income_tax numeric(20,4), -- 所得税费用
      n_income numeric(20,4), -- 净利润(含少数股东损益)
      n_income_attr_p numeric(20,4), -- 净利润(不含少数股东损益)
      minority_gain numeric(20,4), -- 少数股东损益
      oth_compr_income numeric(20,4),
      t_compr_income numeric(20,4),
      compr_inc_attr_p numeric(20,4),
      compr_inc_attr_m_s numeric(20,4),
      ebit numeric(20,4), -- 息税前利润 (与operate_profit可能非常接近或相等)
      ebitda numeric(20,4), -- 息税折旧摊销前利润 (TV计算基础)
      insurance_exp numeric(20,4),
      undist_profit numeric(20,4),
      distable_profit numeric(20,4),
      rd_exp numeric(20,4), -- 研发费用
      fin_exp_int_exp numeric(20,4), -- 财务费用:利息费用 (计算税前债务成本的关键)
      fin_exp_int_inc numeric(20,4), -- 财务费用:利息收入
      transfer_surplus_rese numeric(20,4),
      transfer_housing_imprest numeric(20,4),
      transfer_oth numeric(20,4),
      adj_lossgain numeric(20,4),
      withdra_legal_surplus numeric(20,4),
      withdra_legal_pubfund numeric(20,4),
      withdra_biz_devfund numeric(20,4),
      withdra_rese_fund numeric(20,4),
      withdra_oth_ersu numeric(20,4),
      workers_welfare numeric(20,4),
      distr_profit_shrhder numeric(20,4),
      prfshare_payable_dvd numeric(20,4), -- 应付优先股股利
      comshare_payable_dvd numeric(20,4),
      capit_comstock_div numeric(20,4),
      net_after_nr_lp_correct numeric(20,4),
      credit_impa_loss numeric(20,4),
      net_expo_hedging_benefits numeric(20,4),
      oth_impair_loss_assets numeric(20,4),
      total_opcost numeric(20,4),
      amodcost_fin_assets numeric(20,4),
      oth_income numeric(20,4), -- 其他收益
      asset_disp_income numeric(20,4), -- 资产处置收益 (与Capex口径相关的调整项)
      continued_net_profit numeric(20,4),
      end_net_profit numeric(20,4),
      update_flag varchar(1) NOT NULL,
      PRIMARY KEY(ts_code,end_date,end_type,update_flag)
 );
 -- 股票估值指标表
 CREATE TABLE valuation_metrics(
      trade_date date NOT NULL,
      ts_code varchar(20) NOT NULL,
      name varchar(50),
      industry varchar(50),
      area varchar(50),
      pe numeric(20,4),
      float_share numeric(20,4), -- 流通股本（亿）
      total_share numeric(20,4), -- 总股本（亿）(用于最终每股价值计算)
      total_assets numeric(20,4),
      liquid_assets numeric(20,4),
      fixed_assets numeric(20,4),
      reserved numeric(20,4),
      reserved_pershare numeric(20,4),
      eps numeric(20,4),
      bvps numeric(20,4),
      pb numeric(20,4),
      list_date varchar(20),
      undp numeric(20,4),
      per_undp numeric(20,4),
      rev_yoy numeric(20,4), -- 收入同比（%）
      profit_yoy numeric(20,4), -- 利润同比（%）
      gpr numeric(20,4), -- 毛利率（%）
      npr numeric(20,4), -- 净利润率（%）
      holder_num integer,
      PRIMARY KEY(trade_date,ts_code)
 );
 ```

**6. 计算顺序推理**

严格遵循DCF模型和附件Excel的计算逻辑，各模块的调用和计算顺序如下：

1.  **数据获取 (`database_manager.py`):** 获取历史财务数据（BS, IS, CF）和最新的市场/估值数据 (`valuation_metrics`)。
2.  **数据处理 (`data_processor.py`):** 清洗、整理历史数据，计算历史 NWC，并提取用于预测、WACC 和最终估值的关键历史/最新数据（包括根据 BS 计算最新的总债务、现金、少数股东权益）。
3.  **财务预测 (`financial_forecaster.py`):** 利用处理后的历史数据和用户假设，预测未来各年的 `revenue`, `operate_profit`, 所得税, 折旧摊销, 资本性支出以及营运资本各项余额。
4.  **营运资本计算 (`working_capital_calculator.py`):** 根据预测的营运资本各项余额，计算预测期各年末的 NWC 及各年的 ΔNWC。
5.  **UFCF 计算 (`fcf_calculator.py`):** 根据预测的 `operate_profit`, 所得税率, 折旧摊销, 资本性支出 和 ΔNWC，计算预测期各年的 UFCF。
6.  **WACC 计算 (`wacc_calculator.py`):** 根据获取的市场数据、计算的最新资本结构和用户参数 (Rf, MRP, Rd, 边际税率)，计算 WACC。
7.  **终值计算 (`terminal_value_calculator.py`):** 根据预测期最后一年的 EBITDA 和用户设定的退出乘数，计算终值。
8.  **现值计算 (`valuation_model.py`):** 利用 WACC 计算贴现因子，并将预测期 UFCF 和终值折现至估值基准日计算现值。
9.  **企业价值计算 (`valuation_model.py`):** 将所有 UFCF 的现值和终值的现值相加，得到企业价值 (EV)。
10. **股权价值计算 (`valuation_model.py`):** 根据企业价值和最新的资产负债表数据（`total_liab`, `money_cap`, `minority_int`, `oth_eqt_tools_p_shr`）计算隐含股权价值。
11. **隐含股票价格计算 (`valuation_model.py`):** 将隐含股权价值除以最新的 `total_share` (从 `valuation_metrics` 获取)，得到隐含股票价格。
12. **报告生成 (`main.py` 调用或独立报告模块):** 格式化并输出计算结果。

**7. 关键公式回顾 (使用数据库字段名称)**

* $NWC = \text{total\_cur\_assets} - \text{money\_cap} - (\text{total\_cur\_liab} - \text{short\_loan} - \text{non\_cur\_liab\_due\_1y})$
* $\Delta NWC_t = NWC_t - NWC_{t-1}$
* $UFCF_t = \text{operate\_profit}_t \times (1 - \text{所得税率}_t) + (\text{cash\_flow.depr\_fa\_coga\_dpba}_t + \text{cash\_flow.amort\_intang\_assets}_t) - \text{cash\_flow.c\_pay\_acq\_const\_fiolta}_t - \Delta NWC_t$
* $Re = Rf + \text{valuation\_metrics.beta} \times MRP$
* $\text{市场价值的股权 } (E) = \text{最新的valuation\_metrics.total\_share} \times \text{最新的valuation\_metrics.close}$
* $\text{市场价值的债务 } (D) = \text{最新的balance\_sheet.st\_borr} + \text{最新的balance\_sheet.non\_cur\_liab\_due\_1y} + \text{最新的balance\_sheet.long\_borr} + \text{最新的balance\_sheet.bond\_payable}$
* $V = E + D$
* $WACC = \frac{E}{V} \times Re + \frac{D}{V} \times Rd \times (1 - \text{边际所得税率})$
* $TV = (\text{预测期最后一年的operate\_profit} + \text{预测期最后一年的折旧摊销}) \times \text{退出乘数}$
* $DF_t = \frac{1}{(1 + WACC)^t}$
* $PV(CF) = CF \times DF$
* $EV = \sum PV(UFCF) + PV(TV)$
* $\text{隐含股权价值} = EV - \text{最新的balance\_sheet.total\_liab} - \text{最新的balance\_sheet.oth\_eqt\_tools\_p\_shr} - \text{最新的balance\_sheet.minority\_int} + \text{最新的balance\_sheet.money\_cap}$
* $\text{隐含股票价格} = \frac{\text{隐含股权价值}}{\text{最新的valuation\_metrics.total\_share}}$

**8. 非功能性需求**

* **性能：** 脚本应能高效地从数据库提取数据并进行计算，尤其是在处理大量历史数据或进行敏感性分析时。
* **可靠性：** 脚本应能健壮地处理数据库连接问题、数据缺失或异常情况，并提供有意义的错误提示。对于财务数据的潜在缺失或异常，应有处理策略（如填充0、使用历史平均、或提示用户）。
* **可维护性：** 代码应结构清晰，遵循Python编码规范，模块间接口定义明确。
* **灵活性：** 支持通过配置文件或命令行参数调整关键假设和数据库连接信息。
* **数据准确性：** 计算结果应能通过与历史数据和Excel模型的对比进行验证。
* **用户友好性：** 输入参数清晰，输出报告易于理解。

**9. 未来扩展考虑**

* 支持不同的终值计算方法（如永续增长法）。
* 支持敏感性分析和情景分析，方便用户批量测试不同假设下的估值结果。
* 增加数据可视化功能，展示历史趋势、预测结果和估值敏感性。
* 支持更多类型的数据源（如 API 接口）。
* 增加日志记录功能，详细记录计算过程和数据来源，便于审计和问题排查。
* 考虑数据验证和清洗规则的配置化。
* 增加对非年度报告的处理能力（如季度报告用于更及时的估值）。
* 考虑处理优先股和潜在稀释的影响。

**10. 输出报告规范**

最终报告应包含以下核心数据和信息，建议采用结构化的文本格式、CSV 文件或简单的 HTML 页面形式输出，以便用户查阅、复制或进一步处理。

**10.1 报告标题与基本信息**

* 估值报告
* 股票代码 (`ts_code`) 及名称
* 估值基准日期
* 报告生成日期
* 预测期年数

**10.2 关键输入参数与假设**

清晰列出用户输入的或模型使用的关键参数和预测假设：

* 预测期年数
* 收入增长率预测 (逐年或分阶段)
* 营业利润率预测 (逐年或目标利润率)
* 所得税率预测
* 折旧摊销占收入比或增长率预测
* 资本性支出占收入比或增长率预测
* 营运资本各项周转天数或占收入比预测 (或 ΔNWC 占收入比)
* WACC 输入参数：
    * 无风险利率 (Rf)
    * 市场风险溢价 (MRP)
    * 公司 Beta 值 (`beta`)
    * 税前债务成本 (Rd)
    * 边际所得税率
    * 股权权重 (We)
    * 债务权重 (Wd)
    * 计算出的 WACC 值
* 终值计算参数：
    * 终值计算方法 (退出乘数法)
    * 退出乘数 (Exit Multiple)

**10.3 历史财务数据摘要**

选取最近 3-5 年的核心财务数据进行摘要展示，帮助用户回顾历史表现：

* 年份/报告期 (`end_date`)
* 营业收入 (`revenue`)
* 营业利润 (`operate_profit`)
* 净利润 (`n_income_attr_p`)
* 折旧摊销 (计算值，基于 cash_flow 表字段)
* 资本性支出 (`c_pay_acq_const_fiolta`)
* 营运资本净额 (NWC, 计算值)
* 营运资本净额变化 (ΔNWC, 计算值)

**10.4 预测期财务数据与 UFCF 详情**

以表格形式详细列出预测期各年的关键预测数据和 UFCF 计算过程：

| 年份 (Year) | 预测收入 (`revenue`) | 预测营业利润 (`operate_profit`) | 预测 EBITDA (计算值) | 预测所得税 (计算值) | 税后营业利润 (NOPAT proxy) | 预测折旧摊销 | 预测资本性支出 | 预测 NWC | 预测 ΔNWC | UFCF (计算值) |
| :---------- | :------------------- | :---------------------------- | :------------------- | :------------------ | :------------------------- | :----------- | :----------- | :------- | :-------- | :-------------- |
| 预测年 1    | ...                  | ...                           | ...                  | ...                 | ...                        | ...          | ...          | ...      | ...       | ...             |
| 预测年 2    | ...                  | ...                           | ...                  | ...                 | ...                        | ...          | ...          | ...      | ...       | ...             |
| ...         | ...                  | ...                           | ...                  | ...                 | ...                        | ...          | ...          | ...      | ...       | ...             |
| 预测期末年  | ...                  | ...                           | **[预测期末年 EBITDA]** | ...                 | ...                        | ...          | ...          | ...      | ...       | ...             |

**10.5 终值计算详情**

列出终值计算所需的数据和结果：

* 预测期最后一年的 EBITDA (计算值，**[预测期末年 EBITDA]**)
* 用户设定的退出乘数
* 计算出的终值 (TV)

**10.6 估值结果详情**

以表格形式展示现金流折现过程和最终估值结果：

| 项目            | 金额 / 比率    | 说明                     |
| :-------------- | :------------- | :----------------------- |
| WACC            | [WACC 值] %    | 加权平均资本成本         |
|                 |                |                          |
| **预测期现金流现值** |                |                          |
| 年份 / 终值     | 现金流 (UFCF/TV) | 折现期 (t)               |
| 预测年 1        | [UFCF_1]       | 1                        |
| 预测年 2        | [UFCF_2]       | 2                        |
| ...             | ...            | ...                      |
| 预测期末年      | [UFCF_N]       | N                        |
| 终值            | [TV]           | N                        |
|                 | **折现因子** | **现金流现值** |
| 预测年 1        | [DF_1]         | [PV(UFCF_1)]             |
| 预测年 2        | [DF_2]         | [PV(UFCF_2)]             |
| ...             | ...            | ...                      |
| 预测期末年      | [DF_N]         | [PV(UFCF_N)]             |
| 终值            | [DF_N]         | [PV(TV)]                 |
| **FCF 累计现值** | [$\sum PV(UFCF)$] | 预测期内 UFCF 的总现值   |
| **终值现值** | [PV(TV)]       | 终值的现值               |
| **企业价值 (EV)** | [EV 值]        | 预测期 UFCF 累计现值 + 终值现值 |
|                 |                |                          |
| **股权价值计算** |                |                          |
| 企业价值        | [EV 值]        |                          |
| 减: 总负债      | [最新的total\_liab] | 来自最新资产负债表       |
| 减: 优先股      | [最新的oth\_eqt\_tools\_p\_shr 或 0] | 来自最新资产负债表或假设 |
| 减: 少数股东权益 | [最新的minority\_int] | 来自最新资产负债表       |
| 加: 现金及现金等价物 | [最新的money\_cap] | 来自最新资产负债表       |
| **隐含股权价值** | [隐含股权价值] |                          |
|                 |                |                          |
| **每股价值计算** |                |                          |
| 隐含股权价值    | [隐含股权价值] |                          |
| 全面摊薄已发行股票数量 | [最新的valuation\_metrics.total\_share] | 来自最新估值指标表 (亿股) |
| **隐含股票价格** | [隐含股票价格] / 股 | **最终估值结果** |
|                 |                |                          |
| **复核指标** |                |                          |
| 预测期末年 EBITDA | **[预测期末年 EBITDA]** | 用于计算终值的基础 EBITDA |
| **隐含 EV/EBITDA** | **[EV 值] / [预测期末年 EBITDA]** | **计算出的企业价值与预测期末年 EBITDA 之比** |
|                 |                |                          |
| 当前市场价格    | [最新的valuation\_metrics.close] / 股 | 来自最新估值指标表       |

**10.7 免责声明**

简要说明本报告基于特定假设和历史数据，估值结果具有不确定性，仅供参考。

... (PRD 后面的章节内容保持不变)

---

我已经将“隐含 EV/EBITDA”指标添加到报告的估值结果详情部分，明确了它的计算方式（企业价值 / 预测期末年 EBITDA）。这样在生成报告时，就可以同时输出这个关键的复核指标了。