// packages/shared-types/src/index.ts

/**
 * API请求体：DCF估值参数
 * 注意：百分比值应作为小数传递，例如 WACC 8.5% 应传递 0.085
 */
export interface ApiDcfValuationRequest {
    stock_code: string; // 例如 "000001.SZ"
    discount_rate?: number | null; // WACC，例如 0.085. Optional, backend will use defaults if None.
    terminal_growth_rate?: number | null; // 永续增长率，例如 0.025. Optional.
    prediction_years?: number | null; // 预测年限，例如 5 或 10. Optional.

    // 未来可以扩展更多详细的财务假设参数
    // 例如：
    // revenue_growth_assumptions: { mode: 'auto' | 'manual', rates?: number[] };
    // operating_margin_assumptions: { mode: 'historical_median' | 'target', target_value?: number };
    // ...等等
}

/**
 * API响应体：股票基本信息
 */
export interface ApiStockInfo {
    ts_code: string | null;
    name: string | null;
    latest_price: number | null;
    base_financial_year: string | null; // 估值所依据的最新年报年份，例如 "2023"
    currency: string | null; // 例如 "CNY"
    exchange: string | null; // 例如 "SZSE"
    industry: string | null; // 行业
}

/**
 * API响应体：核心估值指标
 */
export interface ApiCoreMetrics {
    intrinsic_value_per_share: number | null; // 每股内在价值
    upside_potential: number | null; // 上升空间 (小数形式, e.g., 0.25 for 25%)
    dcf_implied_diluted_pe: number | null; // DCF模型隐含的稀释市盈率
    exit_multiple: number | null; // 终值计算中使用的退出乘数 (如果适用)
    implied_terminal_growth_rate: number | null; // 隐含的永续增长率 (如果使用退出乘数法)
    wacc_used: number | null; // 实际使用的WACC (小数形式)
}

/**
 * API响应体：详细财务预测中的单年数据行
 */
export interface ApiDetailedForecastYear {
    year: number | string; // 年份或特殊标记如 "基准年"
    revenue: number | null;
    ebit: number | null;
    nopat: number | null;
    depreciation_amortization: number | null;
    capex: number | null;
    change_in_nwc: number | null;
    fcf: number | null;
    pv_fcf: number | null;
    // 可以根据后端实际提供的列进行调整
}

/**
 * API响应体：敏感性分析表格
 * 键是指标名称 (例如 "每股价值")，值是一个二维数组代表表格数据
 */
export type ApiSensitivityAnalysisTable = (string | number | null)[][];

export interface ApiSensitivityAnalysisTables {
    [metric_name: string]: ApiSensitivityAnalysisTable;
}


/**
 * API响应体：完整的DCF估值结果
 */
export interface ApiDcfValuationResponse {
    stock_info: ApiStockInfo | null;
    core_metrics: ApiCoreMetrics | null;
    detailed_forecast_table: ApiDetailedForecastYear[] | null;
    sensitivity_analysis_tables: ApiSensitivityAnalysisTables | null;
    llm_summary: string | null;
    data_warnings: string[] | null;
    // execution_details: { timestamp: string; request_id: string; } // 可选的执行元数据
}


// 未来可以为股票筛选器也定义类型

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
    latest_price?: number | null;
    pe_ttm?: number | null; // 市盈率 TTM
    pb?: number | null;     // 市净率
    total_market_cap?: number | null; // 总市值（亿元）
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
