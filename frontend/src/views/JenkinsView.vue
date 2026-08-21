<template>
  <div>
    <el-card>
      <template #header>Jenkins 集成</template>
      <el-alert type="info" :closable="false" show-icon>
        平台通过 Jenkins REST API 创建/触发/查询 Pipeline job。Job 使用仓库 Jenkinsfile。
      </el-alert>
    </el-card>

    <el-card class="mt-16">
      <template #header>创建 / 更新 Jenkins Job</template>
      <el-form :model="form" label-width="140px">
        <el-form-item label="Job 名称">
          <el-input v-model="form.job_name" placeholder="autotest-shop-smoke" />
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" /></el-form-item>
        <el-form-item label="Suite">
          <el-radio-group v-model="form.suite">
            <el-radio value="all">all</el-radio><el-radio value="api">api</el-radio><el-radio value="ui">ui</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="API Base URL"><el-input v-model="form.api_base_url" placeholder="留空用 Jenkinsfile 默认" /></el-form-item>
        <el-form-item label="UI Base URL"><el-input v-model="form.ui_base_url" placeholder="留空用 Jenkinsfile 默认" /></el-form-item>
        <el-form-item label="仓库 URL"><el-input v-model="form.repo_url" placeholder="https://github.com/org/repo.git" /></el-form-item>
        <el-form-item label="分支"><el-input v-model="form.repo_branch" /></el-form-item>
        <el-form-item label="Git 凭据 ID"><el-input v-model="form.git_creds" placeholder="Jenkins credentialsId,可空" /></el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="creating" @click="createJob">创建/更新 Job</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="mt-16">
      <template #header>查询 Job 信息</template>
      <div class="flex gap-8 mb-8">
        <el-input v-model="queryJob" placeholder="job 名称" style="width:240px" />
        <el-button type="primary" @click="queryJobInfo">查询</el-button>
      </div>
      <el-descriptions v-if="jobInfo" :column="2" border>
        <el-descriptions-item label="存在">{{ jobInfo.exists }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ jobInfo.name }}</el-descriptions-item>
        <el-descriptions-item label="排队中">{{ jobInfo.in_queue }}</el-descriptions-item>
        <el-descriptions-item label="最近构建">{{ jobInfo.last_build }}</el-descriptions-item>
        <el-descriptions-item label="最近结果">{{ jobInfo.last_result }}</el-descriptions-item>
        <el-descriptions-item label="URL">
          <el-link v-if="jobInfo.url" :href="jobInfo.url" target="_blank">{{ jobInfo.url }}</el-link>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { jenkinsApi } from '@/api'

const form = reactive({
  job_name: '', description: '', suite: 'all' as 'all'|'api'|'ui',
  api_base_url: '', ui_base_url: '', repo_url: '', repo_branch: 'main', git_creds: '',
})
const creating = ref(false)
const queryJob = ref('')
const jobInfo = ref<any>(null)

async function createJob() {
  creating.value = true
  try {
    await jenkinsApi.createJob(form)
    ElMessage.success('Job 已创建/更新')
  } finally { creating.value = false }
}
async function queryJobInfo() {
  jobInfo.value = await jenkinsApi.jobInfo(queryJob.value)
}
</script>
