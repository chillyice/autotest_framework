<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="q" placeholder="搜索项目名/key" style="width:240px" clearable @keyup.enter="load" />
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="success" @click="openCreate">新建项目</el-button>
    </div>
    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="key" label="Key" width="100" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="repo_url" label="仓库地址" show-overflow-tooltip />
      <el-table-column prop="repo_branch" label="分支" width="100" />
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-popconfirm title="确认删除?" @confirm="remove(row.id)">
            <template #reference><el-button link type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg.visible" :title="dlg.id ? '编辑项目' : '新建项目'" width="560px">
      <el-form :model="dlg.form" label-width="100px">
        <el-form-item label="名称"><el-input v-model="dlg.form.name" /></el-form-item>
        <el-form-item label="Key"><el-input v-model="dlg.form.key" placeholder="SHOP" /></el-form-item>
        <el-form-item label="仓库地址"><el-input v-model="dlg.form.repo_url" /></el-form-item>
        <el-form-item label="分支"><el-input v-model="dlg.form.repo_branch" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="dlg.form.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="dlg.form.is_active" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg.visible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { projectApi, type Project } from '@/api'

const rows = ref<Project[]>([])
const loading = ref(false)
const q = ref('')

const dlg = reactive({
  visible: false, id: 0 as number | undefined,
  form: { name: '', key: '', repo_url: '', repo_branch: 'main', description: '', is_active: true } as Partial<Project>,
})

async function load() {
  loading.value = true
  try {
    const r = await projectApi.list({ search: q.value })
    rows.value = (r as any).results || []
  } finally { loading.value = false }
}

function openCreate() {
  dlg.id = undefined
  dlg.form = { name: '', key: '', repo_url: '', repo_branch: 'main', description: '', is_active: true }
  dlg.visible = true
}

function openEdit(row: Project) {
  dlg.id = row.id
  dlg.form = { ...row }
  dlg.visible = true
}

async function save() {
  if (dlg.id) await projectApi.update(dlg.id, dlg.form)
  else await projectApi.create(dlg.form)
  ElMessage.success('已保存')
  dlg.visible = false
  load()
}

async function remove(id: number) {
  await projectApi.remove(id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.page { padding: 0; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
</style>
