<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <h1>股票估值与分析</h1>
    </header>
    <div class="main-layout">
      <nav class="sidebar">
        <!-- 侧边栏导航链接将通过 router-link 在这里添加 -->
        <RouterLink to="/">DCF估值</RouterLink>
        <RouterLink to="/screener">股票筛选器</RouterLink>
      </nav>
      <main class="content-area">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

.app-header {
  background-color: #42b983;
  color: white;
  padding: 1rem;
  text-align: center;
}

.main-layout {
  display: flex;
  flex-grow: 1;
  overflow: hidden; /* 防止内容溢出时出现滚动条 */
}

.sidebar {
  width: 200px;
  background-color: #f4f4f4;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #ddd;
}

.sidebar a {
  font-weight: bold;
  color: #2c3e50;
  text-decoration: none;
  padding: 0.5rem 0;
  margin-bottom: 0.5rem;
}

.sidebar a.router-link-exact-active {
  color: #42b983;
  border-left: 3px solid #42b983;
  padding-left: calc(1rem - 3px); /* 保持文本对齐 */
}

.content-area {
  flex-grow: 1;
  padding: 1rem;
  overflow-y: auto; /* 如果内容超出，允许垂直滚动 */
}
</style>
