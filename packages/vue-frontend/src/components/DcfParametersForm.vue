<template>
    <div class="space-y-2 min-w-0">
        <form @submit.prevent="submitValuationRequest" class="space-y-2">

            <Card class="bg-background py-3 text-card-foreground flex flex-col gap-2 rounded-xl border">
                <CardHeader class="px-3 py-2 cursor-pointer"
                    @click="collapsedSections.prediction = !collapsedSections.prediction">
                    <div class="flex items-center justify-between">
                        <CardTitle class="text-base">业绩假设</CardTitle>
                        <component :is="collapsedSections.prediction ? ChevronRight : ChevronDown" class="h-4 w-4" />
                    </div>
                </CardHeader>
                <CardContent v-show="!collapsedSections.prediction" class="flex flex-col gap-2 px-3 py-2">
                    <div class="space-y-1">
                        <Label for="prediction-years">预测年限:</Label>
                        <Input id="prediction-years" type="number" v-model="formStringValues.prediction_years" min="3"
                            max="15" step="1" class="mt-1 w-full" placeholder="范围: 3-15 年" />
                    </div>
                    <div class="space-y-1">
                        <Label for="cagr-decay-rate">CAGR年衰减率 (0-1):</Label>
                        <Input id="cagr-decay-rate" type="number" v-model="formStringValues.cagr_decay_rate" step="0.01"
                            min="0" max="1" placeholder="例如: 0.1" class="mt-1 w-full" />
                    </div>
                </CardContent>
            </Card>

            <Card class="bg-background py-3 text-card-foreground flex flex-col gap-2 rounded-xl border">
                <CardHeader class="px-3 py-2 cursor-pointer"
                    @click="collapsedSections.financial = !collapsedSections.financial">
                    <div class="flex items-center justify-between">
                        <CardTitle class="text-base">财务假设</CardTitle>
                        <component :is="collapsedSections.financial ? ChevronRight : ChevronDown" class="h-4 w-4" />
                    </div>
                </CardHeader>
                <CardContent v-show="!collapsedSections.financial" class="flex flex-col gap-2 px-3 py-2">
                    <div v-for="section in financialAssumptionSections" :key="section.id" class="space-y-3 py-2">
                        <h6 class="text-base font-medium text-foreground mb-2">{{ section.title }}</h6>
                        <div class="space-y-1">
                            <Label :for="`${section.id}-forecast-mode`"
                                class="block text-xs font-medium text-muted-foreground">预测模式:</Label>
                            <div>
                                <Select :model-value="getForecastMode(section)"
                                    @update:model-value="(value) => setForecastMode(section, value as 'historical_median' | 'transition_to_target')">
                                    <SelectTrigger :id="`${section.id}-forecast-mode`" class="w-full">
                                        <SelectValue placeholder="选择预测模式" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="historical_median">使用历史中位数</SelectItem>
                                        <SelectItem value="transition_to_target">过渡到目标值</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        <div v-if="params[section.modeKey as keyof DcfFormParameters] === 'transition_to_target'"
                            class="space-y-3 mt-2">
                            <div v-for="field in section.fields" :key="field.id" class="space-y-1">
                                <Label :for="field.id" class="block text-xs font-medium text-muted-foreground">{{
                                    field.label }}:</Label>
                                <Input :id="field.id" type="text"
                                    v-model="formStringValues[field.modelKey as keyof StringifiedNumericParams]"
                                    :step="field.step || '0.01'" :min="field.min" :max="field.max"
                                    class="mt-1 w-full" />
                            </div>
                            <div class="space-y-1">
                                <Label :for="`${section.id}-transition-years`"
                                    class="block text-xs font-medium text-muted-foreground">过渡年数:</Label>
                                <Input :id="`${section.id}-transition-years`" type="text"
                                    v-model="formStringValues[section.transitionYearsKey as keyof StringifiedNumericParams]"
                                    min="1" class="mt-1 w-full" />
                            </div>
                        </div>
                    </div>
                    <div class="space-y-2 py-2">
                        <h6 class="text-base font-medium text-foreground mb-2">税率</h6>
                        <Label for="target-effective-tax-rate"
                            class="block text-xs font-medium text-muted-foreground">有效所得税率 (%):</Label>
                        <Input id="target-effective-tax-rate" type="text"
                            v-model="formStringValues.target_effective_tax_rate" step="0.01" min="0" max="100"
                            class="mt-1 w-full" />
                    </div>
                </CardContent>
            </Card>

            <Card class="bg-background py-3 text-card-foreground flex flex-col gap-2 rounded-xl border">
                <CardHeader class="px-3 py-2 cursor-pointer" @click="collapsedSections.wacc = !collapsedSections.wacc">
                    <div class="flex items-center justify-between">
                        <CardTitle class="text-base">WACC假设</CardTitle>
                        <component :is="collapsedSections.wacc ? ChevronRight : ChevronDown" class="h-4 w-4" />
                    </div>
                </CardHeader>
                <CardContent v-show="!collapsedSections.wacc" class="flex flex-col gap-2 px-3 py-2">
                    <div class="space-y-2">
                        <Label for="wacc-weight-mode"
                            class="block text-sm font-medium text-foreground">WACC权重模式:</Label>
                        <Select v-model="params.wacc_weight_mode">
                            <SelectTrigger id="wacc-weight-mode" class="mt-1">
                                <SelectValue placeholder="选择WACC权重模式" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="market">最新市场价值计算权重</SelectItem>
                                <SelectItem value="target">目标债务比例</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div v-if="params.wacc_weight_mode === 'target'" class="space-y-2">
                        <Label for="target-debt-ratio" class="block text-sm font-medium text-foreground">目标债务比例 D/(D+E)
                            (%):</Label>
                        <Input id="target-debt-ratio" type="text" v-model="formStringValues.target_debt_ratio"
                            step="0.01" min="0" max="100" class="mt-1 w-full" />
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3">
                        <div class="space-y-1">
                            <Label for="cost-of-debt" class="block text-xs font-medium text-muted-foreground">税前债务成本
                                (%):</Label>
                            <Input id="cost-of-debt" type="text" v-model="formStringValues.cost_of_debt" step="0.01"
                                min="0" class="mt-1 w-full" />
                        </div>
                        <div class="space-y-1">
                            <Label for="risk-free-rate" class="block text-xs font-medium text-muted-foreground">无风险利率
                                (%):</Label>
                            <Input id="risk-free-rate" type="text" v-model="formStringValues.risk_free_rate" step="0.01"
                                min="0" class="mt-1 w-full" />
                        </div>
                        <div class="space-y-1">
                            <Label for="beta" class="block text-xs font-medium text-muted-foreground">贝塔系数:</Label>
                            <Input id="beta" type="text" v-model="formStringValues.beta" step="0.01"
                                class="mt-1 w-full" />
                        </div>
                        <div class="space-y-1">
                            <Label for="market-risk-premium"
                                class="block text-xs font-medium text-muted-foreground">市场风险溢价
                                (%):</Label>
                            <Input id="market-risk-premium" type="text" v-model="formStringValues.market_risk_premium"
                                step="0.01" min="0" class="mt-1 w-full" />
                        </div>
                        <div class="space-y-1">
                            <Label for="size-premium" class="block text-xs font-medium text-muted-foreground">规模溢价
                                (%):</Label>
                            <Input id="size-premium" type="text" v-model="formStringValues.size_premium" step="0.01"
                                class="mt-1 w-full" />
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card class="bg-background py-3 text-card-foreground flex flex-col gap-2 rounded-xl border">
                <CardHeader class="px-3 py-2 cursor-pointer"
                    @click="collapsedSections.terminal = !collapsedSections.terminal">
                    <div class="flex items-center justify-between">
                        <CardTitle class="text-base">终值计算假设</CardTitle>
                        <component :is="collapsedSections.terminal ? ChevronRight : ChevronDown" class="h-4 w-4" />
                    </div>
                </CardHeader>
                <CardContent v-show="!collapsedSections.terminal" class="flex flex-col gap-2 px-3 py-2">
                    <div class="space-y-2">
                        <Label for="terminal-value-method"
                            class="block text-sm font-medium text-foreground">终值计算方法:</Label>
                        <Select v-model="params.terminal_value_method">
                            <SelectTrigger id="terminal-value-method" class="mt-1">
                                <SelectValue placeholder="选择终值计算方法" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="perpetual_growth">永续增长率法</SelectItem>
                                <SelectItem value="exit_multiple">退出乘数法</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div v-if="params.terminal_value_method === 'exit_multiple'" class="space-y-2">
                        <Label for="exit-multiple" class="block text-sm font-medium text-foreground">退出乘数
                            (基于EBITDA):</Label>
                        <Input id="exit-multiple" type="number" v-model="formStringValues.exit_multiple" step="0.1"
                            min="0" class="mt-1 w-full" />
                    </div>
                    <div v-if="params.terminal_value_method === 'perpetual_growth'" class="space-y-2">
                        <Label for="terminal-growth-rate-conditional"
                            class="block text-sm font-medium text-foreground">永续增长率 (%):</Label>
                        <Input id="terminal-growth-rate-conditional" type="number"
                            v-model="formStringValues.terminal_growth_rate" step="0.1" min="0" max="10"
                            class="mt-1 w-full" />
                    </div>
                </CardContent>
            </Card>

            <Card class="bg-background py-3 text-card-foreground flex flex-col gap-2 rounded-xl border">
                <CardHeader class="px-3 py-2 cursor-pointer" @click="collapsedSections.llm = !collapsedSections.llm">
                    <div class="flex items-center justify-between">
                        <CardTitle class="text-base">LLM分析总结</CardTitle>
                        <component :is="collapsedSections.llm ? ChevronRight : ChevronDown" class="h-4 w-4" />
                    </div>
                </CardHeader>
                <CardContent v-show="!collapsedSections.llm" class="flex flex-col gap-2 px-3 py-2">
                    <div class="flex items-center space-x-2">
                        <input type="checkbox" id="request-llm-summary" v-model="params.request_llm_summary"
                            class="h-4 w-4 rounded border-input text-primary focus:ring-primary" />
                        <Label for="request-llm-summary" class="text-sm font-medium text-foreground">启用LLM分析</Label>
                    </div>
                    <div v-if="params.request_llm_summary" class="space-y-4 mt-4">
                        <div class="space-y-2">
                            <Label for="llm-provider" class="block text-sm font-medium text-foreground">LLM提供商:</Label>
                            <Select v-model="params.llm_provider">
                                <SelectTrigger id="llm-provider" class="mt-1">
                                    <SelectValue placeholder="选择LLM提供商" />
                                </SelectTrigger>
                                <SelectContent position="popper">
                                    <SelectItem value="default">后端默认</SelectItem>
                                    <SelectItem value="deepseek">DeepSeek</SelectItem>
                                    <SelectItem value="custom_openai">自定义OpenAI兼容模型</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div class="space-y-2" v-if="params.llm_provider === 'custom_openai'">
                            <Label for="llm-api-base-url" class="block text-sm font-medium text-foreground">LLM API Base
                                URL:</Label>
                            <Input type="text" id="llm-api-base-url" v-model="params.llm_api_base_url"
                                class="mt-1 w-full" />
                        </div>
                        <div class="space-y-2">
                            <Label for="llm-model-id" class="block text-sm font-medium text-foreground">LLM模型ID:</Label>
                            <Input type="text" id="llm-model-id" v-model="params.llm_model_id" class="mt-1 w-full" />
                            <p class="mt-1 text-xs text-muted-foreground">例如: deepseek-chat, gpt-4-turbo 等。留空则使用提供商默认。
                            </p>
                        </div>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-x-4 gap-y-3">
                            <div class="space-y-1">
                                <Label for="llm-temperature"
                                    class="block text-xs font-medium text-muted-foreground">Temperature:</Label>
                                <Input id="llm-temperature" type="number" v-model="formStringValues.llm_temperature"
                                    step="0.1" min="0" max="2" class="mt-1 w-full" />
                            </div>
                            <div class="space-y-1">
                                <Label for="llm-top-p" class="block text-xs font-medium text-muted-foreground">Top P
                                    (0-1):</Label>
                                <Input id="llm-top-p" type="number" v-model="formStringValues.llm_top_p" step="0.01"
                                    min="0" max="1" class="mt-1 w-full" />
                            </div>
                            <div class="space-y-1">
                                <Label for="llm-max-tokens" class="block text-xs font-medium text-muted-foreground">Max
                                    Tokens:</Label>
                                <Input id="llm-max-tokens" type="number" v-model="formStringValues.llm_max_tokens"
                                    min="1" step="1" class="mt-1 w-full" />
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card class="bg-background py-3 text-card-foreground flex flex-col gap-2 rounded-xl border">
                <CardHeader class="px-3 py-2 cursor-pointer"
                    @click="collapsedSections.sensitivity = !collapsedSections.sensitivity">
                    <div class="flex items-center justify-between">
                        <CardTitle class="text-base">敏感性分析配置</CardTitle>
                        <component :is="collapsedSections.sensitivity ? ChevronRight : ChevronDown" class="h-4 w-4" />
                    </div>
                </CardHeader>
                <CardContent v-show="!collapsedSections.sensitivity" class="flex flex-col gap-2 px-3 py-2">
                    <div class="flex items-center space-x-2">
                        <input type="checkbox" id="enable-sensitivity-analysis"
                            v-model="params.enable_sensitivity_analysis"
                            class="h-4 w-4 rounded border-input text-primary focus:ring-primary" />
                        <Label for="enable-sensitivity-analysis"
                            class="text-sm font-medium text-foreground">启用敏感性分析</Label>
                    </div>

                    <div v-if="params.enable_sensitivity_analysis" class="space-y-4 mt-2">
                        <div class="space-y-3 py-2">
                            <h6 class="text-base font-medium text-foreground mb-2">WACC敏感性</h6>
                            <div class="space-y-1">
                                <Label for="sensitivity-wacc-step"
                                    class="block text-xs font-medium text-muted-foreground">WACC变动步长 (%):</Label>
                                <Input id="sensitivity-wacc-step" type="number"
                                    v-model="formStringValues.sensitivity_wacc_step" step="0.01" class="mt-1 w-full" />
                            </div>
                            <div class="space-y-1">
                                <Label for="sensitivity-wacc-points"
                                    class="block text-xs font-medium text-muted-foreground">WACC分析点数:</Label>
                                <Input id="sensitivity-wacc-points" type="number"
                                    v-model="formStringValues.sensitivity_wacc_points" min="1" max="11" step="2"
                                    class="mt-1 w-full" />
                            </div>
                        </div>

                        <div class="space-y-3 py-2">
                            <h6 class="text-base font-medium text-foreground mb-2">退出乘数 (Exit Multiple) 敏感性</h6>
                            <div class="space-y-1">
                                <Label for="sensitivity-exit-multiple-step"
                                    class="block text-xs font-medium text-muted-foreground">退出乘数 变动步长 (绝对值):</Label>
                                <Input id="sensitivity-exit-multiple-step" type="number"
                                    v-model="formStringValues.sensitivity_exit_multiple_step" step="0.1"
                                    class="mt-1 w-full" />
                            </div>
                            <div class="space-y-1">
                                <Label for="sensitivity-exit-multiple-points"
                                    class="block text-xs font-medium text-muted-foreground">退出乘数 分析点数:</Label>
                                <Input id="sensitivity-exit-multiple-points" type="number"
                                    v-model="formStringValues.sensitivity_exit_multiple_points" min="1" max="11"
                                    step="2" class="mt-1 w-full" />
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>


        </form>
    </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue';
