<template>
    <SidebarProvider :style="{
        '--sidebar-width': '320px', // 调整侧边栏宽度，避免横向滚动
    }">
        <AppSidebar :is-loading="isLoading" :data-update-status="dataUpdateStatus" @apply-filters="handleApplyFilters"
            @update-data="handleUpdateData" />
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
                    <StockScreenerResultsTable :results="screenedStocks" :is-loading="isLoading" :error="error"
                        :has-searched="hasSearched" :total="totalStocks" :page="currentPage" :page-size="pageSize"
                        @go-to-valuation="handleGoToValuation" @batch-valuation="handleBatchValuation"
                        @add-to-watchlist="handleAddToWatchlist" @page-change="handlePageChange" @retry="handleRetry" />
                </div>
            </main>
        </SidebarInset>
    </SidebarProvider>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
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
import { toast } from 'vue-sonner';

const router = useRouter();

const screenedStocks = reactive<ApiScreenedStock[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);
const hasSearched = ref(false);
const lastDataUpdateTime = ref<string | null>(null);
const dataUpdateStatus = ref<string>('');

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

// 保存筛选结果和条件到 localStorage
const saveScreenerState = () => {
    try {
        // 保存筛选条件
        localStorage.setItem('screenerFilters', JSON.stringify(currentFilters.value));

        // 保存筛选结果
        localStorage.setItem('screenerResults', JSON.stringify(screenedStocks));

        // 保存其他状态
        localStorage.setItem('screenerState', JSON.stringify({
            hasSearched: hasSearched.value,
            currentPage: currentPage.value,
            totalStocks: totalStocks.value,
            lastDataUpdateTime: lastDataUpdateTime.value
        }));

        console.log('筛选状态已保存到 localStorage');
    } catch (error) {
        console.error('保存筛选状态时出错:', error);
    }
};

