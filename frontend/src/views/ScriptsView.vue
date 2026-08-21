<template>
  <div>
    <div class="toolbar">
      <el-select v-model="filters.project" placeholder="项目" clearable filterable style="width:180px" @change="load">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-input v-model="q" placeholder="搜索脚本名/路径" style="width:240px" clearable @keyup.enter="load" />
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="success" @click="openCreate">新建脚本</el-button>
      <el-button type="warning" :loading="syncing" @click="syncFromDisk">从磁盘同步</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" width="200" />
      <el-table-column prop="file_path" label="路径" />
      <el-table-column prop="type" label="类型" width="80">
        <template #default="{ row }">
          <el-tag :type="row.type === 'api' ? 'primary' : 'success'" size="small">{{ row.type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_synced_at" label="同步时间" width="180" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push(`/scripts/${row.id}`)">编辑</el-button>
          <el-popconfirm title="确认删除?" @confirm="remove(row.id)">
            <template #reference><el-button link type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg.visible" title="新建脚本" width="520px">
      <el-form :model="dlg.form" label-width="100px">
        <el-form-item label="项目">
          <el-select v-model="dlg.form.project" filterable>
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称"><el-input v-model="dlg.form.name" placeholder="test_login" /></el-form-item>
        <el-form-item label="路径"><el-input v-model="dlg.form.file_path" placeholder="api/test_login.py" /></el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="dlg.form.type"><el-radio value="api">API</el-radio><el-radio value="ui">UI</el-radio></el-radio-group>
        </el-form-item>
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
import { projectApi, scriptApi, type Project, type Script } from '@/api'

const rows = ref<Script[]>([])
const projects = ref<Project[]>([])
const loading = ref(false)
const syncing = ref(false)
const q = ref('')
const filters = reactive<{ project?: number }>({})

const dlg = reactive({
  visible: false,
  form: { project: undefined, name: '', file_path: '', type: 'api' } as Partial<Script>,
})

async function loadProjects() {
  const r = await projectApi.list()
  projects.value = (r as any).results || []
}
async function load() {
  loading.value = true
  try {
    const r = await scriptApi.list({ search: q.value, ...filters })
    rows.value = (r as any).results || []
  } finally { loading.value = false }
}
function openCreate() {
  dlg.form = { project: filters.project, name: '', file_path: '', type: 'api' }
  dlg.visible = true
}
async function save() {
  await scriptApi.create(dlg.form)
  ElMessage.success('已创建')
  dlg.visible = false
  load()
}
async function remove(id: number) {
  await scriptApi.remove(id)
  ElMessage.success('已删除')
  load()
}
async function syncFromDisk() {
  syncing.value = true
  try {
    const r = await scriptApi.syncFromDisk()
    ElMessage.success(`扫描 ${r.scanned} 个,新建 ${r.created},更新 ${r.updated}`)
    load()
  } finally { syncing.value = false }
}

onMounted(async () => { await loadProjects(); load() })
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
</style>
