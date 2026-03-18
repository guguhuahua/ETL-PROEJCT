<template>
  <div class="property-panel">
    <div class="panel-header">
      <h3>{{ selectedNode ? '节点属性' : '工作流属性' }}</h3>
    </div>
    <div class="panel-content">
      <!-- Workflow Properties -->
      <template v-if="!selectedNode">
        <el-form :model="workflowForm" label-position="top" size="small">
          <el-form-item label="工作流名称">
            <el-input v-model="workflowForm.name" placeholder="请输入工作流名称" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input
              v-model="workflowForm.description"
              type="textarea"
              :rows="3"
              placeholder="请输入描述"
            />
          </el-form-item>
          <el-form-item label="触发类型">
            <el-select v-model="workflowForm.trigger_type" style="width: 100%">
              <el-option label="手动触发" value="manual" />
              <el-option label="定时触发" value="cron" />
              <el-option label="事件触发" value="event" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="workflowForm.trigger_type === 'cron'" label="Cron 表达式">
            <el-input v-model="workflowForm.cron_expr" placeholder="0 0 * * *" />
            <div class="cron-help">例: 0 0 * * * (每天凌晨执行)</div>
          </el-form-item>
          <el-form-item v-if="workflowForm.trigger_type === 'event'" label="触发事件">
            <el-select v-model="workflowForm.event_type" style="width: 100%">
              <el-option label="任务完成后" value="task_complete" />
              <el-option label="数据到达" value="data_arrive" />
            </el-select>
          </el-form-item>
          <el-form-item label="是否激活">
            <el-switch v-model="workflowForm.is_active" />
          </el-form-item>
        </el-form>
      </template>

      <!-- Node Properties -->
      <template v-else>
        <el-form :model="nodeForm" label-position="top" size="small">
          <el-form-item label="节点ID">
            <el-input :value="selectedNode.id" disabled />
          </el-form-item>
          <el-form-item label="节点类型">
            <el-tag :type="getNodeTypeTag(selectedNode.nodeType)">
              {{ getNodeTypeLabel(selectedNode.nodeType) }}
            </el-tag>
          </el-form-item>
          <el-form-item label="节点名称">
            <el-input v-model="nodeForm.label" placeholder="请输入节点名称" />
          </el-form-item>

          <!-- Task Node Specific -->
          <template v-if="selectedNode.nodeType === 'TASK'">
            <el-form-item label="关联任务">
              <el-select
                v-model="nodeForm.taskId"
                placeholder="请选择关联任务"
                style="width: 100%"
                clearable
                filterable
              >
                <el-option
                  v-for="task in eltTasks"
                  :key="task.id"
                  :label="task.name"
                  :value="task.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item v-if="nodeForm.taskId" label="任务信息">
              <div class="task-info" v-if="selectedTask">
                <div class="info-row">
                  <span class="label">任务名称:</span>
                  <span>{{ selectedTask.name }}</span>
                </div>
                <div class="info-row">
                  <span class="label">源表:</span>
                  <span>{{ selectedTask.source_table || '自定义SQL' }}</span>
                </div>
                <div class="info-row">
                  <span class="label">目标表:</span>
                  <span>{{ selectedTask.target_table }}</span>
                </div>
              </div>
            </el-form-item>
          </template>

          <!-- Condition Node Specific -->
          <template v-if="selectedNode.nodeType === 'CONDITION'">
            <el-form-item label="条件类型">
              <el-select v-model="nodeForm.conditionType" style="width: 100%">
                <el-option label="执行成功" value="success" />
                <el-option label="执行失败" value="failure" />
                <el-option label="数据量判断" value="rowCount" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="nodeForm.conditionType === 'rowCount'" label="数据量条件">
              <el-input v-model="nodeForm.conditionValue" placeholder="> 1000" />
            </el-form-item>
          </template>

          <!-- Parallel Node Specific -->
          <template v-if="selectedNode.nodeType === 'PARALLEL'">
            <el-form-item label="并行分支数">
              <el-input-number v-model="nodeForm.branchCount" :min="2" :max="10" />
            </el-form-item>
          </template>

          <el-form-item>
            <el-button type="primary" @click="saveNodeProperties">保存修改</el-button>
            <el-button type="danger" @click="deleteCurrentNode">删除节点</el-button>
          </el-form-item>
        </el-form>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/api'

