<template>
    <div class="space-y-6">
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
            <h3 class="text-lg font-semibold mb-4">基本信息</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <!-- 股票信息卡片 -->
                <Card class="p-4">
                    <div class="flex flex-col">
                        <span class="text-sm text-muted-foreground">股票代码</span>
                        <div class="flex items-baseline mt-1">
                            <span class="text-2xl font-bold">{{ valuationData.stock_info?.ts_code || 'N/A' }}</span>
                        </div>
                        <span class="text-sm text-muted-foreground mt-2">{{ valuationData.stock_info?.name || 'N/A' }} |
                            {{ valuationData.stock_info?.industry || 'N/A' }}</span>
                    </div>
                </Card>

                <!-- 最新价格卡片 -->
                <Card class="p-4">
                    <div class="flex flex-col">
                        <span class="text-sm text-muted-foreground">最新价格</span>
                        <div class="flex items-baseline mt-1">
                            <span class="text-2xl font-bold">¥{{ formatNumber(latestPriceForDisplay, 2) }}</span>
                        </div>
                        <div class="flex items-center mt-2">
                            <span class="text-sm text-muted-foreground">年报EPS: {{
                                formatNumber(valuationData.stock_info?.latest_annual_diluted_eps, 2) }}</span>
                        </div>
                    </div>
                </Card>

                <!-- 市盈率卡片 -->
                <Card class="p-4">
                    <div class="flex flex-col">
                        <span class="text-sm text-muted-foreground">当前PE</span>
                        <div class="flex items-baseline mt-1">
                            <span class="text-2xl font-bold">{{
                                formatNumber(valuationData.valuation_results?.current_pe, 2) }}</span>
                        </div>
                        <div class="flex items-center mt-2">
                            <span class="text-sm text-muted-foreground">当前PB: {{
                                formatNumber(valuationData.valuation_results?.current_pb, 2) }}</span>
                        </div>
                    </div>
                </Card>

                <!-- 股息率卡片 -->
                <Card class="p-4">
                    <div class="flex flex-col">
                        <span class="text-sm text-muted-foreground">股息率 (TTM)</span>
                        <div class="flex items-baseline mt-1">
                            <span class="text-2xl font-bold">{{
                                formatPercentage(valuationData.stock_info?.dividend_yield) }}</span>
                        </div>
                        <div class="flex items-center mt-2">
                            <span class="text-sm text-muted-foreground">每股股息: {{
                                formatNumber(valuationData.stock_info?.ttm_dps, 2) }}</span>
                        </div>
                    </div>
                </Card>
            </div>

            <!-- 核心估值指标 -->
            <h3 class="text-lg font-semibold mb-4">核心估值指标</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <!-- 内在价值卡片 -->
                <Card class="p-4">
                    <div class="flex flex-col">
                        <span class="text-sm text-muted-foreground">每股内在价值</span>
                        <div class="flex items-baseline mt-1">
                            <span class="text-2xl font-bold">¥{{
                                formatNumber(valuationData.valuation_results?.dcf_forecast_details?.value_per_share, 2)
                            }}</span>
                        </div>
                        <div class="flex items-center mt-2">
                            <span
                                :class="typeof calculatedUpsidePotential === 'number' && calculatedUpsidePotential < 0 ? 'text-red-500' : 'text-green-500'"
                                class="text-sm">
                                {{ formatPercentage(calculatedUpsidePotential) }} 上升空间
                            </span>
                        </div>
                    </div>
                </Card>

                <!-- DCF隐含PE卡片 -->
                <Card class="p-4">
                    <div class="flex flex-col">
                        <span class="text-sm text-muted-foreground">隐含PE</span>
                        <div class="flex items-baseline mt-1">
                            <span class="text-2xl font-bold">{{
                                formatNumber(valuationData.valuation_results?.dcf_forecast_details?.dcf_implied_diluted_pe,
                                    2) }}×</span>
                        </div>
                        <div class="flex items-center mt-2">
                            <span class="text-sm text-muted-foreground">EV/EBITDA: {{
                                formatNumber(valuationData.valuation_results?.dcf_forecast_details?.base_ev_ebitda, 2)
                            }}×</span>
                        </div>
                    </div>
                </Card>

                <!-- WACC卡片 -->
                <Card class="p-4">
                    <div class="flex flex-col">
                        <span class="text-sm text-muted-foreground">WACC</span>
                        <div class="flex items-baseline mt-1">
                            <span class="text-2xl font-bold">{{
                                formatPercentage(valuationData.valuation_results?.dcf_forecast_details?.wacc_used)
                            }}</span>
                        </div>
                        <div class="flex items-center mt-2">
                            <span class="text-sm text-muted-foreground">股权成本: {{
                                formatPercentage(valuationData.valuation_results?.dcf_forecast_details?.cost_of_equity_used)
                            }}</span>
                        </div>
                    </div>
                </Card>

                <!-- 企业价值卡片 -->
                <Card class="p-4">
                    <div class="flex flex-col">
                        <span class="text-sm text-muted-foreground">企业价值 (EV)</span>
                        <div class="flex items-baseline mt-1">
                            <span class="text-2xl font-bold">{{
                                formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.enterprise_value)
                            }}亿</span>
                        </div>
                        <div class="flex items-center mt-2">
                            <span class="text-sm text-muted-foreground">股权价值: {{
                                formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.equity_value)
                            }}亿</span>
                        </div>
                    </div>
                </Card>

                <!-- 终值卡片 -->
                <Card class="p-4">
                    <div class="flex flex-col">
                        <span class="text-sm text-muted-foreground">终值</span>
                        <div class="flex items-baseline mt-1">
                            <span class="text-2xl font-bold">{{
                                formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.terminal_value)
                            }}亿</span>
                        </div>
                        <div class="flex items-center mt-2">
                            <span class="text-sm text-muted-foreground">终值现值: {{
                                formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.pv_terminal_value)
                            }}亿</span>
                        </div>
                    </div>
                </Card>

                <!-- UFCF现值卡片 -->
                <Card class="p-4">
                    <div class="flex flex-col">
                        <span class="text-sm text-muted-foreground">UFCF现值</span>
                        <div class="flex items-baseline mt-1">
                            <span class="text-2xl font-bold">{{
                                formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.pv_forecast_ufcf)
                            }}亿</span>
                        </div>
                        <div class="flex items-center mt-2">
                            <span class="text-sm text-muted-foreground">净债务: {{
                                formatLargeNumberInBillions(valuationData.valuation_results?.dcf_forecast_details?.net_debt)
                            }}亿</span>
                        </div>
                    </div>
                </Card>

                <!-- 退出乘数卡片 -->
                <Card class="p-4">
                    <div class="flex flex-col">
                        <span class="text-sm text-muted-foreground">使用退出乘数</span>
                        <div class="flex items-baseline mt-1">
                            <span class="text-2xl font-bold">{{
                                valuationData.valuation_results?.dcf_forecast_details?.terminal_value_method_used ===
                                    'exit_multiple' &&
                                    valuationData.valuation_results?.dcf_forecast_details?.exit_multiple_used !== null ?
                                    formatNumber(valuationData.valuation_results?.dcf_forecast_details?.exit_multiple_used,
                                        1) + '×' : 'N/A'
                            }}</span>
                        </div>
                        <div class="flex items-center mt-2">
                            <span class="text-sm text-muted-foreground">隐含永续增长率: {{
                                formatPercentage(valuationData.valuation_results?.dcf_forecast_details?.implied_perpetual_growth_rate)
                            }}</span>
                        </div>
                    </div>
                </Card>

                <!-- 基准年报卡片 -->
                <Card class="p-4">
                    <div class="flex flex-col">
                        <span class="text-sm text-muted-foreground">基准年报</span>
                        <div class="flex items-baseline mt-1">
                            <span class="text-2xl font-bold">{{ baseReportYearForDisplay || 'N/A' }}</span>
                        </div>
                        <div class="flex items-center mt-2">
                            <span class="text-sm text-muted-foreground">市场类型: {{ valuationData.stock_info?.market ||
                                'N/A' }}</span>
                        </div>
                    </div>
                </Card>
            </div>

            <!-- 敏感性分析 -->
            <Card
                v-if="valuationData.valuation_results?.sensitivity_analysis_result && valuationData.valuation_results?.sensitivity_analysis_result.result_tables && Object.keys(valuationData.valuation_results?.sensitivity_analysis_result.result_tables).length > 0">
                <CardHeader>
                    <CardTitle>敏感性分析</CardTitle>
                </CardHeader>
                <CardContent class="space-y-4">
                    <div v-for="(tableData, metricKey) in filteredSensitivityTables" :key="String(metricKey)"
                        class="border p-3 rounded-md bg-muted/20 mb-4">
                        <h4 class="text-md font-medium mb-2">{{ getMetricDisplayName(String(metricKey)) }} ({{
                            getAxisParamDisplayName(valuationData.valuation_results.sensitivity_analysis_result.row_parameter)
                        }} vs {{
                                getAxisParamDisplayName(valuationData.valuation_results.sensitivity_analysis_result.column_parameter)
                            }})</h4>
                        <div class="w-full overflow-x-auto">
                            <div class="min-w-[600px]">
                                <Table class="w-full">
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead class="w-[15%] whitespace-nowrap">
                                                {{
                                                    getAxisParamDisplayName(valuationData.valuation_results.sensitivity_analysis_result.row_parameter)
                                                }}
                                                /
                                                {{
                                                    getAxisParamDisplayName(valuationData.valuation_results.sensitivity_analysis_result.column_parameter)
                                                }}
                                            </TableHead>
                                            <TableHead class="whitespace-nowrap"
                                                v-for="(_, colIndex) in valuationData.valuation_results.sensitivity_analysis_result.column_values"
                                                :key="`col-header-${colIndex}`"
                                                :style="{ width: `${85 / valuationData.valuation_results.sensitivity_analysis_result.column_values.length}%` }">
                                                {{ getFormattedColAxisValue(colIndex) }}
                                            </TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        <TableRow v-for="(row, rowIndex) in tableData" :key="`sa-row-${rowIndex}`">
                                            <TableCell class="whitespace-nowrap"><strong>{{
                                                getFormattedRowAxisValue(rowIndex)
                                                    }}</strong>
                                            </TableCell>
                                            <TableCell class="whitespace-nowrap" v-for="(cellValue, cellIndex) in row"
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
                </CardContent>
            </Card>

            <!-- 高级分析 -->
            <Card class="bg-background">
                <CardHeader class="cursor-pointer" @click="toggleAdvancedAnalysis">
                    <div class="flex items-center justify-between">
                        <CardTitle>高级分析</CardTitle>
                        <component :is="advancedAnalysisCollapsed ? ChevronRight : ChevronDown" class="h-4 w-4" />
                    </div>
                </CardHeader>
                <CardContent v-show="!advancedAnalysisCollapsed" class="space-y-6">
                    <!-- 详细财务预测表格 -->
                    <div v-if="valuationData.valuation_results?.detailed_forecast_table && valuationData.valuation_results?.detailed_forecast_table.length > 0"
                        class="border p-3 rounded-md bg-muted/20 mb-4">
                        <h4 class="text-md font-medium mb-2">详细财务预测 <span
                                class="text-sm text-muted-foreground">(单位：元)</span></h4>
                        <div class="w-full overflow-x-auto">
                            <div class="min-w-[900px]">
                                <Table class="w-full">
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead class="w-[8%] whitespace-nowrap">年份</TableHead>
                                            <TableHead class="w-[11%] whitespace-nowrap">营业收入</TableHead>
                                            <TableHead class="w-[11%] whitespace-nowrap">息税前利润</TableHead>
                                            <TableHead class="w-[11%] whitespace-nowrap">税后净营业利润</TableHead>
                                            <TableHead class="w-[11%] whitespace-nowrap">折旧与摊销</TableHead>
                                            <TableHead class="w-[11%] whitespace-nowrap">资本性支出</TableHead>
                                            <TableHead class="w-[11%] whitespace-nowrap">净营运资本变动</TableHead>
                                            <TableHead class="w-[13%] whitespace-nowrap">无杠杆自由现金流</TableHead>
                                            <TableHead class="w-[13%] whitespace-nowrap">FCF现值</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        <TableRow v-for="row in valuationData.valuation_results.detailed_forecast_table"
                                            :key="row.year">
                                            <TableCell class="whitespace-nowrap"><strong>{{ row.year }}</strong>
                                            </TableCell>
                                            <TableCell class="whitespace-nowrap">{{ formatNumber(row.revenue) }}
                                            </TableCell>
                                            <TableCell class="whitespace-nowrap">{{ formatNumber(row.ebit) }}
                                            </TableCell>
                                            <TableCell class="whitespace-nowrap">{{ formatNumber(row.nopat) }}
                                            </TableCell>
                                            <TableCell class="whitespace-nowrap">{{ formatNumber(row.d_a) }}</TableCell>
                                            <TableCell class="whitespace-nowrap">{{ formatNumber(row.capex) }}
                                            </TableCell>
                                            <TableCell class="whitespace-nowrap">{{ formatNumber(row.delta_nwc) }}
                                            </TableCell>
                                            <TableCell class="whitespace-nowrap font-semibold">{{ formatNumber(row.ufcf)
                                                }}
                                            </TableCell>
                                            <TableCell class="whitespace-nowrap font-semibold">{{
                                                formatNumber(row.pv_ufcf) }}
                                            </TableCell>
                                        </TableRow>
                                    </TableBody>
                                </Table>
                            </div>
                        </div>
                    </div>

                    <!-- 历史财务摘要 -->
                    <div v-if="valuationData.valuation_results?.historical_financial_summary && valuationData.valuation_results?.historical_financial_summary.length > 0"
                        class="border p-3 rounded-md bg-muted/20 mb-4">
                        <h4 class="text-md font-medium mb-2">历史财务摘要</h4>
                        <div class="w-full overflow-x-auto">
                            <div class="min-w-[800px]">
                                <Table class="w-full">
                                    <TableHeader>
                                        <TableRow>
                                            <!-- 先显示科目列 -->
                                            <TableHead v-if="hasColumn('科目')" class="whitespace-nowrap">
                                                {{ getHistoricalHeaderName('科目') }}
                                            </TableHead>
                                            <!-- 再显示报表类型列 -->
                                            <TableHead v-if="hasColumn('报表类型')" class="whitespace-nowrap">
                                                {{ getHistoricalHeaderName('报表类型') }}
                                            </TableHead>
                                            <!-- 然后显示其他列 -->
                                            <TableHead v-for="colKey in otherColumnKeys"
                                                :key="`hist-summary-header-${colKey}`" class="whitespace-nowrap">
                                                {{ getHistoricalHeaderName(colKey) }}
                                            </TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        <TableRow
                                            v-for="(row, rowIndex) in valuationData.valuation_results.historical_financial_summary"
                                            :key="`hist-summary-row-${rowIndex}`">
                                            <!-- 先显示科目单元格 -->
                                            <TableCell v-if="hasColumn('科目')" class="whitespace-nowrap">
                                                <strong>{{ row['科目'] }}</strong>
                                            </TableCell>
                                            <!-- 再显示报表类型单元格 -->
                                            <TableCell v-if="hasColumn('报表类型')" class="whitespace-nowrap">
                                                <strong>{{ row['报表类型'] }}</strong>
                                            </TableCell>
                                            <!-- 然后显示其他单元格 -->
                                            <TableCell v-for="colKey in otherColumnKeys"
                                                :key="`hist-summary-cell-${rowIndex}-${colKey}`"
                                                class="whitespace-nowrap">
                                                {{ formatNumber(row[colKey], typeof row[colKey] === 'number' &&
                                                    !Number.isInteger(row[colKey]) ? 2 : 0) }}
                                            </TableCell>
                                        </TableRow>
                                    </TableBody>
                                </Table>
                            </div>
                        </div>
                    </div>

                    <!-- 历史财务比率 -->
                    <div v-if="valuationData.valuation_results?.historical_ratios_summary && valuationData.valuation_results?.historical_ratios_summary.length > 0"
                        class="border p-3 rounded-md bg-muted/20 mb-4">
                        <h4 class="text-md font-medium mb-2">历史财务比率</h4>
                        <div class="w-full overflow-x-auto">
                            <div class="min-w-[400px]">
                                <Table class="w-full">
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead class="w-[70%] whitespace-nowrap">
                                                {{ getHistoricalHeaderName('metric_name') }}
                                            </TableHead>
                                            <TableHead class="w-[30%] whitespace-nowrap">
                                                {{ getHistoricalHeaderName('value') }}
                                            </TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        <TableRow
                                            v-for="(row, rowIndex) in valuationData.valuation_results.historical_ratios_summary"
                                            :key="`hist-ratios-row-${rowIndex}`">
                                            <TableCell class="whitespace-nowrap">
                                                <strong>{{ getHistoricalHeaderName(String(row.metric_name)) }}</strong>
                                            </TableCell>
                                            <TableCell class="whitespace-nowrap">
                                                {{ formatRatioValue(row.metric_name, row.value) }}
                                            </TableCell>
                                        </TableRow>
                                    </TableBody>
                                </Table>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <!-- LLM 分析摘要 -->
            <Card v-if="valuationData.valuation_results?.llm_analysis_summary">
                <CardHeader>
                    <CardTitle>AI 分析</CardTitle>
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
import { AlertTriangle, ChevronDown, ChevronRight } from 'lucide-vue-next';

