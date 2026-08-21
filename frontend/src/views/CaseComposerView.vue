<template>
  <div class="composer">
    <!-- 顶部工具栏 -->
    <div class="topbar">
      <el-select v-model="projectId" placeholder="选择项目" filterable size="small" style="width:180px" @change="onProjectChange">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>

      <el-select v-model="versionId" placeholder="版本" clearable size="small" style="width:120px" @change="reloadTree">
        <el-option v-for="v in versions" :key="v.id" :label="v.name" :value="v.id" />
      </el-select>

      <el-select v-model="iterationId" placeholder="迭代" clearable size="small" style="width:160px" @change="reloadTree">
        <el-option v-for="it in iterations" :key="it.id" :label="it.name" :value="it.id" />
      </el-select>

      <el-divider direction="vertical" />

      <span v-if="currentCase" class="case-title">
        <el-tag :type="currentCase.type === 'api' ? 'primary' : 'success'" size="small">{{ currentCase.type }}</el-tag>
        <span style="margin:0 4px">{{ currentCase.case_id }}</span>
        {{ currentCase.title }}
      </span>
      <span v-else class="text-muted">从左侧用例树选择一条用例</span>

      <div class="flex-1"></div>
      <el-button size="small" :disabled="!currentCase" :loading="saving" @click="save(false)">保存步骤</el-button>
      <el-button size="small" type="primary" :disabled="!currentCase" :loading="saving" @click="save(true)">保存并生成脚本</el-button>
    </div>

    <div class="body">
      <!-- 左:用例树 -->
      <div class="panel case-tree-panel">
        <div class="panel-head">
          <span>用例树</span>
          <el-input v-model="caseFilter" placeholder="过滤" size="small" clearable style="width:120px" />
        </div>
        <div class="panel-body">
          <el-tree
            ref="treeRef"
            :data="caseTree"
            node-key="id"
            :props="{ label: 'name', children: 'children' }"
            :expand-on-click-node="false"
            highlight-current
            default-expand-all
            @node-click="onCaseClick"
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <span v-if="data.type === 'module'" class="tree-folder">
                  <el-icon><Folder /></el-icon> {{ node.label }}
                </span>
                <span v-else-if="data.type === 'project'" class="tree-folder">
                  <el-icon><Box /></el-icon> {{ node.label }}
                </span>
                <span v-else class="tree-case">
                  <el-tag :type="data.case_type === 'api' ? 'primary' : 'success'" size="small">{{ data.case_type }}</el-tag>
                  <span class="case-name" :title="data.name">{{ data.name }}</span>
                </span>
              </span>
            </template>
          </el-tree>
          <el-empty v-if="!caseTree.length" description="选项目加载用例" :image-size="40" />
        </div>
      </div>

      <!-- 中:画板 -->
      <div class="panel canvas-panel">
        <div class="canvas-head">
          <span>步骤编排画板</span>
          <span class="text-muted" style="font-size:12px">从右侧 AW 库拖入,可跨区调整</span>
        </div>
        <div class="canvas-body" v-if="currentCase">
          <SectionBlock
            v-for="sec in sections" :key="sec.key"
            :title="sec.title" :color="sec.color"
            :list="sectionLists[sec.key]"
            :selected-id="selectedId"
            @select="onSelect"
            @remove="onRemove"
            @toggle="onToggle"
            @change="onSectionsChange"
          />

          <el-divider content-position="left">选中步骤详情</el-divider>
          <div v-if="selected" class="step-detail">
            <el-form label-position="top" size="small">
              <el-row :gutter="8">
                <el-col :span="12">
                  <el-form-item label="步骤名"><el-input v-model="selected.name" :placeholder="selected.action_word_detail?.name" /></el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="启用"><el-switch v-model="selected.enabled" /></el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="区段">
                    <el-select v-model="selected.section" size="small" @change="onSectionMove">
                      <el-option value="setup" label="前置" />
                      <el-option value="test" label="测试" />
                      <el-option value="teardown" label="后置" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="备注"><el-input v-model="selected.comment" type="textarea" :rows="1" /></el-form-item>
              <el-divider content-position="left">
                <span style="font-size:12px">参数</span>
                <el-text type="info" size="small" style="margin-left:8px">$${全局} / ${局部}</el-text>
              </el-divider>
              <div v-if="paramFields.length">
                <el-row v-for="f in paramFields" :key="f.name">
                  <el-form-item :label="`${f.name} (${f.in || '-'})`" style="width:100%">
                    <el-input v-model="paramValues[f.name]" :placeholder="f.description || String(f.default ?? '')" @input="onParamChange">
                      <template #append>
                        <el-dropdown trigger="click" @command="(cmd: string) => insertVarRef(f.name, cmd)">
                          <el-button><el-icon><Plus /></el-icon></el-button>
                          <template #dropdown>
                            <el-dropdown-menu>
                              <el-dropdown-item v-for="g in globalVarKeys" :key="g" :command="`global:${g}`">
                                <code>$${{ g }}</code>
                              </el-dropdown-item>
                              <el-dropdown-item v-for="l in localVars" :key="l" :command="`local:${l}`">
                                <code>${{ l }}</code>
                              </el-dropdown-item>
                              <el-dropdown-item v-if="!globalVarKeys.length && !localVars.length" disabled>(无)</el-dropdown-item>
                            </el-dropdown-menu>
                          </template>
                        </el-dropdown>
                      </template>
                    </el-input>
                  </el-form-item>
                </el-row>
              </div>
              <el-empty v-else description="该 AW 无参数" :image-size="30" />
              <el-divider content-position="left"><span style="font-size:12px">渲染后代码</span></el-divider>
              <pre class="code-pre">{{ selected.rendered_code || '(保存后刷新)' }}</pre>
            </el-form>
          </div>
          <el-empty v-else description="选择一个步骤查看详情" :image-size="40" />

          <el-divider content-position="left"><span style="font-size:12px">整用例预览</span></el-divider>
          <pre class="code-pre full-preview">{{ fullPreview }}</pre>
        </div>
        <div class="canvas-body" v-else>
          <el-empty description="选择左侧用例后开始编排" />
        </div>
      </div>

      <!-- 右:AW 库 -->
      <div class="panel aw-panel">
        <div class="panel-head">
          <span>AW 库</span>
          <el-input v-model="awFilter" placeholder="过滤" size="small" clearable style="width:120px" />
        </div>
        <div class="panel-body">
          <div v-for="group in groupedAws" :key="group.category" class="aw-group">
            <div class="aw-cat">{{ group.category || '未分类' }}</div>
            <draggable
              :list="group.items"
              :group="{ name: 'aw', pull: 'clone', put: false }"
              :sort="false"
              item-key="id"
              :clone="cloneAw"
            >
              <template #item="{ element }">
                <div class="aw-item" :title="element.description">
                  <el-tag v-if="element.method" :type="methodType(element.method)" size="small">{{ element.method }}</el-tag>
                  <span class="aw-name">{{ element.name }}</span>
                </div>
              </template>
            </draggable>
          </div>
          <el-empty v-if="!aws.length" description="AW 库为空" :image-size="40" />
        </div>
      </div>
    </div>

    <!-- 生成脚本对话框 -->
    <el-dialog v-model="genDlg.visible" title="生成脚本" width="640px">
      <el-form label-width="120px">
        <el-form-item label="文件路径">
          <el-input v-model="genDlg.file_path" placeholder="api/test_shop_001.py" />
        </el-form-item>
        <el-form-item label="同步存为 Script">
          <el-switch v-model="genDlg.save_script" />
          <span class="text-muted" style="margin-left:8px">同时写盘 + 入库</span>
        </el-form-item>
      </el-form>
      <pre v-if="genDlg.code" class="code-pre">{{ genDlg.code }}</pre>
      <template #footer>
        <el-button @click="genDlg.visible = false">关闭</el-button>
        <el-button type="primary" :loading="genDlg.loading" @click="confirmGen">确认生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import draggable from 'vuedraggable'

