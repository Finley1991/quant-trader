<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <h1>Quant Trader</h1>
      <div class="nav-links">
        <router-link to="/">仪表盘</router-link>
        <router-link to="/watchlist">自选股</router-link>
        <router-link to="/backtest">策略回测</router-link>
        <router-link to="/signals">信号历史</router-link>
        <router-link to="/settings">设置</router-link>
      </div>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app-container {
  min-height: 100vh;
}

.app-header {
  background: #1f2937;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.app-header h1 {
  font-size: 20px;
  font-weight: 600;
}

.nav-links a {
  color: #9ca3af;
  text-decoration: none;
  margin-left: 24px;
  transition: color 0.2s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: white;
}

.app-main {
  background: #f3f4f6;
  padding: 24px;
}
</style>
