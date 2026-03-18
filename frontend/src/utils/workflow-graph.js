/**
 * Workflow Graph Configuration for AntV G6
 * Custom nodes and graph utilities for workflow editor
 */
import G6 from '@antv/g6'

// Node colors - more professional color scheme
const NODE_COLORS = {
  START: { fill: '#E8F5E9', stroke: '#4CAF50', text: '#2E7D32', icon: '#4CAF50' },
  TASK: { fill: '#E3F2FD', stroke: '#2196F3', text: '#1565C0', icon: '#2196F3' },
  CONDITION: { fill: '#FFF8E1', stroke: '#FFA000', text: '#E65100', icon: '#FFA000' },
  PARALLEL: { fill: '#F3E5F5', stroke: '#9C27B0', text: '#7B1FA2', icon: '#9C27B0' },
  END: { fill: '#FFEBEE', stroke: '#E53935', text: '#C62828', icon: '#E53935' }
}

// Node icons (using unicode symbols)
const NODE_ICONS = {
  START: '▶',
  TASK: '⚙',
  CONDITION: '◆',
  PARALLEL: '⫿',
  END: '■'
}

/**
 * Register custom node types - all rectangular with rounded corners
 */
export function registerCustomNodes() {
  // Start Node - green rounded rectangle
  G6.registerNode('start-node', {
    options: {
      size: [120, 50],
      style: {
        radius: 6,
        fill: NODE_COLORS.START.fill,
        stroke: NODE_COLORS.START.stroke,
        lineWidth: 2
      },
      stateStyles: {
        selected: {
          stroke: '#1890ff',
          lineWidth: 3,
          shadowColor: '#1890ff',
          shadowBlur: 15
        },
        hover: {
          stroke: '#1890ff',
          lineWidth: 2
        }
      }
    },
    shapeType: 'rect',
    // Override drawShape to create custom node appearance
    drawShape(cfg, group) {
      const size = cfg.size || [120, 50]
      const width = size[0]
      const height = size[1]
      const colors = NODE_COLORS.START

      // Background - rounded rectangle
      const keyShape = group.addShape('rect', {
        attrs: {
          x: -width / 2,
          y: -height / 2,
          width,
          height,
          radius: 6,
          fill: colors.fill,
          stroke: colors.stroke,
          lineWidth: 2,
          cursor: 'move',
          shadowColor: 'rgba(0, 0, 0, 0.1)',
          shadowBlur: 4,
          shadowOffsetY: 2
        },
        name: 'key-shape',
        draggable: true
      })

      // Icon circle background
      group.addShape('circle', {
        attrs: {
          x: -width / 2 + 25,
          y: 0,
          r: 14,
          fill: colors.stroke,
          cursor: 'move'
        },
        name: 'icon-bg',
        draggable: true
      })

      // Icon
      group.addShape('text', {
        attrs: {
          x: -width / 2 + 25,
          y: 1,
          text: NODE_ICONS.START,
          fontSize: 12,
          fill: '#fff',
          textAlign: 'center',
          textBaseline: 'middle',
          cursor: 'move'
        },
        name: 'icon-shape',
        draggable: true
      })

      return keyShape
    },
    // Override drawLabel to place label inside node
    drawLabel(cfg, group) {
      const size = cfg.size || [120, 50]
      const width = size[0]

      return group.addShape('text', {
        attrs: {
          x: 15,
          y: 0,
          text: cfg.label || '开始',
          fontSize: 14,
          fontWeight: 500,
          fill: NODE_COLORS.START.text,
          textAlign: 'center',
          textBaseline: 'middle',
          cursor: 'move'
        },
        name: 'label-shape',
        draggable: true
      })
    },
    getAnchorPoints() {
      return [
        [0.5, 0], // top
        [1, 0.5], // right
        [0.5, 1], // bottom
        [0, 0.5]  // left
      ]
    },
    update(cfg, node) {
      const group = node.getContainer()
      const labelShape = group.find(e => e.get('name') === 'label-shape')
      if (labelShape) {
        labelShape.attr('text', cfg.label || '开始')
      }
    }
  }, 'single-node')

  // Task Node - blue rounded rectangle with task info
  G6.registerNode('task-node', {
    options: {
      size: [160, 70],
      style: {
        radius: 6,
        fill: NODE_COLORS.TASK.fill,
        stroke: NODE_COLORS.TASK.stroke,
        lineWidth: 2
      },
      stateStyles: {
        selected: {
          stroke: '#1890ff',
          lineWidth: 3,
          shadowColor: '#1890ff',
          shadowBlur: 15
        },
        hover: {
          stroke: '#1890ff',
          lineWidth: 2
        }
      }
    },
    shapeType: 'rect',
    drawShape(cfg, group) {
      const size = cfg.size || [160, 70]
      const width = size[0]
      const height = size[1]
      const colors = NODE_COLORS.TASK

      // Background
      const keyShape = group.addShape('rect', {
        attrs: {
          x: -width / 2,
          y: -height / 2,
          width,
          height,
          radius: 6,
          fill: colors.fill,
          stroke: colors.stroke,
          lineWidth: 2,
          cursor: 'move',
          shadowColor: 'rgba(0, 0, 0, 0.1)',
          shadowBlur: 4,
          shadowOffsetY: 2
        },
        name: 'key-shape',
        draggable: true
      })

      // Icon circle background
      group.addShape('circle', {
        attrs: {
          x: -width / 2 + 25,
          y: -height / 2 + 25,
          r: 14,
          fill: colors.stroke,
          cursor: 'move'
        },
        name: 'icon-bg',
        draggable: true
      })

      // Icon
      group.addShape('text', {
        attrs: {
          x: -width / 2 + 25,
          y: -height / 2 + 26,
          text: NODE_ICONS.TASK,
          fontSize: 12,
          fill: '#fff',
          textAlign: 'center',
          textBaseline: 'middle',
          cursor: 'move'
        },
        name: 'icon-shape',
        draggable: true
      })

      // Task name (second line)
      const taskNameText = cfg.taskName || '未关联任务'
      group.addShape('text', {
        attrs: {
          x: 10,
          y: -height / 2 + 48,
          text: taskNameText,
          fontSize: 11,
          fill: cfg.taskName ? '#666' : '#999',
          textAlign: 'left',
          textBaseline: 'middle',
          cursor: 'move'
        },
        name: 'task-name-shape',
        draggable: true
      })

      // Status indicator
      if (cfg.taskId) {
        group.addShape('circle', {
          attrs: {
            x: width / 2 - 15,
            y: -height / 2 + 15,
            r: 4,
            fill: '#4CAF50',
            cursor: 'move'
          },
          name: 'status-indicator',
          draggable: true
        })
      }

      return keyShape
    },
    drawLabel(cfg, group) {
      const size = cfg.size || [160, 70]
      const height = size[1]

      return group.addShape('text', {
        attrs: {
          x: 10,
          y: -height / 2 + 25,
          text: cfg.label || '任务节点',
          fontSize: 14,
          fontWeight: 500,
          fill: NODE_COLORS.TASK.text,
          textAlign: 'left',
          textBaseline: 'middle',
          cursor: 'move'
        },
        name: 'label-shape',
        draggable: true
      })
    },
    getAnchorPoints() {
      return [
        [0.5, 0],
        [1, 0.5],
        [0.5, 1],
        [0, 0.5]
      ]
    },
    update(cfg, node) {
      const group = node.getContainer()
      const labelShape = group.find(e => e.get('name') === 'label-shape')
      const taskNameShape = group.find(e => e.get('name') === 'task-name-shape')

      if (labelShape) {
        labelShape.attr('text', cfg.label || '任务节点')
      }
      if (taskNameShape) {
        taskNameShape.attr({
          text: cfg.taskName || '未关联任务',
          fill: cfg.taskName ? '#666' : '#999'
        })
      }
    }
  }, 'single-node')

  // Condition Node - orange diamond-shaped (still diamond for visual distinction)
  G6.registerNode('condition-node', {
    options: {
      size: [70, 70],
      style: {
        fill: NODE_COLORS.CONDITION.fill,
        stroke: NODE_COLORS.CONDITION.stroke,
        lineWidth: 2
      },
      stateStyles: {
        selected: {
          stroke: '#1890ff',
          lineWidth: 3,
          shadowColor: '#1890ff',
          shadowBlur: 15
        },
        hover: {
          stroke: '#1890ff',
          lineWidth: 2
        }
      }
    },
    shapeType: 'path',
    drawShape(cfg, group) {
      const size = 70
      const colors = NODE_COLORS.CONDITION

      // Diamond shape
      const keyShape = group.addShape('path', {
        attrs: {
          path: [
            ['M', 0, -size / 2],
            ['L', size / 2, 0],
            ['L', 0, size / 2],
            ['L', -size / 2, 0],
            ['Z']
          ],
          fill: colors.fill,
          stroke: colors.stroke,
          lineWidth: 2,
          cursor: 'move',
          shadowColor: 'rgba(0, 0, 0, 0.1)',
          shadowBlur: 4,
          shadowOffsetY: 2
        },
        name: 'key-shape',
        draggable: true
      })

      // Icon
      group.addShape('text', {
        attrs: {
          x: 0,
          y: 0,
          text: NODE_ICONS.CONDITION,
          fontSize: 18,
          fill: colors.icon,
          textAlign: 'center',
          textBaseline: 'middle',
          cursor: 'move'
        },
        name: 'icon-shape',
        draggable: true
      })

      return keyShape
    },
    drawLabel(cfg, group) {
      // Condition node doesn't have internal label, icon serves as visual indicator
      return null
    },
    getAnchorPoints() {
      return [
        [0.5, 0],
        [1, 0.5],
        [0.5, 1],
        [0, 0.5]
      ]
    }
  }, 'single-node')

  // Parallel Node - purple rounded rectangle
  G6.registerNode('parallel-node', {
    options: {
      size: [140, 50],
      style: {
        radius: 6,
        fill: NODE_COLORS.PARALLEL.fill,
        stroke: NODE_COLORS.PARALLEL.stroke,
        lineWidth: 2,
        lineDash: [5, 5]
      },
      stateStyles: {
        selected: {
          stroke: '#1890ff',
          lineWidth: 3,
          shadowColor: '#1890ff',
          shadowBlur: 15
        },
        hover: {
          stroke: '#1890ff',
          lineWidth: 2
        }
      }
    },
    shapeType: 'rect',
    drawShape(cfg, group) {
      const size = cfg.size || [140, 50]
      const width = size[0]
      const height = size[1]
      const colors = NODE_COLORS.PARALLEL

      // Background
      const keyShape = group.addShape('rect', {
        attrs: {
          x: -width / 2,
          y: -height / 2,
          width,
          height,
          radius: 6,
          fill: colors.fill,
          stroke: colors.stroke,
          lineWidth: 2,
          lineDash: [5, 5],
          cursor: 'move',
          shadowColor: 'rgba(0, 0, 0, 0.1)',
          shadowBlur: 4,
          shadowOffsetY: 2
        },
        name: 'key-shape',
        draggable: true
      })

      // Icon circle background
      group.addShape('circle', {
        attrs: {
          x: -width / 2 + 22,
          y: 0,
          r: 12,
          fill: colors.stroke,
          cursor: 'move'
        },
        name: 'icon-bg',
        draggable: true
      })

      // Icon
      group.addShape('text', {
        attrs: {
          x: -width / 2 + 22,
          y: 1,
          text: NODE_ICONS.PARALLEL,
          fontSize: 11,
          fill: '#fff',
          textAlign: 'center',
          textBaseline: 'middle',
          cursor: 'move'
        },
        name: 'icon-shape',
        draggable: true
      })

      return keyShape
    },
    drawLabel(cfg, group) {
      const size = cfg.size || [140, 50]
      const width = size[0]

      return group.addShape('text', {
        attrs: {
          x: 15,
          y: 0,
          text: cfg.label || '并行执行',
          fontSize: 14,
          fontWeight: 500,
          fill: NODE_COLORS.PARALLEL.text,
          textAlign: 'center',
          textBaseline: 'middle',
          cursor: 'move'
        },
        name: 'label-shape',
        draggable: true
      })
    },
    getAnchorPoints() {
      return [
        [0.5, 0],
        [1, 0.5],
        [0.5, 1],
        [0, 0.5]
      ]
    },
    update(cfg, node) {
      const group = node.getContainer()
      const labelShape = group.find(e => e.get('name') === 'label-shape')
      if (labelShape) {
        labelShape.attr('text', cfg.label || '并行执行')
      }
    }
  }, 'single-node')

  // End Node - red rounded rectangle
  G6.registerNode('end-node', {
    options: {
      size: [120, 50],
      style: {
        radius: 6,
        fill: NODE_COLORS.END.fill,
        stroke: NODE_COLORS.END.stroke,
        lineWidth: 2
      },
      stateStyles: {
        selected: {
          stroke: '#1890ff',
          lineWidth: 3,
          shadowColor: '#1890ff',
          shadowBlur: 15
        },
        hover: {
          stroke: '#1890ff',
          lineWidth: 2
        }
      }
    },
    shapeType: 'rect',
    drawShape(cfg, group) {
      const size = cfg.size || [120, 50]
      const width = size[0]
      const height = size[1]
      const colors = NODE_COLORS.END

      // Background
      const keyShape = group.addShape('rect', {
        attrs: {
          x: -width / 2,
          y: -height / 2,
          width,
          height,
          radius: 6,
          fill: colors.fill,
          stroke: colors.stroke,
          lineWidth: 2,
          cursor: 'move',
          shadowColor: 'rgba(0, 0, 0, 0.1)',
          shadowBlur: 4,
          shadowOffsetY: 2
        },
        name: 'key-shape',
        draggable: true
      })

      // Icon circle background
      group.addShape('circle', {
        attrs: {
          x: -width / 2 + 25,
          y: 0,
          r: 14,
          fill: colors.stroke,
          cursor: 'move'
        },
        name: 'icon-bg',
        draggable: true
      })

      // Icon
      group.addShape('text', {
        attrs: {
          x: -width / 2 + 25,
          y: 1,
          text: NODE_ICONS.END,
          fontSize: 12,
          fill: '#fff',
          textAlign: 'center',
          textBaseline: 'middle',
          cursor: 'move'
        },
        name: 'icon-shape',
        draggable: true
      })

      return keyShape
    },
    drawLabel(cfg, group) {
      const size = cfg.size || [120, 50]
      const width = size[0]

      return group.addShape('text', {
        attrs: {
          x: 15,
          y: 0,
          text: cfg.label || '结束',
          fontSize: 14,
          fontWeight: 500,
          fill: NODE_COLORS.END.text,
          textAlign: 'center',
          textBaseline: 'middle',
          cursor: 'move'
        },
        name: 'label-shape',
        draggable: true
      })
    },
    getAnchorPoints() {
      return [
        [0.5, 0],
        [1, 0.5],
        [0.5, 1],
        [0, 0.5]
      ]
    },
    update(cfg, node) {
      const group = node.getContainer()
      const labelShape = group.find(e => e.get('name') === 'label-shape')
      if (labelShape) {
        labelShape.attr('text', cfg.label || '结束')
      }
    }
  }, 'single-node')
}

