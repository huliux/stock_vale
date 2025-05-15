# 整合学习与最佳实践

## FastAPI 与 Pydantic

### Pydantic 模型字段别名与JSON序列化
- **核心行为:** 当 Pydantic 模型中的字段使用了 `alias` 参数 (例如 `my_field: str = Field(alias="myFieldAlias")`)，FastAPI 在将此模型序列化为 JSON 响应时，默认会使用该 `alias` (`"myFieldAlias"`) 作为 JSON对象的键名，而不是原始字段名 (`"my_field"`)。
- **重要性:** 这是 FastAPI/Pydantic 的一个关键特性。在进行前后端对接时，如果后端 Pydantic 模型使用了别名，前端接收到的 JSON 数据键名将是这些别名。
- **实践建议:**
    - **共享类型定义:** 必须确保共享类型（如 `packages/shared-types/` 中的 TypeScript 接口）与前端实际接收到的 JSON 结构（即后端序列化后的键名）完全一致。
    - **前后端联调:** 始终以实际网络传输的 JSON 结构为准来定义前端类型和解析逻辑。在 API 客户端或接收 API 调用的地方打印原始响应内容，是验证数据结构和键名的好习惯。

## Vue.js 与 Pinia 状态管理

### Pinia Store 基本模式
- **用途:** 对于 Vue.js 应用中需要跨组件、跨路由共享的状态（例如 API 请求结果、用户会话信息等），使用 Pinia 进行状态管理是推荐且高效的方案。
- **集成步骤:**
    1.  **安装:** `npm install pinia`
    2.  **创建 Store:** 定义一个 store模块 (e.g., `src/stores/myStore.ts`)。
        ```typescript
        import { defineStore } from 'pinia';

        export const useMyStore = defineStore('myStoreName', {
          state: () => ({
            // 在此定义状态属性
            someData: null,
            isLoading: false,
            error: null,
          }),
          getters: {
            // 可选：定义计算属性 (computed properties from state)
            processedData: (state) => {
              // process state.someData
              return /* processed value */;
            },
          },
          actions: {
            // 定义修改状态的方法
            async fetchData() {
              this.isLoading = true;
              this.error = null;
              try {
                // const response = await api.fetchSomething();
                // this.someData = response.data;
              } catch (err) {
                // this.error = err;
              } finally {
                this.isLoading = false;
              }
            },
            setData(newData) {
              this.someData = newData;
            }
          },
        });
        ```
    3.  **在 Vue 应用入口注册 Pinia:**
        ```typescript
        // src/main.ts
        import { createApp } from 'vue';
        import { createPinia } from 'pinia';
        import App from './App.vue';

        const app = createApp(App);
        app.use(createPinia()); // 注册 Pinia 实例
        app.mount('#app');
        ```
    4.  **在组件中使用 Store:**
        ```vue
        <script setup lang="ts">
        import { computed } from 'vue';
        import { useMyStore } from '@/stores/myStoreName'; // 路径可能需要调整

        const myStore = useMyStore();

        // 访问 state (建议通过 store 实例直接访问，或用 computed 包装以保持响应性)
        const isLoading = computed(() => myStore.isLoading);
        const data = computed(() => myStore.someData);

        // 访问 getters (getters 本身就是响应式的)
        const processed = computed(() => myStore.processedData);

        // 调用 actions
        function loadData() {
          myStore.fetchData();
        }

        // 如果需要在 setup 之外或模板中直接修改 state (不推荐，应通过 actions)
        // myStore.someData = 'new value'; // 直接修改
        // myStore.$patch({ someData: 'new value' }); // 批量修改
        </script>
        ```
- **路径别名:** 在 store 文件中导入共享类型或其他模块时，注意 TypeScript 或构建工具（如 Vite）配置的路径别名（例如 `@shared-types/*`）是否正确解析，或者使用相对路径。

## Vue.js 前端开发实践

### 复杂表单参数对齐与迁移
- **场景:** 当从旧系统（如 Streamlit 应用）迁移具有大量输入参数的表单到新的 Vue.js 组件时，确保用户体验的连续性至关重要。
- **核心原则:**
    - **细致对比:** 逐个参数对比新旧系统的输入字段、标签、提示信息、校验规则和默认值。
    - **默认值一致性:** 尽力确保 Vue 表单中各参数的初始默认值与旧系统中的默认行为（包括动态依赖其他参数计算得出的默认值）保持一致。
    - **数据格式转换:** 注意用户界面友好的数据表示（如百分比用整数 `15` 表示15%）与API接口期望的数据格式（如小数 `0.15`）之间的转换。这种转换通常在提交表单、构建API请求体时进行。
    - **动态依赖处理:** 如果某些参数的默认值或可选状态依赖于其他参数的当前值（例如，某过渡年数默认等于用户选择的总预测期年数），在Vue中可使用 `watch` Effect 来监听依赖参数的变化并相应更新。

### Vue 组件间通信：Props 向下，Emits 向上
- **模式:** 这是 Vue 中经典的父子组件通信模式，有助于构建清晰的数据流和组件责任。
- **应用场景 (示例 - 表单校验与错误处理):**
    1.  **子组件 (如表单组件 `DcfParametersForm.vue`):**
        *   内部进行输入校验。
        *   当校验失败时，不直接使用全局方法（如 `alert()`）显示错误，而是通过 `defineEmits` 定义一个自定义事件 (e.g., `validation-error`)。
        *   使用 `emit('validation-error', '具体的错误信息')` 将错误信息作为事件的载荷向上传递。
    2.  **父组件 (如视图组件 `DcfValuationView.vue`):**
        *   在模板中使用子组件时，通过 `@validation-error="handleFormError"` 监听该自定义事件。
        *   定义 `handleFormError(errorMessage: string)` 方法来接收错误信息。
        *   在该方法中，可以将错误信息提交到全局状态管理器（如 Pinia store），或者在父组件层面进行统一的错误展示逻辑。
- **优点:** 实现了子组件的封装性（它只负责发出事件，不关心如何展示错误），并允许父组件或更高层级统一管理和展示来自不同来源（如表单校验、API调用）的错误，提升了用户体验的一致性。

### TypeScript 在 Vue.js 中的应用注意点
- **模板插值类型:** 在 Vue 模板的 Mustache 插值 `{{ }}` 中，最终绑定的表达式结果应为字符串。如果一个表达式可能返回数字、null 或 undefined，需要确保在模板中或通过计算属性/方法将其转换为字符串，以避免潜在的运行时错误或TypeScript编译时关于类型不匹配的警告。例如，对数字调用 `.toFixed(2)` 后，其结果已经是字符串；对于可能为 `null` 的值，可以使用 `(value || 'N/A')` 来确保输出字符串。
- **可选链与类型安全:** 在访问可能为 `null` 或 `undefined` 的对象的属性或调用其方法时，虽然可选链操作符 (`?.`) 可以防止运行时错误，但在进行后续操作（如数学运算、特定方法调用）时，仍需确保操作数的类型符合预期。TypeScript 编译器会对此进行检查，需要通过类型守卫（如 `typeof value === 'number'`）或确保值在操作前已有效赋值来解决。
- **共享类型与后端模型同步:** (重申) 保持 `packages/shared-types/` 中的 TypeScript 接口与后端 Pydantic 模型（特别是其JSON序列化输出）的字段名和类型严格同步，是避免许多前后端集成问题的关键。
