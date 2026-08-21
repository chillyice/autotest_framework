import http from './http'

export interface Project { id: number; name: string; key: string; description?: string; repo_url?: string; repo_branch?: string; is_active: boolean }
export interface Module { id: number; project: number; parent?: number; name: string; path?: string; children_count?: number }
export interface TestCase {
  id: number
  project: number
  module?: number
  title: string
  case_id: string
  type: 'api'|'ui'
  priority: number
  status: string
  tags?: string
  precondition?: string
  expected?: string
  requirements?: number[]
  version?: number
  iteration?: number
}
export interface TestCaseStep { id?: number; test_case?: number; action_word: number; section: 'setup'|'test'|'teardown'; order: number; name?: string; params?: Record<string, unknown>; enabled?: boolean; comment?: string; action_word_detail?: ActionWord; rendered_code?: string }
export interface ActionWord { id: number; project: number; name: string; key: string; category?: string; description?: string; source: 'openapi'|'manual'; suggested_section: 'any'|'setup'|'test'|'teardown'; endpoint?: string; method?: string; code_template?: string; parameters?: { type?: string; properties?: Record<string, any>; required?: string[] } }
export interface Requirement { id: number; project: number; title: string; ext_key?: string; ext_url?: string; source?: string; description?: string; status?: string; cases_count?: number }
export interface Script { id: number; project: number; name: string; file_path: string; type: 'api'|'ui'; content?: string; last_synced_at?: string }
export interface Variable {
  id: number
  scope: 'global'|'project'|'env'
  project?: number
  environment?: number
  category?: number
  key: string
  value: string
  type: 'string'|'int'|'bool'|'json'
  description?: string
  is_secret: boolean
  is_encrypted: boolean
  is_dynamic: boolean
  dynamic_expr?: string
}
export interface VariableCategory {
  id: number
  project?: number
  parent?: number
  name: string
  path?: string
  children_count?: number
  variables_count?: number
}
export interface Environment { id: number; name: string; api_base_url: string; ui_base_url?: string; description?: string }
export interface Version { id: number; project: number; name: string; description?: string; status: 'open'|'locked'|'archived'; release_date?: string; is_baseline?: boolean; iterations_count?: number }
export interface Iteration { id: number; project: number; version?: number; version_name?: string; name: string; description?: string; status: 'planning'|'active'|'closed'; start_date?: string; end_date?: string; cases_count?: number }
export interface TestTask { id: number; name: string; project: number; environment?: number; cases: number[]; trigger: 'manual'|'cron'|'webhook'; cron_expr?: string; status: string; jenkins_job_name?: string; owner?: number; description?: string; case_count?: number; last_run_status?: string }
export interface TaskRun { id: number; task: number; task_name?: string; jenkins_job_name?: string; jenkins_build_number?: number; jenkins_build_url?: string; status: string; triggered_by?: number; started_at?: string; finished_at?: string; duration_ms?: number; params?: Record<string, unknown>; error_message?: string }
export interface TestResult { id: number; run: number; nodeid: string; title?: string; result: 'passed'|'failed'|'skipped'|'error'; duration_ms: number; error_message?: string; traceback?: string; allure_url?: string }
export interface Dashboard { total_runs: number; last_7d_runs: number; pass_rate_avg: number; by_status: Record<string, number> }

const list = <T>(url: string) => (params?: Record<string, unknown>) => http.get<T>(url, { params }).then(r => r.data)

export const projectApi = {
  list: list<{ results: Project[]; count: number }>('/projects/projects'),
  create: (p: Partial<Project>) => http.post<Project>('/projects/projects', p).then(r => r.data),
  update: (id: number, p: Partial<Project>) => http.patch<Project>(`/projects/projects/${id}`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/projects/projects/${id}`),
}

export const moduleApi = {
  list: list<{ results: Module[]; count: number }>('/projects/modules'),
  create: (p: Partial<Module>) => http.post<Module>('/projects/modules', p).then(r => r.data),
  update: (id: number, p: Partial<Module>) => http.patch<Module>(`/projects/modules/${id}`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/projects/modules/${id}`),
}