import SectionBlock from './components/SectionBlock.vue'
import {
  awApi, caseApi, iterationApi, moduleApi, projectApi, varApi, versionApi,
  type ActionWord, type Iteration, type Module, type Project, type TestCase, type TestCaseStep, type Version,
} from '@/api'

const sections = [
  { key: 'setup', title: '前置步骤', color: '#409eff' },
  { key: 'test', title: '测试步骤', color: '#67c23a' },
  { key: 'teardown', title: '后置步骤', color: '#e6a23c' },
] as const

// 顶部筛选
const projectId = ref<number | undefined>()
const versionId = ref<number | undefined>()
const iterationId = ref<number | undefined>()
const projects = ref<Project[]>([])
const versions = ref<Version[]>([])
const iterations = ref<Iteration[]>([])

// 左:用例树
const caseFilter = ref('')
const modules = ref<Module[]>([])
const allCases = ref<TestCase[]>([])
const currentCase = ref<TestCase | null>(null)

// 右:AW 库
const aws = ref<ActionWord[]>([])
const awFilter = ref('')

// 中:画板
const setupSteps = ref<TestCaseStep[]>([])
const testSteps = ref<TestCaseStep[]>([])
const teardownSteps = ref<TestCaseStep[]>([])
const sectionLists = { setup: setupSteps, test: testSteps, teardown: teardownSteps } as const
const selectedId = ref<number | undefined>()
const fullPreview = ref('')
const saving = ref(false)
const paramValues = reactive<Record<string, string>>({})
const globalVarKeys = ref<string[]>([])

