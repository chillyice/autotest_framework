# AutoTest Platform

基于 Python 的自动化测试运维平台：接口自动化、UI 自动化、OpenAPI 自动生成 SDK、Jenkins 调度、Web 管理后台。

## 架构

```
┌────────────────┐    ┌─────────────────┐    ┌──────────────┐
│  Vue3 + EP UI  │ ←→ │  Django + DRF   │ ←→ │ PostgreSQL   │
└────────────────┘    └────────┬────────┘    └──────────────┘
                               │
                               ↓
                      ┌────────────────┐
                      │  Jenkins REST  │ ← Pipeline job → 仓库 Jenkinsfile → pytest
                      └────────────────┘
                               │
                               ↓
                      ┌────────────────┐
                      │  测试仓库      │  api/ ui/ common/ scripts/ Jenkinsfile
                      └────────────────┘
```

## 目录

```
autotest_framework/
├── api/                    # pytest 接口用例(已是可执行脚本)
├── ui/                     # pytest UI 用例 + page objects
├── common/                 # 测试公共库
├── data/openapi/           # Swagger/OpenAPI 源
├── scripts/gen_api.py      # openapi → python SDK
├── conftest.py
├── pyproject.toml
├── Jenkinsfile             # 测试 pipeline
│
├── backend/                # Django + DRF 平台后端
│   ├── autotest_platform/  # settings/urls/wsgi
│   ├── apps/
│   │   ├── projects/       # 项目 + 模块树
│   │   ├── testcases/      # 用例管理
│   │   ├── requirements/   # 需求关联
│   │   ├── scripts/        # 脚本管理 + 内容编辑 + 磁盘同步
│   │   ├── variables/      # 变量 + 环境
│   │   ├── tasks/          # 任务 + 执行记录 + 触发 Jenkins
│   │   ├── results/        # 用例结果 + 汇总 + 仪表盘
│   │   └── jenkins_client/ # Jenkins REST 封装 + job XML 模板
│   ├── requirements.txt
│   ├── Dockerfile
│   └── initadmin.py
│
├── frontend/               # Vue3 + Element Plus 前端
│   ├── src/
│   │   ├── api/            # axios + 接口封装
│   │   ├── layouts/
│   │   ├── router/
│   │   ├── stores/         # pinia
│   │   ├── styles/
│   │   └── views/          # 9 个核心页面
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── nginx.conf
│
├── docker-compose.yml
├── dev.sh / dev.bat        # 一键启动
└── README.md
```

## 快速启动

### 一键启动(开发)

Windows: 双击 `dev.bat`；Linux/Mac: `./dev.sh`

或手动：

```bash
# 1. 启动 PostgreSQL
docker compose up -d db

# 2. 后端
pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py shell < backend/initadmin.py   # 建 admin/admin
python backend/manage.py runserver                       # http://127.0.0.1:8000

# 3. 前端
cd frontend
npm install
npm run dev                                              # http://127.0.0.1:5173
```

登录：`admin` / `admin`

### 生产部署

```bash
docker compose up -d --build
# 后端 :8000 前端 :80
# 进入容器跑迁移 + 建超管
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py shell < /app/initadmin.py
```

## 数据模型一览

| 模型 | 说明 |
|------|------|
| `Project` / `Module` | 项目 + 树形模块 |
| `Version` / `Iteration` | 产品版本 + 迭代/Sprint |
| `Requirement` | 需求/故事,可关联 JIRA/禅道 |
| `TestCase` | 用例元数据,关联需求 + 模块 + 版本 + 迭代,有类型(api/ui)和优先级 |
| `Script` | 脚本文件元数据 + 内容快照,保存时同步写盘到测试仓库 |
| `Environment` / `Variable` / `VariableCategory` | 环境配置 + 多作用域变量 + 变量目录树 |
| `ActionWord` | AW 动作字,OpenAPI 解析或手动创建 |
| `TestCaseStep` | 用例步骤,关联 AW + 区段(setup/test/teardown) |
| `TestTask` | 任务:固定一组用例 + 环境 + Jenkins job 名 |
| `TaskRun` | 单次执行记录,关联 Jenkins build |
| `TestResult` / `RunSummary` | 用例级结果 + 汇总 |

