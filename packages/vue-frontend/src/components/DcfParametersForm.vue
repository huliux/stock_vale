<template>
    <div class="dcf-parameters-form">
        <h4>DCF估值参数</h4>
        <form @submit.prevent="submitValuationRequest">
            <div class="form-group">
                <label for="stock-code">股票代码:</label>
                <input type="text" id="stock-code" v-model="params.stock_code" required />
                <span class="hint">例如: 000001.SZ 或 600519.SH</span>
            </div>

            <div class="form-group">
                <label for="discount-rate">贴现率 (WACC %):</label>
                <input type="number" id="discount-rate" v-model.number="params.discount_rate" step="0.01" required />
            </div>

            <div class="form-group">
                <label for="terminal-growth-rate">永续增长率 (%):</label>
                <input type="number" id="terminal-growth-rate" v-model.number="params.terminal_growth_rate" step="0.01"
                    required />
            </div>

            <div class="form-group">
                <label for="prediction-years">预测年限:</label>
                <input type="number" id="prediction-years" v-model.number="params.prediction_years" min="3" max="15"
                    required />
            </div>

            <!-- 更多参数可以后续添加，例如预测模式、具体财务假设等 -->
            <p class="info">更详细的财务预测假设（如收入增长模式、利润率等）将在后续版本中提供配置。</p>

            <button type="submit" :disabled="isLoading">
                {{ isLoading ? '正在计算...' : '开始估值' }}
            </button>
        </form>
    </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
// defineEmits and defineProps are compiler macros and no longer need to be imported.

// 表单使用的参数结构，百分比按用户输入习惯（例如8.5代表8.5%）
export interface DcfFormParameters {
    stock_code: string;
    discount_rate: number | null;
    terminal_growth_rate: number | null;
    prediction_years: number | null;
    // TODO: Add more detailed financial assumptions as needed
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const props = defineProps<{
    isLoading: boolean;
    initialStockCode?: string | null;
}>();

const params = reactive<DcfFormParameters>({
    stock_code: props.initialStockCode || '',
    discount_rate: 8.5, // Default example value, user sees 8.5
    terminal_growth_rate: 2.5, // Default example value, user sees 2.5
    prediction_years: 5, // Default example value
});

const emit = defineEmits(['submit-valuation']);

const submitValuationRequest = () => {
    // Basic validation
    if (!params.stock_code || params.discount_rate === null || params.terminal_growth_rate === null || params.prediction_years === null) {
        alert('请填写所有必填参数！');
        return;
    }
    if (params.prediction_years < 3 || params.prediction_years > 15) {
        alert('预测年限必须在3到15年之间。');
        return;
    }
    emit('submit-valuation', { ...params });
};

// Watch for changes in initialStockCode prop to update the form
import { watch } from 'vue';

watch(() => props.initialStockCode, (newVal) => {
    if (newVal) {
        params.stock_code = newVal;
    }
});

</script>

<style scoped>
.dcf-parameters-form {
    padding: 1rem;
    border: 1px solid #eee;
    border-radius: 4px;
    background-color: #f9f9f9;
}

.dcf-parameters-form h4 {
    margin-top: 0;
    margin-bottom: 1rem;
}

.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.3rem;
    font-weight: bold;
}

.form-group input[type="text"],
.form-group input[type="number"] {
    width: calc(100% - 1rem);
    /* Adjust for padding */
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.form-group .hint {
    font-size: 0.8em;
    color: #777;
    display: block;
    margin-top: 0.2rem;
}

button {
    padding: 0.7rem 1.5rem;
    background-color: #42b983;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1em;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

button:hover:not(:disabled) {
    background-color: #36a374;
}

.info {
    font-size: 0.9em;
    color: #555;
    margin-bottom: 1rem;
    padding: 0.5rem;
    background-color: #eef;
    border-left: 3px solid #33a;
}
</style>