import type { ApiSensitivityAxis } from '../../../shared-types/src';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ChevronDown, ChevronRight } from 'lucide-vue-next';

import type { ApiDcfValuationRequest as ValuationRequestPayload } from '../../../shared-types/src';

// Define a more specific type for the section iteration to help TypeScript
interface FormSectionField {
    id: string;
    modelKey: keyof DcfFormParameters; // Will point to DcfFormParameters for type safety
    label: string;
    step?: string | number;
    min?: number;
    max?: number;
}
interface FormSection {
    id: string;
    title: string;
    modeKey: keyof DcfFormParameters;
    transitionYearsKey: keyof DcfFormParameters; // Will point to DcfFormParameters
    fields: FormSectionField[];
}

// For fields that will be bound as strings from Inputs and converted to numbers
type StringifiedNumericParams = {
    [K in keyof DcfFormParameters as DcfFormParameters[K] extends number | undefined ? K : never]?: string | undefined;
};


export interface DcfFormParameters {
    stock_code: string;
    valuation_date?: string | undefined; // Stays string
    terminal_growth_rate: number | undefined;
    prediction_years: number | undefined;
    cagr_decay_rate?: number | undefined;
    op_margin_forecast_mode: 'historical_median' | 'transition_to_target'; // Stays string (select)
    target_operating_margin?: number | undefined;
    op_margin_transition_years?: number | undefined;
    sga_rd_ratio_forecast_mode: 'historical_median' | 'transition_to_target'; // Stays string (select)
    target_sga_rd_to_revenue_ratio?: number | undefined;
    sga_rd_transition_years?: number | undefined;
    da_ratio_forecast_mode: 'historical_median' | 'transition_to_target'; // Stays string (select)
    target_da_to_revenue_ratio?: number | undefined;
    da_ratio_transition_years?: number | undefined;
    capex_ratio_forecast_mode: 'historical_median' | 'transition_to_target'; // Stays string (select)
    target_capex_to_revenue_ratio?: number | undefined;
    capex_ratio_transition_years?: number | undefined;
    nwc_days_forecast_mode: 'historical_median' | 'transition_to_target'; // Stays string (select)
    target_accounts_receivable_days?: number | undefined;
    target_inventory_days?: number | undefined;
    target_accounts_payable_days?: number | undefined;
    nwc_days_transition_years?: number | undefined;
    other_nwc_ratio_forecast_mode: 'historical_median' | 'transition_to_target'; // Stays string (select)
    target_other_current_assets_to_revenue_ratio?: number | undefined;
    target_other_current_liabilities_to_revenue_ratio?: number | undefined;
    other_nwc_ratio_transition_years?: number | undefined;
    target_effective_tax_rate?: number | undefined;
    wacc_weight_mode: 'target' | 'market'; // Stays string (select)
    target_debt_ratio?: number | undefined;
    cost_of_debt?: number | undefined;
    risk_free_rate?: number | undefined;
    beta?: number | undefined;
    market_risk_premium?: number | undefined;
    size_premium?: number | undefined;
    terminal_value_method: 'exit_multiple' | 'perpetual_growth'; // Stays string (select)
    exit_multiple?: number | undefined;
    request_llm_summary: boolean; // Stays boolean (checkbox)
    llm_provider?: 'deepseek' | 'custom_openai' | 'default' | undefined; // Stays string (select), 'default' for backend default
    llm_model_id?: string | undefined; // Stays string
    llm_api_base_url?: string | undefined; // Stays string
    llm_temperature?: number | undefined;
    llm_top_p?: number | undefined;
    llm_max_tokens?: number | undefined;
    // sensitivity_analysis is constructed on submit, not part of direct form params
    enable_sensitivity_analysis: boolean; // Stays boolean (checkbox)
    sensitivity_wacc_step?: number | undefined;
    sensitivity_wacc_points?: number | undefined;
    sensitivity_exit_multiple_step?: number | undefined;
    sensitivity_exit_multiple_points?: number | undefined;
}

