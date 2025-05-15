<template>
    <div class="dcf-parameters-form">
        <h4>DCF估值参数</h4>
        <form @submit.prevent="submitValuationRequest">
            <div class="form-group">
                <label for="stock-code">股票代码:</label>
                <input type="text" id="stock-code" v-model="params.stock_code" required />
                <span class="hint">例如: 000001.SZ 或 600519.SH (Streamlit默认: 600519.SH)</span>
            </div>

            <div class="form-group">
                <label for="valuation-date">估值基准日期:</label>
                <input type="date" id="valuation-date" v-model="params.valuation_date" />
                <span class="hint">默认为今天</span>
            </div>

            <div class="form-group">
                <label for="prediction-years">预测年限:</label>
                <input type="number" id="prediction-years" v-model.number="params.prediction_years" min="3" max="15" />
                <span class="hint">范围: 3-15 年 (Streamlit默认: 5年)</span>
            </div>

            <div class="form-group">
                <label for="cagr-decay-rate">历史CAGR年衰减率 (0-1):</label>
                <input type="number" id="cagr-decay-rate" v-model.number="params.cagr_decay_rate" step="0.01" min="0"
                    max="1" />
                <span class="hint">例如: 0.1 代表10%的年衰减率。留空则使用后端默认。</span>
            </div>

            <!-- 详细财务假设 -->
            <fieldset class="form-section">
                <legend>详细财务假设</legend>

                <!-- 营业利润率预测 -->
                <div class="form-subsection">
                    <h5>营业利润率预测</h5>
                    <div class="form-group">
                        <label for="op-margin-forecast-mode">预测模式:</label>
                        <select id="op-margin-forecast-mode" v-model="params.op_margin_forecast_mode">
                            <option value="historical_median">使用历史中位数</option>
                            <option value="transition_to_target">过渡到目标值</option>
                        </select>
                    </div>
                    <div v-if="params.op_margin_forecast_mode === 'transition_to_target'">
                        <div class="form-group">
                            <label for="target-operating-margin">目标营业利润率 (%):</label>
                            <input type="number" id="target-operating-margin"
                                v-model.number="params.target_operating_margin" step="0.01" />
                        </div>
                        <div class="form-group">
                            <label for="op-margin-transition-years">过渡年数:</label>
                            <input type="number" id="op-margin-transition-years"
                                v-model.number="params.op_margin_transition_years" min="1" />
                        </div>
                    </div>
                </div>

                <!-- SGA & RD 费用率预测 -->
                <div class="form-subsection">
                    <h5>SGA & RD 费用率预测</h5>
                    <div class="form-group">
                        <label for="sga-rd-ratio-forecast-mode">预测模式:</label>
                        <select id="sga-rd-ratio-forecast-mode" v-model="params.sga_rd_ratio_forecast_mode">
                            <option value="historical_median">使用历史中位数</option>
                            <option value="transition_to_target">过渡到目标值</option>
                        </select>
                    </div>
                    <div v-if="params.sga_rd_ratio_forecast_mode === 'transition_to_target'">
                        <div class="form-group">
                            <label for="target-sga-rd-ratio">目标SGA & RD占收入比 (%):</label>
                            <input type="number" id="target-sga-rd-ratio"
                                v-model.number="params.target_sga_rd_to_revenue_ratio" step="0.01" />
                        </div>
                        <div class="form-group">
                            <label for="sga-rd-transition-years">过渡年数:</label>
                            <input type="number" id="sga-rd-transition-years"
                                v-model.number="params.sga_rd_transition_years" min="1" />
                        </div>
                    </div>
                </div>

                <!-- D&A 占收入比预测 -->
                <div class="form-subsection">
                    <h5>D&A 占收入比预测</h5>
                    <div class="form-group">
                        <label for="da-ratio-forecast-mode">预测模式:</label>
                        <select id="da-ratio-forecast-mode" v-model="params.da_ratio_forecast_mode">
                            <option value="historical_median">使用历史中位数</option>
                            <option value="transition_to_target">过渡到目标值</option>
                        </select>
                    </div>
                    <div v-if="params.da_ratio_forecast_mode === 'transition_to_target'">
                        <div class="form-group">
                            <label for="target-da-ratio">目标D&A占收入比 (%):</label>
                            <input type="number" id="target-da-ratio" v-model.number="params.target_da_to_revenue_ratio"
                                step="0.01" />
                        </div>
                        <div class="form-group">
                            <label for="da-ratio-transition-years">过渡年数:</label>
                            <input type="number" id="da-ratio-transition-years"
                                v-model.number="params.da_ratio_transition_years" min="1" />
                        </div>
                    </div>
                </div>

                <!-- Capex 占收入比预测 -->
                <div class="form-subsection">
                    <h5>Capex 占收入比预测</h5>
                    <div class="form-group">
                        <label for="capex-ratio-forecast-mode">预测模式:</label>
                        <select id="capex-ratio-forecast-mode" v-model="params.capex_ratio_forecast_mode">
                            <option value="historical_median">使用历史中位数</option>
                            <option value="transition_to_target">过渡到目标值</option>
                        </select>
                    </div>
                    <div v-if="params.capex_ratio_forecast_mode === 'transition_to_target'">
                        <div class="form-group">
                            <label for="target-capex-ratio">目标Capex占收入比 (%):</label>
                            <input type="number" id="target-capex-ratio"
                                v-model.number="params.target_capex_to_revenue_ratio" step="0.01" />
                        </div>
                        <div class="form-group">
                            <label for="capex-ratio-transition-years">过渡年数:</label>
                            <input type="number" id="capex-ratio-transition-years"
                                v-model.number="params.capex_ratio_transition_years" min="1" />
                        </div>
                    </div>
                </div>

                <!-- NWC 周转天数预测 -->
                <div class="form-subsection">
                    <h5>NWC 周转天数预测</h5>
                    <div class="form-group">
                        <label for="nwc-days-forecast-mode">预测模式:</label>
                        <select id="nwc-days-forecast-mode" v-model="params.nwc_days_forecast_mode">
                            <option value="historical_median">使用历史中位数</option>
                            <option value="transition_to_target">过渡到目标值</option>
                        </select>
                    </div>
                    <div v-if="params.nwc_days_forecast_mode === 'transition_to_target'">
                        <div class="form-group">
                            <label for="target-ar-days">目标应收账款周转天数 (DSO):</label>
                            <input type="number" id="target-ar-days"
                                v-model.number="params.target_accounts_receivable_days" min="0" />
                        </div>
                        <div class="form-group">
                            <label for="target-inv-days">目标存货周转天数 (DIO):</label>
                            <input type="number" id="target-inv-days" v-model.number="params.target_inventory_days"
                                min="0" />
                        </div>
                        <div class="form-group">
                            <label for="target-ap-days">目标应付账款周转天数 (DPO):</label>
                            <input type="number" id="target-ap-days"
                                v-model.number="params.target_accounts_payable_days" min="0" />
                        </div>
                        <div class="form-group">
                            <label for="nwc-days-transition-years">过渡年数:</label>
                            <input type="number" id="nwc-days-transition-years"
                                v-model.number="params.nwc_days_transition_years" min="1" />
                        </div>
                    </div>
                </div>

                <!-- 其他 NWC 比率预测 -->
                <div class="form-subsection">
                    <h5>其他 NWC 比率预测</h5>
                    <div class="form-group">
                        <label for="other-nwc-ratio-forecast-mode">预测模式:</label>
                        <select id="other-nwc-ratio-forecast-mode" v-model="params.other_nwc_ratio_forecast_mode">
                            <option value="historical_median">使用历史中位数</option>
                            <option value="transition_to_target">过渡到目标值</option>
                        </select>
                    </div>
                    <div v-if="params.other_nwc_ratio_forecast_mode === 'transition_to_target'">
                        <div class="form-group">
                            <label for="target-other-ca-ratio">目标其他流动资产占收入比 (%):</label>
                            <input type="number" id="target-other-ca-ratio"
                                v-model.number="params.target_other_current_assets_to_revenue_ratio" step="0.01" />
                        </div>
                        <div class="form-group">
                            <label for="target-other-cl-ratio">目标其他流动负债占收入比 (%):</label>
                            <input type="number" id="target-other-cl-ratio"
                                v-model.number="params.target_other_current_liabilities_to_revenue_ratio" step="0.01" />
                        </div>
                        <div class="form-group">
                            <label for="other-nwc-ratio-transition-years">过渡年数:</label>
                            <input type="number" id="other-nwc-ratio-transition-years"
                                v-model.number="params.other_nwc_ratio_transition_years" min="1" />
                        </div>
                    </div>
                </div>

                <!-- 税率 -->
                <div class="form-subsection">
                    <h5>税率</h5>
                    <div class="form-group">
                        <label for="target-effective-tax-rate">目标有效所得税率 (%):</label>
                        <input type="number" id="target-effective-tax-rate"
                            v-model.number="params.target_effective_tax_rate" step="0.01" min="0" max="100" />
                    </div>
                </div>

            </fieldset>

            <!-- WACC 计算参数 -->
            <fieldset class="form-section">
                <legend>WACC 计算假设</legend>
                <div class="form-group">
                    <label for="wacc-weight-mode">WACC权重模式:</label>
                    <select id="wacc-weight-mode" v-model="params.wacc_weight_mode">
                        <option value="market">使用最新市场价值计算权重</option>
                        <option value="target">使用目标债务比例</option>
                    </select>
                </div>
                <div v-if="params.wacc_weight_mode === 'target'">
                    <div class="form-group">
                        <label for="target-debt-ratio">目标债务比例 D/(D+E) (%):</label>
                        <input type="number" id="target-debt-ratio" v-model.number="params.target_debt_ratio"
                            step="0.01" min="0" max="100" />
                    </div>
                </div>
                <div class="form-group">
                    <label for="cost-of-debt">税前债务成本 (%):</label>
                    <input type="number" id="cost-of-debt" v-model.number="params.cost_of_debt" step="0.01" min="0" />
                </div>
                <div class="form-group">
                    <label for="risk-free-rate">无风险利率 (%):</label>
                    <input type="number" id="risk-free-rate" v-model.number="params.risk_free_rate" step="0.01"
                        min="0" />
                </div>
                <div class="form-group">
                    <label for="beta">贝塔系数 (Levered Beta):</label>
                    <input type="number" id="beta" v-model.number="params.beta" step="0.01" />
                </div>
                <div class="form-group">
                    <label for="market-risk-premium">市场风险溢价 (%):</label>
                    <input type="number" id="market-risk-premium" v-model.number="params.market_risk_premium"
                        step="0.01" min="0" />
                </div>
                <div class="form-group">
                    <label for="size-premium">规模溢价 (%):</label>
                    <input type="number" id="size-premium" v-model.number="params.size_premium" step="0.01" />
                </div>
            </fieldset>

            <!-- 终值计算参数 -->
            <fieldset class="form-section">
                <legend>终值计算假设</legend>
                <div class="form-group">
                    <label for="terminal-value-method">终值计算方法:</label>
                    <select id="terminal-value-method" v-model="params.terminal_value_method">
                        <option value="perpetual_growth">永续增长率法</option>
                        <option value="exit_multiple">退出乘数法</option>
                    </select>
                </div>
                <div v-if="params.terminal_value_method === 'exit_multiple'" class="form-group">
                    <label for="exit-multiple">退出乘数 (基于EBITDA):</label>
                    <input type="number" id="exit-multiple" v-model.number="params.exit_multiple" step="0.1" min="0" />
                </div>
                <div v-if="params.terminal_value_method === 'perpetual_growth'" class="form-group">
                    <label for="terminal-growth-rate-conditional">永续增长率 (%):</label>
                    <input type="number" id="terminal-growth-rate-conditional"
                        v-model.number="params.terminal_growth_rate" step="0.01" />
                    <span class="hint">例如: 2.5 代表2.5%</span>
                </div>
            </fieldset>

            <!-- LLM 控制参数 -->
            <fieldset class="form-section">
                <legend>LLM 分析总结</legend>
                <div class="form-group">
                    <label for="request-llm-summary">启用LLM分析总结:</label>
                    <input type="checkbox" id="request-llm-summary" v-model="params.request_llm_summary" />
                </div>
                <div v-if="params.request_llm_summary">
                    <div class="form-group">
                        <label for="llm-provider">LLM提供商:</label>
                        <select id="llm-provider" v-model="params.llm_provider">
                            <option :value="null">后端默认</option>
                            <option value="deepseek">DeepSeek</option>
                            <option value="custom_openai">自定义OpenAI兼容模型</option>
                        </select>
                    </div>
                    <div class="form-group" v-if="params.llm_provider === 'custom_openai'">
                        <label for="llm-api-base-url">LLM API Base URL:</label>
                        <input type="text" id="llm-api-base-url" v-model="params.llm_api_base_url" />
                    </div>
                    <div class="form-group">
                        <label for="llm-model-id">LLM模型ID:</label>
                        <input type="text" id="llm-model-id" v-model="params.llm_model_id" />
                        <span class="hint">例如: deepseek-chat, gpt-4-turbo 等。留空则使用提供商默认。</span>
                    </div>
                    <div class="form-group">
                        <label for="llm-temperature">Temperature (0-2):</label>
                        <input type="number" id="llm-temperature" v-model.number="params.llm_temperature" step="0.1"
                            min="0" max="2" />
                    </div>
                    <div class="form-group">
                        <label for="llm-top-p">Top P (0-1):</label>
                        <input type="number" id="llm-top-p" v-model.number="params.llm_top_p" step="0.01" min="0"
                            max="1" />
                    </div>
                    <div class="form-group">
                        <label for="llm-max-tokens">Max Tokens:</label>
                        <input type="number" id="llm-max-tokens" v-model.number="params.llm_max_tokens" min="1" />
                    </div>
                </div>
            </fieldset>

            <!-- 敏感性分析配置 -->
            <fieldset class="form-section">
                <legend>敏感性分析配置</legend>
                <div class="form-group">
                    <label for="enable-sensitivity-analysis">启用敏感性分析:</label>
                    <input type="checkbox" id="enable-sensitivity-analysis"
                        v-model="params.enable_sensitivity_analysis" />
                </div>

                <div v-if="params.enable_sensitivity_analysis">
                    <div class="form-subsection">
                        <h5>WACC 敏感性</h5>
                        <div class="form-group">
                            <label for="sensitivity-wacc-step">WACC 变动步长 (%):</label>
                            <input type="number" id="sensitivity-wacc-step"
                                v-model.number="params.sensitivity_wacc_step" step="0.01" />
                            <span class="hint">例如: 0.5 代表围绕中心WACC上下浮动0.5个百分点。</span>
                        </div>
                        <div class="form-group">
                            <label for="sensitivity-wacc-points">WACC 分析点数:</label>
                            <input type="number" id="sensitivity-wacc-points"
                                v-model.number="params.sensitivity_wacc_points" min="1" max="11" step="2" />
                            <span class="hint">例如: 3 (中心值, 中心值-步长, 中心值+步长) 或 5。建议奇数, 最大11。</span>
                        </div>
                    </div>

                    <div class="form-subsection">
                        <h5>退出乘数 (Exit Multiple) 敏感性</h5>
                        <div class="form-group">
                            <label for="sensitivity-exit-multiple-step">退出乘数 变动步长 (绝对值):</label>
                            <input type="number" id="sensitivity-exit-multiple-step"
                                v-model.number="params.sensitivity_exit_multiple_step" step="0.1" />
                            <span class="hint">例如: 0.5 代表围绕中心乘数上下浮动0.5。</span>
                        </div>
                        <div class="form-group">
                            <label for="sensitivity-exit-multiple-points">退出乘数 分析点数:</label>
                            <input type="number" id="sensitivity-exit-multiple-points"
                                v-model.number="params.sensitivity_exit_multiple_points" min="1" max="11" step="2" />
                            <span class="hint">例如: 3 或 5。建议奇数, 最大11。</span>
                        </div>
                    </div>
                </div>
            </fieldset>

            <!-- 更多参数可以后续添加，例如预测模式、具体财务假设等 -->
            <p class="info">更详细的财务预测假设（如收入增长模式、利润率等）将在后续版本中提供配置。</p>

            <button type="submit" :disabled="isLoading">
                {{ isLoading ? '正在计算...' : '开始估值' }}
            </button>
        </form>
    </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue';
