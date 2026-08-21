<template>
  <div>
    <div class="toolbar">
      <el-select v-model="filters.project" placeholder="项目" clearable filterable style="width:200px" @change="load">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:140px" @change="load">
        <el-option label="开放" value="open" /><el-option label="锁定" value="locked" /><el-option label="归档" value="archived" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="success" @click="openCreate">新建版本</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="版本号" width="120">
        <template #default="{ row }"><el-tag :type="row.is_baseline ? 'danger' : 'primary'" size="small">{{ row.name }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="release_date" label="发布日期" width="120" />
      <el-table-column prop="is_baseline" label="基线" width="80">
        <template #default="{ row }"><el-tag v-if="row.is_baseline" type="danger" size="small">基线</el-tag></template>
      </el-table-column>
      <el-table-column prop="iterations_count" label="迭代数" width="80" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="row.status === 'open'" link @click="lock(row)">锁定</el-button>
          <el-button link type="success" @click="$router.push({ name: 'iterations', query: { project: row.project, version: row.id } })">查看迭代</el-button>
          <el-popconfirm title="确认删除?" @confirm="remove(row.id)">
            <template #reference><el-button link type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg.visible" :title="dlg.id ? '编辑版本' : '新建版本'" width="560px">
      <el-form :model="dlg.form" label-width="100px">
        <el-form-item label="项目">
          <el-select v-model="dlg.form.project" filterable>
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本号"><el-input v-model="dlg.form.name" placeholder="v1.0" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="dlg.form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="dlg.form.status" style="width:160px">
            <el-option value="open" label="开放" /><el-option value="locked" label="锁定" /><el-option value="archived" label="归档" />
          </el-select>
        </el-form-item>
        <el-form-item label="发布日期"><el-date-picker v-model="dlg.form.release_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="基线版本"><el-switch v-model="dlg.form.is_baseline" /></el-form-item>
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
import { projectApi, versionApi, type Project, type Version } from '@/api'

const route = useRoute()
const rows = ref<Version[]>([])
const projects = ref<Project[]>([])
const loading = ref(false)
const filters = reactive<{ project?: number; status?: string }>({
  project: route.query.project ? Number(route.query.project) : undefined,
})

const dlg = reactive({
  visible: false, id: 0 as number | undefined,
  form: { project: undefined, name: '', description: '', status: 'open', release_date: '', is_baseline: false } as Partial<Version>,
})

const statusLabels: Record<string, string> = { open: '开放', locked: '锁定', archived: '归档' }
const statusLabel = (s: string) => statusLabels[s] || s
const statusType = (s: string) => ({ open: 'success', locked: 'warning', archived: 'info' }[s] || 'info') as any

async function loadProjects() {
  const r = await projectApi.list()
  projects.value = (r as any).results || []
}
async function load() {
  loading.value = true
  try {
    const r = await versionApi.list({ ...filters })
    rows.value = (r as any).results || []
  } finally { loading.value = false }
}

function openCreate() {
  dlg.id = undefined
  dlg.form = { project: filters.project, name: '', description: '', status: 'open', release_date: '', is_baseline: false }
  dlg.visible = true
}
function openEdit(row: Version) {
  dlg.id = row.id
  dlg.form = { ...row }
  dlg.visible = true
}
async function save() {
  if (dlg.id) await versionApi.update(dlg.id, dlg.form)
  else await versionApi.create(dlg.form)
  ElMessage.success('已保存')
  dlg.visible = false
  load()
}
async function remove(id: number) {
  await versionApi.remove(id)
  ElMessage.success('已删除')
  load()
}
async function lock(row: Version) {
  await versionApi.update(row.id, { status: 'locked' })
  ElMessage.success('已锁定')
  load()
}

onMounted(async () => { await loadProjects(); load() })
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
</style>