const props = defineProps<{
    isLoading: boolean;
    stockCode: string;
    valuationDate: string;
}>();



// 添加折叠状态
const collapsedSections = reactive({
    prediction: false,
    financial: false,
    wacc: false,
    terminal: false,
    llm: false,
    sensitivity: false
});

// Main reactive object for form state, including non-numeric strings
const params = reactive<DcfFormParameters>({
    stock_code: props.stockCode,
    valuation_date: props.valuationDate,
    op_margin_forecast_mode: 'historical_median',
    sga_rd_ratio_forecast_mode: 'historical_median',
    da_ratio_forecast_mode: 'historical_median',
    capex_ratio_forecast_mode: 'historical_median',
    nwc_days_forecast_mode: 'historical_median',
    other_nwc_ratio_forecast_mode: 'historical_median',
    wacc_weight_mode: 'market',
    terminal_value_method: 'exit_multiple',
    request_llm_summary: false,
    llm_provider: 'default', // Default to 'default' for backend default
    enable_sensitivity_analysis: true,
    // Numeric fields that will be handled by formStringValues initially
    terminal_growth_rate: 2.5,
    prediction_years: 5,
    cagr_decay_rate: 0.1,
    target_operating_margin: 15,
    op_margin_transition_years: 5,
    target_sga_rd_to_revenue_ratio: 20,
    sga_rd_transition_years: 5,
    target_da_to_revenue_ratio: 5,
    da_ratio_transition_years: 5,
    target_capex_to_revenue_ratio: 7,
    capex_ratio_transition_years: 5,
    target_accounts_receivable_days: 30,
    target_inventory_days: 60,
    target_accounts_payable_days: 45,
    nwc_days_transition_years: 5,
    target_other_current_assets_to_revenue_ratio: 5,
    target_other_current_liabilities_to_revenue_ratio: 3,
    other_nwc_ratio_transition_years: 5,
    target_effective_tax_rate: 25,
    target_debt_ratio: 45,
    cost_of_debt: 5,
    risk_free_rate: 3,
    beta: 1.0,
    market_risk_premium: 6,
    size_premium: undefined, // Keep as undefined if truly optional
    exit_multiple: 7.0,
    llm_temperature: 0.7,
    llm_top_p: 1.0,
    llm_max_tokens: 2048,
    sensitivity_wacc_step: 0.5,
    sensitivity_wacc_points: 3,
    sensitivity_exit_multiple_step: 0.5,
    sensitivity_exit_multiple_points: 3,
    // Non-string/non-select fields that are directly part of params
    llm_model_id: undefined,
    llm_api_base_url: undefined,
});

