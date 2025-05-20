<template>
    <div class="space-y-6">

        <Tabs defaultValue="basic" class="w-full">
            <TabsList class="grid w-full grid-cols-3">
                <TabsTrigger value="basic">基础指标</TabsTrigger>
                <TabsTrigger value="financial">财务指标</TabsTrigger>
                <TabsTrigger value="growth">成长指标</TabsTrigger>
            </TabsList>

            <!-- 基础指标 -->
            <TabsContent value="basic" class="space-y-4 pt-2">
                <div class="filter-group space-y-2">
                    <label for="pe-min" class="text-sm font-medium text-muted-foreground">市盈率 (PE) 范围:</label>
                    <div class="flex items-center space-x-2">
                        <Input type="number" id="pe-min" v-model="filters.peMin" placeholder="最小PE" />
                        <span class="text-muted-foreground">-</span>
                        <Input type="number" id="pe-max" v-model="filters.peMax" placeholder="最大PE" />
                    </div>
                </div>

                <div class="filter-group space-y-2">
                    <label for="pb-min" class="text-sm font-medium text-muted-foreground">市净率 (PB) 范围:</label>
                    <div class="flex items-center space-x-2">
                        <Input type="number" id="pb-min" v-model="filters.pbMin" placeholder="最小PB" />
                        <span class="text-muted-foreground">-</span>
                        <Input type="number" id="pb-max" v-model="filters.pbMax" placeholder="最大PB" />
                    </div>
                </div>

                <div class="filter-group space-y-2">
                    <label for="market-cap-min" class="text-sm font-medium text-muted-foreground">市值 (亿元) 范围:</label>
                    <div class="flex items-center space-x-2">
                        <Input type="number" id="market-cap-min" v-model="filters.marketCapMin" placeholder="最小市值" />
                        <span class="text-muted-foreground">-</span>
                        <Input type="number" id="market-cap-max" v-model="filters.marketCapMax" placeholder="最大市值" />
                    </div>
                </div>

                <div class="filter-group space-y-2">
                    <label for="dividend-yield-min" class="text-sm font-medium text-muted-foreground">股息率 (%)
                        范围:</label>
                    <div class="flex items-center space-x-2">
                        <Input type="number" id="dividend-yield-min" v-model="filters.dividendYieldMin"
                            placeholder="最小股息率" />
                        <span class="text-muted-foreground">-</span>
                        <Input type="number" id="dividend-yield-max" v-model="filters.dividendYieldMax"
                            placeholder="最大股息率" />
                    </div>
                </div>

                <div class="filter-group space-y-2">
                    <label class="text-sm font-medium text-muted-foreground">行业选择:</label>
                    <Select v-model="filters.industry">
                        <SelectTrigger>
                            <SelectValue placeholder="选择行业" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">全部行业</SelectItem>
                            <SelectItem v-for="industry in industries" :key="industry" :value="industry">
                                {{ industry }}
                            </SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </TabsContent>

            <!-- 财务指标 -->
            <TabsContent value="financial" class="space-y-4 pt-2">
                <div class="filter-group space-y-2">
                    <label for="roe-min" class="text-sm font-medium text-muted-foreground">ROE (%) 范围:</label>
                    <div class="flex items-center space-x-2">
                        <Input type="number" id="roe-min" v-model="filters.roeMin" placeholder="最小ROE" />
                        <span class="text-muted-foreground">-</span>
                        <Input type="number" id="roe-max" v-model="filters.roeMax" placeholder="最大ROE" />
                    </div>
                </div>

                <div class="filter-group space-y-2">
                    <label for="gross-margin-min" class="text-sm font-medium text-muted-foreground">毛利率 (%) 范围:</label>
                    <div class="flex items-center space-x-2">
                        <Input type="number" id="gross-margin-min" v-model="filters.grossMarginMin"
                            placeholder="最小毛利率" />
                        <span class="text-muted-foreground">-</span>
                        <Input type="number" id="gross-margin-max" v-model="filters.grossMarginMax"
                            placeholder="最大毛利率" />
                    </div>
                </div>

                <div class="filter-group space-y-2">
                    <label for="net-margin-min" class="text-sm font-medium text-muted-foreground">净利率 (%) 范围:</label>
                    <div class="flex items-center space-x-2">
                        <Input type="number" id="net-margin-min" v-model="filters.netMarginMin" placeholder="最小净利率" />
                        <span class="text-muted-foreground">-</span>
                        <Input type="number" id="net-margin-max" v-model="filters.netMarginMax" placeholder="最大净利率" />
                    </div>
                </div>

                <div class="filter-group space-y-2">
                    <label for="debt-to-equity-min" class="text-sm font-medium text-muted-foreground">资产负债率 (%)
                        范围:</label>
                    <div class="flex items-center space-x-2">
                        <Input type="number" id="debt-to-equity-min" v-model="filters.debtToEquityMin"
                            placeholder="最小资产负债率" />
                        <span class="text-muted-foreground">-</span>
                        <Input type="number" id="debt-to-equity-max" v-model="filters.debtToEquityMax"
                            placeholder="最大资产负债率" />
                    </div>
                </div>
            </TabsContent>

            <!-- 成长指标 -->
            <TabsContent value="growth" class="space-y-4 pt-2">
                <div class="filter-group space-y-2">
                    <label for="revenue-growth-min" class="text-sm font-medium text-muted-foreground">营收增长率 (%)
                        范围:</label>
                    <div class="flex items-center space-x-2">
                        <Input type="number" id="revenue-growth-min" v-model="filters.revenueGrowthMin"
                            placeholder="最小增长率" />
                        <span class="text-muted-foreground">-</span>
                        <Input type="number" id="revenue-growth-max" v-model="filters.revenueGrowthMax"
                            placeholder="最大增长率" />
                    </div>
                </div>

                <div class="filter-group space-y-2">
                    <label for="profit-growth-min" class="text-sm font-medium text-muted-foreground">净利润增长率 (%)
                        范围:</label>
                    <div class="flex items-center space-x-2">
                        <Input type="number" id="profit-growth-min" v-model="filters.profitGrowthMin"
                            placeholder="最小增长率" />
                        <span class="text-muted-foreground">-</span>
                        <Input type="number" id="profit-growth-max" v-model="filters.profitGrowthMax"
                            placeholder="最大增长率" />
                    </div>
                </div>

                <div class="filter-group space-y-2">
                    <label for="eps-growth-min" class="text-sm font-medium text-muted-foreground">EPS增长率 (%) 范围:</label>
                    <div class="flex items-center space-x-2">
                        <Input type="number" id="eps-growth-min" v-model="filters.epsGrowthMin" placeholder="最小增长率" />
                        <span class="text-muted-foreground">-</span>
                        <Input type="number" id="eps-growth-max" v-model="filters.epsGrowthMax" placeholder="最大增长率" />
                    </div>
                </div>

                <div class="filter-group space-y-2">
                    <label class="text-sm font-medium text-muted-foreground">增长期间:</label>
                    <Select v-model="filters.growthPeriod">
                        <SelectTrigger>
                            <SelectValue placeholder="选择期间" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="yoy">同比 (YoY)</SelectItem>
                            <SelectItem value="3yr">3年复合 (CAGR)</SelectItem>
                            <SelectItem value="5yr">5年复合 (CAGR)</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </TabsContent>
        </Tabs>

        <div class="flex flex-col gap-2">
            <div class="flex flex-col sm:flex-row gap-2">
                <Button @click="applyFilters" variant="default" class="w-full">
                    <span class="flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="mr-1">
                            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                        </svg>
                        应用筛选
                    </span>
                </Button>
                <Button @click="resetFilters" variant="outline" class="w-full">
                    <span class="flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="mr-1">
                            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                            <path d="M3 3v5h5" />
                        </svg>
                        重置
                    </span>
                </Button>
            </div>
            <div class="flex flex-col sm:flex-row gap-2">
                <Button @click="saveFilters" variant="outline" class="w-full">
                    <span class="flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="mr-1">
                            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                            <polyline points="17 21 17 13 7 13 7 21" />
                            <polyline points="7 3 7 8 15 8" />
                        </svg>
                        保存条件
                    </span>
                </Button>
                <Button @click="updateData" :disabled="isUpdatingData" variant="secondary" class="w-full">
                    <span class="flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="mr-1" :class="{ 'animate-spin': isUpdatingData }">
                            <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
                            <path d="M21 3v5h-5" />
                        </svg>
                        {{ isUpdatingData ? '正在更新...' : '更新基础数据' }}
                    </span>
                </Button>
            </div>
        </div>

        <div v-if="savedFilters.length > 0" class="pt-2">
            <h5 class="text-sm font-medium text-muted-foreground mb-2">已保存的筛选条件:</h5>
            <div class="flex flex-wrap gap-2">
                <Badge v-for="(filter, index) in savedFilters" :key="index" variant="outline" class="cursor-pointer"
                    @click="loadSavedFilter(index)">
                    {{ filter.name }}
                    <Button variant="ghost" size="icon" class="h-4 w-4 ml-1 p-0" @click.stop="deleteSavedFilter(index)">
                        <XIcon class="h-3 w-3" />
                    </Button>
                </Badge>
            </div>
        </div>

        <p v-if="dataStatus" class="text-sm text-muted-foreground mt-2">{{ dataStatus }}</p>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { XIcon } from 'lucide-vue-next';

