<template>
  <el-container class="app-layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">AutoTest</div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#001529"
        text-color="#cfd3dc"
        active-text-color="#fff"
      >
        <template v-for="r in menuRoutes" :key="r.path">
          <el-menu-item :index="r.path">
            <el-icon><component :is="r.meta?.icon" /></el-icon>
            <span>{{ r.meta?.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <span class="page-title">{{ route.meta?.title || 'AutoTest' }}</span>
        <el-dropdown @command="onCommand">
          <span class="user">
            <el-icon><User /></el-icon>
            {{ auth.username || 'Guest' }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { routes } from '@/router'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const menuRoutes = computed(() =>
  routes
    .flatMap(r => r.children || [])
    .filter(r => !r.meta?.hidden)
    .map(r => ({ ...r, path: '/' + r.path }))
)

function onCommand(cmd: string) {
  if (cmd === 'logout') {
    auth.logout()
    router.push({ name: 'login' })
  }
}
</script>

<style scoped>
.app-layout { height: 100vh; }
.sidebar { background: #001529; }
.logo {
  height: 56px; line-height: 56px; color: #fff;
  text-align: center; font-size: 18px; font-weight: 600;
  border-bottom: 1px solid #1f2d3d;
}
.header {
  background: #fff; display: flex; align-items: center;
  justify-content: space-between; border-bottom: 1px solid #ebeef5;
}
.page-title { font-size: 16px; font-weight: 600; }
.user { display: inline-flex; align-items: center; gap: 6px; cursor: pointer; color: #606266; }
.main { background: #f5f7fa; padding: 16px; overflow: auto; }
:deep(.el-menu) { border-right: none; }
</style>