// Reactive object to hold string representations of numeric inputs
const formStringValues = reactive<StringifiedNumericParams>({
    prediction_years: String(params.prediction_years),
    cagr_decay_rate: params.cagr_decay_rate !== undefined ? String(params.cagr_decay_rate) : '',
    target_operating_margin: params.target_operating_margin !== undefined ? String(params.target_operating_margin) : '',
    op_margin_transition_years: params.op_margin_transition_years !== undefined ? String(params.op_margin_transition_years) : '',
    target_sga_rd_to_revenue_ratio: params.target_sga_rd_to_revenue_ratio !== undefined ? String(params.target_sga_rd_to_revenue_ratio) : '',
    sga_rd_transition_years: params.sga_rd_transition_years !== undefined ? String(params.sga_rd_transition_years) : '',
    target_da_to_revenue_ratio: params.target_da_to_revenue_ratio !== undefined ? String(params.target_da_to_revenue_ratio) : '',
    da_ratio_transition_years: params.da_ratio_transition_years !== undefined ? String(params.da_ratio_transition_years) : '',
    target_capex_to_revenue_ratio: params.target_capex_to_revenue_ratio !== undefined ? String(params.target_capex_to_revenue_ratio) : '',
    capex_ratio_transition_years: params.capex_ratio_transition_years !== undefined ? String(params.capex_ratio_transition_years) : '',
    target_accounts_receivable_days: params.target_accounts_receivable_days !== undefined ? String(params.target_accounts_receivable_days) : '',
    target_inventory_days: params.target_inventory_days !== undefined ? String(params.target_inventory_days) : '',
    target_accounts_payable_days: params.target_accounts_payable_days !== undefined ? String(params.target_accounts_payable_days) : '',
    nwc_days_transition_years: params.nwc_days_transition_years !== undefined ? String(params.nwc_days_transition_years) : '',
    target_other_current_assets_to_revenue_ratio: params.target_other_current_assets_to_revenue_ratio !== undefined ? String(params.target_other_current_assets_to_revenue_ratio) : '',
    target_other_current_liabilities_to_revenue_ratio: params.target_other_current_liabilities_to_revenue_ratio !== undefined ? String(params.target_other_current_liabilities_to_revenue_ratio) : '',
    other_nwc_ratio_transition_years: params.other_nwc_ratio_transition_years !== undefined ? String(params.other_nwc_ratio_transition_years) : '',
    target_effective_tax_rate: params.target_effective_tax_rate !== undefined ? String(params.target_effective_tax_rate) : '',
    target_debt_ratio: params.target_debt_ratio !== undefined ? String(params.target_debt_ratio) : '',
    cost_of_debt: params.cost_of_debt !== undefined ? String(params.cost_of_debt) : '',
    risk_free_rate: params.risk_free_rate !== undefined ? String(params.risk_free_rate) : '',
    beta: params.beta !== undefined ? String(params.beta) : '',
    market_risk_premium: params.market_risk_premium !== undefined ? String(params.market_risk_premium) : '',
    size_premium: params.size_premium !== undefined ? String(params.size_premium) : '',
    terminal_growth_rate: params.terminal_growth_rate !== undefined ? String(params.terminal_growth_rate) : '',
    exit_multiple: params.exit_multiple !== undefined ? String(params.exit_multiple) : '',
    llm_temperature: params.llm_temperature !== undefined ? String(params.llm_temperature) : '',
    llm_top_p: params.llm_top_p !== undefined ? String(params.llm_top_p) : '',
    llm_max_tokens: params.llm_max_tokens !== undefined ? String(params.llm_max_tokens) : '',
    sensitivity_wacc_step: params.sensitivity_wacc_step !== undefined ? String(params.sensitivity_wacc_step) : '',
    sensitivity_wacc_points: params.sensitivity_wacc_points !== undefined ? String(params.sensitivity_wacc_points) : '',
    sensitivity_exit_multiple_step: params.sensitivity_exit_multiple_step !== undefined ? String(params.sensitivity_exit_multiple_step) : '',
    sensitivity_exit_multiple_points: params.sensitivity_exit_multiple_points !== undefined ? String(params.sensitivity_exit_multiple_points) : '',
});


