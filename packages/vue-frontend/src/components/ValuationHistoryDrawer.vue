<template>
    <Sheet :open="isOpen" @update:open="updateOpen">
        <SheetContent side="right" class="w-[400px] sm:w-[540px] overflow-y-auto">
            <SheetHeader>
                <SheetTitle>估值历史记录</SheetTitle>
                <SheetDescription>查看之前的估值结果</SheetDescription>
            </SheetHeader>
            
            <div class="py-4">
                <div v-if="historyRecords.length === 0" class="text-center py-8 text-muted-foreground">
                    <p>暂无历史记录</p>
                </div>
                
                <div v-else class="space-y-4">
                    <div class="flex justify-between items-center mb-4">
                        <span class="text-sm text-muted-foreground">共 {{ historyRecords.length }} 条记录</span>
                        <Button variant="outline" size="sm" @click="confirmClearHistory">
                            <Trash2 class="h-4 w-4 mr-2" />
                            清空历史
                        </Button>
                    </div>
                    
                    <Card v-for="record in historyRecords" :key="record.id" class="cursor-pointer hover:bg-muted/50 transition-colors"
                        @click="loadRecord(record.id)">
                        <CardContent class="p-4">
                            <div class="flex justify-between items-start">
                                <div>
                                    <div class="flex items-center gap-2">
                                        <h3 class="font-medium">
                                            {{ record.valuationResult.stock_info?.name || 'N/A' }}
                                            ({{ record.valuationResult.stock_info?.ts_code || 'N/A' }})
                                        </h3>
                                        <Badge>{{ formatDate(record.timestamp, 'yyyy-MM-dd') }}</Badge>
                                    </div>
                                    <div class="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                                        <div class="flex items-center justify-between">
                                            <span class="text-muted-foreground">内在价值:</span>
                                            <span class="font-medium">¥{{ formatNumber(record.valuationResult.valuation_results?.dcf_forecast_details?.value_per_share) }}</span>
                                        </div>
                                        <div class="flex items-center justify-between">
                                            <span class="text-muted-foreground">最新价格:</span>
                                            <span class="font-medium">¥{{ formatNumber(record.valuationResult.valuation_results?.latest_price) }}</span>
                                        </div>
                                        <div class="flex items-center justify-between">
                                            <span class="text-muted-foreground">上升空间:</span>
                                            <span class="font-medium" :class="getUpsidePotentialClass(record.valuationResult)">
                                                {{ formatUpsidePotential(record.valuationResult) }}
                                            </span>
                                        </div>
                                        <div class="flex items-center justify-between">
                                            <span class="text-muted-foreground">隐含PE:</span>
                                            <span class="font-medium">{{ formatNumber(record.valuationResult.valuation_results?.dcf_forecast_details?.dcf_implied_diluted_pe) }}×</span>
                                        </div>
                                    </div>
                                </div>
                                <Button variant="ghost" size="icon" class="h-8 w-8" @click.stop="removeRecord(record.id)">
                                    <X class="h-4 w-4" />
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </SheetContent>
    </Sheet>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { format as formatDate } from 'date-fns';
import { 
    Sheet, 
    SheetContent, 
    SheetHeader, 
    SheetTitle, 
    SheetDescription 
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Trash2, X } from 'lucide-vue-next';
import { useHistoryStore } from '@/stores/historyStore';
import type { ApiDcfValuationResponse } from '@shared-types/index';
import { toast } from 'vue-sonner';

const props = defineProps<{
    isOpen: boolean;
}>();

const emit = defineEmits<{
    (e: 'update:isOpen', value: boolean): void;
    (e: 'load-record', record: ApiDcfValuationResponse): void;
}>();

const historyStore = useHistoryStore();
const historyRecords = computed(() => historyStore.getAllRecords);

// Update the open state
const updateOpen = (value: boolean) => {
    emit('update:isOpen', value);
};

// Format number with 2 decimal places
const formatNumber = (value: number | null | undefined): string => {
    if (value === null || value === undefined || isNaN(value)) return 'N/A';
    return value.toFixed(2);
};

// Calculate and format upside potential
const formatUpsidePotential = (result: ApiDcfValuationResponse): string => {
    const valuePerShare = result.valuation_results?.dcf_forecast_details?.value_per_share;
    const latestPrice = result.valuation_results?.latest_price ?? result.stock_info?.latest_price;
    
    if (typeof valuePerShare === 'number' && typeof latestPrice === 'number' && latestPrice !== 0) {
        const upsidePotential = (valuePerShare / latestPrice) - 1;
        return `${(upsidePotential * 100).toFixed(2)}%`;
    }
    return 'N/A';
};

// Get CSS class for upside potential
const getUpsidePotentialClass = (result: ApiDcfValuationResponse): string => {
    const valuePerShare = result.valuation_results?.dcf_forecast_details?.value_per_share;
    const latestPrice = result.valuation_results?.latest_price ?? result.stock_info?.latest_price;
    
    if (typeof valuePerShare === 'number' && typeof latestPrice === 'number' && latestPrice !== 0) {
        const upsidePotential = (valuePerShare / latestPrice) - 1;
        return upsidePotential < 0 ? 'text-red-500' : 'text-green-500';
    }
    return '';
};

// Load a record
const loadRecord = (id: string) => {
    const record = historyStore.getRecordById(id);
    if (record) {
        emit('load-record', record.valuationResult);
        updateOpen(false);
        toast.success(`已加载 ${record.valuationResult.stock_info?.name} 的估值记录`);
    }
};

// Remove a record
const removeRecord = (id: string) => {
    historyStore.removeRecord(id);
    toast.success('已删除估值记录');
};

// Clear all history with confirmation
const confirmClearHistory = () => {
    if (confirm('确定要清空所有历史记录吗？此操作不可撤销。')) {
        historyStore.clearAllRecords();
        toast.success('已清空所有历史记录');
    }
};
</script>