const genDlg = reactive({
  visible: false, file_path: '', save_script: true, code: '', loading: false,
})

const methodType = (m?: string) => ({
  GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info',
}[m || ''] || 'info') as any

// ============ 用例树 ============
const caseTree = computed(() => {
  // 项目根 -> 模块树 -> 用例叶
  if (!projectId.value) return []
  const proj = projects.value.find(p => p.id === projectId.value)
  if (!proj) return []
  const root: any = { id: `p-${proj.id}`, name: proj.name, type: 'project', children: [] }

  const moduleNodes: Record<number, any> = {}
  for (const m of modules.value) {
    moduleNodes[m.id] = { id: `m-${m.id}`, name: m.name, type: 'module', children: [], _moduleId: m.id }
  }
  for (const m of modules.value) {
    if (m.parent && moduleNodes[m.parent]) {
      moduleNodes[m.parent].children.push(moduleNodes[m.id])
    } else {
      root.children.push(moduleNodes[m.id])
    }
  }

  // 用例按 module 归类
  const filtered = filterCases(allCases.value)
  for (const c of filtered) {
    const leaf = {
      id: `c-${c.id}`, name: `${c.case_id} ${c.title}`,
      type: 'case', case_type: c.type, _caseId: c.id,
    }
    if (c.module && moduleNodes[c.module]) {
      moduleNodes[c.module].children.push(leaf)
    } else {
      root.children.push(leaf)
    }
  }
  return [root]
})

function filterCases(list: TestCase[]) {
  if (!caseFilter.value) return list
  const q = caseFilter.value.toLowerCase()
  return list.filter(c => c.case_id.toLowerCase().includes(q) || c.title.toLowerCase().includes(q))
}

const filteredAws = computed(() => {
  if (!awFilter.value) return aws.value
  const q = awFilter.value.toLowerCase()
  return aws.value.filter(a =>
    a.name.toLowerCase().includes(q) || a.key.toLowerCase().includes(q) ||
    (a.category || '').toLowerCase().includes(q)
  )
})

const groupedAws = computed(() => {
  const map = new Map<string, ActionWord[]>()
  for (const a of filteredAws.value) {
    const k = a.category || ''
    if (!map.has(k)) map.set(k, [])
    map.get(k)!.push(a)
  }
  return Array.from(map.entries()).map(([category, items]) => ({ category, items }))
})

const steps = computed(() => [
  ...setupSteps.value, ...testSteps.value, ...teardownSteps.value,
])
const selected = computed(() => steps.value.find(s => s.id === selectedId.value))

const paramFields = computed(() => {
  const aw = selected.value?.action_word_detail
  if (!aw?.parameters?.properties) return []
  return Object.entries(aw.parameters.properties).map(([name, schema]: [string, any]) => ({
    name, in: schema.in, description: schema.description, default: schema.default, type: schema.type,
  }))
})

const localVars = computed(() => {
  const set = new Set<string>()
  for (const s of steps.value) {
    if (!s.params) continue
    for (const v of Object.values(s.params)) {
      if (typeof v === 'string') {
        const re = /^\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}$/
        const m = v.match(re)
        if (m) set.add(m[1])
      }
    }
  }
  return Array.from(set)
})

// ============ 加载 ============
async function loadProjects() {
  const r = await projectApi.list({ page_size: 1000 })
  projects.value = (r as any).results || []
}
async function loadVersions() {
  if (!projectId.value) { versions.value = []; return }
  const r = await versionApi.list({ project: projectId.value, page_size: 1000 })
  versions.value = (r as any).results || []
}
async function loadIterations() {
  if (!projectId.value) { iterations.value = []; return }
  const r = await iterationApi.list({ project: projectId.value, page_size: 1000 })
  iterations.value = (r as any).results || []
}
async function loadTree() {
  if (!projectId.value) return
  const [mr, cr] = await Promise.all([
    moduleApi.list({ project: projectId.value, page_size: 1000 }),
    caseApi.list({ project: projectId.value, version: versionId.value, iteration: iterationId.value, page_size: 1000 }),
  ])
  modules.value = (mr as any).results || []
  allCases.value = (cr as any).results || []
}
async function loadAws() {
  if (!projectId.value) return
  const r = await awApi.list({ project: projectId.value, page_size: 1000 })
  aws.value = (r as any).results || []
}
async function loadGlobalVars() {
  if (!projectId.value) return
  const r = await varApi.list({ scope: 'global', project: projectId.value, page_size: 1000 })
  globalVarKeys.value = ((r as any).results || []).map((v: any) => v.key)
}

