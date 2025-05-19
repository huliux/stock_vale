<template>
  <div class="mt-6">
    <div class="flex justify-between items-center mb-3">
      <h4 class="text-lg font-semibold text-foreground">Chart 测试表格</h4>
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
    <div v-else>
      <!-- 图表视图 -->
      <div class="mt-4 space-y-6">
        <div class="border border-border rounded-lg p-4 bg-card">
          <h3 class="text-md font-medium mb-4">市盈率分布</h3>
          <div class="h-80" ref="chartContainer"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ApiScreenedStock } from '@shared-types/index';
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as echarts from 'echarts';

interface Props {
  results: ApiScreenedStock[];
  isLoading: boolean;
  error: string | null;
  hasSearched: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits(['go-to-valuation']);

// 图表容器引用
const chartContainer = ref<HTMLElement | null>(null);
let chart: echarts.ECharts | null = null;

// 渲染图表
const renderChart = () => {
  if (!chartContainer.value || props.results.length === 0) return;
  
  if (!chart) {
    chart = echarts.init(chartContainer.value);
  }
  
  const peData = props.results
    .filter(stock => stock.pe_ttm !== null && stock.pe_ttm !== undefined)
    .map(stock => stock.pe_ttm as number);
  
  if (peData.length > 0) {
    // 创建PE分布直方图
    const bins = 10;
    const max = Math.max(...peData);
    const min = Math.min(...peData);
    const binSize = (max - min) / bins;
    
    const histogramData = Array(bins).fill(0);
    const binLabels = [];
    
    for (let i = 0; i < bins; i++) {
      const binStart = min + i * binSize;
      const binEnd = binStart + binSize;
      binLabels.push(`${binStart.toFixed(1)}-${binEnd.toFixed(1)}`);
      
      peData.forEach(value => {
        if (value >= binStart && value < binEnd) {
          histogramData[i]++;
        }
      });
    }
    
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} 只股票'
      },
      xAxis: {
        type: 'category',
        data: binLabels,
        axisLabel: {
          interval: 0,
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '股票数量'
      },
      series: [{
        name: '市盈率分布',
        type: 'bar',
        data: histogramData,
        itemStyle: {
          color: '#10b981'
        }
      }]
    };
    
    chart.setOption(option);
  }
};

// 处理窗口大小变化
const handleResize = () => {
  if (chart) chart.resize();
};

// 监听结果变化
watch(() => props.results, () => {
  if (props.results.length > 0) {
    // 等待DOM更新后渲染图表
    setTimeout(() => {
      renderChart();
    }, 100);
  }
}, { deep: true });

// 生命周期钩子
onMounted(() => {
  window.addEventListener('resize', handleResize);
  if (props.results.length > 0) {
    renderChart();
  }
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (chart) {
    chart.dispose();
    chart = null;
  }
});
</script>
