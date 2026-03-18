<template>
  <div class="workflow-editor" @dragover.prevent @drop="handleDrop">
    <!-- Header -->
    <div class="editor-header">
      <div class="header-left">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <el-divider direction="vertical" />
        <h2>{{ isNew ? '新建工作流' : '编辑工作流' }}</h2>
      </div>
      <div class="header-right">
        <el-button @click="saveWorkflow" type="primary" :loading="saving">
          <el-icon><Check /></el-icon>
          保存工作流
        </el-button>
        <el-button @click="executeWorkflow" type="success" :disabled="isNew || !workflow.is_active" :loading="executing">
          <el-icon><VideoPlay /></el-icon>
          执行工作流
        </el-button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="editor-content" ref="editorContent">
      <!-- Left Panel: Node Types -->
      <NodePanel @node-drag-start="handleNodeDragStart" />

      <!-- Center: Flow Canvas -->
      <FlowCanvas
        ref="flowCanvasRef"
        :workflow-data="workflowData"
        :readonly="false"
        @node-select="handleNodeSelect"
        @edge-select="handleEdgeSelect"
        @canvas-click="handleCanvasClick"
        @data-change="handleDataChange"
      />

      <!-- Right Panel: Properties -->
      <PropertyPanel
        :selected-node="selectedNode"
        :workflow="workflow"
        @update-node="handleUpdateNode"
        @delete-node="handleDeleteNode"
        @update-workflow="handleUpdateWorkflow"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Check, VideoPlay } from '@element-plus/icons-vue'
import NodePanel from '@/components/workflow/NodePanel.vue'
import FlowCanvas from '@/components/workflow/FlowCanvas.vue'
import PropertyPanel from '@/components/workflow/PropertyPanel.vue'
import api from '@/api'

const route = useRoute()
const router = useRouter()

const flowCanvasRef = ref(null)
const selectedNode = ref(null)
const selectedEdge = ref(null)
const saving = ref(false)
const executing = ref(false)
const isDragging = ref(false)
const dragNodeType = ref(null)

const isNew = computed(() => !route.params.id)

const workflow = reactive({
  id: null,
  name: '',
  description: '',
  trigger_type: 'manual',
  trigger_config: {},
  is_active: true
})

const workflowData = ref({
  nodes: [],
  edges: []
})

// Handle node drag start
const handleNodeDragStart = (nodeType) => {
  isDragging.value = true
  dragNodeType.value = nodeType
}

// Handle drop on canvas - this is now handled by FlowCanvas component
// This handler is kept as a fallback
const handleDrop = (event) => {
  // The FlowCanvas component handles the drop directly
  // This is just a fallback in case the event bubbles up
  console.log('WorkflowEditor handleDrop (fallback)')
}

// Handle node selection
const handleNodeSelect = (node) => {
  selectedNode.value = node
  selectedEdge.value = null
}

// Handle edge selection
const handleEdgeSelect = (edge) => {
  selectedEdge.value = edge
  selectedNode.value = null
}

// Handle canvas click (deselect)
const handleCanvasClick = () => {
  selectedNode.value = null
  selectedEdge.value = null
}

// Handle data change from canvas
const handleDataChange = (data) => {
  workflowData.value = data
}

// Handle node update from property panel
const handleUpdateNode = (nodeId, data) => {
  if (flowCanvasRef.value) {
    flowCanvasRef.value.updateNode(nodeId, data)
  }
}

// Handle node delete from property panel
const handleDeleteNode = (nodeId) => {
  ElMessageBox.confirm('确定要删除该节点吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    if (flowCanvasRef.value) {
      flowCanvasRef.value.deleteNode(nodeId)
      selectedNode.value = null
    }
  }).catch(() => {})
}

// Handle workflow update from property panel
const handleUpdateWorkflow = (data) => {
  Object.assign(workflow, data)
}

