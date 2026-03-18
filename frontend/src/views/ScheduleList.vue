<template>
  <div class="schedule-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>调度列表</span>
          <el-button type="primary" @click="$router.push('/schedules/create')">
            创建调度
          </el-button>
        </div>
      </template>

      <el-table :data="schedules" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="调度名称" width="200" />
        <el-table-column prop="task_name" label="关联任务" width="200" />
        <el-table-column label="调度类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.schedule_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="调度配置" width="150">
          <template #default="{ row }">
            {{ formatScheduleConfig(row) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下次执行" width="180">
          <template #default="{ row }">
            {{ formatDate(row.next_run_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="editSchedule(row)">编辑</el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleSchedule(row)"
            >
              {{ row.is_active ? '暂停' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="deleteSchedule(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const router = useRouter()
const loading = ref(false)
const schedules = ref([])

const formatScheduleConfig = (schedule) => {
  const config = schedule.schedule_config || {}
  if (schedule.schedule_type === 'cron') {
    return config.cron_expression || '-'
  } else if (schedule.schedule_type === 'interval') {
    return `每${config.interval_seconds}秒`
  } else if (schedule.schedule_type === 'date') {
    return config.run_time || '-'
  }
  return '-'
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const loadSchedules = async () => {
  loading.value = true
  try {
    schedules.value = await api.schedules.getAll()
  } catch (error) {
    console.error('Failed to load schedules:', error)
  } finally {
    loading.value = false
  }
}

const editSchedule = (row) => {
  router.push(`/schedules/${row.id}/edit`)
}

const toggleSchedule = async (row) => {
  try {
    await api.schedules.toggle(row.id)
    ElMessage.success(row.is_active ? '已暂停' : '已启用')
    loadSchedules()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteSchedule = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除调度 "${row.name}" 吗？`, '提示', {
      type: 'warning'
    })

    await api.schedules.delete(row.id)
    ElMessage.success('删除成功')
    loadSchedules()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadSchedules()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>