## 业务流

1. **OpenAPI 生成 SDK**：`python scripts/gen_api.py` → 类型化 Python client 入 `api/`
2. **脚本编写**：Web 端 Monaco 编辑器改 `Script.content` → 同步落盘到测试仓库
3. **创建 Jenkins Job**：`Jenkins` 页填表 → 平台调 Jenkins REST API 创建 Pipeline job(引用仓库 `Jenkinsfile`)
4. **创建任务**：选项目 + 用例集 + 环境 + Jenkins job 名
5. **触发执行**：点执行 → 平台调 Jenkins `build` API → 拿 queue id → 轮询 build number → 写 `TaskRun`
6. **结果回传**：前端调 `/tasks/runs/{id}/refresh` 拉最新 build 状态 + allure URL

## 平台 → Jenkins 集成

后端 `apps/jenkins_client/client.py` 用裸 `requests` 调 Jenkins REST API：

- `create_or_update_job(name, xml)` - 用模板 `job_template.xml` 创建 Pipeline
- `trigger_build(name, params)` - 触发 build,返回 queue item id
- `queue_item_to_build(queue_id)` - 轮询拿真实 build number
- `get_build_info(name, number)` - 拉 result/duration/building
- `get_console(name, number)` - 拉控制台日志

需要 Jenkins 装 **Pipeline** + **Git** + **Allure** 插件，并在用户配置里生成 API Token 填到后端 `.env` 的 `JENKINS_TOKEN`。

## API 文档

后端启动后访问 `http://127.0.0.1:8000/api/docs`（drf-spectacular 自动生成的 OpenAPI + Swagger UI）。

## 设计取舍

- **不自研 runner**：pytest 生态足够，平台只做元数据管理 + 调度
- **不自研执行器**：复用 Jenkins，平台通过 REST API 触发，避免引入 Celery/Redis 运维成本
- **裸 requests 调 Jenkins**：不引 `python-jenkins`，避免版本兼容坑，REST API 本就简单
- **Monaco 而非 CodeMirror**：VSCode 同款，Python 语法/补全/快捷键开箱即用
- **DRF ModelViewSet**：CRUD 用框架默认，业务动作才写 `@action`
- **不引权限框架**：`IsAuthenticated` 够初期用，要 RBAC 再加 `django-guardian`

---

## Action Word (AW) 可视化用例编排

平台把 OpenAPI 解析出的每个接口操作称作 **Action Word（AW，动作字）**，是可复用的最小测试动作单元。

### 流程

```
OpenAPI YAML ──解析──> ActionWord 库 ──拖拽──> 用例三段编排 ──生成──> pytest 脚本
```

### 三段编排

用例脚本编写框分三段，每段可拖入任意 AW，AW 之间可跨段拖动调整顺序：

| 段 | 作用 | 典型 AW |
|----|------|---------|
| 前置步骤 (setup) | 准备数据、登录、造资源 | `login`、`createUser` |
| 测试步骤 (test) | 被测核心动作 + 断言 | `createOrder`、`getOrder` |
| 后置步骤 (teardown) | 清理数据 | `deleteOrder`、`logout` |

### 使用步骤

1. **解析 OpenAPI 生成 AW**
   - 进「AW 库」页 → 点「从 OpenAPI 解析」
   - 选项目，留空 spec 路径会扫描 `data/openapi/` 下所有 yaml/json
   - 平台为每个接口生成一个 AW，含代码模板和参数 schema

2. **手动新建 AW**（可选）
   - 「AW 库」页 → 「新建 AW」
   - 填名称、Key、分类、代码模板（`{{ var }}` 占位符）、参数 schema (JSON)

3. **编排用例**
   - 「用例」页找到用例 → 点「编排」
   - 进入 Case Composer 页面：
     - **左侧**：AW 库，按分类分组，可搜索过滤
     - **中间**：三个区段（前置/测试/后置），从左侧拖入 AW
     - **右侧**：选中步骤后填参数 + 实时预览渲染后代码 + 整用例预览
   - 跨区段拖动可调整 AW 所属段；同段内拖动调整顺序

