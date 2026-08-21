# AGENTS.md — AutoTest Platform 项目上下文

> 本文件是项目的「地图」,供 AI 助手或新成员快速理解全貌。修改代码前先读这里。

---

## 1. 项目概述

**AutoTest Platform** 是一个以 Python 为基础的自动化测试运维平台,集成接口自动化、UI 自动化、OpenAPI 文档解析、可视化用例编排、Jenkins 调度于一体。

**核心能力**:
- 接口自动化:pytest + requests
- UI 自动化:pytest + Playwright
- OpenAPI/Swagger 文档自动解析为 Action Word(AW)
- AW 拖拽编排用例(前置/测试/后置三段)
- 变量管理(全局 `$${}` / 局部 `${}` 引用,支持加密、动态变量、目录树)
- 版本与迭代管理
- Jenkins REST API 触发执行 + 结果回传
- Web 管理后台(Django + Vue3)

---

## 2. 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 测试框架 | pytest | >=8.0 |
| 接口库 | requests | >=2.31 |
| UI 自动化 | Playwright | >=1.40 |
| 后端框架 | Django + DRF | 4.2 / 3.15 |
| 鉴权 | djangorestframework-simplejwt | >=5.3 |
| 数据库 | PostgreSQL | 16 |
| 前端框架 | Vue3 + TypeScript | 3.4 |
| UI 组件 | Element Plus | 2.7 |
| 拖拽 | vuedraggable | 4.1 |
| 代码编辑器 | Monaco Editor | 0.47 |
| API 文档 | drf-spectacular | 0.27 |
| 加密 | cryptography (Fernet) | 42.0 |
| 调度 | Jenkins REST API | — |
| 部署 | Docker Compose | — |

---

## 3. 目录结构

```
autotest_framework/
│
├── api/                        # pytest 接口用例(可执行脚本)
│   └── test_example.py
│
├── ui/                         # pytest UI 用例 + page objects
│   ├── pages/login_page.py
│   └── test_login.py
│
├── common/                     # 测试公共库(被 pytest 用例引用)
│   ├── config.py               # pydantic-settings,环境变量注入
│   ├── http_client.py          # requests.Session 封装
│   └── logger.py
│
├── data/openapi/               # OpenAPI/Swagger 源文件
│   └── example.yaml
│
├── scripts/                    # 工具脚本
│   └── gen_api.py              # openapi-python-client 生成 SDK
│
├── conftest.py                 # pytest 根 fixtures(http client)
├── pyproject.toml              # 测试依赖 + pytest 配置
├── Jenkinsfile                 # 测试 pipeline(SUITE/API_BASE_URL 等参数)
│
├── backend/                    # === Django 后端 ===
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── initadmin.py            # 创建超级用户脚本
│   ├── .env.example
│   │
│   ├── autotest_platform/      # Django 项目配置
│   │   ├── settings.py         # INSTALLED_APPS / DB / REST_FRAMEWORK / 业务配置
│   │   ├── urls.py             # API 路由总入口
│   │   └── wsgi.py
│   │
│   └── apps/                   # 业务 app(每个一个领域)
│       ├── projects/           # 项目 + 模块树
│       ├── releases/           # 版本 + 迭代
│       ├── requirements/       # 需求
│       ├── testcases/          # 用例 + 步骤 + 代码生成
│       ├── actionwords/        # AW 动作字 + OpenAPI 解析 + 渲染器
│       ├── scripts/            # 脚本管理(磁盘同步)
│       ├── variables/          # 变量 + 目录树 + 加密 + 动态
│       ├── tasks/              # 任务 + 执行记录 + Jenkins 触发
│       ├── results/            # 测试结果 + 仪表盘
│       └── jenkins_client/     # Jenkins REST 封装 + job XML 模板
│
├── frontend/                   # === Vue3 前端 ===
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   ├── nginx.conf
│   │
│   └── src/
│       ├── main.ts             # 入口(Element Plus + 图标注册)
│       ├── App.vue
│       ├── env.d.ts
│       │
│       ├── api/                # axios 客户端
│       │   ├── http.ts         # 拦截器(JWT 注入 + 401 跳登录)
│       │   ├── auth.ts         # 登录/刷新 token
│       │   └── index.ts        # 所有 API + TypeScript 接口定义
│       │
│       ├── router/index.ts     # 路由(15 个路由)
│       ├── stores/auth.ts      # Pinia auth store
│       ├── styles/main.css     # 全局样式
│       │
│       ├── layouts/
│       │   └── MainLayout.vue  # 侧边栏 + 顶栏布局
│       │
│       └── views/              # 页面(16 个 .vue)
│           ├── LoginView.vue
│           ├── DashboardView.vue
│           ├── ProjectsView.vue
│           ├── VersionsView.vue
│           ├── IterationsView.vue
│           ├── RequirementsView.vue
│           ├── CasesView.vue
│           ├── CaseComposerView.vue     # 三栏拖拽编排(核心)
│           ├── ActionWordsView.vue
│           ├── ScriptsView.vue
│           ├── ScriptEditorView.vue     # Monaco 编辑器
│           ├── VariablesView.vue
│           ├── TasksView.vue
│           ├── RunsView.vue
│           ├── RunDetailView.vue
│           ├── JenkinsView.vue
│           └── components/
│               └── SectionBlock.vue     # 拖拽区段子组件
│
├── docker-compose.yml          # db + backend + frontend
├── dev.bat / dev.sh            # 一键启动(Windows/Linux)
├── DEPLOY.md                   # 部署文档(小白版)
├── README.md                   # 项目说明
└── AGENTS.md                   # 本文件
```

