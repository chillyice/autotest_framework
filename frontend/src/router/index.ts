import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue'), meta: { title: '仪表盘', icon: 'Odometer' } },
      { path: 'projects', name: 'projects', component: () => import('@/views/ProjectsView.vue'), meta: { title: '项目', icon: 'Folder' } },
      { path: 'versions', name: 'versions', component: () => import('@/views/VersionsView.vue'), meta: { title: '版本', icon: 'CopyDocument' } },
      { path: 'iterations', name: 'iterations', component: () => import('@/views/IterationsView.vue'), meta: { title: '迭代', icon: 'Timer' } },
      { path: 'requirements', name: 'requirements', component: () => import('@/views/RequirementsView.vue'), meta: { title: '需求', icon: 'Document' } },
      { path: 'cases', name: 'cases', component: () => import('@/views/CasesView.vue'), meta: { title: '用例', icon: 'List' } },
      { path: 'compose', name: 'case-composer', component: () => import('@/views/CaseComposerView.vue'), meta: { title: '用例编排', icon: 'EditPen' } },
      { path: 'actionwords', name: 'actionwords', component: () => import('@/views/ActionWordsView.vue'), meta: { title: 'AW 库', icon: 'Box' } },
      { path: 'scripts', name: 'scripts', component: () => import('@/views/ScriptsView.vue'), meta: { title: '脚本', icon: 'Files' } },
      { path: 'scripts/:id', name: 'script-editor', component: () => import('@/views/ScriptEditorView.vue'), meta: { title: '脚本编辑', hidden: true } },
      { path: 'variables', name: 'variables', component: () => import('@/views/VariablesView.vue'), meta: { title: '变量', icon: 'Coin' } },
      { path: 'tasks', name: 'tasks', component: () => import('@/views/TasksView.vue'), meta: { title: '任务', icon: 'Calendar' } },
      { path: 'runs', name: 'runs', component: () => import('@/views/RunsView.vue'), meta: { title: '执行记录', icon: 'Histogram' } },
      { path: 'runs/:id', name: 'run-detail', component: () => import('@/views/RunDetailView.vue'), meta: { title: '执行详情', hidden: true } },
      { path: 'jenkins', name: 'jenkins', component: () => import('@/views/JenkinsView.vue'), meta: { title: 'Jenkins', icon: 'Cpu' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export { routes }

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.name !== 'login' && !auth.token) return { name: 'login' }
  if (to.name === 'login' && auth.token) return { name: 'dashboard' }
})

export default router
