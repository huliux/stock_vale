<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import StockResearch from '@/components/Research/StockResearch.vue';
import AppSidebar from '@/components/AppSidebar.vue';
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar';

const route = useRoute();

// 股票代码和名称
const stockCode = ref('');
const stockName = ref('');
const initialStockCode = ref<string | null>(null);

// 从URL参数中获取股票代码和名称
const updateFromRoute = () => {
  const codeFromQuery = route.query.code as string;
  const nameFromQuery = route.query.name as string;

  if (codeFromQuery) {
    stockCode.value = codeFromQuery;
    initialStockCode.value = codeFromQuery;

    if (nameFromQuery) {
      stockName.value = nameFromQuery;
    }
    // 如果没有名称参数，可以在这里添加调用API获取股票名称的逻辑
  }
};

// 组件挂载时设置初始股票代码和名称
onMounted(updateFromRoute);

// 监听路由变化
watch(route, () => {
  updateFromRoute();
});
</script>

<template>
  <SidebarProvider :style="{
    '--sidebar-width': '350px', // Width for the second, wider sidebar panel
  }">
    <AppSidebar :is-loading="false" :initial-stock-code="initialStockCode" />
    <SidebarInset>
      <header class="sticky top-0 z-10 flex h-14 shrink-0 items-center justify-between border-b bg-background p-4">
        <div class="flex items-center gap-2">
          <SidebarTrigger class="-ml-1" />
          <h1 class="text-xl font-semibold">深度研究</h1>
        </div>
      </header>
      <main class="flex-1 overflow-auto p-4">
        <StockResearch :stockCode="stockCode" :stockName="stockName" />
      </main>
    </SidebarInset>
  </SidebarProvider>
</template>
