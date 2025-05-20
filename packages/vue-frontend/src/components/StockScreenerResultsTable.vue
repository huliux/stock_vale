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
                            <SelectItem value="total_mv">市值</SelectItem>
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
            <div class="flex flex-col">
                <div class="flex items-center">
                    <AlertCircleIcon class="h-4 w-4 mr-2" />
                    <span class="font-medium">加载数据时出错</span>
                </div>
                <p class="mt-2 text-sm">{{ error }}</p>
                <Button @click="emit('retry')" variant="outline" class="mt-3 self-start">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                        class="mr-1">
                        <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
                        <path d="M21 3v5h-5" />
                    </svg>
                    重试
                </Button>
            </div>
        </div>
        <div v-else-if="results.length === 0 && !hasSearched"
            class="p-4 border rounded-md mt-4 bg-sky-50 text-sky-700 border-sky-200">
            <div class="flex flex-col">
                <div class="flex items-center">
                    <InfoIcon class="h-4 w-4 mr-2" />
                    <span class="font-medium">请设置筛选条件并点击"应用筛选"</span>
                </div>
                <p class="mt-2 text-sm">您可以设置市盈率、市净率、市值等条件来筛选股票，然后点击"应用筛选"按钮查看结果。</p>
            </div>
        </div>
        <div v-else-if="results.length === 0 && hasSearched"
            class="p-4 border rounded-md mt-4 bg-yellow-50 text-yellow-700 border-yellow-200">
            <div class="flex flex-col">
                <div class="flex items-center">
                    <AlertTriangleIcon class="h-4 w-4 mr-2" />
                    <span class="font-medium">没有找到符合条件的股票</span>
                </div>
                <p class="mt-2 text-sm">请尝试放宽筛选条件，例如扩大市盈率或市值范围，或者移除部分限制条件。</p>
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
                                市盈率(PE_TTM)
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
                            <div class="flex items-center cursor-pointer" @click="setSortField('total_mv')">
                                总市值(万元)
                                <ChevronUpIcon v-if="sortField === 'total_mv' && sortOrder === 'asc'"
                                    class="h-4 w-4 ml-1" />
                                <ChevronDownIcon v-if="sortField === 'total_mv' && sortOrder === 'desc'"
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
                        <td class="p-4 align-middle">{{ formatNumber(stock.total_mv !== null && stock.total_mv !==
                            undefined ? stock.total_mv : stock.market_cap_billion ? stock.market_cap_billion * 10000 :
                            null)
                            }}</td>
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

            <!-- 分页控件 -->
            <div v-if="props.results.length > 0"
                class="p-4 border-t border-border bg-muted/10 flex justify-between items-center">
                <div class="text-sm text-muted-foreground">
                    共 {{ props.total || props.results.length }} 条记录
                </div>
                <div class="flex items-center gap-2">
                    <Button @click="prevPage" variant="outline" size="sm" :disabled="currentPage <= 1">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="mr-1">
                            <polyline points="15 18 9 12 15 6"></polyline>
                        </svg>
                        上一页
                    </Button>
                    <span class="text-sm">第 {{ currentPage }} 页</span>
                    <Button @click="nextPage" variant="outline" size="sm" :disabled="!hasMorePages">
                        下一页
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="ml-1">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                    </Button>
                </div>
            </div>
        </div>

        <!-- 卡片视图 -->
        <div v-else-if="viewMode === 'cards'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
            <div v-for="stock in sortedStocks" :key="stock.ts_code"
                class="border border-border rounded-lg p-4 bg-card hover:shadow-md transition-shadow duration-200">
                <div class="flex justify-between items-start mb-3">
                    <div>
                        <h3 class="text-lg font-medium">{{ stock.name }}</h3>
                        <p class="text-sm text-muted-foreground">{{ stock.ts_code }}</p>
                    </div>
                    <div class="flex items-center">
                        <input type="checkbox" v-model="selectedStocks[stock.ts_code]"
                            class="rounded border-gray-300 text-primary focus:ring-primary mr-2" />
                        <Button variant="ghost" size="icon" @click="showStockDetails(stock)" title="查看详情">
                            <EyeIcon class="h-4 w-4" />
                        </Button>
                    </div>
                </div>

                <!-- 主要指标 -->
                <div class="grid grid-cols-2 gap-3 mb-4">
                    <div class="bg-muted/30 p-2 rounded">
                        <p class="text-xs text-muted-foreground">最新价格</p>
                        <p class="font-medium">{{ formatNumber(stock.close) }}</p>
                    </div>
                    <div class="bg-muted/30 p-2 rounded">
                        <p class="text-xs text-muted-foreground">市盈率(PE)</p>
                        <p class="font-medium">{{ formatNumber(stock.pe) }}</p>
                    </div>
                    <div class="bg-muted/30 p-2 rounded">
                        <p class="text-xs text-muted-foreground">市盈率(TTM)</p>
                        <p class="font-medium">{{ formatNumber(stock.pe_ttm) }}</p>
                    </div>
                    <div class="bg-muted/30 p-2 rounded">
                        <p class="text-xs text-muted-foreground">市净率(PB)</p>
                        <p class="font-medium">{{ formatNumber(stock.pb) }}</p>
                    </div>
                </div>

                <!-- 行业和市值信息 -->
                <div class="mb-4">
                    <div class="bg-muted/30 p-2 rounded mb-2">
                        <p class="text-xs text-muted-foreground">总市值(万元)</p>
                        <p class="font-medium">{{ formatNumber(stock.total_mv !== null && stock.total_mv !== undefined ?
                            stock.total_mv : stock.market_cap_billion ? stock.market_cap_billion * 10000 : null) }}</p>
                    </div>
                    <div class="flex gap-2 flex-wrap">
                        <Badge variant="outline" class="bg-primary/10">
                            {{ stock.industry || '未知行业' }}
                        </Badge>
                        <Badge variant="outline" class="bg-secondary/10">
                            {{ stock.area || '未知地区' }}
                        </Badge>
                    </div>
                </div>

                <!-- 操作按钮 -->
                <div class="flex justify-between">
                    <Button variant="outline" size="sm" @click="goToValuation(stock.ts_code)">
                        <CalculatorIcon class="h-3 w-3 mr-1" />
                        估值分析
                    </Button>
                    <Button variant="outline" size="sm" @click="emit('add-to-watchlist', [stock.ts_code])">
                        <PlusCircleIcon class="h-3 w-3 mr-1" />
                        加入观察
                    </Button>
                </div>
            </div>
        </div>

        <!-- 图表视图 -->
        <div v-else-if="viewMode === 'chart'" class="mt-4 space-y-6">
            <!-- 图表控制区 -->
            <div class="flex justify-between items-center mb-4">
                <div class="flex items-center gap-2">
                    <label for="chart-field" class="text-sm text-muted-foreground">图表指标:</label>
                    <Select v-model="chartField" id="chart-field" class="w-32">
                        <SelectTrigger>
                            <SelectValue placeholder="选择指标" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="pe">市盈率(PE)</SelectItem>
                            <SelectItem value="pe_ttm">市盈率TTM</SelectItem>
                            <SelectItem value="pb">市净率(PB)</SelectItem>
                            <SelectItem value="ps">市销率(PS)</SelectItem>
                            <SelectItem value="ps_ttm">市销率TTM</SelectItem>
                            <SelectItem value="close">最新价格</SelectItem>
                            <SelectItem value="total_mv">总市值(万元)</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
                <div class="flex items-center gap-2">
                    <label for="chart-type" class="text-sm text-muted-foreground">图表类型:</label>
                    <Select v-model="chartType" id="chart-type" class="w-32">
                        <SelectTrigger>
                            <SelectValue placeholder="选择图表类型" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="bar">柱状图</SelectItem>
                            <SelectItem value="scatter">散点图</SelectItem>
                            <SelectItem value="pie">饼图</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <!-- 主图表 -->
            <div class="border border-border rounded-lg p-4 bg-card">
                <h3 class="text-md font-medium mb-4">{{ chartTitle }}</h3>
                <div class="h-80" ref="chartContainer"></div>
            </div>

            <!-- 图表说明 -->
            <div class="text-sm text-muted-foreground mt-2">
                <p>提示: 您可以通过上方的选择器更改图表指标和图表类型。图表展示了筛选结果中各股票的{{ chartFieldName }}分布情况。</p>
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
                                    <span class="text-sm text-muted-foreground">股票代码:</span>
                                    <span class="text-sm">{{ selectedStock.ts_code }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">股票名称:</span>
                                    <span class="text-sm">{{ selectedStock.name || 'N/A' }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">最新价格:</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.close) }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">行业:</span>
                                    <span class="text-sm">{{ selectedStock.industry || '未知' }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">实控人企业性质:</span>
                                    <span class="text-sm">{{ selectedStock.act_ent_type || '未知' }}</span>
                                </div>
                            </div>
                        </div>

                        <div>
                            <h4 class="text-sm font-medium text-muted-foreground mb-1">估值指标</h4>
                            <div class="space-y-2">
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">市盈率(PE):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.pe) }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">市盈率TTM(PE_TTM):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.pe_ttm) }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">市净率(PB):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.pb) }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">市销率(PS):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.ps) }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">市销率TTM(PS_TTM):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.ps_ttm) }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">总市值(万元):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.total_mv !== null &&
                                        selectedStock.total_mv !== undefined ? selectedStock.total_mv :
                                        selectedStock.market_cap_billion ? selectedStock.market_cap_billion * 10000 :
                                            null)
                                    }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4 mt-4">
                        <div>
                            <h4 class="text-sm font-medium text-muted-foreground mb-1">交易指标</h4>
                            <div class="space-y-2">
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">交易日期:</span>
                                    <span class="text-sm">{{ selectedStock.trade_date || '未知' }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">换手率(%):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.turnover_rate) }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">换手率(自由流通股)(%):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.turnover_rate_f) }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">量比:</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.volume_ratio) }}</span>
                                </div>
                            </div>
                        </div>

                        <div>
                            <h4 class="text-sm font-medium text-muted-foreground mb-1">股本信息</h4>
                            <div class="space-y-2">
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">总股本(万股):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.total_share) }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">流通股本(万股):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.float_share) }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">自由流通股本(万):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.free_share) }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">流通市值(万元):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.circ_mv) }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 gap-4 mt-4">
                        <div>
                            <h4 class="text-sm font-medium text-muted-foreground mb-1">股息信息</h4>
                            <div class="space-y-2">
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">股息率(%):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.dv_ratio) }}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-muted-foreground">股息率TTM(%):</span>
                                    <span class="text-sm">{{ formatNumber(selectedStock.dv_ttm) }}</span>
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
import type { ExtendedApiScreenedStock } from '@/types/index';
import { ref, computed, onMounted, onUnmounted, watch, watchEffect } from 'vue';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog as DialogRoot, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ToggleGroup as ToggleGroupRoot, ToggleGroupItem } from '@/components/ui/toggle-group';
import {
    ArrowUpIcon, ArrowDownIcon, TableIcon, LayoutGridIcon, BarChartIcon,
    DownloadIcon, ChevronUpIcon, ChevronDownIcon, Loader2Icon, AlertCircleIcon,
    InfoIcon, AlertTriangleIcon, CalculatorIcon, PlusCircleIcon, EyeIcon
} from 'lucide-vue-next';
import * as echarts from 'echarts';

