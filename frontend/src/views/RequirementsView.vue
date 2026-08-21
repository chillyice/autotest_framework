<template>
  <div>
    <div class="toolbar">
      <el-select v-model="filters.project" placeholder="选择项目" filterable clearable style="width:200px" @change="load">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-input v-model="q" placeholder="搜索标题/外部编号" style="width:240px" clearable @keyup.enter="load" />
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="success" @click="openCreate">新建需求</el-button>
    </div>
    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="ext_key" label="外部编号" width="140" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="source" label="来源" width="100" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="cases_count" label="关联用例" width="100" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-popconfirm title="确认删除?" @confirm="remove(row.id)">
            <template #reference><el-button link type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg.visible" :title="dlg.id ? '编辑需求' : '新建需求'" width="560px">
      <el-form :model="dlg.form" label-width="100px">
        <el-form-item label="项目">
          <el-select v-model="dlg.form.project" placeholder="选择项目">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题"><el-input v-model="dlg.form.title" /></el-form-item>
        <el-form-item label="外部编号"><el-input v-model="dlg.form.ext_key" placeholder="JIRA-1234" /></el-form-item>
        <el-form-item label="外部URL"><el-input v-model="dlg.form.ext_url" /></el-form-item>
        <el-form-item label="来源"><el-input v-model="dlg.form.source" placeholder="jira/zentao/local" /></el-form-item>
        <el-form-item label="状态"><el-input v-model="dlg.form.status" placeholder="open" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="dlg.form.description" type="textarea" :rows="3" /></el-form-item>
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
import { ElMessage } from 'element-plus'
import { projectApi, reqApi, type Project, type Requirement } from '@/api'

const rows = ref<Requirement[]>([])
const projects = ref<Project[]>([])
const loading = ref(false)
const q = ref('')
const filters = reactive<{ project: number | undefined }>({ project: undefined })

const dlg = reactive({
  visible: false, id: 0 as number | undefined,
  form: { project: undefined, title: '', ext_key: '', ext_url: '', source: 'local', status: 'open', description: '' } as Partial<Requirement>,
})

async function loadProjects() {
  const r = await projectApi.list()
  projects.value = (r as any).results || []
}
async function load() {
  loading.value = true
  try {
    const r = await reqApi.list({ search: q.value, project: filters.project })
    rows.value = (r as any).results || []
  } finally { loading.value = false }
}

function openCreate() {
  dlg.id = undefined
  dlg.form = { project: filters.project, title: '', ext_key: '', ext_url: '', source: 'local', status: 'open', description: '' }
  dlg.visible = true
}
function openEdit(row: Requirement) {
  dlg.id = row.id
  dlg.form = { ...row }
  dlg.visible = true
}
async function save() {
  if (dlg.id) await reqApi.update(dlg.id, dlg.form)
  else await reqApi.create(dlg.form)
  ElMessage.success('已保存')
  dlg.visible = false
  load()
}
async function remove(id: number) {
  await reqApi.remove(id)
  ElMessage.success('已删除')
  load()
}

onMounted(async () => { await loadProjects(); load() })
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
</style>
