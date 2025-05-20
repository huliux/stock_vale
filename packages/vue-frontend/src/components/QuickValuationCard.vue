<template>
  <Card class="shadow-none border-t z-10 bg-background/95 backdrop-blur-sm">
    <form @submit.prevent="submitForm">
      <CardContent class="grid gap-2 p-2">
        <div class="grid grid-cols-2 gap-2">
          <div>
            <Label for="stock-code" class="text-xs font-medium">股票代码</Label>
            <Input id="stock-code" type="text" v-model="stockCode" @input="handleStockCodeInput" required placeholder="600519.SH"
              class="mt-0.5 w-full h-8" />
          </div>
          <div>
            <Label for="valuation-date" class="text-xs font-medium">估值日期</Label>
            <div class="mt-0.5">
              <!-- 使用原生input元素，确保日期选择器正常工作 -->
              <input id="valuation-date" type="date" v-model="valuationDate"
                class="flex h-8 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50" />
            </div>
          </div>
        </div>
        <Button type="submit" class="w-full bg-primary text-primary-foreground shadow-none h-8" size="sm"
          :disabled="isLoading">
          {{ isLoading ? '正在计算...' : '开始估值' }}
        </Button>
      </CardContent>
    </form>
  </Card>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
} from '@/components/ui/card';

const props = defineProps<{
  initialStockCode?: string | null;
  isLoading: boolean;
}>();

const emit = defineEmits<{
  (e: 'submit', stockCode: string, valuationDate: string): void;
  (e: 'stock-code-change', stockCode: string): void;
}>();

const stockCode = ref(props.initialStockCode || '600519.SH');
const valuationDate = ref(getTodayDateString());

// 初始化
onMounted(() => {
  console.log('QuickValuationCard: onMounted');

  // 设置初始股票代码
  if (props.initialStockCode) {
    stockCode.value = props.initialStockCode;
  }

  console.log('QuickValuationCard: 初始化完成，日期:', valuationDate.value);
});

// 监听initialStockCode的变化
watch(() => props.initialStockCode, (newVal) => {
  if (newVal) {
    console.log('QuickValuationCard: initialStockCode变化为:', newVal);
    stockCode.value = newVal;
  }
});

function getTodayDateString() {
  const today = new Date();
  const year = today.getFullYear();
  const month = (today.getMonth() + 1).toString().padStart(2, '0');
  const day = today.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// 监听日期变化，确保格式正确
watch(valuationDate, (newDate) => {
  console.log('日期变化:', newDate);

  // 如果日期为空，设置为今天
  if (!newDate) {
    valuationDate.value = getTodayDateString();
    return;
  }

  // 确保日期格式是 YYYY-MM-DD
  if (!/^\d{4}-\d{2}-\d{2}$/.test(newDate)) {
    try {
      const date = new Date(newDate);
      if (!isNaN(date.getTime())) {
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        valuationDate.value = `${year}-${month}-${day}`;
      } else {
        valuationDate.value = getTodayDateString();
      }
    } catch (e) {
      console.error('日期格式化错误:', e);
      valuationDate.value = getTodayDateString();
    }
  }
});



// 当股票代码输入框内容变化时触发
function handleStockCodeInput() {
  console.log('QuickValuationCard: 股票代码输入变化为:', stockCode.value);
  if (stockCode.value) {
    // 立即通知父组件股票代码变化
    emit('stock-code-change', stockCode.value);
  }
}

function submitForm() {
  console.log('QuickValuationCard: submitForm被调用');
  if (stockCode.value) {
    // 确保日期格式正确
    let dateValue = valuationDate.value;

    if (!dateValue) {
      dateValue = getTodayDateString();
    }

    console.log('QuickValuationCard: 发出submit事件，stockCode:', stockCode.value, 'valuationDate:', dateValue);
    emit('submit', stockCode.value, dateValue);
  } else {
    console.error('QuickValuationCard: 股票代码为空，无法提交');
  }
}


</script>