interface Props {
    results: ExtendedApiScreenedStock[];
    isLoading: boolean;
    error: string | null;
    hasSearched: boolean;
    total?: number; // 总记录数，用于分页
    page?: number; // 当前页码
    pageSize?: number; // 每页记录数
}

const props = defineProps<Props>();
const emit = defineEmits(['go-to-valuation', 'batch-valuation', 'add-to-watchlist', 'page-change', 'retry']);

// 排序和视图状态
const sortField = ref<string>('name');
const sortOrder = ref<'asc' | 'desc'>('asc');
const viewMode = ref<'table' | 'cards' | 'chart'>('table');

// 图表相关状态
const chartField = ref<string>('pe');
const chartType = ref<'bar' | 'scatter' | 'pie'>('bar');
const chartFieldName = computed(() => {
    const fieldNames: Record<string, string> = {
        'pe': '市盈率(PE)',
        'pe_ttm': '市盈率TTM',
        'pb': '市净率(PB)',
        'ps': '市销率(PS)',
        'ps_ttm': '市销率TTM',
        'close': '最新价格',
        'total_mv': '总市值(万元)'
    };
    return fieldNames[chartField.value] || chartField.value;
});

// 分页状态
const currentPage = ref(props.page || 1);
const pageSize = ref(props.pageSize || 20);
const hasMorePages = computed(() => {
    if (props.total !== undefined) {
        return currentPage.value * pageSize.value < props.total;
    }
    // 如果没有提供总数，则假设如果当前页面结果数等于页面大小，可能还有更多页面
    return props.results.length >= pageSize.value;
});

