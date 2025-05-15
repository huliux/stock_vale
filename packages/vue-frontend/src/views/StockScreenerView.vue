<template>
    <div class="stock-screener-view">
        <h2>股票筛选器</h2>
        <StockScreenerFilters @apply-filters="handleApplyFilters" @update-data="handleUpdateData" />
        <StockScreenerResultsTable :results="screenedStocks" :is-loading="isLoading" :error="error"
            :has-searched="hasSearched" @go-to-valuation="handleGoToValuation" />
    </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import StockScreenerFilters, { type ScreenerFilters } from '@/components/StockScreenerFilters.vue';
import StockScreenerResultsTable from '@/components/StockScreenerResultsTable.vue'; // Removed ScreenedStock import from here
import { screenerApi, ApiClientError } from '@/services/apiClient';
import type { ApiStockScreenerRequest, ApiScreenedStock } from '@shared-types/index'; // Added ApiScreenedStock import

const router = useRouter();

const screenedStocks = reactive<ApiScreenedStock[]>([]); // Use ApiScreenedStock type
const isLoading = ref(false);
const error = ref<string | null>(null);
const hasSearched = ref(false); // 标记是否执行过搜索

// 不再需要 allStocksData，数据将从API获取

const handleApplyFilters = async (filters: Partial<ScreenerFilters>) => {
    isLoading.value = true;
    hasSearched.value = true;
    error.value = null;
    screenedStocks.splice(0, screenedStocks.length);

    console.log('Applying filters to API:', filters);

    const requestPayload: ApiStockScreenerRequest = {
        pe_min: filters.peMin,
        pe_max: filters.peMax,
        pb_min: filters.pbMin,
        pb_max: filters.pbMax,
        market_cap_min: filters.marketCapMin,
        market_cap_max: filters.marketCapMax,
    };

    try {
        const response = await screenerApi.getScreenedStocks(requestPayload);
        // Ensure the type assertion matches the updated type
        screenedStocks.push(...response.results as ApiScreenedStock[]);
        // TODO: Handle pagination if implemented (response.total, response.page, etc.)
        if (response.results.length === 0) {
            console.log('API returned no stocks matching criteria.');
        }
    } catch (e: any) {
        console.error('Error fetching screened stocks:', e);
        if (e instanceof ApiClientError) {
            error.value = `API错误 (状态 ${e.status}): ${e.message}. ${typeof e.data?.detail === 'string' ? e.data.detail : JSON.stringify(e.data?.detail)}`;
        } else {
            error.value = e.message || '筛选股票时发生未知错误。';
        }
    } finally {
        isLoading.value = false;
    }
};

const handleUpdateData = async () => { // Assuming this button triggers 'all' data update for now
    isLoading.value = true;
    error.value = null;
    console.log('Requesting data update from API...');

    try {
        const response = await screenerApi.updateScreenerData({ data_type: 'all' });
        console.log('Data update API response:', response);
        alert(`数据更新任务已触发: ${response.message}`); // Simple feedback
        // Optionally, refresh data or prompt user to re-apply filters
        hasSearched.value = false;
        screenedStocks.splice(0, screenedStocks.length);
    } catch (e: any) {
        console.error('Error updating screener data:', e);
        if (e instanceof ApiClientError) {
            error.value = `API错误 (状态 ${e.status}): ${e.message}. ${typeof e.data?.detail === 'string' ? e.data.detail : JSON.stringify(e.data?.detail)}`;
        } else {
            error.value = e.message || '更新筛选器数据时发生未知错误。';
        }
        alert(`数据更新失败: ${error.value}`);
    } finally {
        isLoading.value = false;
    }
};

const handleGoToValuation = (stockCode: string) => {
    console.log('Navigating to valuation for stock code:', stockCode);
    // 实际导航逻辑，可能会将 stockCode 作为查询参数或状态管理传递
    // 例如，使用 Pinia store 更新选中的股票代码，然后导航
    // store.setSelectedStock(stockCode);
    router.push({ name: 'dcf-valuation', query: { stockCode: stockCode } });
    // 或者直接在DCF估值页面监听 query.stockCode
};

</script>

<style scoped>
.stock-screener-view {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}
</style>
