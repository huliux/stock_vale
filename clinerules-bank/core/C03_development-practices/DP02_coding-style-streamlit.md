# Streamlit 应用编码风格指南

本文档为使用 Streamlit 构建 Python 应用时的编码风格提供补充性指导。主要目标是确保 Streamlit 应用代码的清晰性、可维护性，并与项目整体的 Python 编码标准保持一致。

## 1. 核心原则

*   **遵循通用 Python 编码标准：**
    *   Streamlit 应用的 Python 代码应严格遵循 `DP01_general-coding-standards.md` 中定义的通用编码标准，特别是关于命名约定 (PEP 8)、类型注解、文档字符串、代码格式化 (如使用 Black) 等。
*   **Streamlit API 的清晰使用：**
    *   清晰、直观地使用 Streamlit 提供的 API 函数 (如 `st.write`, `st.sidebar`, `st.text_input`, `st.button`, `st.dataframe` 等)。
    *   对于复杂的 UI 布局或组件组合，考虑将其封装到独立的 Python 函数中，以提高主应用脚本的可读性。
        *   （例如：在主应用脚本中，可以将UI的不同部分，如侧边栏、主要内容区域的各个区块，分别封装到独立的辅助函数中进行渲染，如 `render_sidebar_inputs()`、`display_data_section()` 等。）

## 2. 代码组织与结构

*   **模块化辅助函数与逻辑：**
    *   对于与 Streamlit UI 无直接关系但被 UI 调用的辅助函数、数据处理逻辑或常量，应考虑将其组织到独立的 `.py` 文件中（例如，可以将这些辅助逻辑组织到如 `utils.py`、`helpers.py` 或特定功能模块如 `data_processing_utils.py` 中）。
    *   这有助于保持主 Streamlit 应用文件（通常是 `app.py` 或 `main.py`）的简洁，使其更专注于 UI 布局和流程控制。
*   **状态管理 (Session State):**
    *   在使用 Streamlit 的会话状态 (`st.session_state`) 时，键名 (key) 应清晰、有意义。
    *   避免在会话状态中存储过多或过于复杂的数据结构，优先存储简单状态，复杂数据通过函数调用重新计算或获取。
    *   对于需要跨多次交互或多个组件共享的状态，合理使用会话状态。
*   **回调函数 (Callbacks):**
    *   为 Streamlit 小部件 (widgets) 提供的回调函数应简洁明了，专注于其核心职责。
    *   如果回调逻辑复杂，应将其提取为独立的函数。

## 3. 性能考虑（编码层面）

*   **缓存 (`@st.cache_data`, `@st.cache_resource`):**
    *   对于耗时的数据加载、计算或资源初始化操作，应积极使用 Streamlit 的缓存装饰器，以提高应用的响应速度和用户体验。
    *   理解不同缓存装饰器的适用场景。
*   **避免不必要的重计算：**
    *   Streamlit 应用的脚本在每次用户交互时会从头到尾重新运行。注意优化代码逻辑，避免在每次运行时重复执行不必要的昂贵操作（除非它们已被缓存）。

## 4. UI 与逻辑分离 (推荐)

*   虽然 Streamlit 允许将 UI 代码和业务逻辑紧密结合，但在可能的情况下，尽量将核心的业务逻辑（如数据转换、复杂计算）与纯粹的 UI 展示代码分离。
*   这可以通过将业务逻辑封装在独立的函数或类中，Streamlit 代码主要负责调用这些逻辑并展示结果来实现。

---

本指南主要强调在 Streamlit 开发中继续遵循良好的 Python 编码实践，并结合 Streamlit 自身特性进行代码组织和优化。