4. **保存 + 生成脚本**
   - 点「保存步骤」只持久化步骤序列
   - 点「保存并生成脚本」额外触发代码生成：
     - 把步骤按 `setup → test → teardown` 顺序渲染为完整 pytest 函数
     - 可选写盘到指定路径（如 `api/test_shop_001.py`）
     - 可选同步入库为 `Script` 记录（与「脚本」页打通，可在 Monaco 编辑器继续编辑）

### 后端 API

| Endpoint | 方法 | 作用 |
|----------|------|------|
| `/api/actionwords/` | GET/POST | AW 列表 / 新建 |
| `/api/actionwords/{id}/` | GET/PATCH/DELETE | AW 详情/改/删 |
| `/api/actionwords/parse/` | POST | 从 OpenAPI 解析生成 AW |
| `/api/actionwords/{id}/render/` | POST | 渲染单个 AW 为代码块（预览） |
| `/api/testcases/cases/{id}/steps/` | GET/PUT | 获取/整体保存用例步骤序列 |
| `/api/testcases/steps/` | CRUD | 单步骤增删改查 |
| `/api/testcases/cases/{id}/generate_script/` | POST | 把用例+步骤渲染为完整 pytest 脚本（可写盘+入库） |

### 代码模板语法

AW 的 `code_template` 字段使用 `{{ var }}` 占位符：

```
resp = http.request("POST", "/orders", json=body)
assert resp.status_code in (200, 201, 204)
```

参数 schema 示例：

```json
{
  "type": "object",
  "properties": {
    "body": { "type": "object", "in": "body", "description": "订单 JSON" }
  },
  "required": ["body"]
}
```

渲染时，字符串参数会原样插入（若是合法 Python 标识符则作为变量引用），dict/list 会转 JSON。

### 生成的脚本示例

```python
import pytest

pytestmark = [pytest.mark.api]

def test_shop_001(http):
    # === 全局变量 ===
    base_url = "https://api.example.com"
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')  # 动态变量

    # === 前置步骤 ===
    # step 1: 登录
    resp = http.request("POST", f"{base_url}/login", json={"user": "admin", "pass": "***"})
    assert resp.status_code in (200, 201, 204)
    token = resp.json()["token"]  # 局部变量,用户在步骤里自己赋值

    # === 测试步骤 ===
    # step 1: 创建订单
    resp = http.request("POST", f"{base_url}/orders?ts={timestamp}", json={"product_id": 123})
    assert resp.status_code in (200, 201, 204)

    # === 后置步骤 ===
    # step 1: 清理
    resp = http.request("DELETE", f"{base_url}/orders/{token}")
    assert resp.status_code in (200, 201, 204)
```

---

## 变量管理

### 变量引用语法

在 AW 参数值里可使用变量引用,代码生成时自动解析替换:

| 语法 | 含义 | 渲染为 |
|------|------|-------|
| `$${name}` | 全局变量 | Python 变量名 `name`,函数顶部自动注入初始化 |
| `${name}` | 局部变量 | Python 变量名 `name`(用户需在前序步骤自己赋值) |

混合字符串自动转 f-string:

- 参数值 = `$${base_url}` → 渲染为 `base_url`
- 参数值 = `prefix-$${ts}` → 渲染为 `f"prefix-{ts}"`
- JSON body = `{"k": "${token}"}` → 渲染为 `{"k": token}`

### 变量属性

| 字段 | 作用 |
|------|------|
| `key` | 变量名,代码引用用 |
| `value` | 静态值 |
| `type` | string / int / bool / json |
| `description` | 备注 |
| `is_secret` | 保护:API 返回 `***`,不入日志 |
| `is_encrypted` | 加密存储:Fernet 对称加密入库 |
| `is_dynamic` | 动态变量:`value` 存表达式,运行时计算 |
| `dynamic_expr` | 动态表达式,如 `datetime.now().strftime('%Y%m%d%H%M%S')` |