async function onProjectChange() {
  versionId.value = undefined
  iterationId.value = undefined
  currentCase.value = null
  await Promise.all([loadVersions(), loadIterations(), loadTree(), loadAws(), loadGlobalVars()])
}
async function reloadTree() { await loadTree() }

// ============ 用例选中 ============
async function onCaseClick(node: any) {
  if (node.type !== 'case' || !node._caseId) return
  const id = node._caseId
  currentCase.value = await caseApi.get(id)
  const ss = await caseApi.getSteps(id)
  const mapped = ss.map(s => ({
    ...s,
    action_word_detail: aws.value.find(a => a.id === s.action_word) || s.action_word_detail,
  }))
  setupSteps.value = mapped.filter(s => s.section === 'setup')
  testSteps.value = mapped.filter(s => s.section === 'test')
  teardownSteps.value = mapped.filter(s => s.section === 'teardown')
  selectedId.value = undefined
  onSectionsChange()
}

// ============ 拖拽 ============
let stepSeq = 0
function cloneAw(aw: ActionWord): TestCaseStep {
  return {
    action_word: aw.id,
    action_word_detail: aw,
    section: 'test',
    order: ++stepSeq,
    name: '',
    params: {},
    enabled: true,
    comment: '',
  }
}

function onSectionsChange() {
  for (const sec of sections) {
    const arr = sectionLists[sec.key].value
    arr.forEach((s, i) => {
      s.section = sec.key
      s.order = i + 1
    })
  }
  refreshPreview()
}

function onSectionMove() {
  // 用户改了下拉框的 section,把步骤挪到对应段
  if (!selected.value) return
  const s = selected.value
  setupSteps.value = setupSteps.value.filter(x => x !== s)
  testSteps.value = testSteps.value.filter(x => x !== s)
  teardownSteps.value = teardownSteps.value.filter(x => x !== s)
  sectionLists[s.section as keyof typeof sectionLists].value.push(s)
  onSectionsChange()
}

function onSelect(step: TestCaseStep) {
  selectedId.value = step.id
  Object.keys(paramValues).forEach(k => delete paramValues[k])
  const aw = step.action_word_detail
  if (aw?.parameters?.properties) {
    for (const name of Object.keys(aw.parameters.properties)) {
      paramValues[name] = String((step.params as any)?.[name] ?? aw.parameters.properties[name].default ?? '')
    }
  }
}
function onRemove(step: TestCaseStep) {
  setupSteps.value = setupSteps.value.filter(s => s !== step)
  testSteps.value = testSteps.value.filter(s => s !== step)
  teardownSteps.value = teardownSteps.value.filter(s => s !== step)
  if (selectedId.value === step.id) selectedId.value = undefined
  onSectionsChange()
}
function onToggle(step: TestCaseStep) {
  step.enabled = !step.enabled
  refreshPreview()
}
function onParamChange() {
  if (!selected.value) return
  const out: Record<string, any> = {}
  const aw = selected.value.action_word_detail
  const props = aw?.parameters?.properties || {}
  for (const name of Object.keys(paramValues)) {
    const sch = props[name]
    const raw = paramValues[name]
    if (raw === '' || raw == null) continue
    if (sch?.type === 'int') out[name] = Number(raw)
    else if (sch?.type === 'bool') out[name] = raw === 'true' || raw === '1'
    else if (sch?.type === 'object' || sch?.in === 'body') {
      try { out[name] = JSON.parse(raw) } catch { out[name] = raw }
    } else out[name] = raw
  }
  selected.value.params = out
  refreshPreview()
}
function insertVarRef(paramName: string, cmd: string) {
  const [kind, name] = cmd.split(':')
  if (!name) return
  const ref = kind === 'global' ? `$${'$'}{${name}}` : `$\{${name}\}`
  paramValues[paramName] = (paramValues[paramName] || '') + ref
  onParamChange()
}

