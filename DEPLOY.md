# AutoTest Platform 部署文档（小白版）

> 本文档面向计算机初学者，从零开始一步步把平台跑起来。Windows 和 Linux 都覆盖。
> 每一步都有命令 + 解释 + 验证方法。遇到报错先看文末「常见问题」。

---

## 目录

- [一、整体说明](#一整体说明)
- [二、需要装什么（前置软件）](#二需要装什么前置软件)
  - [2.1 Windows 安装](#21-windows-安装)
  - [2.2 Linux 安装](#22-linux-安装)
- [三、获取代码（GitHub）](#三获取代码github)
- [四、部署 PostgreSQL 数据库](#四部署-postgresql-数据库)
- [五、部署后端（Django）](#五部署后端django)
- [六、部署前端（Vue3）](#六部署前端vue3)
- [七、首次初始化](#七首次初始化)
- [八、登录验证](#八登录验证)
- [九、配置 Jenkins 对接](#九配置-jenkins-对接)
- [十、生产部署（Docker Compose 一键）](#十生产部署docker-compose-一键)
- [十一、代码仓推送到 GitHub](#十一代码仓推送到-github)
- [十二、常见问题](#十二常见问题)
- [附录 A：端口清单](#附录-a端口清单)
- [附录 B：目录结构](#附录-b目录结构)

---

## 一、整体说明

平台分三部分：

| 组件 | 作用 | 默认端口 |
|------|------|---------|
| PostgreSQL | 数据库，存所有数据 | 5432 |
| Django 后端 | API 服务 | 8000 |
| Vue3 前端 | 网页面板 | 5173（开发）/ 80（生产）|

启动顺序：**数据库 → 后端 → 前端**。

---

## 二、需要装什么（前置软件）

下面 5 个软件，Windows 和 Linux 都要装。

| 软件 | 版本要求 | 干什么用 |
|------|---------|---------|
| Git | 任意版本 | 拉代码、推代码到 GitHub |
| Python | 3.10 或更高 | 跑后端、跑测试脚本 |
| Node.js | 20.x LTS | 跑前端、装 npm 包 |
| PostgreSQL | 16.x | 数据库 |
| Docker（可选） | 24+ | 生产一键部署用，开发可不装 |

### 2.1 Windows 安装

#### ① 装 Git

1. 打开浏览器访问 https://git-scm.com/download/win
2. 页面会自动开始下载安装包（`Git-2.x.x-64-bit.exe`），没开始就点 "Click here to download"
3. 双击安装包，一路点 **Next**，全部默认即可
4. 装完后，按 `Win + R`，输入 `cmd` 回车，在弹出的黑窗口里输入：
   ```cmd
   git --version
   ```
   看到 `git version 2.x.x` 说明装好了

#### ② 装 Python

1. 访问 https://www.python.org/downloads/windows/
2. 下载 **Python 3.11.x** 的 **Windows installer (64-bit)**
3. 双击安装包，**重要：在第一页勾选最下面的 "Add Python to PATH"**，然后点 **Install Now**
4. 验证：打开新的 `cmd` 窗口（旧窗口看不到新装的环境变量），输入：
   ```cmd
   python --version
   pip --version
   ```
   两条都有版本号输出即成功

#### ③ 装 Node.js

1. 访问 https://nodejs.org/zh-cn/download
2. 选 **LTS（长期支持版）**，下载 Windows Installer（.msi）
3. 双击安装，一路 Next，全部默认
4. 验证：
   ```cmd
   node --version
   npm --version
   ```
   看到 `v20.x.x` 和 `10.x.x` 即可

#### ④ 装 PostgreSQL

1. 访问 https://www.postgresql.org/download/windows/
2. 点 "Download the installer" 进入 EnterpriseDB 页面，选版本 16.x 的 Windows x86-64
3. 双击安装包，**记住你设置的 superuser 密码**（后面要用，比如设为 `postgres`）
4. 端口保持默认 `5432`
5. 后面一路 Next 直到完成
6. 验证：打开 `cmd`，输入：
   ```cmd
   "C:\Program Files\PostgreSQL\16\bin\psql" -U postgres -h localhost
   ```
   输入密码，看到 `postgres=#` 提示符即成功。输入 `\q` 退出。

#### ⑤ 装 Docker（可选，仅生产部署用）

1. 访问 https://www.docker.com/products/docker-desktop/
2. 下载 Docker Desktop for Windows
3. 安装时勾选 "Use WSL 2 instead of Hyper-V"（推荐）
4. 安装完重启电脑
5. 启动 Docker Desktop，等右下角图标变绿
6. 验证：
   ```cmd
   docker --version
   docker compose version
   ```

### 2.2 Linux 安装

> 下面命令在 **Ubuntu 22.04/24.04** 上验证过。CentOS/RHEL 把 `apt` 换成 `dnf/yum` 即可。

#### ① 装 Git

```bash
sudo apt update
sudo apt install -y git
git --version
```

#### ② 装 Python

Ubuntu 24.04 自带 Python 3.12，22.04 自带 3.10。装开发头文件和 pip：

```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev
python3 --version
pip3 --version
```

#### ③ 装 Node.js 20

```bash
# 加 NodeSource 源
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version
```

#### ④ 装 PostgreSQL 16

```bash
# 加官方源
sudo sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
sudo apt update
sudo apt install -y postgresql-16

# 启动
sudo systemctl enable --now postgresql
sudo systemctl status postgresql    # 看到 active (running) 即可
```

设置 postgres 用户密码（后面要用）：

```bash
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"
```

#### ⑤ 装 Docker（可选）

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER        # 让当前用户免 sudo 用 docker
newgrp docker                         # 立即生效组变更
docker --version
docker compose version
```

---

## 三、获取代码（GitHub）

假设代码已经推到 GitHub 仓库 `https://github.com/你的用户名/autotest_framework.git`（推送方法见第十一章）。

### Windows

```cmd
cd C:\Users\你的用户名
git clone https://github.com/你的用户名/autotest_framework.git
cd autotest_framework
```

### Linux

```bash
cd ~
git clone https://github.com/你的用户名/autotest_framework.git
cd autotest_framework
```

> 如果是私有仓库，会提示输入 GitHub 用户名和密码。**密码要用 Personal Access Token**，不是登录密码。Token 生成方法见第十一章。

---

## 四、部署 PostgreSQL 数据库

### 4.1 创建数据库和用户

#### Windows

打开 `cmd`，执行（密码替换成你安装时设的）：

```cmd
"C:\Program Files\PostgreSQL\16\bin\psql" -U postgres -h localhost
```

输入密码后进入 `postgres=#` 提示符，依次执行：

```sql
CREATE DATABASE autotest ENCODING 'UTF8';
CREATE USER autotest_user WITH PASSWORD 'autotest_pass';
ALTER DATABASE autotest OWNER TO autotest_user;
GRANT ALL PRIVILEGES ON DATABASE autotest TO autotest_user;
\q
```

#### Linux

```bash
sudo -u postgres psql
```

进入后执行同样的 4 条 SQL，然后 `\q` 退出。

### 4.2 验证连接

#### Windows

```cmd
"C:\Program Files\PostgreSQL\16\bin\psql" -U autotest_user -h localhost -d autotest
```

输入密码 `autotest_pass`，看到 `autotest=>` 提示符即成功。`\q` 退出。

#### Linux

```bash
psql -U autotest_user -h localhost -d autotest
```

---

## 五、部署后端（Django）

### 5.1 Windows

#### ① 进入后端目录

```cmd
cd C:\Users\你的用户名\autotest_framework\backend
```

#### ② 创建虚拟环境

虚拟环境把项目依赖隔离，不污染系统 Python。

```cmd
python -m venv .venv
```

#### ③ 激活虚拟环境

```cmd
.venv\Scripts\activate
```

激活成功后命令行前面会出现 `(.venv)` 前缀。**之后所有 pip / python 命令都要在激活状态下执行。**

> 每次重新打开 cmd 都要重新执行这一步激活。

#### ④ 装依赖

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

国内网络慢可换清华源：

```cmd
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### ⑤ 配置环境变量

复制示例配置：

```cmd
copy .env.example .env
```

用记事本（或 VSCode）打开 `.env`，修改为：

```env
DJANGO_SECRET_KEY=随便填一串长字符比如abc123xyz789qwerty
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=*

DB_NAME=autotest
DB_USER=autotest_user
DB_PASSWORD=autotest_pass
DB_HOST=127.0.0.1
DB_PORT=5432

JENKINS_URL=http://127.0.0.1:8080
JENKINS_USER=admin
JENKINS_TOKEN=

CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

保存关闭。

#### ⑥ 跑数据库迁移（建表）

```cmd
python manage.py migrate
```

会看到一堆 `Applying ... OK`，最后回到提示符即成功。

#### ⑦ 创建管理员账号

```cmd
python manage.py createsuperuser
```

按提示输入：
- Username: `admin`
- Email: 回车跳过
- Password: `admin123456`（输入时屏幕不显示，正常现象）
- Bypass password validation and continue? 输入 `y`

看到 `Superuser created successfully.` 即成功。

#### ⑧ 启动后端

```cmd
python manage.py runserver 0.0.0.0:8000
```

看到：

```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
...
Starting development server at http://0.0.0.0:8000/
Quit the server with CTRL-BREAK.
```

即成功。**这个窗口不要关，后端在跑。**

#### ⑨ 验证

浏览器打开 http://127.0.0.1:8000/api/docs ，能看到 Swagger UI 文档页即后端 OK。

### 5.2 Linux

#### ① 进入目录

```bash
cd ~/autotest_framework/backend
```

#### ② 创建并激活虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

激活后提示符前会出现 `(.venv)`。

#### ③ 装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
# 国内加速:
# pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### ④ 配置环境变量

```bash
cp .env.example .env
nano .env
```

按 Windows 章节同样的内容改 `.env`，保存退出（nano：`Ctrl+O` 回车 `Ctrl+X`）。

#### ⑤ 迁移 + 建超管

```bash
python manage.py migrate
python manage.py createsuperuser
```

#### ⑥ 启动后端

```bash
python manage.py runserver 0.0.0.0:8000
```

#### ⑦ 验证

```bash
curl http://127.0.0.1:8000/api/docs
```

有 HTML 输出即成功。或浏览器访问同一地址（服务器要开 8000 安全组）。

---

## 六、部署前端（Vue3）

### 6.1 Windows

**新开一个 cmd 窗口**（后端那个窗口保持开着）：

```cmd
cd C:\Users\你的用户名\autotest_framework\frontend
npm install
```

`npm install` 会下载几百兆依赖，耐心等几分钟。国内可换淘宝镜像加速：

```cmd
npm config set registry https://registry.npmmirror.com
npm install
```

启动前端：

```cmd
npm run dev
```

看到：

```
  VITE v5.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://x.x.x.x:5173/
```

即成功。**这个窗口也不要关。**

### 6.2 Linux

```bash
cd ~/autotest_framework/frontend
npm install
# 加速: npm config set registry https://registry.npmmirror.com
npm run dev
```

要让外网访问，加 `--host`：

```bash
npm run dev -- --host 0.0.0.0
```

---

## 七、首次初始化

后端和前端都跑起来后，**还需要初始化一些基础数据**。

### 7.1 用 admin 后台快速建项目

浏览器打开 http://127.0.0.1:8000/admin/

用刚才创建的超级用户登录（admin / admin123456）。

这里能看到所有数据模型，可以直接增删改查。**生产环境不要用 admin 给业务用户用，仅做初始化和应急。**

### 7.2 用平台前端建初始数据

浏览器打开 http://localhost:5173

用 admin / admin123456 登录。

按顺序建：

1. **项目**：进入「项目」页 → 新建项目 → 填名称、Key、仓库地址（可填你的 GitHub 仓库 URL）、分支
2. **环境**：进入「变量」页 → 切到「环境」Tab → 新建环境，如 dev（API Base URL 填被测系统地址）
3. **变量**：同页面「变量」Tab → 新建变量，如 `AUTOTEST_API_TOKEN`（如有）
4. **需求**：进「需求」页 → 新建需求（可关联 JIRA 编号）
5. **用例**：进「用例」页 → 新建用例，关联项目、需求
6. **脚本**：进「脚本」页 → 点「从磁盘同步」自动把仓库里 `api/` 和 `ui/` 下的 `test_*.py` 导入；或新建脚本，在线编辑保存
7. **任务**：进「任务」页 → 新建任务，选项目、环境、关联用例、填 Jenkins Job 名（先空着，第十章配好 Jenkins 再回填）

---

## 八、登录验证

到这里整个平台应该能访问了。检查清单：

| 检查项 | 方法 | 期望结果 |
|--------|------|---------|
| 数据库 | `psql -U autotest_user -d autotest -h localhost` 能登录 | 看到 `autotest=>` |
| 后端 | 浏览器 http://127.0.0.1:8000/api/docs | Swagger UI 页面 |
| 前端 | 浏览器 http://localhost:5173 | 登录页 |
| 登录 | admin / admin123456 | 跳转到 Dashboard |
| 建项目 | 前端「项目」页新建 | 列表能看到新项目 |
| Jenkins 集成 | 第九章配完测 | 能触发任务 |

---

## 九、配置 Jenkins 对接

平台通过 REST API 调 Jenkins 触发测试任务。**需要先有一个跑着的 Jenkins。**

### 9.1 装 Jenkins

#### Windows

1. 访问 https://www.jenkins.io/download/
2. 下载 Windows LTS 安装包（.msi）
3. 双击安装，全部默认。安装完会自动启动服务并打开浏览器 http://127.0.0.1:8080
4. 按提示输入初始密码（密码在 `C:\Program Files\Jenkins\secrets\initialAdminPassword` 文件里，用记事本打开复制）
5. 选「安装推荐插件」，等待安装
6. 创建管理员账号

#### Linux

```bash
# Ubuntu
sudo apt install -y fontconfig openjdk-17-jre
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | sudo tee /etc/apt/sources.list.d/jenkins.list
sudo apt update
sudo apt install -y jenkins
sudo systemctl enable --now jenkins

# 查初始密码
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

浏览器打开 http://127.0.0.1:8080 ，按提示完成初始化。

### 9.2 装 Jenkins 插件

进入 `Manage Jenkins → Plugins → Available plugins`，搜索并安装：

- **Pipeline** （默认已装）
- **Git** （默认已装）
- **Allure Jenkins Plugin** （用于测试报告）
- **WSL** 或 **Batch** （看你测试脚本跑在哪）

装完重启 Jenkins。

### 9.3 生成 API Token

1. 登录 Jenkins，右上角点用户名 → `Configure`（设置）
2. 找到 **API Token** 区域，点 `Add new Token`
3. 起个名字如 `autotest-platform`，点 Generate
4. **复制 token 字符串**（只显示一次，丢了要重新生成）

### 9.4 配置平台连接 Jenkins

回到平台前端，进「Jenkins」页，或者直接改后端 `.env`：

```env
JENKINS_URL=http://127.0.0.1:8080
JENKINS_USER=admin
JENKINS_TOKEN=刚才复制的token
```

改完要重启后端（关掉 runserver 窗口重新执行 `python manage.py runserver`）。

### 9.5 创建 Jenkins Job

在平台「Jenkins」页填表：

- Job 名称：`autotest-smoke`
- 仓库 URL：你的 GitHub 仓库地址
- 分支：`main`
- Suite：`all`

点「创建/更新 Job」。平台会调 Jenkins REST API 帮你创建好 Pipeline job。

之后在「任务」页新建任务时，Jenkins Job 名填 `autotest-smoke` 即可关联。

---

## 十、生产部署（Docker Compose 一键）

开发用上面的方式（手动起三个进程），生产用 Docker Compose 一键。

### 10.1 前置

装好 Docker（见第二章），项目代码已经 clone 下来。

### 10.2 配置环境变量

在项目根目录建 `.env`（和 docker-compose.yml 同级）：

```env
DB_NAME=autotest
DB_USER=postgres
DB_PASSWORD=换成强密码比如Aa123456!
```

在 `backend/.env` 里也同步：

```env
DJANGO_SECRET_KEY=换成随机长字符串
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=*

DB_NAME=autotest
DB_USER=postgres
DB_PASSWORD=Aa123456!
DB_HOST=db
DB_PORT=5432

JENKINS_URL=http://你的Jenkins地址:8080
JENKINS_USER=admin
JENKINS_TOKEN=你的token

CORS_ORIGINS=http://你的服务器IP,http://你的域名
```

注意 `DB_HOST=db`，因为 docker compose 里数据库服务名是 `db`。

### 10.3 启动

在项目根目录（有 `docker-compose.yml` 的地方）：

```bash
docker compose up -d --build
```

第一次会拉镜像、构建、跑迁移，大约 5-10 分钟。

### 10.4 初始化数据库和管理员

```bash
# 跑迁移（Dockerfile 里已经跑过，这里再确认）
docker compose exec backend python manage.py migrate

# 建超管
docker compose exec backend python manage.py createsuperuser
```

### 10.5 验证

- 前端：http://服务器IP
- 后端 API 文档：http://服务器IP/api/docs
- 数据库：在容器里，不直接暴露

### 10.6 常用运维命令

```bash
docker compose ps                    # 看服务状态
docker compose logs -f backend       # 看后端日志
docker compose logs -f frontend      # 看前端日志
docker compose restart backend       # 重启后端
docker compose down                  # 停止全部
docker compose up -d                 # 启动全部
docker compose up -d --build backend # 重新构建后端镜像
```

### 10.7 更新代码后部署

```bash
git pull
docker compose up -d --build
docker compose exec backend python manage.py migrate    # 有新迁移才需要
```

---

## 十一、代码仓推送到 GitHub

### 11.1 注册 GitHub 账号

访问 https://github.com/signup 注册一个账号。

### 11.2 在 GitHub 创建仓库

1. 登录后点右上角 `+` → `New repository`
2. Repository name 填 `autotest_framework`
3. Description 随便填
4. 选 **Private**（私有，推荐）或 **Public**（公开）
5. **不要勾** "Add a README"、"Add .gitignore"、"Choose a license"——本地已经有这些文件
6. 点 `Create repository`

会跳到一个页面，显示推送命令，**保留这个页面**，下面要用。

### 11.3 配置 Git 身份（首次用 Git 才需要）

#### Windows

打开 cmd：

```cmd
git config --global user.name "你的GitHub用户名"
git config --global user.email "你的GitHub注册邮箱"
```

#### Linux

```bash
git config --global user.name "你的GitHub用户名"
git config --global user.email "你的GitHub注册邮箱"
```

### 11.4 生成 Personal Access Token（代替密码）

GitHub 从 2021 年起不允许用账号密码推送，必须用 Token。

1. 登录 GitHub，右上角头像 → `Settings`
2. 左侧最下面 `Developer settings`
3. `Personal access tokens` → `Tokens (classic)` → `Generate new token (classic)`
4. Note 填 `autotest-push`
5. Expiration 选 `No expiration`（或 90 天）
6. 勾选 `repo`（整个 repo 那一行的复选框）
7. 点 `Generate token`
8. **复制 token 字符串**（形如 `ghp_xxxxxxxxxxxx`），保存好，关掉页面就看不到了

### 11.5 把本地代码推到 GitHub

在项目根目录（有 `pyproject.toml` 和 `README.md` 的地方）：

#### Windows

```cmd
cd C:\Users\你的用户名\autotest_framework

git init
git add .
git commit -m "init: autotest framework with Django platform"

git branch -M main
git remote add origin https://github.com/你的用户名/autotest_framework.git
git push -u origin main
```

推送时会弹出登录框（或 cmd 里提示输入）：
- Username：你的 GitHub 用户名
- Password：**粘贴刚才的 Token**（不是 GitHub 登录密码）

#### Linux

```bash
cd ~/autotest_framework

git init
git add .
git commit -m "init: autotest framework with Django platform"

git branch -M main
git remote add origin https://github.com/你的用户名/autotest_framework.git
git push -u origin main
```

第一次推送会提示输入用户名密码：
- Username for 'https://github.com': 你的 GitHub 用户名
- Password for 'https://...@github.com': 粘贴 Token

### 11.6 验证推送成功

刷新 GitHub 仓库页面，能看到所有文件即成功。

### 11.7 缓存 Token（避免每次输入）

#### Windows

```cmd
git config --global credential.helper manager
```

下次推送输一次就记住了。

#### Linux

```bash
# 缓存 1 小时
git config --global credential.helper cache
git config --global credential.helper 'cache --timeout=3600'

# 或永久保存（明文存在 ~/.git-credentials，安全要求高别用）
git config --global credential.helper store
```

### 11.8 之后日常更新代码

每次改完代码，提交并推送：

```bash
git add .
git commit -m "描述这次改了啥"
git push
```

其他机器拉最新代码：

```bash
git pull
```

---

## 十二、常见问题

### Q1: `pip install` 报错 `error: Microsoft Visual C++ 14.0 is required`

**原因**：Windows 装 psycopg2 需要编译。

**解决**：

```cmd
pip install psycopg2-binary -i https://pypi.tuna.tsinghua.edu.cn/simple
```

`requirements.txt` 里已经是 `psycopg2-binary`，正常不会报错。如果还是报，去 https://visualstudio.microsoft.com/visual-cpp-build-tools/ 下载装一下 Build Tools。

### Q2: `python manage.py migrate` 报 `could not connect to server`

**原因**：数据库没启动，或 `.env` 里连接参数错。

**检查**：

1. PostgreSQL 服务在跑（Windows：`services.msc` 找 postgresql；Linux：`sudo systemctl status postgresql`）
2. `.env` 里 `DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD` 对得上
3. 防火墙没挡 5432 端口

### Q3: `python manage.py migrate` 报 `password authentication failed for user`

**原因**：密码不对。

**解决**：重新设密码：

```sql
-- psql 进去后
ALTER USER autotest_user WITH PASSWORD 'autotest_pass';
```

### Q4: 前端 `npm install` 卡住或报错

**解决**：

```cmd
npm config set registry https://registry.npmmirror.com
rm -rf node_modules package-lock.json
npm install
```

Windows 删 `node_modules` 用 `rmdir /s /q node_modules`。

### Q5: 前端访问 `http://localhost:5173` 白屏

**检查**：

1. 后端在跑（http://127.0.0.1:8000/api/docs 能打开）
2. 浏览器 F12 打开控制台，看红色报错
3. 多数是接口 401，先确认登录态

### Q6: 后端启动报 `ModuleNotFoundError: No module named 'xxx'`

**原因**：没激活虚拟环境，或依赖没装全。

**解决**：

```cmd
.venv\Scripts\activate         # Windows
source .venv/bin/activate      # Linux
pip install -r requirements.txt
```

### Q7: Jenkins 触发报 `JenkinsError: POST /job/.../build -> 403`

**原因**：Jenkins CSRF 保护，token 没拿到或失效。

**解决**：

1. 确认 `.env` 里 `JENKINS_TOKEN` 是有效的 API Token（不是登录密码）
2. Jenkins 进 `Manage Jenkins → Security → CSRF Protection` 看是否启用
3. 重启后端让配置生效

### Q8: `git push` 报 `Authentication failed`

**原因**：Token 不对或过期。

**解决**：

1. 重新生成 Token（见 11.4）
2. Windows：控制面板 → 凭据管理器 → Windows 凭据 → 找到 git:https://github.com → 编辑或删除，下次推送重新输
3. Linux：`rm ~/.git-credentials`，重新推送时输入

### Q9: Docker 部署后前端打不开

**检查**：

1. `docker compose ps` 三个服务都是 `running` 状态
2. `docker compose logs frontend` 看有没有报错
3. 服务器安全组/防火墙开 80 端口
4. `backend/.env` 里 `CORS_ORIGINS` 包含你的访问地址

### Q10: Linux 服务器从外部访问不到

**原因**：防火墙挡了。

**解决**：

```bash
# Ubuntu ufw
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 5173/tcp
sudo ufw reload

# 云服务器还要去控制台安全组放行
```

### Q11: 改了 `.env` 不生效

**原因**：Django 不会自动重载环境变量。

**解决**：重启后端进程：

- 开发模式：`Ctrl+C` 关掉 `runserver`，重新执行
- Docker：`docker compose restart backend`

### Q12: 端口被占用

**Windows 查谁占了**：

```cmd
netstat -ano | findstr :8000
taskkill /PID 找到的PID /F
```

**Linux**：

```bash
sudo lsof -i:8000
sudo kill 找到的PID
```

或换个端口启动：`python manage.py runserver 0.0.0.0:9000`

---

## 附录 A：端口清单

| 端口 | 服务 | 是否需要对外 |
|------|------|-------------|
| 5432 | PostgreSQL | 否（仅本机） |
| 8000 | Django 后端 | 开发期可对外，生产建议反代 |
| 5173 | Vue3 前端（开发） | 否 |
| 80 | Vue3 前端（生产 nginx） | 是 |
| 8080 | Jenkins | 是（如需远程触发） |

---

## 附录 B：目录结构

```
autotest_framework/
├── api/                    # pytest 接口用例
├── ui/                     # pytest UI 用例
├── common/                 # 测试公共库
├── data/openapi/           # OpenAPI 源
├── scripts/                # openapi → SDK 生成器
├── conftest.py
├── pyproject.toml
├── Jenkinsfile             # 测试 pipeline
│
├── backend/                # Django 后端
│   ├── autotest_platform/  # 项目配置
│   ├── apps/               # 8 个业务 app
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   ├── initadmin.py
│   └── manage.py
│
├── frontend/               # Vue3 前端
│   ├── src/
│   ├── vite.config.ts
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── docker-compose.yml
├── dev.bat / dev.sh
├── DEPLOY.md               # 本文档
└── README.md
```

---

## 附录 C：快速启动清单（已熟练后用）

```bash
# 1. clone
git clone https://github.com/你的用户名/autotest_framework.git
cd autotest_framework

# 2. 数据库（已装好 PostgreSQL）
sudo -u postgres psql -c "CREATE DATABASE autotest ENCODING 'UTF8';"
sudo -u postgres psql -c "CREATE USER autotest_user WITH PASSWORD 'autotest_pass';"
sudo -u postgres psql -c "ALTER DATABASE autotest OWNER TO autotest_user;"

# 3. 后端
cd backend
python3 -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Windows: copy .env.example .env
# 改 .env 里的 DB_USER/DB_PASSWORD
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000

# 4. 前端（新窗口）
cd ../frontend
npm install
npm run dev

# 5. 浏览器打开
# 前端: http://localhost:5173
# 后端: http://127.0.0.1:8000/api/docs
```

---

**部署遇到本文档没覆盖的问题，把报错原文贴出来，按报错信息逐项排查。**
