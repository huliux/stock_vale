// packages/shared-types/src/index.ts

/**
 * API请求体：DCF估值参数
 * 注意：百分比值应作为小数传递，例如 WACC 8.5% 应传递 0.085
 */
export interface ApiDcfValuationRequest {
    stock_code: string; // 例如 "000001.SZ" // ts_code in backend
    valuation_date?: string | null; // YYYY-MM-DD, matches backend
    // discount_rate?: number | null; // WACC, e.g., 0.085. Removed, WACC now derived from components.
    terminal_growth_rate?: number | null; // 永续增长率，例如 0.025.
    prediction_years?: number | null; // 预测年限，例如 5 或 10. // forecast_years in backend
    cagr_decay_rate?: number | null; // 历史CAGR年衰减率 (0-1)

    // 利润率预测
    op_margin_forecast_mode?: 'historical_median' | 'transition_to_target';
    target_operating_margin?: number | null; // 例如 0.15 for 15%
    op_margin_transition_years?: number | null;

    // SGA & RD 费用率预测
    sga_rd_ratio_forecast_mode?: 'historical_median' | 'transition_to_target';
    target_sga_rd_to_revenue_ratio?: number | null; // 例如 0.10 for 10%
    sga_rd_transition_years?: number | null;

    // D&A 占收入比预测
    da_ratio_forecast_mode?: 'historical_median' | 'transition_to_target';
    target_da_to_revenue_ratio?: number | null; // 例如 0.05 for 5%
    da_ratio_transition_years?: number | null;

    // Capex 占收入比预测
    capex_ratio_forecast_mode?: 'historical_median' | 'transition_to_target';
    target_capex_to_revenue_ratio?: number | null; // 例如 0.03 for 3%
    capex_ratio_transition_years?: number | null;

    // NWC 周转天数预测
    nwc_days_forecast_mode?: 'historical_median' | 'transition_to_target';
    target_accounts_receivable_days?: number | null;
    target_inventory_days?: number | null;
    target_accounts_payable_days?: number | null;
    nwc_days_transition_years?: number | null;

    // 其他 NWC 比率预测
    other_nwc_ratio_forecast_mode?: 'historical_median' | 'transition_to_target';
    target_other_current_assets_to_revenue_ratio?: number | null;
    target_other_current_liabilities_to_revenue_ratio?: number | null;
    other_nwc_ratio_transition_years?: number | null;

    // 税率
    target_effective_tax_rate?: number | null; // 例如 0.25 for 25%

    // WACC 计算参数
    wacc_weight_mode?: 'target' | 'market';
    target_debt_ratio?: number | null; // 例如 0.30 for 30%
    cost_of_debt?: number | null; // 例如 0.05 for 5%
    risk_free_rate?: number | null; // 例如 0.025 for 2.5%
    beta?: number | null;
    market_risk_premium?: number | null; // 例如 0.06 for 6%
    size_premium?: number | null; // 例如 0.01 for 1%

    // 终值计算参数
    terminal_value_method?: 'exit_multiple' | 'perpetual_growth';
    exit_multiple?: number | null;

    // LLM 控制参数
    request_llm_summary?: boolean;
    llm_provider?: 'deepseek' | 'custom_openai' | null;
    llm_model_id?: string | null;
    llm_api_base_url?: string | null;
    llm_temperature?: number | null;
    llm_top_p?: number | null;
    llm_max_tokens?: number | null;

    // 敏感性分析 - 保持与后端一致，但前端表单可能简化此部分
    sensitivity_analysis?: ApiSensitivityAnalysisRequest | null; // Reference backend model structure
}

/**
 * API请求体/响应体：敏感性分析轴定义 (与后端 sensitivity_models.py 中的 SensitivityAxisRequest 一致)
 */
export interface ApiSensitivityAxis {
    parameter_name: string;
    values?: (number | string | null)[] | null;
    min_value?: number | null;
    max_value?: number | null;
    step?: number | null;
    points?: number | null;
    value_type?: 'percentage' | 'absolute' | 'string';
}

