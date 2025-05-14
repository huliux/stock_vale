<template>
    <div class="results-table-container">
        <h4>筛选结果</h4>
        <div v-if="isLoading" class="loading-indicator">正在加载数据...</div>
        <div v-else-if="error" class="error-message">{{ error }}</div>
        <div v-else-if="results.length === 0 && !hasSearched" class="info-message">
            请设置筛选条件并点击“应用筛选”。
        </div>
        <div v-else-if="results.length === 0 && hasSearched" class="info-message">
            没有找到符合条件的股票。
        </div>
        <table v-else>
            <thead>
                <tr>
                    <th>股票代码</th>
                    <th>股票名称</th>
                    <th>最新价格</th>
                    <th>市盈率(PE)</th>
                    <th>市净率(PB)</th>
                    <th>总市值(亿元)</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="stock in results" :key="stock.ts_code">
                    <td>{{ stock.ts_code }}</td>
                    <td>{{ stock.name }}</td>
                    <td>{{ stock.latest_price?.toFixed(2) ?? 'N/A' }}</td>
                    <td>{{ stock.pe_ttm?.toFixed(2) ?? 'N/A' }}</td>
                    <td>{{ stock.pb?.toFixed(2) ?? 'N/A' }}</td>
                    <td>{{ stock.total_market_cap?.toFixed(2) ?? 'N/A' }}</td>
                    <td>
                        <button @click="goToValuation(stock.ts_code)">进行估值</button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script setup lang="ts">
// defineProps and defineEmits are compiler macros and no longer need to be imported.

// 假设的股票数据结构，后续会从 shared-types 引入或在此定义更准确的类型
export interface ScreenedStock {
    ts_code: string;
    name: string;
    latest_price?: number | null;
    pe_ttm?: number | null;
    pb?: number | null;
    total_market_cap?: number | null; // 单位：亿元
    // 可以根据实际从API获取的数据添加更多字段
}

interface Props {
    results: ScreenedStock[];
    isLoading: boolean;
    error: string | null;
    hasSearched: boolean; // 用于区分初始状态和搜索后无结果的状态
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const props = defineProps<Props>();

const emit = defineEmits(['go-to-valuation']);

const goToValuation = (stockCode: string) => {
    emit('go-to-valuation', stockCode);
};
</script>

<style scoped>
.results-table-container {
    margin-top: 1rem;
}

.results-table-container h4 {
    margin-bottom: 0.5rem;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

th,
td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

th {
    background-color: #f2f2f2;
    font-weight: bold;
}

tr:nth-child(even) {
    background-color: #f9f9f9;
}

tr:hover {
    background-color: #f1f1f1;
}

button {
    padding: 0.3rem 0.6rem;
    font-size: 0.9em;
    background-color: #42b983;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background-color: #36a374;
}

.loading-indicator,
.error-message,
.info-message {
    padding: 1rem;
    border: 1px solid #eee;
    border-radius: 4px;
    margin-top: 1rem;
}

.loading-indicator {
    background-color: #eef;
    color: #33a;
}

.error-message {
    background-color: #fee;
    color: #a33;
}

.info-message {
    background-color: #eff;
    color: #3aa;
}
</style>