export interface ScreenerFilters {
    // 基础指标
    peMin: number | string | undefined;
    peMax: number | string | undefined;
    pbMin: number | string | undefined;
    pbMax: number | string | undefined;
    marketCapMin: number | string | undefined;
    marketCapMax: number | string | undefined;
    dividendYieldMin: number | string | undefined;
    dividendYieldMax: number | string | undefined;
    industry: string;

    // 财务指标
    roeMin: number | string | undefined;
    roeMax: number | string | undefined;
    grossMarginMin: number | string | undefined;
    grossMarginMax: number | string | undefined;
    netMarginMin: number | string | undefined;
    netMarginMax: number | string | undefined;
    debtToEquityMin: number | string | undefined;
    debtToEquityMax: number | string | undefined;

    // 成长指标
    revenueGrowthMin: number | string | undefined;
    revenueGrowthMax: number | string | undefined;
    profitGrowthMin: number | string | undefined;
    profitGrowthMax: number | string | undefined;
    epsGrowthMin: number | string | undefined;
    epsGrowthMax: number | string | undefined;
    growthPeriod: string;
}

// 初始化筛选条件
const filters = reactive<ScreenerFilters>({
    // 基础指标
    peMin: '',
    peMax: '',
    pbMin: '',
    pbMax: '',
    marketCapMin: '',
    marketCapMax: '',
    dividendYieldMin: '',
    dividendYieldMax: '',
    industry: 'all',

    // 财务指标
    roeMin: '',
    roeMax: '',
    grossMarginMin: '',
    grossMarginMax: '',
    netMarginMin: '',
    netMarginMax: '',
    debtToEquityMin: '',
    debtToEquityMax: '',

    // 成长指标
    revenueGrowthMin: '',
    revenueGrowthMax: '',
    profitGrowthMin: '',
    profitGrowthMax: '',
    epsGrowthMin: '',
    epsGrowthMax: '',
    growthPeriod: 'yoy',
});

