<template>
    <div class="mt-6">
        <div class="flex justify-between items-center mb-3">
            <h4 class="text-lg font-semibold text-foreground">筛选结果</h4>
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
                <Button @click="toggleSortOrder" variant="outline" size="sm" class="h-9">
                    <ArrowUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 mr-1" />
                    <ArrowDownIcon v-else class="h-4 w-4 mr-1" />
                    {{ sortOrder === 'asc' ? '升序' : '降序' }}
                </Button>
                <div class="flex items-center gap-1 ml-4">
                    <label for="view-mode" class="text-sm text-muted-foreground">视图:</label>
                    <ToggleGroupRoot type="single" v-model="viewMode" variant="outline" class="h-9">
                        <ToggleGroupItem value="table" class="px-3">
                            <TableIcon class="h-4 w-4" />
                        </ToggleGroupItem>
                        <ToggleGroupItem value="cards" class="px-3">
                            <LayoutGridIcon class="h-4 w-4" />
                        </ToggleGroupItem>
                        <ToggleGroupItem value="chart" class="px-3">
                            <BarChartIcon class="h-4 w-4" />
                        </ToggleGroupItem>
                    </ToggleGroupRoot>
                </div>
                <Button @click="exportResults" variant="outline" size="sm" class="h-9 ml-2">
                    <DownloadIcon class="h-4 w-4 mr-1" />
                    导出
                </Button>
            </div>
        </div>

        <div v-if="isLoading" class="p-4 border rounded-md mt-4 bg-blue-50 text-blue-700 border-blue-200">
            <div class="flex items-center">
                <Loader2Icon class="h-4 w-4 mr-2 animate-spin" />
                正在加载数据...
            </div>
        </div>
        <div v-else-if="error" class="p-4 border rounded-md mt-4 bg-red-50 text-red-700 border-red-200">
            <div class="flex items-center">
                <AlertCircleIcon class="h-4 w-4 mr-2" />
                {{ error }}
            </div>
        </div>
        <div v-else-if="results.length === 0 && !hasSearched"
            class="p-4 border rounded-md mt-4 bg-sky-50 text-sky-700 border-sky-200">
            <div class="flex items-center">
                <InfoIcon class="h-4 w-4 mr-2" />
                请设置筛选条件并点击"应用筛选"。
            </div>
        </div>
        <div v-else-if="results.length === 0 && hasSearched"
            class="p-4 border rounded-md mt-4 bg-yellow-50 text-yellow-700 border-yellow-200">
            <div class="flex items-center">
                <AlertTriangleIcon class="h-4 w-4 mr-2" />
                没有找到符合条件的股票。
            </div>
        </div>

        <!-- 表格视图 -->
        <div v-else-if="viewMode === 'table'" class="overflow-x-auto rounded-md border border-border">
            <table class="w-full text-sm caption-bottom">
                <thead class="[&_tr]:border-b [&_tr]:border-border">
                    <tr class="hover:bg-muted/50 data-[state=selected]:bg-muted">
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                            <div class="flex items-center">
                                <input type="checkbox" v-model="selectAll" @change="toggleSelectAll"
                                    class="rounded border-gray-300 text-primary focus:ring-primary" />
                            </div>
                        </th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                            <div class="flex items-center cursor-pointer" @click="setSortField('ts_code')">
                                股票代码
                                <ChevronUpIcon v-if="sortField === 'ts_code' && sortOrder === 'asc'"
                                    class="h-4 w-4 ml-1" />
                                <ChevronDownIcon v-if="sortField === 'ts_code' && sortOrder === 'desc'"
                                    class="h-4 w-4 ml-1" />
                            </div>
                        </th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                            <div class="flex items-center cursor-pointer" @click="setSortField('name')">
                                股票名称
                                <ChevronUpIcon v-if="sortField === 'name' && sortOrder === 'asc'"
                                    class="h-4 w-4 ml-1" />
                                <ChevronDownIcon v-if="sortField === 'name' && sortOrder === 'desc'"
                                    class="h-4 w-4 ml-1" />
                            </div>
                        </th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                            <div class="flex items-center cursor-pointer" @click="setSortField('close')">
                                最新价格
                                <ChevronUpIcon v-if="sortField === 'close' && sortOrder === 'asc'"
                                    class="h-4 w-4 ml-1" />
                                <ChevronDownIcon v-if="sortField === 'close' && sortOrder === 'desc'"
                                    class="h-4 w-4 ml-1" />
                            </div>
                        </th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                            <div class="flex items-center cursor-pointer" @click="setSortField('pe_ttm')">
                                市盈率(PE)
                                <ChevronUpIcon v-if="sortField === 'pe_ttm' && sortOrder === 'asc'"
                                    class="h-4 w-4 ml-1" />
                                <ChevronDownIcon v-if="sortField === 'pe_ttm' && sortOrder === 'desc'"
                                    class="h-4 w-4 ml-1" />
                            </div>
                        </th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                            <div class="flex items-center cursor-pointer" @click="setSortField('pb')">
                                市净率(PB)
                                <ChevronUpIcon v-if="sortField === 'pb' && sortOrder === 'asc'" class="h-4 w-4 ml-1" />
                                <ChevronDownIcon v-if="sortField === 'pb' && sortOrder === 'desc'"
                                    class="h-4 w-4 ml-1" />
                            </div>
                        </th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                            <div class="flex items-center cursor-pointer" @click="setSortField('market_cap_billion')">
                                总市值(亿元)
                                <ChevronUpIcon v-if="sortField === 'market_cap_billion' && sortOrder === 'asc'"
                                    class="h-4 w-4 ml-1" />
                                <ChevronDownIcon v-if="sortField === 'market_cap_billion' && sortOrder === 'desc'"
                                    class="h-4 w-4 ml-1" />
                            </div>
                        </th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">操作</th>
                    </tr>
                </thead>
                <tbody class="[&_tr:last-child]:border-0">
                    <tr v-for="stock in sortedStocks" :key="stock.ts_code"
                        class="border-b border-border transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                        <td class="p-4 align-middle">
                            <input type="checkbox" v-model="selectedStocks[stock.ts_code]"
                                class="rounded border-gray-300 text-primary focus:ring-primary" />
                        </td>
                        <td class="p-4 align-middle">{{ stock.ts_code }}</td>
                        <td class="p-4 align-middle">{{ stock.name }}</td>
                        <td class="p-4 align-middle">{{ formatNumber(stock.close) }}</td>
                        <td class="p-4 align-middle">{{ formatNumber(stock.pe_ttm) }}</td>
                        <td class="p-4 align-middle">{{ formatNumber(stock.pb) }}</td>
                        <td class="p-4 align-middle">{{ formatNumber(stock.market_cap_billion) }}</td>
                        <td class="p-4 align-middle">
                            <div class="flex items-center gap-2">
                                <Button @click="goToValuation(stock.ts_code)" variant="default" size="sm">估值</Button>
                                <Button @click="showStockDetails(stock)" variant="outline" size="sm">详情</Button>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>

            <!-- 批量操作 -->
            <div v-if="hasSelectedStocks" class="p-4 border-t border-border bg-muted/20">
                <div class="flex items-center justify-between">
                    <div class="text-sm text-muted-foreground">已选择 {{ selectedCount }} 只股票</div>
                    <div class="flex items-center gap-2">
                        <Button @click="batchValuation" variant="default" size="sm">批量估值</Button>
                        <Button @click="addToWatchlist" variant="outline" size="sm">添加到观察列表</Button>
                        <Button @click="clearSelection" variant="ghost" size="sm">清除选择</Button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 卡片视图 -->
        <div v-else-if="viewMode === 'cards'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
            <div v-for="stock in sortedStocks" :key="stock.ts_code"
                class="border border-border rounded-lg p-4 bg-card hover:shadow-md transition-shadow">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <h3 class="font-medium text-foreground">{{ stock.name }}</h3>
                        <p class="text-sm text-muted-foreground">{{ stock.ts_code }}</p>
                    </div>
                    <input type="checkbox" v-model="selectedStocks[stock.ts_code]"
                        class="rounded border-gray-300 text-primary focus:ring-primary" />
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
                    <Button @click="showStockDetails(stock)" variant="outline" size="sm">详情</Button>
                </div>
            </div>
        </div>

        <!-- 图表视图 -->
        <div v-else-if="viewMode === 'chart'" class="mt-4 space-y-6">
            <div class="border border-border rounded-lg p-4 bg-card">
                <h3 class="text-md font-medium mb-4">{{ chartTitle }}</h3>
                <div class="h-80" ref="chartContainer"></div>
            </div>

            <div class="flex flex-wrap gap-4">
                <div class="flex-1 min-w-[300px] border border-border rounded-lg p-4 bg-card">
                    <h3 class="text-md font-medium mb-4">市盈率分布</h3>
                    <div class="h-60" ref="peChartContainer"></div>
                </div>
                <div class="flex-1 min-w-[300px] border border-border rounded-lg p-4 bg-card">
                    <h3 class="text-md font-medium mb-4">市净率分布</h3>
                    <div class="h-60" ref="pbChartContainer"></div>
                </div>
            </div>
        </div>

        <!-- 股票详情对话框 -->
        <DialogRoot :open="!!selectedStock" @update:open="closeStockDetails">
            <DialogContent class="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle v-if="selectedStock">{{ selectedStock.name }} ({{ selectedStock.ts_code }})
                    </DialogTitle>
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
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">行业:</span>
                                    <span class="text-sm">{{ selectedStock.industry || 'N/A' }}</span>
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
        </DialogRoot>
    </div>