// defineProps is a compiler macro and no longer needs to be imported.
// import DOMPurify from 'dompurify'; // For v-html, if LLM output is complex HTML
// For basic markdown to HTML, a simpler library or custom function might be used.
// For now, we'll assume LLM summary is safe or simple HTML/markdown.

// Import types from shared-types
import { computed, ref } from 'vue';
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

// 高级分析折叠状态，默认折叠
const advancedAnalysisCollapsed = ref(true);

// 切换高级分析折叠状态
const toggleAdvancedAnalysis = () => {
    advancedAnalysisCollapsed.value = !advancedAnalysisCollapsed.value;
};

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

// 过滤敏感性分析表格，排除DCF隐含PE相关表格
const filteredSensitivityTables = computed(() => {
    if (!props.valuationData?.valuation_results?.sensitivity_analysis_result?.result_tables) {
        return {};
    }

    const tables = props.valuationData.valuation_results.sensitivity_analysis_result.result_tables;
    const filteredTables: Record<string, (string | number | null)[][]> = {};

    // 遍历所有表格，排除dcf_implied_pe和dcf_implied_diluted_pe
    for (const [key, value] of Object.entries(tables)) {
        if (key !== 'dcf_implied_pe' && key !== 'dcf_implied_diluted_pe') {
            filteredTables[key] = value;
        }
    }

    return filteredTables;
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



// Basic markdown rendering (very simplified, consider a library for complex markdown)

// 格式化比率值，根据指标类型选择合适的格式
const formatRatioValue = (metricName: string | null | undefined, value: string | number | null | undefined): string => {
    if (metricName === null || metricName === undefined) {
        return formatNumber(value);
    }

    if (value === null || value === undefined || (typeof value === 'number' && isNaN(value))) {
        return 'N/A';
    }

    // 判断是否为百分比类型的指标
    const percentageMetrics = [
        'operating_margin_median', 'cogs_to_revenue_ratio', 'sga_rd_to_revenue_ratio',
        'da_to_revenue_ratio', 'capex_to_revenue_ratio', 'effective_tax_rate',
        'other_current_assets_to_revenue_ratio', 'other_current_liabilities_to_revenue_ratio',
        'nwc_to_revenue_ratio', 'historical_revenue_cagr'
    ];

    if (percentageMetrics.includes(String(metricName))) {
        return formatPercentage(Number(value));
    }

    // 判断是否为天数类型的指标
    const daysMetrics = ['accounts_receivable_days', 'inventory_days', 'accounts_payable_days'];
    if (daysMetrics.includes(String(metricName))) {
        return `${formatNumber(Number(value), 1)} 天`;
    }

    // 默认格式化
    const numValue = Number(value);
    return formatNumber(numValue, !isNaN(numValue) && !Number.isInteger(numValue) ? 2 : 0);
};

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

// 检查历史财务摘要表格是否包含特定列
const hasColumn = (colName: string): boolean => {
    if (!props.valuationData?.valuation_results?.historical_financial_summary ||
        props.valuationData.valuation_results.historical_financial_summary.length === 0) {
        return false;
    }
    return colName in props.valuationData.valuation_results.historical_financial_summary[0];
};

// 获取除了"科目"和"报表类型"之外的所有列名
const otherColumnKeys = computed(() => {
    if (!props.valuationData?.valuation_results?.historical_financial_summary ||
        props.valuationData.valuation_results.historical_financial_summary.length === 0) {
        return [];
    }

    const firstRow = props.valuationData.valuation_results.historical_financial_summary[0];
    return Object.keys(firstRow).filter(key => key !== '科目' && key !== '报表类型');
});


</script>

<style scoped>
/* All scoped styles have been removed and replaced by Tailwind utility classes in the template,
   or are covered by global styles / shadcn-vue component styles. */
</style>
