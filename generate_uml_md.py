"""Generate Mermaid UML markdown: User System + Admin System (dual portal)."""

from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "docs"


def to_md(
    filename: str,
    title: str,
    diagram: str,
    description: str = "",
    diagram_kind: str = "class",
) -> None:
    md = f"""# {title}

{description}

```mermaid
{diagram.strip()}
```
"""
    path = OUTPUT_DIR / filename
    path.write_text(md, encoding="utf-8")
    print(f"Wrote {path}")


# (filename, title, diagram, description, diagram_kind)
DIAGRAMS: list[tuple[str, ...]] = [
    (
        "01-dual-system-overview.md",
        "双系统总览",
        """
flowchart TB
    subgraph UserSystem["用户系统 User Portal"]
        U_FE[User Frontend SPA]
        U_MOD[填报 / 我的报销 / 审核任务]
    end

    subgraph AdminSystem["管理系统 Admin Portal"]
        A_FE[Admin Frontend SPA]
        A_MOD[字段配置 / 用户权限 / 审核顺序]
    end

    subgraph Backend["共享后端 API"]
        GW[API Gateway + Auth]
        UM[User API Module]
        AM[Admin API Module]
        CORE[Expense + Approval Engine]
        DB[(Database)]
    end

    U_FE --> GW
    A_FE --> GW
    GW --> UM
    GW --> AM
    UM --> CORE
    AM --> CORE
    CORE --> DB
""",
        "两个独立前端应用共用一套后端：**用户系统**负责 expense 生命周期；**Admin 系统**负责元数据配置（字段、权限、审核顺序），配置变更影响用户侧表单与审批路由。",
        "flowchart",
    ),
    (
        "02-domain-model.md",
        "领域模型",
        """
classDiagram
    direction TB

    class Organization {
        +String id
        +String name
    }

    class User {
        +String id
        +String orgId
        +String email
        +String departmentId
        +boolean active
    }

    class Role {
        +String id
        +String code
        +String name
    }

    class Permission {
        +String id
        +String code
        +String description
    }

    class RolePermission {
        +String roleId
        +String permissionId
    }

    class UserRoleAssignment {
        +String userId
        +String roleId
    }

    class ExpenseFieldDefinition {
        +String id
        +String fieldKey
        +String label
        +FieldType type
        +boolean required
        +int displayOrder
        +boolean enabled
        +Json options
        +Json validation
    }

    class Expense {
        +String id
        +String ownerId
        +ExpenseStatus status
        +Json fieldValues
        +DateTime submittedAt
        +String approvalInstanceId
    }

    class Receipt {
        +String expenseId
        +String fileUrl
    }

    class ApprovalSequence {
        +String id
        +String name
        +boolean isDefault
        +boolean active
    }

    class ApprovalStep {
        +String id
        +String sequenceId
        +int stepOrder
        +ApproverRule approverRule
        +String fixedUserId
        +String roleCode
    }

    class ApprovalInstance {
        +String id
        +String expenseId
        +String sequenceId
        +int currentStepOrder
        +ApprovalInstanceStatus status
    }

    class ApprovalAction {
        +String instanceId
        +int stepOrder
        +String actorUserId
        +ActionType action
        +String comment
        +DateTime actedAt
    }

    class ArchiveRecord {
        +String expenseId
        +DateTime archivedAt
        +String bundlePath
    }

    Organization --> User
    Role --> RolePermission
    Permission --> RolePermission
    User --> UserRoleAssignment
    Role --> UserRoleAssignment
    Organization --> ExpenseFieldDefinition
    Organization --> ApprovalSequence
    ApprovalSequence --> ApprovalStep
    User --> Expense
    Expense --> Receipt
    Expense --> ApprovalInstance
    ApprovalInstance --> ApprovalAction
    Expense --> ArchiveRecord
""",
        "核心仍为 **Expense**；Admin 可配置的三元组：`ExpenseFieldDefinition`（动态字段）、`Role`+`Permission`（权限）、`ApprovalSequence`+`ApprovalStep`（审核顺序）。",
    ),
    (
        "03-admin-config-model.md",
        "Admin 配置模型",
        """
classDiagram
    direction LR

    class FieldSchemaService {
        +listFields()
        +createField(dto)
        +updateField(id, dto)
        +reorderFields(orderedIds)
        +disableField(id)
        +publishSchemaVersion()
    }

    class ExpenseFieldDefinition {
        +FieldType TEXT
        +FieldType NUMBER
        +FieldType DATE
        +FieldType SELECT
        +FieldType FILE
        +FieldType CURRENCY
    }

    class PermissionService {
        +listPermissions()
        +assignToRole(roleId, permIds)
        +assignRolesToUser(userId, roleIds)
    }

    class ApprovalConfigService {
        +listSequences()
        +createSequence(dto)
        +addStep(sequenceId, step)
        +reorderSteps(sequenceId, orderedStepIds)
        +setDefaultSequence(id)
    }

    class ApprovalStep {
        +ApproverRule FIXED_USER
        +ApproverRule ROLE
        +ApproverRule DEPARTMENT_HEAD
        +ApproverRule SUBMITTER_MANAGER
    }

    class ConfigAuditLog {
        +String entityType
        +String entityId
        +String changedBy
        +Json diff
    }

    FieldSchemaService --> ExpenseFieldDefinition
    PermissionService --> RolePermission
    ApprovalConfigService --> ApprovalSequence
    ApprovalConfigService --> ApprovalStep
    FieldSchemaService --> ConfigAuditLog
    ApprovalConfigService --> ConfigAuditLog
""",
        "Admin 侧三类配置服务；每次发布字段 schema 或调整审核顺序写入 `ConfigAuditLog` 便于追溯。",
    ),
    (
        "04-user-portal-frontend.md",
        "用户系统 · 前端",
        """
classDiagram
    direction TB

    class UserApp {
        +AuthProvider
        +PermissionGuard
        +Router
    }

    class HomePage {
        +draftCount
        +pendingApprovalCount
        +rejectedCount
    }

    class DynamicExpenseFormPage {
        -FieldDefinition[] schema
        -FormState fieldValues
        +loadSchema()
        +validateDynamic()
        +saveDraft()
        +submitExpense()
    }

    class MyExpensesPage {
        +tabs DRAFT SUBMITTED REJECTED APPROVED
        +filter sort
        +openDetail(id)
    }

    class ExpenseDetailPage {
        +Expense expense
        +ApprovalTimeline timeline
        +ReviewComments comments
        +editIfRejected()
        +resubmit()
    }

    class MyApprovalTasksPage {
        +Expense[] inbox
        +approve(step)
        +reject(comment)
    }

    class DynamicFieldRenderer {
        +render(fieldDef, value, onChange)
    }

    class UserExpenseApi {
        +getFieldSchema()
        +crudExpense()
        +submit/resubmit
    }

    class UserApprovalApi {
        +listMyTasks()
        +approve/reject
    }

    UserApp --> HomePage
    UserApp --> DynamicExpenseFormPage
    UserApp --> MyExpensesPage
    UserApp --> ExpenseDetailPage
    UserApp --> MyApprovalTasksPage
    DynamicExpenseFormPage --> DynamicFieldRenderer
    DynamicExpenseFormPage --> UserExpenseApi
    MyExpensesPage --> UserExpenseApi
    ExpenseDetailPage --> UserExpenseApi
    MyApprovalTasksPage --> UserApprovalApi
""",
        "用户 SPA：根据 Admin 发布的 **field schema** 动态渲染表单；具备审批权限的用户在「我的审核任务」处理当前步骤。",
    ),
    (
        "05-admin-portal-frontend.md",
        "Admin 系统 · 前端",
        """
classDiagram
    direction TB

    class AdminApp {
        +AdminAuthProvider
        +requirePermission(CONFIG_*)
    }

    class FieldConfigPage {
        +FieldEditorTable
        +AddFieldModal
        +DragReorderList
        +PreviewFormPanel
        +publishSchema()
    }

    class UserPermissionPage {
        +UserTable
        +RoleMatrix
        +AssignRoleDrawer
        +toggleActive(user)
    }

    class ApprovalSequencePage {
        +SequenceList
        +StepBuilder timeline
        +ApproverPicker rule+target
        +setDefaultSequence()
    }

    class AdminDashboardPage {
        +configVersion
        +recentAuditLogs
    }

    class AdminConfigApi {
        +fields CRUD reorder publish
        +users roles permissions
        +sequences steps reorder
    }

    AdminApp --> AdminDashboardPage
    AdminApp --> FieldConfigPage
    AdminApp --> UserPermissionPage
    AdminApp --> ApprovalSequencePage
    FieldConfigPage --> AdminConfigApi
    UserPermissionPage --> AdminConfigApi
    ApprovalSequencePage --> AdminConfigApi
""",
        "Admin SPA 三大配置页：字段、用户权限、审核顺序；支持拖拽排序与表单预览。",
    ),
    (
        "06-user-backend-api.md",
        "用户系统 · 后端 API",
        """
classDiagram
    direction TB

    class UserExpenseController {
        +GET /user/field-schema
        +POST /user/expenses
        +PUT /user/expenses/:id
        +GET /user/expenses
        +GET /user/expenses/:id
        +POST /user/expenses/:id/submit
        +POST /user/expenses/:id/resubmit
        +POST /user/expenses/:id/receipts
    }

    class UserApprovalController {
        +GET /user/approval-tasks
        +GET /user/approval-tasks/:expenseId
        +POST /user/approval-tasks/:id/approve
        +POST /user/approval-tasks/:id/reject
    }

    class UserArchiveController {
        +GET /user/archives/:expenseId
    }

    class ExpenseService {
        +createFromSchema(userId, fieldValues)
        +validateAgainstSchema(fieldValues)
        +submit(expenseId) ApprovalInstance
        +resubmit(expenseId)
    }

    class FieldSchemaReader {
        +getPublishedSchema(orgId)
    }

    class ApprovalEngine {
        +startInstance(expenseId)
        +resolveCurrentApprovers(instance)
        +approve(instanceId, actorId)
        +reject(instanceId, actorId, comment)
        +advanceOrComplete(instance)
    }

    class PermissionChecker {
        +has(userId, permissionCode)
    }

    UserExpenseController --> ExpenseService
    UserExpenseController --> FieldSchemaReader
    UserExpenseController --> PermissionChecker
    UserApprovalController --> ApprovalEngine
    UserApprovalController --> PermissionChecker
    ExpenseService --> ApprovalEngine
""",
        "用户 API 前缀 `/user/*`；submit 时 `ApprovalEngine` 按 Admin 配置的 `ApprovalSequence` 创建实例并定位第一步审批人。",
    ),
    (
        "07-admin-backend-api.md",
        "Admin 系统 · 后端 API",
        """
classDiagram
    direction TB

    class AdminFieldController {
        +GET /admin/fields
        +POST /admin/fields
        +PUT /admin/fields/:id
        +PATCH /admin/fields/reorder
        +POST /admin/fields/publish
        +DELETE /admin/fields/:id
    }

    class AdminUserController {
        +GET /admin/users
        +POST /admin/users
        +PUT /admin/users/:id
        +PUT /admin/users/:id/roles
        +PATCH /admin/users/:id/status
    }

    class AdminPermissionController {
        +GET /admin/permissions
        +GET /admin/roles
        +PUT /admin/roles/:id/permissions
    }

    class AdminApprovalConfigController {
        +GET /admin/approval-sequences
        +POST /admin/approval-sequences
        +PUT /admin/approval-sequences/:id
        +POST /admin/approval-sequences/:id/steps
        +PATCH /admin/approval-sequences/:id/steps/reorder
        +POST /admin/approval-sequences/:id/default
    }

    class FieldSchemaService
    class PermissionService
    class ApprovalConfigService
    class ConfigAuditService

    class AdminAuthGuard {
        +requireAdmin()
        +requirePermission(CONFIG_FIELDS)
    }

    AdminFieldController --> FieldSchemaService
    AdminUserController --> PermissionService
    AdminPermissionController --> PermissionService
    AdminApprovalConfigController --> ApprovalConfigService
    AdminFieldController --> AdminAuthGuard
    AdminUserController --> AdminAuthGuard
    FieldSchemaService --> ConfigAuditService
    ApprovalConfigService --> ConfigAuditService
""",
        "Admin API 前缀 `/admin/*`；所有写操作需 `CONFIG_*` 权限并由 `ConfigAuditService` 记日志。",
    ),
    (
        "08-permission-model.md",
        "权限模型细节",
        """
classDiagram
    direction TB

    class Permission {
        <<codes>>
        EXPENSE_CREATE
        EXPENSE_SUBMIT
        EXPENSE_VIEW_OWN
        APPROVAL_ACT
        ARCHIVE_VIEW
        CONFIG_FIELDS
        CONFIG_USERS
        CONFIG_APPROVAL
    }

    class Role {
        EMPLOYEE
        APPROVER
        FINANCE
        ADMIN
    }

    class RolePermission {
        +roleId
        +permissionId
    }

    class User {
        +id
        +roles Role[]
    }

    class PermissionChecker {
        +has(user, code) boolean
        +hasAny(user, codes[]) boolean
        +assert(user, code)
    }

    class UserPortalGate {
        +canCreateExpense()
        +canApprove()
    }

    class AdminPortalGate {
        +canEditFields()
        +canEditUsers()
        +canEditApprovalFlow()
    }

    Role --> RolePermission
    Permission --> RolePermission
    User --> PermissionChecker
    PermissionChecker --> UserPortalGate
    PermissionChecker --> AdminPortalGate
""",
        "典型映射：Employee→CREATE/SUBMIT；Approver→APPROVAL_ACT；Finance→APPROVAL_ACT+ARCHIVE；Admin→全部 CONFIG_*。",
    ),
    (
        "09-dynamic-expense-fields.md",
        "动态 Expense 字段",
        """
classDiagram
    direction LR

    class ExpenseFieldDefinition {
        +fieldKey amount
        +fieldKey expense_date
        +fieldKey category
        +fieldKey description
        +fieldKey receipt
    }

    class Expense {
        +Json fieldValues
    }

    class FieldSchemaVersion {
        +int version
        +DateTime publishedAt
        +String publishedBy
    }

    class DynamicValidator {
        +validate(fieldValues, schema) errors[]
    }

    class DynamicExpenseFormPage {
        +bind schema version
    }

    class ExpenseService {
        +snapshotSchemaVersionOnSubmit()
    }

    FieldSchemaVersion --> ExpenseFieldDefinition
    ExpenseService --> DynamicValidator
    DynamicValidator --> ExpenseFieldDefinition
    Expense --> FieldSchemaVersion : schemaVersionId
    DynamicExpenseFormPage --> FieldSchemaVersion
""",
        "提交时锁定 `schemaVersionId`，避免 Admin 改字段后历史 expense 语义漂移；用户表单始终拉取**当前已发布** schema。",
    ),
    (
        "10-approval-sequence-engine.md",
        "审核顺序引擎",
        """
classDiagram
    direction TB

    class ApprovalConfigService {
        +getDefaultSequence(orgId)
        +getSteps(sequenceId) ordered
    }

    class ApprovalEngine {
        +startInstance(expense)
        +getCurrentStep(instance)
        +resolveApprovers(step, expense) User[]
        +approve(instance, actor)
        +reject(instance, actor, comment)
    }

    class ApprovalSequence {
        +id
        +name
        +isDefault
    }

    class ApprovalStep {
        +stepOrder 1..n
        +approverRule
    }

    class ApprovalInstance {
        +currentStepOrder
        +status PENDING
    }

    class ApproverResolver {
        +resolve(rule, expense, submitter) userIds[]
    }

    class NotificationService {
        +notifyApprovers(users, expense)
        +notifySubmitterRejected(expense)
        +notifySubmitterApproved(expense)
    }

    ApprovalEngine --> ApprovalConfigService
    ApprovalEngine --> ApproverResolver
    ApprovalEngine --> ApprovalInstance
    ApprovalEngine --> NotificationService
    ApprovalStep --> ApproverResolver
""",
        "按 `stepOrder` 串行推进：当前步骤全部 approve 后 `currentStepOrder++`；任一步 reject 则 expense→REJECTED 并通知提交人。",
    ),
    (
        "11-expense-state-machine.md",
        "Expense 状态机",
        """
stateDiagram-v2
    [*] --> DRAFT : 用户创建

    DRAFT --> DRAFT : 保存草稿
    DRAFT --> SUBMITTED : submit\n校验字段+权限

    SUBMITTED --> IN_APPROVAL : 创建 ApprovalInstance\n通知第1步审批人

    IN_APPROVAL --> REJECTED : 任一步 reject
    REJECTED --> SUBMITTED : resubmit\n重走审核链

    IN_APPROVAL --> APPROVED : 最后一步 approve
    APPROVED --> ARCHIVED : 财务/系统存档

    note right of DRAFT
        仅 EXPENSE_CREATE 可编辑
    end note
    note right of IN_APPROVAL
        当前 step 的审批人可见
    end note
""",
        "用户侧 expense 生命周期；`IN_APPROVAL` 与 `ApprovalInstance` 同步。",
        "stateDiagram-v2",
    ),
    (
        "12-approval-instance-state-machine.md",
        "ApprovalInstance 状态机",
        """
stateDiagram-v2
    [*] --> PENDING : startInstance

    PENDING --> STEP_ACTIVE : currentStep = 1
    STEP_ACTIVE --> STEP_ACTIVE : approve current\n若还有下一步
    STEP_ACTIVE --> COMPLETED : approve 最后一步
    STEP_ACTIVE --> REJECTED : reject + comment

    REJECTED --> PENDING : resubmit 重置\nstepOrder = 1
    COMPLETED --> [*]
    REJECTED --> [*] : 等待用户修改

    note right of STEP_ACTIVE
        currentStepOrder 指向
        ApprovalStep.stepOrder
    end note
""",
        "审批实例与 expense 状态联动；resubmit 时实例重置从第 1 步开始。",
        "stateDiagram-v2",
    ),
    (
        "13-user-flow-sequence.md",
        "用户系统 · 端到端时序",
        """
sequenceDiagram
    actor Emp as 员工
    participant UFE as User Frontend
    participant API as User API
    participant ES as ExpenseService
    participant AE as ApprovalEngine
    actor Appr as 审批人

    Emp->>UFE: 打开新建报销
    UFE->>API: GET /user/field-schema
    API-->>UFE: published schema
    Emp->>UFE: 填写动态字段 + 附件
    UFE->>API: POST /user/expenses (DRAFT)
    Emp->>UFE: 提交
    UFE->>API: POST /user/expenses/:id/submit
    API->>ES: validate + submit
    ES->>AE: startInstance(sequence)
    AE-->>Emp: 通知已提交
    AE-->>Appr: 通知待审 step 1

    Appr->>UFE: 打开审核任务
    UFE->>API: POST approve
    API->>AE: approve
    alt 还有下一步
        AE-->>Appr: 通知 step n+1
    else 最后一步
        AE-->>Emp: 通知已通过
    end

    opt 审批人 reject
        Appr->>API: POST reject + comment
        AE-->>Emp: 通知退回
        Emp->>API: PUT 修改 + resubmit
        ES->>AE: reset instance step 1
    end
""",
        "从动态表单填报到多级审核、退回重提的完整用户系统时序。",
        "sequenceDiagram",
    ),
    (
        "14-admin-flow-sequence.md",
        "Admin 系统 · 配置时序",
        """
sequenceDiagram
    actor Adm as 管理员
    participant AFE as Admin Frontend
    participant API as Admin API
    participant FS as FieldSchemaService
    participant PS as PermissionService
    participant AC as ApprovalConfigService

    Adm->>AFE: 配置报销字段
    AFE->>API: POST/PUT /admin/fields
    API->>FS: save + reorder
    Adm->>AFE: 发布 schema
    AFE->>API: POST /admin/fields/publish
    FS-->>AFE: version++ 

    Adm->>AFE: 分配用户角色
    AFE->>API: PUT /admin/users/:id/roles
    API->>PS: assignRoles

    Adm->>AFE: 配置审核顺序
    AFE->>API: POST steps + PATCH reorder
    API->>AC: save ApprovalSequence
    Adm->>API: POST .../default
    AC-->>AFE: 新提交走此序列
""",
        "Admin 配置生效顺序建议：先字段 → 再权限 → 再审核链；发布字段后用户表单即时更新。",
        "sequenceDiagram",
    ),
    (
        "15-finance-review-archive.md",
        "终审与存档",
        """
classDiagram
    direction TB

    class FinanceReviewController {
        +GET /user/approval-tasks
        +POST approve/reject
    }

    class ArchiveController {
        +POST /admin/archives/batch
        +GET /admin/archives
    }

    class ArchiveService {
        +canArchive(expenseId)
        +buildBundle(expense, receipts)
        +markArchived()
    }

    class Expense {
        APPROVED
        ARCHIVED
    }

    FinanceReviewController --> ApprovalEngine
    ArchiveController --> ArchiveService
    ArchiveService --> Expense
""",
        "审核链最后一步常为 FINANCE 角色；全部 APPROVED 后由具备权限的 Admin/Finance 批量 archive。",
    ),
    (
        "16-shared-backend-layers.md",
        "共享后端分层",
        """
classDiagram
    direction TB

    class Presentation {
        UserExpenseController
        UserApprovalController
        AdminFieldController
        AdminUserController
        AdminApprovalConfigController
    }

    class Application {
        ExpenseService
        ApprovalEngine
        FieldSchemaService
        PermissionService
        ApprovalConfigService
        ArchiveService
    }

    class Domain {
        Expense
        ApprovalInstance
        ExpenseFieldDefinition
        ApprovalSequence
    }

    class Infrastructure {
        ExpenseRepository
        SchemaRepository
        ApprovalRepository
        UserRepository
        FileStorage
        EmailNotifier
    }

    Presentation --> Application
    Application --> Domain
    Application --> Infrastructure
""",
        "六边形简化视图：Presentation 按 User/Admin 拆分，Domain 共享。",
    ),
    (
        "17-end-to-end-actors.md",
        "端到端参与方",
        """
classDiagram
    direction TB

    class Employee {
        +User Portal
        +create/submit/resubmit
    }

    class Approver {
        +User Portal
        +approve/reject step
    }

    class Admin {
        +Admin Portal
        +config fields/roles/sequence
    }

    class System {
        +ApprovalEngine
        +NotificationService
        +ArchiveService
    }

    Employee --> ExpenseService : 1-2
    System --> ApprovalEngine : 3 route by sequence
    Approver --> ApprovalEngine : 4 each step
    Employee --> ExpenseService : 5 if rejected
    Approver --> ApprovalEngine : 6 final approve
    Admin --> ArchiveService : 7 archive batch
""",
        "三类人与系统协作：Admin 事前配置 → Employee 提交 → Approver 按序审核 → 存档。",
    ),
    (
        "18-api-routes-summary.md",
        "API 路由总表",
        """
classDiagram
    direction LR

    class UserRoutes {
        <</user>>
        GET field-schema
        CRUD expenses
        POST submit/resubmit
        GET approval-tasks
        POST approve/reject
    }

    class AdminRoutes {
        <</admin>>
        CRUD fields + publish
        CRUD users + roles
        CRUD approval-sequences
        POST archives/batch
    }

    class Auth {
        JWT access token
        role claims
        permission claims
    }

    UserRoutes --> Auth
    AdminRoutes --> Auth
""",
        "路由隔离：普通用户 token 无法访问 `/admin/*`；Admin token 可访问配置接口，默认不可代替他人填报 expense。",
    ),
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for item in DIAGRAMS:
        if len(item) == 4:
            filename, title, diagram, description = item
            diagram_kind = "classDiagram"
        else:
            filename, title, diagram, description, diagram_kind = item
        to_md(filename, title, diagram, description, diagram_kind)

    index = """# 报销系统 UML（用户系统 + Admin 系统）

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
"""
    (OUTPUT_DIR / "README.md").write_text(index, encoding="utf-8")
    print(f"Wrote {OUTPUT_DIR / 'README.md'}")

    keep = {d[0] for d in DIAGRAMS} | {"README.md"}
    for path in OUTPUT_DIR.glob("*.md"):
        if path.name not in keep:
            path.unlink()
            print(f"Removed obsolete {path}")


if __name__ == "__main__":
    main()
