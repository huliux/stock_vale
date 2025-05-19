<template>
  <div class="mt-6">
    <h4 class="text-lg font-semibold mb-3 text-foreground">筛选结果 (简化版)</h4>
    
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
              <button 
                @click="goToValuation(stock.ts_code)" 
                class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-4 py-2"
              >
                进行估值
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ApiScreenedStock } from '@shared-types/index';

interface Props {
  results: ApiScreenedStock[];
  isLoading: boolean;
  error: string | null;
  hasSearched: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits(['go-to-valuation']);

// 格式化数字
const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return 'N/A';
  return value.toFixed(2);
};

const goToValuation = (stockCode: string) => {
  emit('go-to-valuation', stockCode);
};
</script>
