<template>
    <div class="space-y-6">
        <h2 class="text-2xl font-semibold text-foreground mb-4">估值结果</h2>

        <div v-if="isLoading" class="space-y-3 p-4 border rounded-md bg-card">
            <Skeleton class="h-8 w-1/3" />
            <Skeleton class="h-4 w-full" />
            <Skeleton class="h-4 w-full" />
            <Skeleton class="h-4 w-3/4" />
        </div>
        <Alert variant="destructive" v-else-if="error">
            <!-- Assuming AlertCircle is imported or available globally if used -->
            <!-- <AlertCircle class="h-4 w-4" /> -->
            <AlertTitle>错误</AlertTitle>
            <AlertDescription>{{ error }}</AlertDescription>
        </Alert>
        <div v-else-if="!valuationData && hasCalculated" class="text-center py-8 text-muted-foreground">
            <p>未能获取估值结果。</p>
        </div>
        <div v-else-if="!valuationData && !hasCalculated" class="text-center py-8 text-muted-foreground">
            <p>请输入参数并开始估值。</p>
        </div>

        <div v-if="valuationData" class="space-y-6">
            <!-- 基本信息 -->
            <Card>
                <CardHeader>
                    <CardTitle>基本信息</CardTitle>
                </CardHeader>
                <CardContent class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-3 text-sm">
                    <div><strong class="text-muted-foreground">股票代码:</strong> <span class="text-foreground">{{
                        valuationData.stock_info?.ts_code || 'N/A' }}</span></div>
                    <div><strong class="text-muted-foreground">股票名称:</strong> <span class="text-foreground">{{
                        valuationData.stock_info?.name || 'N/A' }}</span></div>
                    <div><strong class="text-muted-foreground">所属行业:</strong> <span class="text-foreground">{{
                        valuationData.stock_info?.industry || 'N/A' }}</span></div>
                    <div><strong class="text-muted-foreground">市场类型:</strong> <span class="text-foreground">{{
                        valuationData.stock_info?.market || 'N/A' }}</span></div>
                    <div><strong class="text-muted-foreground">实控人:</strong> <span class="text-foreground">{{
                        valuationData.stock_info?.act_name || 'N/A' }}</span></div>
                    <div><strong class="text-muted-foreground">实控人性质:</strong> <span class="text-foreground">{{
                        valuationData.stock_info?.act_ent_type || 'N/A' }}</span></div>

                    <div><strong class="text-muted-foreground">最新价格:</strong> <span class="text-foreground">{{
                        formatNumber(latestPriceForDisplay, 2) }}</span></div>
                    <div><strong class="text-muted-foreground">当前PE:</strong> <span class="text-foreground">{{
                        formatNumber(valuationData.valuation_results?.current_pe, 2) }}</span></div>
                    <div><strong class="text-muted-foreground">当前PB:</strong> <span class="text-foreground">{{
                        formatNumber(valuationData.valuation_results?.current_pb, 2) }}</span></div>
                    <div><strong class="text-muted-foreground">年报EPS:</strong> <span class="text-foreground">{{
                        formatNumber(valuationData.stock_info?.latest_annual_diluted_eps, 2) }}</span></div>
                    <div><strong class="text-muted-foreground">股息率 (TTM):</strong> <span class="text-foreground">{{
                        formatPercentage(valuationData.stock_info?.dividend_yield) }}</span></div>
                    <div><strong class="text-muted-foreground">TTM每股股息:</strong> <span class="text-foreground">{{
                        formatNumber(valuationData.stock_info?.ttm_dps, 4) }}</span></div>
                    <div class="md:col-span-2 lg:col-span-3"><strong class="text-muted-foreground">基准年报:</strong> <span
                            class="text-foreground">{{ baseReportYearForDisplay || 'N/A' }}</span></div>
                </CardContent>
            </Card>

            <!-- 核心估值指标 -->
            <Card>
                <CardHeader>
                    <CardTitle>核心估值指标</CardTitle>
                </CardHeader>
                <CardContent class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 text-sm">
                    <div>
                        <span class="text-muted-foreground">每股内在价值:</span>
                        <span class="font-medium text-foreground ml-1">{{
                            formatNumber(valuationData.valuation_results?.dcf_forecast_details?.value_per_share, 2)
                        }}</span>
                    </div>
                    <div>
                        <span class="text-muted-foreground">上升空间:</span>
                        <span :class="getUpsideClass(calculatedUpsidePotential)" class="font-medium ml-1">
                            {{ formatPercentage(calculatedUpsidePotential) }}
                        </span>
                    </div>
                    <div>
                        <span class="text-muted-foreground">DCF隐含PE:</span>
                        <span class="font-medium text-foreground ml-1">{{
                            formatNumber(valuationData.valuation_results?.dcf_forecast_details?.dcf_implied_diluted_pe,
                                2)
                        }}x</span>
                    </div>
                    <div>
                        <span class="text-muted-foreground">隐含EV/EBITDA:</span>
                        <span class="font-medium text-foreground ml-1">{{
                            formatNumber(valuationData.valuation_results?.dcf_forecast_details?.base_ev_ebitda, 2)
                        }}x</span>
                    </div>
                    <div>
                        <span class="text-muted-foreground">WACC:</span>
                        <span class="font-medium text-foreground ml-1">{{
                            formatPercentage(valuationData.valuation_results?.dcf_forecast_details?.wacc_used) }}</span>
                    </div>
                    <div>
                        <span class="text-muted-foreground">Ke (股权成本):</span>
                        <span class="font-medium text-foreground ml-1">{{
                            formatPercentage(valuationData.valuation_results?.dcf_forecast_details?.cost_of_equity_used)
                        }}</span>
                    </div>

                    <div>
                        <span class="text-muted-foreground">企业价值 (EV):</span>
                        <span class="font-medium text-foreground ml-1">{{
                            formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.enterprise_value)
                        }} 亿</span>
                    </div>
                    <div>
                        <span class="text-muted-foreground">股权价值:</span>
                        <span class="font-medium text-foreground ml-1">{{
                            formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.equity_value)
                        }} 亿</span>
                    </div>
                    <div>
                        <span class="text-muted-foreground">UFCF现值:</span>
                        <span class="font-medium text-foreground ml-1">{{
                            formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.pv_forecast_ufcf)
                        }} 亿</span>
                    </div>
                    <div>
                        <span class="text-muted-foreground">终值现值:</span>
                        <span class="font-medium text-foreground ml-1">{{
                            formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.pv_terminal_value)
                        }} 亿</span>
                    </div>
                    <div>
                        <span class="text-muted-foreground">终值:</span>
                        <span class="font-medium text-foreground ml-1">{{
                            formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.terminal_value)
                        }} 亿</span>
                    </div>
                    <div>
                        <span class="text-muted-foreground">净债务:</span>
                        <span class="font-medium text-foreground ml-1">{{
                            formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.net_debt)
                        }} 亿</span>
                    </div>

                    <div>
                        <span class="text-muted-foreground">使用退出乘数:</span>
                        <span class="font-medium text-foreground ml-1">{{
                            valuationData.valuation_results?.dcf_forecast_details?.terminal_value_method_used ===
                                'exit_multiple' && valuationData.valuation_results?.dcf_forecast_details?.exit_multiple_used
                                !== null ?
                                formatNumber(valuationData.valuation_results?.dcf_forecast_details?.exit_multiple_used, 1) +
                                'x' : 'N/A'
                        }}</span>
                    </div>
                    <div>
                        <span class="text-muted-foreground">隐含永续增长率:</span>
                        <span class="font-medium text-foreground ml-1">{{
                            formatPercentage(valuationData.valuation_results?.dcf_forecast_details?.implied_perpetual_growth_rate)
                        }}</span>
                    </div>
                </CardContent>
            </Card>

            <!-- 详细财务预测表格 -->
            <Card
                v-if="valuationData.valuation_results?.detailed_forecast_table && valuationData.valuation_results?.detailed_forecast_table.length > 0">
                <CardHeader>
                    <CardTitle>高级分析 - 详细财务预测 (单位：元)</CardTitle>
                </CardHeader>
                <CardContent>
                    <div class="w-full overflow-hidden">
                        <div class="w-full max-w-full">
                            <Table class="w-full table-fixed">
                                <TableHeader>
                                    <TableRow>
                                        <TableHead class="w-[10%] break-words">年份 (Year)</TableHead>
                                        <TableHead class="w-[10%] break-words">营业收入 (Revenue)</TableHead>
                                        <TableHead class="w-[10%] break-words">息税前利润 (EBIT)</TableHead>
                                        <TableHead class="w-[10%] break-words">税后净营业利润 (NOPAT)</TableHead>
                                        <TableHead class="w-[10%] break-words">折旧与摊销 (D&A)</TableHead>
                                        <TableHead class="w-[10%] break-words">资本性支出 (CapEx)</TableHead>
                                        <TableHead class="w-[10%] break-words">净营运资本变动 (ΔNWC)</TableHead>
                                        <TableHead class="w-[15%] break-words">无杠杆自由现金流 (FCF)</TableHead>
                                        <TableHead class="w-[15%] break-words">FCF现值 (PV of FCF)</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    <TableRow v-for="row in valuationData.valuation_results.detailed_forecast_table"
                                        :key="row.year">
                                        <TableCell class="break-words">{{ row.year }}</TableCell>
                                        <TableCell class="break-words">{{ formatNumber(row.revenue) }}</TableCell>
                                        <TableCell class="break-words">{{ formatNumber(row.ebit) }}</TableCell>
                                        <TableCell class="break-words">{{ formatNumber(row.nopat) }}</TableCell>
                                        <TableCell class="break-words">{{ formatNumber(row.d_a) }}</TableCell>
                                        <TableCell class="break-words">{{ formatNumber(row.capex) }}</TableCell>
                                        <TableCell class="break-words">{{ formatNumber(row.delta_nwc) }}</TableCell>
                                        <TableCell class="break-words">{{ formatNumber(row.ufcf) }}</TableCell>
                                        <TableCell class="break-words">{{ formatNumber(row.pv_ufcf) }}</TableCell>
                                    </TableRow>
                                </TableBody>
                            </Table>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <!-- 历史财务摘要 -->
            <Card
                v-if="valuationData.valuation_results?.historical_financial_summary && valuationData.valuation_results?.historical_financial_summary.length > 0">
                <CardHeader>
                    <CardTitle>高级分析 - 历史财务摘要</CardTitle>
                </CardHeader>
                <CardContent>
                    <div class="w-full overflow-hidden">
                        <div class="w-full max-w-full">
                            <Table class="w-full table-fixed">
                                <TableHeader>
                                    <TableRow>
                                        <TableHead class="break-words"
                                            v-for="(_, colKey) in valuationData.valuation_results.historical_financial_summary[0]"
                                            :key="`hist-summary-header-${String(colKey)}`"
                                            :style="{ width: `${100 / Object.keys(valuationData.valuation_results.historical_financial_summary[0]).length}%` }">
                                            {{ getHistoricalHeaderName(String(colKey)) }}
                                        </TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    <TableRow
                                        v-for="(row, rowIndex) in valuationData.valuation_results.historical_financial_summary"
                                        :key="`hist-summary-row-${rowIndex}`">
                                        <TableCell class="break-words" v-for="(cellValue, cellKey) in row"
                                            :key="`hist-summary-cell-${rowIndex}-${String(cellKey)}`">
                                            <span v-if="String(cellKey) === '科目' || String(cellKey) === '报表类型'">
                                                {{ cellValue }}
                                            </span>
                                            <span v-else>
                                                {{ formatNumber(cellValue, typeof cellValue === 'number' &&
                                                    !Number.isInteger(cellValue) ? 2 : 0) }}
                                            </span>
                                        </TableCell>
                                    </TableRow>
                                </TableBody>
                            </Table>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <!-- 历史财务比率 -->
            <Card
                v-if="valuationData.valuation_results?.historical_ratios_summary && valuationData.valuation_results?.historical_ratios_summary.length > 0">
                <CardHeader>
                    <CardTitle>高级分析 - 历史财务比率</CardTitle>
                </CardHeader>
                <CardContent>
                    <div class="w-full overflow-hidden">
                        <div class="w-full max-w-full">
                            <Table class="w-full table-fixed">
                                <TableHeader>
                                    <TableRow>
                                        <TableHead class="w-[70%] break-words">{{ getHistoricalHeaderName('metric_name')
                                        }}
                                        </TableHead>
                                        <TableHead class="w-[30%] break-words">{{ getHistoricalHeaderName('value') }}
                                        </TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    <TableRow
                                        v-for="(row, rowIndex) in valuationData.valuation_results.historical_ratios_summary"
                                        :key="`hist-ratios-row-${rowIndex}`">
                                        <TableCell class="break-words">
                                            {{ getHistoricalHeaderName(String(row.metric_name)) }}
                                        </TableCell>
                                        <TableCell class="break-words">
                                            {{ formatNumber(row.value, typeof row.value === 'number' &&
                                                !Number.isInteger(row.value) ? 2 : 0) }}
                                        </TableCell>
                                    </TableRow>
                                </TableBody>
                            </Table>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <!-- 敏感性分析 -->
            <Card>
                <CardHeader>
                    <CardTitle>敏感性分析数据状态</CardTitle>
                </CardHeader>
                <CardContent>
                    <div class="text-sm space-y-2">
                        <p>敏感性分析结果存在: {{ !!valuationData.valuation_results?.sensitivity_analysis_result }}</p>
                        <p v-if="valuationData.valuation_results?.sensitivity_analysis_result">
                            结果表存在: {{ !!valuationData.valuation_results?.sensitivity_analysis_result.result_tables }}
                        </p>
                        <p v-if="valuationData.valuation_results?.sensitivity_analysis_result?.result_tables">
                            结果表数量: {{
                                Object.keys(valuationData.valuation_results?.sensitivity_analysis_result.result_tables).length
                            }}
                        </p>
                        <p v-if="valuationData.valuation_results?.sensitivity_analysis_result">
                            行参数: {{ valuationData.valuation_results?.sensitivity_analysis_result.row_parameter }}
                        </p>
                        <p v-if="valuationData.valuation_results?.sensitivity_analysis_result">
                            列参数: {{ valuationData.valuation_results?.sensitivity_analysis_result.column_parameter }}
                        </p>
                    </div>
                </CardContent>
            </Card>

            <!-- 敏感性分析 -->
            <Card
                v-if="valuationData.valuation_results?.sensitivity_analysis_result && valuationData.valuation_results?.sensitivity_analysis_result.result_tables && Object.keys(valuationData.valuation_results?.sensitivity_analysis_result.result_tables).length > 0">
                <CardHeader>
                    <CardTitle>高级分析 - 敏感性分析</CardTitle>
                </CardHeader>
                <CardContent class="space-y-4">
                    <Tabs defaultValue="simple" class="w-full">
                        <TabsList>
                            <TabsTrigger value="heatmap">热力图</TabsTrigger>
                            <TabsTrigger value="simple">简易表格</TabsTrigger>
                            <TabsTrigger value="table">详细表格</TabsTrigger>
                        </TabsList>
                        <TabsContent value="heatmap">
                            <SensitivityHeatmap
                                :sensitivity-data="valuationData.valuation_results.sensitivity_analysis_result"
                                :is-loading="false" />
                        </TabsContent>
                        <TabsContent value="simple">
                            <SimpleSensitivityDisplay
                                :sensitivity-data="valuationData.valuation_results.sensitivity_analysis_result"
                                :is-loading="false" />
                        </TabsContent>
                        <TabsContent value="table">
                            <div v-for="(tableData, metricKey) in valuationData.valuation_results.sensitivity_analysis_result.result_tables"
                                :key="String(metricKey)" class="border p-3 rounded-md bg-muted/20 mb-4">
                                <h4 class="text-md font-medium mb-2">{{ getMetricDisplayName(String(metricKey)) }} ({{
                                    getAxisParamDisplayName(valuationData.valuation_results.sensitivity_analysis_result.row_parameter)
                                }} vs {{
                                        getAxisParamDisplayName(valuationData.valuation_results.sensitivity_analysis_result.column_parameter)
                                    }})</h4>
                                <div class="w-full overflow-hidden">
                                    <div class="w-full max-w-full">
                                        <Table class="w-full table-fixed">
                                            <TableHeader>
                                                <TableRow>
                                                    <TableHead class="w-[15%] break-words">
                                                        {{
                                                            getAxisParamDisplayName(valuationData.valuation_results.sensitivity_analysis_result.row_parameter)
                                                        }}
                                                        /
                                                        {{
                                                            getAxisParamDisplayName(valuationData.valuation_results.sensitivity_analysis_result.column_parameter)
                                                        }}
                                                    </TableHead>
                                                    <TableHead class="break-words"
                                                        v-for="(_, colIndex) in valuationData.valuation_results.sensitivity_analysis_result.column_values"
                                                        :key="`col-header-${colIndex}`"
                                                        :style="{ width: `${85 / valuationData.valuation_results.sensitivity_analysis_result.column_values.length}%` }">
                                                        {{ getFormattedColAxisValue(colIndex) }}
                                                    </TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                <TableRow v-for="(row, rowIndex) in tableData"
                                                    :key="`sa-row-${rowIndex}`">
                                                    <TableCell class="break-words"><strong>{{
                                                        getFormattedRowAxisValue(rowIndex)
                                                            }}</strong>
                                                    </TableCell>
                                                    <TableCell class="break-words" v-for="(cellValue, cellIndex) in row"
                                                        :key="`sa-cell-${rowIndex}-${cellIndex}`"
                                                        :class="{ 'bg-primary/10 font-semibold': centerRowIndex(String(metricKey)).value === rowIndex && centerColIndex(String(metricKey)).value === cellIndex }">
                                                        {{ formatSensitivityCellValue(cellValue, String(metricKey)) }}
                                                    </TableCell>
                                                </TableRow>
                                            </TableBody>
                                        </Table>
                                    </div>
                                </div>
                            </div>
                        </TabsContent>
                    </Tabs>
                </CardContent>
            </Card>

            <!-- LLM 分析摘要 -->
            <Card v-if="valuationData.valuation_results?.llm_analysis_summary">
                <CardHeader>
                    <CardTitle>LLM 分析摘要</CardTitle>
                </CardHeader>
                <CardContent>
                    <div class="prose prose-sm max-w-none dark:prose-invert"
                        v-html="renderMarkdown(valuationData.valuation_results.llm_analysis_summary)">
                    </div>
                </CardContent>
            </Card>

            <!-- 数据警告 -->
            <Card
                v-if="valuationData.valuation_results?.data_warnings && valuationData.valuation_results?.data_warnings.length > 0">
                <CardHeader>
                    <CardTitle>数据警告</CardTitle>
                </CardHeader>
                <CardContent class="space-y-2">
                    <Alert v-for="(warning, index) in valuationData.valuation_results.data_warnings" :key="index">
                        <AlertTriangle class="h-4 w-4" />
                        <AlertDescription>{{ warning }}</AlertDescription>
                    </Alert>
                </CardContent>
            </Card>
        </div>
    </div>
</template>

<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle } from 'lucide-vue-next';
import SensitivityHeatmap from '@/components/SensitivityHeatmap.vue';
import SimpleSensitivityDisplay from '@/components/SimpleSensitivityDisplay.vue';

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
/* All scoped styles have been removed and replaced by Tailwind utility classes in the template,
   or are covered by global styles / shadcn-vue component styles. */
</style>
