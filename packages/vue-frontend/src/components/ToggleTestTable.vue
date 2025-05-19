<template>
  <div class="mt-6">
    <div class="flex justify-between items-center mb-3">
      <h4 class="text-lg font-semibold text-foreground">Toggle 测试表格</h4>
      <div class="flex items-center gap-2" v-if="results.length > 0">
        <div class="flex items-center gap-1">
          <label for="view-mode" class="text-sm text-muted-foreground">视图:</label>
          <ToggleGroupRoot type="single" v-model="viewMode" variant="outline" class="h-9">
            <ToggleGroupItem value="table" class="px-3">
              表格
            </ToggleGroupItem>
            <ToggleGroupItem value="cards" class="px-3">
              卡片
            </ToggleGroupItem>
          </ToggleGroupRoot>
        </div>
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

    <!-- 表格视图 -->
    <div v-else-if="viewMode === 'table'" class="overflow-x-auto rounded-md border border-border">
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
              <Button @click="goToValuation(stock.ts_code)" variant="default" size="sm">估值</Button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 卡片视图 -->
    <div v-else-if="viewMode === 'cards'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
      <div v-for="stock in results" :key="stock.ts_code"
        class="border border-border rounded-lg p-4 bg-card hover:shadow-md transition-shadow">
        <div class="flex justify-between items-start mb-2">
          <div>
            <h3 class="font-medium text-foreground">{{ stock.name }}</h3>
            <p class="text-sm text-muted-foreground">{{ stock.ts_code }}</p>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-2 my-3">
          <div class="text-sm">
            <span class="text-muted-foreground">价格:</span>
            <span class="font-medium">{{ formatNumber(stock.close) }}</span>
          </div>
          <div class="text-sm">
            <span class="text-muted-foreground">市值:</span>
            <span class="font-medium">{{ formatNumber(stock.market_cap_billion) }}亿</span>
          </div>
          <div class="text-sm">
            <span class="text-muted-foreground">PE:</span>
            <span class="font-medium">{{ formatNumber(stock.pe_ttm) }}</span>
          </div>
          <div class="text-sm">
            <span class="text-muted-foreground">PB:</span>
            <span class="font-medium">{{ formatNumber(stock.pb) }}</span>
          </div>
        </div>

        <div class="flex justify-end gap-2 mt-3">
          <Button @click="goToValuation(stock.ts_code)" variant="default" size="sm">估值</Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ApiScreenedStock } from '@shared-types/index';
import { ref } from 'vue';
import { Button } from '@/components/ui/button';
import { ToggleGroup as ToggleGroupRoot, ToggleGroupItem } from '@/components/ui/toggle-group';

interface Props {
  results: ApiScreenedStock[];
  isLoading: boolean;
  error: string | null;
  hasSearched: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits(['go-to-valuation']);

// 视图状态
const viewMode = ref<'table' | 'cards'>('table');

// 格式化数字
const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return 'N/A';
  return value.toFixed(2);
};

const goToValuation = (stockCode: string) => {
  emit('go-to-valuation', stockCode);
};
</script>
