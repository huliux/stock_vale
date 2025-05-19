<template>
  <div class="container py-10 space-y-10">
    <div>
      <h1 class="text-3xl font-bold tracking-tight">敏感性分析测试</h1>
      <p class="text-muted-foreground mt-2">
        这个页面用于测试敏感性分析组件是否正常工作。
      </p>
    </div>

    <div class="grid grid-cols-1 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>敏感性分析热力图</CardTitle>
          <CardDescription>使用模拟数据测试热力图组件</CardDescription>
        </CardHeader>
        <CardContent>
          <SensitivityHeatmap :sensitivity-data="mockSensitivityData" :is-loading="false" />
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import SensitivityHeatmap from '@/components/SensitivityHeatmap.vue';

// 模拟敏感性分析数据
const mockSensitivityData = {
  row_parameter: 'wacc',
  column_parameter: 'exit_multiple',
  row_values: [0.08, 0.09, 0.10, 0.11, 0.12],
  column_values: [8, 10, 12, 14, 16],
  result_tables: {
    value_per_share: [
      [25.6, 30.2, 34.8, 39.4, 44.0],
      [22.1, 26.1, 30.1, 34.1, 38.1],
      [19.2, 22.7, 26.2, 29.7, 33.2],
      [16.8, 19.8, 22.9, 25.9, 28.9],
      [14.7, 17.4, 20.1, 22.7, 25.4]
    ],
    enterprise_value: [
      [256000000000, 302000000000, 348000000000, 394000000000, 440000000000],
      [221000000000, 261000000000, 301000000000, 341000000000, 381000000000],
      [192000000000, 227000000000, 262000000000, 297000000000, 332000000000],
      [168000000000, 198000000000, 229000000000, 259000000000, 289000000000],
      [147000000000, 174000000000, 201000000000, 227000000000, 254000000000]
    ],
    dcf_implied_diluted_pe: [
      [12.8, 15.1, 17.4, 19.7, 22.0],
      [11.1, 13.1, 15.1, 17.1, 19.1],
      [9.6, 11.4, 13.1, 14.9, 16.6],
      [8.4, 9.9, 11.5, 13.0, 14.5],
      [7.4, 8.7, 10.1, 11.4, 12.7]
    ]
  }
};
</script>
