<template>
  <div class="dashboard">
    <h1>欢迎使用ETL数据管理系统</h1>
    <p>这是一个用于管理数据源、配置ETL任务和调度的平台。</p>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-number">{{ stats.dataSources }}</div>
          <div class="stat-label">数据源数量</div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-number">{{ stats.eltTasks }}</div>
          <div class="stat-label">ETL任务数</div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-number">{{ stats.schedules }}</div>
          <div class="stat-label">调度任务数</div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-number">{{ stats.executions }}</div>
          <div class="stat-label">执行次数</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Executions -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>最近执行记录</span>
      </template>

      <el-table :data="recentExecutions" style="width: 100%">
        <el-table-column prop="task_name" label="任务名称" width="200" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180" />
        <el-table-column prop="processed_rows" label="处理行数" width="120" />
        <el-table-column prop="error_message" label="错误信息" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const stats = ref({
  dataSources: 0,
  eltTasks: 0,
  schedules: 0,
  executions: 0
})

const recentExecutions = ref([])

const getStatusType = (status) => {
  const types = {
    success: 'success',
    failed: 'danger',
    running: 'primary',
    pending: 'info'
  }
  return types[status] || 'info'
}

const loadStats = async () => {
  try {
    const [dataSources, eltTasks, schedules, executionStats] = await Promise.all([
      api.dataSources.getAll(),
      api.eltTasks.getAll(),
      api.schedules.getAll(),
      api.taskExecutions.getStats()
    ])

    stats.value = {
      dataSources: dataSources.length,
      eltTasks: eltTasks.length,
      schedules: schedules.length,
      executions: executionStats.total_executions
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

const loadRecentExecutions = async () => {
  try {
    const response = await api.taskExecutions.getAll({ per_page: 5 })
    recentExecutions.value = response.executions || []
  } catch (error) {
    console.error('Failed to load recent executions:', error)
  }
}

onMounted(() => {
  loadStats()
  loadRecentExecutions()
})
</script>

<style scoped>
.dashboard h1 {
  margin-bottom: 10px;
}

.stat-card {
  text-align: center;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  color: #909399;
  margin-top: 10px;
}
</style>