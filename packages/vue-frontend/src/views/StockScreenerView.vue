<template>
    <SidebarProvider :style="{
        '--sidebar-width': '350px', // Width for the second, wider sidebar panel
    }">
        <AppSidebar :is-loading="isLoading" @apply-filters="handleApplyFilters" @update-data="handleUpdateData" />
        <SidebarInset>
            <header
                class="sticky top-0 z-10 flex h-14 shrink-0 items-center justify-between gap-2 border-b bg-background p-4">
                <div class="flex items-center gap-2">
                    <SidebarTrigger class="-ml-1" />
                    <h2 class="text-xl font-semibold text-card-foreground">股票筛选结果</h2>
                </div>
                <div v-if="lastDataUpdateTime" class="text-sm text-muted-foreground">
                    数据更新时间: {{ formatDateTime(lastDataUpdateTime) }}
                </div>
            </header>
            <main class="flex-1 overflow-auto p-4">
                <div class="space-y-4">
                    <div class="bg-card p-4 rounded-md border border-border shadow-sm">
                        <h3 class="text-lg font-semibold mb-4">筛选结果</h3>
                        <StockScreenerResultsTable :results="screenedStocks" :is-loading="isLoading" :error="error"
                            :has-searched="hasSearched" :total="totalStocks" :page="currentPage" :page-size="pageSize"
                            @go-to-valuation="handleGoToValuation" @batch-valuation="handleBatchValuation"
                            @add-to-watchlist="handleAddToWatchlist" @page-change="handlePageChange" />
                    </div>
                </div>
            </main>
        </SidebarInset>
    </SidebarProvider>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import StockScreenerResultsTable from '@/components/StockScreenerResultsTable.vue';
import { type ScreenerFilters } from '@/components/StockScreenerFilters.vue';
import { screenerApi, ApiClientError } from '@/services/apiClient';
import type { ApiStockScreenerRequest, ApiScreenedStock } from '@shared-types/index';
import AppSidebar from '@/components/AppSidebar.vue';
import {
    SidebarInset,
    SidebarProvider,
    SidebarTrigger,
} from '@/components/ui/sidebar';

const router = useRouter();

const screenedStocks = reactive<ApiScreenedStock[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);
const hasSearched = ref(false);
const lastDataUpdateTime = ref<string | null>(null);

// 分页状态
const currentPage = ref(1);
const pageSize = ref(20);
const totalStocks = ref(0);
const currentFilters = ref<Partial<ScreenerFilters>>({});

