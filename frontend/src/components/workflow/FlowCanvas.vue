<template>
  <div
    class="flow-canvas-container"
    @dragover.prevent
    @drop="handleDrop"
  >
    <div ref="canvasContainer" class="canvas-wrapper"></div>
    <div class="canvas-toolbar">
      <el-button-group>
        <el-button size="small" @click="zoomIn" title="放大">
          <el-icon><ZoomIn /></el-icon>
        </el-button>
        <el-button size="small" @click="zoomOut" title="缩小">
          <el-icon><ZoomOut /></el-icon>
        </el-button>
        <el-button size="small" @click="fitView" title="适应画布">
          <el-icon><FullScreen /></el-icon>
        </el-button>
        <el-button size="small" @click="clearCanvas" title="清空画布">
          <el-icon><Delete /></el-icon>
        </el-button>
      </el-button-group>
      <div class="toolbar-hint">
        <el-tooltip content="从节点边缘拖拽可创建连线" placement="bottom">
          <el-icon><InfoFilled /></el-icon>
        </el-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import G6 from '@antv/g6'
import {
  registerCustomNodes,
  createGraphConfig,
  workflowToG6Data,
  g6DataToWorkflow,
  generateId,
  getDefaultLabel,
  getDefaultSize
} from '@/utils/workflow-graph'
import { ZoomIn, ZoomOut, FullScreen, Delete, InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  workflowData: {
    type: Object,
    default: () => ({ nodes: [], edges: [] })
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['node-select', 'edge-select', 'canvas-click', 'data-change'])

const canvasContainer = ref(null)
let graph = null
let isInternalUpdate = false  // Flag to prevent recursive updates

// Initialize graph
const initGraph = () => {
  if (!canvasContainer.value) return

  // Register custom nodes
  registerCustomNodes()

  const width = canvasContainer.value.offsetWidth
  const height = canvasContainer.value.offsetHeight

  const config = createGraphConfig(canvasContainer.value, width, height)

  graph = new G6.Graph(config)

  // Bind events
  graph.on('node:click', (evt) => {
    const node = evt.item
    const model = node.getModel()
    // Deselect others
    graph.getNodes().forEach(n => {
      if (n !== node) graph.setItemState(n, 'selected', false)
    })
    graph.setItemState(node, 'selected', true)
    emit('node-select', model)
  })

  graph.on('node:mouseenter', (evt) => {
    const node = evt.item
    graph.setItemState(node, 'hover', true)
  })

  graph.on('node:mouseleave', (evt) => {
    const node = evt.item
    graph.setItemState(node, 'hover', false)
  })

  graph.on('edge:click', (evt) => {
    const edge = evt.item
    const model = edge.getModel()
    // Deselect others
    graph.getEdges().forEach(e => {
      if (e !== edge) graph.setItemState(e, 'selected', false)
    })
    graph.setItemState(edge, 'selected', true)
    emit('edge-select', model)
  })

  graph.on('edge:mouseenter', (evt) => {
    const edge = evt.item
    graph.setItemState(edge, 'hover', true)
  })

  graph.on('edge:mouseleave', (evt) => {
    const edge = evt.item
    graph.setItemState(edge, 'hover', false)
  })

  graph.on('canvas:click', () => {
    // Deselect all
    graph.getNodes().forEach(node => {
      graph.setItemState(node, 'selected', false)
    })
    graph.getEdges().forEach(edge => {
      graph.setItemState(edge, 'selected', false)
    })
    emit('canvas-click')
  })

  graph.on('afteradditem', (evt) => {
    emitDataChange()
    // Focus on newly added item
    if (evt.item && evt.item.getType() === 'node') {
      focusOnNode(evt.item.getModel().id)
    }
  })

  graph.on('afterremoveitem', () => {
    emitDataChange()
  })

  graph.on('afterupdateitem', () => {
    emitDataChange()
  })

  // Handle edge creation - show tooltip
  graph.on('aftercreateedge', (evt) => {
    const edge = evt.item
    const model = edge.getModel()
    console.log('Edge created:', model)

    // Focus the graph to show the new edge
    graph.fitView(20)
  })

  // Load initial data
  if (props.workflowData && props.workflowData.nodes && props.workflowData.nodes.length > 0) {
    const data = workflowToG6Data(props.workflowData)
    graph.data(data)
    graph.render()
    graph.fitView(20)
  } else {
    graph.render()
  }
}

// Add node from drag
const addNode = (type, x, y, customData = {}) => {
  console.log('addNode called:', { type, x, y, graph: !!graph, readonly: props.readonly })

  if (!graph) {
    console.error('Graph not initialized')
    return null
  }

  if (props.readonly) {
    console.warn('Canvas is in readonly mode')
    return null
  }

  const id = generateId('node')
  const size = getDefaultSize(type)
  const label = getDefaultLabel(type)

  const node = {
    id,
    type: getNodeType(type),
    label,
    x,
    y,
    size,
    nodeType: type,
    ...customData
  }

  console.log('Adding node to graph:', node)

  try {
    graph.addItem('node', node)
    console.log('Node added to graph successfully')

    // Focus on the new node
    nextTick(() => {
      focusOnNode(id)
    })

    return node
  } catch (error) {
    console.error('Error adding node to graph:', error)
    return null
  }
}

// Get node type for G6
const getNodeType = (type) => {
  const typeMap = {
    START: 'start-node',
    TASK: 'task-node',
    CONDITION: 'condition-node',
    PARALLEL: 'parallel-node',
    END: 'end-node'
  }
  return typeMap[type] || 'task-node'
}

// Focus on a specific node
const focusOnNode = (nodeId) => {
  if (!graph) return

  const node = graph.findById(nodeId)
  if (node) {
    const model = node.getModel()
    const width = canvasContainer.value?.offsetWidth || 800
    const height = canvasContainer.value?.offsetHeight || 600

    // Center the view on the node
    graph.focusItem(node, true, {
      easing: 'easeCubicOut',
      duration: 300
    })
  }
}

// Delete selected node
const deleteNode = (nodeId) => {
  if (!graph || props.readonly) return
  graph.removeItem(nodeId)
}

// Delete selected edge
const deleteEdge = (edgeId) => {
  if (!graph || props.readonly) return
  graph.removeItem(edgeId)
}

// Update node data
const updateNode = (nodeId, data) => {
  if (!graph) return

  const node = graph.findById(nodeId)
  if (node) {
    const model = node.getModel()
    graph.updateItem(node, {
      ...data,
      label: data.label || model.label
    })
  }
}

// Get current workflow data
const getWorkflowData = () => {
  if (!graph) return { nodes: [], edges: [] }
  return g6DataToWorkflow(graph)
}

// Emit data change
const emitDataChange = () => {
  if (isInternalUpdate) return  // Skip if this is an internal update

  const data = getWorkflowData()
  emit('data-change', data)
}

// Toolbar actions
const zoomIn = () => {
  if (graph) {
    const zoom = graph.getZoom()
    graph.zoomTo(zoom * 1.2, { x: canvasContainer.value.offsetWidth / 2, y: canvasContainer.value.offsetHeight / 2 })
  }
}

const zoomOut = () => {
  if (graph) {
    const zoom = graph.getZoom()
    graph.zoomTo(zoom / 1.2, { x: canvasContainer.value.offsetWidth / 2, y: canvasContainer.value.offsetHeight / 2 })
  }
}

const fitView = () => {
  if (graph) {
    graph.fitView(20)
  }
}

const clearCanvas = () => {
  if (!graph || props.readonly) return

  graph.clear()
  emit('data-change', { nodes: [], edges: [] })
}

// Handle resize
const handleResize = () => {
  if (graph && canvasContainer.value) {
    graph.changeSize(canvasContainer.value.offsetWidth, canvasContainer.value.offsetHeight)
  }
}

// Handle drop event directly on canvas
const handleDrop = (event) => {
  event.preventDefault()
  console.log('FlowCanvas handleDrop triggered')

  // Get node type from dataTransfer
  const nodeType = event.dataTransfer?.getData('nodeType')
  if (!nodeType) {
    console.warn('No nodeType in dataTransfer')
    return
  }

  if (!graph) {
    console.error('Graph not initialized when dropping')
    return
  }

  // Get drop position relative to canvas wrapper
  const rect = canvasContainer.value?.getBoundingClientRect()
  if (!rect) {
    console.warn('Canvas container rect not found')
    return
  }

  let x = event.clientX - rect.left
  let y = event.clientY - rect.top

  // Convert canvas coordinates to graph coordinates (account for zoom/pan)
  const point = graph.getPointByClient(event.clientX, event.clientY)
  x = point.x
  y = point.y

  console.log('Dropping node on canvas:', nodeType, 'at graph coordinates', x, y)

  addNode(nodeType, x, y)
}

// Watch for workflow data changes - only for external updates (loading saved workflow)
watch(() => props.workflowData, (newData, oldData) => {
  if (!graph || !newData) return

  // Skip if this update came from internal graph changes
  if (isInternalUpdate) return

  // Compare node and edge counts to detect actual external changes
  const newNodeCount = newData.nodes?.length || 0
  const oldNodeCount = oldData?.nodes?.length || 0
  const newEdgeCount = newData.edges?.length || 0
  const oldEdgeCount = oldData?.edges?.length || 0

  // Only re-render if there's an actual external change (like loading a saved workflow)
  if (newNodeCount !== oldNodeCount || newEdgeCount !== oldEdgeCount) {
    isInternalUpdate = true
    graph.clear()
    if (newData.nodes && newData.nodes.length > 0) {
      const data = workflowToG6Data(newData)
      graph.data(data)
      graph.render()
      graph.fitView(20)
    }
    isInternalUpdate = false
  }
}, { deep: true })

onMounted(() => {
  nextTick(() => {
    initGraph()
  })
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (graph) {
    graph.destroy()
    graph = null
  }
  window.removeEventListener('resize', handleResize)
})

// Expose methods
defineExpose({
  addNode,
  deleteNode,
  deleteEdge,
  updateNode,
  getWorkflowData,
  fitView,
  focusOnNode
})
</script>

<style scoped>
.flow-canvas-container {
  width: 100%;
  height: 100%;
  position: relative;
  background: #f5f7fa;
  background-image:
    linear-gradient(rgba(0, 0, 0, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 0, 0, 0.03) 1px, transparent 1px);
  background-size: 20px 20px;
}

.canvas-wrapper {
  width: 100%;
  height: 100%;
}

.canvas-toolbar {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-hint {
  padding: 4px 8px;
  color: #909399;
  cursor: help;
}

.toolbar-hint:hover {
  color: #606266;
}
</style>