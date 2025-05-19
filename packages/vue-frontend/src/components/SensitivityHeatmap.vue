<template>
  <div class="sensitivity-heatmap-container">
    <div v-if="isLoading" class="flex items-center justify-center h-60">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      <span class="ml-2 text-muted-foreground">加载中...</span>
    </div>

    <div
      v-else-if="!sensitivityData || !sensitivityData.result_tables || !Object.keys(sensitivityData.result_tables || {}).length"
      class="flex items-center justify-center h-60 text-muted-foreground flex-col">
      <div>没有敏感性分析数据可显示</div>
      <pre v-if="sensitivityData"
        class="text-xs mt-2 text-left max-w-full overflow-auto">{{ JSON.stringify(sensitivityData, null, 2) }}</pre>
    </div>

    <div v-else>
      <div class="mb-4 flex flex-wrap gap-2">
        <Button v-for="metric in availableMetrics" :key="metric.key"
          :variant="selectedMetric === metric.key ? 'default' : 'outline'" @click="selectedMetric = metric.key"
          size="sm">
          {{ metric.label }}
        </Button>
      </div>

      <div class="flex flex-col md:flex-row gap-4 w-full overflow-hidden">
        <!-- 热力图 -->
        <div class="flex-1 min-h-[300px] w-full max-w-full" ref="heatmapContainer"></div>

        <!-- 控制面板 -->
        <div class="w-full md:w-64 space-y-4 bg-muted/20 p-3 rounded-md">
          <h4 class="text-sm font-medium">调整参数</h4>

          <div class="space-y-2">
            <label class="text-xs text-muted-foreground">{{ rowParamLabel }}</label>
            <Slider :model-value="rowParamValue"
              @update:model-value="(val: number | number[]) => updateRowParam(Number(val))" :min="rowParamMin"
              :max="rowParamMax" :step="rowParamStep" class="my-6" />
            <div class="text-xs text-right">{{ formatParamValue(rowParamValue, sensitivityData.row_parameter) }}</div>
          </div>

          <div class="space-y-2">
            <label class="text-xs text-muted-foreground">{{ colParamLabel }}</label>
            <Slider :model-value="colParamValue"
              @update:model-value="(val: number | number[]) => updateColParam(Number(val))" :min="colParamMin"
              :max="colParamMax" :step="colParamStep" class="my-6" />
            <div class="text-xs text-right">{{ formatParamValue(colParamValue, sensitivityData.column_parameter) }}
            </div>
          </div>

          <div class="pt-4 border-t border-border">
            <h4 class="text-sm font-medium mb-2">导出</h4>
            <div class="flex flex-col gap-2">
              <Button @click="exportToCSV" variant="outline" size="sm">
                <DownloadIcon class="w-4 h-4 mr-1" /> 导出CSV
              </Button>
              <Button @click="exportImage" variant="outline" size="sm">
                <ImageIcon class="w-4 h-4 mr-1" /> 导出图片
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { DownloadIcon, ImageIcon } from 'lucide-vue-next';
import * as echarts from 'echarts';
import type { ApiSensitivityAnalysisResult } from '@shared-types/index';

const props = defineProps<{
  sensitivityData: ApiSensitivityAnalysisResult | null;
  isLoading?: boolean;
}>();

// 图表容器引用
const heatmapContainer = ref<HTMLElement | null>(null);
let chart: echarts.ECharts | null = null;

// 当前选中的指标
const selectedMetric = ref<string>('value_per_share');

// 参数值
const rowParamValue = ref<number>(0);
const colParamValue = ref<number>(0);

// 可用指标列表
const availableMetrics = computed(() => {
  if (!props.sensitivityData?.result_tables) return [];

  return Object.keys(props.sensitivityData.result_tables).map(key => {
    const label = getMetricLabel(key);
    return { key, label };
  });
});

// 参数标签
const rowParamLabel = computed(() => getParamLabel(props.sensitivityData?.row_parameter || ''));
const colParamLabel = computed(() => getParamLabel(props.sensitivityData?.column_parameter || ''));

