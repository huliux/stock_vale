<template>
    <div class="dcf-valuation-view">
        <h2>DCF估值</h2>
        <DcfParametersForm :is-loading="isLoading" :initial-stock-code="initialStockCode"
            @submit-valuation="handleValuationRequest" />
        <DcfResultsDisplay :valuation-data="valuationResult" :is-loading="isLoading" :error="error"
            :has-calculated="hasCalculated" />
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import DcfParametersForm, { type DcfFormParameters } from '@/components/DcfParametersForm.vue';
import DcfResultsDisplay from '@/components/DcfResultsDisplay.vue';
import { valuationApi, ApiClientError } from '@/services/apiClient'; // Use valuationApi
import type { ApiDcfValuationRequest, ApiDcfValuationResponse } from '@shared-types/index';

const route = useRoute();

const valuationResult = ref<ApiDcfValuationResponse | null>(null); // Use ApiDcfValuationResponse
const isLoading = ref(false);
const error = ref<string | null>(null);
const hasCalculated = ref(false); // 标记是否已尝试计算
const initialStockCode = ref<string | null>(null);

onMounted(() => {
    if (route.query.stockCode && typeof route.query.stockCode === 'string') {
        initialStockCode.value = route.query.stockCode;
    }
});

const handleValuationRequest = async (formParams: DcfFormParameters) => { // Parameter type updated
    isLoading.value = true;
    error.value = null;
    valuationResult.value = null;
    hasCalculated.value = true;

    console.log('Requesting valuation with form params:', formParams);

    // 将表单参数转换为API请求参数
    const apiParams: ApiDcfValuationRequest = {
        stock_code: formParams.stock_code,
        discount_rate: formParams.discount_rate !== null ? formParams.discount_rate / 100 : null,
        terminal_growth_rate: formParams.terminal_growth_rate !== null ? formParams.terminal_growth_rate / 100 : null,
        prediction_years: formParams.prediction_years !== null ? formParams.prediction_years : null,
    };

    // 移除值为 null 的可选参数，以便后端使用其默认值（如果Pydantic模型中定义了）
    // 或者让后端明确处理 null 值。当前后端模型将 Optional[float]=Field(None,...) 视为 None。
    // 所以发送 null 是可以的。

    try {
        const result = await valuationApi.performDcfValuation(apiParams);
        valuationResult.value = result;

    } catch (e: any) {
        console.error('Error during valuation request:', e);
        if (e instanceof ApiClientError) {
            error.value = `API错误 (状态 ${e.status}): ${e.message}. ${typeof e.data?.detail === 'string' ? e.data.detail : JSON.stringify(e.data?.detail)}`;
        } else {
            error.value = e.message || '进行估值计算时发生未知错误。';
        }
        valuationResult.value = null;
    } finally {
        isLoading.value = false;
    }
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