---

## 4. 数据模型

### 4.1 关系图

```
Project ──┬── Module (树形)
          ├── Version ── Iteration
          ├── Requirement
          ├── TestCase ──┬── TestCaseStep ── ActionWord
          │               ├── Requirement (M2M)
          │               ├── Version (FK)
          │               └── Iteration (FK)
          ├── Script (TestCase 可选关联)
          ├── Variable ── VariableCategory (树形)
          ├── Environment
          ├── ActionWord
          └── TestTask ── TaskRun ── TestResult / RunSummary
```

### 4.2 模型清单

| App | 模型 | 关键字段 | 说明 |
|-----|------|---------|------|
| projects | `Project` | name, key, repo_url, repo_branch | 项目 |
| projects | `Module` | project, parent(自引用), name, path | 模块树 |
| releases | `Version` | project, name, status(open/locked/archived), release_date, is_baseline | 产品版本 |
| releases | `Iteration` | project, version, name, status(planning/active/closed), start_date, end_date | 迭代/Sprint |
| requirements | `Requirement` | project, title, ext_key, ext_url, source | 需求 |
| testcases | `TestCase` | project, module, version, iteration, title, case_id, type(api/ui), priority, status, tags | 用例 |
| testcases | `TestCaseStep` | test_case, action_word, section(setup/test/teardown), order, params(JSON), enabled, comment | 用例步骤 |
| actionwords | `ActionWord` | project, name, key, category, source(openapi/manual), endpoint, method, code_template, parameters(JSON) | 动作字 |
| scripts | `Script` | project, test_case, name, file_path, type, content, last_synced_at | 脚本文件 |
| variables | `Variable` | scope(global/project/env), project, environment, category, key, value, type, is_secret, is_encrypted, is_dynamic, dynamic_expr | 变量 |
| variables | `VariableCategory` | project, parent(自引用), name, path | 变量目录树 |
| variables | `Environment` | name, api_base_url, ui_base_url | 环境 |
| tasks | `TestTask` | project, environment, cases(M2M), trigger(manual/cron/webhook), cron_expr, status, jenkins_job_name, owner | 测试任务 |
| tasks | `TaskRun` | task, jenkins_job_name, jenkins_queue_id, jenkins_build_number, jenkins_build_url, status, params(JSON) | 执行记录 |
| results | `TestResult` | run, test_case, nodeid, result(passed/failed/skipped/error), duration_ms, error_message, traceback | 用例结果 |
| results | `RunSummary` | run, total, passed, failed, skipped, error, pass_rate | 汇总 |

---

## 5. API 端点

所有 API 前缀 `/api`,JWT 鉴权(除 login)。

### 认证
| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | JWT 登录,返 access + refresh |
| `/api/auth/refresh` | POST | 刷新 token |

### 项目与模块
| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/projects/projects` | CRUD | 项目 |
| `/api/projects/modules` | CRUD | 模块树 |

### 版本与迭代
| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/releases/versions` | CRUD | 版本 |
| `/api/releases/iterations` | CRUD | 迭代 |

### 需求
| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/requirements/` | CRUD | 需求 |

### 用例与步骤
| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/testcases/cases` | CRUD | 用例(支持 filter: project/module/type/status/version/iteration) |
| `/api/testcases/cases/{id}/steps` | GET/PUT | 获取/整体保存步骤序列 |
| `/api/testcases/cases/{id}/generate_script` | POST | 生成 pytest 脚本(可写盘+入库) |
| `/api/testcases/steps` | CRUD | 单步骤 |