// 参数范围
const rowParamMin = computed(() => {
  if (!props.sensitivityData?.row_values?.length) return 0;
  return Number(props.sensitivityData.row_values[0]);
});

const rowParamMax = computed(() => {
  if (!props.sensitivityData?.row_values?.length) return 1;
  return Number(props.sensitivityData.row_values[props.sensitivityData.row_values.length - 1]);
});

const rowParamStep = computed(() => {
  if (!props.sensitivityData?.row_values?.length || props.sensitivityData.row_values.length < 2) return 0.01;
  return Number(props.sensitivityData.row_values[1]) - Number(props.sensitivityData.row_values[0]);
});

const colParamMin = computed(() => {
  if (!props.sensitivityData?.column_values?.length) return 0;
  return Number(props.sensitivityData.column_values[0]);
});

const colParamMax = computed(() => {
  if (!props.sensitivityData?.column_values?.length) return 1;
  return Number(props.sensitivityData.column_values[props.sensitivityData.column_values.length - 1]);
});

const colParamStep = computed(() => {
  if (!props.sensitivityData?.column_values?.length || props.sensitivityData.column_values.length < 2) return 0.01;
  return Number(props.sensitivityData.column_values[1]) - Number(props.sensitivityData.column_values[0]);
});

// 初始化参数值
watch(() => props.sensitivityData, (newData) => {
  if (newData?.row_values?.length && newData?.column_values?.length) {
    // 设置为中间值
    const rowMiddleIndex = Math.floor(newData.row_values.length / 2);
    const colMiddleIndex = Math.floor(newData.column_values.length / 2);

    rowParamValue.value = Number(newData.row_values[rowMiddleIndex]);
    colParamValue.value = Number(newData.column_values[colMiddleIndex]);

    // 如果有可用指标，选择第一个
    if (availableMetrics.value.length > 0) {
      selectedMetric.value = availableMetrics.value[0].key;
    }
  }
}, { immediate: true });

// 监听选中指标和参数值变化，更新图表
watch([selectedMetric, () => props.sensitivityData], () => {
  renderHeatmap();
}, { immediate: true });

// 渲染热力图
const renderHeatmap = () => {
  if (!heatmapContainer.value || !props.sensitivityData || !props.sensitivityData.result_tables) return;

  if (!chart) {
    chart = echarts.init(heatmapContainer.value, undefined, {
      renderer: 'canvas',
      useDirtyRect: false
    });
  }

  const data = props.sensitivityData;
  const tableData = data.result_tables[selectedMetric.value];

  if (!tableData) return;

  // 准备数据
  const rowValues = data.row_values.map(v => formatParamValue(Number(v), data.row_parameter));
  const colValues = data.column_values.map(v => formatParamValue(Number(v), data.column_parameter));

  // 转换为热力图数据
  const heatmapData: [number, number, number | string][] = [];
  tableData.forEach((row, i) => {
    row.forEach((value, j) => {
      if (value !== null) {
        heatmapData.push([j, i, Number(value)]);
      }
    });
  });

  // 高亮当前选中的参数值
  const rowIndex = data.row_values.findIndex(v => Number(v) === rowParamValue.value);
  const colIndex = data.column_values.findIndex(v => Number(v) === colParamValue.value);

  // 设置图表选项
  const option: echarts.EChartsOption = {
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const rowValue = rowValues[params.data[1]];
        const colValue = colValues[params.data[0]];
        const value = formatMetricValue(params.data[2], selectedMetric.value);

        return `${rowParamLabel.value}: ${rowValue}<br>${colParamLabel.value}: ${colValue}<br>${getMetricLabel(selectedMetric.value)}: ${value}`;
      }
    },
    grid: {
      height: '70%',
      top: '10%',
      containLabel: true,
      left: '3%',
      right: '4%'
    },
    xAxis: {
      type: 'category',
      data: colValues,
      name: colParamLabel.value,
      nameLocation: 'middle',
      nameGap: 30,
      splitArea: {
        show: true
      }
    },
    yAxis: {
      type: 'category',
      data: rowValues,
      name: rowParamLabel.value,
      nameLocation: 'middle',
      nameGap: 40,
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: Math.min(...heatmapData.map(item => Number(item[2]))),
      max: Math.max(...heatmapData.map(item => Number(item[2]))),
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      formatter: (value: number) => formatMetricValue(value, selectedMetric.value)
    } as any,
    series: [{
      name: getMetricLabel(selectedMetric.value),
      type: 'heatmap',
      data: heatmapData,
      label: {
        show: false
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      markPoint: rowIndex >= 0 && colIndex >= 0 ? {
        data: [
          { coord: [colIndex, rowIndex], symbol: 'circle', symbolSize: 10 }
        ]
      } : undefined
    }] as any
  };

  chart.setOption(option);
};