const emit = defineEmits<{
    (e: 'submit-valuation', payload: ValuationRequestPayload): void;
    (e: 'validation-error', message: string): void;
}>();

const simpleAxisParamDisplayNames: Record<string, string> = {
    "wacc": "WACC",
    "exit_multiple": "退出乘数",
    "terminal_growth_rate": "永续增长率"
};

// 辅助函数，用于获取财务假设部分的Select组件的值
const getForecastMode = (section: FormSection) => {
    if (section.modeKey === 'op_margin_forecast_mode') {
        return params.op_margin_forecast_mode;
    } else if (section.modeKey === 'sga_rd_ratio_forecast_mode') {
        return params.sga_rd_ratio_forecast_mode;
    } else if (section.modeKey === 'da_ratio_forecast_mode') {
        return params.da_ratio_forecast_mode;
    } else if (section.modeKey === 'capex_ratio_forecast_mode') {
        return params.capex_ratio_forecast_mode;
    } else if (section.modeKey === 'nwc_days_forecast_mode') {
        return params.nwc_days_forecast_mode;
    } else if (section.modeKey === 'other_nwc_ratio_forecast_mode') {
        return params.other_nwc_ratio_forecast_mode;
    }
    return 'historical_median'; // 默认值
};

// 辅助函数，用于设置财务假设部分的Select组件的值
const setForecastMode = (section: FormSection, value: 'historical_median' | 'transition_to_target') => {
    if (section.modeKey === 'op_margin_forecast_mode') {
        params.op_margin_forecast_mode = value;
    } else if (section.modeKey === 'sga_rd_ratio_forecast_mode') {
        params.sga_rd_ratio_forecast_mode = value;
    } else if (section.modeKey === 'da_ratio_forecast_mode') {
        params.da_ratio_forecast_mode = value;
    } else if (section.modeKey === 'capex_ratio_forecast_mode') {
        params.capex_ratio_forecast_mode = value;
    } else if (section.modeKey === 'nwc_days_forecast_mode') {
        params.nwc_days_forecast_mode = value;
    } else if (section.modeKey === 'other_nwc_ratio_forecast_mode') {
        params.other_nwc_ratio_forecast_mode = value;
    }
};