// Save workflow
const saveWorkflow = async () => {
  // Validation
  if (!workflow.name) {
    ElMessage.warning('请输入工作流名称')
    return
  }

  // Get current workflow data from canvas
  const currentData = flowCanvasRef.value?.getWorkflowData() || workflowData.value

  // Validate nodes
  if (!currentData.nodes || currentData.nodes.length === 0) {
    ElMessage.warning('请至少添加一个节点')
    return
  }

  // Check for start node
  const hasStart = currentData.nodes.some(n => n.type === 'START')
  if (!hasStart) {
    ElMessage.warning('工作流必须包含一个开始节点')
    return
  }

  // Check for end node
  const hasEnd = currentData.nodes.some(n => n.type === 'END')
  if (!hasEnd) {
    ElMessage.warning('工作流必须包含至少一个结束节点')
    return
  }

  // Validate task nodes have taskId
  const taskNodesWithoutTask = currentData.nodes.filter(n => n.type === 'TASK' && !n.taskId)
  if (taskNodesWithoutTask.length > 0) {
    ElMessage.warning('所有任务节点必须关联一个ELT任务')
    return
  }

  saving.value = true

  try {
    const payload = {
      name: workflow.name,
      description: workflow.description,
      trigger_type: workflow.trigger_type,
      trigger_config: workflow.trigger_config,
      is_active: workflow.is_active,
      nodes: currentData.nodes,
      edges: currentData.edges
    }

    let response
    if (isNew.value) {
      response = await api.workflows.create(payload)
    } else {
      response = await api.workflows.update(workflow.id, payload)
    }

    ElMessage.success(isNew.value ? '工作流创建成功' : '工作流更新成功')

    if (isNew.value && response.id) {
      router.replace({ name: 'WorkflowEdit', params: { id: response.id } })
    }
  } catch (error) {
    console.error('Failed to save workflow:', error)
    ElMessage.error(error.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// Execute workflow
const executeWorkflow = async () => {
  if (isNew.value) {
    ElMessage.warning('请先保存工作流')
    return
  }

  ElMessageBox.confirm(
    '确定要立即执行该工作流吗？',
    '执行确认',
    {
      confirmButtonText: '执行',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(async () => {
    executing.value = true

    try {
      await api.workflows.execute(workflow.id)
      ElMessage.success('工作流已开始执行')

      // Navigate to execution history
      router.push({ name: 'WorkflowList' })
    } catch (error) {
      console.error('Failed to execute workflow:', error)
      ElMessage.error(error.response?.data?.message || '执行失败')
    } finally {
      executing.value = false
    }
  }).catch(() => {})
}

// Load workflow data for editing
const loadWorkflow = async (id) => {
  try {
    const response = await api.workflows.getById(id)
    const data = response.data || response

    workflow.id = data.id
    workflow.name = data.name
    workflow.description = data.description
    workflow.trigger_type = data.trigger_type
    workflow.trigger_config = data.trigger_config || {}
    workflow.is_active = data.is_active

    // Load nodes and edges
    workflowData.value = {
      nodes: data.nodes || [],
      edges: data.edges || []
    }
  } catch (error) {
    console.error('Failed to load workflow:', error)
    ElMessage.error('加载工作流失败')
    router.push({ name: 'WorkflowList' })
  }
}

// Go back to list
const goBack = () => {
  ElMessageBox.confirm(
    '确定要离开吗？未保存的更改将丢失。',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    router.push({ name: 'WorkflowList' })
  }).catch(() => {})
}

// Handle drag events globally
const handleGlobalDragEnd = () => {
  isDragging.value = false
  dragNodeType.value = null
}

onMounted(() => {
  // Load workflow if editing
  if (!isNew.value) {
    loadWorkflow(route.params.id)
  }

  // Add global drag end listener
  document.addEventListener('dragend', handleGlobalDragEnd)
})

onUnmounted(() => {
  document.removeEventListener('dragend', handleGlobalDragEnd)
})
</script>

<style scoped>
.workflow-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.editor-header {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.header-right {
  display: flex;
  gap: 10px;
}

.editor-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.drop-overlay {
  position: fixed;
  top: 56px;
  left: 220px;
  right: 280px;
  bottom: 0;
  background: rgba(64, 158, 255, 0.1);
  border: 2px dashed #409eff;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.drop-hint {
  font-size: 16px;
  color: #409eff;
  background: #fff;
  padding: 12px 24px;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

:deep(.el-divider--vertical) {
  height: 20px;
}
</style>