import type { ApiDcfValuationRequest, ApiSensitivityAnalysisRequest, ApiSensitivityAxis } from '../../../shared-types/src'; // Adjust path as needed

// defineEmits and defineProps are compiler macros and no longer need to be imported.

const simpleAxisParamDisplayNames: Record<string, string> = {
    "wacc": "WACC",
    "exit_multiple": "退出乘数",
    "terminal_growth_rate": "永续增长率"
};

// 表单使用的参数结构，百分比按用户输入习惯（例如8.5代表8.5%）
export interface DcfFormParameters {
    stock_code: string;
    valuation_date?: string | null; // YYYY-MM-DD
    // discount_rate: number | null; // Removed as per user feedback
    terminal_growth_rate: number | null; // e.g., 2.5 for 2.5%
    prediction_years: number | null; // e.g., 5
    cagr_decay_rate?: number | null; // e.g., 0.1 for 10%

    // 利润率预测
    op_margin_forecast_mode: 'historical_median' | 'transition_to_target';
    target_operating_margin?: number | null; // e.g., 15 for 15%
    op_margin_transition_years?: number | null;

    // SGA & RD 费用率预测
    sga_rd_ratio_forecast_mode: 'historical_median' | 'transition_to_target';
    target_sga_rd_to_revenue_ratio?: number | null; // e.g., 10 for 10%
    sga_rd_transition_years?: number | null;