// 行业列表
const industries = ref<string[]>([
    '银行', '保险', '证券', '房地产', '建筑建材',
    '电子', '计算机', '通信', '医药生物', '食品饮料',
    '家用电器', '纺织服装', '汽车', '机械设备', '电气设备',
    '公用事业', '交通运输', '商业贸易', '农林牧渔', '采掘',
    '化工', '钢铁', '有色金属', '传媒', '综合'
]);

// 状态变量
const isUpdatingData = ref(false);
const dataStatus = ref('');

// 保存的筛选条件
interface SavedFilter {
    name: string;
    filters: ScreenerFilters;
}

const savedFilters = ref<SavedFilter[]>([]);

// 从本地存储加载保存的筛选条件
onMounted(() => {
    const savedFiltersStr = localStorage.getItem('stockScreenerSavedFilters');
    if (savedFiltersStr) {
        try {
            savedFilters.value = JSON.parse(savedFiltersStr);
        } catch (e) {
            console.error('Failed to parse saved filters:', e);
        }
    }
});

// 事件
const emit = defineEmits(['apply-filters', 'update-data']);

// 应用筛选条件
const applyFilters = () => {
    const activeFilters = Object.entries(filters).reduce((acc, [key, value]) => {
        if (value !== null && value !== undefined) {
            // Ensure type compatibility
            const typedKey = key as keyof ScreenerFilters;
            acc[typedKey] = value as any; // Using 'any' to bypass the type check since we know the values are compatible
        }
        return acc;
    }, {} as Partial<ScreenerFilters>);
    emit('apply-filters', activeFilters);
};

