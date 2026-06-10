# 报销系统 UML（用户系统 + Admin 系统）

由 `generate_uml_md.py` 自动生成。

## 双系统架构

| 系统 | 前端 | 职责 |
|------|------|------|
| **用户系统** | User Portal SPA | 按动态字段填报 Expense、查看状态、处理「我的审核任务」 |
| **Admin 系统** | Admin Portal SPA | 配置 Expense 字段、用户权限、审核顺序（ApprovalSequence） |

共享后端：`/user/*` 与 `/admin/*` 路由分离，共用 Expense + ApprovalEngine 领域层。

## Admin 可配置项

1. **Expense 字段** — `ExpenseFieldDefinition`：类型、必填、顺序、校验；发布后生成 `FieldSchemaVersion`
2. **用户权限** — `Role` + `Permission` + `RolePermission` + `UserRoleAssignment`
3. **审核顺序** — `ApprovalSequence` + `ApprovalStep`（stepOrder 1→n，审批人规则可指定用户/角色/部门负责人）

## 文档索引

| 文件 | 说明 |
|------|------|
| [01-dual-system-overview.md](01-dual-system-overview.md) | 双系统总览 |
| [02-domain-model.md](02-domain-model.md) | 领域模型 |
| [03-admin-config-model.md](03-admin-config-model.md) | Admin 配置模型 |
| [04-user-portal-frontend.md](04-user-portal-frontend.md) | 用户前端 |
| [05-admin-portal-frontend.md](05-admin-portal-frontend.md) | Admin 前端 |
| [06-user-backend-api.md](06-user-backend-api.md) | 用户后端 API |
| [07-admin-backend-api.md](07-admin-backend-api.md) | Admin 后端 API |
| [08-permission-model.md](08-permission-model.md) | 权限细节 |
| [09-dynamic-expense-fields.md](09-dynamic-expense-fields.md) | 动态字段 |
| [10-approval-sequence-engine.md](10-approval-sequence-engine.md) | 审核顺序引擎 |
| [11-expense-state-machine.md](11-expense-state-machine.md) | Expense 状态机 |
| [12-approval-instance-state-machine.md](12-approval-instance-state-machine.md) | 审批实例状态机 |
| [13-user-flow-sequence.md](13-user-flow-sequence.md) | 用户端到端时序 |
| [14-admin-flow-sequence.md](14-admin-flow-sequence.md) | Admin 配置时序 |
| [15-finance-review-archive.md](15-finance-review-archive.md) | 终审与存档 |
| [16-shared-backend-layers.md](16-shared-backend-layers.md) | 后端分层 |
| [17-end-to-end-actors.md](17-end-to-end-actors.md) | 参与方 |
| [18-api-routes-summary.md](18-api-routes-summary.md) | API 路由 |

## Expense 状态（摘要）

`DRAFT` → `SUBMITTED` → `IN_APPROVAL` → `APPROVED` → `ARCHIVED`；任一步可 → `REJECTED` → resubmit 重走审核链。

## 重新生成

```bash
python generate_uml_md.py
```
