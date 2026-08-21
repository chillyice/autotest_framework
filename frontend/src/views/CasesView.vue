<template>
  <div>
    <div class="toolbar">
      <el-select v-model="filters.project" placeholder="项目" clearable filterable style="width:180px" @change="load">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-select v-model="filters.type" placeholder="类型" clearable style="width:120px" @change="load">
        <el-option label="API" value="api" /><el-option label="UI" value="ui" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:120px" @change="load">
        <el-option label="草稿" value="draft" /><el-option label="就绪" value="ready" /><el-option label="废弃" value="deprecated" />
      </el-select>
      <el-select v-model="filters.version" placeholder="版本" clearable filterable style="width:140px" @change="load">
        <el-option v-for="v in versions" :key="v.id" :label="v.name" :value="v.id" />
      </el-select>
      <el-select v-model="filters.iteration" placeholder="迭代" clearable filterable style="width:160px" @change="load">
        <el-option v-for="it in iterations" :key="it.id" :label="it.name" :value="it.id" />
      </el-select>
      <el-input v-model="q" placeholder="搜索标题/编号" style="width:240px" clearable @keyup.enter="load" />
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="success" @click="openCreate">新建用例</el-button>
      <el-button type="warning" @click="$router.push('/compose')">用例编排</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="case_id" label="编号" width="120" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="type" label="类型" width="80">
        <template #default="{ row }">
          <el-tag :type="row.type === 'api' ? 'primary' : 'success'" size="small">{{ row.type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80">
        <template #default="{ row }">P{{ row.priority }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'ready' ? 'success' : row.status === 'deprecated' ? 'info' : 'warning'" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="tags" label="标签" width="160" />
      <el-table-column label="操作" width="260">
        <template #default="{ row }">
          <el-button link type="success" @click="$router.push({ name: 'case-composer', query: { project: row.project } })">编排</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-popconfirm title="确认删除?" @confirm="remove(row.id)">
            <template #reference><el-button link type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg.visible" :title="dlg.id ? '编辑用例' : '新建用例'" width="640px">
      <el-form :model="dlg.form" label-width="100px">
        <el-form-item label="项目">
          <el-select v-model="dlg.form.project" filterable>
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="编号"><el-input v-model="dlg.form.case_id" placeholder="SHOP-001" /></el-form-item>
        <el-form-item label="标题"><el-input v-model="dlg.form.title" /></el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="dlg.form.type"><el-radio value="api">API</el-radio><el-radio value="ui">UI</el-radio></el-radio-group>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="dlg.form.priority" style="width:120px">
            <el-option :value="1" label="P0" /><el-option :value="2" label="P1" /><el-option :value="3" label="P2" /><el-option :value="4" label="P3" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="dlg.form.status" style="width:120px">
            <el-option value="draft" label="草稿" /><el-option value="ready" label="就绪" /><el-option value="deprecated" label="废弃" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本">
          <el-select v-model="dlg.form.version" clearable filterable>
            <el-option v-for="v in versions" :key="v.id" :label="v.name" :value="v.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="迭代">
          <el-select v-model="dlg.form.iteration" clearable filterable>
            <el-option v-for="it in iterations" :key="it.id" :label="it.name" :value="it.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签"><el-input v-model="dlg.form.tags" placeholder="逗号分隔,如 smoke,regression" /></el-form-item>
        <el-form-item label="前置条件"><el-input v-model="dlg.form.precondition" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="预期结果"><el-input v-model="dlg.form.expected" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg.visible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { caseApi, iterationApi, projectApi, versionApi, type Iteration, type Project, type TestCase, type Version } from '@/api'

const rows = ref<TestCase[]>([])
const projects = ref<Project[]>([])
const versions = ref<Version[]>([])
const iterations = ref<Iteration[]>([])
const loading = ref(false)
const q = ref('')
const filters = reactive<{ project?: number; type?: string; status?: string; version?: number; iteration?: number }>({})

const dlg = reactive({
  visible: false, id: 0 as number | undefined,
  form: {
    project: undefined, case_id: '', title: '', type: 'api', priority: 2, status: 'draft',
    tags: '', precondition: '', expected: '',
    version: undefined, iteration: undefined,
  } as Partial<TestCase>,
})

async function loadProjects() {
  const r = await projectApi.list()
  projects.value = (r as any).results || []
}
async function loadVersionsIterations() {
  if (!filters.project) { versions.value = []; iterations.value = []; return }
  const [vr, ir] = await Promise.all([
    versionApi.list({ project: filters.project, page_size: 1000 }),
    iterationApi.list({ project: filters.project, page_size: 1000 }),
  ])
  versions.value = (vr as any).results || []
  iterations.value = (ir as any).results || []
}
async function load() {
  loading.value = true
  try {
    const r = await caseApi.list({ search: q.value, ...filters })
    rows.value = (r as any).results || []
  } finally { loading.value = false }
}

// 项目变化时联动版本/迭代
let lastProject: number | undefined
watch(() => filters.project, async (p) => {
  if (p !== lastProject) {
    lastProject = p
    filters.version = undefined
    filters.iteration = undefined
    await loadVersionsIterations()
  }
})

function openCreate() {
  dlg.id = undefined
  dlg.form = {
    project: filters.project, case_id: '', title: '', type: 'api', priority: 2, status: 'draft',
    tags: '', precondition: '', expected: '',
    version: filters.version, iteration: filters.iteration,
  }
  dlg.visible = true
}
function openEdit(row: TestCase) {
  dlg.id = row.id
  dlg.form = { ...row }
  dlg.visible = true
}
async function save() {
  if (dlg.id) await caseApi.update(dlg.id, dlg.form)
  else await caseApi.create(dlg.form)
  ElMessage.success('已保存')
  dlg.visible = false
  load()
}
async function remove(id: number) {
  await caseApi.remove(id)
  ElMessage.success('已删除')
  load()
}

onMounted(async () => { await loadProjects(); load() })</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
</style>
