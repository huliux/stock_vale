<template>
  <div class="sensitivity-display-container">
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
      <div class="mb-4">
        <h3 class="text-lg font-semibold">敏感性分析结果</h3>
        <p class="text-sm text-muted-foreground">
          分析 {{ getParamLabel(sensitivityData.row_parameter) }} 和 {{ getParamLabel(sensitivityData.column_parameter) }}
          对估值的影响
        </p>
      </div>

      <div class="grid grid-cols-1 gap-4">
        <Card v-for="(table, metric) in sensitivityData.result_tables" :key="metric">
          <CardHeader>
            <CardTitle>{{ getMetricLabel(metric) }}</CardTitle>
            <CardDescription>
              {{ getParamLabel(sensitivityData.row_parameter) }} (行) vs {{
                getParamLabel(sensitivityData.column_parameter) }} (列)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div class="w-full overflow-hidden">
              <div class="w-full max-w-full">
                <table class="w-full border-collapse table-fixed">
                  <thead>
                    <tr>
                      <th class="p-2 border bg-muted font-medium text-center break-words w-[15%]">{{
                        getParamLabel(sensitivityData.row_parameter) }} \\ {{
                          getParamLabel(sensitivityData.column_parameter) }}</th>
                      <th v-for="(colValue, colIndex) in sensitivityData.column_values" :key="colIndex"
                        class="p-2 border bg-muted font-medium text-center break-words"
                        :style="{ width: `${85 / sensitivityData.column_values.length}%` }">
                        {{ formatParamValue(colValue, sensitivityData.column_parameter) }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, rowIndex) in table" :key="rowIndex">
                      <th class="p-2 border bg-muted font-medium text-center break-words">
                        {{ formatParamValue(sensitivityData.row_values[rowIndex], sensitivityData.row_parameter) }}
                      </th>
                      <td v-for="(value, colIndex) in row" :key="colIndex" class="p-2 border text-center break-words"
                        :class="getCellClass(value, table)">
                        {{ formatMetricValue(value, metric) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

// 使用更通用的接口，兼容 ApiSensitivityAnalysisResult
interface SensitivityData {
  row_parameter: string;
  column_parameter: string;
  row_values: any[]; // 可以是 number[] 或 string[]
  column_values: any[]; // 可以是 number[] 或 string[]
  result_tables: {
    [key: string]: any[][];
  };
}

const props = defineProps<{
  sensitivityData: SensitivityData | null;
  isLoading?: boolean;
}>();

// 获取参数标签
const getParamLabel = (param: string): string => {
  const labels: Record<string, string> = {
    'wacc': 'WACC',
    'exit_multiple': '退出乘数',
    'terminal_growth_rate': '永续增长率',
    'revenue_growth_rate': '收入增长率',
    'operating_margin': '营业利润率'
  };
  return labels[param] || param;
};

// 获取指标标签
const getMetricLabel = (metric: string | number): string => {
  const metricStr = String(metric);
  const labels: Record<string, string> = {
    'value_per_share': '每股价值',
    'enterprise_value': '企业价值',
    'dcf_implied_diluted_pe': '隐含市盈率'
  };
  return labels[metricStr] || metricStr;
};

// 格式化参数值
const formatParamValue = (value: number | string, param: string): string => {
  const numValue = Number(value);

  if (isNaN(numValue)) {
    return String(value);
  }

  if (param === 'wacc' || param === 'terminal_growth_rate' || param === 'revenue_growth_rate' || param === 'operating_margin') {
    return `${(numValue * 100).toFixed(1)}%`;
  }
  return numValue.toString();
};

// 格式化指标值
const formatMetricValue = (value: number | string, metric: string | number): string => {
  const numValue = Number(value);
  const metricStr = String(metric);

  if (isNaN(numValue)) {
    return String(value);
  }

  if (metricStr === 'value_per_share') {
    return `¥${numValue.toFixed(2)}`;
  } else if (metricStr === 'enterprise_value') {
    return formatLargeNumber(numValue);
  } else if (metricStr === 'dcf_implied_diluted_pe') {
    return numValue.toFixed(1);
  }
  return numValue.toString();
};

// 格式化大数字
const formatLargeNumber = (num: number): string => {
  if (num >= 1e12) {
    return `¥${(num / 1e12).toFixed(2)}万亿`;
  } else if (num >= 1e8) {
    return `¥${(num / 1e8).toFixed(2)}亿`;
  } else if (num >= 1e4) {
    return `¥${(num / 1e4).toFixed(2)}万`;
  }
  return `¥${num.toFixed(2)}`;
};

// 获取单元格样式
const getCellClass = (value: number | string, table: any[][]): string => {
  const numValue = Number(value);
  if (isNaN(numValue)) return '';

  // 将表格中的所有值转换为数字
  const allValues = table.flat().map(Number).filter(v => !isNaN(v));
  if (allValues.length === 0) return '';

  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const range = max - min;

  if (range === 0) return '';

  const normalized = (numValue - min) / range;

  if (normalized < 0.2) return 'bg-red-50 text-red-800';
  if (normalized < 0.4) return 'bg-orange-50 text-orange-800';
  if (normalized < 0.6) return 'bg-yellow-50 text-yellow-800';
  if (normalized < 0.8) return 'bg-green-50 text-green-800';
  return 'bg-emerald-50 text-emerald-800';
};
</script>
