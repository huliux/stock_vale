<template>
    <div class="space-y-4 w-full max-w-full">

        <div class="space-y-3 pt-1">
            <div class="filter-group space-y-1">
                <label for="pe-min" class="text-sm font-medium text-muted-foreground">市盈率 (PE) 范围:</label>
                <div class="flex items-center gap-1">
                    <Input type="number" id="pe-min" v-model="filters.peMin" placeholder="最小PE"
                        class="min-w-0 flex-1" />
                    <span class="text-muted-foreground px-1">-</span>
                    <Input type="number" id="pe-max" v-model="filters.peMax" placeholder="最大PE"
                        class="min-w-0 flex-1" />
                </div>
            </div>

            <div class="filter-group space-y-1">
                <label for="pe-ttm-min" class="text-sm font-medium text-muted-foreground">市盈率TTM (PE_TTM) 范围:</label>
                <div class="flex items-center gap-1">
                    <Input type="number" id="pe-ttm-min" v-model="filters.peTtmMin" placeholder="最小PE_TTM"
                        class="min-w-0 flex-1" />
                    <span class="text-muted-foreground px-1">-</span>
                    <Input type="number" id="pe-ttm-max" v-model="filters.peTtmMax" placeholder="最大PE_TTM"
                        class="min-w-0 flex-1" />
                </div>
            </div>

            <div class="filter-group space-y-1">
                <label for="pb-min" class="text-sm font-medium text-muted-foreground">市净率 (PB) 范围:</label>
                <div class="flex items-center gap-1">
                    <Input type="number" id="pb-min" v-model="filters.pbMin" placeholder="最小PB"
                        class="min-w-0 flex-1" />
                    <span class="text-muted-foreground px-1">-</span>
                    <Input type="number" id="pb-max" v-model="filters.pbMax" placeholder="最大PB"
                        class="min-w-0 flex-1" />
                </div>
            </div>

            <div class="filter-group space-y-1">
                <label for="ps-min" class="text-sm font-medium text-muted-foreground">市销率 (PS) 范围:</label>
                <div class="flex items-center gap-1">
                    <Input type="number" id="ps-min" v-model="filters.psMin" placeholder="最小PS"
                        class="min-w-0 flex-1" />
                    <span class="text-muted-foreground px-1">-</span>
                    <Input type="number" id="ps-max" v-model="filters.psMax" placeholder="最大PS"
                        class="min-w-0 flex-1" />
                </div>
            </div>

            <div class="filter-group space-y-1">
                <label for="ps-ttm-min" class="text-sm font-medium text-muted-foreground">市销率TTM (PS_TTM) 范围:</label>
                <div class="flex items-center gap-1">
                    <Input type="number" id="ps-ttm-min" v-model="filters.psTtmMin" placeholder="最小PS_TTM"
                        class="min-w-0 flex-1" />
                    <span class="text-muted-foreground px-1">-</span>
                    <Input type="number" id="ps-ttm-max" v-model="filters.psTtmMax" placeholder="最大PS_TTM"
                        class="min-w-0 flex-1" />
                </div>
            </div>

            <div class="filter-group space-y-1">
                <label for="total-mv-min" class="text-sm font-medium text-muted-foreground">总市值 (亿元) 范围:</label>
                <div class="flex items-center gap-1">
                    <Input type="number" id="total-mv-min" v-model="filters.totalMvMin" placeholder="最小总市值"
                        class="min-w-0 flex-1" />
                    <span class="text-muted-foreground px-1">-</span>
                    <Input type="number" id="total-mv-max" v-model="filters.totalMvMax" placeholder="最大总市值"
                        class="min-w-0 flex-1" />
                </div>
                <p class="text-xs text-muted-foreground">输入单位为亿元</p>
            </div>

            <div class="filter-group space-y-1">
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

            <div class="filter-group space-y-1">
                <label class="text-sm font-medium text-muted-foreground">实控人企业性质:</label>
                <Select v-model="filters.actEntType">
                    <SelectTrigger>
                        <SelectValue placeholder="选择企业性质" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">全部</SelectItem>
                        <SelectItem value="中央国企">中央国企</SelectItem>
                        <SelectItem value="地方国企">地方国企</SelectItem>
                        <SelectItem value="民营企业">民营企业</SelectItem>
                        <SelectItem value="外资企业">外资企业</SelectItem>
                        <SelectItem value="集体企业">集体企业</SelectItem>
                        <SelectItem value="无">无</SelectItem>
                        <SelectItem value="未知">未知</SelectItem>
                    </SelectContent>
                </Select>
            </div>
        </div>

        <div class="flex flex-col gap-2">
            <!-- 主要操作按钮 -->
            <div class="grid grid-cols-2 gap-2">
                <Button @click="applyFilters" variant="default" class="w-full">
                    <span class="flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="mr-1">
                            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                        </svg>
                        应用筛选
                    </span>
                </Button>
                <Button @click="resetFilters" variant="outline" class="w-full">
                    <span class="flex items-center justify-center">
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

            <!-- 保存和更新按钮 -->
            <div class="grid grid-cols-2 gap-2">
                <Button @click="saveFilters" variant="outline" class="w-full">
                    <span class="flex items-center justify-center">
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
                <Button @click="updateData('all')" :disabled="isUpdatingData" variant="secondary" class="w-full">
                    <span class="flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="mr-1" :class="{ 'animate-spin': isUpdatingData }">
                            <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
                            <path d="M21 3v5h-5" />
                        </svg>
                        {{ isUpdatingData ? '更新中...' : '更新数据' }}
                    </span>
                </Button>
            </div>

            <!-- 更新特定类型数据按钮 -->
            <div class="grid grid-cols-2 gap-2">
                <Button @click="updateData('basic')" :disabled="isUpdatingData" variant="outline" size="sm">
                    更新基础数据
                </Button>
                <Button @click="updateData('daily')" :disabled="isUpdatingData" variant="outline" size="sm">
                    更新行情数据
                </Button>
            </div>
        </div>

        <div v-if="savedFilters.length > 0" class="pt-2">
            <h5 class="text-sm font-medium text-muted-foreground mb-2">已保存的筛选条件:</h5>
            <div class="flex flex-wrap gap-1">
                <Badge v-for="(filter, index) in savedFilters" :key="index" variant="outline"
                    class="cursor-pointer text-xs flex-shrink-0 max-w-full" @click="loadSavedFilter(index)">
                    <span class="truncate">{{ filter.name }}</span>
                    <Button variant="ghost" size="icon" class="h-4 w-4 ml-1 p-0 flex-shrink-0"
                        @click.stop="deleteSavedFilter(index)">
                        <XIcon class="h-3 w-3" />
                    </Button>
                </Badge>
            </div>
        </div>

        <!-- 数据状态指示器 -->
        <div v-if="dataStatus" class="text-sm p-2 rounded-md mt-2" :class="{
            'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400': dataStatus.includes('成功') || dataStatus.includes('完成'),
            'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400': dataStatus.includes('正在') || dataStatus.includes('请稍候'),
            'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400': dataStatus.includes('失败') || dataStatus.includes('错误')
        }">
            <div class="flex items-center">
                <!-- 成功图标 -->
                <svg v-if="dataStatus.includes('成功') || dataStatus.includes('完成')" xmlns="http://www.w3.org/2000/svg"
                    class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>

                <!-- 加载图标 -->
                <svg v-else-if="dataStatus.includes('正在') || dataStatus.includes('请稍候')"
                    class="animate-spin h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none"
                    viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                    </path>
                </svg>

                <!-- 错误图标 -->
                <svg v-else-if="dataStatus.includes('失败') || dataStatus.includes('错误')"
                    xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24"
                    stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>

                <span>{{ dataStatus }}</span>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { XIcon } from 'lucide-vue-next';