    // D&A 占收入比预测
    da_ratio_forecast_mode: 'historical_median' | 'transition_to_target';
    target_da_to_revenue_ratio?: number | null; // e.g., 5 for 5%
    da_ratio_transition_years?: number | null;

    // Capex 占收入比预测
    capex_ratio_forecast_mode: 'historical_median' | 'transition_to_target';
    target_capex_to_revenue_ratio?: number | null; // e.g., 3 for 3%
    capex_ratio_transition_years?: number | null;

    // NWC 周转天数预测
    nwc_days_forecast_mode: 'historical_median' | 'transition_to_target';
    target_accounts_receivable_days?: number | null;
    target_inventory_days?: number | null;
    target_accounts_payable_days?: number | null;
    nwc_days_transition_years?: number | null;

    // 其他 NWC 比率预测
    other_nwc_ratio_forecast_mode: 'historical_median' | 'transition_to_target';
    target_other_current_assets_to_revenue_ratio?: number | null;
    target_other_current_liabilities_to_revenue_ratio?: number | null;
    other_nwc_ratio_transition_years?: number | null;

    // 税率
    target_effective_tax_rate?: number | null; // e.g., 25 for 25%

    // WACC 计算参数
    wacc_weight_mode: 'target' | 'market';
    target_debt_ratio?: number | null; // e.g., 30 for 30%
    cost_of_debt?: number | null; // e.g., 5 for 5%
    risk_free_rate?: number | null; // e.g., 2.5 for 2.5%
    beta?: number | null;
    market_risk_premium?: number | null; // e.g., 6 for 6%
    size_premium?: number | null; // e.g., 1 for 1%

