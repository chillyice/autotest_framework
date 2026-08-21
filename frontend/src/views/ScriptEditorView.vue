<template>
  <div class="editor-page">
    <div class="toolbar">
      <el-button link type="primary" @click="$router.back()"><el-icon><Back /></el-icon> 返回</el-button>
      <span class="file-path">{{ script?.file_path }}</span>
      <div class="flex-1"></div>
      <el-tag v-if="dirty" type="warning" size="small">未保存</el-tag>
      <el-button type="primary" :loading="saving" :disabled="!dirty" @click="save">保存 (Ctrl+S)</el-button>
    </div>
    <div ref="editorEl" class="monaco-container"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as monaco from 'monaco-editor'
import { scriptApi, type Script } from '@/api'

const route = useRoute()
const editorEl = ref<HTMLDivElement>()
const script = ref<Script>()
const saving = ref(false)
const dirty = ref(false)
let editor: monaco.editor.IStandaloneCodeEditor | null = null

async function load() {
  const id = Number(route.params.id)
  script.value = await scriptApi.get(id)
  const content = await scriptApi.getContent(id)
  if (!editorEl.value) return
  editor = monaco.editor.create(editorEl.value, {
    value: content,
    language: 'python',
    theme: 'vs',
    automaticLayout: true,
    fontSize: 13,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    tabSize: 4,
  })
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, save)
  editor.onDidChangeModelContent(() => { dirty.value = true })
}

async function save() {
  if (!editor || !script.value) return
  saving.value = true
  try {
    await scriptApi.saveContent(script.value.id, editor.getValue())
    dirty.value = false
    ElMessage.success('已保存')
  } finally { saving.value = false }
}

onMounted(load)
onBeforeUnmount(() => editor?.dispose())
</script>

<style scoped>
.editor-page { display: flex; flex-direction: column; height: calc(100vh - 90px); }
.toolbar { display: flex; align-items: center; gap: 12px; padding: 8px 12px; background: #fff; border-radius: 6px; margin-bottom: 8px; }
.file-path { font-family: monospace; color: #606266; }
.monaco-container { flex: 1; border: 1px solid #dcdfe6; border-radius: 6px; overflow: hidden; }
</style>
