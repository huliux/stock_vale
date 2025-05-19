<template>
    <SidebarProvider :style="{
        '--sidebar-width': '350px', // Width for the second, wider sidebar panel
    }">
        <AppSidebar :is-loading="computedIsLoading" :initial-stock-code="initialStockCode"
            @submit-valuation="handleValuationRequest" @validation-error="handleFormValidationError" />
        <SidebarInset>
            <header class="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b bg-background p-4">
                <SidebarTrigger class="-ml-1" />
                <h2 class="text-lg font-semibold text-foreground ml-2">估值结果</h2>
            </header>
            <main class="flex-1 overflow-auto p-4">
                <DcfResultsDisplay :valuation-data="computedValuationResult" :is-loading="computedIsLoading"
                    :error="computedError" :has-calculated="hasCalculated" />
            </main>
        </SidebarInset>
    </SidebarProvider>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import DcfResultsDisplay from '@/components/DcfResultsDisplay.vue';
import { valuationApi, ApiClientError } from '@/services/apiClient';
import type { ApiDcfValuationRequest } from '@shared-types/index';
import { useValuationStore } from '@/stores/valuationStore';

// Imports for Sidebar09 structure
import AppSidebar from '@/components/AppSidebar.vue';
import {
    SidebarInset,
    SidebarProvider,
    SidebarTrigger,
} from '@/components/ui/sidebar';

const route = useRoute();
const valuationStore = useValuationStore();

const computedValuationResult = computed(() => valuationStore.getValuationResult);
const computedIsLoading = computed(() => valuationStore.getIsLoading);
const computedError = computed(() => valuationStore.getError);

const hasCalculated = ref(false);
const initialStockCode = ref<string | null>(null);

onMounted(() => {
    if (route.query.stockCode && typeof route.query.stockCode === 'string') {
        initialStockCode.value = route.query.stockCode;
    }
});

const handleValuationRequest = async (apiParams: ApiDcfValuationRequest) => {
    hasCalculated.value = true;
    valuationStore.setLoading(true);
    console.log('Requesting valuation with API params:', apiParams);
    try {
        const result = await valuationApi.performDcfValuation(apiParams);
        valuationStore.setValuationResult(result);
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
</script>

<style scoped>
/* This block is intentionally empty. */
</style>
