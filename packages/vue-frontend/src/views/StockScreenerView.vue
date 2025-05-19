<template>
    <div class="flex flex-col h-full">
        <!-- View-specific Header -->
        <header class="p-4 border-b border-border bg-card flex-shrink-0">
            <h2 class="text-xl font-semibold text-card-foreground">股票筛选器</h2>
        </header>

        <!-- Main content area for this view -->
        <div class="flex-grow flex flex-col md:flex-row overflow-hidden p-4 gap-4">
            <!-- Left Panel: Filters -->
            <div
                class="w-full md:w-1/3 lg:w-1/4 xl:w-1/5 flex-shrink-0 bg-card p-4 rounded-md border border-border shadow-sm overflow-y-auto">
                <StockScreenerFilters @apply-filters="handleApplyFilters" @update-data="handleUpdateData" />
            </div>

            <!-- Right Panel: Results Table -->
            <div class="flex-grow bg-card p-4 rounded-md border border-border shadow-sm overflow-y-auto">
                <StockScreenerResultsTable :results="screenedStocks" :is-loading="isLoading" :error="error"
                    :has-searched="hasSearched" @go-to-valuation="handleGoToValuation" />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import StockScreenerFilters, { type ScreenerFilters } from '@/components/StockScreenerFilters.vue';
import StockScreenerResultsTable from '@/components/StockScreenerResultsTable.vue';
import { screenerApi, ApiClientError } from '@/services/apiClient';
import type { ApiStockScreenerRequest, ApiScreenedStock } from '@shared-types/index';

const router = useRouter();

const screenedStocks = reactive<ApiScreenedStock[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);
const hasSearched = ref(false);

const handleApplyFilters = async (filters: Partial<ScreenerFilters>) => {
    isLoading.value = true;
    hasSearched.value = true;
    error.value = null;
    screenedStocks.splice(0, screenedStocks.length);

    console.log('Applying filters to API:', filters);

    const requestPayload: ApiStockScreenerRequest = {
        pe_min: filters.peMin ? Number(filters.peMin) : null,
        pe_max: filters.peMax ? Number(filters.peMax) : null,
        pb_min: filters.pbMin ? Number(filters.pbMin) : null,
        pb_max: filters.pbMax ? Number(filters.pbMax) : null,
        market_cap_min: filters.marketCapMin ? Number(filters.marketCapMin) : null,
        market_cap_max: filters.marketCapMax ? Number(filters.marketCapMax) : null,
        // Add other filters as they are implemented in ScreenerFilters and backend
    };

    try {
        const response = await screenerApi.getScreenedStocks(requestPayload);
        screenedStocks.push(...response.results as ApiScreenedStock[]);
        if (response.results.length === 0) {
            console.log('API returned no stocks matching criteria.');
        }
    } catch (e) {
        console.error('Error fetching screened stocks:', e);
        if (e instanceof ApiClientError) {
            error.value = `API错误 (状态 ${e.status}): ${e.message}. ${typeof e.data?.detail === 'string' ? e.data.detail : JSON.stringify(e.data?.detail)}`;
        } else if (e instanceof Error) {
            error.value = e.message || '筛选股票时发生未知错误。';
        } else {
            error.value = '筛选股票时发生未知错误。';
        }
    } finally {
        isLoading.value = false;
    }
};

const handleUpdateData = async () => {
    isLoading.value = true;
    error.value = null;
    console.log('Requesting data update from API...');

    try {
        const response = await screenerApi.updateScreenerData({ data_type: 'all' });
        console.log('Data update API response:', response);
        alert(`数据更新任务已触发: ${response.message}`);
        hasSearched.value = false;
        screenedStocks.splice(0, screenedStocks.length);
    } catch (e) {
        console.error('Error updating screener data:', e);
        if (e instanceof ApiClientError) {
            error.value = `API错误 (状态 ${e.status}): ${e.message}. ${typeof e.data?.detail === 'string' ? e.data.detail : JSON.stringify(e.data?.detail)}`;
        } else if (e instanceof Error) {
            error.value = e.message || '更新筛选器数据时发生未知错误。';
        } else {
            error.value = '更新筛选器数据时发生未知错误。';
        }
        alert(`数据更新失败: ${error.value}`);
    } finally {
        isLoading.value = false;
    }
};

const handleGoToValuation = (stockCode: string) => {
    console.log('Navigating to valuation for stock code:', stockCode);
    router.push({ name: 'dcf-valuation', query: { stockCode: stockCode } });
};

</script>

<style scoped>
/* All scoped styles should have been removed. */
/* This block is intentionally empty. */
</style>