### Action Word
| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/actionwords/` | CRUD | AW 库 |
| `/api/actionwords/parse/` | POST | 从 OpenAPI 解析生成 AW |
| `/api/actionwords/{id}/render/` | POST | 渲染单 AW 为代码 |

### 脚本
| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/scripts/` | CRUD | 脚本管理 |
| `/api/scripts/{id}/content` | GET/PUT | 读/写脚本内容(同步落盘) |
| `/api/scripts/sync-from-disk/` | POST | 从仓库扫描 .py 入库 |

### 变量
| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/variables/` | CRUD | 变量 |
| `/api/variables/{id}/reveal/` | POST | 查看加密/保护变量真实值 |
| `/api/variables/test-dynamic/` | POST | 测试动态表达式 |
| `/api/variables/categories` | CRUD | 变量目录树 |
| `/api/variables/envs` | CRUD | 环境 |

### 任务与执行
| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/tasks/tasks` | CRUD | 测试任务 |
| `/api/tasks/tasks/{id}/trigger` | POST | 触发执行(调 Jenkins) |
| `/api/tasks/tasks/{id}/runs` | GET | 任务执行历史 |
| `/api/tasks/runs` | GET | 执行记录列表 |
| `/api/tasks/runs/{id}/refresh` | POST | 从 Jenkins 拉最新状态 |
| `/api/results/ingest` | POST | Jenkins 回传 junit XML,写 TestResult + RunSummary |

### 结果与仪表盘
| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/results/items` | GET | 用例级结果 |
| `/api/results/summaries` | GET | 汇总 |
| `/api/results/summaries/dashboard` | GET | 仪表盘聚合 |

### Jenkins
| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/jenkins/jobs` | POST | 创建/更新 Pipeline job |
| `/api/jenkins/jobs/{name}` | GET | 查询 job 信息 |
| `/api/jenkins/builds/trigger` | POST | 触发 build |
| `/api/jenkins/builds/status` | GET | 查询 build 状态 |

### API 文档
| 路径 | 说明 |
|------|------|
| `/api/docs` | Swagger UI |
| `/api/schema` | OpenAPI schema |

---

## 6. 前端页面

| 路由 | 组件 | 功能 |
|------|------|------|
| `/login` | LoginView | 登录 |
| `/dashboard` | DashboardView | 仪表盘(统计 + 近期执行) |
| `/projects` | ProjectsView | 项目管理 |
| `/versions` | VersionsView | 版本管理(锁定/基线) |
| `/iterations` | IterationsView | 迭代管理(状态流转) |
| `/requirements` | RequirementsView | 需求管理 |
| `/cases` | CasesView | 用例列表(按版本/迭代筛选) |
| `/compose` | CaseComposerView | **三栏拖拽编排**(用例树/画板/AW库) |
| `/actionwords` | ActionWordsView | AW 库管理(OpenAPI 解析) |
| `/scripts` | ScriptsView | 脚本列表(磁盘同步) |
| `/scripts/:id` | ScriptEditorView | Monaco 脚本编辑器 |
| `/variables` | VariablesView | 变量管理(左目录树+右变量表) |
| `/tasks` | TasksView | 任务管理(触发执行) |
| `/runs` | RunsView | 执行记录(批量刷新状态) |
| `/runs/:id` | RunDetailView | 执行详情(结果明细) |
| `/jenkins` | JenkinsView | Jenkins 集成(创建 job) |

---

## 7. 核心业务流

### 7.1 OpenAPI → AW → 用例 → 脚本

```
1. OpenAPI YAML 放入 data/openapi/
2. AW 库页「从 OpenAPI 解析」→ 每个 endpoint 生成一个 AW
   - AW 含 code_template + parameters schema
3. 用例编排页(/compose):
   - 左:选项目 → 用例树(按版本/迭代过滤)
   - 右:AW 库(按分类分组)
   - 中:三段画板(前置/测试/后置),从右拖入
   - 选中步骤 → 填参数(可引用 $${全局}/${局部} 变量)
   - 实时预览渲染代码 + 整用例代码
4. 「保存并生成脚本」→ 后端 codegen 渲染完整 pytest 函数
   - 函数顶部注入全局变量初始化
   - 按 setup → test → teardown 顺序拼装
   - 可选写盘到 api/test_xxx.py + 入库为 Script
```

### 7.2 变量引用

