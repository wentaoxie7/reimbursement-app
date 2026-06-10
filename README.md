# 报销系统（Expense 直达财务 + 双门户）

用户系统（React）与 Admin 系统（React）共用 FastAPI 后端与 PostgreSQL，设计说明见 [`docs/README.md`](docs/README.md)。

## 项目结构

```
uml_reimbursement/
├── backend/           # FastAPI + SQLAlchemy + Alembic
├── user-portal/       # 用户端 React (port 5173)
├── admin-portal/      # 管理端 React (port 5174)
├── docs/              # UML 文档
└── docker-compose.yml # PostgreSQL + Backend + 双前端
```

## 环境要求

| 工具 | 用途 | 检查命令 |
|------|------|----------|
| Docker Desktop | 一键运行整套系统 | `docker compose version` |
| Python 3.11+ | 本机后端开发（可选） | `python --version` |
| Node.js LTS | 本机前端开发（可选） | `node -v` 和 `npm -v` |

若提示 **`npm is not recognized`**：请安装 [Node.js LTS](https://nodejs.org/)，安装时勾选 “Add to PATH”，然后**关闭并重新打开**终端/Cursor，再执行 `npm install`。

## 快速开始

### Docker 一键运行（推荐）

先打开 Docker Desktop，等状态变成 Running，然后在项目根目录执行：

```powershell
cd C:\Users\TobyXie\Downloads\codes\uml_reimbursement
docker compose up --build
```

首次启动会自动完成这些事：

- 启动 PostgreSQL，宿主机端口 `5433`
- 构建并启动 FastAPI 后端，宿主机端口 `8000`
- 构建并启动用户端 React，宿主机端口 `5173`
- 构建并启动管理端 React，宿主机端口 `5174`
- 运行一次 `seed` 服务，自动建表并写入演示账号

| 服务 | 地址 |
|------|------|
| API / Swagger | http://localhost:8000/docs |
| 用户端 | http://localhost:5173 |
| 管理端 | http://localhost:5174 |

后台运行：

```powershell
docker compose up -d --build
```

查看日志：

```powershell
docker compose logs -f backend
```

停止：

```powershell
docker compose down
```

重置数据库并重新 seed：

```powershell
docker compose down -v
docker compose up --build
```

### 本机开发模式（可选）

如果你想本机热更新开发后端/前端，也可以只用 Docker 跑数据库：

```powershell
docker compose up -d postgres
```

**后端**

```powershell
cd C:\Users\TobyXie\Downloads\codes\uml_reimbursement\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python scripts\check_db.py
python scripts\seed.py
uvicorn app.main:app --reload --port 8000
```

**用户端**

```powershell
cd C:\Users\TobyXie\Downloads\codes\uml_reimbursement\user-portal
npm install
copy .env.example .env
npm run dev
```

**管理端**

```powershell
cd C:\Users\TobyXie\Downloads\codes\uml_reimbursement\admin-portal
npm install
copy .env.example .env
npm run dev
```

## 演示账号（seed 后）

| 邮箱 | 密码 | 门户 |
|------|------|------|
| employee@demo.com | employee123 | 用户端 — 填报报销 |
| finance@demo.com | finance123 | 用户端 — 第 1 步财务审核 |
| manager@demo.com | manager123 | 用户端 — 第 2 步经理审核 |
| admin@demo.com | admin123 | 管理端 — 字段/权限/审核链 |

## 主要 API

| 前缀 | 说明 |
|------|------|
| `POST /api/auth/login` | 登录 |
| `GET/PUT /api/auth/me` | 查看/更新当前用户名称 |
| `PUT /api/auth/password` | 修改当前用户密码 |
| `GET /api/user/field-schema` | 已发布字段（用户表单） |
| `GET /api/user/all-expenses` | 审核账号查看全组织报销 |
| `DELETE /api/user/expenses/{id}` | 删除自己的报销单 |
| `POST /api/user/expenses/{id}/submit` | 提交并进入审核链 |
| `POST /api/user/expenses/{id}/withdraw` | 撤回报销单到草稿 |
| `GET /api/user/approval-tasks` | 当前用户待审 |
| `GET/POST /api/admin/fields` | Admin 配置字段 |
| `DELETE /api/admin/fields/{id}` | 删除字段配置 |
| `POST /api/admin/fields/publish` | 发布 schema |
| `GET /api/admin/roles` | 角色列表 |
| `PUT /api/admin/users/{id}/roles` | 分配用户角色 |
| `GET/POST /api/admin/approval-sequences` | 审核顺序 |
| `DELETE /api/admin/approval-sequences/{id}` | 删除审核顺序 |

## 数据库迁移（可选）

```bash
cd backend
alembic revision --autogenerate -m "init"
alembic upgrade head
```

开发环境可直接 `python scripts/seed.py`（内部 `create_all`）。

## 启动失败排查

### `dockerDesktopLinuxEngine` / pipe not found

**含义：** Docker Desktop **没启动**或**没安装**。`docker compose` 无法拉取/启动镜像。

**使用 Docker（推荐）**

1. 安装并打开 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. 等托盘图标显示 **Running**
3. 项目根目录：`docker compose up --build`

Docker 版不依赖 `backend/.env`，compose 会在容器内注入 `postgres:5432` 的数据库地址。

### 不用 Docker，用本机 PostgreSQL（5432）

1. 确认本机 Postgres 服务已启动（安装版或 pgAdmin 自带）
2. 用超级用户执行 [`scripts/init-local-postgres.sql`](scripts/init-local-postgres.sql) 创建用户和库
3. 修改 `backend/.env`：

```env
DATABASE_URL=postgresql://reimbursement:reimbursement@localhost:5432/reimbursement
```

4. `cd backend` → `python scripts\check_db.py` → `python scripts\seed.py`

若你本机 Postgres 已有别的账号，也可把 `DATABASE_URL` 改成你的用户名/密码/库名。

| 现象 | 原因 | 处理 |
|------|------|------|
| `password authentication failed for user "reimbursement"` | 5432 上有 Postgres，但未创建 `reimbursement` 用户 | 执行 `init-local-postgres.sql`，或改 `.env` 为你自己的账号 |
| `Connection refused` on 5433 | Docker 数据库未运行 | 启动 Docker Desktop 后执行 `docker compose up -d postgres` |
| `reimbursement-seed` 失败 | 数据库初始化失败 | 执行 `docker compose logs seed` 查看原因，修好后再 `docker compose up seed` |
| `seed.py` 失败但 uvicorn 已启动 | 本机开发模式未初始化表/数据 | 修好数据库后重新运行 `python scripts\seed.py` |

本机开发模式连接测试：`cd backend` 后 `python scripts\check_db.py`，输出 `OK` 再执行 `seed.py`。