// ============ 预览 ============
function refreshPreview() {
  if (!currentCase.value) { fullPreview.value = ''; return }
  const lines: string[] = []
  for (const sec of sections) {
    const arr = steps.value.filter(s => s.section === sec.key && s.enabled)
    if (!arr.length) continue
    lines.push(`    # === ${sec.title} ===`)
    arr.forEach((s, i) => {
      lines.push(`    # step ${i + 1}: ${s.name || s.action_word_detail?.name || ''}`)
      const code = s.rendered_code || `# ${s.action_word_detail?.name} (保存后渲染)`
      code.split('\n').forEach(l => lines.push('    ' + l))
      lines.push('')
    })
  }
  if (!lines.length) lines.push('    pass  # 暂无步骤')
  const fn = `test_${currentCase.value.case_id.toLowerCase()}`
  fullPreview.value = `import pytest\n\npytestmark = [pytest.mark.${currentCase.value.type}]\n\ndef ${fn}(http):\n${lines.join('\n')}\n`
}

// ============ 保存 ============
async function save(generate: boolean) {
  if (!currentCase.value) return
  saving.value = true
  try {
    const payload = steps.value.map((s, i) => ({
      id: s.id, action_word: s.action_word, section: s.section,
      order: s.order ?? i, name: s.name, params: s.params || {},
      enabled: s.enabled ?? true, comment: s.comment || '',
    }))
    const saved = await caseApi.saveSteps(currentCase.value.id, payload)
    const mapped = saved.map(s => ({
      ...s,
      action_word_detail: aws.value.find(a => a.id === s.action_word) || s.action_word_detail,
    }))
    setupSteps.value = mapped.filter(s => s.section === 'setup')
    testSteps.value = mapped.filter(s => s.section === 'test')
    teardownSteps.value = mapped.filter(s => s.section === 'teardown')
    ElMessage.success('步骤已保存')
    refreshPreview()
    if (generate) {
      genDlg.file_path = `api/test_${currentCase.value.case_id.toLowerCase()}.py`
      genDlg.save_script = true
      genDlg.code = ''
      genDlg.visible = true
    }
  } finally { saving.value = false }
}

async function confirmGen() {
  if (!currentCase.value) return
  genDlg.loading = true
  try {
    const r = await caseApi.generateScript(currentCase.value.id, {
      file_path: genDlg.file_path || undefined,
      save_script: genDlg.save_script,
    })
    genDlg.code = r.code
    ElMessage.success(r.script_id ? `已生成并保存为 Script #${r.script_id}` : '代码已生成')
  } finally { genDlg.loading = false }
}

onMounted(async () => {
  await loadProjects()
})
</script>

<style scoped>
.composer { display: flex; flex-direction: column; height: calc(100vh - 90px); }
.topbar { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #fff; border-radius: 6px; margin-bottom: 8px; }
.case-title { font-weight: 600; }
.body { flex: 1; display: flex; gap: 8px; min-height: 0; }
.panel { background: #fff; border-radius: 6px; display: flex; flex-direction: column; overflow: hidden; }
.panel-head { padding: 8px 12px; border-bottom: 1px solid #ebeef5; display: flex; align-items: center; justify-content: space-between; font-weight: 600; }
.panel-body { padding: 8px; overflow: auto; flex: 1; }
.case-tree-panel { width: 280px; }
.canvas-panel { flex: 1; }
.aw-panel { width: 260px; }
.canvas-head { padding: 8px 12px; border-bottom: 1px solid #ebeef5; display: flex; align-items: center; gap: 8px; font-weight: 600; }
.canvas-body { padding: 12px; overflow: auto; flex: 1; }
.tree-node { display: flex; align-items: center; flex: 1; }
.tree-folder { display: flex; align-items: center; gap: 4px; color: #606266; }
.tree-case { display: flex; align-items: center; gap: 6px; flex: 1; }
.case-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }
.aw-group { margin-bottom: 12px; }
.aw-cat { font-size: 12px; color: #909399; margin-bottom: 4px; padding: 0 4px; }
.aw-item { display: flex; align-items: center; gap: 6px; padding: 6px 8px; border: 1px solid #ebeef5; border-radius: 4px; margin-bottom: 4px; cursor: grab; background: #fafafa; font-size: 13px; }
.aw-item:hover { border-color: #c6e2ff; background: #ecf5ff; }
.aw-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.step-detail { padding: 8px; background: #fafafa; border-radius: 4px; }
.code-pre { background: #1e1e1e; color: #d4d4d4; padding: 8px; border-radius: 4px; font-family: monospace; font-size: 12px; white-space: pre-wrap; max-height: 200px; overflow: auto; margin: 0; }
.full-preview { max-height: 280px; }
code { background: #e6e8eb; padding: 1px 4px; border-radius: 2px; font-family: monospace; }
</style>
