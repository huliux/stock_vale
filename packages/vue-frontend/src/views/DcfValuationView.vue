<template>
    <SidebarProvider :style="{
        '--sidebar-width': '350px', // Width for the second, wider sidebar panel
    }">
        <AppSidebar :is-loading="computedIsLoading" :initial-stock-code="initialStockCode"
            @submit-valuation="handleValuationRequest" @validation-error="handleFormValidationError" />
        <SidebarInset>
            <header
                class="sticky top-0 z-10 flex h-14 shrink-0 items-center justify-between border-b bg-background p-4">
                <div class="flex items-center gap-2">
                    <SidebarTrigger class="-ml-1" />
                </div>
                <Button variant="outline" size="sm" @click="toggleHistoryDrawer">
                    <History class="h-4 w-4 mr-2" />
                    历史记录
                </Button>
            </header>
            <main class="flex-1 overflow-auto p-4">
                <DcfResultsDisplay :valuation-data="computedValuationResult" :is-loading="computedIsLoading"
                    :error="computedError" :has-calculated="hasCalculated" />
            </main>
        </SidebarInset>
    </SidebarProvider>

    <!-- 历史记录抽屉 -->
    <ValuationHistoryDrawer :is-open="historyDrawerOpen" @update:is-open="historyDrawerOpen = $event"
        @load-record="loadHistoryRecord" />
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import DcfResultsDisplay from '@/components/DcfResultsDisplay.vue';
import { valuationApi, ApiClientError } from '@/services/apiClient';
import type { ApiDcfValuationRequest, ApiDcfValuationResponse } from '@shared-types/index';
import { useValuationStore } from '@/stores/valuationStore';
import { useHistoryStore } from '@/stores/historyStore';
import { Button } from '@/components/ui/button';
import { History } from 'lucide-vue-next';
import ValuationHistoryDrawer from '@/components/ValuationHistoryDrawer.vue';

// Imports for Sidebar09 structure
import AppSidebar from '@/components/AppSidebar.vue';
import {
    SidebarInset,
    SidebarProvider,
    SidebarTrigger,
} from '@/components/ui/sidebar';

const route = useRoute();
const valuationStore = useValuationStore();
const historyStore = useHistoryStore();

const computedValuationResult = computed(() => valuationStore.getValuationResult);
const computedIsLoading = computed(() => valuationStore.getIsLoading);
const computedError = computed(() => valuationStore.getError);

const hasCalculated = ref(false);
const initialStockCode = ref<string | null>(null);
const historyDrawerOpen = ref(false);

// 监听路由查询参数的变化
const updateStockCodeFromRoute = () => {
    if (route.query.stockCode && typeof route.query.stockCode === 'string') {
        console.log('DcfValuationView: 从URL查询参数中获取股票代码:', route.query.stockCode);
        initialStockCode.value = route.query.stockCode;
    }
};

// 组件挂载时设置初始股票代码
onMounted(updateStockCodeFromRoute);

// 监听整个route对象，当它变化时检查stockCode
watch(route, (newRoute) => {
    if (newRoute.query.stockCode && typeof newRoute.query.stockCode === 'string') {
        console.log('DcfValuationView: 路由查询参数stockCode变化为:', newRoute.query.stockCode);
        initialStockCode.value = newRoute.query.stockCode;
    }
});

const handleValuationRequest = async (apiParams: ApiDcfValuationRequest) => {
    console.log('DcfValuationView: handleValuationRequest被调用');
    hasCalculated.value = true;
    valuationStore.setLoading(true);
    console.log('DcfValuationView: Requesting valuation with API params:', apiParams);
    try {
        console.log('DcfValuationView: 调用valuationApi.performDcfValuation');
        const result = await valuationApi.performDcfValuation(apiParams);
        console.log('DcfValuationView: API调用成功，结果:', result);
        valuationStore.setValuationResult(result);

        // 将估值结果保存到历史记录
        historyStore.addRecord(result);
    } catch (e: unknown) {
        console.error('Error during valuation request:', e);
        let errorMessage: string;
        if (e instanceof ApiClientError) {
            errorMessage = `API错误 (状态 ${e.status}): ${e.message}. ${typeof e.data?.detail === 'string' ? e.data.detail : JSON.stringify(e.data?.detail)}`;
        } else if (e instanceof Error) {
            errorMessage = e.message || '进行估值计算时发生未知错误。';
        } else {
            errorMessage = '进行估值计算时发生未知错误。';
        }
        valuationStore.setError(errorMessage);
    } finally {
        valuationStore.setLoading(false);
    }
};

const handleFormValidationError = (errorMessage: string) => {
    valuationStore.setError(errorMessage);
    if (valuationStore.getIsLoading) {
        valuationStore.setLoading(false);
    }
    valuationStore.clearResult();
    hasCalculated.value = true;
};

// 切换历史记录抽屉的显示状态
const toggleHistoryDrawer = () => {
    historyDrawerOpen.value = !historyDrawerOpen.value;

    // 如果是打开抽屉，确保历史记录已从localStorage加载
    if (historyDrawerOpen.value) {
        historyStore.loadFromLocalStorage();
    }
};

// 加载历史记录中的估值结果
const loadHistoryRecord = (record: ApiDcfValuationResponse) => {
    valuationStore.setValuationResult(record);
    hasCalculated.value = true;

    // 如果记录中有股票代码，更新initialStockCode以便在侧边栏显示
    if (record.stock_info?.ts_code) {
        initialStockCode.value = record.stock_info.ts_code;
    }
};
</script>

<style scoped>
/* This block is intentionally empty. */
</style>
