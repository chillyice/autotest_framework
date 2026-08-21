<template>
  <div v-loading="loading">
    <el-page-header @back="$router.back()">
      <template #content>
        <span>Run #{{ run?.id }} - {{ run?.task_name }}</span>
      </template>
    </el-page-header>

    <el-card class="mt-16">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(run?.status)" size="small">{{ statusLabel(run?.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Build">{{ run?.jenkins_build_number || '-' }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ run?.duration_ms || 0 }} ms</el-descriptions-item>
        <el-descriptions-item label="开始">{{ run?.started_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="结束">{{ run?.finished_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Jenkins">
          <el-link v-if="run?.jenkins_build_url" type="primary" :href="run.jenkins_build_url" target="_blank">查看构建</el-link>
        </el-descriptions-item>
      </el-descriptions>
      <div class="mt-16">
        <el-button :loading="refreshing" @click="refresh">刷新状态</el-button>
      </div>
    </el-card>

    <el-card class="mt-16">
      <template #header>
        <div class="flex" style="align-items:center;justify-content:space-between">
          <span>用例结果</span>
          <el-tag v-if="summary" type="info" size="small">
            总 {{ summary.total }} / 通过 {{ summary.passed }} / 失败 {{ summary.failed }} / 跳过 {{ summary.skipped }} / 异常 {{ summary.error }}
          </el-tag>
        </div>
      </template>
      <el-table :data="results" stripe size="small">
        <el-table-column prop="nodeid" label="Node ID" min-width="280" />
        <el-table-column prop="result" label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="resultType(row.result)" size="small">{{ row.result }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.error_message" class="text-danger" style="font-family:monospace;font-size:12px">{{ row.error_message }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button v-if="row.traceback" link type="warning" @click="showTrace(row)">堆栈</el-button>
            <el-button v-if="row.allure_url" link type="primary" @click="openUrl(row.allure_url)">Allure</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="run?.error_message" class="mt-16">
      <template #header>异常信息</template>
      <pre class="error-pre">{{ run.error_message }}</pre>
    </el-card>

    <el-dialog v-model="traceDlg.visible" :title="`堆栈 - ${traceDlg.nodeid}`" width="900px">
      <pre class="trace-pre">{{ traceDlg.trace }}</pre>
      <template #footer>
        <el-button @click="traceDlg.visible = false">关闭</el-button>
        <el-button type="primary" @click="copyTrace">复制</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { resultApi, runApi, type RunSummary, type TaskRun, type TestResult } from '@/api'

const route = useRoute()
const run = ref<TaskRun>()
const results = ref<TestResult[]>([])
const summary = ref<RunSummary>()
const loading = ref(false)
const refreshing = ref(false)
const traceDlg = reactive({ visible: false, nodeid: '', trace: '' })

const labels: Record<string, string> = { queued: '排队', running: '执行中', success: '成功', failed: '失败', aborted: '取消', error: '异常' }
const statusLabel = (s?: string) => (s ? labels[s] || s : '-')
const statusType = (s?: string) => (s ? ({ success: 'success', failed: 'danger', aborted: 'info', error: 'warning', running: 'primary', queued: 'info' }[s] || 'info') as any : 'info')
const resultType = (s: string) => ({ passed: 'success', failed: 'danger', skipped: 'info', error: 'warning' }[s] || 'info') as any

async function load() {
  loading.value = true
  try {
    const id = Number(route.params.id)
    const all = await runApi.list({ page_size: 1000 })
    run.value = ((all as any).results || []).find((r: TaskRun) => r.id === id)
    const rr = await resultApi.list({ run: id, page_size: 1000 })
    results.value = (rr as any).results || []
  } finally { loading.value = false }
}
async function refresh() {
  refreshing.value = true
  try {
    run.value = await runApi.refresh(Number(route.params.id))
    ElMessage.success('已刷新')
    load()
  } finally { refreshing.value = false }
}
function openUrl(url: string) { window.open(url, '_blank') }
function showTrace(row: TestResult) {
  traceDlg.nodeid = row.nodeid
  traceDlg.trace = row.traceback || row.error_message || '(空)'
  traceDlg.visible = true
}
function copyTrace() {
  navigator.clipboard.writeText(traceDlg.trace)
  ElMessage.success('已复制')
}

onMounted(load)
</script>

<style scoped>
.error-pre { white-space: pre-wrap; word-break: break-all; color: #f56c6c; font-family: monospace; font-size: 12px; }
.trace-pre { background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 12px; white-space: pre-wrap; word-break: break-all; max-height: 60vh; overflow: auto; }
</style>
