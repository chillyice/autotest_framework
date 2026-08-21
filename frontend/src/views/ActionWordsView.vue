<template>
  <div>
    <div class="toolbar">
      <el-select v-model="filters.project" placeholder="项目" clearable filterable style="width:180px" @change="load">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-input v-model="q" placeholder="搜索名称/key/分类" style="width:240px" clearable @keyup.enter="load" />
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="success" @click="openCreate">新建 AW</el-button>
      <el-button type="warning" :loading="parsing" @click="openParseDlg">从 OpenAPI 解析</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="category" label="分类" width="120" />
      <el-table-column prop="name" label="名称" width="200" />
      <el-table-column prop="key" label="Key" width="180" />
      <el-table-column label="接口" width="200">
        <template #default="{ row }">
          <el-tag v-if="row.method" :type="methodType(row.method)" size="small">{{ row.method }}</el-tag>
          <span style="margin-left:6px;font-family:monospace;font-size:12px">{{ row.endpoint }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="source" label="来源" width="100">
        <template #default="{ row }">
          <el-tag :type="row.source === 'openapi' ? 'primary' : 'info'" size="small">{{ row.source }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="suggested_section" label="建议区" width="100" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link @click="preview(row)">预览代码</el-button>
          <el-popconfirm title="确认删除?" @confirm="remove(row.id)">
            <template #reference><el-button link type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建/编辑 AW -->
    <el-dialog v-model="dlg.visible" :title="dlg.id ? '编辑 AW' : '新建 AW'" width="720px">
      <el-form :model="dlg.form" label-width="120px">
        <el-form-item label="项目">
          <el-select v-model="dlg.form.project" filterable>
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称"><el-input v-model="dlg.form.name" /></el-form-item>
        <el-form-item label="Key"><el-input v-model="dlg.form.key" placeholder="createOrder" /></el-form-item>
        <el-form-item label="分类"><el-input v-model="dlg.form.category" placeholder="订单" /></el-form-item>
        <el-form-item label="建议区">
          <el-select v-model="dlg.form.suggested_section" style="width:160px">
            <el-option value="any" label="任意" /><el-option value="setup" label="前置" />
            <el-option value="test" label="测试" /><el-option value="teardown" label="后置" />
          </el-select>
        </el-form-item>
        <el-form-item label="接口路径"><el-input v-model="dlg.form.endpoint" placeholder="/orders/{id}" /></el-form-item>
        <el-form-item label="HTTP 方法"><el-input v-model="dlg.form.method" placeholder="POST" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="dlg.form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="代码模板">
          <el-input v-model="dlg.form.code_template" type="textarea" :rows="4" placeholder='resp = http.request("POST", "/orders", json=body)' />
        </el-form-item>
        <el-form-item label="参数 schema (JSON)">
          <el-input v-model="paramsJson" type="textarea" :rows="6" placeholder='{"type":"object","properties":{"body":{"type":"object","in":"body"}}}' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg.visible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- OpenAPI 解析 -->
    <el-dialog v-model="parseDlg.visible" title="从 OpenAPI 解析生成 AW" width="520px">
      <el-form label-width="120px">
        <el-form-item label="项目">
          <el-select v-model="parseDlg.project" filterable>
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Spec 路径">
          <el-input v-model="parseDlg.spec_path" placeholder="留空扫描 data/openapi/ 下全部" />
        </el-form-item>
        <el-form-item label="分类覆盖">
          <el-input v-model="parseDlg.category" placeholder="留空用 OpenAPI tags" />
        </el-form-item>
        <el-form-item label="覆盖已有">
          <el-switch v-model="parseDlg.overwrite" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="parseDlg.visible = false">取消</el-button>
        <el-button type="primary" :loading="parsing" @click="doParse">解析</el-button>
      </template>
    </el-dialog>

    <!-- 预览代码 -->
    <el-dialog v-model="previewDlg.visible" title="AW 代码预览" width="720px">
      <pre class="code-pre">{{ previewDlg.code }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { awApi, projectApi, type ActionWord, type Project } from '@/api'

const rows = ref<ActionWord[]>([])
const projects = ref<Project[]>([])
const loading = ref(false)
const parsing = ref(false)
const q = ref('')
const filters = reactive<{ project?: number }>({})

const dlg = reactive({
  visible: false, id: 0 as number | undefined,
  form: {
    project: undefined, name: '', key: '', category: '', suggested_section: 'any',
    endpoint: '', method: '', description: '', code_template: '',
  } as Partial<ActionWord>,
})
const paramsJson = ref('{}')

const parseDlg = reactive({
  visible: false, project: undefined as number | undefined,
  spec_path: '', category: '', overwrite: true,
})

const previewDlg = reactive({ visible: false, code: '' })

const methodType = (m: string) => ({
  GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info',
}[m] || 'info') as any

async function loadProjects() {
  const r = await projectApi.list()
  projects.value = (r as any).results || []
}
async function load() {
  loading.value = true
  try {
    const r = await awApi.list({ search: q.value, ...filters })
    rows.value = (r as any).results || []
  } finally { loading.value = false }
}

function openCreate() {
  dlg.id = undefined
  dlg.form = { project: filters.project, name: '', key: '', category: '', suggested_section: 'any', endpoint: '', method: '', description: '', code_template: '' }
  paramsJson.value = '{}'
  dlg.visible = true
}
function openEdit(row: ActionWord) {
  dlg.id = row.id
  dlg.form = { ...row }
  paramsJson.value = JSON.stringify(row.parameters || {}, null, 2)
  dlg.visible = true
}
async function save() {
  let params = {}
  try { params = JSON.parse(paramsJson.value || '{}') } catch { ElMessage.error('参数 schema 不是合法 JSON'); return }
  const payload = { ...dlg.form, parameters: params }
  if (dlg.id) await awApi.update(dlg.id, payload)
  else await awApi.create(payload)
  ElMessage.success('已保存')
  dlg.visible = false
  load()
}
async function remove(id: number) {
  await awApi.remove(id)
  ElMessage.success('已删除')
  load()
}
function openParseDlg() {
  parseDlg.project = filters.project
  parseDlg.spec_path = ''
  parseDlg.category = ''
  parseDlg.overwrite = true
  parseDlg.visible = true
}
async function doParse() {
  if (!parseDlg.project) { ElMessage.warning('请选项目'); return }
  parsing.value = true
  try {
    const r = await awApi.parse({
      project: parseDlg.project,
      spec_path: parseDlg.spec_path || undefined,
      category: parseDlg.category || undefined,
      overwrite: parseDlg.overwrite,
    })
    const sum = r.results.reduce((acc, x) => ({ created: acc.created + x.created, updated: acc.updated + x.updated, skipped: acc.skipped + x.skipped }), { created: 0, updated: 0, skipped: 0 })
    ElMessage.success(`新建 ${sum.created},更新 ${sum.updated},跳过 ${sum.skipped}`)
    parseDlg.visible = false
    load()
  } finally { parsing.value = false }
}
async function preview(row: ActionWord) {
  const r = await awApi.render(row.id, {})
  previewDlg.code = r.code
  previewDlg.visible = true
}

onMounted(async () => { await loadProjects(); load() })
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.code-pre { background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 13px; white-space: pre-wrap; }
</style>
