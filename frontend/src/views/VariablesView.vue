<template>
  <div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="环境" name="envs">
        <div class="toolbar">
          <el-button type="success" @click="openEnvDlg()">新建环境</el-button>
        </div>
        <el-table :data="envs" v-loading="envLoading" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="api_base_url" label="API Base" />
          <el-table-column prop="ui_base_url" label="UI Base" />
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button link type="primary" @click="openEnvDlg(row)">编辑</el-button>
              <el-popconfirm title="确认删除?" @confirm="removeEnv(row.id)">
                <template #reference><el-button link type="danger">删除</el-button></template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="变量" name="vars">
        <div class="vars-layout">
          <!-- 左:目录树 -->
          <div class="cat-panel">
            <div class="cat-head">
              <span>目录</span>
              <el-button link type="primary" size="small" @click="openCatDlg()">+</el-button>
            </div>
            <div class="cat-body">
              <el-select v-model="catProjectFilter" placeholder="项目" clearable size="small" filterable style="width:100%;margin-bottom:8px" @change="loadCategories">
                <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
              <el-tree
                ref="catTreeRef"
                :data="catTree"
                node-key="id"
                :props="{ label: 'name', children: 'children' }"
                :expand-on-click-node="false"
                highlight-current
                default-expand-all
                @node-click="onCatClick"
              >
                <template #default="{ node, data }">
                  <span class="cat-node">
                    <span>{{ node.label }}</span>
                    <span class="cat-actions">
                      <el-icon title="新建子目录" @click.stop="openCatDlg(undefined, data)"><Plus /></el-icon>
                      <el-icon title="编辑" @click.stop="openCatDlg(data)"><Edit /></el-icon>
                      <el-icon title="删除" @click.stop="removeCat(data)"><Delete /></el-icon>
                    </span>
                  </span>
                </template>
              </el-tree>
              <div class="cat-empty" v-if="!catTree.length">
                <el-button link type="primary" @click="openCatDlg()">建第一个目录</el-button>
              </div>
            </div>
          </div>

          <!-- 右:变量表 -->
          <div class="var-panel">
            <div class="toolbar">
              <el-select v-model="filters.scope" placeholder="作用域" clearable style="width:120px" @change="loadVars">
                <el-option label="全局" value="global" /><el-option label="项目" value="project" /><el-option label="环境" value="env" />
              </el-select>
              <el-select v-model="filters.project" placeholder="项目" clearable filterable style="width:180px" @change="loadVars">
                <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
              <el-select v-model="filters.environment" placeholder="环境" clearable style="width:140px" @change="loadVars">
                <el-option v-for="e in envs" :key="e.id" :label="e.name" :value="e.id" />
              </el-select>
              <el-input v-model="q" placeholder="搜索 key/备注" style="width:200px" clearable @keyup.enter="loadVars" />
              <el-button type="primary" @click="loadVars">查询</el-button>
              <el-button type="success" @click="openVarDlg()">新建变量</el-button>
            </div>

            <el-table :data="vars" v-loading="varLoading" stripe>
              <el-table-column prop="id" label="ID" width="60" />
              <el-table-column prop="scope" label="作用域" width="80" />
              <el-table-column prop="key" label="Key" width="160">
                <template #default="{ row }">
                  <code>{{ row.key }}</code>
                </template>
              </el-table-column>
              <el-table-column prop="value" label="Value" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="row.is_secret || row.is_encrypted" class="text-warning">*** ({{ row.is_encrypted ? '加密' : '保护' }})</span>
                  <span v-else-if="row.is_dynamic" class="text-muted">动态: <code>{{ row.dynamic_expr }}</code></span>
                  <span v-else>{{ row.value }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="type" label="类型" width="80" />
              <el-table-column label="属性" width="180">
                <template #default="{ row }">
                  <el-tag v-if="row.is_secret" type="warning" size="small">保护</el-tag>
                  <el-tag v-if="row.is_encrypted" type="danger" size="small">加密</el-tag>
                  <el-tag v-if="row.is_dynamic" type="primary" size="small">动态</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="备注" show-overflow-tooltip />
              <el-table-column label="操作" width="180">
                <template #default="{ row }">
                  <el-button v-if="row.is_secret || row.is_encrypted || row.is_dynamic" link @click="reveal(row)">查看值</el-button>
                  <el-button link type="primary" @click="openVarDlg(row)">编辑</el-button>
                  <el-popconfirm title="确认删除?" @confirm="removeVar(row.id)">
                    <template #reference><el-button link type="danger">删除</el-button></template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 环境对话框 -->
    <el-dialog v-model="envDlg.visible" :title="envDlg.id ? '编辑环境' : '新建环境'" width="500px">
      <el-form :model="envDlg.form" label-width="100px">
        <el-form-item label="名称"><el-input v-model="envDlg.form.name" /></el-form-item>
        <el-form-item label="API Base"><el-input v-model="envDlg.form.api_base_url" /></el-form-item>
        <el-form-item label="UI Base"><el-input v-model="envDlg.form.ui_base_url" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="envDlg.form.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="envDlg.visible = false">取消</el-button>
        <el-button type="primary" @click="saveEnv">保存</el-button>
      </template>
    </el-dialog>

    <!-- 目录对话框 -->
    <el-dialog v-model="catDlg.visible" :title="catDlg.id ? '编辑目录' : '新建目录'" width="480px">
      <el-form :model="catDlg.form" label-width="100px">
        <el-form-item label="项目">
          <el-select v-model="catDlg.form.project" clearable filterable>
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="父目录" v-if="catDlg.parent">
          <el-input :model-value="catDlg.parent.path || catDlg.parent.name" disabled />
        </el-form-item>
        <el-form-item label="名称"><el-input v-model="catDlg.form.name" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="catDlg.visible = false">取消</el-button>
        <el-button type="primary" @click="saveCat">保存</el-button>
      </template>
    </el-dialog>

    <!-- 变量对话框 -->
    <el-dialog v-model="varDlg.visible" :title="varDlg.id ? '编辑变量' : '新建变量'" width="640px">
      <el-form :model="varDlg.form" label-width="120px">
        <el-form-item label="作用域">
          <el-select v-model="varDlg.form.scope" style="width:160px" @change="onScopeChange">
            <el-option label="全局" value="global" /><el-option label="项目" value="project" /><el-option label="环境" value="env" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" v-if="varDlg.form.scope !== 'global'">
          <el-select v-model="varDlg.form.project" clearable filterable>
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="环境" v-if="varDlg.form.scope === 'env'">
          <el-select v-model="varDlg.form.environment" clearable filterable>
            <el-option v-for="e in envs" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="目录">
          <el-cascader
            v-model="varDlg.categoryPath"
            :options="catCascaderOptions"
            :props="{ checkStrictly: true, emitPath: true, label: 'name', value: 'id', children: 'children' }"
            clearable
            placeholder="不选目录"
            style="width:100%"
            @change="onCategoryChange"
          />
        </el-form-item>
        <el-form-item label="Key"><el-input v-model="varDlg.form.key" placeholder="如 base_url" /></el-form-item>

        <el-form-item label="是否动态">
          <el-switch v-model="varDlg.form.is_dynamic" @change="onDynamicToggle" />
          <span class="text-muted" style="margin-left:8px">动态变量:value 存表达式,运行时计算</span>
        </el-form-item>

        <el-form-item v-if="varDlg.form.is_dynamic" label="动态表达式">
          <el-input v-model="varDlg.form.dynamic_expr" type="textarea" :rows="2" placeholder="datetime.now().strftime('%Y%m%d%H%M%S')" />
          <el-button link type="primary" size="small" @click="testDynamic">测试表达式</el-button>
          <span v-if="dynamicTestResult" class="text-success" style="margin-left:8px">= {{ dynamicTestResult }}</span>
        </el-form-item>

        <el-form-item v-else label="Value">
          <el-input
            v-model="varDlg.form.value"
            :type="(varDlg.form.is_secret || varDlg.form.is_encrypted) && varDlg.valueHidden ? 'password' : 'text'"
            :placeholder="varDlg.id && (varDlg.form.is_secret || varDlg.form.is_encrypted) ? '*** 留空不修改' : ''"
          >
            <template #append v-if="varDlg.form.is_secret || varDlg.form.is_encrypted">
              <el-button @click="varDlg.valueHidden = !varDlg.valueHidden">
                <el-icon><View v-if="varDlg.valueHidden" /><Hide v-else /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="类型">
          <el-select v-model="varDlg.form.type" style="width:120px">
            <el-option value="string" /><el-option value="int" /><el-option value="bool" /><el-option value="json" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="varDlg.form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="保护">
          <el-switch v-model="varDlg.form.is_secret" />
          <span class="text-muted" style="margin-left:8px">API 返回 ***</span>
        </el-form-item>
        <el-form-item label="加密存储">
          <el-switch v-model="varDlg.form.is_encrypted" />
          <span class="text-muted" style="margin-left:8px">Fernet 对称加密入库</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="varDlg.visible = false">取消</el-button>
        <el-button type="primary" @click="saveVar">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { categoryApi, envApi, projectApi, varApi, type Environment, type Project, type Variable, type VariableCategory } from '@/api'

const activeTab = ref('vars')
const projects = ref<Project[]>([])
const envs = ref<Environment[]>([])
const vars = ref<Variable[]>([])
const categories = ref<VariableCategory[]>([])
const envLoading = ref(false)
const varLoading = ref(false)
const q = ref('')
const catProjectFilter = ref<number | undefined>()
const filters = reactive<{ scope?: string; project?: number; environment?: number; category?: number }>({})
const dynamicTestResult = ref('')

const envDlg = reactive({
  visible: false, id: 0 as number | undefined,
  form: { name: '', api_base_url: '', ui_base_url: '', description: '' } as Partial<Environment>,
})

const catDlg = reactive({
  visible: false, id: 0 as number | undefined, parent: null as VariableCategory | null,
  form: { project: undefined as number | undefined, parent: undefined as number | undefined, name: '' } as Partial<VariableCategory>,
})

const varDlg = reactive({
  visible: false, id: 0 as number | undefined, valueHidden: true,
  categoryPath: [] as number[],
  form: {
    scope: 'global', project: undefined, environment: undefined, category: undefined,
    key: '', value: '', type: 'string', description: '',
    is_secret: false, is_encrypted: false, is_dynamic: false, dynamic_expr: '',
  } as Partial<Variable>,
})

// 目录树:把平铺的 categories 组装成树
const catTree = computed(() => {
  const byId = new Map<number, any>()
  const roots: any[] = []
  for (const c of categories.value) {
    byId.set(c.id, { ...c, children: [] })
  }
  for (const c of categories.value) {
    const node = byId.get(c.id)!
    if (c.parent && byId.has(c.parent)) {
      byId.get(c.parent)!.children.push(node)
    } else {
      roots.push(node)
    }
  }
  return roots
})

const catCascaderOptions = computed(() => catTree.value)

async function loadProjects() {
  const r = await projectApi.list()
  projects.value = (r as any).results || []
}
async function loadEnvs() {
  envLoading.value = true
  try {
    const r = await envApi.list()
    envs.value = (r as any).results || []
  } finally { envLoading.value = false }
}
async function loadCategories() {
  const r = await categoryApi.list({ project: catProjectFilter.value, page_size: 1000 })
  categories.value = (r as any).results || []
}
async function loadVars() {
  varLoading.value = true
  try {
    const r = await varApi.list({ search: q.value, ...filters })
    vars.value = (r as any).results || []
  } finally { varLoading.value = false }
}

function onCatClick(node: any) {
  filters.category = node.id
  loadVars()
}

function openEnvDlg(row?: Environment) {
  envDlg.id = row?.id
  envDlg.form = row ? { ...row } : { name: '', api_base_url: '', ui_base_url: '', description: '' }
  envDlg.visible = true
}
async function saveEnv() {
  if (envDlg.id) await envApi.update(envDlg.id, envDlg.form)
  else await envApi.create(envDlg.form)
  ElMessage.success('已保存')
  envDlg.visible = false
  loadEnvs()
}
async function removeEnv(id: number) {
  await envApi.remove(id)
  ElMessage.success('已删除')
  loadEnvs()
}

function openCatDlg(row?: VariableCategory, parent?: VariableCategory) {
  catDlg.id = row?.id
  catDlg.parent = parent || null
  catDlg.form = row
    ? { ...row }
    : { project: catProjectFilter.value, parent: parent?.id, name: '' }
  catDlg.visible = true
}
async function saveCat() {
  if (catDlg.id) await categoryApi.update(catDlg.id, catDlg.form)
  else await categoryApi.create(catDlg.form)
  ElMessage.success('已保存')
  catDlg.visible = false
  loadCategories()
}
async function removeCat(row: VariableCategory) {
  await ElMessageBox.confirm(`删除目录 "${row.name}"? 目录下变量会变为无目录。`, '确认', { type: 'warning' })
  await categoryApi.remove(row.id)
  ElMessage.success('已删除')
  loadCategories()
}

function openVarDlg(row?: Variable) {
  varDlg.id = row?.id
  varDlg.valueHidden = true
  varDlg.categoryPath = []
  varDlg.form = row
    ? { ...row, value: row.is_secret || row.is_encrypted ? '***' : row.value }
    : {
        scope: 'global', project: filters.project, environment: undefined, category: undefined,
        key: '', value: '', type: 'string', description: '',
        is_secret: false, is_encrypted: false, is_dynamic: false, dynamic_expr: '',
      }
  if (row?.category) varDlg.categoryPath = [row.category]
  dynamicTestResult.value = ''
  varDlg.visible = true
}
function onScopeChange() {
  if (varDlg.form.scope === 'global') {
    varDlg.form.project = undefined
    varDlg.form.environment = undefined
  }
}
function onCategoryChange(path: number[]) {
  varDlg.form.category = path && path.length ? path[path.length - 1] : undefined
}
function onDynamicToggle(v: boolean) {
  if (v && !varDlg.form.dynamic_expr) {
    varDlg.form.dynamic_expr = "datetime.now().strftime('%Y%m%d%H%M%S')"
  }
}
async function testDynamic() {
  if (!varDlg.form.dynamic_expr) return
  try {
    const r = await varApi.testDynamic(varDlg.form.dynamic_expr)
    dynamicTestResult.value = r.result
  } catch { dynamicTestResult.value = '错误' }
}
async function saveVar() {
  // 加密/保护的变量,value 是 *** 时表示不修改,清空避免覆盖
  if ((varDlg.form.is_secret || varDlg.form.is_encrypted) && varDlg.form.value === '***') {
    varDlg.form.value = ''
  }
  if (varDlg.id) await varApi.update(varDlg.id, varDlg.form)
  else await varApi.create(varDlg.form)
  ElMessage.success('已保存')
  varDlg.visible = false
  loadVars()
}
async function removeVar(id: number) {
  await varApi.remove(id)
  ElMessage.success('已删除')
  loadVars()
}
async function reveal(row: Variable) {
  const r = await varApi.reveal(row.id)
  ElMessageBox.alert(r.value, `变量 ${row.key} 的值`, { confirmButtonText: '关闭' })
}

onMounted(async () => {
  await loadProjects()
  await loadEnvs()
  await loadCategories()
  loadVars()
})
</script>

<style scoped>
.vars-layout { display: flex; gap: 12px; min-height: 500px; }
.cat-panel { width: 260px; background: #fff; border-radius: 6px; display: flex; flex-direction: column; }
.cat-head { padding: 8px 12px; border-bottom: 1px solid #ebeef5; display: flex; align-items: center; justify-content: space-between; font-weight: 600; }
.cat-body { padding: 8px; overflow: auto; flex: 1; }
.var-panel { flex: 1; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.cat-node { display: flex; align-items: center; justify-content: space-between; width: 100%; padding-right: 4px; }
.cat-actions { display: none; gap: 4px; }
.cat-node:hover .cat-actions { display: inline-flex; }
.cat-actions .el-icon { cursor: pointer; color: #909399; font-size: 12px; }
.cat-actions .el-icon:hover { color: #409eff; }
.cat-empty { text-align: center; padding: 16px; color: #909399; }
code { background: #f5f7fa; padding: 1px 4px; border-radius: 2px; font-family: monospace; font-size: 12px; }
</style>