// 更新参数值
const updateRowParam = (value: number) => {
  rowParamValue.value = value;
  renderHeatmap();
};

const updateColParam = (value: number) => {
  colParamValue.value = value;
  renderHeatmap();
};

// 格式化函数
const getMetricLabel = (metricKey: string): string => {
  const labels: Record<string, string> = {
    'value_per_share': '每股价值',
    'enterprise_value': '企业价值',
    'equity_value': '股权价值',
    'tv_ev_ratio': '终值/企业价值比',
    'dcf_implied_diluted_pe': 'DCF隐含PE',
    'ev_ebitda': 'EV/EBITDA'
  };

  return labels[metricKey] || metricKey;
};

const getParamLabel = (paramKey: string): string => {
  const labels: Record<string, string> = {
    'wacc': 'WACC',
    'exit_multiple': '退出乘数',
    'terminal_growth_rate': '永续增长率',
    'perpetual_growth_rate': '永续增长率'
  };

  return labels[paramKey] || paramKey;
};

const formatParamValue = (value: number, paramType: string | undefined): string => {
  if (paramType === 'wacc' || paramType === 'terminal_growth_rate' || paramType === 'perpetual_growth_rate') {
    return `${(value * 100).toFixed(2)}%`;
  } else if (paramType === 'exit_multiple') {
    return `${value.toFixed(1)}x`;
  }
  return value.toFixed(2);
};

const formatMetricValue = (value: number | string, metricType: string): string => {
  const numValue = Number(value);

  if (metricType === 'value_per_share') {
    return numValue.toFixed(2);
  } else if (metricType === 'enterprise_value' || metricType === 'equity_value') {
    return `${(numValue / 1e8).toFixed(2)}亿`;
  } else if (metricType === 'tv_ev_ratio') {
    return `${(numValue * 100).toFixed(2)}%`;
  } else if (metricType === 'dcf_implied_diluted_pe' || metricType === 'ev_ebitda') {
    return `${numValue.toFixed(2)}x`;
  }

  return String(value);
};

// 导出功能
const exportToCSV = () => {
  if (!props.sensitivityData || !props.sensitivityData.result_tables || !selectedMetric.value) return;

  const data = props.sensitivityData;
  const tableData = data.result_tables[selectedMetric.value];

  if (!tableData) return;

  // 创建CSV内容
  let csvContent = `${colParamLabel.value}/${rowParamLabel.value},${data.column_values.join(',')}\n`;

  tableData.forEach((row, i) => {
    csvContent += `${data.row_values[i]},${row.join(',')}\n`;
  });

  // 创建下载链接
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `敏感性分析_${getMetricLabel(selectedMetric.value)}.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const exportImage = () => {
  if (!chart) return;

  const url = chart.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff'
  });

  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `敏感性分析_${getMetricLabel(selectedMetric.value)}.png`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// 生命周期钩子
onMounted(() => {
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (chart) {
    chart.dispose();
    chart = null;
  }
});

const handleResize = () => {
  if (chart) {
    chart.resize();
  }
};
</script>
