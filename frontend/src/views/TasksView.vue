<template>
  <div>
    <div class="toolbar">
      <el-select v-model="filters.project" placeholder="项目" clearable filterable style="width:180px" @change="load">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:120px" @change="load">
        <el-option label="草稿" value="draft" /><el-option label="启用" value="active" /><el-option label="归档" value="archived" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="success" @click="openCreate">新建任务</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="任务名" />
      <el-table-column prop="trigger" label="触发方式" width="100" />
      <el-table-column prop="case_count" label="用例数" width="80" />
      <el-table-column prop="cron_expr" label="Cron" width="120" />
      <el-table-column prop="jenkins_job_name" label="Jenkins Job" />
      <el-table-column prop="last_run_status" label="最近结果" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.last_run_status" :type="runStatusType(row.last_run_status)" size="small">{{ row.last_run_status }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button link type="success" :loading="triggering === row.id" @click="trigger(row)">执行</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link @click="viewRuns(row.id)">记录</el-button>
          <el-popconfirm title="确认删除?" @confirm="remove(row.id)">
            <template #reference><el-button link type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg.visible" :title="dlg.id ? '编辑任务' : '新建任务'" width="640px">
      <el-form :model="dlg.form" label-width="120px">
        <el-form-item label="任务名"><el-input v-model="dlg.form.name" /></el-form-item>
        <el-form-item label="项目">
          <el-select v-model="dlg.form.project" filterable @change="onProjectChange">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="环境">
          <el-select v-model="dlg.form.environment" clearable>
            <el-option v-for="e in envs" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="触发方式">
          <el-radio-group v-model="dlg.form.trigger">
            <el-radio value="manual">手动</el-radio><el-radio value="cron">定时</el-radio><el-radio value="webhook">Webhook</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="Cron 表达式" v-if="dlg.form.trigger === 'cron'">
          <el-input v-model="dlg.form.cron_expr" placeholder="0 2 * * *" />
        </el-form-item>
        <el-form-item label="Jenkins Job">
          <el-input v-model="dlg.form.jenkins_job_name" placeholder="autotest-shop-smoke" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="dlg.form.status" style="width:140px">
            <el-option value="draft" label="草稿" /><el-option value="active" label="启用" /><el-option value="archived" label="归档" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联用例">
          <el-select v-model="dlg.form.cases" multiple filterable style="width:100%">
            <el-option v-for="c in availableCases" :key="c.id" :label="`${c.case_id} ${c.title}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="dlg.form.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg.visible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { caseApi, envApi, projectApi, taskApi, type Environment, type Project, type TestCase, type TestTask } from '@/api'

const router = useRouter()
const rows = ref<TestTask[]>([])
const projects = ref<Project[]>([])
const envs = ref<Environment[]>([])
const availableCases = ref<TestCase[]>([])
const loading = ref(false)
const triggering = ref<number | null>(null)
const filters = reactive<{ project?: number; status?: string }>({})

const dlg = reactive({
  visible: false, id: 0 as number | undefined,
  form: {
    name: '', project: undefined, environment: undefined, cases: [] as number[],
    trigger: 'manual', cron_expr: '', status: 'draft', jenkins_job_name: '', description: '',
  } as Partial<TestTask>,
})

const statusMap: Record<string, string> = { queued: '排队', running: '执行中', success: '成功', failed: '失败', aborted: '取消', error: '异常' }
const runStatusType = (s: string) => ({ success: 'success', failed: 'danger', aborted: 'info', error: 'warning', running: 'primary', queued: 'info' }[s] || 'info') as any

async function loadProjects() {
  const r = await projectApi.list()
  projects.value = (r as any).results || []
}
async function loadEnvs() {
  const r = await envApi.list()
  envs.value = (r as any).results || []
}
async function load() {
  loading.value = true
  try {
    const r = await taskApi.list({ ...filters })
    rows.value = (r as any).results || []
  } finally { loading.value = false }
}

async function onProjectChange() {
  if (!dlg.form.project) { availableCases.value = []; return }
  const r = await caseApi.list({ project: dlg.form.project, page_size: 1000 })
  availableCases.value = (r as any).results || []
}

function openCreate() {
  dlg.id = undefined
  dlg.form = { name: '', project: filters.project, environment: undefined, cases: [], trigger: 'manual', cron_expr: '', status: 'draft', jenkins_job_name: '', description: '' }
  dlg.visible = true
  onProjectChange()
}
function openEdit(row: TestTask) {
  dlg.id = row.id
  dlg.form = { ...row, cases: row.cases || [] }
  dlg.visible = true
  onProjectChange()
}
async function save() {
  if (dlg.id) await taskApi.update(dlg.id, dlg.form)
  else await taskApi.create(dlg.form)
  ElMessage.success('已保存')
  dlg.visible = false
  load()
}
async function remove(id: number) {
  await taskApi.remove(id)
  ElMessage.success('已删除')
  load()
}
async function trigger(row: TestTask) {
  triggering.value = row.id
  try {
    const run = await taskApi.trigger(row.id)
    ElMessage.success(`已触发,Run #${run.id}`)
    router.push(`/runs/${run.id}`)
  } finally { triggering.value = null }
}
function viewRuns(taskId: number) {
  router.push({ name: 'runs', query: { task: taskId } })
}

onMounted(async () => { await loadProjects(); await loadEnvs(); load() })
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
</style>
