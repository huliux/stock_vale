<template>
    <div class="screener-filters">
        <h4>筛选条件</h4>
        <div class="filter-group">
            <label for="pe-min">市盈率 (PE) 范围:</label>
            <input type="number" id="pe-min" v-model.number="filters.peMin" placeholder="最小PE" />
            <span>-</span>
            <input type="number" id="pe-max" v-model.number="filters.peMax" placeholder="最大PE" />
        </div>
        <div class="filter-group">
            <label for="pb-min">市净率 (PB) 范围:</label>
            <input type="number" id="pb-min" v-model.number="filters.pbMin" placeholder="最小PB" />
            <span>-</span>
            <input type="number" id="pb-max" v-model.number="filters.pbMax" placeholder="最大PB" />
        </div>
        <div class="filter-group">
            <label for="market-cap-min">市值 (亿元) 范围:</label>
            <input type="number" id="market-cap-min" v-model.number="filters.marketCapMin" placeholder="最小市值" />
            <span>-</span>
            <input type="number" id="market-cap-max" v-model.number="filters.marketCapMax" placeholder="最大市值" />
        </div>
        <button @click="applyFilters">应用筛选</button>
        <button @click="updateData" :disabled="isUpdatingData">
            {{ isUpdatingData ? '正在更新...' : '更新基础数据' }}
        </button>
        <p v-if="dataStatus">{{ dataStatus }}</p>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';

export interface ScreenerFilters { // Added export
    peMin: number | null;
    peMax: number | null;
    pbMin: number | null;
    pbMax: number | null;
    marketCapMin: number | null; // 单位：亿元
    marketCapMax: number | null; // 单位：亿元
}

const filters = reactive<ScreenerFilters>({
    peMin: null,
    peMax: null,
    pbMin: null,
    pbMax: null,
    marketCapMin: null,
    marketCapMax: null,
});

const isUpdatingData = ref(false);
const dataStatus = ref('');

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const emit = defineEmits(['apply-filters', 'update-data']);

const applyFilters = () => {
    // 过滤掉空的筛选条件
    const activeFilters = Object.entries(filters).reduce((acc, [key, value]) => {
        if (value !== null && value !== undefined) { // Removed: value !== ''
            acc[key as keyof ScreenerFilters] = value;
        }
        return acc;
    }, {} as Partial<ScreenerFilters>);
    emit('apply-filters', activeFilters);
};

const updateData = async () => {
    isUpdatingData.value = true;
    dataStatus.value = '正在更新数据，请稍候...';
    try {
        // 实际的数据更新逻辑将在这里调用
        // 例如: await someDataService.updateStockBasics();
        //       await someDataService.updateDailyMetrics();
        // 暂时用 setTimeout 模拟异步操作
        await new Promise(resolve => setTimeout(resolve, 2000));
        dataStatus.value = '数据更新成功！'; // 或者显示具体的更新日期
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
.screener-filters {
    padding: 1rem;
    border: 1px solid #eee;
    border-radius: 4px;
    background-color: #f9f9f9;
}

.screener-filters h4 {
    margin-top: 0;
    margin-bottom: 1rem;
}

.filter-group {
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
}

.filter-group label {
    margin-right: 0.5rem;
    min-width: 120px;
    /* Ensure labels align */
}

.filter-group input[type="number"] {
    width: 100px;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    margin-right: 0.5rem;
}

.filter-group span {
    margin: 0 0.5rem;
}

button {
    padding: 0.5rem 1rem;
    background-color: #42b983;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-right: 0.5rem;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

button:hover:not(:disabled) {
    background-color: #36a374;
}

p {
    margin-top: 1rem;
    font-size: 0.9em;
    color: #555;
}
</style>