export interface ScreenerFilters {
    // 基础指标
    peMin: number | string | undefined;
    peMax: number | string | undefined;
    peTtmMin: number | string | undefined;
    peTtmMax: number | string | undefined;
    pbMin: number | string | undefined;
    pbMax: number | string | undefined;
    psMin: number | string | undefined;
    psMax: number | string | undefined;
    psTtmMin: number | string | undefined;
    psTtmMax: number | string | undefined;
    totalMvMin: number | string | undefined;
    totalMvMax: number | string | undefined;
    industry: string;
    actEntType: string;
}

// 定义组件属性
interface Props {
    isLoading?: boolean;
    dataUpdateStatus?: string;
}

const props = withDefaults(defineProps<Props>(), {
    isLoading: false,
    dataUpdateStatus: ''
});

// 初始化筛选条件
const filters = reactive<ScreenerFilters>({
    // 基础指标
    peMin: '',
    peMax: '',
    peTtmMin: '',
    peTtmMax: '',
    pbMin: '',
    pbMax: '',
    psMin: '',
    psMax: '',
    psTtmMin: '',
    psTtmMax: '',
    totalMvMin: '',
    totalMvMax: '',
    industry: 'all',
    actEntType: 'all'
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

// 监听props变化
watch(() => props.isLoading, (newValue) => {
    isUpdatingData.value = newValue;
});

watch(() => props.dataUpdateStatus, (newValue) => {
    if (newValue) {
        dataStatus.value = newValue;
        // 状态消息会由父组件清除，不需要在这里设置定时器
    }
});

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
        if (key === 'industry' || key === 'actEntType') {
            filters[typedKey] = 'all';
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
        // 对于所有字段，确保它们是字符串或数字
        if (typedKey in filters) {
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
const updateData = async (dataType: 'basic' | 'daily' | 'all' = 'all') => {
    isUpdatingData.value = true;

    const dataTypeText = {
        'basic': '基础',
        'daily': '行情',
        'all': '全部'
    }[dataType];

    dataStatus.value = `正在更新${dataTypeText}数据，请稍候...`;
    try {
        emit('update-data', dataType);
        // 不再使用模拟延迟，而是依赖父组件的实际API调用
        // 状态更新将由父组件通过事件通知
    } catch (error) {
        console.error('Error updating data:', error);
        dataStatus.value = `${dataTypeText}数据更新失败，请检查网络或联系管理员。`;
        isUpdatingData.value = false;
    }
};
</script>

<style scoped>
/* All previous scoped styles are removed as Tailwind utility classes are used for styling.
   If specific non-utility styles are needed, they can be added here,
   but the goal is to rely on Tailwind and shadcn/ui components as much as possible. */
</style>
