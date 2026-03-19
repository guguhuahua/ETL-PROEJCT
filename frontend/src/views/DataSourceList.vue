<template>
  <div class="data-source-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据源列表</span>
          <el-button type="primary" @click="showAddDialog">添加数据源</el-button>
        </div>
      </template>

      <el-table :data="dataSources" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="数据源名称" width="200" />
        <el-table-column prop="type" label="类型" width="150">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">{{ getTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="连接信息">
          <template #default="{ row }">
            <span v-if="row.connection_params">
              {{ row.connection_params.host }}:{{ row.connection_params.port }} / {{ row.connection_params.database }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="testConnection(row)">测试连接</el-button>
            <el-button size="small" @click="editDataSource(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteDataSource(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑数据源' : '添加数据源'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="数据源名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入数据源名称" />
        </el-form-item>

        <el-form-item label="数据库类型" prop="type">
          <el-select v-model="formData.type" placeholder="请选择数据库类型" style="width: 100%;" @change="onDbTypeChange">
            <el-option label="MySQL" value="mysql">
              <span>MySQL</span>
              <span style="color: #909399; font-size: 12px; margin-left: 10px;">端口: 3306</span>
            </el-option>
            <el-option label="Kingbase8 (人大金仓)" value="kingbase8">
              <span>Kingbase8</span>
              <span style="color: #909399; font-size: 12px; margin-left: 10px;">端口: 54321</span>
            </el-option>
            <el-option label="PostgreSQL" value="postgresql">
              <span>PostgreSQL</span>
              <span style="color: #909399; font-size: 12px; margin-left: 10px;">端口: 5432</span>
            </el-option>
            <el-option label="Hive" value="hive">
              <span>Hive</span>
              <span style="color: #909399; font-size: 12px; margin-left: 10px;">端口: 10000</span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-divider>连接参数</el-divider>

        <el-form-item label="主机地址" prop="connection_params.host">
          <el-input v-model="formData.connection_params.host" placeholder="请输入主机地址，如：localhost 或 192.168.1.100" />
        </el-form-item>

        <el-form-item label="端口" prop="connection_params.port">
          <el-input-number v-model="formData.connection_params.port" :min="1" :max="65535" style="width: 100%;" />
        </el-form-item>

        <el-form-item label="数据库名" prop="connection_params.database">
          <el-input v-model="formData.connection_params.database" placeholder="请输入数据库名" />
        </el-form-item>

        <el-form-item label="用户名" prop="connection_params.username">
          <el-input v-model="formData.connection_params.username" placeholder="请输入用户名" />
        </el-form-item>

        <!-- 非 Hive 数据库的密码字段 -->
        <el-form-item v-if="formData.type !== 'hive'" label="密码" prop="connection_params.password">
          <el-input
            v-model="formData.connection_params.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>

        <!-- MySQL 特有配置 -->
        <el-form-item v-if="formData.type === 'mysql'" label="字符集">
          <el-select v-model="formData.connection_params.charset" style="width: 100%;">
            <el-option label="utf8mb4 (推荐)" value="utf8mb4" />
            <el-option label="utf8" value="utf8" />
            <el-option label="gbk" value="gbk" />
            <el-option label="latin1" value="latin1" />
          </el-select>
        </el-form-item>

        <!-- Hive 特有配置 -->
        <template v-if="formData.type === 'hive'">
          <el-form-item label="认证方式">
            <el-select v-model="formData.connection_params.auth" style="width: 100%;" placeholder="请选择认证方式">
              <el-option label="无认证 (NOSASL)" value="NOSASL" />
              <el-option label="PLAIN (仅用户名)" value="PLAIN" />
              <el-option label="LDAP (用户名+密码)" value="LDAP" />
              <el-option label="CUSTOM (自定义认证)" value="CUSTOM" />
              <el-option label="Kerberos" value="KERBEROS" />
              <el-option label="默认 (NONE)" value="NONE" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="['LDAP', 'CUSTOM'].includes(formData.connection_params.auth)" label="密码" prop="connection_params.password">
            <el-input
              v-model="formData.connection_params.password"
              type="password"
              placeholder="请输入密码"
              show-password
            />
          </el-form-item>
          <el-form-item v-if="formData.connection_params.auth === 'KERBEROS'" label="服务名">
            <el-input v-model="formData.connection_params.kerberos_service_name" placeholder="如：hive" />
          </el-form-item>
          <el-alert
            v-if="formData.connection_params.auth === 'PLAIN'"
            title="PLAIN模式仅传递用户名，不需要密码"
            type="info"
            :closable="false"
            show-icon
            style="margin-bottom: 15px;"
          />
          <el-alert
            v-if="formData.connection_params.auth === 'LDAP'"
            title="LDAP认证需要正确的用户名和密码"
            type="warning"
            :closable="false"
            show-icon
            style="margin-bottom: 15px;"
          />
        </template>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button @click="testConnectionInDialog">测试连接</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const submitting = ref(false)
const dataSources = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const currentId = ref(null)

// 数据库类型默认端口
const defaultPorts = {
  mysql: 3306,
  kingbase8: 54321,
  postgresql: 5432,
  hive: 10000
}

const formData = reactive({
  name: '',
  type: '',
  connection_params: {
    host: '',
    port: 3306,
    database: '',
    username: '',
    password: '',
    charset: 'utf8mb4',
    auth: 'NONE',  // Hive认证方式
    kerberos_service_name: ''
  }
})

const formRules = {
  name: [{ required: true, message: '请输入数据源名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择数据库类型', trigger: 'change' }],
  'connection_params.host': [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  'connection_params.port': [{ required: true, message: '请输入端口号', trigger: 'blur' }],
  'connection_params.database': [{ required: true, message: '请输入数据库名', trigger: 'blur' }],
  'connection_params.username': [{ required: true, message: '请输入用户名', trigger: 'blur' }]
}

const getTypeLabel = (type) => {
  const labels = {
    mysql: 'MySQL',
    kingbase8: 'Kingbase8',
    postgresql: 'PostgreSQL',
    hive: 'Hive'
  }
  return labels[type] || type
}

const getTypeTagType = (type) => {
  const types = {
    mysql: 'primary',
    kingbase8: 'success',
    postgresql: 'info',
    hive: 'warning'
  }
  return types[type] || ''
}

const formatDate = (date) => {
  if (!date) return ''
  // 后端已经返回格式化的本地时间，直接显示
  return date
}

const loadDataSources = async () => {
  loading.value = true
  try {
    dataSources.value = await api.dataSources.getAll()
  } catch (error) {
    console.error('Failed to load data sources:', error)
  } finally {
    loading.value = false
  }
}

const onDbTypeChange = (type) => {
  // 自动设置默认端口
  formData.connection_params.port = defaultPorts[type] || 3306
  // 重置字符集（仅MySQL需要）
  if (type !== 'mysql') {
    formData.connection_params.charset = 'utf8mb4'
  }
}

const showAddDialog = () => {
  isEdit.value = false
  currentId.value = null
  Object.assign(formData, {
    name: '',
    type: '',
    connection_params: {
      host: '',
      port: 3306,
      database: '',
      username: '',
      password: '',
      charset: 'utf8mb4',
      auth: 'NONE',
      kerberos_service_name: ''
    }
  })
  dialogVisible.value = true
}

const editDataSource = async (row) => {
  isEdit.value = true
  currentId.value = row.id

  try {
    // 获取完整的数据源信息（包含连接参数）
    const source = await api.dataSources.getById(row.id)
    Object.assign(formData, {
      name: source.name,
      type: source.type,
      connection_params: {
        host: source.connection_params?.host || '',
        port: source.connection_params?.port || defaultPorts[source.type] || 3306,
        database: source.connection_params?.database || '',
        username: source.connection_params?.username || '',
        password: source.connection_params?.password || '',
        charset: source.connection_params?.charset || 'utf8mb4',
        auth: source.connection_params?.auth || 'NONE',
        kerberos_service_name: source.connection_params?.kerberos_service_name || ''
      }
    })
  } catch (error) {
    console.error('Failed to load data source details:', error)
    ElMessage.error('获取数据源详情失败')
    return
  }

  dialogVisible.value = true
}

const testConnection = async (row) => {
  try {
    ElMessage.info(`正在测试 ${row.name} 的连接...`)
    const result = await api.dataSources.testConnection({
      type: row.type,
      connection_params: row.connection_params || {}
    })
    if (result.success) {
      ElMessage.success(result.message || '连接成功！')
    } else {
      ElMessage.error(result.message || '连接失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '连接失败')
  }
}

const testConnectionInDialog = async () => {
  try {
    ElMessage.info('正在测试连接...')
    const result = await api.dataSources.testConnection({
      type: formData.type,
      connection_params: formData.connection_params
    })
    if (result.success) {
      ElMessage.success(result.message || '连接成功！')
    } else {
      ElMessage.error(result.message || '连接失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '连接失败')
  }
}

const deleteDataSource = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除数据源 "${row.name}" 吗？`, '提示', {
      type: 'warning'
    })

    await api.dataSources.delete(row.id)
    ElMessage.success('删除成功')
    loadDataSources()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const submitForm = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value) {
      await api.dataSources.update(currentId.value, formData)
      ElMessage.success('更新成功')
    } else {
      await api.dataSources.create(formData)
      ElMessage.success('添加成功')
    }

    dialogVisible.value = false
    loadDataSources()
  } catch (error) {
    ElMessage.error(error.response?.data?.error || (isEdit.value ? '更新失败' : '添加失败'))
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadDataSources()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>