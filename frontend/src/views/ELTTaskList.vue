<template>
  <div class="elt-task-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>ETL任务列表</span>
          <el-button type="primary" @click="$router.push('/elt-tasks/create')">
            创建任务
          </el-button>
        </div>
      </template>

      <el-table :data="tasks" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="任务名称" width="200" />
        <el-table-column prop="source_db_name" label="源数据源" width="150" />
        <el-table-column prop="target_db_name" label="目标数据源" width="150" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.last_status)">
              {{ row.last_status || '待执行' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_execution_time" label="最后执行时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.last_execution_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="editTask(row)">编辑</el-button>
            <el-button size="small" type="success" @click="executeTask(row)">执行</el-button>
            <el-button size="small" type="danger" @click="deleteTask(row)">删除</el-button>
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
const tasks = ref([])

const getStatusType = (status) => {
  const types = {
    success: 'success',
    failed: 'danger',
    running: 'primary',
    pending: 'info'
  }
  return types[status] || 'info'
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const loadTasks = async () => {
  loading.value = true
  try {
    tasks.value = await api.eltTasks.getAll()
  } catch (error) {
    console.error('Failed to load tasks:', error)
  } finally {
    loading.value = false
  }
}

const editTask = (row) => {
  router.push(`/elt-tasks/${row.id}/edit`)
}

const executeTask = async (row) => {
  try {
    ElMessage.info(`正在执行任务 ${row.name}...`)
    const result = await api.eltTasks.execute(row.id)
    ElMessage.success(`执行成功，处理了 ${result.details?.processed_rows || 0} 行数据`)
    loadTasks()
  } catch (error) {
    ElMessage.error('执行失败')
  }
}

const deleteTask = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务 "${row.name}" 吗？`, '提示', {
      type: 'warning'
    })

    await api.eltTasks.delete(row.id)
    ElMessage.success('删除成功')
    loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>