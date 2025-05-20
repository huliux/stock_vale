/**
 * 扩展的筛选出的股票信息接口，包含所有可能的返回字段
 */
export interface ExtendedApiScreenedStock {
    // 基本信息
    ts_code: string;
    name: string | null;

    // 交易信息
    trade_date?: string | null;
    close?: number | null;
    turnover_rate?: number | null;
    turnover_rate_f?: number | null;
    volume_ratio?: number | null;

    // 估值指标
    pe?: number | null;
    pe_ttm?: number | null;
    pb?: number | null;
    ps?: number | null;
    ps_ttm?: number | null;

    // 股息信息
    dv_ratio?: number | null;
    dv_ttm?: number | null;

    // 股本信息
    total_share?: number | null;
    float_share?: number | null;
    free_share?: number | null;
    total_mv?: number | null;
    circ_mv?: number | null;

    // 其他信息
    market_cap_billion?: number | null;
    total_market_cap?: number | null; // 别名 market_cap_billion
    latest_price?: number | null; // 别名 close
    industry?: string | null;
    area?: string | null;
    fullname?: string | null;
    enname?: string | null;
    cnspell?: string | null;
    market?: string | null;
    exchange?: string | null;
    curr_type?: string | null;
    list_status?: string | null;
    list_date?: string | null;
    delist_date?: string | null;
    is_hs?: string | null;
    act_name?: string | null;
    act_ent_type?: string | null;
}