// 从 localStorage 恢复筛选结果和条件
const restoreScreenerState = () => {
    try {
        // 恢复筛选条件
        const savedFilters = localStorage.getItem('screenerFilters');
        if (savedFilters) {
            currentFilters.value = JSON.parse(savedFilters);
        }

        // 恢复筛选结果
        const savedResults = localStorage.getItem('screenerResults');
        if (savedResults) {
            const parsedResults = JSON.parse(savedResults);
            screenedStocks.splice(0, screenedStocks.length, ...parsedResults);
        }

        // 恢复其他状态
        const savedState = localStorage.getItem('screenerState');
        if (savedState) {
            const state = JSON.parse(savedState);
            hasSearched.value = state.hasSearched;
            currentPage.value = state.currentPage;
            totalStocks.value = state.totalStocks;
            lastDataUpdateTime.value = state.lastDataUpdateTime;
        }

        console.log('筛选状态已从 localStorage 恢复');
    } catch (error) {
        console.error('恢复筛选状态时出错:', error);
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

    // 构建API请求参数 - 使用后端路由处理代码中使用的字段名称
    const requestPayload: ApiStockScreenerRequest = {
        // 基础指标
        pe_min: filters.peMin ? Number(filters.peMin) : null,
        pe_max: filters.peMax ? Number(filters.peMax) : null,
        pe_ttm_min: filters.peTtmMin ? Number(filters.peTtmMin) : null,
        pe_ttm_max: filters.peTtmMax ? Number(filters.peTtmMax) : null,
        pb_min: filters.pbMin ? Number(filters.pbMin) : null,
        pb_max: filters.pbMax ? Number(filters.pbMax) : null,
        ps_min: filters.psMin ? Number(filters.psMin) : null,
        ps_max: filters.psMax ? Number(filters.psMax) : null,
        ps_ttm_min: filters.psTtmMin ? Number(filters.psTtmMin) : null,
        ps_ttm_max: filters.psTtmMax ? Number(filters.psTtmMax) : null,

        // 自由流通股本参数 - 暂时不使用，因为与市值参数有冲突
        free_share_min: null,
        free_share_max: null,

        // 市值参数 - 使用后端路由处理代码中使用的字段名称（单位：亿元）
        // 前端输入的是亿元，直接传递
        market_cap_min: filters.totalMvMin ? Number(filters.totalMvMin) : null,
        market_cap_max: filters.totalMvMax ? Number(filters.totalMvMax) : null,

        // 其他参数
        industry: filters.industry && filters.industry !== 'all' ? filters.industry : null,
        act_ent_type: filters.actEntType && filters.actEntType !== 'all' ? filters.actEntType : null,

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

        // 保存筛选状态到 localStorage
        saveScreenerState();
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

const handleUpdateData = async (dataType: 'basic' | 'daily' | 'all' = 'all') => {
    isLoading.value = true;
    error.value = null;

    const dataTypeText = {
        'basic': '基础',
        'daily': '行情',
        'all': '全部'
    }[dataType];

    dataUpdateStatus.value = `正在更新${dataTypeText}数据，请稍候...`;
    console.log(`Requesting ${dataType} data update from API...`);

    try {
        const response = await screenerApi.updateScreenerData({ data_type: dataType });
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

        // 使用Toast通知用户更新成功
        toast.success({
            title: "数据更新成功",
            description: `${dataTypeText}数据更新任务已触发: ${response.message}`,
            duration: 3000
        });

        dataUpdateStatus.value = `${dataTypeText}数据更新任务已触发: ${response.message}`;

        // 如果已经有搜索结果，询问用户是否要刷新
        if (hasSearched.value && screenedStocks.length > 0) {
            if (confirm('数据已更新，是否要使用当前筛选条件重新搜索？')) {
                dataUpdateStatus.value = '正在使用新数据重新搜索...';
                await handleApplyFilters(currentFilters.value);
                dataUpdateStatus.value = '搜索完成！';
            }
        } else {
            hasSearched.value = false;
            screenedStocks.splice(0, screenedStocks.length);
        }
    } catch (e) {
        console.error('Error updating screener data:', e);
        let errorMessage = '';

        if (e instanceof ApiClientError) {
            errorMessage = `API错误 (状态 ${e.status}): ${e.message}. ${typeof e.data?.detail === 'string' ? e.data.detail : JSON.stringify(e.data?.detail)}`;
        } else if (e instanceof Error) {
            errorMessage = e.message || '更新筛选器数据时发生未知错误。';
        } else {
            errorMessage = '更新筛选器数据时发生未知错误。';
        }

        error.value = errorMessage;
        dataUpdateStatus.value = `数据更新失败: ${error.value}`;

        // 使用Toast通知用户更新失败
        toast.error({
            title: "数据更新失败",
            description: errorMessage,
            duration: 5000
        });
    } finally {
        // 5秒后清除状态消息
        setTimeout(() => {
            dataUpdateStatus.value = '';
            isLoading.value = false;
        }, 5000);
    }
};

const handlePageChange = async (page: number) => {
    console.log('Changing to page:', page);
    currentPage.value = page;
    isLoading.value = true;
    error.value = null;

    try {
        // 构建API请求参数 - 使用当前筛选条件，但更新页码
        const requestPayload: ApiStockScreenerRequest = {
            // 基础指标
            pe_min: currentFilters.value.peMin ? Number(currentFilters.value.peMin) : null,
            pe_max: currentFilters.value.peMax ? Number(currentFilters.value.peMax) : null,
            pe_ttm_min: currentFilters.value.peTtmMin ? Number(currentFilters.value.peTtmMin) : null,
            pe_ttm_max: currentFilters.value.peTtmMax ? Number(currentFilters.value.peTtmMax) : null,
            pb_min: currentFilters.value.pbMin ? Number(currentFilters.value.pbMin) : null,
            pb_max: currentFilters.value.pbMax ? Number(currentFilters.value.pbMax) : null,
            ps_min: currentFilters.value.psMin ? Number(currentFilters.value.psMin) : null,
            ps_max: currentFilters.value.psMax ? Number(currentFilters.value.psMax) : null,
            ps_ttm_min: currentFilters.value.psTtmMin ? Number(currentFilters.value.psTtmMin) : null,
            ps_ttm_max: currentFilters.value.psTtmMax ? Number(currentFilters.value.psTtmMax) : null,

            // 自由流通股本参数 - 暂时不使用，因为与市值参数有冲突
            free_share_min: null,
            free_share_max: null,

            // 市值参数 - 使用后端路由处理代码中使用的字段名称（单位：亿元）
            market_cap_min: currentFilters.value.totalMvMin ? Number(currentFilters.value.totalMvMin) : null,
            market_cap_max: currentFilters.value.totalMvMax ? Number(currentFilters.value.totalMvMax) : null,

            // 其他参数
            industry: currentFilters.value.industry && currentFilters.value.industry !== 'all' ? currentFilters.value.industry : null,
            act_ent_type: currentFilters.value.actEntType && currentFilters.value.actEntType !== 'all' ? currentFilters.value.actEntType : null,

            // 分页参数 - 使用新的页码
            page: page,
            page_size: pageSize.value
        };

        // 清空当前结果，准备加载新页面数据
        screenedStocks.splice(0, screenedStocks.length);

        const response = await screenerApi.getScreenedStocks(requestPayload);
        screenedStocks.push(...response.results as ApiScreenedStock[]);

        // 更新总记录数
        if (response.total !== undefined) {
            totalStocks.value = response.total;
        }

        console.log(`Page ${page} loaded with ${response.results.length} results. Total: ${totalStocks.value}`);

        // 保存筛选状态到 localStorage
        saveScreenerState();
    } catch (e) {
        console.error('Error fetching page data:', e);
        if (e instanceof ApiClientError) {
            error.value = `API错误 (状态 ${e.status}): ${e.message}. ${typeof e.data?.detail === 'string' ? e.data.detail : JSON.stringify(e.data?.detail)}`;
        } else if (e instanceof Error) {
            error.value = e.message || '获取分页数据时发生未知错误。';
        } else {
            error.value = '获取分页数据时发生未知错误。';
        }
    } finally {
        isLoading.value = false;
    }
};

// 处理重试事件
const handleRetry = () => {
    console.log('Retrying with current filters...');
    error.value = null;

    // 使用当前筛选条件重新请求数据
    if (hasSearched.value) {
        handleApplyFilters(currentFilters.value);
    }
};

const handleGoToValuation = (stockCode: string) => {
    console.log('Navigating to valuation for stock code:', stockCode);
    router.push({ name: 'dcf-valuation', query: { stockCode: stockCode } });
};

const handleBatchValuation = (stockCodes: string[]) => {
    console.log('Batch valuation for stock codes:', stockCodes);

    if (stockCodes.length === 0) {
        alert('请先选择要估值的股票');
        return;
    }

    // 将选中的股票代码保存到本地存储
    localStorage.setItem('batchValuationStocks', JSON.stringify(stockCodes));

    // 如果只有一只股票，直接跳转到估值页面
    if (stockCodes.length === 1) {
        router.push({ name: 'dcf-valuation', query: { stockCode: stockCodes[0] } });
        return;
    }

    // 如果有多只股票，跳转到估值页面并传递第一只股票的代码，其他股票将从本地存储中读取
    router.push({
        name: 'dcf-valuation',
        query: {
            stockCode: stockCodes[0],
            batchMode: 'true',
            batchCount: stockCodes.length.toString()
        }
    });
};

// 组件挂载时恢复筛选状态
onMounted(() => {
    restoreScreenerState();
});

const handleAddToWatchlist = (stockCodes: string[]) => {
    console.log('Adding to watchlist:', stockCodes);

    if (stockCodes.length === 0) {
        alert('请先选择要添加到观察列表的股票');
        return;
    }

    try {
        // 从本地存储获取现有观察列表
        const watchlist = JSON.parse(localStorage.getItem('stockWatchlist') || '[]');

        // 找出新添加的股票（不在现有观察列表中的）
        const newStocks = stockCodes.filter(code => !watchlist.includes(code));

        // 如果没有新的股票要添加，提示用户
        if (newStocks.length === 0) {
            alert('所选股票已全部在观察列表中');
            return;
        }

        // 合并并去重
        const newWatchlist = [...new Set([...watchlist, ...stockCodes])];

        // 保存到本地存储
        localStorage.setItem('stockWatchlist', JSON.stringify(newWatchlist));

        // 获取股票名称以显示在提示中
        const stockNames = stockCodes.map(code => {
            const stock = screenedStocks.find(s => s.ts_code === code);
            return stock ? `${stock.name}(${code})` : code;
        });

        // 显示成功消息
        alert(`已将 ${newStocks.length} 只股票添加到观察列表，共 ${newWatchlist.length} 只股票\n\n添加的股票: ${stockNames.join(', ')}`);
    } catch (error) {
        console.error('添加到观察列表时出错:', error);
        alert('添加到观察列表时出错，请重试');
    }
};

</script>

<style scoped>
/* All scoped styles should have been removed. */
/* This block is intentionally empty. */
</style>