const financialAssumptionSections: FormSection[] = [
    { id: 'op-margin', title: '营业利润率预测', modeKey: 'op_margin_forecast_mode', transitionYearsKey: 'op_margin_transition_years', fields: [{ id: 'target-operating-margin', modelKey: 'target_operating_margin', label: '目标营业利润率 (%)' }] },
    { id: 'sga-rd-ratio', title: 'SGA & RD 费用率预测', modeKey: 'sga_rd_ratio_forecast_mode', transitionYearsKey: 'sga_rd_transition_years', fields: [{ id: 'target-sga-rd-ratio', modelKey: 'target_sga_rd_to_revenue_ratio', label: '目标SGA & RD占收入比 (%)' }] },
    { id: 'da-ratio', title: 'D&A 占收入比预测', modeKey: 'da_ratio_forecast_mode', transitionYearsKey: 'da_ratio_transition_years', fields: [{ id: 'target-da-ratio', modelKey: 'target_da_to_revenue_ratio', label: '目标D&A占收入比 (%)' }] },
    { id: 'capex-ratio', title: 'Capex 占收入比预测', modeKey: 'capex_ratio_forecast_mode', transitionYearsKey: 'capex_ratio_transition_years', fields: [{ id: 'target-capex-ratio', modelKey: 'target_capex_to_revenue_ratio', label: '目标Capex占收入比 (%)' }] },
    {
        id: 'nwc-days', title: 'NWC 周转天数预测', modeKey: 'nwc_days_forecast_mode', transitionYearsKey: 'nwc_days_transition_years', fields: [
            { id: 'target-ar-days', modelKey: 'target_accounts_receivable_days', label: '目标应收账款周转天数 (DSO)', min: 0 },
            { id: 'target-inv-days', modelKey: 'target_inventory_days', label: '目标存货周转天数 (DIO)', min: 0 },
            { id: 'target-ap-days', modelKey: 'target_accounts_payable_days', label: '目标应付账款周转天数 (DPO)', min: 0 }
        ]
    },
    {
        id: 'other-nwc-ratio', title: '其他 NWC 比率预测', modeKey: 'other_nwc_ratio_forecast_mode', transitionYearsKey: 'other_nwc_ratio_transition_years', fields: [
            { id: 'target-other-ca-ratio', modelKey: 'target_other_current_assets_to_revenue_ratio', label: '目标其他流动资产占收入比 (%)' },
            { id: 'target-other-cl-ratio', modelKey: 'target_other_current_liabilities_to_revenue_ratio', label: '目标其他流动负债占收入比 (%)' }
        ]
    },
];



