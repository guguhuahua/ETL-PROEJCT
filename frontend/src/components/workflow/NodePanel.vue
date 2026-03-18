<template>
  <div class="node-panel">
    <div class="panel-header">
      <h3>节点面板</h3>
    </div>
    <div class="panel-content">
      <div class="node-category">
        <div class="category-title">基础节点</div>
        <div class="node-list">
          <div
            class="node-item start-node"
            draggable="true"
            @dragstart="onDragStart($event, 'START')"
          >
            <span class="node-icon">&#9654;</span>
            <span class="node-label">开始节点</span>
          </div>
          <div
            class="node-item end-node"
            draggable="true"
            @dragstart="onDragStart($event, 'END')"
          >
            <span class="node-icon">&#9632;</span>
            <span class="node-label">结束节点</span>
          </div>
        </div>
      </div>

      <div class="node-category">
        <div class="category-title">任务节点</div>
        <div class="node-list">
          <div
            class="node-item task-node"
            draggable="true"
            @dragstart="onDragStart($event, 'TASK')"
          >
            <span class="node-icon">&#9881;</span>
            <span class="node-label">任务节点</span>
          </div>
        </div>
      </div>

      <div class="node-category">
        <div class="category-title">控制节点</div>
        <div class="node-list">
          <div
            class="node-item condition-node"
            draggable="true"
            @dragstart="onDragStart($event, 'CONDITION')"
          >
            <span class="node-icon">&#9671;</span>
            <span class="node-label">条件节点</span>
          </div>
          <div
            class="node-item parallel-node"
            draggable="true"
            @dragstart="onDragStart($event, 'PARALLEL')"
          >
            <span class="node-icon">&#11042;</span>
            <span class="node-label">并行节点</span>
          </div>
        </div>
      </div>
    </div>
    <div class="panel-footer">
      <el-button size="small" @click="showHelp = true">
        <el-icon><QuestionFilled /></el-icon>
        使用帮助
      </el-button>
    </div>

    <el-dialog v-model="showHelp" title="使用帮助" width="400px">
      <div class="help-content">
        <h4>节点说明</h4>
        <ul>
          <li><strong>开始节点</strong>：工作流的起始点，只能有一个</li>
          <li><strong>结束节点</strong>：工作流的结束点，可以有多个</li>
          <li><strong>任务节点</strong>：执行具体的 ELT 任务</li>
          <li><strong>条件节点</strong>：根据条件判断执行路径</li>
          <li><strong>并行节点</strong>：并行执行多个分支</li>
        </ul>
        <h4>操作说明</h4>
        <ul>
          <li>拖拽节点到画布添加</li>
          <li>从节点边缘拖拽创建连线</li>
          <li>点击节点查看/编辑属性</li>
          <li>右键节点删除</li>
        </ul>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { QuestionFilled } from '@element-plus/icons-vue'

const emit = defineEmits(['node-drag-start'])

const showHelp = ref(false)

const onDragStart = (event, nodeType) => {
  event.dataTransfer.setData('nodeType', nodeType)
  event.dataTransfer.effectAllowed = 'copy'
  emit('node-drag-start', nodeType)
}
</script>

<style scoped>
.node-panel {
  width: 220px;
  height: 100%;
  background: #fff;
  border-right: 1px solid #e4e7ed;
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
  padding: 12px;
}

.node-category {
  margin-bottom: 16px;
}

.category-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  padding-left: 4px;
}

.node-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.node-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: grab;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.node-item:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.node-item:active {
  cursor: grabbing;
}

.node-icon {
  font-size: 18px;
  margin-right: 10px;
  width: 24px;
  text-align: center;
}

.node-label {
  font-size: 13px;
  font-weight: 500;
}

.start-node {
  background: #E8F5E9;
  border-color: #4CAF50;
  color: #2E7D32;
}

.start-node:hover {
  background: #C8E6C9;
}

.end-node {
  background: #FFEBEE;
  border-color: #F44336;
  color: #C62828;
}

.end-node:hover {
  background: #FFCDD2;
}

.task-node {
  background: #E3F2FD;
  border-color: #2196F3;
  color: #1565C0;
}

.task-node:hover {
  background: #BBDEFB;
}

.condition-node {
  background: #FFF3E0;
  border-color: #FF9800;
  color: #EF6C00;
}

.condition-node:hover {
  background: #FFE0B2;
}

.parallel-node {
  background: #F3E5F5;
  border-color: #9C27B0;
  color: #7B1FA2;
}

.parallel-node:hover {
  background: #E1BEE7;
}

.panel-footer {
  padding: 12px;
  border-top: 1px solid #e4e7ed;
  text-align: center;
}

.help-content {
  font-size: 13px;
  line-height: 1.8;
}

.help-content h4 {
  margin: 12px 0 8px;
  color: #303133;
}

.help-content h4:first-child {
  margin-top: 0;
}

.help-content ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
}

.help-content li {
  margin: 4px 0;
}
</style>