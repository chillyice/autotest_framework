<template>
  <div>
    <div class="toolbar">
      <el-select v-model="filters.task" placeholder="任务" clearable filterable style="width:200px" @change="load">
        <el-option v-for="t in tasks" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:120px" @change="load">
        <el-option v-for="s in ['queued','running','success','failed','aborted','error']" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button :loading="refreshingAll" @click="refreshAll">批量刷新状态</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="Run ID" width="80" />
      <el-table-column prop="task_name" label="任务" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="jenkins_build_number" label="Build#" width="80" />
      <el-table-column prop="started_at" label="开始" width="180" />
      <el-table-column prop="finished_at" label="结束" width="180" />
      <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push(`/runs/${row.id}`)">详情</el-button>
          <el-button link :loading="refreshing === row.id" @click="refresh(row.id)">刷新</el-button>
          <el-button v-if="row.jenkins_build_url" link type="success" @click="openJenkins(row.jenkins_build_url)">Jenkins</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { runApi, taskApi, type TaskRun, type TestTask } from '@/api'

const route = useRoute()
const rows = ref<TaskRun[]>([])
const tasks = ref<TestTask[]>([])
const loading = ref(false)
const refreshing = ref<number | null>(null)
const refreshingAll = ref(false)
const filters = reactive<{ task?: number; status?: string }>({
  task: route.query.task ? Number(route.query.task) : undefined,
})

const labels: Record<string, string> = { queued: '排队', running: '执行中', success: '成功', failed: '失败', aborted: '取消', error: '异常' }
const statusLabel = (s: string) => labels[s] || s
const statusType = (s: string) => ({ success: 'success', failed: 'danger', aborted: 'info', error: 'warning', running: 'primary', queued: 'info' }[s] || 'info') as any

async function loadTasks() {
  const r = await taskApi.list({ page_size: 1000 })
  tasks.value = (r as any).results || []
}
async function load() {
  loading.value = true
  try {
    const r = await runApi.list({ ...filters })
    rows.value = (r as any).results || []
  } finally { loading.value = false }
}
async function refresh(id: number) {
  refreshing.value = id
  try {
    await runApi.refresh(id)
    ElMessage.success('已刷新')
    load()
  } finally { refreshing.value = null }
}
async function refreshAll() {
  refreshingAll.value = true
  try {
    const pending = rows.value.filter(r => r.status === 'queued' || r.status === 'running').map(r => r.id)
    for (const id of pending) await runApi.refresh(id)
    ElMessage.success(`已刷新 ${pending.length} 条`)
    load()
  } finally { refreshingAll.value = false }
}
function openJenkins(url: string) { window.open(url, '_blank') }

onMounted(async () => { await loadTasks(); load() })
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
</style>