// 选择状态
const selectedStocks = ref<Record<string, boolean>>({});
const selectAll = ref(false);
const selectedStock = ref<ExtendedApiScreenedStock | null>(null);

// 图表容器引用
const chartContainer = ref<HTMLElement | null>(null);
let mainChart: echarts.ECharts | null = null;

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
    const chartTypeNames: Record<string, string> = {
        'bar': '柱状图',
        'scatter': '散点图',
        'pie': '饼图'
    };

    return `${chartFieldName.value} ${chartTypeNames[chartType.value] || ''} 分布`;
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

const showStockDetails = (stock: ExtendedApiScreenedStock) => {
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
        .filter(([, selected]) => selected) // Using comma to skip the unused variable
        .map(([code]) => code);

    if (selectedCodes.length > 0) {
        if (selectedCodes.length > 5) {
            // 限制批量估值的数量，避免一次处理太多
            if (!confirm(`您选择了 ${selectedCodes.length} 只股票进行批量估值，数量较多可能会影响性能。是否继续？`)) {
                return;
            }
        }

        // 发出批量估值事件，由父组件处理
        emit('batch-valuation', selectedCodes);
    }
};

const addToWatchlist = () => {
    const selectedCodes = Object.entries(selectedStocks.value)
        .filter(([, selected]) => selected) // Using comma to skip the unused variable
        .map(([code]) => code);

    if (selectedCodes.length > 0) {
        // 发出添加到观察列表事件，由父组件处理
        emit('add-to-watchlist', selectedCodes);
    }
};