// 格式化日期时间
const formatDateTime = (dateTimeStr: string | null): string => {
    if (!dateTimeStr) return '未知';

    try {
        // 处理特殊格式的日期，如 "20250519"
        if (/^\d{8}$/.test(dateTimeStr)) {
            const year = dateTimeStr.substring(0, 4);
            const month = dateTimeStr.substring(4, 6);
            const day = dateTimeStr.substring(6, 8);
            return `${year}-${month}-${day}`;
        }

        const date = new Date(dateTimeStr);
        if (isNaN(date.getTime())) {
            console.warn('无效的日期字符串:', dateTimeStr);
            return dateTimeStr;
        }

        return new Intl.DateTimeFormat('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        }).format(date);
    } catch (e) {
        console.error('日期格式化错误:', e);
        return dateTimeStr;
    }
};

const handleApplyFilters = async (filters: Partial<ScreenerFilters>) => {
    isLoading.value = true;
    hasSearched.value = true;
    error.value = null;

    // 保存当前筛选条件，用于分页
    currentFilters.value = { ...filters };

    // 重置分页状态
    currentPage.value = 1;
    screenedStocks.splice(0, screenedStocks.length);

    console.log('Applying filters to API:', filters);

    // 构建API请求参数
    const requestPayload: ApiStockScreenerRequest = {
        // 基础指标
        pe_min: filters.peMin ? Number(filters.peMin) : null,
        pe_max: filters.peMax ? Number(filters.peMax) : null,
        pb_min: filters.pbMin ? Number(filters.pbMin) : null,
        pb_max: filters.pbMax ? Number(filters.pbMax) : null,
        market_cap_min: filters.marketCapMin ? Number(filters.marketCapMin) : null,
        market_cap_max: filters.marketCapMax ? Number(filters.marketCapMax) : null,
        dividend_yield_min: filters.dividendYieldMin ? Number(filters.dividendYieldMin) : null,
        dividend_yield_max: filters.dividendYieldMax ? Number(filters.dividendYieldMax) : null,
        industry: filters.industry || null,

        // 财务指标
        roe_min: filters.roeMin ? Number(filters.roeMin) : null,
        roe_max: filters.roeMax ? Number(filters.roeMax) : null,
        gross_margin_min: filters.grossMarginMin ? Number(filters.grossMarginMin) : null,
        gross_margin_max: filters.grossMarginMax ? Number(filters.grossMarginMax) : null,
        net_margin_min: filters.netMarginMin ? Number(filters.netMarginMin) : null,
        net_margin_max: filters.netMarginMax ? Number(filters.netMarginMax) : null,
        debt_to_equity_min: filters.debtToEquityMin ? Number(filters.debtToEquityMin) : null,
        debt_to_equity_max: filters.debtToEquityMax ? Number(filters.debtToEquityMax) : null,

        // 成长指标
        revenue_growth_min: filters.revenueGrowthMin ? Number(filters.revenueGrowthMin) : null,
        revenue_growth_max: filters.revenueGrowthMax ? Number(filters.revenueGrowthMax) : null,
        profit_growth_min: filters.profitGrowthMin ? Number(filters.profitGrowthMin) : null,
        profit_growth_max: filters.profitGrowthMax ? Number(filters.profitGrowthMax) : null,
        eps_growth_min: filters.epsGrowthMin ? Number(filters.epsGrowthMin) : null,
        eps_growth_max: filters.epsGrowthMax ? Number(filters.epsGrowthMax) : null,
        growth_period: filters.growthPeriod || null,

        // 分页参数
        page: currentPage.value,
        page_size: pageSize.value
    };

    try {
        const response = await screenerApi.getScreenedStocks(requestPayload);
        screenedStocks.push(...response.results as ApiScreenedStock[]);

        // 更新总记录数
        if (response.total !== undefined) {
            totalStocks.value = response.total;
        }

        // 更新数据时间戳
        if (response.last_data_update_time) {
            lastDataUpdateTime.value = response.last_data_update_time;
        }

        if (response.results.length === 0) {
            console.log('API returned no stocks matching criteria.');
        } else {
            console.log(`API returned ${response.results.length} stocks matching criteria.`);
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

        // 更新最后数据更新时间
        if (response.last_update_times) {
            // 使用最新的时间戳
            const timestamps = [
                response.last_update_times.stock_basic,
                response.last_update_times.daily_basic
            ].filter(Boolean);

            if (timestamps.length > 0) {
                // 找出最新的时间戳
                lastDataUpdateTime.value = timestamps.sort().pop() || null;
            }
        }

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

const handlePageChange = (page: number) => {
    console.log('Changing to page:', page);
    currentPage.value = page;

    // 使用当前筛选条件重新请求数据
    handleApplyFilters(currentFilters.value);
};

const handleGoToValuation = (stockCode: string) => {
    console.log('Navigating to valuation for stock code:', stockCode);
    router.push({ name: 'dcf-valuation', query: { stockCode: stockCode } });
};

const handleBatchValuation = (stockCodes: string[]) => {
    console.log('Batch valuation for stock codes:', stockCodes);
    // 这里可以实现批量估值的逻辑
    // 例如，可以将股票代码保存到本地存储，然后跳转到批量估值页面
    // 或者打开一个新窗口进行批量估值

    // 临时实现：提示用户功能正在开发中
    alert(`批量估值功能正在开发中。选中的股票: ${stockCodes.join(', ')}`);
};

const handleAddToWatchlist = (stockCodes: string[]) => {
    console.log('Adding to watchlist:', stockCodes);
    // 这里可以实现添加到观察列表的逻辑
    // 例如，可以将股票代码保存到本地存储或发送到后端API

    // 临时实现：保存到本地存储
    const watchlist = JSON.parse(localStorage.getItem('stockWatchlist') || '[]');
    const newWatchlist = [...new Set([...watchlist, ...stockCodes])]; // 去重
    localStorage.setItem('stockWatchlist', JSON.stringify(newWatchlist));

    alert(`已将 ${stockCodes.length} 只股票添加到观察列表，共 ${newWatchlist.length} 只股票`);
};

</script>

<style scoped>
/* All scoped styles should have been removed. */
/* This block is intentionally empty. */
</style>
