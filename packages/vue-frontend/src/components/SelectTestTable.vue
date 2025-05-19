<template>
  <div class="mt-6">
    <div class="flex justify-between items-center mb-3">
      <h4 class="text-lg font-semibold text-foreground">Select 测试表格</h4>
      <div class="flex items-center gap-2" v-if="results.length > 0">
        <div class="flex items-center gap-1">
          <label for="sort-field" class="text-sm text-muted-foreground">排序:</label>
          <Select v-model="sortField" id="sort-field" class="w-32">
            <SelectTrigger>
              <SelectValue placeholder="选择排序字段" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="name">股票名称</SelectItem>
              <SelectItem value="close">最新价格</SelectItem>
              <SelectItem value="pe_ttm">市盈率</SelectItem>
              <SelectItem value="pb">市净率</SelectItem>
              <SelectItem value="market_cap_billion">市值</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button @click="toggleSortOrder" variant="outline" size="sm">
          {{ sortOrder === 'asc' ? '升序' : '降序' }}
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
          <tr v-for="stock in sortedStocks" :key="stock.ts_code"
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
  </div>
</template>

<script setup lang="ts">
import type { ApiScreenedStock } from '@shared-types/index';
import { ref, computed } from 'vue';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface Props {
  results: ApiScreenedStock[];
  isLoading: boolean;
  error: string | null;
  hasSearched: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits(['go-to-valuation']);

// 排序状态
const sortField = ref<string>('name');
const sortOrder = ref<'asc' | 'desc'>('asc');

// 计算属性
const sortedStocks = computed(() => {
  if (!props.results || props.results.length === 0) return [];
  
  return [...props.results].sort((a, b) => {
    const aValue = a[sortField.value as keyof ApiScreenedStock];
    const bValue = b[sortField.value as keyof ApiScreenedStock];
    
    // 处理可能为 null 或 undefined 的值
    if (aValue === null || aValue === undefined) return sortOrder.value === 'asc' ? -1 : 1;
    if (bValue === null || bValue === undefined) return sortOrder.value === 'asc' ? 1 : -1;
    
    // 字符串比较
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortOrder.value === 'asc' 
        ? aValue.localeCompare(bValue) 
        : bValue.localeCompare(aValue);
    }
    
    // 数字比较
    return sortOrder.value === 'asc' 
      ? (aValue as number) - (bValue as number) 
      : (bValue as number) - (aValue as number);
  });
});

// 方法
const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
};

// 格式化数字
const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return 'N/A';
  return value.toFixed(2);
};

const goToValuation = (stockCode: string) => {
  emit('go-to-valuation', stockCode);
};
</script>