| 语法 | 含义 | 渲染 |
|------|------|------|
| `$${name}` | 全局变量 | Python 变量 `name`,函数顶部注入 |
| `${name}` | 局部变量 | Python 变量 `name`(前序步骤赋值) |
| `prefix-$${ts}` | 混合 | `f"prefix-{ts}"` (f-string) |
| `{"k":"${v}"}` | JSON 内嵌 | `{"k": v}` (Python dict) |

变量属性:`is_secret`(保护) / `is_encrypted`(Fernet 加密) / `is_dynamic`(运行时 eval)

### 7.3 触发执行

```
1. 任务页点「执行」
2. 后端 TestTaskViewSet.trigger:
   - 按 cases 推断 SUITE 参数(api/ui/all)
   - 注入环境 base_url
   - 调 JenkinsClient.trigger_build → 返回 queue_id
   - 轮询 queue → 拿 build_number → 写 TaskRun
3. Jenkins pipeline 跑 pytest --junitxml=target/junit-report.xml
4. Jenkins 「Report to Platform」stage 把 junit XML POST 到 /api/results/ingest
   - 后端 junit_parser 解析 XML → 写 TestResult(nodeid/result/traceback)
   - 调 RunSummary.recompute() 重算汇总
   - 失败结果同步回写 TaskRun.status = failed
5. 前端 RunsView 页轮询 /refresh
   - 后端调 Jenkins get_build_info 拉整体状态
6. 结果页查看 TestResult 列表 + 失败用例 traceback 弹窗
```

### 7.4 定时执行

```
1. 任务表设 trigger=cron,填 cron_expr(如 0 2 * * *)
2. 系统 cron 每分钟跑:
   python manage.py trigger_scheduled_tasks
3. 命令扫描 status=active 的 cron 任务
   - 简化 cron 匹配(支持 * / 数字 / 逗号 / ranges,不支持 */N)
   - 防重:同任务 90 秒内不重复触发
   - 命中即调 JenkinsClient.trigger_build
4. 配 cron 示例(Linux crontab):
   * * * * * cd /path/to/backend && .venv/bin/python manage.py trigger_scheduled_tasks >> /var/log/autotest_cron.log 2>&1
```

### 7.5 数据隔离

测试脚本执行时,造的数据与被测系统数据隔离,三层机制:

| 层 | 机制 | 说明 |
|----|------|------|
| 账号/家庭 | 专用测试账号 + 测试家庭 | 平台变量页配 `test_email` / `test_password`,不要用生产账号 |
| 用例数据 | `cleanup` fixture LIFO 清理栈 | 用例造的资源注册到 cleanup,用例结束(无论成功/失败)自动倒序删除 |
| 并行/重跑 | `test_prefix` 唯一前缀 | 每次执行生成 UUID 前 8 位,造数据时带上避免冲突 |

**conftest.py 三个 fixture**:

```python
def test_xxx(http, cleanup, test_prefix):
    # 造数据 + 注册清理
    resp = http.request("POST", "/blog", json={"title": f"[{test_prefix}] hi"})
    blog_id = resp.json()["data"]["id"]
    cleanup.append(("DELETE", f"/blog/{blog_id}"))
    # 或用 track helper(自动从响应提取路径变量)
    track(http, cleanup, resp, "DELETE", "/blog/{data.id}")

    # 测试断言(失败也会触发 cleanup)
    resp = http.request("GET", f"/blog/{blog_id}")
    assert resp.status_code == 200
```

**codegen 自动注入**:
- 函数签名:有 setup/test 步骤时自动加 `cleanup, test_prefix` 参数
- try/finally 包裹:setup+test 在 try,teardown 在 finally,保证失败也执行
- 生成代码顶部加注释提示数据隔离用法

**track helper 路径模板**:
- `{data.id}` → `resp.json()["data"]["id"]`
- `{data.blog.id}` → 嵌套取值
- `{data.items.0.id}` → 数组下标

**测试账号约定**(在平台变量页配置):
- `test_email` / `test_password`:专用测试账号
- `test_family_name`:专用测试家庭
- `captcha_code`:开发环境固定验证码(ihomy 是 `qwer`)
- 不要在测试脚本里硬编码生产账号密码

---

## 8. 关键文件索引

### 后端

