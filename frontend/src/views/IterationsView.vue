<template>
  <div>
    <div class="toolbar">
      <el-select v-model="filters.project" placeholder="项目" clearable filterable style="width:200px" @change="onProjectChange">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-select v-model="filters.version" placeholder="版本" clearable filterable style="width:180px" @change="load">
        <el-option v-for="v in versions" :key="v.id" :label="v.name" :value="v.id" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:140px" @change="load">
        <el-option label="计划中" value="planning" /><el-option label="进行中" value="active" /><el-option label="已结束" value="closed" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="success" @click="openCreate">新建迭代</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="迭代名" />
      <el-table-column prop="version_name" label="所属版本" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="开始日期" width="120" />
      <el-table-column prop="end_date" label="结束日期" width="120" />
      <el-table-column prop="cases_count" label="关联用例" width="100" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="row.status === 'planning'" link type="success" @click="start(row)">启动</el-button>
          <el-button v-if="row.status === 'active'" link @click="close(row)">结束</el-button>
          <el-button link type="primary" @click="$router.push({ name: 'cases', query: { project: row.project, iteration: row.id } })">用例</el-button>
          <el-popconfirm title="确认删除?" @confirm="remove(row.id)">
            <template #reference><el-button link type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg.visible" :title="dlg.id ? '编辑迭代' : '新建迭代'" width="560px">
      <el-form :model="dlg.form" label-width="100px">
        <el-form-item label="项目">
          <el-select v-model="dlg.form.project" filterable @change="onDlgProjectChange">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本">
          <el-select v-model="dlg.form.version" clearable filterable>
            <el-option v-for="v in dlgVersions" :key="v.id" :label="v.name" :value="v.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="迭代名"><el-input v-model="dlg.form.name" placeholder="2024Q1Sprint3" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="dlg.form.status" style="width:160px">
            <el-option value="planning" label="计划中" /><el-option value="active" label="进行中" /><el-option value="closed" label="已结束" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期"><el-date-picker v-model="dlg.form.start_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="结束日期"><el-date-picker v-model="dlg.form.end_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
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
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { iterationApi, projectApi, versionApi, type Iteration, type Project, type Version } from '@/api'

const route = useRoute()
const rows = ref<Iteration[]>([])
const projects = ref<Project[]>([])
const versions = ref<Version[]>([])
const dlgVersions = ref<Version[]>([])
const loading = ref(false)
const filters = reactive<{ project?: number; version?: number; status?: string }>({
  project: route.query.project ? Number(route.query.project) : undefined,
  version: route.query.version ? Number(route.query.version) : undefined,
})

const dlg = reactive({
  visible: false, id: 0 as number | undefined,
  form: { project: undefined, version: undefined, name: '', description: '', status: 'planning', start_date: '', end_date: '' } as Partial<Iteration>,
})

const statusLabels: Record<string, string> = { planning: '计划中', active: '进行中', closed: '已结束' }
const statusLabel = (s: string) => statusLabels[s] || s
const statusType = (s: string) => ({ planning: 'info', active: 'success', closed: 'warning' }[s] || 'info') as any

async function loadProjects() {
  const r = await projectApi.list()
  projects.value = (r as any).results || []
}
async function loadVersions(project?: number) {
  if (!project) { versions.value = []; return }
  const r = await versionApi.list({ project, page_size: 1000 })
  versions.value = (r as any).results || []
}
async function load() {
  loading.value = true
  try {
    const r = await iterationApi.list({ ...filters })
    rows.value = (r as any).results || []
  } finally { loading.value = false }
}

async function onProjectChange() {
  await loadVersions(filters.project)
  filters.version = undefined
  load()
}
async function onDlgProjectChange() {
  if (dlg.form.project) {
    const r = await versionApi.list({ project: dlg.form.project, page_size: 1000 })
    dlgVersions.value = (r as any).results || []
  } else {
    dlgVersions.value = []
  }
  dlg.form.version = undefined
}

function openCreate() {
  dlg.id = undefined
  dlg.form = { project: filters.project, version: filters.version, name: '', description: '', status: 'planning', start_date: '', end_date: '' }
  dlgVersions.value = versions.value
  dlg.visible = true
}
function openEdit(row: Iteration) {
  dlg.id = row.id
  dlg.form = { ...row }
  onDlgProjectChange()
  dlg.visible = true
}
async function save() {
  if (dlg.id) await iterationApi.update(dlg.id, dlg.form)
  else await iterationApi.create(dlg.form)
  ElMessage.success('已保存')
  dlg.visible = false
  load()
}
async function remove(id: number) {
  await iterationApi.remove(id)
  ElMessage.success('已删除')
  load()
}
async function start(row: Iteration) {
  await iterationApi.update(row.id, { status: 'active' })
  ElMessage.success('已启动')
  load()
}
async function close(row: Iteration) {
  await iterationApi.update(row.id, { status: 'closed' })
  ElMessage.success('已结束')
  load()
}

onMounted(async () => {
  await loadProjects()
  if (filters.project) await loadVersions(filters.project)
  load()
})
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
</style>
