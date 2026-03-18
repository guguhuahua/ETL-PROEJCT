<template>
  <div class="layout-container">
    <!-- Sidebar -->
    <el-aside class="sidebar" width="200px">
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical"
        background-color="#545c64"
        text-color="#fff"
        active-text-color="#ffd04b"
        router
      >
        <div class="logo">
          <h3>ETL系统</h3>
        </div>

        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表板</span>
        </el-menu-item>

        <el-sub-menu index="data-source">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>数据源管理</span>
          </template>
          <el-menu-item index="/data-sources">数据源列表</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="elt-tasks">
          <template #title>
            <el-icon><DataAnalysis /></el-icon>
            <span>ETL配置</span>
          </template>
          <el-menu-item index="/elt-tasks">任务列表</el-menu-item>
          <el-menu-item index="/elt-tasks/create">创建任务</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="schedules">
          <template #title>
            <el-icon><Timer /></el-icon>
            <span>调度配置</span>
          </template>
          <el-menu-item index="/schedules">调度列表</el-menu-item>
          <el-menu-item index="/schedules/create">创建调度</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <!-- Main Container -->
    <div class="main-container">
      <!-- Header -->
      <el-header class="header">
        <h3>ETL数据管理系统</h3>
        <div class="header-right">
          <el-dropdown>
            <span class="el-dropdown-link">
              {{ authStore.user?.username || '用户' }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- Main Content -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Odometer, Setting, DataAnalysis, Timer, Share, ArrowDown } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  display: flex;
  height: 100vh;
  width: 100vw;
}

.sidebar {
  background-color: #545c64;
  overflow-y: auto;
}

.el-menu-vertical {
  border-right: none;
  height: 100%;
}

.logo {
  padding: 20px;
  text-align: center;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h3 {
  margin: 0;
  font-size: 18px;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.header-right {
  cursor: pointer;
}

.el-dropdown-link {
  display: flex;
  align-items: center;
  color: #409eff;
  font-size: 14px;
}

.el-dropdown-link:hover {
  color: #66b1ff;
}

.main-content {
  flex: 1;
  padding: 20px;
  background-color: #f0f2f5;
  overflow-y: auto;
}
</style>