| 文件 | 作用 |
|------|------|
| `backend/autotest_platform/settings.py` | Django 配置(DB/JWT/CORS/业务参数) |
| `backend/autotest_platform/urls.py` | API 路由总入口 |
| `backend/apps/actionwords/parser.py` | OpenAPI → AW 解析器 |
| `backend/apps/actionwords/renderer.py` | AW 模板渲染 + `$${}` / `${}` 解析 |
| `backend/apps/testcases/codegen.py` | 用例步骤 → 完整 pytest 函数 |
| `backend/apps/testcases/views.py` | steps endpoint + generate_script endpoint |
| `backend/apps/variables/crypto.py` | Fernet 加密 + 动态变量 eval |
| `backend/apps/jenkins_client/client.py` | Jenkins REST API 封装 |
| `backend/apps/jenkins_client/job_template.xml` | Pipeline job XML 模板 |
| `backend/apps/tasks/views.py` | trigger + refresh endpoint |
| `backend/apps/tasks/management/commands/trigger_scheduled_tasks.py` | cron 定时调度命令 |
| `backend/apps/results/junit_parser.py` | junit XML 解析 → TestResult + RunSummary |

### 前端

| 文件 | 作用 |
|------|------|
| `frontend/src/api/index.ts` | 所有 API + TypeScript 接口定义 |
| `frontend/src/api/http.ts` | axios 拦截器(JWT + 401) |
| `frontend/src/router/index.ts` | 路由表(15 路由) |
| `frontend/src/views/CaseComposerView.vue` | **三栏拖拽编排页**(核心) |
| `frontend/src/views/components/SectionBlock.vue` | 拖拽区段子组件 |
| `frontend/src/views/VariablesView.vue` | 变量管理(目录树+变量表) |
| `frontend/src/views/ScriptEditorView.vue` | Monaco 脚本编辑器 |

### 测试

| 文件 | 作用 |
|------|------|
| `conftest.py` | pytest 根 fixtures(http client + cleanup + test_prefix) |
| `common/config.py` | pydantic-settings 配置 |
| `common/http_client.py` | requests.Session 封装 |
| `api/test_example.py` | 接口用例示例 |
| `ui/test_login.py` | UI 用例示例 |
| `pyproject.toml` | pytest 配置 + markers(api/ui) |
| `Jenkinsfile` | 测试 pipeline |

---

## 9. 配置

### 后端环境变量 (`backend/.env`)

```
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=1
DB_NAME=autotest
DB_USER=autotest_user
DB_PASSWORD=autotest_pass
DB_HOST=127.0.0.1
DB_PORT=5432
JENKINS_URL=http://127.0.0.1:8080
JENKINS_USER=admin
JENKINS_TOKEN=...
CORS_ORIGINS=http://localhost:5173
```

### 前端环境变量

```
VITE_API_BASE=http://127.0.0.1:8000  # vite.config.ts proxy 目标
```

### 测试配置 (`pyproject.toml`)

```
markers = ["api", "ui"]
testpaths = ["api", "ui"]
```

---

## 10. 开发命令

### 启动

```bash
# 一键启动(Windows)
dev.bat

# 一键启动(Linux)
./dev.sh

# 手动启动后端
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000

# 手动启动前端
cd frontend
npm install
npm run dev
```

### 验证

```bash
# 后端语法检查
python -m compileall -q backend

# API 文档
# 浏览器打开 http://127.0.0.1:8000/api/docs

# 前端
# 浏览器打开 http://localhost:5173

# 测试
pytest                          # 全跑
pytest -m api                   # 只接口
pytest -m ui                    # 只 UI
```

### Docker 部署