    // 终值计算参数
    terminal_value_method: 'exit_multiple' | 'perpetual_growth';
    exit_multiple?: number | null;

    // LLM 控制参数
    request_llm_summary: boolean;
    llm_provider?: 'deepseek' | 'custom_openai' | null;
    llm_model_id?: string | null;
    llm_api_base_url?: string | null;
    llm_temperature?: number | null;
    llm_top_p?: number | null;
    llm_max_tokens?: number | null;

    // 敏感性分析
    sensitivity_analysis?: ApiSensitivityAnalysisRequest | null;

    // 新增：敏感性分析参数 (这些是表单的直接 v-model 绑定)
    enable_sensitivity_analysis: boolean;
    sensitivity_wacc_step?: number | null; // e.g., 0.5 for 0.5% step
    sensitivity_wacc_points?: number | null; // e.g., 3 or 5 points
    sensitivity_exit_multiple_step?: number | null; // e.g., 0.5 for absolute step
    sensitivity_exit_multiple_points?: number | null;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const props = defineProps<{
    isLoading: boolean;
    initialStockCode?: string | null;
}>();

const getTodayDateString = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = (today.getMonth() + 1).toString().padStart(2, '0');
    const day = today.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
};

const params = reactive<DcfFormParameters>({
    stock_code: props.initialStockCode || '600519.SH', // Streamlit default
    valuation_date: getTodayDateString(), // Streamlit default
    // discount_rate: 8.5, // Removed
    terminal_growth_rate: 2.5, // Streamlit default 0.025
    prediction_years: 5, // Streamlit default
    cagr_decay_rate: 0.1, // Streamlit default

    op_margin_forecast_mode: 'historical_median', // Streamlit default
    target_operating_margin: 15, // Streamlit default 0.15
    op_margin_transition_years: 5, // Streamlit default forecast_years_val

    sga_rd_ratio_forecast_mode: 'historical_median', // Streamlit default
    target_sga_rd_to_revenue_ratio: 20, // Streamlit default 0.20
    sga_rd_transition_years: 5, // Streamlit default forecast_years_val

    da_ratio_forecast_mode: 'historical_median', // Streamlit default
    target_da_to_revenue_ratio: 5, // Streamlit default 0.05
    da_ratio_transition_years: 5, // Streamlit default forecast_years_val

    capex_ratio_forecast_mode: 'historical_median', // Streamlit default
    target_capex_to_revenue_ratio: 7, // Streamlit default 0.07
    capex_ratio_transition_years: 5, // Streamlit default forecast_years_val

    nwc_days_forecast_mode: 'historical_median', // Streamlit default
    target_accounts_receivable_days: 30, // Streamlit default 30.0
    target_inventory_days: 60, // Streamlit default 60.0
    target_accounts_payable_days: 45, // Streamlit default 45.0
    nwc_days_transition_years: 5, // Streamlit default forecast_years_val

    other_nwc_ratio_forecast_mode: 'historical_median', // Streamlit default
    target_other_current_assets_to_revenue_ratio: 5, // Streamlit default 0.05
    target_other_current_liabilities_to_revenue_ratio: 3, // Streamlit default 0.03
    other_nwc_ratio_transition_years: 5, // Streamlit default forecast_years_val

    target_effective_tax_rate: 25, // Streamlit default 0.25

    wacc_weight_mode: 'market', // Streamlit default "使用最新市场价值计算权重" -> 'market'
    target_debt_ratio: 45, // Streamlit default 0.45
    cost_of_debt: 5, // Streamlit default 0.05
    risk_free_rate: 3, // Streamlit default 0.03
    beta: 1.0, // Streamlit default 1.0
    market_risk_premium: 6, // Streamlit default 0.06
    size_premium: null, // Streamlit has no direct input, keep null or a sensible default like 0 or 1

    terminal_value_method: 'exit_multiple', // Streamlit default
    exit_multiple: 7.0, // Streamlit default

    request_llm_summary: false, // Streamlit default
    llm_provider: 'deepseek', // Streamlit default from env or "DeepSeek" UI
    llm_model_id: null,
    llm_api_base_url: null,
    llm_temperature: null,
    llm_top_p: null,
    llm_max_tokens: null,

    // 敏感性分析默认值
    enable_sensitivity_analysis: false,
    sensitivity_wacc_step: 0.5, // 用户输入 0.5 代表 0.5%
    sensitivity_wacc_points: 3,
    sensitivity_exit_multiple_step: 0.5,
    sensitivity_exit_multiple_points: 3,
});

const emit = defineEmits(['submit-valuation', 'validation-error']);

