<template>
    <div class="dcf-valuation-view">
        <h2>DCF估值</h2>
        <DcfParametersForm :is-loading="computedIsLoading" :initial-stock-code="initialStockCode"
            @submit-valuation="handleValuationRequest" @validation-error="handleFormValidationError" />
        <DcfResultsDisplay :valuation-data="computedValuationResult" :is-loading="computedIsLoading"
            :error="computedError" :has-calculated="hasCalculated" />
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import DcfParametersForm, { type DcfFormParameters } from '@/components/DcfParametersForm.vue';
import DcfResultsDisplay from '@/components/DcfResultsDisplay.vue';
import { valuationApi, ApiClientError } from '@/services/apiClient';
import type { ApiDcfValuationRequest, ApiDcfValuationResponse } from '@shared-types/index';
import { useValuationStore } from '@/stores/valuationStore';

const route = useRoute();
const valuationStore = useValuationStore();

// Computed properties to get state from the store
const computedValuationResult = computed(() => valuationStore.getValuationResult);
const computedIsLoading = computed(() => valuationStore.getIsLoading);
const computedError = computed(() => valuationStore.getError);

const hasCalculated = ref(false); // 标记是否已尝试计算, 暂时保留本地状态
const initialStockCode = ref<string | null>(null);

onMounted(() => {
    if (route.query.stockCode && typeof route.query.stockCode === 'string') {
        initialStockCode.value = route.query.stockCode;
    }
    // Optionally, clear store on mount if results should not persist across navigations
    // or if they should only be loaded if specific query params are present.
    // For now, we assume results might persist if user navigates away and back.
    // If results should always clear on mount unless triggered by query, add:
    // valuationStore.clearResult();
});

const handleValuationRequest = async (formParams: DcfFormParameters) => {
    hasCalculated.value = true;
    valuationStore.setLoading(true);
    // valuationStore.clearResult(); // setLoading(true) already clears error, and we want to clear previous result

    console.log('Requesting valuation with form params:', formParams);

    // 将表单参数转换为API请求参数
    const apiParams: ApiDcfValuationRequest = {
        stock_code: formParams.stock_code,
        valuation_date: formParams.valuation_date, // Already in YYYY-MM-DD string or null
        prediction_years: formParams.prediction_years,
        cagr_decay_rate: formParams.cagr_decay_rate, // Already a decimal or null

        // Financial forecast modes and transition years are direct pass-through
        op_margin_forecast_mode: formParams.op_margin_forecast_mode,
        op_margin_transition_years: formParams.op_margin_transition_years,
        sga_rd_ratio_forecast_mode: formParams.sga_rd_ratio_forecast_mode,
        sga_rd_transition_years: formParams.sga_rd_transition_years,
        da_ratio_forecast_mode: formParams.da_ratio_forecast_mode,
        da_ratio_transition_years: formParams.da_ratio_transition_years,
        capex_ratio_forecast_mode: formParams.capex_ratio_forecast_mode,
        capex_ratio_transition_years: formParams.capex_ratio_transition_years,
        nwc_days_forecast_mode: formParams.nwc_days_forecast_mode,
        nwc_days_transition_years: formParams.nwc_days_transition_years,
        other_nwc_ratio_forecast_mode: formParams.other_nwc_ratio_forecast_mode,
        other_nwc_ratio_transition_years: formParams.other_nwc_ratio_transition_years,

        // Target percentages are already converted to decimals in DcfParametersForm.vue
        target_operating_margin: formParams.target_operating_margin,
        target_sga_rd_to_revenue_ratio: formParams.target_sga_rd_to_revenue_ratio,
        target_da_to_revenue_ratio: formParams.target_da_to_revenue_ratio,
        target_capex_to_revenue_ratio: formParams.target_capex_to_revenue_ratio,
        target_other_current_assets_to_revenue_ratio: formParams.target_other_current_assets_to_revenue_ratio,
        target_other_current_liabilities_to_revenue_ratio: formParams.target_other_current_liabilities_to_revenue_ratio,
        target_effective_tax_rate: formParams.target_effective_tax_rate,

        // NWC days are direct pass-through
        target_accounts_receivable_days: formParams.target_accounts_receivable_days,
        target_inventory_days: formParams.target_inventory_days,
        target_accounts_payable_days: formParams.target_accounts_payable_days,

        // WACC parameters
        wacc_weight_mode: formParams.wacc_weight_mode,
        // Percentages already converted in DcfParametersForm.vue
        target_debt_ratio: formParams.target_debt_ratio,
        cost_of_debt: formParams.cost_of_debt,
        risk_free_rate: formParams.risk_free_rate,
        market_risk_premium: formParams.market_risk_premium,
        beta: formParams.beta, // Beta is not a percentage

        // Terminal value
        terminal_value_method: formParams.terminal_value_method,
        // terminal_growth_rate already converted in DcfParametersForm.vue
        terminal_growth_rate: formParams.terminal_growth_rate,
        exit_multiple: formParams.exit_multiple, // Not a percentage

        // LLM parameters are direct pass-through
        request_llm_summary: formParams.request_llm_summary,
        llm_provider: formParams.llm_provider,
        llm_model_id: formParams.llm_model_id,
        llm_api_base_url: formParams.llm_api_base_url,
        llm_temperature: formParams.llm_temperature,
        llm_top_p: formParams.llm_top_p,
        llm_max_tokens: formParams.llm_max_tokens,

        // Sensitivity analysis object is already constructed correctly in DcfParametersForm.vue
        sensitivity_analysis: formParams.sensitivity_analysis,
    };

    // Conditionally add size_premium (already converted to decimal in DcfParametersForm.vue if provided)
    if (formParams.size_premium !== null && formParams.size_premium !== undefined) {
        apiParams.size_premium = formParams.size_premium;
    }
    // If formParams.size_premium is null/undefined (meaning it wasn't a valid number in the form),
    // it will be omitted from apiParams, which is correct.

    try {
        const result = await valuationApi.performDcfValuation(apiParams);
        valuationStore.setValuationResult(result);

    } catch (e: any) {
        console.error('Error during valuation request:', e);
        let errorMessage: string;
        if (e instanceof ApiClientError) {
            errorMessage = `API错误 (状态 ${e.status}): ${e.message}. ${typeof e.data?.detail === 'string' ? e.data.detail : JSON.stringify(e.data?.detail)}`;
        } else {
            errorMessage = e.message || '进行估值计算时发生未知错误。';
        }
        valuationStore.setError(errorMessage);
        // valuationStore.setValuationResult(null); // setError action could also clear the result if desired
    }
    // isLoading is managed by the store actions setLoading and setValuationResult/setError
};

const handleFormValidationError = (errorMessage: string) => {
    valuationStore.setError(errorMessage);
    // Optionally, ensure loading is false if a validation error occurs before API call
    if (valuationStore.getIsLoading) {
        valuationStore.setLoading(false);
    }
    // Clear previous results if a new validation error occurs on a new submission attempt
    valuationStore.clearResult();
    hasCalculated.value = true; // Indicate an attempt was made, even if it failed validation
};
</script>

<style scoped>
.dcf-valuation-view {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}
</style>
