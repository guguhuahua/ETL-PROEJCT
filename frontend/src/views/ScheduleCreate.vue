<template>
  <div class="schedule-create">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑调度' : '创建调度' }}</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        style="max-width: 800px;"
      >
        <el-form-item label="调度名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入调度名称" />
        </el-form-item>

        <el-form-item label="关联任务" prop="task_id">
          <el-select v-model="formData.task_id" placeholder="请选择关联的任务" style="width: 100%;">
            <el-option v-for="task in tasks" :key="task.id" :label="task.name" :value="task.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="调度类型" prop="schedule_type">
          <el-select v-model="formData.schedule_type" placeholder="请选择调度类型" style="width: 100%;" @change="resetScheduleConfig">
            <el-option label="Cron表达式" value="cron" />
            <el-option label="时间间隔" value="interval" />
            <el-option label="指定时间" value="date" />
          </el-select>
        </el-form-item>

        <!-- Cron Config -->
        <template v-if="formData.schedule_type === 'cron'">
          <el-form-item label="Cron表达式" prop="schedule_config.cron_expression">
            <el-input v-model="formData.schedule_config.cron_expression" placeholder="例如: 0 2 * * *" />
          </el-form-item>
          <el-form-item>
            <div class="cron-helper">
              <strong>Cron表达式说明:</strong>
              <div>格式: 分 时 日 月 周</div>
              <div class="cron-examples">
                <div>每分钟执行: * * * * *</div>
                <div>每小时执行: 0 * * * *</div>
                <div>每天凌晨2点执行: 0 2 * * *</div>
                <div>每周一上午6点执行: 0 6 * * 1</div>
                <div>每月1号上午3点执行: 0 3 1 * *</div>
              </div>
            </div>
          </el-form-item>
        </template>

        <!-- Interval Config -->
        <template v-if="formData.schedule_type === 'interval'">
          <el-form-item label="间隔时间">
            <el-col :span="12">
              <el-input-number v-model="intervalAmount" :min="1" style="width: 100%;" />
            </el-col>
            <el-col :span="12">
              <el-select v-model="intervalUnit" style="width: 100%;">
                <el-option label="秒" value="seconds" />
                <el-option label="分钟" value="minutes" />
                <el-option label="小时" value="hours" />
                <el-option label="天" value="days" />
              </el-select>
            </el-col>
          </el-form-item>
        </template>

        <!-- Date Config -->
        <template v-if="formData.schedule_type === 'date'">
          <el-form-item label="执行时间" prop="schedule_config.run_time">
            <el-date-picker
              v-model="formData.schedule_config.run_time"
              type="datetime"
              placeholder="选择执行时间"
              style="width: 100%;"
            />
          </el-form-item>
        </template>

        <el-divider>高级配置</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="失败重试次数">
              <el-input-number v-model="formData.retry_count" :min="0" :max="10" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="重试间隔(秒)">
              <el-input-number v-model="formData.retry_interval" :min="1" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="依赖任务">
          <el-select v-model="formData.dependencies" multiple placeholder="选择依赖任务" style="width: 100%;">
            <el-option v-for="task in tasks" :key="task.id" :label="task.name" :value="task.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="立即启用">
          <el-switch v-model="formData.is_active" />
        </el-form-item>

        <el-form-item>
          <el-button @click="$router.back()">取消</el-button>
          <el-button type="primary" @click="saveSchedule">保存调度</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const route = useRoute()
const router = useRouter()

const isEdit = ref(false)
const formRef = ref(null)
const tasks = ref([])

const intervalAmount = ref(1)
const intervalUnit = ref('hours')

const formData = reactive({
  name: '',
  task_id: null,
  schedule_type: 'cron',
  schedule_config: {
    cron_expression: '',
    interval_seconds: 3600,
    run_time: null
  },
  dependencies: [],
  retry_count: 3,
  retry_interval: 300,
  is_active: true
})

const formRules = {
  name: [{ required: true, message: '请输入调度名称', trigger: 'blur' }],
  task_id: [{ required: true, message: '请选择关联任务', trigger: 'change' }],
  schedule_type: [{ required: true, message: '请选择调度类型', trigger: 'change' }]
}

// Watch interval changes
watch([intervalAmount, intervalUnit], () => {
  const multipliers = {
    seconds: 1,
    minutes: 60,
    hours: 3600,
    days: 86400
  }
  formData.schedule_config.interval_seconds = intervalAmount.value * multipliers[intervalUnit.value]
})

const resetScheduleConfig = () => {
  formData.schedule_config = {
    cron_expression: '',
    interval_seconds: 3600,
    run_time: null
  }
}

const loadTasks = async () => {
  try {
    tasks.value = await api.eltTasks.getAll()
  } catch (error) {
    console.error('Failed to load tasks:', error)
  }
}

const loadSchedule = async (id) => {
  try {
    const schedule = await api.schedules.getById(id)
    Object.assign(formData, {
      name: schedule.name,
      task_id: schedule.task_id,
      schedule_type: schedule.schedule_type,
      schedule_config: schedule.schedule_config,
      dependencies: schedule.dependencies || [],
      retry_count: schedule.retry_count,
      retry_interval: schedule.retry_interval,
      is_active: schedule.is_active
    })

    // Set interval display
    if (schedule.schedule_type === 'interval') {
      const seconds = schedule.schedule_config.interval_seconds
      if (seconds % 86400 === 0) {
        intervalAmount.value = seconds / 86400
        intervalUnit.value = 'days'
      } else if (seconds % 3600 === 0) {
        intervalAmount.value = seconds / 3600
        intervalUnit.value = 'hours'
      } else if (seconds % 60 === 0) {
        intervalAmount.value = seconds / 60
        intervalUnit.value = 'minutes'
      } else {
        intervalAmount.value = seconds
        intervalUnit.value = 'seconds'
      }
    }
  } catch (error) {
    ElMessage.error('加载调度失败')
    router.push('/schedules')
  }
}

const saveSchedule = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  // Validate schedule config
  if (formData.schedule_type === 'cron' && !formData.schedule_config.cron_expression) {
    ElMessage.error('请填写Cron表达式')
    return
  }

  try {
    if (isEdit.value) {
      await api.schedules.update(route.params.id, formData)
      ElMessage.success('更新成功')
    } else {
      await api.schedules.create(formData)
      ElMessage.success('创建成功')
    }

    router.push('/schedules')
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  }
}

onMounted(() => {
  loadTasks()

  if (route.params.id) {
    isEdit.value = true
    loadSchedule(route.params.id)
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cron-helper {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
}

.cron-examples {
  margin-top: 10px;
  font-size: 13px;
  color: #606266;
}

.cron-examples div {
  margin: 5px 0;
}
</style>