// 暴露给父组件调用
const submitValuationRequest = () => {
    // 确保使用最新的股票代码
    console.log('DcfParametersForm: submitValuationRequest被调用，当前股票代码:', params.stock_code);

    if (!params.stock_code) {
        emit('validation-error', '股票代码为必填项！');
        return;
    }

    const finalParams: DcfFormParameters = { ...params };

    // Convert string values from formStringValues back to numbers or undefined
    for (const key in formStringValues) {
        const K = key as keyof StringifiedNumericParams;
        const stringVal = formStringValues[K];
        if (stringVal === '' || stringVal === null || stringVal === undefined) {
            finalParams[K] = undefined;
        } else {
            const numVal = parseFloat(stringVal);
            finalParams[K] = isNaN(numVal) ? undefined : numVal;
        }
    }

    // Handle llm_provider being 'default' for backend default
    if (finalParams.llm_provider === 'default') {
        finalParams.llm_provider = undefined;
    }

    // Construct the API payload using the now correctly typed finalParams
    const apiPayload: ValuationRequestPayload = {
        stock_code: finalParams.stock_code,
        valuation_date: finalParams.valuation_date || undefined,
        prediction_years: finalParams.prediction_years,
        cagr_decay_rate: finalParams.cagr_decay_rate,
        op_margin_forecast_mode: finalParams.op_margin_forecast_mode,
        op_margin_transition_years: finalParams.op_margin_transition_years,
        sga_rd_ratio_forecast_mode: finalParams.sga_rd_ratio_forecast_mode,
        sga_rd_transition_years: finalParams.sga_rd_transition_years,
        da_ratio_forecast_mode: finalParams.da_ratio_forecast_mode,
        da_ratio_transition_years: finalParams.da_ratio_transition_years,
        capex_ratio_forecast_mode: finalParams.capex_ratio_forecast_mode,
        capex_ratio_transition_years: finalParams.capex_ratio_transition_years,
        nwc_days_forecast_mode: finalParams.nwc_days_forecast_mode,
        nwc_days_transition_years: finalParams.nwc_days_transition_years,
        other_nwc_ratio_forecast_mode: finalParams.other_nwc_ratio_forecast_mode,
        other_nwc_ratio_transition_years: finalParams.other_nwc_ratio_transition_years,
        target_operating_margin: typeof finalParams.target_operating_margin === 'number' ? finalParams.target_operating_margin / 100 : undefined,
        target_sga_rd_to_revenue_ratio: typeof finalParams.target_sga_rd_to_revenue_ratio === 'number' ? finalParams.target_sga_rd_to_revenue_ratio / 100 : undefined,
        target_da_to_revenue_ratio: typeof finalParams.target_da_to_revenue_ratio === 'number' ? finalParams.target_da_to_revenue_ratio / 100 : undefined,
        target_capex_to_revenue_ratio: typeof finalParams.target_capex_to_revenue_ratio === 'number' ? finalParams.target_capex_to_revenue_ratio / 100 : undefined,
        target_other_current_assets_to_revenue_ratio: typeof finalParams.target_other_current_assets_to_revenue_ratio === 'number' ? finalParams.target_other_current_assets_to_revenue_ratio / 100 : undefined,
        target_other_current_liabilities_to_revenue_ratio: typeof finalParams.target_other_current_liabilities_to_revenue_ratio === 'number' ? finalParams.target_other_current_liabilities_to_revenue_ratio / 100 : undefined,
        target_effective_tax_rate: typeof finalParams.target_effective_tax_rate === 'number' ? finalParams.target_effective_tax_rate / 100 : undefined,
        target_accounts_receivable_days: finalParams.target_accounts_receivable_days,
        target_inventory_days: finalParams.target_inventory_days,
        target_accounts_payable_days: finalParams.target_accounts_payable_days,
        wacc_weight_mode: finalParams.wacc_weight_mode,
        target_debt_ratio: typeof finalParams.target_debt_ratio === 'number' ? finalParams.target_debt_ratio / 100 : undefined,
        cost_of_debt: typeof finalParams.cost_of_debt === 'number' ? finalParams.cost_of_debt / 100 : undefined,
        risk_free_rate: typeof finalParams.risk_free_rate === 'number' ? finalParams.risk_free_rate / 100 : undefined,
        market_risk_premium: typeof finalParams.market_risk_premium === 'number' ? finalParams.market_risk_premium / 100 : undefined,
        beta: finalParams.beta,
        size_premium: typeof finalParams.size_premium === 'number' ? finalParams.size_premium / 100 : undefined,
        terminal_value_method: finalParams.terminal_value_method,
        terminal_growth_rate: typeof finalParams.terminal_growth_rate === 'number' ? finalParams.terminal_growth_rate / 100 : undefined,
        exit_multiple: finalParams.exit_multiple,
        request_llm_summary: finalParams.request_llm_summary,
        llm_provider: finalParams.llm_provider,
        llm_model_id: finalParams.llm_model_id,
        llm_api_base_url: finalParams.llm_api_base_url,
        llm_temperature: finalParams.llm_temperature,
        llm_top_p: finalParams.llm_top_p,
        llm_max_tokens: finalParams.llm_max_tokens,
        // Sensitivity analysis part
        sensitivity_analysis: undefined // Initialize
    };

    if (finalParams.enable_sensitivity_analysis) {
        const maxSensitivityPoints = 11;
        const waccStepForApi = typeof finalParams.sensitivity_wacc_step === 'number' ? finalParams.sensitivity_wacc_step / 100 : undefined;

        console.log('敏感性分析参数:', {
            enable: finalParams.enable_sensitivity_analysis,
            wacc_step: finalParams.sensitivity_wacc_step,
            wacc_step_for_api: waccStepForApi,
            wacc_points: finalParams.sensitivity_wacc_points,
            exit_multiple_step: finalParams.sensitivity_exit_multiple_step,
            exit_multiple_points: finalParams.sensitivity_exit_multiple_points,
            terminal_value_method: finalParams.terminal_value_method
        });

        if (finalParams.sensitivity_wacc_points && finalParams.sensitivity_wacc_points > 1 && (waccStepForApi === 0 || waccStepForApi === null || waccStepForApi === undefined)) {
            emit('validation-error', `当 ${simpleAxisParamDisplayNames['wacc']} 的分析点数大于1时，其变动步长不能为空且不能为0。`);
            return;
        }
        if (finalParams.sensitivity_wacc_points && finalParams.sensitivity_wacc_points > maxSensitivityPoints) {
            emit('validation-error', `${simpleAxisParamDisplayNames['wacc']} 的分析点数不能超过 ${maxSensitivityPoints}。`);
            return;
        }
        if (finalParams.sensitivity_exit_multiple_points && finalParams.sensitivity_exit_multiple_points > 1 && (finalParams.sensitivity_exit_multiple_step === 0 || finalParams.sensitivity_exit_multiple_step === null || finalParams.sensitivity_exit_multiple_step === undefined)) {
            emit('validation-error', `当 ${simpleAxisParamDisplayNames['exit_multiple']} 的分析点数大于1时，其变动步长不能为空且不能为0。`);
            return;
        }
        if (finalParams.sensitivity_exit_multiple_points && finalParams.sensitivity_exit_multiple_points > maxSensitivityPoints) {
            emit('validation-error', `${simpleAxisParamDisplayNames['exit_multiple']} 的分析点数不能超过 ${maxSensitivityPoints}。`);
            return;
        }

        const axis1: ApiSensitivityAxis = {
            parameter_name: 'wacc',
            step: waccStepForApi ?? 0,
            points: finalParams.sensitivity_wacc_points ?? 1,
            value_type: 'percentage', values: []
        };
        const axis2: ApiSensitivityAxis = {
            parameter_name: 'exit_multiple',
            step: finalParams.sensitivity_exit_multiple_step ?? 0,
            points: finalParams.sensitivity_exit_multiple_points ?? 1,
            value_type: 'absolute', values: []
        };
        if (finalParams.terminal_value_method === 'perpetual_growth') {
            axis2.parameter_name = 'terminal_growth_rate';
            const baseGrowthRate = typeof finalParams.terminal_growth_rate === 'number' ? finalParams.terminal_growth_rate / 100 : 0; // Already decimal
            axis2.step = baseGrowthRate ? baseGrowthRate * 0.1 : 0.0025;
            axis2.value_type = 'percentage';
        }

        if (axis1.points && axis1.points < 1) axis1.points = 1;
        if (axis1.points && axis1.points % 2 === 0) axis1.points += 1;
        if (axis2.points && axis2.points < 1) axis2.points = 1;
        if (axis2.points && axis2.points % 2 === 0) axis2.points += 1;

        apiPayload.sensitivity_analysis = {
            row_axis: axis1, column_axis: axis2,
            output_metrics: ['value_per_share', 'enterprise_value', 'equity_value', 'ev_ebitda', 'dcf_implied_diluted_pe', 'tv_ev_ratio']
        };

        console.log('构建的敏感性分析参数:', apiPayload.sensitivity_analysis);
    } else {
        console.log('敏感性分析未启用');
    }

    console.log('DcfParametersForm: 发出submit-valuation事件，payload:', apiPayload);
    emit('submit-valuation', apiPayload);
};