const exportResults = () => {
    const stocks = sortedStocks.value;
    if (!stocks || stocks.length === 0) return;

    // 创建CSV内容
    const headers = ['股票代码', '股票名称', '最新价格', '市盈率', '市净率', '总市值(万元)'];
    let csvContent = headers.join(',') + '\n';

    stocks.forEach(stock => {
        const row = [
            stock.ts_code,
            stock.name,
            formatNumber(stock.close),
            formatNumber(stock.pe),
            formatNumber(stock.pb),
            formatNumber(stock.total_mv !== null && stock.total_mv !== undefined ? stock.total_mv : stock.market_cap_billion ? stock.market_cap_billion * 10000 : null)
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

// 分页函数
const prevPage = () => {
    if (currentPage.value > 1) {
        currentPage.value--;
        emit('page-change', currentPage.value);
    }
};

const nextPage = () => {
    if (hasMorePages.value) {
        currentPage.value++;
        emit('page-change', currentPage.value);
    }
};

// 格式化数字
const formatNumber = (value: number | string | null | undefined, suffix = '') => {
    if (value === null || value === undefined || value === 'N/A') return 'N/A';

    // 处理字符串类型
    if (typeof value === 'string') {
        if (isNaN(Number(value))) return value;
        value = Number(value);
    }

    // 处理数字类型
    if (typeof value === 'number') {
        // 检查是否为特殊浮点数值
        if (!isFinite(value) || isNaN(value)) return 'N/A';

        // 对于总市值，如果是万元单位或大数值，格式化为更易读的形式
        if (suffix === '万元' || (suffix === '' && value > 10000)) {
            if (value >= 100000000) { // 大于10亿
                return (value / 100000000).toFixed(2) + '亿' + suffix;
            } else if (value >= 10000) { // 大于1万
                return (value / 10000).toFixed(2) + '亿' + suffix;
            }
        }

        return value.toFixed(2) + suffix;
    }

    return 'N/A';
};

// 渲染图表
const renderCharts = () => {
    if (viewMode.value !== 'chart') return;

    // 主图表
    if (chartContainer.value) {
        if (!mainChart) {
            mainChart = echarts.init(chartContainer.value);
        }

        const data = sortedStocks.value.map(stock => {
            const value = stock[chartField.value as keyof ApiScreenedStock] as number;
            return {
                name: stock.name || stock.ts_code,
                code: stock.ts_code,
                value: value
            };
        }).filter(item => {
            // 过滤掉 null、undefined、NaN 和 Infinity 值
            return item.value !== null &&
                item.value !== undefined &&
                isFinite(item.value) &&
                !isNaN(item.value);
        });

        // 根据图表类型创建不同的配置
        // 初始化一个默认的空选项对象
        let option: Record<string, unknown> = {};

        if (chartType.value === 'bar') {
            option = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: { type: 'shadow' },
                    formatter: function (params: unknown) {
                        // 使用类型断言处理 params
                        const paramArray = params as Array<{
                            name: string;
                            dataIndex: number;
                            value: number;
                        }>;

                        if (!paramArray || paramArray.length === 0) return '';

                        const item = paramArray[0];
                        const stockCode = data[item.dataIndex]?.code || '';
                        const value = item.value;

                        // 检查值是否为有效数字
                        const formattedValue = isFinite(value) && !isNaN(value)
                            ? value.toFixed(2)
                            : 'N/A';

                        return `${item.name} (${stockCode})<br/>${chartFieldName.value}: ${formattedValue}`;
                    }
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '10%',
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
                    name: chartFieldName.value
                },
                series: [{
                    name: chartFieldName.value,
                    type: 'bar',
                    data: data.map(item => item.value),
                    itemStyle: {
                        color: '#3b82f6'
                    }
                }]
            };
        } else if (chartType.value === 'scatter') {
            // 散点图需要两个维度的数据，我们使用索引作为X轴
            option = {
                tooltip: {
                    trigger: 'item',
                    formatter: function (params: unknown) {
                        // 使用类型断言处理 params
                        const param = params as { data: { name: string, code: string, value: number } };

                        if (!param || !param.data) return '';

                        const { name, code, value } = param.data;

                        // 检查值是否为有效数字
                        const formattedValue = isFinite(value) && !isNaN(value)
                            ? value.toFixed(2)
                            : 'N/A';

                        return `${name} (${code})<br/>${chartFieldName.value}: ${formattedValue}`;
                    }
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
                    name: chartFieldName.value
                },
                series: [{
                    name: chartFieldName.value,
                    type: 'scatter',
                    data: data.map(item => ({
                        name: item.name,
                        code: item.code,
                        value: item.value
                    })),
                    symbolSize: 10,
                    itemStyle: {
                        color: '#3b82f6'
                    }
                }]
            };
        } else if (chartType.value === 'pie') {
            option = {
                tooltip: {
                    trigger: 'item',
                    formatter: function (params: unknown) {
                        // 使用类型断言处理 params
                        const param = params as {
                            name: string,
                            data: { code: string },
                            value: number,
                            percent: number
                        };

                        if (!param || !param.data) return '';

                        const { name, data, value, percent } = param;

                        // 检查值是否为有效数字
                        const formattedValue = isFinite(value) && !isNaN(value)
                            ? value.toFixed(2)
                            : 'N/A';

                        return `${name} (${data.code})<br/>${chartFieldName.value}: ${formattedValue} (${percent.toFixed(2)}%)`;
                    }
                },
                legend: {
                    type: 'scroll',
                    orient: 'vertical',
                    right: 10,
                    top: 20,
                    bottom: 20,
                },
                series: [{
                    name: chartFieldName.value,
                    type: 'pie',
                    radius: '55%',
                    center: ['40%', '50%'],
                    data: data.map(item => ({
                        name: item.name,
                        code: item.code,
                        value: item.value
                    })),
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }]
            };
        }

        mainChart.setOption(option);
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

// 监听图表字段和类型变化，更新图表
watch([chartField, chartType], () => {
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

// 监听页码属性变化
watch(() => props.page, (newPage) => {
    if (newPage !== undefined && newPage !== currentPage.value) {
        currentPage.value = newPage;
    }
});

// 处理窗口大小变化
const handleResize = () => {
    if (mainChart) mainChart.resize();
};

// 添加窗口大小变化监听
onMounted(() => {
    window.addEventListener('resize', handleResize);
});

// 移除窗口大小变化监听
onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
    if (mainChart) mainChart.dispose();
});
</script>

<style scoped>
/* All scoped styles should have been removed. */
/* This block is intentionally empty. */
</style>
