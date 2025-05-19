<template>
  <div class="mt-6">
    <div class="flex justify-between items-center mb-3">
      <h4 class="text-lg font-semibold text-foreground">Dialog 测试表格</h4>
      <div class="flex items-center gap-2" v-if="results.length > 0">
        <Button @click="showDialog" variant="outline" size="sm">
          打开对话框
        </Button>
      </div>
    </div>

    <div v-if="isLoading" class="p-4 border rounded-md mt-4 bg-blue-50 text-blue-700 border-blue-200">
      正在加载数据...
    </div>
    <div v-else-if="error" class="p-4 border rounded-md mt-4 bg-red-50 text-red-700 border-red-200">
      {{ error }}
    </div>
    <div v-else-if="results.length === 0 && !hasSearched"
      class="p-4 border rounded-md mt-4 bg-sky-50 text-sky-700 border-sky-200">
      请设置筛选条件并点击"应用筛选"。
    </div>
    <div v-else-if="results.length === 0 && hasSearched"
      class="p-4 border rounded-md mt-4 bg-yellow-50 text-yellow-700 border-yellow-200">
      没有找到符合条件的股票。
    </div>
    <div v-else class="overflow-x-auto rounded-md border border-border">
      <table class="w-full text-sm caption-bottom">
        <thead class="[&_tr]:border-b [&_tr]:border-border">
          <tr class="hover:bg-muted/50 data-[state=selected]:bg-muted">
            <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">股票代码</th>
            <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">股票名称</th>
            <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">最新价格</th>
            <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">市盈率(PE)</th>
            <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">市净率(PB)</th>
            <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">总市值(亿元)</th>
            <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">操作</th>
          </tr>
        </thead>
        <tbody class="[&_tr:last-child]:border-0">
          <tr v-for="stock in results" :key="stock.ts_code"
            class="border-b border-border transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
            <td class="p-4 align-middle">{{ stock.ts_code }}</td>
            <td class="p-4 align-middle">{{ stock.name }}</td>
            <td class="p-4 align-middle">{{ formatNumber(stock.close) }}</td>
            <td class="p-4 align-middle">{{ formatNumber(stock.pe_ttm) }}</td>
            <td class="p-4 align-middle">{{ formatNumber(stock.pb) }}</td>
            <td class="p-4 align-middle">{{ formatNumber(stock.market_cap_billion) }}</td>
            <td class="p-4 align-middle">
              <Button @click="showStockDetails(stock)" variant="outline" size="sm">详情</Button>
              <Button @click="goToValuation(stock.ts_code)" variant="default" size="sm" class="ml-2">估值</Button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 股票详情对话框 -->
    <Dialog :open="!!selectedStock" @update:open="closeStockDetails">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle v-if="selectedStock">{{ selectedStock.name }} ({{ selectedStock.ts_code }})</DialogTitle>
          <DialogDescription>股票详细信息</DialogDescription>
        </DialogHeader>

        <div v-if="selectedStock" class="py-4 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <h4 class="text-sm font-medium text-muted-foreground mb-1">基本信息</h4>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-sm text-muted-foreground">最新价格:</span>
                  <span class="text-sm">{{ formatNumber(selectedStock.close) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-muted-foreground">总市值:</span>
                  <span class="text-sm">{{ formatNumber(selectedStock.market_cap_billion) }}亿</span>
                </div>
              </div>
            </div>

            <div>
              <h4 class="text-sm font-medium text-muted-foreground mb-1">估值指标</h4>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-sm text-muted-foreground">市盈率(PE):</span>
                  <span class="text-sm">{{ formatNumber(selectedStock.pe_ttm) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-muted-foreground">市净率(PB):</span>
                  <span class="text-sm">{{ formatNumber(selectedStock.pb) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button @click="goToValuation(selectedStock?.ts_code || '')" variant="default">进行估值</Button>
          <Button @click="closeStockDetails" variant="outline">关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 测试对话框 -->
    <Dialog :open="dialogOpen" @update:open="dialogOpen = $event">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>测试对话框</DialogTitle>
          <DialogDescription>这是一个测试对话框，用于验证 Dialog 组件是否正常工作。</DialogDescription>
        </DialogHeader>
        <div class="py-4">
          <p>对话框内容</p>
        </div>
        <DialogFooter>
          <Button @click="dialogOpen = false" variant="outline">关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import type { ApiScreenedStock } from '@shared-types/index';
import { ref } from 'vue';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface Props {
  results: ApiScreenedStock[];
  isLoading: boolean;
  error: string | null;
  hasSearched: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits(['go-to-valuation']);

// 对话框状态
const dialogOpen = ref(false);
const selectedStock = ref<ApiScreenedStock | null>(null);

// 格式化数字
const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return 'N/A';
  return value.toFixed(2);
};

const showDialog = () => {
  dialogOpen.value = true;
};

const showStockDetails = (stock: ApiScreenedStock) => {
  selectedStock.value = stock;
};

const closeStockDetails = () => {
  selectedStock.value = null;
};

const goToValuation = (stockCode: string) => {
  emit('go-to-valuation', stockCode);
};
</script>