### 变量目录

支持任意层级的目录树,变量可挂到某个目录下分类管理:

- 全局目录:`project` 为空
- 项目目录:绑定到具体项目
- 自引用 `parent` 实现子目录
- 变量页左侧 el-tree 展示,支持新建/编辑/删除目录节点

### 动态变量表达式

受限命名空间 eval,只暴露 `datetime` / `random` / `uuid` / `time`:

```python
datetime.now().strftime('%Y%m%d%H%M%S')         # 时间戳
str(random.randint(100000, 999999))              # 随机数
str(uuid.uuid4())                                # UUID
```

变量页表单里有「测试表达式」按钮,可即时预览计算结果。

### 变量 API

| Endpoint | 方法 | 作用 |
|----------|------|------|
| `/api/variables/` | GET/POST | 变量列表/新建 |
| `/api/variables/{id}/` | GET/PATCH/DELETE | 改/删 |
| `/api/variables/{id}/reveal/` | POST | 查看加密/保护变量的真实值 |
| `/api/variables/test-dynamic/` | POST | 测试动态表达式 |
| `/api/variables/categories/` | CRUD | 目录树增删改查 |
| `/api/variables/envs/` | CRUD | 环境增删改查 |

---

## 版本与迭代管理

### 版本 (Version)

按产品版本管理用例基线,锁定后用例不可改。

| 字段 | 说明 |
|------|------|
| `name` | 版本号,如 v1.0 |
| `status` | open(开放) / locked(锁定) / archived(归档) |
| `release_date` | 发布日期 |
| `is_baseline` | 是否基线版本 |

### 迭代 (Iteration)

迭代/Sprint,关联到版本,有起止时间。

| 字段 | 说明 |
|------|------|
| `name` | 迭代号,如 2024Q1Sprint3 |
| `version` | 关联版本 |
| `status` | planning / active / closed |
| `start_date` / `end_date` | 起止日期 |

### 用例关联

`TestCase` 同时关联 `version` 和 `iteration`,可在用例列表按版本/迭代筛选,在用例编排页按版本/迭代过滤用例树。

### 版本迭代 API

| Endpoint | 方法 | 作用 |
|----------|------|------|
| `/api/releases/versions/` | CRUD | 版本管理 |
| `/api/releases/iterations/` | CRUD | 迭代管理 |

---

## 用例编排页（三栏布局）

「用例编排」页(`/compose`)是核心可视化编排界面:

```
┌──────────────┬──────────────────────────┬──────────────┐
│  用例树      │     步骤编排画板         │   AW 库      │
│              │                          │              │
│ 项目         │ ┌─前置步骤─────────┐    │ [分类1]      │
│ └ 模块A      │ │ step1: login     │    │  - AW1       │
│   └ 用例1    │ └─────────────────┘    │  - AW2       │
│   └ 用例2    │ ┌─测试步骤─────────┐    │              │
│ └ 模块B      │ │ step1: createXxx │    │ [分类2]      │
│              │ │ step2: getXxx    │    │  - AW3       │
│              │ └─────────────────┘    │              │
│              │ ┌─后置步骤─────────┐    │              │
│              │ │ step1: cleanup   │    │              │
│              │ └─────────────────┘    │              │
│              │ ┌─选中步骤详情────┐    │              │
│              │ │ 参数表单         │    │              │
│              │ │ 渲染代码预览     │    │              │
│              │ └─────────────────┘    │              │
│              │ ┌─整用例预览──────┐    │              │
│              │ │ def test_xxx():  │    │              │
│              │ └─────────────────┘    │              │
└──────────────┴──────────────────────────┴──────────────┘
```

- **左:用例树** - 项目 -> 模块 -> 用例 三级树,顶部按版本/迭代过滤,点击用例加载到画板
- **中:画板** - 三段(setup/test/teardown),从右侧 AW 库拖入;选中步骤下方显示参数表单 + 渲染代码 + 整用例预览
- **右:AW 库** - 按分类分组的可拖动 AW 列表,搜索过滤
