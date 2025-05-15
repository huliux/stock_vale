<template>
    <div class="dcf-results-display">
        <h4>估值结果</h4>

        <div v-if="isLoading" class="loading-indicator">正在加载估值结果...</div>
        <div v-else-if="error" class="error-message">{{ error }}</div>
        <div v-else-if="!valuationData && hasCalculated" class="info-message">未能获取估值结果。</div>
        <div v-else-if="!valuationData && !hasCalculated" class="info-message">请输入参数并开始估值。</div>

        <div v-if="valuationData" class="results-content">
            <!-- 基本信息 -->
            <section class="result-section">
                <h5>基本信息</h5>
                <div class="info-grid two-rows">
                    <div><strong>股票代码:</strong> {{ valuationData.stock_info?.ts_code || 'N/A' }}</div>
                    <div><strong>股票名称:</strong> {{ valuationData.stock_info?.name || 'N/A' }}</div>
                    <div><strong>所属行业:</strong> {{ valuationData.stock_info?.industry || 'N/A' }}</div>
                    <div><strong>市场类型:</strong> {{ valuationData.stock_info?.market || 'N/A' }}</div>
                    <div><strong>实控人:</strong> {{ valuationData.stock_info?.act_name || 'N/A' }}</div>
                    <div><strong>实控人性质:</strong> {{ valuationData.stock_info?.act_ent_type || 'N/A' }}</div>

                    <div><strong>最新价格:</strong> {{ formatNumber(latestPriceForDisplay, 2) }}</div>
                    <div><strong>当前PE:</strong> {{ formatNumber(valuationData.valuation_results?.current_pe, 2) }}</div>
                    <div><strong>当前PB:</strong> {{ formatNumber(valuationData.valuation_results?.current_pb, 2) }}</div>
                    <div><strong>年报EPS:</strong> {{ formatNumber(valuationData.stock_info?.latest_annual_diluted_eps, 2)
                        }}</div>
                    <div><strong>股息率 (TTM):</strong> {{ formatPercentage(valuationData.stock_info?.dividend_yield) }}
                    </div>
                    <div><strong>TTM每股股息:</strong> {{ formatNumber(valuationData.stock_info?.ttm_dps, 4) }}</div>
                    <div class="full-width-item"><strong>基准年报:</strong> {{ baseReportYearForDisplay || 'N/A' }}</div>
                </div>
            </section>

            <!-- 核心估值指标 -->
            <section class="result-section">
                <h5>核心估值指标</h5>
                <div class="metrics-grid two-rows">
                    <div>
                        <span class="metric-label">每股内在价值:</span>
                        <span class="metric-value">{{
                            formatNumber(valuationData.valuation_results?.dcf_forecast_details?.value_per_share, 2)
                            }}</span>
                    </div>
                    <div>
                        <span class="metric-label">上升空间:</span>
                        <span :class="getUpsideClass(calculatedUpsidePotential)">
                            {{ formatPercentage(calculatedUpsidePotential) }}
                        </span>
                    </div>
                    <div>
                        <span class="metric-label">DCF隐含PE:</span>
                        <span class="metric-value">{{
                            formatNumber(valuationData.valuation_results?.dcf_forecast_details?.dcf_implied_diluted_pe,
                                2)
                        }}x</span>
                    </div>
                    <div>
                        <span class="metric-label">隐含EV/EBITDA:</span>
                        <span class="metric-value">{{
                            formatNumber(valuationData.valuation_results?.dcf_forecast_details?.base_ev_ebitda, 2)
                            }}x</span>
                    </div>
                    <div>
                        <span class="metric-label">WACC:</span>
                        <span class="metric-value">{{
                            formatPercentage(valuationData.valuation_results?.dcf_forecast_details?.wacc_used) }}</span>
                    </div>
                    <div>
                        <span class="metric-label">Ke (股权成本):</span>
                        <span class="metric-value">{{
                            formatPercentage(valuationData.valuation_results?.dcf_forecast_details?.cost_of_equity_used)
                            }}</span>
                    </div>

                    <div>
                        <span class="metric-label">企业价值 (EV):</span>
                        <span class="metric-value">{{
                            formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.enterprise_value)
                            }} 亿</span>
                    </div>
                    <div>
                        <span class="metric-label">股权价值:</span>
                        <span class="metric-value">{{
                            formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.equity_value)
                            }} 亿</span>
                    </div>
                    <div>
                        <span class="metric-label">UFCF现值:</span>
                        <span class="metric-value">{{
                            formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.pv_forecast_ufcf)
                            }} 亿</span>
                    </div>
                    <div>
                        <span class="metric-label">终值现值:</span>
                        <span class="metric-value">{{
                            formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.pv_terminal_value)
                            }} 亿</span>
                    </div>
                    <div>
                        <span class="metric-label">终值:</span>
                        <span class="metric-value">{{
                            formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.terminal_value)
                            }} 亿</span>
                    </div>
                    <div>
                        <span class="metric-label">净债务:</span>
                        <span class="metric-value">{{
                            formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.net_debt)
                            }} 亿</span>
                    </div>

                    <div>
                        <span class="metric-label">使用退出乘数:</span>
                        <span class="metric-value">{{
                            valuationData.valuation_results?.dcf_forecast_details?.terminal_value_method_used ===
                                'exit_multiple' && valuationData.valuation_results?.dcf_forecast_details?.exit_multiple_used
                                !== null ?
                                formatNumber(valuationData.valuation_results?.dcf_forecast_details?.exit_multiple_used, 1) +
                                'x' : 'N/A'
                        }}</span>
                    </div>
                    <div>
                        <span class="metric-label">隐含永续增长率:</span>
                        <span class="metric-value">{{
                            formatPercentage(valuationData.valuation_results?.dcf_forecast_details?.implied_perpetual_growth_rate)
                            }}</span>
                    </div>
                </div>
            </section>

            <!-- 详细财务预测表格 -->
            <section class="result-section"
                v-if="valuationData.valuation_results?.detailed_forecast_table && valuationData.valuation_results?.detailed_forecast_table.length > 0">
                <h5>高级分析 - 详细财务预测 (单位：元)</h5>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>年份 (Year)</th>
                                <th>营业收入 (Revenue)</th>
                                <th>息税前利润 (EBIT)</th>
                                <th>税后净营业利润 (NOPAT)</th>
                                <th>折旧与摊销 (D&A)</th>
                                <th>资本性支出 (CapEx)</th>
                                <th>净营运资本变动 (ΔNWC)</th>
                                <th>无杠杆自由现金流 (FCF)</th>
                                <th>FCF现值 (PV of FCF)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="row in valuationData.valuation_results.detailed_forecast_table" :key="row.year">
                                <td>{{ row.year }}</td>
                                <td>{{ formatNumber(row.revenue) }}</td>
                                <td>{{ formatNumber(row.ebit) }}</td>
                                <td>{{ formatNumber(row.nopat) }}</td>
                                <td>{{ formatNumber(row.d_a) }}</td>
                                <td>{{ formatNumber(row.capex) }}</td>
                                <td>{{ formatNumber(row.delta_nwc) }}</td>
                                <td>{{ formatNumber(row.ufcf) }}</td>
                                <td>{{ formatNumber(row.pv_ufcf) }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- 历史财务摘要 -->
            <section class="result-section"
                v-if="valuationData.valuation_results?.historical_financial_summary && valuationData.valuation_results?.historical_financial_summary.length > 0">
                <h5>高级分析 - 历史财务摘要</h5>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th v-for="(colValue, colKey) in valuationData.valuation_results.historical_financial_summary[0]"
                                    :key="`hist-summary-header-${String(colKey)}`">
                                    {{ getHistoricalHeaderName(String(colKey)) }}
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(row, rowIndex) in valuationData.valuation_results.historical_financial_summary"
                                :key="`hist-summary-row-${rowIndex}`">
                                <td v-for="(cellValue, cellKey) in row"
                                    :key="`hist-summary-cell-${rowIndex}-${String(cellKey)}`">
                                    <span v-if="String(cellKey) === '科目' || String(cellKey) === '报表类型'">
                                        {{ cellValue }}
                                    </span>
                                    <span v-else>
                                        {{ formatNumber(cellValue, typeof cellValue === 'number' &&
                                            !Number.isInteger(cellValue) ? 2 : 0) }}
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- 历史财务比率 -->
            <section class="result-section"
                v-if="valuationData.valuation_results?.historical_ratios_summary && valuationData.valuation_results?.historical_ratios_summary.length > 0">
                <h5>高级分析 - 历史财务比率</h5>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>{{ getHistoricalHeaderName('metric_name') }}</th>
                                <th>{{ getHistoricalHeaderName('value') }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(row, rowIndex) in valuationData.valuation_results.historical_ratios_summary"
                                :key="`hist-ratios-row-${rowIndex}`">
                                <td>
                                    {{ getHistoricalHeaderName(String(row.metric_name)) }}
                                </td>
                                <td>
                                    {{ formatNumber(row.value, typeof row.value === 'number' &&
                                        !Number.isInteger(row.value) ? 2 : 0) }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- 敏感性分析表格 -->
            <section class="result-section"
                v-if="valuationData.valuation_results?.sensitivity_analysis_result && valuationData.valuation_results?.sensitivity_analysis_result.result_tables && Object.keys(valuationData.valuation_results?.sensitivity_analysis_result.result_tables).length > 0">
                <h5>高级分析 - 敏感性分析</h5>
                <div v-for="(tableData, metricKey) in valuationData.valuation_results.sensitivity_analysis_result.result_tables"
                    :key="String(metricKey)" class="sensitivity-table-item">
                    <h6>{{ getMetricDisplayName(String(metricKey)) }} ({{
                        getAxisParamDisplayName(valuationData.valuation_results.sensitivity_analysis_result.row_parameter)
                        }} vs {{
                            getAxisParamDisplayName(valuationData.valuation_results.sensitivity_analysis_result.column_parameter)
                        }})</h6>
                    <div class="table-responsive">
                        <table>
                            <thead>
                                <tr>
                                    <th>
                                        {{
                                            getAxisParamDisplayName(valuationData.valuation_results.sensitivity_analysis_result.row_parameter)
                                        }}
                                        /
                                        {{
                                            getAxisParamDisplayName(valuationData.valuation_results.sensitivity_analysis_result.column_parameter)
                                        }}
                                    </th>
                                    <th v-for="(colValue, colIndex) in valuationData.valuation_results.sensitivity_analysis_result.column_values"
                                        :key="`col-header-${colIndex}`">
                                        {{ getFormattedColAxisValue(colIndex) }}
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(row, rowIndex) in tableData" :key="`sa-row-${rowIndex}`">
                                    <td><strong>{{
                                        getFormattedRowAxisValue(rowIndex)
                                            }}</strong>
                                    </td>
                                    <td v-for="(cellValue, cellIndex) in row" :key="`sa-cell-${rowIndex}-${cellIndex}`"
                                        :class="{ 'is-center-cell': centerRowIndex(String(metricKey)).value === rowIndex && centerColIndex(String(metricKey)).value === cellIndex }">
                                        {{ formatSensitivityCellValue(cellValue, String(metricKey)) }}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <!-- TODO: LLM 分析摘要 -->
            <section class="result-section" v-if="valuationData.valuation_results?.llm_analysis_summary">
                <h5>LLM 分析摘要</h5>
                <div class="llm-summary" v-html="renderMarkdown(valuationData.valuation_results.llm_analysis_summary)">
                </div>
            </section>

            <!-- 数据警告 -->
            <section class="result-section"
                v-if="valuationData.valuation_results?.data_warnings && valuationData.valuation_results?.data_warnings.length > 0">
                <h5>数据警告</h5>
                <ul>
                    <li v-for="(warning, index) in valuationData.valuation_results.data_warnings" :key="index"
                        class="warning-message">{{
                            warning }}</li>
                </ul>
            </section>
        </div>
    </div>
</template>

<script setup lang="ts">
// defineProps is a compiler macro and no longer needs to be imported.
// import DOMPurify from 'dompurify'; // For v-html, if LLM output is complex HTML
// For basic markdown to HTML, a simpler library or custom function might be used.
// For now, we'll assume LLM summary is safe or simple HTML/markdown.

// Import types from shared-types
import { computed } from 'vue';
import type {
    ApiDcfValuationResponse,
    // ApiStockInfo, // Not needed if ApiDcfValuationResponse is used directly for prop
    // ApiCoreMetrics, // Not needed if ApiDcfValuationResponse is used directly for prop
    // ApiDetailedForecastYear, // These would be used if we destructured props further
    // ApiSensitivityAnalysisTables 
} from '@shared-types/index';


interface Props {
    valuationData: ApiDcfValuationResponse | null; // Use the imported type
    isLoading: boolean;
    error: string | null;
    hasCalculated: boolean; // To distinguish initial state from calculation attempt
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const props = defineProps<Props>();

const baseReportYearForDisplay = computed(() => {
    const reportDate = props.valuationData?.stock_info?.base_report_date;
    if (reportDate && typeof reportDate === 'string') {
        return reportDate.split('-')[0];
    }
    return 'N/A';
});

const latestPriceForDisplay = computed(() => {
    return props.valuationData?.valuation_results?.latest_price ?? props.valuationData?.stock_info?.latest_price ?? 'N/A';
});

const calculatedUpsidePotential = computed(() => {
    const valuePerShare = props.valuationData?.valuation_results?.dcf_forecast_details?.value_per_share;
    const latestPrice = props.valuationData?.valuation_results?.latest_price ?? props.valuationData?.stock_info?.latest_price;

    if (typeof valuePerShare === 'number' && typeof latestPrice === 'number' && latestPrice !== 0) {
        return (valuePerShare / latestPrice) - 1;
    }
    return 'N/A'; // Return 'N/A' as string if calculation is not possible, formatPercentage will handle it
});


const metricDisplayNames: Record<string, string> = {
    "value_per_share": "每股价值",
    "enterprise_value": "企业价值 (EV)",
    "equity_value": "股权价值",
    "tv_ev_ratio": "终值/企业价值 (%)",
    "dcf_implied_pe": "DCF隐含PE", // Streamlit uses "DCF模型隐含的稀释市盈率"
    "dcf_implied_diluted_pe": "DCF隐含PE", // Changed to match screenshot header, assuming it's for diluted
    "ev_ebitda": "EV/EBITDA"
};

const getMetricDisplayName = (metricKey: string): string => {
    return metricDisplayNames[metricKey] || metricKey;
};

const axisParamDisplayNames: Record<string, string> = {
    "wacc": "WACC",
    "exit_multiple": "退出乘数",
    "perpetual_growth_rate": "永续增长率",
    "terminal_growth_rate": "永续增长率" // Alias for consistency
};

const getAxisParamDisplayName = (paramKey: string | undefined): string => {
    if (!paramKey) return 'N/A';
    return axisParamDisplayNames[paramKey.toLowerCase()] || paramKey;
};


const historicalTableHeadersMap: Record<string, string> = {
    report_date: '报告日期',
    ts_code: '代码',
    ann_date: '公告日期',
    f_ann_date: '实际公告日期',
    end_date: '报告期',
    comp_type: '公司类型',
    // 资产负债表 (示例)
    total_assets: '总资产',
    total_liab: '总负债',
    total_hldr_eqy_inc_min_int: '股东权益合计',
    // 利润表 (示例)
    revenue: '营业总收入',
    oper_cost: '营业总成本',
    net_profit: '净利润',
    // 现金流量表 (示例)
    n_cashflow_act: '经营活动现金流量净额',
    // 比率 (示例)
    metric_name: '指标名称',
    value: '数值',
    // 历史财务比率的键名 (来自 DataProcessor.historical_ratios)
    cogs_to_revenue_ratio: '成本占收比',
    sga_rd_to_revenue_ratio: '销售管理研发费用率',
    operating_margin_median: '营业利润率(中位数)',
    da_to_revenue_ratio: '折旧与摊销占收比',
    capex_to_revenue_ratio: '资本支出占收比',
    accounts_receivable_days: '应收账款周转天数',
    inventory_days: '存货周转天数',
    accounts_payable_days: '应付账款周转天数',
    other_current_assets_to_revenue_ratio: '其他流动资产占收比',
    other_current_liabilities_to_revenue_ratio: '其他流动负债占收比',
    nwc_to_revenue_ratio: '净营运资本占收比',
    last_historical_nwc: '期末历史NWC',
    effective_tax_rate: '有效税率',
    historical_revenue_cagr: '历史营收CAGR'
    // Add more mappings as needed based on actual keys from backend
};

const getHistoricalHeaderName = (key: string): string => {
    return historicalTableHeadersMap[key] || key; // Fallback to original key if no mapping
};

// const formatNumber = (value: number | null | undefined | string, precision: number = 0): string => {
//     if (value === 'N/A' || value === null || value === undefined || (typeof value === 'number' && isNaN(value))) return 'N/A';
//     const numValue = Number(value);
//     if (isNaN(numValue)) return 'N/A';
//     return numValue.toLocaleString(undefined, { minimumFractionDigits: precision, maximumFractionDigits: precision });
// };

const formatNumber = (rawValue: string | number | null | undefined, precision: number = 0): string => {
    const value: string | number | null | undefined = rawValue;

    if (value === 'N/A' || value === null || value === undefined) return 'N/A';
    if (typeof value === 'number' && isNaN(value)) return 'N/A';

    const numValue = Number(value); // Handles string-to-number conversion
    if (isNaN(numValue)) {
        // If value was a string that couldn't be converted to a number (and wasn't 'N/A')
        // Depending on desired behavior, you might return the original string or 'N/A'
        // For now, if it's not 'N/A' initially but can't become a number, treat as 'N/A' for formatting.
        // However, if the original string was meaningful (e.g. text from API), this might lose info.
        // Given the context of a number formatting function, 'N/A' seems appropriate.
        return 'N/A';
    }
    // For very small or very large numbers, toLocaleString might use scientific notation.
    // Consider toFixed if specific non-scientific formatting is always needed.
    return numValue.toLocaleString(undefined, { minimumFractionDigits: precision, maximumFractionDigits: precision });
};

const formatLargeNumberInBillions = (value: number | null | undefined | string, precision: number = 2): string => {
    if (value === 'N/A' || value === null || value === undefined || (typeof value === 'number' && isNaN(value))) return 'N/A';
    const numValue = Number(value);
    if (isNaN(numValue)) return 'N/A';
    return (numValue / 1e8).toLocaleString(undefined, { minimumFractionDigits: precision, maximumFractionDigits: precision });
};

const formatPercentage = (value: number | null | undefined | string): string => {
    if (value === 'N/A' || value === null || value === undefined || (typeof value === 'number' && isNaN(value))) return 'N/A';
    const numValue = Number(value);
    if (isNaN(numValue)) return 'N/A';
    return `${(numValue * 100).toFixed(2)}%`;
};

const formatSensitivityCellValue = (value: string | number | null | undefined, metricKey: string): string => {
    if (value === null || value === undefined) {
        return 'N/A';
    }
    const numValue = Number(value); // Attempt to convert to number

    if (isNaN(numValue)) { // Check if conversion failed
        return 'N/A';
    }

    switch (metricKey) {
        case 'value_per_share':
            return numValue.toFixed(2);
        case 'enterprise_value':
        case 'equity_value':
            return (numValue / 1e8).toFixed(2) + ' 亿';
        case 'dcf_implied_pe':
        case 'dcf_implied_diluted_pe':
            return numValue.toFixed(2) + 'x';
        case 'ev_ebitda':
            return numValue.toFixed(1) + 'x';
        case 'tv_ev_ratio':
            return formatPercentage(numValue);
        default:
            return numValue.toFixed(2);
    }
};

// Helper function to get formatted column axis value
const getFormattedColAxisValue = (colIndex: number): string => {
    const colValue = props.valuationData?.valuation_results?.sensitivity_analysis_result?.column_values[colIndex];
    const colParamName = props.valuationData?.valuation_results?.sensitivity_analysis_result?.column_parameter;
    return formatAxisValue(String(colValue ?? ''), colParamName);
};

// Helper function to get formatted row axis value
const getFormattedRowAxisValue = (rowIndex: number): string => {
    const rowValue = props.valuationData?.valuation_results?.sensitivity_analysis_result?.row_values[rowIndex];
    const rowParamName = props.valuationData?.valuation_results?.sensitivity_analysis_result?.row_parameter;
    return formatAxisValue(String(rowValue ?? ''), rowParamName);
};

const formatAxisValue = (valueAsString: string, paramNameInput: string | undefined): string => {
    const paramName = String(paramNameInput || '').toLowerCase();
    let numericValue: number | undefined = undefined;

    if (valueAsString.trim() === '' || valueAsString.toLowerCase() === 'n/a' || valueAsString.toLowerCase() === 'null' || valueAsString.toLowerCase() === 'undefined') {
        return 'N/A';
    }

    if (!isNaN(Number(valueAsString))) {
        numericValue = Number(valueAsString);
    }

    if (numericValue !== undefined) {
        if (paramName.includes('wacc') ||
            paramName.includes('growth_rate') ||
            paramName.includes('rate') ||
            paramName.includes('margin')) {
            return formatPercentage(numericValue); // formatPercentage can handle number
        }
        return numericValue.toFixed(paramName.includes('multiple') ? 1 : 2);
    }
    // If not a number or couldn't be parsed, return the original string
    return valueAsString;
};

const getUpsideClass = (upside: number | null | undefined | string): string => {
    if (upside === 'N/A' || upside === null || upside === undefined) return 'metric-value';
    const numUpside = Number(upside);
    if (isNaN(numUpside)) return 'metric-value';
    return numUpside >= 0 ? 'metric-value positive-upside' : 'metric-value negative-upside';
};

// Basic markdown rendering (very simplified, consider a library for complex markdown)
const renderMarkdown = (markdownText: string | null | undefined): string => {
    if (!markdownText) return '';
    // This is a very naive implementation. For real use, use a library like 'marked' or 'markdown-it'.
    // And sanitize with DOMPurify if rendering HTML from untrusted sources.
    return markdownText.replace(/\n/g, '<br>');
};

const findClosestIndex = (arr: (string | number)[] | undefined, target: number | null | undefined): number | null => {
    if (!arr || arr.length === 0 || target === null || target === undefined || isNaN(Number(target))) {
        return null;
    }
    // Ensure all elements in arr are numbers before processing
    const numericArr = arr.map(Number).filter(n => !isNaN(n));
    if (numericArr.length === 0) return null;

    const numTarget = Number(target);
    return numericArr.reduce((closestIndex, currentValue, currentIndex) => {
        return (Math.abs(currentValue - numTarget) < Math.abs(numericArr[closestIndex] - numTarget) ? currentIndex : closestIndex);
    }, 0);
};

const centerRowIndex = (metricKey: string) => computed(() => {
    const sensitivityResult = props.valuationData?.valuation_results?.sensitivity_analysis_result;
    const dcfDetails = props.valuationData?.valuation_results?.dcf_forecast_details;
    if (!sensitivityResult || !dcfDetails || !sensitivityResult.result_tables[metricKey]) {
        return null;
    }
    const rowParamName = sensitivityResult.row_parameter;
    let baseValue: number | null | undefined = null;
    if (rowParamName === 'wacc') baseValue = dcfDetails.wacc_used;
    else if (rowParamName === 'exit_multiple') baseValue = dcfDetails.exit_multiple_used;
    else if (rowParamName === 'perpetual_growth_rate' || rowParamName === 'terminal_growth_rate') baseValue = dcfDetails.perpetual_growth_rate_used;

    return findClosestIndex(sensitivityResult.row_values, baseValue);
});

const centerColIndex = (metricKey: string) => computed(() => {
    const sensitivityResult = props.valuationData?.valuation_results?.sensitivity_analysis_result;
    const dcfDetails = props.valuationData?.valuation_results?.dcf_forecast_details;
    if (!sensitivityResult || !dcfDetails || !sensitivityResult.result_tables[metricKey]) {
        return null;
    }
    const colParamName = sensitivityResult.column_parameter;
    let baseValue: number | null | undefined = null;
    if (colParamName === 'wacc') baseValue = dcfDetails.wacc_used;
    else if (colParamName === 'exit_multiple') baseValue = dcfDetails.exit_multiple_used;
    else if (colParamName === 'perpetual_growth_rate' || colParamName === 'terminal_growth_rate') baseValue = dcfDetails.perpetual_growth_rate_used;

    return findClosestIndex(sensitivityResult.column_values, baseValue);
});


</script>

<style scoped>
.dcf-results-display {
    margin-top: 1rem;
}

.dcf-results-display h4 {
    margin-bottom: 1rem;
}

.results-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.result-section {
    padding: 1rem;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    background-color: #fff;
}

.result-section h5 {
    margin-top: 0;
    margin-bottom: 0.8rem;
    color: #333;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.5rem;
}

.info-grid,
.metrics-grid {
    display: grid;
    /* grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); */
    gap: 0.8rem;
}

.info-grid.two-rows {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    /* Adjust minmax for more items */
}

.metrics-grid.two-rows {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    /* Adjust minmax for more items */
}


.info-grid div,
.metrics-grid div {
    background-color: #f9f9f9;
    padding: 0.6rem;
    border-radius: 3px;
    font-size: 0.9em;
    /* Slightly smaller font for more items */
    display: flex;
    /* Added for better alignment of label and value */
    flex-direction: column;
    /* Stack label and value vertically */
}

.info-grid .full-width-item {
    grid-column: 1 / -1;
    /* Make item span all columns */
    text-align: center;
}


.metric-label {
    font-weight: bold;
    margin-right: 0.5rem;
}

.positive-upside {
    color: #28a745;
    /* Green */
    font-weight: bold;
}

.negative-upside {
    color: #dc3545;
    /* Red */
    font-weight: bold;
}

.llm-summary {
    padding: 0.5rem;
    background-color: #f0f8ff;
    /* AliceBlue */
    border-radius: 3px;
    line-height: 1.6;
}

.warning-message {
    color: #856404;
    /* Dark yellow */
    background-color: #fff3cd;
    /* Light yellow */
    border-color: #ffeeba;
    padding: 0.5rem;
    margin-bottom: 0.3rem;
    border-radius: 3px;
    list-style-type: none;
}

.warning-message:before {
    content: "⚠️ ";
}

.loading-indicator,
.error-message,
.info-message {
    padding: 1rem;
    border: 1px solid #eee;
    border-radius: 4px;
    margin-top: 1rem;
    text-align: center;
}

.loading-indicator {
    background-color: #eef;
    color: #33a;
}

.error-message {
    background-color: #fee;
    color: #a33;
}

.info-message {
    background-color: #eff;
    color: #3aa;
}

.table-responsive {
    overflow-x: auto;
    width: 100%;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 0.5rem;
    font-size: 0.9em;
}

th,
td {
    border: 1px solid #ddd;
    padding: 6px 8px;
    text-align: right;
    white-space: nowrap;
}

th {
    background-color: #f2f2f2;
    font-weight: bold;
    text-align: center;
}

td:first-child,
th:first-child {
    text-align: left;
}

.is-center-cell {
    background-color: #d1ecf1 !important;
    /* Light blue, adjust as needed */
    font-weight: bold;
}


pre {
    background-color: #f5f5f5;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 0.85em;
}
</style>