</template>

<script setup lang="ts">
import type { ApiScreenedStock } from '@shared-types/index';
import { ref, computed, onMounted, onUnmounted, watch, watchEffect } from 'vue';
import { Button } from '@/components/ui/button';
import { Dialog as DialogRoot, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ToggleGroup as ToggleGroupRoot, ToggleGroupItem } from '@/components/ui/toggle-group';
import {
    ArrowUpIcon, ArrowDownIcon, TableIcon, LayoutGridIcon, BarChartIcon,
    DownloadIcon, ChevronUpIcon, ChevronDownIcon, Loader2Icon, AlertCircleIcon,
    InfoIcon, AlertTriangleIcon
} from 'lucide-vue-next';
import * as echarts from 'echarts';

interface Props {
    results: ApiScreenedStock[];
    isLoading: boolean;
    error: string | null;
    hasSearched: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits(['go-to-valuation']);

// 排序和视图状态
const sortField = ref<string>('name');
const sortOrder = ref<'asc' | 'desc'>('asc');
const viewMode = ref<'table' | 'cards' | 'chart'>('table');

// 选择状态
const selectedStocks = ref<Record<string, boolean>>({});
const selectAll = ref(false);
const selectedStock = ref<ApiScreenedStock | null>(null);

// 图表容器引用
const chartContainer = ref<HTMLElement | null>(null);
const peChartContainer = ref<HTMLElement | null>(null);
const pbChartContainer = ref<HTMLElement | null>(null);
let mainChart: echarts.ECharts | null = null;
let peChart: echarts.ECharts | null = null;
let pbChart: echarts.ECharts | null = null;

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

const hasSelectedStocks = computed(() => {
    return Object.values(selectedStocks.value).some(selected => selected);
});

const selectedCount = computed(() => {
    return Object.values(selectedStocks.value).filter(selected => selected).length;
});

const chartTitle = computed(() => {
    const fieldNames: Record<string, string> = {
        'pe_ttm': '市盈率',
        'pb': '市净率',
        'market_cap_billion': '市值',
        'close': '价格'
    };

    return `${fieldNames[sortField.value] || sortField.value} 分布`;
});

// 方法
const setSortField = (field: string) => {
    if (sortField.value === field) {
        toggleSortOrder();
    } else {
        sortField.value = field;
        sortOrder.value = 'asc';
    }
};

const toggleSortOrder = () => {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
};

const toggleSelectAll = () => {
    const newValue = selectAll.value;
    props.results.forEach(stock => {
        selectedStocks.value[stock.ts_code] = newValue;
    });
};

const clearSelection = () => {
    selectAll.value = false;
    selectedStocks.value = {};
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

const batchValuation = () => {
    const selectedCodes = Object.entries(selectedStocks.value)
        .filter(([_, selected]) => selected)
        .map(([code]) => code);

    if (selectedCodes.length > 0) {
        // 这里可以实现批量估值逻辑，例如打开一个新页面或对话框
        alert(`将对 ${selectedCodes.length} 只股票进行批量估值: ${selectedCodes.join(', ')}`);
    }
};

const addToWatchlist = () => {
    const selectedCodes = Object.entries(selectedStocks.value)
        .filter(([_, selected]) => selected)
        .map(([code]) => code);

    if (selectedCodes.length > 0) {
        // 这里可以实现添加到观察列表的逻辑
        alert(`已将 ${selectedCodes.length} 只股票添加到观察列表`);
    }
};

const exportResults = () => {
    const stocks = sortedStocks.value;
    if (!stocks || stocks.length === 0) return;

    // 创建CSV内容
    const headers = ['股票代码', '股票名称', '最新价格', '市盈率', '市净率', '总市值(亿元)'];
    let csvContent = headers.join(',') + '\n';

    stocks.forEach(stock => {
        const row = [
            stock.ts_code,
            stock.name,
            formatNumber(stock.close),
            formatNumber(stock.pe_ttm),
            formatNumber(stock.pb),
            formatNumber(stock.market_cap_billion)
        ];
        csvContent += row.join(',') + '\n';
    });

    // 创建下载链接
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `股票筛选结果_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

// 格式化数字
const formatNumber = (value: number | null | undefined, suffix = '') => {
    if (value === null || value === undefined) return 'N/A';
    return value.toFixed(2) + suffix;
};

// 渲染图表
const renderCharts = () => {
    if (viewMode.value !== 'chart') return;

    // 主图表
    if (chartContainer.value) {
        if (!mainChart) {
            mainChart = echarts.init(chartContainer.value);
        }

        const data = sortedStocks.value.map(stock => ({
            name: stock.name,
            value: stock[sortField.value as keyof ApiScreenedStock] as number
        })).filter(item => item.value !== null && item.value !== undefined);

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: data.map(item => item.name),
                axisLabel: {
                    interval: 0,
                    rotate: 45
                }
            },
            yAxis: {
                type: 'value',
                name: chartTitle.value
            },
            series: [{
                name: chartTitle.value,
                type: 'bar',
                data: data.map(item => item.value),
                itemStyle: {
                    color: '#3b82f6'
                }
            }]
        };

        mainChart.setOption(option);
    }

    // PE分布图
    if (peChartContainer.value) {
        if (!peChart) {
            peChart = echarts.init(peChartContainer.value);
        }

        const peData = sortedStocks.value
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

            peChart.setOption(option);
        }
    }

    // PB分布图
    if (pbChartContainer.value) {
        if (!pbChart) {
            pbChart = echarts.init(pbChartContainer.value);
        }

        const pbData = sortedStocks.value
            .filter(stock => stock.pb !== null && stock.pb !== undefined)
            .map(stock => stock.pb as number);

        if (pbData.length > 0) {
            // 创建PB分布直方图
            const bins = 10;
            const max = Math.max(...pbData);
            const min = Math.min(...pbData);
            const binSize = (max - min) / bins;

            const histogramData = Array(bins).fill(0);
            const binLabels = [];

            for (let i = 0; i < bins; i++) {
                const binStart = min + i * binSize;
                const binEnd = binStart + binSize;
                binLabels.push(`${binStart.toFixed(1)}-${binEnd.toFixed(1)}`);

                pbData.forEach(value => {
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
                    name: '市净率分布',
                    type: 'bar',
                    data: histogramData,
                    itemStyle: {
                        color: '#f59e0b'
                    }
                }]
            };

            pbChart.setOption(option);
        }
    }
};

// 监听视图模式变化，渲染图表
watch(viewMode, (newMode) => {
    if (newMode === 'chart') {
        // 等待DOM更新后渲染图表
        setTimeout(() => {
            renderCharts();
        }, 100);
    }
});

// 监听排序字段和排序顺序变化，更新图表
watch([sortField, sortOrder], () => {
    if (viewMode.value === 'chart') {
        renderCharts();
    }
});

// 监听结果变化
watchEffect(() => {
    if (props.results && props.results.length > 0) {
        // 初始化选择状态
        const newSelectedStocks: Record<string, boolean> = {};
        props.results.forEach(stock => {
            newSelectedStocks[stock.ts_code] = selectedStocks.value[stock.ts_code] || false;
        });
        selectedStocks.value = newSelectedStocks;

        // 如果是图表视图，渲染图表
        if (viewMode.value === 'chart') {
            setTimeout(() => {
                renderCharts();
            }, 100);
        }
    } else {
        // 清空选择状态
        selectedStocks.value = {};
        selectAll.value = false;
    }
});

// 处理窗口大小变化
const handleResize = () => {
    if (mainChart) mainChart.resize();
    if (peChart) peChart.resize();
    if (pbChart) pbChart.resize();
};

// 生命周期钩子
onMounted(() => {
    window.addEventListener('resize', handleResize);
});

// 组件卸载时清理
onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
    if (mainChart) {
        mainChart.dispose();
        mainChart = null;
    }
    if (peChart) {
        peChart.dispose();
        peChart = null;
    }
    if (pbChart) {
        pbChart.dispose();
        pbChart = null;
    }
});
</script>

<style scoped>
/* 所有样式通过 Tailwind CSS 实现 */
</style>
