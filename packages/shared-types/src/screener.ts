/**
 * API请求体：股票筛选器参数
 */
export interface ApiStockScreenerRequest {
    // 基础指标
    pe_min?: number | null;
    pe_max?: number | null;
    pe_ttm_min?: number | null;
    pe_ttm_max?: number | null;
    pb_min?: number | null;
    pb_max?: number | null;
    ps_min?: number | null;
    ps_max?: number | null;
    ps_ttm_min?: number | null;
    ps_ttm_max?: number | null;
    free_share_min?: number | null;
    free_share_max?: number | null;

    // 市值参数 - 后端路由处理代码中使用的字段名称（单位：亿元）
    market_cap_min?: number | null;
    market_cap_max?: number | null;

    // 其他参数
    industry?: string | null;
    act_ent_type?: string | null;

    // 分页参数
    page?: number;
    page_size?: number;
}

/**
 * API响应体：单个筛选出的股票信息
 */
export interface ApiScreenedStock {
    ts_code: string;
    name: string | null;
    trade_date?: string | null;
    close?: number | null;
    turnover_rate?: number | null;
    turnover_rate_f?: number | null;
    volume_ratio?: number | null;
    pe?: number | null;
    pe_ttm?: number | null;
    pb?: number | null;
    ps?: number | null;
    ps_ttm?: number | null;
    dv_ratio?: number | null;
    dv_ttm?: number | null;
    total_share?: number | null;
    float_share?: number | null;
    free_share?: number | null;
    total_mv?: number | null;
    circ_mv?: number | null;
    industry?: string | null;
    area?: string | null;
    market?: string | null;
    act_ent_type?: string | null;
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

// 用于触发数据更新的API
export interface ApiUpdateScreenerDataRequest {
    data_type: 'basic' | 'daily' | 'all'; // 'basic' 指股票列表, 'daily' 指行情指标
}

export interface ApiUpdateScreenerDataResponse {
    status: string; // e.g., "Update started", "Update completed", "Error"
    message: string;
    last_update_times?: {
        stock_basic?: string | null;
        daily_basic?: string | null;
    };
}
