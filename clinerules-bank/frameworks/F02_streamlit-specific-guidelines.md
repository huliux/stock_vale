# Streamlit 特定使用指南

本文档为使用 Streamlit 构建数据应用和交互式 Web 界面时提供特定的指导原则和最佳实践。它旨在补充 `core/` 目录下的通用 GUI 设计原则 (`DA03_gui-design-principles.md`) 和 Python 编码标准 (`DP01_general-coding-standards.md`, `DP02_coding-style-streamlit.md`)。

## 1. Streamlit 应用设计理念

*   **快速迭代与原型验证：** Streamlit 非常适合快速将数据脚本转化为交互式应用，便于快速验证想法和展示原型。
*   **数据驱动：** 其核心优势在于展示和交互数据。设计应围绕如何清晰、有效地呈现数据和分析结果。
*   **简洁性：** Streamlit 鼓励简洁的脚本式编程模型。避免过度复杂的 UI 逻辑和状态管理，除非确有必要。

## 2. 应用结构与布局

*   **单一脚本入口：** 通常一个 Streamlit 应用对应一个主 Python 脚本。
*   **侧边栏 (`st.sidebar`)：**
    *   用于放置全局配置、主要的用户输入控件、导航选项等。
    *   保持侧边栏内容简洁，避免过于拥挤。
*   **主页面布局：**
    *   使用 `st.columns` 创建多列布局。
    *   使用 `st.container` 和 `st.expander` 来组织和分隔内容区块。
    *   合理使用标题 (`st.title`, `st.header`, `st.subheader`) 和 Markdown (`st.markdown`) 来构建信息层级。
*   **模块化 UI 函数：**
    *   将复杂的 UI 区块或可重用的 UI 片段封装到独立的 Python 函数中。
    *   主脚本负责调用这些函数来渲染页面。
*   **多页面应用 (Multi-Page Apps - MPA):**
    *   对于功能较多的应用，可以使用 Streamlit 的多页面应用功能，将不同功能模块放到不同的页面（即不同的 `.py` 文件存放在 `pages/` 目录下）。

## 3. 组件使用 (Widgets)

*   **选择合适的组件：** 根据输入数据的类型和用户交互需求，选择最合适的 Streamlit 输入组件（如 `st.text_input`, `st.number_input`, `st.selectbox`, `st.slider`, `st.checkbox`, `st.date_input`, `st.file_uploader` 等）。
*   **默认值与提示：** 为输入组件提供合理的默认值和清晰的提示信息 (`help` 参数)。
*   **键 (Key)：** 为需要通过 `st.session_state` 访问或在回调中引用的组件显式设置唯一的 `key`。
*   **回调函数 (`on_change`):**
    *   使用 `on_change` 参数为输入组件绑定回调函数，以响应用户输入的变化。
    *   回调函数应简洁，专注于处理状态更新或触发特定逻辑。

## 4. 状态管理 (`st.session_state`)

*   **用途：** 用于在用户多次交互之间保持应用的状态，或在不同组件/函数间共享状态。
*   **初始化：** 在应用脚本的开头检查并初始化会话状态中所需的键。
    ```python
    if 'my_variable' not in st.session_state:
        st.session_state.my_variable = "initial_value"
    ```
*   **访问与修改：** 通过字典式访问 (`st.session_state.my_key` 或 `st.session_state['my_key']`)。
*   **注意事项：**
    *   避免在会话状态中存储非常大的数据对象，这可能影响性能。考虑使用缓存。
    *   清晰命名会话状态的键。

## 5. 数据展示

*   **表格 (`st.dataframe`, `st.table`):**
    *   `st.dataframe` 提供交互式表格（可排序、滚动）。
    *   `st.table` 用于静态表格。
    *   对于 Pandas DataFrame，可以直接传递给这些函数。
*   **图表 (`st.pyplot`, `st.altair_chart`, `st.plotly_chart`, etc.):**
    *   Streamlit 支持多种流行的 Python绘图库。
*   **文本与指标 (`st.text`, `st.markdown`, `st.metric`, `st.json`):**
    *   `st.metric` 适合展示关键性能指标 (KPI) 及其变化。
    *   `st.markdown` 支持 Markdown 语法，用于格式化文本和嵌入 HTML (需 `unsafe_allow_html=True`)。

## 6. 性能优化

*   **缓存 (`@st.cache_data`, `@st.cache_resource`):**
    *   **`@st.cache_data`:** 用于缓存返回数据的函数（如从 API 获取数据、执行耗时计算）。当函数输入参数不变时，直接返回缓存结果。
    *   **`@st.cache_resource`:** 用于缓存全局资源（如加载机器学习模型、数据库连接池）。资源在整个会话中只初始化一次。
    *   正确使用缓存是提升 Streamlit 应用性能的关键。
*   **避免在主脚本中执行不必要的重计算：** Streamlit 脚本在每次交互时会重新运行。将可缓存的逻辑封装到函数中并使用缓存装饰器。

## 7. 与后端 API 交互

*   使用标准的 Python HTTP 客户端库（如 `requests`, `httpx`）来调用后端 API。
*   将 API 调用逻辑封装到独立的函数中，并考虑使用 `@st.cache_data` 缓存 API 响应（如果适用）。
    *   在 API 调用期间，使用 `st.spinner` 提供加载状态反馈。
    *   妥善处理 API 调用可能发生的错误（如网络错误、API 返回错误状态码），并向用户显示友好的错误信息。

---

本指南旨在帮助开发者更有效地使用 Streamlit 构建应用。建议同时参考 Streamlit 官方文档以获取最新和最全面的信息。