const props = defineProps({
  selectedNode: {
    type: Object,
    default: null
  },
  workflow: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update-node', 'delete-node', 'update-workflow'])

const eltTasks = ref([])
const workflowForm = ref({
  name: '',
  description: '',
  trigger_type: 'manual',
  cron_expr: '',
  event_type: 'task_complete',
  is_active: true
})

const nodeForm = ref({
  label: '',
  taskId: null,
  conditionType: 'success',
  conditionValue: '',
  branchCount: 2
})

const selectedTask = computed(() => {
  if (!nodeForm.value.taskId) return null
  return eltTasks.value.find(t => t.id === nodeForm.value.taskId)
})

const getNodeTypeLabel = (type) => {
  const labels = {
    START: '开始节点',
    TASK: '任务节点',
    CONDITION: '条件节点',
    PARALLEL: '并行节点',
    END: '结束节点'
  }
  return labels[type] || '未知节点'
}

const getNodeTypeTag = (type) => {
  const tags = {
    START: 'success',
    TASK: 'primary',
    CONDITION: 'warning',
    PARALLEL: 'info',
    END: 'danger'
  }
  return tags[type] || ''
}

const saveNodeProperties = () => {
  if (!props.selectedNode) return

  const updateData = {
    label: nodeForm.value.label
  }

  if (props.selectedNode.nodeType === 'TASK') {
    updateData.taskId = nodeForm.value.taskId
    const task = eltTasks.value.find(t => t.id === nodeForm.value.taskId)
    if (task) {
      updateData.taskName = task.name
    }
  } else if (props.selectedNode.nodeType === 'CONDITION') {
    updateData.condition = {
      type: nodeForm.value.conditionType,
      value: nodeForm.value.conditionValue
    }
  } else if (props.selectedNode.nodeType === 'PARALLEL') {
    updateData.branches = Array.from({ length: nodeForm.value.branchCount }, (_, i) => i)
  }

  emit('update-node', props.selectedNode.id, updateData)
}

const deleteCurrentNode = () => {
  if (!props.selectedNode) return
  emit('delete-node', props.selectedNode.id)
}

const loadEltTasks = async () => {
  try {
    const response = await api.eltTasks.getAll()
    eltTasks.value = response.data || response
  } catch (error) {
    console.error('Failed to load ELT tasks:', error)
  }
}

// Watch for selected node changes
watch(() => props.selectedNode, (newNode) => {
  if (newNode) {
    nodeForm.value.label = newNode.label || ''
    nodeForm.value.taskId = newNode.taskId || null
    nodeForm.value.conditionType = newNode.condition?.type || 'success'
    nodeForm.value.conditionValue = newNode.condition?.value || ''
    nodeForm.value.branchCount = newNode.branches?.length || 2
  }
}, { immediate: true })

// Watch for workflow changes
watch(() => props.workflow, (newWorkflow) => {
  if (newWorkflow) {
    workflowForm.value.name = newWorkflow.name || ''
    workflowForm.value.description = newWorkflow.description || ''
    workflowForm.value.trigger_type = newWorkflow.trigger_type || 'manual'
    workflowForm.value.is_active = newWorkflow.is_active !== false
    if (newWorkflow.trigger_config) {
      workflowForm.value.cron_expr = newWorkflow.trigger_config.cron_expr || ''
      workflowForm.value.event_type = newWorkflow.trigger_config.event_type || 'task_complete'
    }
  }
}, { immediate: true, deep: true })

// Watch form changes and emit updates
watch(workflowForm, (newVal) => {
  const workflowData = {
    name: newVal.name,
    description: newVal.description,
    trigger_type: newVal.trigger_type,
    is_active: newVal.is_active
  }

  if (newVal.trigger_type === 'cron') {
    workflowData.trigger_config = { cron_expr: newVal.cron_expr }
  } else if (newVal.trigger_type === 'event') {
    workflowData.trigger_config = { event_type: newVal.event_type }
  }

  emit('update-workflow', workflowData)
}, { deep: true })

onMounted(() => {
  loadEltTasks()
})
</script>

<style scoped>
.property-panel {
  width: 280px;
  height: 100%;
  background: #fff;
  border-left: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.cron-help {
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
}

.task-info {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 10px;
}

.info-row {
  display: flex;
  margin-bottom: 6px;
  font-size: 12px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  color: #909399;
  width: 70px;
  flex-shrink: 0;
}

.info-row span:last-child {
  color: #303133;
}

:deep(.el-form-item) {
  margin-bottom: 16px;
}

:deep(.el-form-item__label) {
  font-size: 12px;
  color: #606266;
}
</style>