```bash
docker compose up -d --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

---

## 11. 端口清单

| 端口 | 服务 | 对外 |
|------|------|------|
| 5432 | PostgreSQL | 否 |
| 8000 | Django 后端 | 开发期可 |
| 5173 | Vue3 前端(开发) | 否 |
| 80 | Vue3 前端(生产 nginx) | 是 |
| 8080 | Jenkins | 是 |

---

## 12. 编码约定

### 后端
- 每个 app 一个领域,标准 DRF ModelViewSet
- 业务动作用 `@action(detail=...)`
- 模型继承 `TimestampedModel`(created_at / updated_at)
- 环境变量走 `os.getenv`,配置集中在 `settings.py` 末尾
- 不引第三方 Jenkins SDK,裸 `requests` 调 REST
- AW 模板用 `{{ var }}` 占位,变量引用用 `$${}` / `${}`

### 前端
- `<script setup lang="ts">` 组合式 API
- API 全部在 `src/api/index.ts` 统一定义
- 页面在 `src/views/`,子组件在 `src/views/components/`
- 路由 meta 带 `title` + `icon` 用于侧边栏
- Element Plus 全量注册(main.ts)
- 拖拽用 vuedraggable,`group: { name: 'aw', pull: 'clone', put: false }` 克隆模式

### 测试
- 用例标记 `@pytest.mark.api` 或 `@pytest.mark.ui`
- http fixture 在 `conftest.py` session 级
- 配置走 `common/config.py` 的 `AUTOTEST_` 前缀环境变量

---

## 13. 已知简化(ponytail)

- 不自研 runner:pytest 足够
- 不自研执行器:复用 Jenkins REST API
- 不引 Celery/Redis:定时用系统 cron + management command,前端轮询 `/refresh` 拉状态
- 不引 RBAC 框架:`IsAuthenticated` 够初期用
- 动态变量用受限 eval:只暴露 datetime/random/uuid/time
- AW 模板渲染用自研正则,不引 Jinja2
- 步骤参数无复杂类型表单:字符串输入 + JSON 解析
- cron 匹配用自研简化版,不支持 `*/N`,要完整换 `croniter`

---

## 14. 待办参考(可能的方向)

- RBAC 权限(django-guardian)
- Celery 异步轮询 Jenkins
- WebSocket 实时日志推送
- 测试数据工厂(YAML 驱动)
- 步骤级断言编辑器
- 用例版本快照与回滚
- Allure 报告深度集成
- 跨用例步骤复用(fixture 抽取)

---

## 15. 本机部署进展与代码修改记录(2026-08-17)

> 本节记录在 Windows 开发机上跑通「OpenAPI → AW → TestCase → codegen」链路时所做的修改和当前状态,与生产 Docker Compose 部署路径**正交**——下面所有改动都不影响 `docker compose up` 走 PostgreSQL 的原始路径。

### 15.1 数据库改用 SQLite(开发期)

**原因**:本机 Docker Hub 拉不动 `postgres:16-alpine` 镜像,为不阻塞验证链路,改用 SQLite 零依赖跑通。

**配置方式**:`backend/.env` 加一行
```
DB_ENGINE=django.db.backends.sqlite3
```
`settings.py` 已加兜底:`if "sqlite" in ENGINE: DATABASES = {NAME: BASE_DIR / "db.sqlite3"}`,否则走原 PostgreSQL 配置。**生产部署仍用 PostgreSQL**(docker-compose.yml 不变)。

**数据库文件**:`backend/db.sqlite3`(17 张表,含 django 默认 + 8 个业务 app)。

### 15.2 生成 8 个 app 的 initial migrations

原仓库 `apps/*/migrations/` 目录**全部缺失**(只有 `__init__.py` 没有 0001_initial)。本机跑 `makemigrations` 生成了以下 migration 文件(已入库,git 可见):

| App | Migration 文件 |
|-----|---------------|
| releases | `0001_initial.py` |
| requirements | `0001_initial.py` |
| scripts | `0001_initial.py` |
| variables | `0001_initial.py` |
| tasks | `0001_initial.py` + `0002_initial.py`(外键依赖拆分) |
| results | `0001_initial.py` + `0002_initial.py` |
| testcases | `0001_initial.py`(原本就有) |
| actionwords | `0001_initial.py`(原本就有) |
| projects | `0001_initial.py`(原本就有) |

### 15.3 修复的代码 bug(6 处)

| 文件:行 | 症状 | 修法 |
|---------|------|------|
| `autotest_platform/settings.py` | `SIMPLE_JWT["ACCESS_TOKEN_LIFETIME": timedelta(...)]` 在 import timedelta 之前使用 → NameError | 把 `from datetime import timedelta` 移到文件顶部 import 区 |
| `autotest_platform/settings.py` | DATABASES 不支持 SQLite 环境变量(只硬编码 PostgreSQL) | 加 `if "sqlite" in ENGINE` 分支用 `BASE_DIR / "db.sqlite3"` |
| `apps/testcases/serializers.py:28` | `requirements = PrimaryKeyRelatedField(many=True, queryset=None)` 新版 DRF 报错 | 改 `read_only=True` + `__init__` 里动态赋 `child_relation.queryset = Requirement.objects.all()` |
| `apps/tasks/serializers.py:7` | 同上 queryset=None 问题 | 改 `queryset=TestCase.objects.none()` + `__init__` 动态赋 |
| `apps/testcases/serializers.py:43` | `TestCaseStepWriteSerializer` 用 `fields="__all__"` 导致 `test_case` 外键必填,但 `PUT /cases/{id}/steps/` 端点 views 会手动赋值 → 400 "test_case 该字段是必填项" | 加 `read_only_fields = ("test_case",)` |
| `apps/testcases/views.py:69` | `code.splitlines()[3].split("(")[0].split()[-1]` 假设 codegen 输出至少 4 行,若不到 4 行 → IndexError | 改用循环找 `def ` 开头的行提取函数名,找不到 fallback 到 `case.case_id` |

### 15.4 ihomy 项目集成验证(链路全通)

被测系统:`ihomy` 后端 `http://localhost:8080/api`(Spring Boot,启动时设 `IHOMY_CONFIG_PATH`)。

**OpenAPI 导出**:从 ihomy 的 `/api/v3/api-docs` 抓取,保存到 `data/openapi/ihomy.json`(84KB / 130 path / 159 operation)。

**链路验证步骤**:
1. 建超管 `admin/admin`(SQLite)
2. `POST /api/auth/login` 拿 JWT
3. `POST /api/projects/projects/` 建 Project(`key=IHOMY`, id=1)
4. `POST /api/actionwords/parse/` 传 ihomy.json → 生成 **159 个 ActionWord**(每个 endpoint 一个)
5. `POST /api/testcases/cases/` 建 TestCase(`case_id=ihomy_login_verify`, priority=1, status=ready, id=1)
6. `PUT /api/testcases/cases/1/steps/` 加 2 步骤(POST /auth/login + GET /auth/me)
7. `POST /api/testcases/cases/1/generate_script/` → 渲染出 529 字节 pytest 脚本

**生成的脚本示例**(codegen 输出):
```python
import pytest
pytestmark = [pytest.mark.api]

def test_ihomy_login_verify(http, cleanup, test_prefix):
    # === 数据隔离 ===
    # 造数据后调 cleanup.append(("DELETE", path)) ...
    # === 测试步骤 ===
    # step 1: 登录
    resp = http.request("POST", "/auth/login", json=body)
    assert resp.status_code in (200, 201, 204)
    # step 2: 获取当前用户
    resp = http.request("GET", "/auth/me")
    assert resp.status_code in (200, 201, 204)
```

### 15.5 ihomy 测试套件现状(37 passed)

在 `autotest_framework/` 根目录跑 pytest(走 `conftest.py` + `common/config.py` + `.env`):

| 文件 | 用例数 | 覆盖 |
|------|--------|------|
| `api/test_ihomy.py` | 12 | 核心流(登录/博客/相册/积分/通知/家庭) |
| `api/test_roles.py` | 12 | OPS 登录/运维接口/角色隔离/未登录拦截 |
| `api/test_family_isolation.py` | 5 | 注册临时家庭验证跨家庭 404 |
| `api/test_chat_ws.py` | 8 | WebSocket 握手/广播/落库/跨家庭隔离 |
| `ui/test_login.py` | 0 (skip) | 待装 playwright |

**总计 37 passed, 1 skipped**,耗时 ~6.4s。Allure 报告 `target/allure-results/`,查看用 `allure serve target/allure-results`(端口 3225)。

### 15.6 关键配置文件

| 文件 | 作用 |
|------|------|
| `backend/.env` | `DB_ENGINE=django.db.backends.sqlite3`(开发期) |
| `backend/db.sqlite3` | SQLite 数据库(17 表,含 1 Project + 159 AW + 1 TestCase) |
| `data/openapi/ihomy.json` | ihomy OpenAPI spec(从 `/api/v3/api-docs` 导出) |
| `conftest.py` | 全局 fixtures(http_base/auth_factory/auth/http/second_family_auth) |
| `common/config.py` | Settings(api_base_url/api_email/api_password/captcha_code) |
| `common/http_client.py` | HttpClient(token + traceId 日志) |
| `common/ws_client.py` | WsClient(独立事件循环,适配 websockets 17 API) |
| `.env`(根) | `AUTOTEST_API_BASE_URL=http://localhost:8080/api` 等 |

### 15.7 本机启动命令(SQLite 模式)

```powershell
# 后端(端口 8000)
cd C:\Users\chill\OneDrive\WorkStation\Projects\autotest_framework\backend
$env:DB_ENGINE = "django.db.backends.sqlite3"
$env:DJANGO_DEBUG = "1"
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
# 访问 http://localhost:8000/api/ (admin/admin)

# 测试(在根目录)
cd C:\Users\chill\OneDrive\WorkStation\Projects\autotest_framework
.venv\Scripts\python.exe -m pytest --alluredir target/allure-results
```

**注意**:`--noreload` 必加,否则改代码后 server 重启会丢失 `DB_ENGINE` 环境变量(走默认 PostgreSQL 连不上)。改完代码手动重启 server。

### 15.8 各组件启动状态

| 项 | 状态 | 端口 | 说明 |
|----|------|------|------|
| 前端 Vue3 Web UI | **已启动** | 5173 | `npm run dev`(vite 5.4.21),所有页面编译 200,代理 `/api` → 8000;登录 admin/admin |
| 后端 Django | **已启动** | 8000 | SQLite 模式,`--noreload`(改代码手动重启) |
| ihomy 后端 | **已启动** | 8080 | 被测系统,Spring Boot |
| Jenkins 集成 | **链路已验证**(未装 Jenkins) | — | 用脚本模拟 Jenkinsfile 行为:跑 pytest → POST `/api/results/ingest` → TestResult+RunSummary 写入成功。装真 Jenkins 只差服务安装+credentials 配置 |
| UI 自动化 | **已打通**(1 条登录用例) | — | playwright 1.62 + chromium 已装;`ui/test_login.py` 真实登录通过(admin/admin → /dashboard);后续按模式补页面对象 |
| Docker Compose | 未用 | — | 生产部署走原 PostgreSQL 路径,不影响 |
| PostgreSQL | 未装 | — | 本机 Docker Hub 拉不动镜像,开发期 SQLite 替代 |

**前端启动命令**:
```powershell
cd C:\Users\chill\OneDrive\WorkStation\Projects\autotest_framework\frontend
Start-Process -FilePath "cmd.exe" -ArgumentList "/c","npm run dev > C:\Users\chill\AppData\Local\Temp\opencode\vite_out.log 2>&1" -WindowStyle Hidden
# 等待 ~8 秒,访问 http://localhost:5173/
```

**已验证的前端页面编译**(vite dev 实时编译,均 200):
- LoginView / DashboardView / ProjectsView / CasesView
- CaseComposerView(三栏拖拽编排核心页,107KB)
- ActionWordsView(AW 库管理,51KB)
- ScriptsView / VariablesView / TasksView / RunsView / JenkinsView 等

**API 代理验证**:`POST http://localhost:5173/api/auth/login`(无尾斜杠)→ 200,JWT 正常返回。

### 15.9 下一步优先级

1. ~~启动前端 Web UI~~ ✅ 已完成(vite 5173,所有页面编译 200)
2. ~~Jenkins 回传链路验证~~ ✅ 已完成(模拟 Jenkinsfile:pytest→junit→ingest→TestResult+RunSummary,37 passed 入库)
3. ~~UI 自动化打通~~ ✅ 已完成(playwright + chromium,`ui/test_login.py` 真实登录通过;**38 passed** = 37 API/WS + 1 UI)
4. **UI 自动化扩展** 补更多页面对象(项目/用例/AW 库/编排页等),按 `ui/pages/login_page.py` 模式复制
5. 修复 ihomy `buildTokens` isOps bug(改 SQL 一行,见 ihomy `docs/业务逻辑待优化清单.md` #15)
6. 装真 Jenkins 服务(可选,链路已验证,只差服务安装 + credentials 配置 `autotest-platform`)

### 15.10 UI 自动化记录(2026-08-17 追加)

**环境**:`playwright 1.62.0` + `pytest-playwright 0.9.0` 已装;chromium + chromium-headless-shell + ffmpeg 下载到 `%USERPROFILE%\AppData\Local\ms-playwright`(191.8 MiB,注意 `playwright install chromium` 只装完整版,headless 测试还需 `playwright install chromium-headless-shell`)。

**UI 测试链路**:`page` fixture 由 pytest-playwright 插件提供(conftest 无需手动定义);`ui/pages/login_page.py` POM 用 Element Plus 选择器(`input[placeholder="admin"]` / `input[type="password"]` / `button:has-text("登录")`);`ui/test_login.py` 登录 admin/admin → 断言跳转 /dashboard。

**踩坑:前端 3 个代码 bug(登录被阻塞,已修复)**:

| 文件 | bug | 修法 |
|------|-----|------|
| `frontend/src/router/index.ts` | 只 `export default router`,MainLayout.vue:50 `import { routes }` 报 "does not provide an export named 'routes'" | 加 `export { routes }` |
| `frontend/src/views/DashboardView.vue:14` | `<el-card>` 第 14 行误写 `</el-col>` 闭合,标签不匹配 → vite "Element is missing end tag" 编译失败 | 改回 `</el-card>` |
| `frontend/src/api/index.ts:135` | `varApi` 声明两次(121 和 135),esbuild "Multiple exports with the same name" | 删掉 121 的重复定义,保留 135 的更完整版本(含 reveal/testDynamic) |

**调试方法**:playwright `page.on("response")` + `page.on("console")` 监听网络/控制台,定位 vite 模块加载失败;vite 编译错误看 `vite_out.log` 的 "Internal server error" 行。