/**
 * API请求体：敏感性分析配置 (与后端 sensitivity_models.py 中的 SensitivityAnalysisRequest 一致)
 */
export interface ApiSensitivityAnalysisRequest {
    row_axis: ApiSensitivityAxis; // Renamed from axis1
    column_axis: ApiSensitivityAxis; // Renamed from axis2
    output_metrics: string[]; // e.g., ["intrinsic_value_per_share", "upside_potential"]
}


/**
 * API响应体：股票基本信息
 */
export interface ApiStockInfo {
    ts_code: string | null;
    name: string | null;
    latest_price: number | null;
    base_report_date: string | null; // 估值所依据的最新年报日期 (YYYY-MM-DD)，例如 "2023-12-31"
    currency: string | null; // 例如 "CNY"
    exchange: string | null; // 例如 "SZSE"
    industry: string | null; // 行业
    market?: string | null; // 市场类型, e.g., "A"
    act_name?: string | null; // 实际控制人名称
    act_ent_type?: string | null; // 实际控制人企业性质
    latest_annual_diluted_eps?: number | null; // 最新年报稀释每股收益
    dividend_yield?: number | null; // 股息率 (小数, e.g., 0.0333 for 3.33%)
    ttm_dps?: number | null; // TTM每股股息
}

/**
 * API响应体：核心估值指标 (对应后端 DcfForecastDetails)
 */
export interface ApiCoreMetrics {
    enterprise_value: number | null;
    equity_value: number | null;
    value_per_share: number | null; // 每股内在价值 (原 intrinsic_value_per_share)
    net_debt: number | null;
    pv_forecast_ufcf: number | null;
    pv_terminal_value: number | null;
    terminal_value: number | null;
    wacc_used: number | null; // 实际使用的WACC (小数形式)
    cost_of_equity_used: number | null;
    terminal_value_method_used: string | null;
    exit_multiple_used: number | null; // 终值计算中使用的退出乘数 (如果适用) (原 exit_multiple)
    perpetual_growth_rate_used: number | null;
    forecast_period_years: number | null;
    dcf_implied_diluted_pe: number | null; // DCF模型隐含的稀释市盈率
    base_ev_ebitda: number | null; // 新增 EV/EBITDA from DcfForecastDetails
    implied_perpetual_growth_rate: number | null; // 隐含的永续增长率 (如果使用退出乘数法)
    // upside_potential is calculated on the frontend
}

/**
 * API响应体：股息分析
 */
export interface ApiDividendAnalysis {
    current_yield_pct: number | null;
    avg_dividend_3y: number | null;
    payout_ratio_pct: number | null;
}

/**
 * API响应体：增长分析
 */
export interface ApiGrowthAnalysis {
    net_income_cagr_3y: number | null;
    revenue_cagr_3y: number | null;
}

/**
 * API响应体：其他分析容器
 */
export interface ApiOtherAnalysis {
    dividend_analysis: ApiDividendAnalysis | null;
    growth_analysis: ApiGrowthAnalysis | null;
}

/**
 * API响应体：详细财务预测中的单年数据行
 */
export interface ApiDetailedForecastYear {
    year: number | string; // 年份或特殊标记如 "基准年"
    revenue: number | null;
    ebit: number | null;
    nopat: number | null;
    d_a: number | null; // Was depreciation_amortization, matches backend 'd_a'
    capex: number | null;
    delta_nwc: number | null; // Was change_in_nwc, matches backend 'delta_nwc'
    ufcf: number | null; // Was fcf, matches backend 'ufcf'
    pv_ufcf: number | null; // Was pv_fcf, assuming backend will provide 'pv_ufcf' for per-year PV
    // 可以根据后端实际提供的列进行调整
}

/**
 * API响应体：敏感性分析表格
 * 键是指标名称 (例如 "每股价值")，值是一个二维数组代表表格数据
 */