// 重置筛选条件
const resetFilters = () => {
    Object.keys(filters).forEach(key => {
        const typedKey = key as keyof ScreenerFilters;
        if (key === 'growthPeriod') {
            filters[typedKey] = 'yoy';
        } else {
            filters[typedKey] = '';
        }
    });
};

// 保存筛选条件
const saveFilters = () => {
    // 检查是否有有效的筛选条件
    const hasActiveFilters = Object.values(filters).some(value => value !== null && value !== undefined);
    if (!hasActiveFilters) {
        dataStatus.value = '没有可保存的筛选条件';
        setTimeout(() => {
            dataStatus.value = '';
        }, 3000);
        return;
    }

    // 提示用户输入名称
    const name = prompt('请输入筛选条件名称:', '筛选条件 ' + (savedFilters.value.length + 1));
    if (!name) return;

    // 保存筛选条件
    const newFilter: SavedFilter = {
        name,
        filters: JSON.parse(JSON.stringify(filters)) // 深拷贝
    };

    savedFilters.value.push(newFilter);
    localStorage.setItem('stockScreenerSavedFilters', JSON.stringify(savedFilters.value));

    dataStatus.value = '筛选条件已保存';
    setTimeout(() => {
        dataStatus.value = '';
    }, 3000);
};

// 加载保存的筛选条件
const loadSavedFilter = (index: number) => {
    const savedFilter = savedFilters.value[index];
    if (!savedFilter) return;

    // 应用保存的筛选条件
    Object.keys(savedFilter.filters).forEach(key => {
        const typedKey = key as keyof ScreenerFilters;
        // 确保类型兼容性
        if (typedKey === 'growthPeriod') {
            filters[typedKey] = savedFilter.filters[typedKey] as string;
        } else {
            // 对于数字字段和其他字段，确保它们是字符串或数字
            filters[typedKey] = savedFilter.filters[typedKey] as any; // 使用any类型绕过类型检查
        }
    });

    dataStatus.value = `已加载筛选条件: ${savedFilter.name}`;
    setTimeout(() => {
        dataStatus.value = '';
    }, 3000);
};

// 删除保存的筛选条件
const deleteSavedFilter = (index: number) => {
    savedFilters.value.splice(index, 1);
    localStorage.setItem('stockScreenerSavedFilters', JSON.stringify(savedFilters.value));

    dataStatus.value = '筛选条件已删除';
    setTimeout(() => {
        dataStatus.value = '';
    }, 3000);
};

// 更新数据
const updateData = async () => {
    isUpdatingData.value = true;
    dataStatus.value = '正在更新数据，请稍候...';
    try {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate async
        dataStatus.value = '数据更新成功！';
        emit('update-data');
    } catch (error) {
        console.error('Error updating data:', error);
        dataStatus.value = '数据更新失败，请检查网络或联系管理员。';
    } finally {
        isUpdatingData.value = false;
    }
};
</script>

<style scoped>
/* All previous scoped styles are removed as Tailwind utility classes are used for styling.
   If specific non-utility styles are needed, they can be added here,
   but the goal is to rely on Tailwind and shadcn/ui components as much as possible. */
</style>
