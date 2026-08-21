<template>
  <div class="dashboard">
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-label">总执行次数</div>
          <div class="stat-value">{{ data?.total_runs ?? '-' }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-label">近 7 天执行</div>
          <div class="stat-value">{{ data?.last_7d_runs ?? '-' }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-label">平均通过率</div>
          <div class="stat-value text-success">{{ ((data?.pass_rate_avg ?? 0) * 100).toFixed(1) }}%</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-label">状态分布</div>
          <el-tag v-for="(v, k) in data?.by_status" :key="k" :type="statusType(k)" style="margin:2px">
            {{ statusLabel(k as string) }}: {{ v }}
          </el-tag>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="mt-16" shadow="hover">
      <template #header>最近执行</template>
      <el-table :data="recentRuns" stripe size="small">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="task_name" label="任务" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="runStatusType(row.status)" size="small">{{ runStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180" />
        <el-table-column prop="duration_ms" label="耗时(ms)" width="120" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push(`/runs/${row.id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { resultApi, runApi, type Dashboard, type TaskRun } from '@/api'

const data = ref<Dashboard>()
const recentRuns = ref<TaskRun[]>([])

const statusLabels: Record<string, string> = {
  queued: '排队', running: '执行中', success: '成功', failed: '失败', aborted: '取消', error: '异常',
}
const statusLabel = (s: string) => statusLabels[s] || s
const statusType = (s: string) => ({ success: 'success', failed: 'danger', aborted: 'info', error: 'warning', running: 'primary', queued: 'info' }[s] || 'info') as any

const runStatusLabel = statusLabel
const runStatusType = statusType

onMounted(async () => {
  data.value = await resultApi.dashboard()
  const r = await runApi.list({ page_size: 10 })
  recentRuns.value = (r as any).results || []
})
</script>

<style scoped>
.stat-label { color: #909399; font-size: 13px; }
.stat-value { font-size: 26px; font-weight: 600; margin-top: 8px; }
</style>