watch(() => props.stockCode, (newVal) => {
    console.log('DcfParametersForm: stockCode变化为:', newVal);
    params.stock_code = newVal;
}, { immediate: true });

watch(() => props.valuationDate, (newVal) => {
    console.log('DcfParametersForm: valuationDate变化为:', newVal);
    params.valuation_date = newVal;
}, { immediate: true });

watch(() => formStringValues.prediction_years, (newValStr) => {
    const numVal = parseInt(newValStr || '', 10);
    if (!isNaN(numVal) && numVal >= 1) {
        const newPredictionYears = numVal;
        params.op_margin_transition_years = newPredictionYears;
        formStringValues.op_margin_transition_years = String(newPredictionYears);
        params.sga_rd_transition_years = newPredictionYears;
        formStringValues.sga_rd_transition_years = String(newPredictionYears);
        params.da_ratio_transition_years = newPredictionYears;
        formStringValues.da_ratio_transition_years = String(newPredictionYears);
        params.capex_ratio_transition_years = newPredictionYears;
        formStringValues.capex_ratio_transition_years = String(newPredictionYears);
        params.nwc_days_transition_years = newPredictionYears;
        formStringValues.nwc_days_transition_years = String(newPredictionYears);
        params.other_nwc_ratio_transition_years = newPredictionYears;
        formStringValues.other_nwc_ratio_transition_years = String(newPredictionYears);
    }
}, { immediate: false });

// 监听LLM分析状态变化
watch(() => params.request_llm_summary, (newVal) => {
    console.log('LLM分析状态变化:', newVal);

    // 如果取消启用LLM分析，重置LLM相关参数
    if (!newVal) {
        params.llm_provider = 'default';
        params.llm_model_id = undefined;
        params.llm_api_base_url = undefined;
    }
});

// 监听敏感性分析状态变化
watch(() => params.enable_sensitivity_analysis, (newVal) => {
    console.log('敏感性分析状态变化:', newVal);
});

// 暴露方法给父组件
defineExpose({
    submitValuationRequest
});
</script>

<style scoped>
/* All previous scoped styles are removed. Styling is now handled by Tailwind CSS utility classes.
   Native form elements (input, select) have been styled with Tailwind classes to mimic shadcn/ui.
   Ideally, these would be replaced with actual shadcn-vue components (Input, Select, Checkbox, Label)
   once they are added to the project via `npx shadcn-vue add <component>` for full theme consistency.
*/
</style>