const submitValuationRequest = () => {
    if (!params.stock_code) {
        emit('validation-error', '股票代码为必填项！');
        return;
    }

    // Prepare payload, converting empty strings from number inputs to null
    // and ensuring all fields from DcfFormParameters are present
    // Also, convert percentage inputs (like 2.5 for 2.5%) to decimals (0.025) for API
    const apiPayload: ApiDcfValuationRequest = { // Use ApiDcfValuationRequest for type safety with API
        stock_code: params.stock_code,
        valuation_date: params.valuation_date, // Assuming backend handles date string
        // discount_rate: (typeof params.discount_rate === 'number' && !isNaN(params.discount_rate)) ? params.discount_rate : null, // Removed
        terminal_growth_rate: (typeof params.terminal_growth_rate === 'number' && !isNaN(params.terminal_growth_rate)) ? params.terminal_growth_rate / 100 : null,
        prediction_years: (typeof params.prediction_years === 'number' && !isNaN(params.prediction_years)) ? params.prediction_years : null,
        cagr_decay_rate: (typeof params.cagr_decay_rate === 'number' && !isNaN(params.cagr_decay_rate)) ? params.cagr_decay_rate : null,

        op_margin_forecast_mode: params.op_margin_forecast_mode,
        target_operating_margin: (typeof params.target_operating_margin === 'number' && !isNaN(params.target_operating_margin)) ? params.target_operating_margin / 100 : null,
        op_margin_transition_years: (typeof params.op_margin_transition_years === 'number' && !isNaN(params.op_margin_transition_years)) ? params.op_margin_transition_years : null,

        sga_rd_ratio_forecast_mode: params.sga_rd_ratio_forecast_mode,
        target_sga_rd_to_revenue_ratio: (typeof params.target_sga_rd_to_revenue_ratio === 'number' && !isNaN(params.target_sga_rd_to_revenue_ratio)) ? params.target_sga_rd_to_revenue_ratio / 100 : null,
        sga_rd_transition_years: (typeof params.sga_rd_transition_years === 'number' && !isNaN(params.sga_rd_transition_years)) ? params.sga_rd_transition_years : null,

        da_ratio_forecast_mode: params.da_ratio_forecast_mode,
        target_da_to_revenue_ratio: (typeof params.target_da_to_revenue_ratio === 'number' && !isNaN(params.target_da_to_revenue_ratio)) ? params.target_da_to_revenue_ratio / 100 : null,
        da_ratio_transition_years: (typeof params.da_ratio_transition_years === 'number' && !isNaN(params.da_ratio_transition_years)) ? params.da_ratio_transition_years : null,

        capex_ratio_forecast_mode: params.capex_ratio_forecast_mode,
        target_capex_to_revenue_ratio: (typeof params.target_capex_to_revenue_ratio === 'number' && !isNaN(params.target_capex_to_revenue_ratio)) ? params.target_capex_to_revenue_ratio / 100 : null,
        capex_ratio_transition_years: (typeof params.capex_ratio_transition_years === 'number' && !isNaN(params.capex_ratio_transition_years)) ? params.capex_ratio_transition_years : null,

        nwc_days_forecast_mode: params.nwc_days_forecast_mode,
        target_accounts_receivable_days: (typeof params.target_accounts_receivable_days === 'number' && !isNaN(params.target_accounts_receivable_days)) ? params.target_accounts_receivable_days : null,
        target_inventory_days: (typeof params.target_inventory_days === 'number' && !isNaN(params.target_inventory_days)) ? params.target_inventory_days : null,
        target_accounts_payable_days: (typeof params.target_accounts_payable_days === 'number' && !isNaN(params.target_accounts_payable_days)) ? params.target_accounts_payable_days : null,
        nwc_days_transition_years: (typeof params.nwc_days_transition_years === 'number' && !isNaN(params.nwc_days_transition_years)) ? params.nwc_days_transition_years : null,

        other_nwc_ratio_forecast_mode: params.other_nwc_ratio_forecast_mode,
        target_other_current_assets_to_revenue_ratio: (typeof params.target_other_current_assets_to_revenue_ratio === 'number' && !isNaN(params.target_other_current_assets_to_revenue_ratio)) ? params.target_other_current_assets_to_revenue_ratio / 100 : null,
        target_other_current_liabilities_to_revenue_ratio: (typeof params.target_other_current_liabilities_to_revenue_ratio === 'number' && !isNaN(params.target_other_current_liabilities_to_revenue_ratio)) ? params.target_other_current_liabilities_to_revenue_ratio / 100 : null,
        other_nwc_ratio_transition_years: (typeof params.other_nwc_ratio_transition_years === 'number' && !isNaN(params.other_nwc_ratio_transition_years)) ? params.other_nwc_ratio_transition_years : null,

        target_effective_tax_rate: (typeof params.target_effective_tax_rate === 'number' && !isNaN(params.target_effective_tax_rate)) ? params.target_effective_tax_rate / 100 : null,

        wacc_weight_mode: params.wacc_weight_mode,
        target_debt_ratio: (typeof params.target_debt_ratio === 'number' && !isNaN(params.target_debt_ratio)) ? params.target_debt_ratio / 100 : null,
        cost_of_debt: (typeof params.cost_of_debt === 'number' && !isNaN(params.cost_of_debt)) ? params.cost_of_debt / 100 : null,
        risk_free_rate: (typeof params.risk_free_rate === 'number' && !isNaN(params.risk_free_rate)) ? params.risk_free_rate / 100 : null,
        beta: (typeof params.beta === 'number' && !isNaN(params.beta)) ? params.beta : null,
        market_risk_premium: (typeof params.market_risk_premium === 'number' && !isNaN(params.market_risk_premium)) ? params.market_risk_premium / 100 : null,
        // size_premium will be conditionally added below
        // size_premium: (typeof params.size_premium === 'number' && !isNaN(params.size_premium)) ? params.size_premium / 100 : null,

        terminal_value_method: params.terminal_value_method,
        exit_multiple: (typeof params.exit_multiple === 'number' && !isNaN(params.exit_multiple)) ? params.exit_multiple : null,

        request_llm_summary: params.request_llm_summary,
        llm_provider: params.llm_provider,
        llm_model_id: params.llm_model_id,
        llm_api_base_url: params.llm_api_base_url,
        llm_temperature: (typeof params.llm_temperature === 'number' && !isNaN(params.llm_temperature)) ? params.llm_temperature : null,
        llm_top_p: (typeof params.llm_top_p === 'number' && !isNaN(params.llm_top_p)) ? params.llm_top_p : null,
        llm_max_tokens: (typeof params.llm_max_tokens === 'number' && !isNaN(params.llm_max_tokens)) ? params.llm_max_tokens : null,

        // Sensitivity analysis part will be constructed below
        sensitivity_analysis: null
        // size_premium is intentionally omitted here if not valid, to be added conditionally
    };

    // Conditionally add size_premium if it's a valid number
    if (typeof params.size_premium === 'number' && !isNaN(params.size_premium)) {
        apiPayload.size_premium = params.size_premium / 100;
    }
    // Otherwise, apiPayload.size_premium remains undefined and won't be sent

    if (params.enable_sensitivity_analysis) {
        // Validation for sensitivity steps and points before constructing the objects for the payload
        const maxSensitivityPoints = 11;
        if (params.sensitivity_wacc_points && params.sensitivity_wacc_points > 1 && (params.sensitivity_wacc_step === 0 || params.sensitivity_wacc_step === null || params.sensitivity_wacc_step === undefined)) {
            emit('validation-error', `当 ${simpleAxisParamDisplayNames['wacc']} 的分析点数大于1时，其变动步长不能为空且不能为0。`);
            return;
        }
        if (params.sensitivity_wacc_points && params.sensitivity_wacc_points > maxSensitivityPoints) {
            emit('validation-error', `${simpleAxisParamDisplayNames['wacc']} 的分析点数不能超过 ${maxSensitivityPoints}。`);
            return;
        }

        // Axis2 is always exit_multiple for sensitivity analysis as per user request
        if (params.sensitivity_exit_multiple_points && params.sensitivity_exit_multiple_points > 1 && (params.sensitivity_exit_multiple_step === 0 || params.sensitivity_exit_multiple_step === null || params.sensitivity_exit_multiple_step === undefined)) {
            emit('validation-error', `当 ${simpleAxisParamDisplayNames['exit_multiple']} 的分析点数大于1时，其变动步长不能为空且不能为0。`);
            return;
        }
        if (params.sensitivity_exit_multiple_points && params.sensitivity_exit_multiple_points > maxSensitivityPoints) {
            emit('validation-error', `${simpleAxisParamDisplayNames['exit_multiple']} 的分析点数不能超过 ${maxSensitivityPoints}。`);
            return;
        }

        const axis1: ApiSensitivityAxis = {
            parameter_name: 'wacc',
            step: (typeof params.sensitivity_wacc_step === 'number' && !isNaN(params.sensitivity_wacc_step)) ? params.sensitivity_wacc_step / 100 : 0,
            points: (typeof params.sensitivity_wacc_points === 'number' && !isNaN(params.sensitivity_wacc_points)) ? params.sensitivity_wacc_points : 1,
            value_type: 'percentage',
            values: []
        };

        const axis2: ApiSensitivityAxis = {
            parameter_name: 'exit_multiple',
            step: (typeof params.sensitivity_exit_multiple_step === 'number' && !isNaN(params.sensitivity_exit_multiple_step)) ? params.sensitivity_exit_multiple_step : 0,
            points: (typeof params.sensitivity_exit_multiple_points === 'number' && !isNaN(params.sensitivity_exit_multiple_points)) ? params.sensitivity_exit_multiple_points : 1,
            value_type: 'absolute',
            values: []
        };

        // Ensure points are odd and >= 1 
        if (axis1.points && axis1.points < 1) axis1.points = 1;
        if (axis1.points && axis1.points % 2 === 0) axis1.points += 1;
        if (axis2.points && axis2.points < 1) axis2.points = 1;
        if (axis2.points && axis2.points % 2 === 0) axis2.points += 1;


        apiPayload.sensitivity_analysis = {
            row_axis: axis1,
            column_axis: axis2,
            output_metrics: [
                'value_per_share',
                'enterprise_value',
                'equity_value',
                'ev_ebitda',
                'dcf_implied_diluted_pe',
                'tv_ev_ratio'
            ]
        };
    } else {
        apiPayload.sensitivity_analysis = null;
    }

    if (typeof apiPayload.prediction_years === 'number' && (apiPayload.prediction_years < 1 || apiPayload.prediction_years > 20)) {
        emit('validation-error', '预测年限必须在1到20年之间（如果填写）。');
        return;
    }

    if (typeof apiPayload.cagr_decay_rate === 'number' && (apiPayload.cagr_decay_rate < 0 || apiPayload.cagr_decay_rate > 1)) {
        emit('validation-error', '历史CAGR年衰减率必须在0到1之间（如果填写）。');
        return;
    }

    const checkTransitionYears = (transitionYears: number | null | undefined, predictionYears: number | null | undefined, fieldName: string): boolean => {
        if (predictionYears !== null && predictionYears !== undefined &&
            transitionYears !== null && transitionYears !== undefined &&
            transitionYears > predictionYears) {
            emit('validation-error', `${fieldName}的过渡年数 (${transitionYears}年) 不能超过预测期年数 (${predictionYears}年)。`);
            return false;
        }
        return true;
    };

    if (params.op_margin_forecast_mode === 'transition_to_target') {
        if (params.target_operating_margin === null || params.target_operating_margin === undefined) {
            emit('validation-error', '当营业利润率预测模式为“过渡到目标值”时，目标营业利润率不能为空。');
            return;
        }
        if (params.op_margin_transition_years === null || params.op_margin_transition_years === undefined || params.op_margin_transition_years < 1) {
            emit('validation-error', '当营业利润率预测模式为“过渡到目标值”时，过渡年数必须大于等于1。');
            return;
        }
        if (!checkTransitionYears(params.op_margin_transition_years, params.prediction_years, '营业利润率')) return;
        if (typeof params.target_operating_margin === 'number' && (params.target_operating_margin < -50 || params.target_operating_margin > 100)) {
            emit('validation-error', '目标营业利润率应在 -50% 到 100% 之间。');
            return;
        }
    }

    if (params.sga_rd_ratio_forecast_mode === 'transition_to_target') {
        if (params.target_sga_rd_to_revenue_ratio === null || params.target_sga_rd_to_revenue_ratio === undefined) {
            emit('validation-error', '当SGA&RD占收入比预测模式为“过渡到目标值”时，目标SGA&RD占收入比不能为空。');
            return;
        }
        if (params.sga_rd_transition_years === null || params.sga_rd_transition_years === undefined || params.sga_rd_transition_years < 1) {
            emit('validation-error', '当SGA&RD占收入比预测模式为“过渡到目标值”时，过渡年数必须大于等于1。');
            return;
        }
        if (!checkTransitionYears(params.sga_rd_transition_years, params.prediction_years, 'SGA&RD占收入比')) return;
        if (typeof params.target_sga_rd_to_revenue_ratio === 'number' && (params.target_sga_rd_to_revenue_ratio < 0 || params.target_sga_rd_to_revenue_ratio > 100)) {
            emit('validation-error', '目标SGA&RD占收入比应在 0% 到 100% 之间。');
            return;
        }
    }

    if (params.da_ratio_forecast_mode === 'transition_to_target') {
        if (params.target_da_to_revenue_ratio === null || params.target_da_to_revenue_ratio === undefined) {
            emit('validation-error', '当D&A占收入比预测模式为“过渡到目标值”时，目标D&A占收入比不能为空。');
            return;
        }
        if (params.da_ratio_transition_years === null || params.da_ratio_transition_years === undefined || params.da_ratio_transition_years < 1) {
            emit('validation-error', '当D&A占收入比预测模式为“过渡到目标值”时，过渡年数必须大于等于1。');
            return;
        }
        if (!checkTransitionYears(params.da_ratio_transition_years, params.prediction_years, 'D&A占收入比')) return;
        if (typeof params.target_da_to_revenue_ratio === 'number' && (params.target_da_to_revenue_ratio < 0 || params.target_da_to_revenue_ratio > 50)) {
            emit('validation-error', '目标D&A占收入比应在 0% 到 50% 之间。');
            return;
        }
    }

    if (params.capex_ratio_forecast_mode === 'transition_to_target') {
        if (params.target_capex_to_revenue_ratio === null || params.target_capex_to_revenue_ratio === undefined) {
            emit('validation-error', '当Capex占收入比预测模式为“过渡到目标值”时，目标Capex占收入比不能为空。');
            return;
        }
        if (params.capex_ratio_transition_years === null || params.capex_ratio_transition_years === undefined || params.capex_ratio_transition_years < 1) {
            emit('validation-error', '当Capex占收入比预测模式为“过渡到目标值”时，过渡年数必须大于等于1。');
            return;
        }
        if (!checkTransitionYears(params.capex_ratio_transition_years, params.prediction_years, 'Capex占收入比')) return;
        if (typeof params.target_capex_to_revenue_ratio === 'number' && (params.target_capex_to_revenue_ratio < 0 || params.target_capex_to_revenue_ratio > 50)) {
            emit('validation-error', '目标Capex占收入比应在 0% 到 50% 之间。');
            return;
        }
    }

    if (params.nwc_days_forecast_mode === 'transition_to_target') {
        const anyNwcTargetDaySet = params.target_accounts_receivable_days !== null || params.target_inventory_days !== null || params.target_accounts_payable_days !== null;
        if (anyNwcTargetDaySet && (params.nwc_days_transition_years === null || params.nwc_days_transition_years === undefined || params.nwc_days_transition_years < 1)) {
            emit('validation-error', '当NWC周转天数预测模式为“过渡到目标值”且设置了任一目标天数时，过渡年数必须大于等于1。');
            return;
        }
        if (anyNwcTargetDaySet) {
            if (!checkTransitionYears(params.nwc_days_transition_years, params.prediction_years, 'NWC周转天数')) return;
            if (typeof params.target_accounts_receivable_days === 'number' && params.target_accounts_receivable_days < 0) {
                emit('validation-error', '目标应收账款周转天数不能为负。');
                return;
            }
            if (typeof params.target_inventory_days === 'number' && params.target_inventory_days < 0) {
                emit('validation-error', '目标存货周转天数不能为负。');
                return;
            }
            if (typeof params.target_accounts_payable_days === 'number' && params.target_accounts_payable_days < 0) {
                emit('validation-error', '目标应付账款周转天数不能为负。');
                return;
            }
        }
    }

    if (params.other_nwc_ratio_forecast_mode === 'transition_to_target') {
        const anyOtherNwcTargetSet = params.target_other_current_assets_to_revenue_ratio !== null || params.target_other_current_liabilities_to_revenue_ratio !== null;
        if (anyOtherNwcTargetSet && (params.other_nwc_ratio_transition_years === null || params.other_nwc_ratio_transition_years === undefined || params.other_nwc_ratio_transition_years < 1)) {
            emit('validation-error', '当其他NWC比率预测模式为“过渡到目标值”且设置了任一目标比率时，过渡年数必须大于等于1。');
            return;
        }
        if (anyOtherNwcTargetSet) {
            if (!checkTransitionYears(params.other_nwc_ratio_transition_years, params.prediction_years, '其他NWC比率')) return;
            if (typeof params.target_other_current_assets_to_revenue_ratio === 'number' && (params.target_other_current_assets_to_revenue_ratio < 0 || params.target_other_current_assets_to_revenue_ratio > 100)) {
                emit('validation-error', '目标其他流动资产占收入比应在 0% 到 100% 之间。');
                return;
            }
            if (typeof params.target_other_current_liabilities_to_revenue_ratio === 'number' && (params.target_other_current_liabilities_to_revenue_ratio < 0 || params.target_other_current_liabilities_to_revenue_ratio > 100)) {
                emit('validation-error', '目标其他流动负债占收入比应在 0% 到 100% 之间。');
                return;
            }
        }
    }

    if (params.terminal_value_method === 'exit_multiple' && (params.exit_multiple === null || params.exit_multiple === undefined || params.exit_multiple < 0)) {
        emit('validation-error', '当终值计算方法为“退出乘数法”时，退出乘数不能为空且必须大于等于0。');
        return;
    }
    if (params.terminal_value_method === 'perpetual_growth' && (params.terminal_growth_rate === null || params.terminal_growth_rate === undefined)) {
        emit('validation-error', '当终值计算方法为“永续增长率法”时，永续增长率不能为空。');
        return;
    }

    // 税率和WACC参数校验
    if (typeof params.target_effective_tax_rate === 'number' && (params.target_effective_tax_rate < 0 || params.target_effective_tax_rate > 100)) {
        emit('validation-error', '目标有效所得税率应在 0% 到 100% 之间。');
        return;
    }
    if (params.wacc_weight_mode === 'target' && typeof params.target_debt_ratio === 'number' && (params.target_debt_ratio < 0 || params.target_debt_ratio > 100)) {
        emit('validation-error', '目标债务比例应在 0% 到 100% 之间。');
        return;
    }

    // WACC参数范围校验 (用户输入值)
    if (typeof params.risk_free_rate === 'number' && (params.risk_free_rate < 0 || params.risk_free_rate > 10)) {
        emit('validation-error', '无风险利率应在 0% 到 10% 之间。');
        return;
    }
    if (typeof params.market_risk_premium === 'number' && (params.market_risk_premium < 0 || params.market_risk_premium > 15)) {
        emit('validation-error', '市场风险溢价应在 0% 到 15% 之间。');
        return;
    }
    if (typeof params.cost_of_debt === 'number' && (params.cost_of_debt < 0 || params.cost_of_debt > 20)) {
        emit('validation-error', '税前债务成本应在 0% 到 20% 之间。');
        return;
    }
    if (typeof params.beta === 'number' && (params.beta < 0 || params.beta > 3)) {
        emit('validation-error', '贝塔系数应在 0 到 3 之间。');
        return;
    }
    if (typeof params.size_premium === 'number' && (params.size_premium < -5 || params.size_premium > 5)) {
        emit('validation-error', '规模溢价应在 -5% 到 5% 之间。');
        return;
    }

    // 终值参数范围校验 (用户输入值)
    if (params.terminal_value_method === 'perpetual_growth' && typeof params.terminal_growth_rate === 'number') {
        if (params.terminal_growth_rate < 0 || params.terminal_growth_rate > 5) {
            emit('validation-error', '永续增长率应在 0% 到 5% 之间。');
            return;
        }
    }
    if (params.terminal_value_method === 'exit_multiple' && typeof params.exit_multiple === 'number') {
        if (params.exit_multiple < 1 || params.exit_multiple > 30) {
            emit('validation-error', '退出乘数应在 1 到 30 之间。');
            return;
        }
    }

    // LLM Parameters Validation
    if (params.request_llm_summary) {
        if (typeof params.llm_temperature === 'number' && (params.llm_temperature < 0 || params.llm_temperature > 2)) {
            emit('validation-error', 'LLM Temperature 必须在 0 到 2 之间。');
            return;
        }
        if (typeof params.llm_top_p === 'number' && (params.llm_top_p < 0 || params.llm_top_p > 1)) {
            emit('validation-error', 'LLM Top P 必须在 0 到 1 之间。');
            return;
        }
        if (typeof params.llm_max_tokens === 'number' && params.llm_max_tokens < 1) {
            emit('validation-error', 'LLM Max Tokens 必须大于等于 1。');
            return;
        }
        if (params.llm_provider === 'custom_openai' && (!params.llm_api_base_url || params.llm_api_base_url.trim() === '')) {
            emit('validation-error', '当选择自定义OpenAI兼容模型时，LLM API Base URL 不能为空。');
            return;
        }
    }

    emit('submit-valuation', apiPayload);
};

