<template>
  <div class="workflow-list">
    <div class="page-header">
      <h2>工作流编排</h2>
      <el-button type="primary" @click="createWorkflow">
        <el-icon><Plus /></el-icon>
        新建工作流
      </el-button>
    </div>

    <!-- Search & Filter -->
    <div class="filter-bar">
      <el-input
        v-model="searchText"
        placeholder="搜索工作流名称"
        style="width: 300px"
        clearable
        @clear="loadWorkflows"
        @keyup.enter="loadWorkflows"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="filterTrigger" placeholder="触发类型" clearable style="width: 150px" @change="loadWorkflows">
        <el-option label="手动触发" value="manual" />
        <el-option label="定时触发" value="cron" />
        <el-option label="事件触发" value="event" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px" @change="loadWorkflows">
        <el-option label="已激活" value="active" />
        <el-option label="已停用" value="inactive" />
      </el-select>
    </div>

    <!-- Workflow Table -->
    <el-table
      v-loading="loading"
      :data="workflows"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="name" label="工作流名称" min-width="180">
        <template #default="{ row }">
          <div class="workflow-name">
            <span>{{ row.name }}</span>
            <el-tag v-if="!row.is_active" type="info" size="small">已停用</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="trigger_type" label="触发类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getTriggerTagType(row.trigger_type)" size="small">
            {{ getTriggerLabel(row.trigger_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="节点数" width="100" align="center">
        <template #default="{ row }">
          <span>{{ row.nodes?.length || 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            @change="toggleActive(row)"
          />
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="160">
        <template #default="{ row }">
          {{ formatDate(row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="editWorkflow(row)">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button
            text
            type="success"
            :disabled="!row.is_active"
            @click="executeWorkflow(row)"
          >
            <el-icon><VideoPlay /></el-icon>
            执行
          </el-button>
          <el-dropdown trigger="click">
            <el-button text>
              <el-icon><More /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="viewExecutions(row)">
                  <el-icon><List /></el-icon>
                  执行记录
                </el-dropdown-item>
                <el-dropdown-item @click="copyWorkflow(row)">
                  <el-icon><CopyDocument /></el-icon>
                  复制工作流
                </el-dropdown-item>
                <el-dropdown-item divided @click="deleteWorkflow(row)">
                  <el-icon><Delete /></el-icon>
                  <span style="color: #f56c6c">删除</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadWorkflows"
        @current-change="loadWorkflows"
      />
    </div>

    <!-- Execution History Dialog -->
    <el-dialog
      v-model="showExecutions"
      title="执行记录"
      width="800px"
      destroy-on-close
    >
      <el-table :data="executions" v-loading="loadingExecutions">
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" width="160">
          <template #default="{ row }">
            {{ row.end_time ? formatDate(row.end_time) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="100">
          <template #default="{ row }">
            {{ getDuration(row) }}
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.error_message" style="color: #f56c6c">{{ row.error_message }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  Edit,
  VideoPlay,
  More,
  List,
  CopyDocument,
  Delete
} from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()

const loading = ref(false)
const workflows = ref([])
const searchText = ref('')
const filterTrigger = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const showExecutions = ref(false)
const executions = ref([])
const loadingExecutions = ref(false)

const getTriggerLabel = (type) => {
  const labels = {
    manual: '手动触发',
    cron: '定时触发',
    event: '事件触发'
  }
  return labels[type] || type
}

const getTriggerTagType = (type) => {
  const types = {
    manual: '',
    cron: 'warning',
    event: 'success'
  }
  return types[type] || ''
}

const getStatusLabel = (status) => {
  const labels = {
    running: '执行中',
    success: '成功',
    failed: '失败',
    partial: '部分成功'
  }
  return labels[status] || status
}

const getStatusTagType = (status) => {
  const types = {
    running: 'primary',
    success: 'success',
    failed: 'danger',
    partial: 'warning'
  }
  return types[status] || ''
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const getDuration = (row) => {
  if (!row.start_time) return '-'
  const start = new Date(row.start_time)
  const end = row.end_time ? new Date(row.end_time) : new Date()
  const duration = Math.floor((end - start) / 1000)

  if (duration < 60) return `${duration}秒`
  if (duration < 3600) return `${Math.floor(duration / 60)}分${duration % 60}秒`
  return `${Math.floor(duration / 3600)}小时${Math.floor((duration % 3600) / 60)}分`
}

const loadWorkflows = async () => {
  loading.value = true

  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value
    }

    if (searchText.value) {
      params.search = searchText.value
    }
    if (filterTrigger.value) {
      params.trigger_type = filterTrigger.value
    }
    if (filterStatus.value) {
      params.is_active = filterStatus.value === 'active'
    }

    const response = await api.workflows.getAll(params)
    const data = response.data || response

    workflows.value = data.items || data.workflows || data || []
    total.value = data.total || workflows.value.length
  } catch (error) {
    console.error('Failed to load workflows:', error)
    ElMessage.error('加载工作流列表失败')
  } finally {
    loading.value = false
  }
}

const createWorkflow = () => {
  router.push({ name: 'WorkflowCreate' })
}

const editWorkflow = (row) => {
  router.push({ name: 'WorkflowEdit', params: { id: row.id } })
}

const executeWorkflow = async (row) => {
  ElMessageBox.confirm(
    `确定要立即执行工作流 "${row.name}" 吗？`,
    '执行确认',
    {
      confirmButtonText: '执行',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(async () => {
    try {
      await api.workflows.execute(row.id)
      ElMessage.success('工作流已开始执行')
    } catch (error) {
      console.error('Failed to execute workflow:', error)
      ElMessage.error(error.response?.data?.message || '执行失败')
    }
  }).catch(() => {})
}

const toggleActive = async (row) => {
  try {
    await api.workflows.toggleActive(row.id, row.is_active)
    ElMessage.success(row.is_active ? '已激活' : '已停用')
  } catch (error) {
    console.error('Failed to toggle active:', error)
    row.is_active = !row.is_active
    ElMessage.error('操作失败')
  }
}

const viewExecutions = async (row) => {
  showExecutions.value = true
  loadingExecutions.value = true

  try {
    const response = await api.workflows.getExecutions(row.id)
    executions.value = response.data || response.executions || response || []
  } catch (error) {
    console.error('Failed to load executions:', error)
    ElMessage.error('加载执行记录失败')
  } finally {
    loadingExecutions.value = false
  }
}

const copyWorkflow = async (row) => {
  ElMessageBox.confirm(
    `确定要复制工作流 "${row.name}" 吗？`,
    '复制确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(async () => {
    try {
      const newWorkflow = {
        name: `${row.name} (副本)`,
        description: row.description,
        trigger_type: row.trigger_type,
        trigger_config: row.trigger_config,
        is_active: false,
        nodes: row.nodes || [],
        edges: row.edges || []
      }

      await api.workflows.create(newWorkflow)
      ElMessage.success('工作流复制成功')
      loadWorkflows()
    } catch (error) {
      console.error('Failed to copy workflow:', error)
      ElMessage.error('复制失败')
    }
  }).catch(() => {})
}

const deleteWorkflow = async (row) => {
  ElMessageBox.confirm(
    `确定要删除工作流 "${row.name}" 吗？此操作不可恢复。`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await api.workflows.delete(row.id)
      ElMessage.success('工作流已删除')
      loadWorkflows()
    } catch (error) {
      console.error('Failed to delete workflow:', error)
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  loadWorkflows()
})
</script>

<style scoped>
.workflow-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
  color: #303133;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.workflow-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table) {
  border-radius: 4px;
}
</style>