export const caseApi = {
  list: list<{ results: TestCase[]; count: number }>('/testcases/cases'),
  get: (id: number) => http.get<TestCase>(`/testcases/cases/${id}/`).then(r => r.data),
  create: (p: Partial<TestCase>) => http.post<TestCase>('/testcases/cases', p).then(r => r.data),
  update: (id: number, p: Partial<TestCase>) => http.patch<TestCase>(`/testcases/cases/${id}/`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/testcases/cases/${id}/`),
  getSteps: (id: number) => http.get<TestCaseStep[]>(`/testcases/cases/${id}/steps`).then(r => r.data),
  saveSteps: (id: number, steps: Partial<TestCaseStep>[]) => http.put<TestCaseStep[]>(`/testcases/cases/${id}/steps`, { steps }).then(r => r.data),
  generateScript: (id: number, opts?: { file_path?: string; save_script?: boolean }) => http.post<{ code: string; function_name?: string; script_id?: number; file_path?: string }>(`/testcases/cases/${id}/generate_script`, opts || {}).then(r => r.data),
}

export const stepApi = {
  list: list<{ results: TestCaseStep[]; count: number }>('/testcases/steps'),
  create: (p: Partial<TestCaseStep>) => http.post<TestCaseStep>('/testcases/steps', p).then(r => r.data),
  update: (id: number, p: Partial<TestCaseStep>) => http.patch<TestCaseStep>(`/testcases/steps/${id}/`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/testcases/steps/${id}/`),
}

export const awApi = {
  list: list<{ results: ActionWord[]; count: number }>('/actionwords/'),
  get: (id: number) => http.get<ActionWord>(`/actionwords/${id}/`).then(r => r.data),
  create: (p: Partial<ActionWord>) => http.post<ActionWord>('/actionwords/', p).then(r => r.data),
  update: (id: number, p: Partial<ActionWord>) => http.patch<ActionWord>(`/actionwords/${id}/`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/actionwords/${id}/`),
  parse: (p: { project: number; spec_path?: string; category?: string; overwrite?: boolean }) =>
    http.post<{ results: Array<{ created: number; updated: number; skipped: number; spec: string }> }>('/actionwords/parse', p).then(r => r.data),
  render: (id: number, params?: Record<string, unknown>) =>
    http.post<{ code: string; aw: ActionWord }>(`/actionwords/${id}/render`, { action_word: id, params }).then(r => r.data),
}

export const reqApi = {
  list: list<{ results: Requirement[]; count: number }>('/requirements/'),
  create: (p: Partial<Requirement>) => http.post<Requirement>('/requirements/', p).then(r => r.data),
  update: (id: number, p: Partial<Requirement>) => http.patch<Requirement>(`/requirements/${id}/`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/requirements/${id}/`),
}

export const scriptApi = {
  list: list<{ results: Script[]; count: number }>('/scripts/'),
  get: (id: number) => http.get<Script>(`/scripts/${id}/`).then(r => r.data),
  create: (p: Partial<Script>) => http.post<Script>('/scripts/', p).then(r => r.data),
  update: (id: number, p: Partial<Script>) => http.patch<Script>(`/scripts/${id}/`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/scripts/${id}/`),
  getContent: (id: number) => http.get<{ content: string }>(`/scripts/${id}/content`).then(r => r.data.content),
  saveContent: (id: number, content: string) => http.put(`/scripts/${id}/content`, { content }),
  syncFromDisk: () => http.post<{ scanned: number; updated: number; created: number }>('/scripts/sync-from-disk/').then(r => r.data),
}

export const envApi = {
  list: list<{ results: Environment[]; count: number }>('/variables/envs'),
  create: (p: Partial<Environment>) => http.post<Environment>('/variables/envs', p).then(r => r.data),
  update: (id: number, p: Partial<Environment>) => http.patch<Environment>(`/variables/envs/${id}/`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/variables/envs/${id}/`),
}