watch(() => props.initialStockCode, (newVal) => {
    if (newVal) {
        params.stock_code = newVal;
    }
});

watch(() => params.prediction_years, (newPredictionYears) => {
    if (typeof newPredictionYears === 'number' && newPredictionYears >= 1) {
        params.op_margin_transition_years = newPredictionYears;
        params.sga_rd_transition_years = newPredictionYears;
        params.da_ratio_transition_years = newPredictionYears;
        params.capex_ratio_transition_years = newPredictionYears;
        params.nwc_days_transition_years = newPredictionYears;
        params.other_nwc_ratio_transition_years = newPredictionYears;
    }
}, { immediate: false });

</script>

<style scoped>
.dcf-parameters-form {
    padding: 1rem;
    border: 1px solid #eee;
    border-radius: 4px;
    background-color: #f9f9f9;
}

.dcf-parameters-form h4,
.form-section legend,
.form-subsection h5 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: #333;
}

.form-section legend {
    font-size: 1.1em;
    font-weight: bold;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #ddd;
    width: 100%;
}

.form-subsection {
    margin-top: 1rem;
    padding-left: 1rem;
    border-left: 2px solid #e0e0e0;
}

.form-subsection h5 {
    font-size: 1em;
    font-weight: bold;
    color: #555;
}

.dcf-parameters-form h4 {
    margin-top: 0;
    margin-bottom: 1rem;
}

.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.3rem;
    font-weight: bold;
}

.form-group input[type="text"],
.form-group input[type="number"],
.form-group select {
    width: calc(100% - 1rem);
    /* Adjust for padding */
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.form-group .hint {
    font-size: 0.8em;
    color: #777;
    display: block;
    margin-top: 0.2rem;
}

button {
    padding: 0.7rem 1.5rem;
    background-color: #42b983;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1em;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

button:hover:not(:disabled) {
    background-color: #36a374;
}

.info {
    font-size: 0.9em;
    color: #555;
    margin-bottom: 1rem;
    padding: 0.5rem;
    background-color: #eef;
    border-left: 3px solid #33a;
}
</style>