/**
 * Get node type for G6
 */
export function getNodeType(type) {
  const typeMap = {
    START: 'start-node',
    TASK: 'task-node',
    CONDITION: 'condition-node',
    PARALLEL: 'parallel-node',
    END: 'end-node'
  }
  return typeMap[type] || 'task-node'
}

/**
 * Create graph configuration
 */
export function createGraphConfig(container, width, height) {
  return {
    container,
    width,
    height,
    modes: {
      default: [
        'drag-canvas',
        'zoom-canvas',
        'drag-node',
        {
          type: 'create-edge',
          trigger: 'drag',
          shouldBegin: (e) => {
            // Only allow creating edges from key-shape (node body)
            return e.target && e.target.get('name') === 'key-shape'
          },
          shouldEnd: (e) => {
            // Only allow ending on key-shape of another node
            return e.target && e.target.get('name') === 'key-shape'
          }
        }
      ]
    },
    defaultNode: {
      type: 'task-node',
      size: [160, 70]
    },
    defaultEdge: {
      type: 'polyline',
      style: {
        stroke: '#aab7c4',
        lineWidth: 2,
        endArrow: {
          path: G6.Arrow.triangle(8, 10, 0),
          fill: '#aab7c4'
        },
        radius: 8
      }
    },
    nodeStateStyles: {
      selected: {
        stroke: '#1890ff',
        lineWidth: 3,
        shadowColor: '#1890ff',
        shadowBlur: 15
      },
      hover: {
        stroke: '#1890ff',
        lineWidth: 2
      }
    },
    edgeStateStyles: {
      selected: {
        stroke: '#1890ff',
        lineWidth: 3
      },
      hover: {
        stroke: '#1890ff',
        lineWidth: 2
      }
    }
  }
}