export type ApiSensitivityAnalysisTable = (string | number | null)[][];

export interface ApiSensitivityAnalysisTables {
    [metric_name: string]: ApiSensitivityAnalysisTable; // Key: output metric name, Value: 2D array for the table
}

/**
 * API响应体：完整的敏感性分析结果结构 (与后端 sensitivity_models.py 中的 SensitivityAnalysisResult 一致)
 */
export interface ApiSensitivityAnalysisResult {
    row_parameter: string; // Name of the parameter on the rows
    column_parameter: string; // Name of the parameter on the columns
    row_values: (number | string)[]; // Actual values used for rows after generation/validation
    column_values: (number | string)[]; // Actual values used for columns - Reverted for consistency with row_values and to simplify formatting logic
    result_tables: ApiSensitivityAnalysisTables; // Tables for each output metric
}

/**
 * API响应体：对应后端 ValuationResultsContainer
 */
export interface ApiValuationResultsContainer {
    latest_price: number | null;
    current_pe: number | null;
    current_pb: number | null;
    dcf_forecast_details: ApiCoreMetrics | null; // ApiCoreMetrics now maps to DcfForecastDetails
    other_analysis: ApiOtherAnalysis | null;
    llm_analysis_summary: string | null;
    data_warnings: string[] | null;
    detailed_forecast_table: ApiDetailedForecastYear[] | null;
    sensitivity_analysis_result: ApiSensitivityAnalysisResult | null;
    historical_financial_summary: Record<string, any>[] | null; // or more specific type
    historical_ratios_summary: Record<string, any>[] | null; // or more specific type
    special_industry_warning: string | null;
}

/**
 * API响应体：完整的DCF估值结果 (对应后端 StockValuationResponse)
 */
export interface ApiDcfValuationResponse {
    stock_info: ApiStockInfo | null;
    valuation_results: ApiValuationResultsContainer | null; // Changed from core_metrics and other fields
    error?: string | null; // Added optional error field
    // execution_details: { timestamp: string; request_id: string; } // 可选的执行元数据
}


// 股票筛选器类型

/**
 * API请求体：股票筛选器参数
 */
export interface ApiStockScreenerRequest {
    pe_min?: number | null;
    pe_max?: number | null;
    pb_min?: number | null;
    pb_max?: number | null;
    market_cap_min?: number | null; // 单位：亿元
    market_cap_max?: number | null; // 单位：亿元
    // 可以添加其他筛选条件，如行业、交易所等
    // page?: number; // 用于分页
    // page_size?: number; // 用于分页
}

/**
 * API响应体：单个筛选出的股票信息
 */
export interface ApiScreenedStock {
    ts_code: string;
    name: string | null;
    close?: number | null; // Renamed from latest_price
    pe_ttm?: number | null; // 市盈率 TTM
    pb?: number | null;     // 市净率
    market_cap_billion?: number | null; // Renamed from total_market_cap (总市值（亿元）)
    industry?: string | null;
    // 可以根据需要添加更多字段，例如换手率、股息率等
}

/**
 * API响应体：股票筛选器结果
 */
export interface ApiStockScreenerResponse {
    results: ApiScreenedStock[];
    total: number; // 符合条件的总股票数 (用于分页)
    page?: number;
    page_size?: number;
    last_data_update_time?: string | null; // 数据源的最后更新时间
}

// 用于触发数据更新的API（可能不需要请求体，或者包含要更新的数据类型）
export interface ApiUpdateScreenerDataRequest {
    data_type: 'basic' | 'daily' | 'all'; // 'basic' 指股票列表, 'daily' 指行情指标
}

export interface ApiUpdateScreenerDataResponse {
    status: string; // e.g., "Update started", "Update completed", "Error"
    message: string;
    last_update_times?: {
        stock_basic?: string | null;
        daily_basic?: string | null; // 可能需要更细致的日期
    };
}
