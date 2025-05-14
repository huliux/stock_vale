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
                <div class="info-grid">
                    <div><strong>股票代码:</strong> {{ valuationData.stock_info?.ts_code || 'N/A' }}</div>
                    <div><strong>股票名称:</strong> {{ valuationData.stock_info?.name || 'N/A' }}</div>
                    <div><strong>最新价格:</strong> {{ valuationData.stock_info?.latest_price?.toFixed(2) || 'N/A' }}</div>
                    <div><strong>基准年报:</strong> {{ valuationData.stock_info?.base_financial_year || 'N/A' }}</div>
                </div>
            </section>

            <!-- 核心估值指标 -->
            <section class="result-section">
                <h5>核心估值指标</h5>
                <div class="metrics-grid">
                    <div>
                        <span class="metric-label">每股内在价值:</span>
                        <span class="metric-value">{{ valuationData.core_metrics?.intrinsic_value_per_share?.toFixed(2)
                            || 'N/A' }}</span>
                    </div>
                    <div>
                        <span class="metric-label">上升空间:</span>
                        <span :class="getUpsideClass(valuationData.core_metrics?.upside_potential)">
                            {{ formatPercentage(valuationData.core_metrics?.upside_potential) || 'N/A' }}
                        </span>
                    </div>
                    <div>
                        <span class="metric-label">DCF隐含PE:</span>
                        <span class="metric-value">{{ valuationData.core_metrics?.dcf_implied_diluted_pe?.toFixed(2) ||
                            'N/A' }}</span>
                    </div>
                    <div>
                        <span class="metric-label">退出乘数:</span>
                        <span class="metric-value">{{ valuationData.core_metrics?.exit_multiple?.toFixed(2) || 'N/A'
                            }}</span>
                    </div>
                    <div>
                        <span class="metric-label">隐含永续增长率:</span>
                        <span class="metric-value">{{
                            formatPercentage(valuationData.core_metrics?.implied_terminal_growth_rate) || 'N/A'
                            }}</span>
                    </div>
                </div>
            </section>

            <!-- TODO: 详细财务预测表格 -->
            <section class="result-section"
                v-if="valuationData.detailed_forecast_table && valuationData.detailed_forecast_table.length > 0">
                <h5>详细财务预测</h5>
                <!-- Placeholder for table component or rendering logic -->
                <pre>{{ valuationData.detailed_forecast_table }}</pre>
            </section>

            <!-- TODO: 敏感性分析表格 -->
            <section class="result-section"
                v-if="valuationData.sensitivity_analysis_tables && Object.keys(valuationData.sensitivity_analysis_tables).length > 0">
                <h5>敏感性分析</h5>
                <!-- Placeholder for table component or rendering logic -->
                <pre>{{ valuationData.sensitivity_analysis_tables }}</pre>
            </section>

            <!-- TODO: LLM 分析摘要 -->
            <section class="result-section" v-if="valuationData.llm_summary">
                <h5>LLM 分析摘要</h5>
                <div class="llm-summary" v-html="renderMarkdown(valuationData.llm_summary)"></div>
            </section>

            <!-- 数据警告 -->
            <section class="result-section"
                v-if="valuationData.data_warnings && valuationData.data_warnings.length > 0">
                <h5>数据警告</h5>
                <ul>
                    <li v-for="(warning, index) in valuationData.data_warnings" :key="index" class="warning-message">{{
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

const formatPercentage = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
};

const getUpsideClass = (upside: number | null | undefined): string => {
    if (upside === null || upside === undefined) return 'metric-value';
    return upside >= 0 ? 'metric-value positive-upside' : 'metric-value negative-upside';
};

// Basic markdown rendering (very simplified, consider a library for complex markdown)
const renderMarkdown = (markdownText: string | null | undefined): string => {
    if (!markdownText) return '';
    // This is a very naive implementation. For real use, use a library like 'marked' or 'markdown-it'.
    // And sanitize with DOMPurify if rendering HTML from untrusted sources.
    return markdownText.replace(/\n/g, '<br>');
};

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
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 0.8rem;
}

.info-grid div,
.metrics-grid div {
    background-color: #f9f9f9;
    padding: 0.6rem;
    border-radius: 3px;
    font-size: 0.95em;
}

.metric-label {
    font-weight: bold;
    margin-right: 0.5rem;
}

.metric-value {
    /* Basic styling */
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

pre {
    background-color: #f5f5f5;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 0.85em;
}
</style>