export const varApi = {
  list: list<{ results: Variable[]; count: number }>('/variables/'),
  create: (p: Partial<Variable>) => http.post<Variable>('/variables/', p).then(r => r.data),
  update: (id: number, p: Partial<Variable>) => http.patch<Variable>(`/variables/${id}/`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/variables/${id}/`),
  reveal: (id: number) => http.post<{ key: string; value: string }>(`/variables/${id}/reveal`).then(r => r.data),
  testDynamic: (expr: string) => http.post<{ expr: string; result: string }>('/variables/test-dynamic', { expr }).then(r => r.data),
}

export const categoryApi = {
  list: list<{ results: VariableCategory[]; count: number }>('/variables/categories'),
  create: (p: Partial<VariableCategory>) => http.post<VariableCategory>('/variables/categories', p).then(r => r.data),
  update: (id: number, p: Partial<VariableCategory>) => http.patch<VariableCategory>(`/variables/categories/${id}/`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/variables/categories/${id}/`),
}

export const versionApi = {
  list: list<{ results: Version[]; count: number }>('/releases/versions'),
  create: (p: Partial<Version>) => http.post<Version>('/releases/versions', p).then(r => r.data),
  update: (id: number, p: Partial<Version>) => http.patch<Version>(`/releases/versions/${id}/`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/releases/versions/${id}/`),
}

export const iterationApi = {
  list: list<{ results: Iteration[]; count: number }>('/releases/iterations'),
  create: (p: Partial<Iteration>) => http.post<Iteration>('/releases/iterations', p).then(r => r.data),
  update: (id: number, p: Partial<Iteration>) => http.patch<Iteration>(`/releases/iterations/${id}/`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/releases/iterations/${id}/`),
}

export const taskApi = {
  list: list<{ results: TestTask[]; count: number }>('/tasks/tasks'),
  create: (p: Partial<TestTask>) => http.post<TestTask>('/tasks/tasks', p).then(r => r.data),
  update: (id: number, p: Partial<TestTask>) => http.patch<TestTask>(`/tasks/tasks/${id}`, p).then(r => r.data),
  remove: (id: number) => http.delete(`/tasks/tasks/${id}`),
  trigger: (id: number, params?: Record<string, unknown>) => http.post<TaskRun>(`/tasks/tasks/${id}/trigger`, { params }).then(r => r.data),
  runs: (id: number) => http.get<TaskRun[]>(`/tasks/tasks/${id}/runs`).then(r => r.data),
}

export const runApi = {
  list: list<{ results: TaskRun[]; count: number }>('/tasks/runs'),
  refresh: (id: number) => http.post<TaskRun>(`/tasks/runs/${id}/refresh`).then(r => r.data),
}

export const resultApi = {
  list: list<{ results: TestResult[]; count: number }>('/results/items'),
  dashboard: () => http.get<Dashboard>('/results/summaries/dashboard').then(r => r.data),
}

export const jenkinsApi = {
  createJob: (p: { job_name: string; description?: string; suite?: 'all'|'api'|'ui'; repo_url: string; repo_branch?: string; api_base_url?: string; ui_base_url?: string; git_creds?: string }) =>
    http.post('/jenkins/jobs', p),
  jobInfo: (job_name: string) => http.get('/jenkins/jobs/' + encodeURIComponent(job_name)).then(r => r.data),
  trigger: (job_name: string, params?: Record<string, unknown>) =>
    http.post<{ queue_id: number; job_name: string }>('/jenkins/builds/trigger', { job_name, params }).then(r => r.data),
  buildStatus: (job_name: string, build_number: number) =>
    http.get<{ number: number; result: string; building: boolean; duration_ms: number; url: string }>('/jenkins/builds/status', { params: { job_name, build_number } }).then(r => r.data),
}