/**
 * Convert workflow data to G6 format
 */
export function workflowToG6Data(workflow) {
  if (!workflow || !workflow.nodes) {
    return { nodes: [], edges: [] }
  }

  const nodes = workflow.nodes.map(node => ({
    id: node.id,
    type: getNodeType(node.type),
    label: node.label,
    x: node.x,
    y: node.y,
    taskId: node.taskId,
    taskName: node.taskName,
    condition: node.condition,
    branches: node.branches,
    ...node
  }))

  const edges = (workflow.edges || []).map((edge, index) => ({
    id: edge.id || `edge_${index}`,
    source: edge.source,
    target: edge.target,
    label: edge.label || '',
    condition: edge.condition
  }))

  return { nodes, edges }
}

/**
 * Convert G6 data to workflow format
 */
export function g6DataToWorkflow(graph) {
  const nodes = graph.getNodes().map(node => {
    const model = node.getModel()
    return {
      id: model.id,
      type: model.nodeType || model.type.replace('-node', '').toUpperCase(),
      label: model.label,
      x: model.x,
      y: model.y,
      taskId: model.taskId,
      taskName: model.taskName,
      condition: model.condition,
      branches: model.branches
    }
  })

  const edges = graph.getEdges().map((edge, index) => {
    const model = edge.getModel()
    return {
      id: model.id || `edge_${index}`,
      source: model.source,
      target: model.target,
      label: model.label || '',
      condition: model.condition
    }
  })

  return { nodes, edges }
}

/**
 * Generate unique ID
 */
export function generateId(prefix = 'node') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Get node default label by type
 */
export function getDefaultLabel(type) {
  const labels = {
    START: '开始',
    TASK: '任务节点',
    CONDITION: '条件判断',
    PARALLEL: '并行执行',
    END: '结束'
  }
  return labels[type] || '节点'
}

/**
 * Get node default size by type
 */
export function getDefaultSize(type) {
  const sizes = {
    START: [120, 50],
    TASK: [160, 70],
    CONDITION: [70, 70],
    PARALLEL: [140, 50],
    END: [120, 50]
  }
  return sizes[type] || [120, 50]
}

export default {
  registerCustomNodes,
  getNodeType,
  createGraphConfig,
  workflowToG6Data,
  g6DataToWorkflow,
  generateId,
  getDefaultLabel,
  getDefaultSize,
  NODE_COLORS,
  NODE_ICONS
}